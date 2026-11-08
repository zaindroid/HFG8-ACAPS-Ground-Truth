"""MASTER_PROMPT section 6c tests, one per line of the table.

These check the mechanisms themselves, not the routes: a round trip, a signature that fails on a
flipped byte, a credential that cannot be spent twice, an anchor that only reads `anchored` when the
public log returns an inclusion proof, and a registry read that lands in the log. test_routes.py checks the product
surface on top of them.
"""
from __future__ import annotations
import hashlib
import base64
import os

import pytest

from engine.hardening import anchors as anchors_mod
from engine.hardening import attest as attest_mod
from engine.hardening import credentials as credentials_mod
from engine.hardening import flags, registry as registry_mod, zk as zk_mod

IDENTITY = {"name": "Test Person (synthetic)", "email": "test@example.invalid"}


# -- 1. post-quantum registry encryption ---------------------------------------
def test_registry_round_trip_under_the_hybrid_kem():
    registry = registry_mod.Registry()
    registry.put("X-1", IDENTITY)

    assert registry.blob, "the map must be stored as ciphertext"
    assert IDENTITY["email"] not in registry.blob
    assert registry.wrap["kem_ciphertext"], "the data key must be wrapped by the KEM"
    assert registry.read("X-1", who="committee", why="test") == IDENTITY
    assert registry.status()["encryption"] == registry_mod.SUITE


def test_registry_ciphertext_is_not_decryptable_without_the_committee_key():
    registry = registry_mod.Registry()
    registry.put("X-1", IDENTITY)
    # Corrupting the wrapped data key must break the read rather than degrade quietly.
    broken = bytearray(base64.b64decode(registry.wrapped_data_key))
    broken[0] ^= 0xFF
    registry.wrapped_data_key = base64.b64encode(bytes(broken)).decode()
    with pytest.raises(Exception):
        registry.read("X-1", who="committee", why="test")


def test_registry_falls_back_and_says_so_when_the_flag_is_off(monkeypatch):
    monkeypatch.setenv("FF_PQ", "0")
    registry = registry_mod.Registry()
    registry.put("X-1", IDENTITY)
    status = registry.status()
    assert status["encryption"] == "off"
    assert "FF_PQ is off" in status["lock_line"]
    # The fallback still works, which is the point of having one.
    assert registry.read("X-1", who="committee", why="test") == IDENTITY


# -- 6. registry access log ----------------------------------------------------
def test_a_registry_read_appears_in_the_log():
    registry = registry_mod.Registry()
    registry.put("X-1", IDENTITY)
    assert registry.log() == []
    registry.read("X-1", who="desk-admin", why="verify a reported duplicate")
    entry = registry.log()[-1]
    assert entry["who"] == "desk-admin"
    assert entry["why"] == "verify a reported duplicate"
    assert entry["expert_id"] == "X-1"


def test_an_unattributed_read_is_refused():
    registry = registry_mod.Registry()
    registry.put("X-1", IDENTITY)
    with pytest.raises(ValueError):
        registry.read("X-1", who="", why="curiosity")
    with pytest.raises(ValueError):
        registry.read("X-1", who="desk-admin", why="")
    assert registry.log() == [], "a refused read must not be logged as a read"


def test_counting_identities_is_not_a_read():
    registry = registry_mod.Registry()
    registry.put("X-1", IDENTITY)
    assert registry.count() == 1
    assert registry.log() == []


# -- 2. post-quantum outcome attestations --------------------------------------
def test_attestation_verifies_and_fails_on_a_flipped_byte():
    attestations = attest_mod.Attestations()
    record = attestations.attest("R1043", "materialised", "2026-11-07T12:00:00+00:00", "ab" * 32)

    assert record["scheme"] == attest_mod.PQ_SCHEME
    assert attestations.verify(record)["valid"] is True

    signature = bytearray(base64.b64decode(record["signature"]))
    signature[7] ^= 0x01
    flipped = {**record, "signature": base64.b64encode(bytes(signature)).decode()}
    assert attestations.verify(flipped)["valid"] is False


def test_attestation_fails_when_the_record_is_edited():
    attestations = attest_mod.Attestations()
    record = attestations.attest("R1043", "materialised", "2026-11-07T12:00:00+00:00", "cd" * 32)
    assert attestations.verify({**record, "outcome": "not_materialised"})["valid"] is False


def test_attestation_public_key_is_stable_across_instances():
    """A published key id that changed on every restart would be worthless."""
    first, second = attest_mod.Attestations(), attest_mod.Attestations()
    assert first.public_key()["key_id"] == second.public_key()["key_id"]
    assert first.public_key()["scheme"] == "ML-DSA-65"


def test_attestation_fallback_is_labelled_as_an_hmac(monkeypatch):
    monkeypatch.setenv("FF_PQ", "0")
    attestations = attest_mod.Attestations()
    record = attestations.attest("R1043", "materialised", "2026-11-07T12:00:00+00:00", "ef" * 32)
    assert record["scheme"] == attest_mod.FALLBACK_SCHEME
    assert attestations.verify(record)["valid"] is True
    assert attestations.public_key()["public_key"] is None


# -- 3. blind-signed single-use credentials ------------------------------------
def test_blind_signature_verifies_as_standard_rsa_pss():
    """The committee signs a value it cannot read, and the result passes a plain RSA-PSS verify."""
    issuer = credentials_mod.Credentials()
    public = issuer.public_key()
    modulus, exponent = int(public["n"], 16), public["e"]

    token_id = os.urandom(16).hex()
    blinded, inverse = credentials_mod.blind(
        credentials_mod.message_for(token_id), modulus, exponent
    )
    issued = issuer.issue("X-1", "PAN-TCD", blinded=[hex(blinded)])
    assert issued["unlinkable"] is True

    raw = credentials_mod.unblind(int(issued["blind_signatures"][0], 16), inverse, modulus)
    signature = base64.b64encode(raw).decode()
    assert issuer.verify(token_id, signature) is True
    assert issuer.verify(token_id, base64.b64encode(b"\x00" * 256).decode()) is False


def test_a_credential_cannot_be_spent_twice():
    issuer = credentials_mod.Credentials()
    issued = issuer.issue("X-1", "PAN-TCD", count=1)
    token = issued["credentials"][0]

    assert issuer.spend(token["token_id"], token["signature"], "P-0001")["pulse_id"] == "P-0001"
    with pytest.raises(ValueError, match="already spent"):
        issuer.spend(token["token_id"], token["signature"], "P-0002")


def test_an_unsigned_token_cannot_be_spent():
    issuer = credentials_mod.Credentials()
    with pytest.raises(ValueError, match="valid committee signature"):
        issuer.spend(os.urandom(16).hex(), base64.b64encode(b"\x01" * 256).decode(), "P-0001")


def test_the_issuer_cannot_match_a_spent_token_to_an_approval():
    """The unlinkability claim, as a test: on the blind path nothing the server stored names the
    token it later accepts."""
    issuer = credentials_mod.Credentials()
    public = issuer.public_key()
    modulus, exponent = int(public["n"], 16), public["e"]
    token_id = os.urandom(16).hex()
    blinded, inverse = credentials_mod.blind(
        credentials_mod.message_for(token_id), modulus, exponent
    )
    issued = issuer.issue("X-approved-expert", "PAN-TCD", blinded=[hex(blinded)])
    signature = base64.b64encode(
        credentials_mod.unblind(int(issued["blind_signatures"][0], 16), inverse, modulus)
    ).decode()
    issuer.spend(token_id, signature, "P-0001")

    summary = issuer.summary()
    assert summary["n_issued"] == 1 and summary["n_spent"] == 1
    assert summary["linked"] is False
    for batch in summary["batches"]:
        assert token_id not in repr(batch), "the issuance record must not contain the token id"
    assert issuer.spent[token_id].get("expert_id") is None


def test_the_demo_path_does_not_claim_unlinkability():
    issuer = credentials_mod.Credentials()
    issued = issuer.issue("X-1", "PAN-TCD", count=2)
    assert issued["unlinkable"] is False
    assert "unlinkability claim does not apply" in issued["note"]
    assert issuer.summary()["n_unlinkable_issued"] == 0


# -- 4. zero-knowledge group membership ----------------------------------------
def _proof(group, secret: str, pulse_id: str) -> dict:
    return {
        "panel_id": group.panel_id,
        "group_root": group.root,
        "nullifier": zk_mod.nullifier(secret, pulse_id),
        "points": list(range(8)),
    }


def test_no_membership_proof_is_accepted_while_the_flag_is_off():
    membership = zk_mod.Membership()
    group = membership.add_group("PAN-TCD", [zk_mod.identity_commitment("s1")])
    verdict = membership.verify(_proof(group, "s1", "P-0001"), "P-0001")
    assert flags.enabled("FF_ZK") is False
    assert verdict["accepted"] is False
    assert "FF_ZK is off" in verdict["reason"]


def test_nullifier_rejects_a_second_answer(monkeypatch):
    monkeypatch.setenv("FF_ZK", "1")
    membership = zk_mod.Membership()
    group = membership.add_group("PAN-TCD", [zk_mod.identity_commitment(f"s{i}") for i in range(8)])

    first = membership.verify(_proof(group, "s3", "P-0001"), "P-0001")
    assert first["accepted"] is True
    second = membership.verify(_proof(group, "s3", "P-0001"), "P-0001")
    assert second["accepted"] is False
    assert second["checks"]["nullifier_unused"] is False
    # A different pulse means a different nullifier, so the same member may answer that one.
    assert membership.verify(_proof(group, "s3", "P-0002"), "P-0002")["accepted"] is True


def test_the_verdict_never_claims_the_proof_was_checked(monkeypatch):
    monkeypatch.setenv("FF_ZK", "1")
    membership = zk_mod.Membership()
    group = membership.add_group("PAN-TCD", [zk_mod.identity_commitment("s1")])
    verdict = membership.verify(_proof(group, "s1", "P-0001"), "P-0001")
    assert verdict["cryptographic_verification"] is False
    assert "Groth16" in verdict["not_checked"]


def test_a_proof_against_an_unknown_group_is_rejected(monkeypatch):
    monkeypatch.setenv("FF_ZK", "1")
    membership = zk_mod.Membership()
    membership.add_group("PAN-TCD", [zk_mod.identity_commitment("s1")])
    bad = {"panel_id": "PAN-OTHER", "group_root": "00" * 32,
           "nullifier": zk_mod.nullifier("s1", "P-0001"), "points": list(range(8))}
    assert membership.verify(bad, "P-0001")["accepted"] is False


# -- 5. public timestamp (Sigstore Rekor) -------------------------------------
def _entry(index: int, proof: bool) -> dict:
    verification = {"signedEntryTimestamp": "c2V0"}
    if proof:
        verification["inclusionProof"] = {"logIndex": index, "rootHash": "ab" * 32,
                                          "treeSize": index + 1, "hashes": []}
    return {"logIndex": index, "integratedTime": 1794096000, "logID": "c0d23d6a",
            "body": "e30=", "verification": verification}


class FakeLog:
    """Stands in for Rekor: logs a root, returns the inclusion proof only when told to."""

    def __init__(self, proof: bool = False) -> None:
        self.proof = proof
        self.submitted: list[str] = []

    def submit(self, root_hex: str):
        self.submitted.append(root_hex)
        return "24296fb2" + root_hex[:8], _entry(1234567, self.proof)

    def fetch(self, uuid: str):
        return uuid, _entry(1234567, self.proof)


def test_merkle_root_is_stable_and_order_independent():
    leaves = ["aa" * 32, "bb" * 32, "cc" * 32]
    assert anchors_mod.merkle_root(leaves) == anchors_mod.merkle_root(list(reversed(leaves)))
    assert anchors_mod.merkle_root(["aa" * 32]) == "aa" * 32
    assert anchors_mod.merkle_root([]) == ""


def test_the_logged_entry_carries_only_the_root_and_a_valid_signature():
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    root = "ab" * 32
    entry = anchors_mod.hashedrekord(root)
    spec = entry["spec"]
    assert entry["kind"] == "hashedrekord"
    assert spec["data"]["hash"]["value"] == hashlib.sha256(bytes.fromhex(root)).hexdigest()
    public = serialization.load_pem_public_key(
        base64.b64decode(spec["signature"]["publicKey"]["content"]))
    public.verify(base64.b64decode(spec["signature"]["content"]), bytes.fromhex(root),
                  ec.ECDSA(hashes.SHA256()))
    # Same committee secret, same key: past entries stay checkable after a restart.
    assert anchors_mod.public_key_pem() == anchors_mod.public_key_pem()


def test_anchor_goes_pending_then_anchored():
    store = anchors_mod.Anchors()
    store.log = FakeLog(proof=False)
    store.record("2026-11-07", ["aa" * 32, "bb" * 32])

    submitted = store.submit("2026-11-07")
    assert submitted.status == "pending"
    assert submitted.log_index == 1234567 and submitted.entry_uuid
    assert "becomes anchored" in submitted.note
    assert submitted.verify_url() is None

    store.log.proof = True
    anchored = store.upgrade("2026-11-07")
    assert anchored.status == "anchored"
    assert anchored.anchored_at and anchored.integrated_at
    assert anchored.receipt, "the signed timestamp and proof must be kept"
    assert anchored.verify_url() == "https://search.sigstore.dev/?logIndex=1234567"
    assert "existed by that time" in anchored.as_dict()["guarantees"]


def test_an_entry_returned_with_its_proof_is_anchored_at_once():
    store = anchors_mod.Anchors()
    store.log = FakeLog(proof=True)
    store.record("2026-11-07", ["aa" * 32])
    assert store.submit("2026-11-07").status == "anchored"


def test_a_pending_root_says_it_proves_nothing_yet():
    store = anchors_mod.Anchors()
    store.log = FakeLog()
    store.record("2026-11-07", ["aa" * 32])
    assert "proves nothing" in store.submit("2026-11-07").as_dict()["means"]


def test_an_unreachable_log_does_not_invent_an_anchor():
    class Dead:
        def submit(self, root_hex):
            return None

        def fetch(self, uuid):
            return None

    store = anchors_mod.Anchors()
    store.log = Dead()
    store.record("2026-11-07", ["aa" * 32])
    root = store.submit("2026-11-07")
    assert root.status == "pending" and root.receipt is None and root.log_index is None
    assert "not reachable" in root.note


def test_the_flag_off_computes_the_root_and_never_submits(monkeypatch):
    monkeypatch.setenv("FF_ANCHOR", "0")
    store = anchors_mod.Anchors()
    store.log = FakeLog()
    store.record("2026-11-07", ["aa" * 32])
    root = store.submit("2026-11-07")
    assert root.merkle_root and root.status == "pending"
    assert store.log.submitted == []

def test_a_receipt_is_only_returned_for_a_commitment_in_that_root():
    store = anchors_mod.Anchors()
    store.record("2026-11-06", ["aa" * 32])
    store.record("2026-11-07", ["bb" * 32])
    assert store.receipt_for_commitment("aa" * 32)["day"] == "2026-11-06"
    assert store.receipt_for_commitment("bb" * 32)["day"] == "2026-11-07"
    assert store.receipt_for_commitment("cc" * 32) is None


# -- the wording, which is part of the build -----------------------------------
def test_every_mechanism_states_a_guarantee_and_a_limit():
    for mechanism in flags.mechanisms():
        assert mechanism["guarantees"].strip()
        assert mechanism["does_not"].strip()
        assert mechanism["name"].strip()
    assert len(flags.mechanisms()) == 8


def test_the_linkage_note_describes_the_path_the_tokens_actually_took():
    """The sentence shown to the committee must match the mix of tokens on this instance."""
    issuer = credentials_mod.Credentials()
    assert "No credentials issued" in issuer.summary()["linkage_note"]

    issuer.issue("X-1", "PAN-TCD", count=2)
    demo_only = issuer.summary()["linkage_note"]
    assert "demo path" in demo_only and "not unlinkable" in demo_only

    public = issuer.public_key()
    modulus, exponent = int(public["n"], 16), public["e"]
    blinded, _ = credentials_mod.blind(credentials_mod.message_for("aa" * 16), modulus, exponent)
    issuer.issue("X-2", "PAN-TCD", blinded=[hex(blinded)])
    mixed = issuer.summary()["linkage_note"]
    assert "1 of 3" in mixed and "The other 2" in mixed
