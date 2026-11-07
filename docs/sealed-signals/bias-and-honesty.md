# Integrity layer and honesty

Lane C. Revised for master prompt v3.2 (7 Nov). Maps each design element in master prompt sections 6 and 6a to its research source, says what the source does and does not support, and records the mentor's words on honesty.

v3 principle: the integrity layer **describes, it does not diagnose**. No automatic penalty, no automatic switch of the number, no verdict colours. The analyst reads the notes and decides.

Verification: each citation was looked up on 6-7 Nov 2026 (bibliographic record or abstract, through search). We did not read every full paper. Status: **verified** (record found and matches), **corrected** (found, but the wording we were given was wrong), **design** (our own choice, no source claimed).

## 1. The mentor's frame

- "We will get things wrong, like a prediction market; the point is honesty about it." [mentor, 6 Nov]
- The app is one validation layer among others. Products never change automatically. ACAPS must minimise bias and state limitations and what fed into each product. [mentor]
- His open question: a panel could lean one way, or be packed to steer funding. [mentor]

Our answer in one line: we cannot remove bias, so we describe it to the analyst, state our limits in public in the honesty box, and let the analyst decide.

## 2. Element by element

| # | Design element (v3) | What it does | Research source | Status |
|---|---|---|---|---|
| 1 | Rating hidden until after submission | Round 1 does not show the ACAPS rating. We avoid displaying the anchor. We cannot guarantee independent judgement. | Tversky and Kahneman 1974 (anchoring); Dalkey and Helmer 1963 (Delphi, independent first round) | verified |
| 2 | Round 2 optional and asynchronous | Opens only with new evidence or real disagreement. The shift from round 1 is logged as an integrity note. | Dalkey and Helmer 1963 | verified |
| 3 | Accuracy prompt and source tag | One line asks whether the point was seen, read or heard | Pennycook et al. 2021 (accuracy nudge); the source tag itself is ours | verified / design |
| 4 | Equal-weight mean as the primary number | Plain average of probabilities, with min, max, IQR and minority reasons beside it | Simple averaging is the standard baseline in the forecasting literature; our choice for the pilot | design |
| 5 | Weighted mean (secondary) | Weights start equal, shrink toward the prior, capped at 2 times the median. No extremizing. | Calibrated-weighting practice in Mellers et al. 2015; shrinkage and cap are ours | verified / design |
| 6 | Surprisingly popular (experiment, labelled) | Compares the share who say yes with the panel's guess of that share, with a fixed question | Prelec, Seung and McCoy 2017; Palley and Satopaa 2023 for peer-prediction weighting | verified, one citation corrected |
| 7 | Scoring | Brier per forecast on resolved questions, after a frozen question contract. Committee-side. Stances "outside my expertise" and "not enough evidence" and all free text are never scored. | Brier 1950; Tetlock 2005; Tetlock and Gardner 2015 | verified |
| 8 | Convergence note (herding) | Notes when round 2 answers move toward the mean with no new reasons | Lorenz et al. 2011 | verified |
| 9 | Co-movement note (independence) | Notes pairs that agree beyond what shared evidence explains. Composition caps at panel build: at most 3 of 8 from one affiliation type. | Lorenz et al. 2011 (influence reduces independence); caps are ours | design |
| 10 | News-driven note (recency) | Notes when the panel moves with news volume while hard indicators are flat | Tversky and Kahneman 1973 (availability) | verified |
| 11 | Coverage gap | Compares panel tags with the risk's triggers; public as a caveat in the honesty box | Delphi expert-selection practice; rule is ours | design |
| 12 | Shared origin | Near-identical wording counts once: "these claims may share an origin" | Our design | design |
| 13 | Corroboration (Skeptic) | Checks each claim against the ACAPS API, ReliefWeb and ACLED. Unchecked claims go to a verification queue. Absence from the databases is not evidence of falsity. | Our design | design |
| 14 | Honesty box | See section 4 | Brier 1950; the mentor for the principle | verified / mentor |

## 3. Notes per source: what it supports, what it does not

### 3.1 Anchoring: Tversky and Kahneman
- Tversky, A. and Kahneman, D. (1974). Judgment under Uncertainty: Heuristics and Biases. *Science* 185(4157): 1124-1131. DOI 10.1126/science.185.4157.1124. Record: [PubMed 17835457](https://pubmed.ncbi.nlm.nih.gov/17835457/).
- Supports: people anchor on a starting value in numerical estimates. This is why round 1 hides the ACAPS rating.
- Does not support: any size of effect on expert forecasts. The paper's experiments used lay participants. We say "known effect", not "measured on our panel". Hiding a number is not the same as independent thinking, and the card says only "rating hidden until after submission".

### 3.2 Delphi method: Dalkey and Helmer
- Dalkey, N. and Helmer, O. (1963). An Experimental Application of the Delphi Method to the Use of Experts. *Management Science* 9(3): 458-467. DOI 10.1287/mnsc.9.3.458. Record: [RePEc](https://econpapers.repec.org/RePEc:inm:ormnsc:v:9:y:1963:i:3:p:458-467).
- Supports: repeated rounds with controlled feedback, first answered independently, is an established way to reach group opinion. The organisers' brief names Delphi as the model.
- Does not support: any claim that Delphi gives correct answers. Verified from the abstract only.

### 3.3 Scoring, calibration and the Good Judgment Project
- Tetlock, P. E. (2005). *Expert Political Judgment: How Good Is It? How Can We Know?* Princeton University Press. Reviews confirm it scored forecasts for calibration and discrimination and found experts often overconfident.
- Tetlock, P. E. and Gardner, D. (2015). *Superforecasting: The Art and Science of Prediction.* Crown (US edition). The IARPA tournament run by the Good Judgment Project, 2011 to 2015.
- Mellers, B. et al. (2015). Identifying and Cultivating Superforecasters as a Method of Improving Probabilistic Predictions. *Perspectives on Psychological Science* 10(3): 267-281. Record: [APS](https://www.psychologicalscience.org/journals/perspectives/1745691615577794/).
- Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review* 78(1): 1-3. Origin of the Brier score. Title wording varies between sources; check the original before printing.
- Supports: forecasts should be scored on resolved outcomes against a frozen question.
- Does not support: any claim that scores identify good experts from a handful of questions. v3 keeps scores committee-side, never gates approval on them, and offers private calibration only after 5 resolutions.
- Source caution: wiki sites quote superforecaster advantage figures from 30 % to 85 %. We cite no percentage.

### 3.4 Why no extremizing (a change from v2)
- Baron, J., Mellers, B. A., Tetlock, P. E., Stone, E. and Ungar, L. H. (2014). Two Reasons to Make Aggregated Probability Forecasts More Extreme. *Decision Analysis* 11(2): 133-145. DOI 10.1287/deca.2014.0293. Record: [RePEc](https://econpapers.repec.org/RePEc:inm:ordeca:v:11:y:2014:i:2:p:133-145).
- v2 used a fixed factor of 1.3. v3 removes it. The paper supports extremizing in some settings; later work (Satopaa et al., arXiv 1705.02391) argues it is not always appropriate, and a panel of 5 to 8 with overlapping information is the case where it can hurt. We cite the paper only to explain why we considered and dropped it.

### 3.5 Surprisingly popular: an experiment
- Prelec, D., Seung, H. S. and McCoy, J. (2017). A solution to the single-question crowd wisdom problem. *Nature* 541: 532-535. Record: [MIT News](https://news.mit.edu/2017/algorithm-better-wisdom-crowds-0125).
- Supports: in the authors' studies the answer that is more popular than respondents predicted was a better guide than the majority.
- Does not support: reliability with 5 to 8 respondents. The authors say results depend on assumptions real respondents may not meet. It is labelled "experimental" and never sets the number.
- **Corrected:** the master prompt names "Palley and Soll" for peer-prediction weighting. The records we found show Palley and Soll (2019), *Management Science* 65(5): 2291-2309, DOI 10.1287/mnsc.2018.3047, is about "pivoting" for shared information. The peer-prediction weighted average is Palley and Satopaa (2023), *Management Science* 69(9): 5128-5146. Use Palley and Satopaa for the weighting claim. Lane A should confirm which method the code implements before it is named on a slide.

### 3.6 Accuracy prompt
- Pennycook, G., Epstein, Z., Mosleh, M., Arechar, A. A., Eckles, D. and Rand, D. G. (2021). Shifting attention to accuracy can reduce misinformation online. *Nature* 592: 590-595. DOI 10.1038/s41586-021-03344-2. Record: [MIT Sloan](https://mitsloan.mit.edu/press/what-can-be-done-to-reduce-spread-fake-news-mit-sloan-research-finds-shifting-peoples-attention-toward-accuracy-can-decrease-online-misinformation-sharing).
- Cite as "Pennycook et al. 2021"; Rand is the senior author.
- Supports: a subtle accuracy prompt improved the quality of news people chose to share, in survey experiments and a Twitter field experiment.
- Does not support: any effect on expert forecasts. It was about sharing headlines. We say "adapted from". The master prompt's phrase "reduces the spread of false claims" is stronger than what we verified; use "improved the quality of news people chose to share". Page range not checked.

### 3.7 Convergence and independence
- Lorenz, J., Rauhut, H., Schweitzer, F. and Helbing, D. (2011). How social influence can undermine the wisdom of crowd effect. *PNAS* 108(22): 9020-9025. DOI 10.1073/pnas.1008636108. Record: [PMC3107299](https://pmc.ncbi.nlm.nih.gov/articles/PMC3107299).
- Supports: after seeing others' estimates, diversity falls without accuracy improving and confidence rises. This is the reason to note round 2 convergence.
- Does not support: our threshold for "converged", or any inference about a particular person. The note says what the numbers did, not why.

### 3.8 Availability
- Tversky, A. and Kahneman, D. (1973). Availability: A heuristic for judging frequency and probability. *Cognitive Psychology* 5(2): 207-232. DOI 10.1016/0010-0285(73)90033-9.
- Supports: people judge likelihood by how easily examples come to mind. News volume is a proxy for that. The note says "the panel moved with news volume while hard indicators were flat". It does not say the panel was biased.

### 3.9 Per-expert response-pattern reports (master prompt 6d)
- Content: per pseudonym, after 3 or more pulses: calibration and overconfidence, extremity, agreement with ACAPS after reveal, round-2 shift, source-tag mix, abstention, answer latency, co-movement partners. Descriptive sentences, committee-side, opt-in for the expert.
- Basis: the scoring and calibration literature in 3.3 supports reporting calibration and overconfidence back to forecasters as feedback. Round-2 shift connects to 3.1 and 3.7. We found no source that validates the other measures (extremity, latency, co-movement) as indicators of anything about a person. They are descriptions of behaviour, not findings.
- Cautions (details in `privacy-engineering.md` section 4): a pseudonym is not anonymity, so a "per pseudonym" report is personal data; counts after 3 pulses are noise; latency is a time-based metric close to what the brief says not to optimise; co-movement named per pair reads as an accusation; the report must say what happened, not why. `anonymous` answers carry no pseudonym and must be excluded.
- Wording: "Your round-2 answers moved toward the ACAPS band on 4 of 5 pulses. Five pulses is too few to call this a pattern."

## 4. The honesty box (public, on every ledger entry)

- n, agreement, spread (min, max)
- coverage gaps, in plain words
- claims corroborated, claims in the verification queue, claims total
- the panel's hit rate and number of misses, or "no resolved questions yet"
- one caveat line
- **what decision this could inform, for whom, by when** (set by the analyst)
- **when the analyst rejected the panel view: that fact and the analyst's reason**

Not public: any note about a person; the integrity notes themselves. Those stay on the analyst's desk.

Caveat line templates (for Lane A):
1. "Panel of 6 vetted experts. No displacement specialist. Read the displacement signal with caution."
2. "Round 2 answers moved toward the mean without new reasons. The analyst used round 1."  (Only if the analyst chose so. See question Q1 below.)
3. "Two claims could not be checked against the sources we searched and are queued. That is not evidence they are false."
4. "Synthetic panel for demonstration. Not a real forecast."

## 5. Citations changed or dropped

| Original wording | Problem | Action |
|---|---|---|
| Mellers et al., Psychological Science 2014 | Wrong journal and year | *Perspectives on Psychological Science* 10(3), 2015 |
| Extremizing credited to Mellers and the GJP | Not shown in the record we saw | Cited to Baron et al. 2014, and dropped from the product in v3 |
| "Pennycook and Rand" | Lead author is Pennycook; six authors | Pennycook et al. 2021 |
| "Palley and Soll" for peer-prediction weighting | Palley and Soll 2019 is pivoting; peer-prediction weighting is Palley and Satopaa 2023 | Corrected, Lane A to confirm method |
| Superforecaster percentage advantage | Sources disagree | Not cited |
| "Half the cost" for Bangladesh anticipatory action | One secondary source | Not cited (see impact.md) |

## 6. Limits we say out loud

- Experts are not sources on the ground. They are informed professionals. [mentor]
- Commitments give timing and consistency. They do not hide answers from the operator (master prompt section 1a).
- Aggregates with 5 or more contributions are a disclosure rule, not an anonymity guarantee.
- A small panel can lean one way. We cap composition and show coverage gaps. We cannot prove independence.
- The seeded detector tests show the code produces the intended note. They are not a claim about sensitivity or specificity.
- The bias literature is mostly lab work on non-experts. Effects on vetted experts are unknown.
- The sensitivity test on 104 resolved risks uses synthetic panels. It says nothing about real experts and makes no timing claim.

## 7. Open questions for the team

- **Q1 (Lane A):** Master prompt 6a still says that on suspected herding "the aggregate then uses round 1 (`used_round`)". The v3 changelog says no automatic fallback. Which holds? This file follows the changelog: describe, analyst decides.
- **Q2 (Lane A):** Which peer-prediction method does the experiment implement, and which citation goes with it?
