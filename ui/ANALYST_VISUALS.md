# Analyst visual walkthrough

The local `/desk` has a **Simulate arrivals** action. Responses arrive one by one, can be paused, resumed or restarted, and stay sealed until an explicit reveal. Region dots and expertise bars describe the selected roster; a disclosure lists pseudonyms, locations and themes. The mock replay uses the matching fixture's roster order, not a claimed identity-to-answer association. Live mode shows selected panel composition without assigning anonymous response arrivals to profiles.

After replay reveal, the analyst can step through:

1. The distribution, equal-weight mean and spread.
2. Regional group views above the three-estimate display floor, panel expertise and selection gaps.
3. Corroborated versus unchecked raised themes, with source-origin labels.
4. A draft preview with supporting numbers and expandable full wording.

The replay writes no answers, approvals, or ledger records. **Return to current round** restores the existing desk view. Accept, Edit and Reject remain on the current round. Evidence-review percentages are expandable and labelled as checks of the draft rather than forecast confidence. `n_estimates` is used for the number of numeric forecasts where provided, keeping abstentions distinct from estimates.

Location dots, expertise bars and transitions use short motion and honour reduced-motion preferences. The severity chart moves its marked point from the previous edition while keeping that previous point visible.

The current backend metric named `moved_before_acaps` counts correct classifications when the mapped ACAPS band was wrong; the panel table labels this **Correct when band missed**, avoiding a timing claim.

Validation: mock build, browser replay checks at phone/desktop/projector sizes, pause/resume, reveal gating, the four review steps, current-round restoration, accessibility, local page JavaScript errors and horizontal overflow. Existing sample/journey checks and targeted API checks cover the surrounding flow. This does not implement v3.3 Reach, seed questions, private pattern reports or hardening services.

## Flow corrections after browser review

The last analysis step has an active handoff to the actual decision panel. The forecast-versus-ACAPS chart stays visible at every analysis step. A compact response counter replaces the flip cards; the actual distribution appears in the forecast chart. Country-level panel locations are mapped; region details remain in the roster. Specialties have separate muted colours with labels and counts.

The main simulation toolbar has only the applicable controls; the expert-card link and redundant replay/load buttons were removed from that toolbar. Question context is visible by default, while editing resolution rules is a separate disclosure. Severity uses a moving marker when it enters view and an explicit replay control; reduced-motion settings suppress motion. The original draft and source evidence remain inspectable.

## Balanced desk layout

Responses occupy a compact full-width strip. The primary forecast-versus-ACAPS graphic and geographic/expertise coverage sit alongside each other. Observed severity has its own full-width evidence row. Draft interpretation and analyst decision controls share the next row, without repeating the forecast and severity tiles. Secondary experimental output is expandable rather than a headline statistic.

Question, Panel details, Review notes, Method and Outcome are full-width context tabs, with keyboard navigation. Tabs preserve mounted form state. On phones, the layout becomes one column. The main estimate remains an equal-weight mean; composition and evidence checks inform review and are not presented as mathematical bias correction.

Each mock desk visit starts with zero received responses, including when a previous decision is saved. Simulate arrivals increments the response count, completion percentage and coverage; saved ledger decisions are preserved. Forecasts stay sealed until reveal. Historical monthly severity readings do not change with arrivals.

The Forecast brief uses labelled icon tabs, a prominent exact event definition and separate location, deadline and resolution-source cards. The analyst confirmation status stays visible, and contract editing remains available below the brief. Dates are displayed in readable form without changing their stored values.

The arrival map starts at a neutral world view with no markers or highlighted panel countries. Only received locations enter its framing; the camera pans and zooms over 450 ms, preserving marker and label sizes. Reduced motion makes camera changes immediate. Closing the simulation returns to the zero-response map.

A separate **Simulation forecast** shows an illustrative, unlinked sequence of eight estimates and its running equal-weight mean. The marker can move up or down at each arrival, ending at 69% with a 30–90% range. This preview neither reads individual sealed answers nor writes to the API, ledger or saved group result. Historical severity remains separately labelled supporting evidence. Ledger labels distinguish observed event outcomes from on-demand receipt checks.
