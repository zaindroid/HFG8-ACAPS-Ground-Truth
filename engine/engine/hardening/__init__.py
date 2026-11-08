"""The hardening stack of MASTER_PROMPT sections 6c and 6d.

One object, `Hardening`, holds the stateful pieces so the API has a single thing to reset
between tests and a single thing to report on. Each piece keeps its own honest fallback, and the
status payload always carries the guarantee / does-not wording, because a mechanism described
loosely is worse than one that is switched off.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from . import anchors as anchors_mod
from . import attest as attest_mod
from . import calibration as calibration_mod
from . import credentials as credentials_mod
from . import flags, keys, patterns, registry as registry_mod, zk as zk_mod

__all__ = ["Hardening", "flags", "keys", "patterns", "calibration_mod", "new"]


@dataclass
class Hardening:
    registry: registry_mod.Registry = field(default_factory=registry_mod.Registry)
    attestations: attest_mod.Attestations = field(default_factory=attest_mod.Attestations)
    credentials: credentials_mod.Credentials = field(default_factory=credentials_mod.Credentials)
    anchors: anchors_mod.Anchors = field(default_factory=anchors_mod.Anchors)
    membership: zk_mod.Membership = field(default_factory=zk_mod.Membership)
    calibration: calibration_mod.Programme = field(default_factory=calibration_mod.Programme)

    def status(self) -> dict:
        return {
            "flags": flags.flags(),
            "mechanisms": flags.mechanisms(),
            "registry": self.registry.status(),
            "attestation_key": self.attestations.public_key(),
            "credentials": {k: v for k, v in self.credentials.summary().items()
                            if k != "batches"},
            "anchors": {"days": len(self.anchors.roots),
                        "anchored": sum(1 for r in self.anchors.roots.values()
                                        if r.status == "anchored"),
                        "pending": sum(1 for r in self.anchors.roots.values()
                                       if r.status != "anchored")},
            "zk": self.membership.status(),
            "calibration": self.calibration.counts(),
        }

    def reset(self) -> None:
        self.registry.reset()
        self.attestations.reset()
        self.credentials.reset()
        self.anchors.reset()
        self.membership.reset()
        self.calibration.enrolments.clear()


def new() -> Hardening:
    return Hardening()
