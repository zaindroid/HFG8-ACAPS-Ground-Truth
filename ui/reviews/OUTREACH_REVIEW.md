# Critical review of the 7 November outreach proposal

This reviews the pasted Version 1 proposal, not an independently evaluated production system. Scores below are design judgements, not measured response rates. The pasted copy has no numbered section headings, so the overclaim audit identifies mechanisms and phrases instead.

## Verdict

Keep the personal outreach, precise forecast, independent first response, abstention, analyst accountability and feedback. Cut the number of measurements substantially. The proposal combines a useful consultation service with an insufficiently validated individual assessment programme. Calling that assessment quiet, private or a sentence rather than a score does not resolve the trust problem.

The statements limiting commitment proofs and anonymity are welcome. The document then contradicts some of them in its storage, measurement and erasure promises. Make those claims consistent before a pilot.

## Answers to the eleven questions

### 1. Channels

Audit the actual panel's access and preferences first. Age, seniority and institution do not establish channel preference. Neither email universality nor near-universal WhatsApp should be assumed.

| Option | Pilot judgement |
|---|---|
| 1. IVR | Potentially useful where participants request it. Test a scheduled human call first; recording, language, tariffs and gateway reliability make automated voice a substantial integration. No evidence here establishes the largest coverage gain. |
| 2. Missed-call callback | Worth testing with a local partner where familiar. Verify local and roaming tariffs before promising zero cost. |
| 3. USSD | Defer unless the recruited panel needs it. Operator agreements, short sessions and country-specific behaviour matter. A fixed character limit and a final 10% coverage gain are unsupported. |
| 4. Teams/Slack | Choose only if the participating agency permits the integration. Existing organisational Teams access does not imply external adaptive-card access. |
| 5. Telegram | A preference-driven alternative, not a required additional build. |
| 6. Email links | Best initial route for an email-first recruited panel. Open a confirmation screen; do not commit an answer on a GET request, which automated link inspection or accidental opening could trigger. |
| 7. Calendar | Offer an optional reminder. A standing ten-minute meeting conflicts with the promised minute-long request. |
| 8. Liaison | Valuable for inclusion, with direct consent, private elicitation and provenance. Record that the answer was relayed and allow the expert to confirm it. Translation and intermediary influence need attention. |
| 9. Paper/photo | Manual fallback where requested. OCR needs human confirmation; an image may expose names, handwriting or other context. |

Missing: a plain-text reply to the existing analyst conversation and a prearranged human call without recording. Both may be better first tests than building another platform. Add explicit handling for forwarded invitations, duplicate submissions, expired links and corrections across channels.

### 2. Card

Put the exact future event, geography, threshold and deadline first. An observed severity change is context, not the forecast question. Showing the largest severity increase before elicitation also provides an anchor even when the ACAPS probability band is hidden.

Use one likelihood input with explicit percentage ranges for the words; retain optional precise percentages without silently treating a word as an exact point. Drop the mandatory panel prediction, separate confidence word, seed and first-use mask selection from the core response. Keep abstention and optional reason/source. Explain visibility before submission. Submit explicitly and allow an auditable correction before the deadline.

Intervals are suitable for some uncertain quantities but need a clearly specified target and instruction. They are not a universal replacement for a probability of a binary event. Frequency wording can be offered when a defensible reference class exists. Natural-frequency research about Bayesian inference does not establish that imagining ten similar crises improves this forecasting task. [Gigerenzer and Hoffrage, discussion of frequency representations](https://pure.mpg.de/rest/items/item_2101266_7/component/file_2563079/content).

Treat one minute and low bandwidth as measured performance targets. Do not forbid scrolling at the expense of zoom, translations, accessibility or a complete question. Five taps is incompatible with the proposed mandatory items plus first-use choices.

### 3. Seeds and disclosure

As written, it is a test described as something other than a test. General first-contact disclosure is inadequate for a hidden individual report to a vetting committee. Offer a separate optional calibration activity. Suggested wording: “Optional calibration questions help us evaluate this forecasting process. We will explain how answers are scored and who can see them. Taking part or declining will not affect your panel membership.” This promise requires actual governance and enforcement.

Do not label a categorical recall item about an ACAPS report as Cooke calibration. That model elicits distributions for relevant calibration quantities with subsequently assessable realizations and evaluates statistical accuracy and information. The proposed item may primarily measure access to ACAPS publications. [Colson and Cooke](https://pureportal.strath.ac.uk/files-asset/72633039/Colson_Cooke_REEP_2018_Expert_elicitation_using_the_classical_model_to_validate_experts_judgments.pdf).

### 4. Knowledge gap and sample size

The measure is not sound as defined. Three confidence words and categorical accuracy have no defined common scale. A difference between them is not an interpretable knowledge gap. Topic selection, difficulty, language and publication access confound the result.

There is no universal minimum that validates this construct. A weekly three-month pilot with a seed every third pulse yields roughly four seeds per person: insufficient for an individual characterisation. For exploratory factual-task calibration, collect numeric confidence in correctness on comparable items and show uncertainty. Twenty comparable observations could be an operational floor for descriptive review, not a validated threshold; even substantially larger samples may be too weak for individual decisions. Set sample requirements through a precision/power analysis, account for correlated questions, and withhold committee labels in this pilot.

Brier is the mean of `(forecast probability − binary outcome)²`. It is not “Brier against stated confidence.” Calibration requires repeated probability/outcome comparisons; discrimination and outcome difficulty also affect Brier. An ordinal confidence word cannot supply this calculation.

### 5. Fictitious report

Remove it from this pilot, including the feature flag. A fabricated operational reference introduces deception, reputational risk and possible downstream repetition of misinformation. An organisation's consent is not the participant's informed consent. If ever researched, use a separately reviewed study with appropriate participant information and debriefing, not routine humanitarian consultation.

### 6. Round two and meta-knowledge

Keep an optional second round if the analyst needs deliberation. Preserve the independent answer, show anonymised reasoning as well as the distribution, allow “keep,” and record reasons for revision. Movement may be rational learning; it does not establish anchoring susceptibility.

Keep meta-knowledge outside the required quick response until its burden and usefulness are tested. “Most of the panel will say unlikely/even/likely” is not the numerical prediction of a defined answer frequency used by the current binary surprisingly-popular experiment. Predicting peers does not itself prove subject expertise. This method compares actual and predicted answer prevalence under assumptions; it is not an individual accreditation tool. [Prelec, Seung and McCoy](https://marketing.wharton.upenn.edu/wp-content/uploads/2017/08/11-02-2017-McCoy-John-PAPER.pdf).

### 7. Options 12–23

Priority order: **15 → 14 → a properly facilitated 16**. Use a trigger pick when it serves a real decision, an optional counterargument, then deliberate discussion when justified.

| Option | Decision |
|---|---|
| 12. Pairwise | Optional prioritisation task only. Different questions and time horizons make apparent rankings hard to interpret. Not a knowledge seed without a defensible answer key. |
| 13. Bootstrapping | Research only. A second self-estimate is correlated, improvement is not guaranteed, and it is not a test–retest reliability measure. |
| 14. Opposite | Useful optional prompt. Avoid asserting that it has removed confirmation bias. |
| 15. Triggers | Strong practical candidate; agree the decision use first. |
| 16. IDEA | Align the process if using its name. A histogram and revision button alone omit investigation and facilitated discussion. |
| 17. Cooke information | Separate research activity requiring appropriate interval tasks and enough calibration items. Narrowness alone is not quality. |
| 18. Channel consistency | Usability study only. Different pulses also differ in events, information and timing; the difference cannot be attributed to channel. |
| 19. Interval coverage | Appropriate for repeated realized quantities with defined intervals. Not directly applicable to intervals around an event probability whose realization is only 0 or 1. |
| 20. Known unknowns | Measures familiarity with the institution's evidence catalogue, not general awareness or contextual expertise. Optional onboarding aid. |
| 21. Affiliation | Descriptive composition review with adequate group sizes. Differences are not evidence that one affiliation is biased; role and information access differ. |
| 22. News salience | A timestamp association cannot distinguish irrational headline influence from relevant new information. Do not present causal labels. |
| 23. Straight-lining | Constant answers across different events may be reasonable. Inspect process issues without labelling acquiescence. |

### 8. Participation and attrition

The most likely design risks are repeated irrelevant questions, expired or distrusted links, uncertain confidentiality, no useful feedback, inaccurate translation, and perceived covert evaluation. These are hypotheses to test with participants, not conclusions about sixty-year-olds.

Use a verified human sender and working reply address; make “why you,” time horizon and visibility clear. Let experts set timing and cadence themselves. Support larger text, screen readers, weak connections, saving/retrying and corrections. Avoid automatically quoting a sensitive place or identifiable note in a message visible on a lock screen. Do not promise their suggestion was used unless the analyst explicitly records that attribution.

### 9. Humanitarian data responsibility

Require purpose-specific assessment of necessity, access, retention, provider processing and potential harm. Aggregated information can remain sensitive in humanitarian contexts; removing names does not settle the issue. [OCHA Centre for Humanitarian Data](https://centre.humdata.org/guidance-note-responsible-approaches-to-data-sharing/).

Resolve these contradictions:

- Anonymous “without identity at all” conflicts with per-expert links, reminders, personalised feedback and longitudinal profiles unless a specified separation mechanism supports the claim.
- Deleting the registry does not necessarily anonymise linked answers, pseudonyms, prose or committee reports. Pseudonymisation remains distinct from anonymisation. [EDPB](https://www.edpb.europa.eu/topics/ai-and-technology/anonymisation-pseudonymisation_en).
- Five responses is a disclosure threshold, not proof of formal k-anonymity or safety. Location, affiliation, expertise and quotes can identify small groups or individuals.
- “No location beyond time zone” contradicts geographic panel matching and the location dashboard. Specify broad professional coverage versus current physical location and minimise both.
- “Legitimate interest plus consent” is not a complete lawful-basis assessment. Establish basis, purposes and rights handling with the organisation's privacy lead rather than promising erasure by registry deletion.
- Encryption algorithm names do not establish deployed protection, end-to-end secrecy or sound key management. State what is implemented and tested. A key-encapsulation mechanism is not by itself an at-rest storage design.
- Audio deletion needs coverage of provider copies, backups and transcripts; transcription confirmation must come from the participant. Free text needs a minimisation and redaction procedure.
- A private committee report about a person's performance is still consequential profiling, even without a numeric score. Require transparency, correction and restricted secondary use.

### 10. Overclaim audit

These are the substantive unsupported promises and construct substitutions in the pasted sections and candidate list. They should become hypotheses, bounded descriptions or deletions:

| Claim or implication | Correction |
|---|---|
| Existing conversations leave no record or timing | Emails already provide both. The tool structures and standardises records. |
| Quietly learn how reliable each answer is | These mechanisms supply partial signals, not an answer-level truth or reliability test. |
| Universal email / near-universal WhatsApp / voice preference by age | Verify with this recruited panel. |
| No signup ever, all basic phones, one browser card | Basic phones may not support a browser; provide a genuine non-web route. |
| Under a minute, five taps, no scrolling, 50 KB, 2G | Benchmark the complete interaction and payload on actual devices. They are targets, not established facts. |
| Reveal once five arrive | Early reveal can privilege fast responders. Use a defined deadline or an explicit, auditable early-close rule; keep late respondents blind until submission. |
| “6 of 8 answered” reminder | Adds conformity pressure and can expose participation in a tiny panel. Use a neutral reminder. |
| 08:00 and no Friday afternoon | Not a universal availability rule; respect local weekends, shifts and participant preference. |
| Seed accuracy equals actual knowledge | At most accuracy on the sampled tasks, confounded by access, language and difficulty. |
| Confidence equals perceived knowledge; their gap measures knowledge gap | Undefined scales and unvalidated construct. |
| Panel prediction identifies informed experts without a track record | Not guaranteed by the aggregation method or this three-category item. |
| Different format two pulses later measures reliability | Real information and event probability may have changed. |
| Fast extremes or edits indicate concern | Timing and editing have many legitimate causes; optional accessibility and interruption effects matter. Minimise collection. |
| Every forecast scored once ACAPS resolves it | Requires a frozen, resolvable contract and credible adjudication; some outcomes remain disputed or unresolvable. |
| Brier against confidence measures overconfidence | Incorrect definition. |
| Round-two shift measures anchoring susceptibility | Confounds social influence with legitimate learning. |
| Saw/read/heard mix establishes reliability | Provenance categories do not establish truth or independence. |
| Acknowledging a fabricated report measures overclaiming | Could reflect misunderstanding, a similarly named report or response error; unsuitable as an operational personal label. |
| Scores are for forecasts, not people | Per-pseudonym committee reports explicitly characterise people. State their actual use. |
| IVR cheap and largest coverage gain | Cost and effect are untested and local. |
| Missed calls zero cost; USSD any phone / 182 chars / last 10% | Depend on country, operator, tariff, device and measured unmet need. |
| Teams right for UN / email-first majority / Telegram coverage | Recruitment assumptions, not demonstrated reach. |
| One-click email records a valid deliberate answer | Needs explicit confirmation and protection from automated link visits. |
| Paper rare and cheap | Need and staffing unknown; includes confirmation and privacy costs. |
| Four-step intervals reduce overconfidence here for two taps | Task-dependent; input and instruction burden is understated. |
| Frequencies judged better by most people | Overgeneralises Bayesian reasoning research to this forecast task. |
| Relative judgements easier and more consistent | Not established for these participants and non-comparable risks. |
| Average of two self-estimates better than either | Possible empirical benefit, not a guarantee; not independent information. |
| Consider-opposite reduces bias in this implementation | Requires testing; a prompt is not proof of mitigation. |
| Trigger picks natural; feeds triggers directly | Verify relevance and analyst interpretation; not automatic evidence. |
| Already loosely follow IDEA | A partial resemblance is not implementation of the protocol. |
| Interval narrowness and coverage establish useful weighting | Require proper calibration, target relevance and validation; avoid rewarding unjustified precision. |
| Cross-channel differences measure reliability/channel quality | Confounded without an appropriate study. |
| Known-unknowns measure evidence awareness | More narrowly, familiarity with selected ACAPS catalogue items. |
| Affiliation differences show bias | Describe differences without inferring a causal bias. |
| Timing identifies headlines rather than field evidence | Cannot infer that distinction from timing and text matches. |
| Repeated answers establish acquiescence | Not across different forecast questions. |
| Named sender, membership, reciprocity or charter guarantee engagement | Sensible hypotheses; measure their effects and honour consent. A photo is optional, not a trust mechanism by itself. |
| Parser accepts five languages | Requires tested translations, uncertainty terms, number formats and ambiguity handling. Preserve originals and seek confirmation. |
| Registry encryption, identity-free answers, erasure and n ≥ 5 settle privacy | Each needs a precise threat model, deployed evidence and governance; see question 9. |

Source mix and abstention counts themselves are legitimate descriptive measures if their denominators, missingness and limits are shown. They become overclaims when used to infer competence or independence.

### 11. Three pilot priorities

1. **A precise, short, accessible forecast request:** one likelihood input, optional reason, real abstention, preferred language/channel and an explicit deadline. Test with actual panel members.
2. **Trustworthy independent elicitation:** no displayed probability anchor before submission, clear visibility, neutral reminders, auditable revisions and a consistent reveal policy. Keep personal assessment and deception out of the consultation.
3. **Close the loop and evaluate honestly:** an analyst-confirmed decision summary, participant feedback, observed completion/response rates, and pre-specified outcome scoring. A three-month usability pilot cannot validate six-month forecasts that have not resolved. Keep usability and predictive-validation conclusions separate.

## Scores for the proposal as written

| Dimension | Score | Reason |
|---|---:|---|
| Response-rate design | 6/10 | Good personal outreach and feedback; too many questions, brittle timing and untested channel assumptions. No numerical response-rate forecast is justified. |
| Elicited judgement | 6/10 | Independent first response and abstention help, but question specification, initial evidence anchoring and probability mappings need repair. |
| Fairness and trust | 4/10 | Privacy caveats help; covert individual assessment, deceptive foils and contradictory anonymity promises undermine them. |
| Measurement validity | 3/10 | Brier on properly resolved forecasts is useful; knowledge gap, susceptibility and channel-reliability interpretations are not validated. |

## Implications for the current frontend

Show the expert forecast, ACAPS band, observed severity, coverage and source checks as separate views with explicit meanings. Do not imply the primary calculation blends all these into a sophisticated bias-corrected score: the inspected backend uses an equal-weight mean as its primary estimate. Additional checks inform the analyst; they do not establish the absence of bias. Keep experimental estimates secondary. Simplify the dashboard around comparison, coverage, evidence and the analyst's decision; do not add personal competence badges or diagnostic labels from this proposal.
