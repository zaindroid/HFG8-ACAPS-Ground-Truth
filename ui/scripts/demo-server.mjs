import http from "node:http";
import { randomBytes, createHash, timingSafeEqual } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync, renameSync, statSync, createReadStream } from "node:fs";
import { dirname, extname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");
const statePath = join(root, ".demo-state", "state.json");
const port = Number(process.env.DEMO_PORT || 4174);
const accessCode = process.env.DEMO_ACCESS_CODE || randomBytes(4).toString("hex");
if (!existsSync(join(dist, "index.html"))) throw new Error("Build the shared demo first: npm run build:share");
mkdirSync(dirname(statePath), { recursive: true });
writeFileSync(join(dirname(statePath), "access-code.txt"), `${accessCode}\n`, { mode: 0o600 });
// The live panel. Its five fixed answers and its three seat labels live in the same file the
// browser reads, so a seat is never defined twice and the two sides cannot drift apart.
const livePanel = JSON.parse(readFileSync(join(root, "src", "data", "live-panel.json"), "utf8"));
const seatTokens = new Set(livePanel.seats.map((seat) => seat.token));
// A hold on a seat is a lease, not a lock: somebody who scans a code, reads the question and
// puts their phone away must not keep the seat shut. An open card renews while it is on screen.
const LEASE_MS = 45000;
let state = { invitations: [], answers: {}, seats: {} };
if (existsSync(statePath)) {
  try { state = JSON.parse(readFileSync(statePath, "utf8")); }
  catch { throw new Error("Demo state could not be read; refusing to overwrite it."); }
}
if (!state.seats) state.seats = {};
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
// --- the three open seats on the live panel -------------------------------------------------
// open -> in use (a lease held by one scanner) -> submitted (closed for good). A submitted
// seat never reopens, lease or no lease; an abandoned one reopens when its lease runs out.
function seatState(token, holder) {
  const seat = state.seats[token];
  if (seat?.submitted) return { token, state: "submitted", mine: seat.holder === holder, committed_at: seat.committedAt };
  const held = !!seat?.holder && (seat.leaseUntil || 0) > Date.now();
  return { token, state: held ? "in_use" : "open", mine: held && seat.holder === holder };
}
function seatHolderFrom(body) {
  const holder = String(body?.holder || "");
  return /^[a-f0-9-]{8,64}$/i.test(holder) ? holder : "";
}
function liveEstimate(answer) {
  const midpoints = { very_unlikely: 0.05, unlikely: 0.225, even: 0.5, likely: 0.775, very_likely: 0.95 };
  if (typeof answer?.probability === "number" && Number.isFinite(answer.probability)) return answer.probability;
  const word = answer?.likelihood_word;
  return typeof word === "string" && word in midpoints ? midpoints[word] : null;
}
const insightTopics = [
  ["Displacement", ["displacement", "protection"]],
  ["Conflict", ["conflict", "political"]],
  ["Access and logistics", ["access", "logistics"]],
  ["Health and services", ["health", "food"]],
];
const concernTopics = [
  ["Movement and routes", /mov|route|road|river|cross|return|transport/i],
  ["Host-site capacity", /site|camp|capacity|shelter|registration|service|hospital|health/i],
  ["Conflict and talks", /fight|clash|conflict|talk|peace|violence|security/i],
  ["Aid access", /access|agency|aid|humanitarian|supply/i],
];
function liveAnalysis() {
  const entries = [
    ...livePanel.directory.map((expert) => ({ region: "South Sudan perspectives", tags: expert.theme_tags, answer: expert.answer })),
    ...livePanel.seats.map((seat) => ({ region: "Netherlands perspectives", tags: seat.theme_tags, answer: state.seats[seat.token]?.answer })),
  ];
  const rated = entries.map((entry) => ({ ...entry, estimate: liveEstimate(entry.answer) })).filter((entry) => entry.estimate !== null);
  const regions = ["South Sudan perspectives", "Netherlands perspectives"].map((region) => {
    const values = rated.filter((entry) => entry.region === region).map((entry) => entry.estimate);
    return { region, n: values.length, mean: values.length >= 3 ? values.reduce((a, b) => a + b, 0) / values.length : null };
  });
  const topics = insightTopics.map(([topic, tags]) => {
    const values = rated.filter((entry) => entry.tags.some((tag) => tags.includes(tag))).map((entry) => entry.estimate);
    return { topic, n: values.length, higher: values.length >= 3 ? values.filter((value) => value >= 0.5).length : null, lower: values.length >= 3 ? values.filter((value) => value < 0.5).length : null };
  });
  const notes = entries.map((entry) => String(entry.answer?.missing || "").trim()).filter(Boolean);
  const concerns = concernTopics.map(([topic, pattern]) => ({ topic, n: notes.filter((note) => pattern.test(note)).length })).filter((item) => item.n > 0);
  const other = notes.filter((note) => !concernTopics.some(([, pattern]) => pattern.test(note))).length;
  if (other) concerns.push({ topic: "Other concerns for review", n: other });
  return { regions, topics, concerns, notes: notes.length };
}
async function engineJson(pathname, options = {}) {
  const response = await fetch(`http://127.0.0.1:${Number(process.env.ENGINE_PORT || 18000)}${pathname}`, options);
  const value = await response.json();
  if (!response.ok) { const error = new Error(value.detail || `Trust engine returned ${response.status}`); error.status = response.status; throw error; }
  return value;
}
async function currentEnginePanel() {
  if (!state.enginePanel) return null;
  try {
    const tray = await engineJson(`/api/pulses/${encodeURIComponent(state.enginePanel.pulseId)}/tray`);
    return { invitations: state.enginePanel.invitations, confirmedCount: tray.n_answers };
  } catch (error) {
    if (error.status !== 404) throw error;
    state.enginePanel = null;
    persist();
    return null;
  }
}
function publicEngineRoute(pathname, method) {
  if (method === "GET" && (
    ["/api/answer-key", "/api/anchors", "/api/trust/status", "/api/panels/match", "/api/registry/status", "/api/credentials/status", "/api/committee/access-log", "/api/committee/patterns"].includes(pathname)
    || /^\/api\/risks\/[^/]+\/chain$/.test(pathname)
    || /^\/api\/ledger(?:\/[^/]+)?(?:\/attestation)?$/.test(pathname)
  )) return true;
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
    if (pathname === "/api/demo/state" && req.method === "GET") {
      const panel = await currentEnginePanel();
      return json(res, 200, panel || { invitations: [], confirmedCount: 0 });
    }
    if (pathname === "/api/demo/invitations" && req.method === "POST") {
      const body = await readJson(req);
      if (body.riskId !== "R1043" || !Array.isArray(body.expertIds) || body.expertIds.length !== 8 || new Set(body.expertIds).size !== 8) return json(res, 400, { error: "Choose eight experts for the Chad case." });
      const existing = await currentEnginePanel();
      if (existing) return json(res, 200, existing);
      const issued = await engineJson("/api/demo/interactive-panel", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ risk_id: "R1043" }) });
      if (new Set(issued.invitations.map((item) => item.expertId)).size !== 8 || issued.invitations.some((item) => !body.expertIds.includes(item.expertId))) return json(res, 409, { error: "The roster changed. Refresh and choose the current experts." });
      state.enginePanel = { pulseId: issued.pulse_id, invitations: issued.invitations };
      persist();
      return json(res, 200, { invitations: issued.invitations, confirmedCount: 0 });
    }
    // Seat state carries no answers: the three live answers stay sealed with the other five
    // until the analyst reveals. That is why the result below is behind the access code and
    // this is not -- an expert's own card has to read it, and that card has no code.
    if (pathname === "/api/demo/live/seats" && req.method === "GET") {
      const holder = new URL(req.url, "http://localhost").searchParams.get("holder") || "";
      return json(res, 200, { seats: [...seatTokens].map((token) => seatState(token, holder)) });
    }
    if (pathname === "/api/demo/live/result" && req.method === "GET") {
      const submissions = [...seatTokens]
        .filter((token) => state.seats[token]?.submitted)
        .map((token) => ({ token, committed_at: state.seats[token].committedAt }))
        .sort((a, b) => String(a.committed_at).localeCompare(String(b.committed_at)));
      const liveEstimates = submissions.length === seatTokens.size
        ? [...seatTokens].map((token) => liveEstimate(state.seats[token].answer)).filter((value) => value !== null).sort((a, b) => a - b)
        : null;
      return json(res, 200, { submissions, n_seats: seatTokens.size, liveEstimates, analysis: liveEstimates ? liveAnalysis() : null });
    }
    if (pathname === "/api/demo/live/reset" && req.method === "POST") {
      if (!authorized(req)) return json(res, 401, { error: "Demo access code required" });
      state.seats = {};
      persist();
      return json(res, 200, { ok: true, seats: [...seatTokens].map((token) => seatState(token, "")) });
    }
    const seatMatch = /^\/api\/demo\/live\/seats\/([a-z0-9-]{1,48})\/(claim|heartbeat|release|reopen|answer)$/.exec(pathname);
    if (seatMatch && req.method === "POST") {
      const [, token, action] = seatMatch;
      if (!seatTokens.has(token)) return json(res, 404, { error: "No such seat" });
      if (action === "reopen") {
        if (!authorized(req)) return json(res, 401, { error: "Demo access code required" });
        if (state.seats[token]?.submitted) return json(res, 409, { error: "This seat has been answered and stays closed.", ...seatState(token, "") });
        delete state.seats[token];
        persist();
        return json(res, 200, seatState(token, ""));
      }
      const body = await readJson(req);
      const holder = seatHolderFrom(body);
      if (!holder) return json(res, 400, { error: "A seat needs a holder id." });
      const seat = state.seats[token];
      const heldByOther = !!seat?.holder && seat.holder !== holder && (seat.leaseUntil || 0) > Date.now();
      if (action === "release") {
        if (seat && !seat.submitted && (!seat.holder || seat.holder === holder)) { delete state.seats[token]; persist(); }
        return json(res, 200, seatState(token, holder));
      }
      if (seat?.submitted) return json(res, 409, { error: "This seat has already been answered and is closed.", ...seatState(token, holder) });
      if (heldByOther) return json(res, 409, { error: "Someone else has this question open right now. Try another code.", ...seatState(token, holder) });
      if (action === "claim" || action === "heartbeat") {
        state.seats[token] = { ...seat, holder, leaseUntil: Date.now() + LEASE_MS };
        persist();
        return json(res, 200, seatState(token, holder));
      }
      const answer = body.answer;
      if (!answer || !["known", "pseudonym", "anonymous"].includes(answer.mask) || !["estimate", "outside_my_expertise", "not_enough_evidence"].includes(answer.stance) || JSON.stringify(answer).length > 4000) return json(res, 400, { error: "Invalid answer" });
      const salt = randomBytes(16).toString("hex"), committedAt = new Date().toISOString();
      const commitment = createHash("sha256").update(JSON.stringify({ answer, salt })).digest("hex");
      state.seats[token] = { holder, leaseUntil: 0, submitted: true, committedAt, answer, salt, commitment };
      persist();
      return json(res, 200, { commitment, committed_at: committedAt, version: 1, correction_allowed_until: committedAt, message: "Answer confirmed in the shared demo. This seat is now closed.", served_from: "demo", generated_at: committedAt });
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
  process.stdout.write(`Shared demo: http://127.0.0.1:${port}\nDemo access: open to everyone.\n`);
});
