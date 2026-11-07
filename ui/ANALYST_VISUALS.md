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
