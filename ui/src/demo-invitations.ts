export type DemoInvitation = {
  token: string;
  riskId: string;
  expertId: string;
  issuedAt: string;
  expiresAt: string;
};
export const sharedDemo = import.meta.env.VITE_DEMO_SHARED === "1";
const accessKey = "sealed-signals-shared-access-v1";
export function demoAccessHeaders() { return { "X-Demo-Code": sessionStorage.getItem(accessKey) || "" }; }
export async function loginSharedDemo(code: string) {
  const response = await fetch("/api/demo/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code }) });
  if (!response.ok) throw new Error("That demo access code is not valid.");
  sessionStorage.setItem(accessKey, code);
}
export function clearSharedDemoAccess() { sessionStorage.removeItem(accessKey); }
const key = "sealed-signals-demo-invitations-v1";
const answersKey = "sealed-signals-demo-confirmed-v1";
function all(): DemoInvitation[] {
  try { return JSON.parse(localStorage.getItem(key) || "[]") as DemoInvitation[]; }
  catch { return []; }
}
export function invitationsForRisk(riskId: string) {
  return all().filter((item) => item.riskId === riskId && Date.parse(item.expiresAt) > Date.now());
}
export function getDemoInvitation(token: string) {
  return all().find((item) => item.token === token && Date.parse(item.expiresAt) > Date.now()) || null;
}
export async function loadDemoState(riskId: string): Promise<{ invitations: DemoInvitation[]; confirmedCount: number }> {
  if (!sharedDemo) return { invitations: invitationsForRisk(riskId), confirmedCount: countDemoAnswers(riskId) };
  const response = await fetch("/api/demo/state", { headers: demoAccessHeaders(), cache: "no-store" });
  if (!response.ok) throw new Error("Shared demo state is unavailable. Sign in again.");
  const value = await response.json() as { invitations: DemoInvitation[]; confirmedCount: number };
  return { invitations: value.invitations.filter((item) => item.riskId === riskId), confirmedCount: value.confirmedCount };
}
export async function issueDemoInvitations(riskId: string, expertIds: string[]) {
  if (sharedDemo) {
    const response = await fetch("/api/demo/invitations", { method: "POST", headers: { "Content-Type": "application/json", ...demoAccessHeaders() }, body: JSON.stringify({ riskId, expertIds }) });
    const value = await response.json();
    if (!response.ok) throw new Error(value.error || "Could not issue invitations.");
    return value.invitations as DemoInvitation[];
  }
  const existing = all();
  const next = [...existing];
  for (const expertId of expertIds) {
    if (next.some((item) => item.riskId === riskId && item.expertId === expertId && Date.parse(item.expiresAt) > Date.now())) continue;
    const issuedAt = new Date();
    const expiresAt = new Date(issuedAt.getTime() + 14 * 86400000);
    next.push({ token: `demo-${crypto.randomUUID()}`, riskId, expertId, issuedAt: issuedAt.toISOString(), expiresAt: expiresAt.toISOString() });
  }
  localStorage.setItem(key, JSON.stringify(next));
  return next.filter((item) => item.riskId === riskId && expertIds.includes(item.expertId) && Date.parse(item.expiresAt) > Date.now());
}
export function markDemoAnswered(token: string) {
  const invitation = getDemoInvitation(token);
  if (!invitation) return;
  let saved: Record<string, string> = {};
  try { saved = JSON.parse(localStorage.getItem(answersKey) || "{}"); } catch { /* empty */ }
  localStorage.setItem(answersKey, JSON.stringify({ ...saved, [token]: new Date().toISOString() }));
}
export function countDemoAnswers(riskId: string) {
  let saved: Record<string, string> = {};
  try { saved = JSON.parse(localStorage.getItem(answersKey) || "{}"); } catch { /* empty */ }
  return invitationsForRisk(riskId).filter((item) => !!saved[item.token]).length;
}
export function resetDemoInvitations() {
  if (sharedDemo) return;
  localStorage.removeItem(key);
  localStorage.removeItem(answersKey);
}
