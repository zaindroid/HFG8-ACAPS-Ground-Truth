import chad from "../../fixtures/GET_risks_R1043.json";
import panel from "../../fixtures/GET_panels_match.json";

export type DemoRisk = {
  risk_id: string;
  country: string;
  country_iso: string;
  title: string;
  short: string;
  probability_acaps: string;
  level: string;
  status: string;
  source: string;
};

// R1043 is the active challenge case. The other rows are active records in
// data/acaps-risk-list.csv, included to make risk selection realistic.
export const demoRisks: DemoRisk[] = [
  { risk_id: chad.risk_id, country: chad.country, country_iso: chad.country_iso, title: chad.title, short: "Cross-border insecurity in eastern Chad", probability_acaps: chad.probability_acaps, level: chad.level, status: chad.status, source: "Challenge case" },
  { risk_id: "R0604", country: "Afghanistan", country_iso: "AFG", title: "US funding suspension worsen the healthcare and food security situation in Afghanistan", short: "Funding cuts affect health and food security", probability_acaps: "High", level: "High", status: "Active", source: "ACAPS Risk Radar export" },
  { risk_id: "R0480", country: "Ukraine", country_iso: "UKR", title: "The targeting of structures supporting Ukrainian nuclear power plants’ safety causes more extensive power outages and potential nuclear incidents, leading to immediate and long-term radioactive-related health issues and environmental contamination", short: "Nuclear plant safety and outages", probability_acaps: "Low", level: "Medium", status: "Active", source: "ACAPS Risk Radar export" },
  { risk_id: "R0602", country: "South Sudan", country_iso: "SSD", title: "Violence in Nasir county, Upper Nile state, sparks civil war in South Sudan, forcing mass displacement and worsening humanitarian crisis", short: "Violence and displacement in Upper Nile", probability_acaps: "Medium", level: "Medium", status: "Active", source: "ACAPS Risk Radar export" },
];

export type DemoExpert = (typeof panel.experts)[number];
export const demoExperts = panel.experts;
export function expertsForRisk(risk: DemoRisk): DemoExpert[] {
  if (risk.risk_id === "R1043") return demoExperts;
  return demoExperts.filter((expert) => expert.geo_tags.includes(risk.country_iso));
}
