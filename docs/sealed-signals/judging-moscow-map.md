# The organisers' MoSCoW rows, mapped to the product

Lane C. Revised for master prompt v3.4 (8 Nov). `judging-checklist.md` maps the jury sheet's six weighted criteria (A to F) to slides and sentences. This page does the other half: the organisers' own MoSCoW rows from `docs/evaluation-criteria.md` to the screen or file where each is shown. Code paths are in `README.md` section 3 and `AGENTS.md`. Status: covered, partial (works, a limit is stated), gap.

| Row | Where it is shown | Status |
|---|---|---|
| Must: easy to use | `/e/:token`: event first, one required tap, about a minute, no account, any channel; a plain reply or a voice note also counts | covered; channel preferences are hypotheses until the pilot |
| Must: expert-controlled anonymity | Mask picker per answer with no default: named to ACAPS, nickname to peers, no identity kept. The limit is stated on the screen: pseudonymised, not anonymous from ACAPS. | covered |
| Must: public anonymity | Public ledger and every public aggregate: n of 5 or more, never an individual. Disclosure rule, not an anonymity guarantee; the honesty box says a distinctive reason may identify its author to colleagues. | covered |
| Should: sustained engagement | Thank-you built from the record after the reveal and on resolution; one pulse per expert per 7 days; STOP by one word; no streaks | covered; week-8 participation measured in the pilot |
| Should: short contributions | One screen, one required input | covered |
| Should: small trusted groups | Eight per panel, committee-vetted, at most 3 per affiliation type | covered |
| Should not: engagement metrics as the goal | None stored or shown; v3.4 removed response-time and edit-count measures | covered |
| Should not: chatbot feel | The expert never talks to a model; AI is analyst-side and model-optional | covered |
| Could: super-estimator scoreboard | By design none public: forecasts scored at panel level; individual calibration private, consent-gated, seen by the expert first | partial, by decision (README section 3) |
| Could: agreement and disagreement, including by geography | Desk reveal view (agreement, disagreement, missing evidence, rationale); regions in the country scan | covered |
| Could: mobile and low bandwidth | Expert screen payload under 50 KB; SMS and voice channels | partial: the 50 KB payload and the timing on two phones are measured at the Sunday freeze and written to `docs/evidence/phones.md`; until then they are targets |
| Could: multilingual (French) | English and French parsing of replies | partial: the card itself is English |
| Can: AI behind the scenes | Investigator, Skeptic, Judge behind `FF_AGENTS`; deterministic template by default | covered |
