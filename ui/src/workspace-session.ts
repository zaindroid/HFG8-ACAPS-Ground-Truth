export const workspaceSessionKey = "sealed-signals-demo-session";
const sessionDuration = 8 * 60 * 60 * 1000;

// Presentation gate only. This is not an authentication token or server authorization.
export function hasWorkspaceSession() {
  try {
    const session = JSON.parse(
      sessionStorage.getItem(workspaceSessionKey) || "null",
    );
    return (
      session?.kind === "demo" &&
      Number.isFinite(session.expiresAt) &&
      session.expiresAt > Date.now()
    );
  } catch {
    return false;
  }
}
export function startDemoSession() {
  sessionStorage.setItem(
    workspaceSessionKey,
    JSON.stringify({ kind: "demo", expiresAt: Date.now() + sessionDuration }),
  );
}
export function endDemoSession() {
  sessionStorage.removeItem(workspaceSessionKey);
}
export function workspaceDestination(value: string | null) {
  if (
    !value ||
    !/^\/(workspace|alerts|radar|expert|calibration|desk|ledger|stage|apply|committee|e|me)(\/|\?|$)/.test(
      value,
    ) ||
    /[\\\r\n]/.test(value)
  )
    return "/workspace";
  return value;
}
