export type Honesty = {
  relayed_share?: number;
  reidentification_note?: string;
  channel_mix?: Record<string, number>;
  n: number;
  agreement: number;
  spread: number[];
  coverage_gaps: string[];
  claims_corroborated: number;
  claims_total: number;
  claims_in_verification_queue: number;
  misses: number;
  decision_use: { what_decision: string; for_whom: string; by_when: string };
  panel_view_rejected: boolean;
  analyst_rationale: string | null;
  panel_hit_rate: number | null;
  caveat: string;
};
export type Integrity = {
  pulse_id?: string;
  integrity_notes: { kind: string; text: string; evidence: string }[];
};
export type TrackRecord = {
  reported: boolean;
  n_resolved: number;
  mean_brier?: number;
  hit_rate?: number | null;
  moved_before_acaps?: number;
  reliability_weight?: number;
  on_theme_share?: number;
  note?: string;
};
export type Match = {
  risk_id: string;
  n_approved_available?: number;
  experts: {
    pseudonym: string;
    match: number;
    geo_tags: string[];
    theme_tags: string[];
    region?: string;
    affiliation_tag?: string;
    languages?: string[];
    years_experience?: number;
    track_record?: TrackRecord;
  }[];
  composition: {
    max_per_affiliation: number;
    ok: boolean;
    geo_spread: string[];
    theme_cover: string[];
    gaps: string[];
  };
};
export type RadarStatus = {
  source?: "csv" | "acaps-api";
  fetched_at?: string;
  n_risks?: number;
  risk_list?: {
    source: string;
    fetched_at: string;
    n: number;
    api_n?: number;
    api_last_update?: string;
  };
  editions?: {
    dataset: string;
    month: string;
    source: "api" | "cache";
    fetched_at: string;
  }[];
  token_present?: boolean;
  live_available?: boolean;
};
export type Application = {
  geo_tags: string[];
  theme_tags: string[];
  affiliation_tag: string;
  languages: string[];
  channel: string;
};
export type Approval = {
  expert_id?: string;
  status: string;
  approved_by?: string[];
  approvals?: number;
  credential?: string;
};
