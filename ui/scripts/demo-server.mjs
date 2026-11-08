import http from "node:http";
import { randomBytes, randomUUID, createHash, timingSafeEqual } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync, renameSync, statSync, createReadStream } from "node:fs";
import { dirname, extname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");
const statePath = join(root, ".demo-state", "state.json");
const port = Number(process.env.DEMO_PORT || 4174);
const accessCode = process.env.DEMO_ACCESS_CODE || randomBytes(4).toString("hex");
const expertIds = new Set(JSON.parse(readFileSync(join(root, "..", "fixtures", "GET_panels_match.json"), "utf8")).experts.map((item) => item.expert_id));
if (!existsSync(join(dist, "index.html"))) throw new Error("Build the shared demo first: npm run build:share");
mkdirSync(dirname(statePath), { recursive: true });
writeFileSync(join(dirname(statePath), "access-code.txt"), `${accessCode}\n`, { mode: 0o600 });
let state = { invitations: [], answers: {} };
if (existsSync(statePath)) {
  try { state = JSON.parse(readFileSync(statePath, "utf8")); }
  catch { throw new Error("Demo state could not be read; refusing to overwrite it."); }
}
function persist() {
  const temp = `${statePath}.${process.pid}.tmp`;
  writeFileSync(temp, JSON.stringify(state), { mode: 0o600 });
  renameSync(temp, statePath);
}
function headers(extra = {}) { return { "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "Cache-Control": "no-store", ...extra }; }
function json(res, status, body) { const data = JSON.stringify(body); res.writeHead(status, headers({ "Content-Type": "application/json; charset=utf-8", "Content-Length": Buffer.byteLength(data) })); res.end(data); }
function authorized(req) {
  const supplied = String(req.headers["x-demo-code"] || "");
  const a = Buffer.from(supplied), b = Buffer.from(accessCode);
  return a.length === b.length && timingSafeEqual(a, b);
}
async function readJson(req) {
  let body = "";
  for await (const chunk of req) {
    body += chunk;
    if (body.length > 32000) throw new Error("Request is too large.");
  }
  return JSON.parse(body || "{}");
}
function activeInvitation(token) { return state.invitations.find((item) => item.token === token && Date.parse(item.expiresAt) > Date.now()); }
function publicEngineRoute(pathname, method) {
  if (method === "GET" && (pathname === "/api/answer-key" || pathname === "/api/anchors" || /^\/api\/ledger(?:\/[^/]+)?(?:\/attestation)?$/.test(pathname))) return true;
  return /^\/api\/e\/[^/]+(?:\/(?:answer|confirm|feedback))?$/.test(pathname)
    && ((method === "GET" && !/\/(?:answer|confirm)$/.test(pathname)) || (method === "POST" && /\/(?:answer|confirm)$/.test(pathname)));
}
function proxyEngine(req, res, pathname) {
  if (!authorized(req) && !publicEngineRoute(pathname, req.method)) return json(res, 401, { error: "Analyst access code required" });
  const upstream = http.request({ hostname: "127.0.0.1", port: Number(process.env.ENGINE_PORT || 18000), path: req.url, method: req.method,
    headers: { ...req.headers, host: "127.0.0.1", connection: "close" } }, (response) => {
    res.writeHead(response.statusCode || 502, headers({ ...response.headers, "Cache-Control": "no-store" }));
    response.pipe(res);
  });
  upstream.on("error", () => { if (!res.headersSent) json(res, 502, { error: "The trust engine is unavailable" }); else res.destroy(); });
  req.pipe(upstream);
}
const mime = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".woff2": "font/woff2", ".woff": "font/woff", ".ico": "image/x-icon" };
function staticFile(res, pathname) {
  const candidate = resolve(dist, `.${pathname}`);
  if (candidate !== dist && !candidate.startsWith(dist + sep)) return json(res, 403, { error: "Forbidden" });
  const file = existsSync(candidate) && statSync(candidate).isFile() ? candidate : extname(pathname) ? null : join(dist, "index.html");
  if (!file || !existsSync(file)) return json(res, 404, { error: "Not found" });
  res.writeHead(200, headers({ "Content-Type": mime[extname(file)] || "application/octet-stream" }));
  createReadStream(file).pipe(res);
}

const server = http.createServer(async (req, res) => {
  let pathname;
  try { pathname = decodeURIComponent(new URL(req.url || "/", "http://localhost").pathname); }
  catch { return json(res, 400, { error: "Invalid URL" }); }
  try {
    if (pathname === "/api/demo/health" && req.method === "GET") return json(res, 200, { ok: true, mode: "shared-demo" });
    if (pathname === "/api/demo/login" && req.method === "POST") {
      const value = await readJson(req);
      const a = Buffer.from(String(value.code || "")), b = Buffer.from(accessCode);
      return json(res, a.length === b.length && timingSafeEqual(a, b) ? 200 : 401, { ok: a.length === b.length && timingSafeEqual(a, b) });
    }
    if (pathname === "/api/demo/state" && req.method === "GET") {
      if (!authorized(req)) return json(res, 401, { error: "Demo access code required" });
      const invitations = state.invitations.filter((item) => item.riskId === "R1043" && expertIds.has(item.expertId) && Date.parse(item.expiresAt) > Date.now());
      const confirmedCount = invitations.filter((item) => !!state.answers[item.token]).length;
      return json(res, 200, { invitations, confirmedCount });
    }
    if (pathname === "/api/demo/invitations" && req.method === "POST") {
      if (!authorized(req)) return json(res, 401, { error: "Demo access code required" });
      const body = await readJson(req);
      if (body.riskId !== "R1043" || !Array.isArray(body.expertIds) || body.expertIds.length !== 8 || new Set(body.expertIds).size !== 8 || body.expertIds.some((id) => !expertIds.has(id))) return json(res, 400, { error: "Use the eight fixture profiles for the Chad demo." });
      for (const expertId of body.expertIds) {
        if (state.invitations.some((item) => item.riskId === "R1043" && item.expertId === expertId && Date.parse(item.expiresAt) > Date.now())) continue;
        const issuedAt = new Date(), expiresAt = new Date(issuedAt.getTime() + 14 * 86400000);
        state.invitations.push({ token: `demo-${randomUUID()}`, riskId: "R1043", expertId, issuedAt: issuedAt.toISOString(), expiresAt: expiresAt.toISOString() });
      }
      persist();
      return json(res, 200, { invitations: state.invitations.filter((item) => item.riskId === "R1043" && expertIds.has(item.expertId) && Date.parse(item.expiresAt) > Date.now()) });
    }
    const invitationMatch = /^\/api\/demo\/invitations\/(demo-[a-f0-9-]+)$/.exec(pathname);
    if (invitationMatch && req.method === "GET") {
      const invitation = activeInvitation(invitationMatch[1]);
      return invitation ? json(res, 200, { invitation }) : json(res, 404, { error: "Invitation unavailable or expired" });
    }
    const answerMatch = /^\/api\/demo\/invitations\/(demo-[a-f0-9-]+)\/answer$/.exec(pathname);
    if (answerMatch && req.method === "POST") {
      const invitation = activeInvitation(answerMatch[1]);
      if (!invitation) return json(res, 404, { error: "Invitation unavailable or expired" });
      const body = await readJson(req), answer = body.answer;
      if (!answer || !["known", "pseudonym", "anonymous"].includes(answer.mask) || !["estimate", "outside_my_expertise", "not_enough_evidence"].includes(answer.stance) || JSON.stringify(answer).length > 4000) return json(res, 400, { error: "Invalid answer" });
      const salt = randomBytes(16).toString("hex"), committedAt = new Date().toISOString();
      const commitment = createHash("sha256").update(JSON.stringify({ answer, salt })).digest("hex");
      const version = (state.answers[invitation.token]?.version || 0) + 1;
      state.answers[invitation.token] = { answer, salt, commitment, committedAt, version };
      persist();
      return json(res, 200, { committed_at: committedAt, commitment, version, correction_allowed_until: invitation.expiresAt, message: "Answer confirmed in the shared demo. No independent timestamp is connected.", served_from: "demo", generated_at: committedAt });
    }
    if (pathname.startsWith("/api/")) return proxyEngine(req, res, pathname);
    return staticFile(res, pathname);
  } catch (error) { return json(res, 400, { error: error instanceof Error ? error.message : "Request failed" }); }
});
server.listen(port, "127.0.0.1", () => {
  process.stdout.write(`Shared demo: http://127.0.0.1:${port}\nAnalyst access code: ${accessCode}\n`);
});
