import { api } from "./service";
import { mock } from "./api";
import alerts from "../../fixtures/GET_alerts.json";
import current from "../../fixtures/POST_alerts_run_response.json";
import replay from "../../fixtures/POST_alerts_replay_response.json";
import crisis from "../../fixtures/GET_crises_TCD005.json";

export type Shift = Omit<
  (typeof alerts.events)[number],
  | "pulse_id"
  | "status"
  | "risk_id"
  | "before"
  | "after"
  | "components"
  | "reliability"
  | "adm1"
  | "connected_crises"
  | "note"
  | "access"
> & {
  pulse_id: string | null;
  status: string;
  risk_id: string | null;
  before: number | null;
  after: number | null;
  components?: Record<string, number[]>;
  reliability?: string;
  adm1?: string[];
  connected_crises?: string[];
  // Both are null on a freshly run event and filled in later: a dismissal writes the note, and
  // access is absent for crises the access edition does not cover.
  note?: string | null;
  access?: (number | null)[];
};
export type Crisis = typeof crisis;
type Run = {
  events: Shift[];
  month_from: string;
  month_to: string;
  n_crises: number;
  note?: string;
};
const key = "sealed-signals-alert-decisions-v1";
const linksKey = "sealed-signals-risk-links-v1";
function links(): Record<string, string> {
  try {
    return JSON.parse(sessionStorage.getItem(linksKey) || "{}");
  } catch {
    return {};
  }
}
function stored(): Record<
  string,
  { status: string; pulse_id: string | null; note?: string }
> {
  try {
    return JSON.parse(sessionStorage.getItem(key) || "{}");
  } catch {
    return {};
  }
}
function withDecisions(events: Shift[]) {
  const saved = stored();
  const linked = links();
  return events.map((e) => ({
    ...e,
    ...saved[e.id],
    risk_id:
      Object.entries(linked).find(([, id]) => id === e.crisis_id)?.[0] ||
      (e.risk_id && linked[e.risk_id] && linked[e.risk_id] !== e.crisis_id
        ? null
        : e.risk_id),
  }));
}
function save(event: Shift, note?: string) {
  sessionStorage.setItem(
    key,
    JSON.stringify({
      ...stored(),
      [event.id]: { status: event.status, pulse_id: event.pulse_id, note },
    }),
  );
  return event;
}
export const alertService = {
  list: async (): Promise<Shift[]> =>
    mock
      ? withDecisions(alerts.events)
      : (await api<{ events: Shift[] }>("/alerts")).events,
  run: async (replaying: boolean): Promise<Run> =>
    mock
      ? {
          ...(replaying ? replay : current),
          events: withDecisions((replaying ? replay : current).events),
        }
      : api<Run>(
          replaying ? "/alerts/replay" : "/alerts/run",
          replaying ? { month_from: "Mar2026", month_to: "Apr2026" } : {},
        ),
  crisis: async (id: string): Promise<Crisis> => {
    if (mock) {
      if (id !== crisis.crisis_id)
        throw new Error("This crisis is not available.");
      const linked = links();
      return {
        ...crisis,
        linked_risks: [
          ...new Set([
            ...crisis.linked_risks.filter(
              (id) => !linked[id] || linked[id] === crisis.crisis_id,
            ),
            ...Object.keys(linked).filter(
              (id) => linked[id] === crisis.crisis_id,
            ),
          ]),
        ],
      };
    }
    return api<Crisis>(`/crises/${encodeURIComponent(id)}`);
  },
  pulse: async (event: Shift): Promise<Shift> =>
    mock
      ? save({ ...event, status: "pulsed", pulse_id: "P-0001" })
      : api<Shift>(`/alerts/${encodeURIComponent(event.id)}/pulse`, {}),
  dismiss: async (event: Shift, note: string): Promise<Shift> =>
    mock
      ? save({ ...event, status: "dismissed" }, note)
      : api<Shift>(`/alerts/${encodeURIComponent(event.id)}/dismiss`, { note }),
  linkRisk: async (riskId: string, crisisId: string): Promise<Crisis> => {
    if (mock) {
      if (crisisId !== crisis.crisis_id)
        throw new Error("This crisis is not available.");
      sessionStorage.setItem(
        linksKey,
        JSON.stringify({ ...links(), [riskId]: crisisId }),
      );
      return {
        ...crisis,
        linked_risks: [...new Set([...crisis.linked_risks, riskId])],
      };
    }
    await api<unknown>(`/risks/${encodeURIComponent(riskId)}/link`, {
      crisis_id: crisisId,
    });
    const record = await api<Crisis>(`/crises/${encodeURIComponent(crisisId)}`);
    if (record.crisis_id !== crisisId || !record.linked_risks?.includes(riskId))
      throw new Error(
        "The API has not confirmed this risk link in the crisis record. Refresh before trying again.",
      );
    return record;
  },
};
