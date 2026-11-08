/** Writes the interoperability vector for end-to-end answers: an envelope sealed by the browser
 *  module (src/e2e.ts, @noble/post-quantum ML-KEM-768) that engine/tests/hardening/test_e2e.py
 *  must open with kyber_py. Run from ui/:
 *
 *    node --experimental-strip-types scripts/make-e2e-vector.ts <answer-key.json> <out.json>
 *
 *  where answer-key.json is GET /api/answer-key from an engine started with
 *  COMMITTEE_KEY=test-committee-key (the value the engine tests use). */
import { readFileSync, writeFileSync } from "node:fs";
import { seal, type AnswerKey } from "../src/e2e.ts";

const [keyPath, outPath] = process.argv.slice(2);
if (!keyPath || !outPath) {
  console.error("usage: make-e2e-vector.ts <answer-key.json> <out.json>");
  process.exit(2);
}
const key = JSON.parse(readFileSync(keyPath, "utf8")) as AnswerKey;
const token = "vector-token";
const body = {
  mask: "pseudonym",
  stance: "estimate",
  likelihood_word: "likely",
  probability: 0.62,
  missing: "Grenzübergang offen? -- non-ASCII on purpose",
};
const envelope = await seal(body, token, "draft", key);
writeFileSync(
  outPath,
  JSON.stringify(
    {
      note: "Sealed by ui/src/e2e.ts (@noble/post-quantum ML-KEM-768, @noble/curves X25519, " +
        "@noble/hashes HKDF-SHA256, WebCrypto AES-256-GCM); opened in Python by test_e2e.py.",
      committee_key: "test-committee-key",
      kid: key.kid,
      token,
      route: "draft",
      body,
      envelope,
    },
    null,
    2,
  ) + "\n",
);
console.log(`wrote ${outPath} for key ${key.kid}`);
