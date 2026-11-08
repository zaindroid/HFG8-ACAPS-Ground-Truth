/** End-to-end encryption of the expert's answer, in the browser. The engine side, with the full
 *  envelope format, is engine/engine/hardening/e2e.py; the two must stay byte-for-byte in step,
 *  which engine/tests/hardening/test_e2e.py checks against a vector this file produced.
 *
 *  ML-KEM-768 encapsulation and an ephemeral X25519 exchange to the engine's published keys,
 *  both secrets through HKDF-SHA256 to one AES-256-GCM key; the token and the route are the AAD,
 *  so a ciphertext sealed for one link or route does not open on another. */
import { ml_kem768 } from "@noble/post-quantum/ml-kem.js";
import { x25519 } from "@noble/curves/ed25519.js";
import { hkdf } from "@noble/hashes/hkdf.js";
import { sha256 } from "@noble/hashes/sha2.js";

export type AnswerKey = {
  enabled: boolean;
  v: number;
  kid: string;
  suite: string;
  ml_kem_768_pub: string;
  x25519_pub: string;
};
export type Envelope = {
  e2e: {
    v: 1;
    kid: string;
    kem_ct: string;
    x25519_pub: string;
    nonce: string;
    ct: string;
  };
};
export const ROUTES = {
  draft: "POST /e/answer",
  confirm: "POST /e/confirm",
  correct: "PUT /e/answer",
} as const;
export type Route = keyof typeof ROUTES;

const utf8 = new TextEncoder();
const INFO_LABEL = "sealed-signals/e2e-answer/v1|";
const AAD_LABEL = "sealed-signals/e2e/v1";

function fromB64(value: string): Uint8Array {
  const binary = atob(value);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) out[i] = binary.charCodeAt(i);
  return out;
}
function toB64(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}
function concat(...parts: Uint8Array[]): Uint8Array {
  const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let offset = 0;
  for (const part of parts) {
    out.set(part, offset);
    offset += part.length;
  }
  return out;
}
/** A copy on a fresh ArrayBuffer, which is what the WebCrypto types ask for. */
function buf(bytes: Uint8Array): Uint8Array<ArrayBuffer> {
  const out = new Uint8Array(new ArrayBuffer(bytes.length));
  out.set(bytes);
  return out;
}

export async function seal(
  body: unknown,
  token: string,
  route: Route,
  key: AnswerKey,
): Promise<Envelope> {
  const serverX = fromB64(key.x25519_pub);
  const { cipherText, sharedSecret } = ml_kem768.encapsulate(
    fromB64(key.ml_kem_768_pub),
  );
  const ephemeral = x25519.utils.randomSecretKey();
  const ephemeralPub = x25519.getPublicKey(ephemeral);
  const classical = x25519.getSharedSecret(ephemeral, serverX);
  const aesKey = hkdf(
    sha256,
    concat(sharedSecret, classical, ephemeralPub, serverX),
    undefined,
    utf8.encode(INFO_LABEL + key.kid),
    32,
  );
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    buf(aesKey),
    "AES-GCM",
    false,
    ["encrypt"],
  );
  const ct = new Uint8Array(
    await crypto.subtle.encrypt(
      {
        name: "AES-GCM",
        iv: nonce,
        additionalData: utf8.encode(`${AAD_LABEL}|${ROUTES[route]}|${token}`),
      },
      cryptoKey,
      utf8.encode(JSON.stringify(body)),
    ),
  );
  return {
    e2e: {
      v: 1,
      kid: key.kid,
      kem_ct: toB64(cipherText),
      x25519_pub: toB64(ephemeralPub),
      nonce: toB64(nonce),
      ct: toB64(ct),
    },
  };
}
