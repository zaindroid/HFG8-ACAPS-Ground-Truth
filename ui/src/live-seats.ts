// The three open seats on the live demo panel, and who holds them.
//
// A seat is a question nobody has been invited to by name: it is claimed by whoever scans its
// code. Three states, and the transitions are the whole point of the mechanism:
//
//   open        nobody holds it; its code works
//   in use      somebody opened it and is still there; a second scanner is refused
//   submitted   an answer was confirmed; the seat is closed for good
//
// A hold is a lease, not a lock, because the common case on a conference floor is someone who
// scans a code, reads the question and puts their phone away. The open card renews its lease
// while it is on screen; once it stops, the seat reopens for the next person. Closing the tab
// releases it at once. A submitted seat never reopens, lease or no lease.
//
// Two backends, same contract. The shared demo server holds the state when the demo is served
// over a tunnel, which is the only way a phone can reach it. Without that server the state is
// per-browser, which is enough for development and honest about its limits in the UI.
import { demoAccessHeaders, sharedDemo } from "./demo-invitations";
import type { Answer } from "./demo-api";
import { estimateFrom, liveSeats } from "./live-panel";

export type SeatState = "open" | "in_use" | "submitted";
export type LiveSeat = {
  token: string;
  state: SeatState;
  /** True when this browser is the holder, so the card does not refuse itself on a reload. */
  mine: boolean;
  committed_at?: string;
};
export type SeatReceipt = {
  commitment: string;
  committed_at: string;
  version: number;
  correction_allowed_until: string;
  message: string;
};
export type LiveSubmission = {
  token: string;
  committed_at: string;
};
export type LiveAnalysis = {
  regions: { region: string; n: number; mean: number | null }[];
  topics: { topic: string; n: number; higher: number | null; lower: number | null }[];
  concerns: { topic: string; n: number }[];
  notes: number;
};
export type LiveSubmissions = { submissions: LiveSubmission[]; liveEstimates: number[] | null; analysis: LiveAnalysis | null };

export const LEASE_MS = 45000;
export const HEARTBEAT_MS = 12000;
const holderKey = "sealed-signals-live-holder-v1";
const seatsKey = "sealed-signals-live-seats-v1";

/** One holder id per tab. In sessionStorage so a reload keeps the seat and a new tab does not. */
export function holderId() {
  let value = sessionStorage.getItem(holderKey);
  if (!value) {
    value = crypto.randomUUID();
    sessionStorage.setItem(holderKey, value);
  }
  return value;
}

type LocalSeat = {
  holder?: string;
  leaseUntil?: number;
  submitted?: boolean;
  committedAt?: string;
  answer?: Answer;
};
function localSeats(): Record<string, LocalSeat> {
  try {
    return JSON.parse(localStorage.getItem(seatsKey) || "{}") as Record<string, LocalSeat>;
  } catch {
    return {};
  }
}
function writeLocalSeats(value: Record<string, LocalSeat>) {
  localStorage.setItem(seatsKey, JSON.stringify(value));
}
function localState(seat: LocalSeat | undefined, holder: string): LiveSeat["state"] {
  if (seat?.submitted) return "submitted";
  if (seat?.holder && seat.holder !== holder && (seat.leaseUntil || 0) > Date.now())
    return "in_use";
  return seat?.holder === holder && (seat.leaseUntil || 0) > Date.now() ? "in_use" : "open";
}

async function post(path: string, body: unknown) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const value = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(value.error || "The shared demo refused this request.");
  return value;
}

/** Every seat's current state. Carries no answers: those stay sealed until the reveal. */
export async function loadSeats(tokens: string[]): Promise<LiveSeat[]> {
  const holder = holderId();
  if (sharedDemo) {
    const response = await fetch(`/api/demo/live/seats?holder=${encodeURIComponent(holder)}`, {
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Seat state is unavailable. Check the demo server.");
    const value = (await response.json()) as { seats: LiveSeat[] };
    return tokens.map(
      (token) =>
        value.seats.find((seat) => seat.token === token) || { token, state: "open", mine: false },
    );
  }
  const seats = localSeats();
  return tokens.map((token) => ({
    token,
    state: localState(seats[token], holder),
    mine: seats[token]?.holder === holder,
    committed_at: seats[token]?.committedAt,
  }));
}

/** Take a seat, or fail with the reason the next person needs to read. */
export async function claimSeat(token: string): Promise<LiveSeat> {
  const holder = holderId();
  if (sharedDemo) return (await post(`/api/demo/live/seats/${token}/claim`, { holder })) as LiveSeat;
  const seats = localSeats();
  const current = seats[token];
  if (current?.submitted)
    throw new Error("This seat has already been answered and is closed.");
  if (current?.holder && current.holder !== holder && (current.leaseUntil || 0) > Date.now())
    throw new Error("Someone else has this question open right now. Try another code.");
  seats[token] = { ...current, holder, leaseUntil: Date.now() + LEASE_MS };
  writeLocalSeats(seats);
  return { token, state: "in_use", mine: true };
}

export async function heartbeatSeat(token: string) {
  const holder = holderId();
  if (sharedDemo) {
    await post(`/api/demo/live/seats/${token}/heartbeat`, { holder });
    return;
  }
  const seats = localSeats();
  if (seats[token]?.holder !== holder || seats[token]?.submitted) return;
  seats[token] = { ...seats[token], leaseUntil: Date.now() + LEASE_MS };
  writeLocalSeats(seats);
}

/**
 * Give the seat back. Called when the card closes, and from the analyst screen when a seat is
 * stuck. `beacon` is for pagehide, where a fetch is cancelled with the document.
 */
export function releaseSeat(token: string, beacon = false) {
  const holder = holderId();
  if (sharedDemo) {
    const body = JSON.stringify({ holder });
    if (beacon && navigator.sendBeacon) {
      navigator.sendBeacon(
        `/api/demo/live/seats/${token}/release`,
        new Blob([body], { type: "application/json" }),
      );
      return;
    }
    void post(`/api/demo/live/seats/${token}/release`, { holder }).catch(() => {
      /* A release that does not land costs one lease period, which is why it is a lease. */
    });
    return;
  }
  const seats = localSeats();
  if (seats[token]?.submitted) return;
  if (seats[token]?.holder && seats[token]?.holder !== holder) return;
  seats[token] = { ...seats[token], holder: undefined, leaseUntil: 0 };
  writeLocalSeats(seats);
}

/** Reopen a seat whoever holds it. The analyst screen offers this for a phone that walked off. */
export async function reopenSeat(token: string) {
  if (sharedDemo) {
    await fetch(`/api/demo/live/seats/${token}/reopen`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...demoAccessHeaders() },
      body: "{}",
    }).then(async (response) => {
      if (!response.ok) throw new Error("The seat could not be reopened.");
    });
    return;
  }
  const seats = localSeats();
  if (seats[token]?.submitted) return;
  seats[token] = {};
  writeLocalSeats(seats);
}

export async function submitSeatAnswer(token: string, answer: Answer): Promise<SeatReceipt> {
  const holder = holderId();
  if (sharedDemo)
    return (await post(`/api/demo/live/seats/${token}/answer`, { holder, answer })) as SeatReceipt;
  const seats = localSeats();
  if (seats[token]?.submitted) throw new Error("This seat has already been answered.");
  if (seats[token]?.holder && seats[token].holder !== holder)
    throw new Error("This seat is held by someone else.");
  const salt = crypto.randomUUID();
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(JSON.stringify({ answer, salt })),
  );
  const commitment = Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
  const committedAt = new Date().toISOString();
  seats[token] = { holder, leaseUntil: 0, submitted: true, committedAt, answer };
  writeLocalSeats(seats);
  return {
    commitment,
    committed_at: committedAt,
    version: 1,
    correction_allowed_until: committedAt,
    message: "Answer confirmed. This seat is now closed.",
  };
}

/** The answers the seats hold. Read by the analyst screen only, and only to aggregate them. */
export async function loadSubmissions(): Promise<LiveSubmissions> {
  if (sharedDemo) {
    const response = await fetch("/api/demo/live/result", {
      headers: demoAccessHeaders(),
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Live panel answers are unavailable. Retry shortly.");
    return (await response.json()) as LiveSubmissions;
  }
  const seats = localSeats();
  const submissions = Object.entries(seats)
    .filter(([, seat]) => seat.submitted && seat.answer)
    .map(([token, seat]) => ({
      token,
      committed_at: seat.committedAt || new Date().toISOString(),
    }))
    .sort((a, b) => a.committed_at.localeCompare(b.committed_at));
  const liveEstimates = submissions.length === liveSeats.length
    ? submissions.map((item) => estimateFrom(seats[item.token].answer?.probability ?? null, seats[item.token].answer?.likelihood_word)).filter((value): value is number => value !== null).sort((a, b) => a - b)
    : null;
  return { submissions, liveEstimates, analysis: null };
}

/** Clear every seat. Part of the demo reset, so the next run starts with three open codes. */
export async function resetSeats() {
  if (sharedDemo) {
    await fetch("/api/demo/live/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...demoAccessHeaders() },
      body: "{}",
    }).catch(() => {
      /* Reported by the roster when the shared server is unreachable. */
    });
    return;
  }
  localStorage.removeItem(seatsKey);
}
