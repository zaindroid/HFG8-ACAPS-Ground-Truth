# Sealed Signals — Reach and elicitation design, for external review

Version 1, Saturday 7 November 2026, as sent for review. **Superseded by master prompt v3.4** after three reviews: the
hidden measures of section 3.3 (seed questions on pulses, knowledge-gap measure, response time, overclaiming foil) were
removed; calibration became a consent-gated programme; the card, link flow, reveal policy and privacy wording changed.
Kept here as the record of what was reviewed.

**Review prompt (paste together with this document):**
You are reviewing the expert-outreach and elicitation design of a humanitarian risk-analysis tool built in a 48-hour
hackathon for ACAPS, an organisation that publishes risk analysis on humanitarian crises. Review the design in this
document as a sceptical specialist in survey methodology, expert elicitation, behavioural science and humanitarian
practice. Be concrete: for each point say whether it is sound, what it over-claims, what would fail with real experts,
and what you would change. Then answer the numbered questions in section 9. Do not rewrite the document; critique it.

---

## 1. The problem in one paragraph

ACAPS analysts rate risks (probability band, impact, triggers) for crises such as "Displacement from Sudan to Chad". The
ratings are strongest when experts who are close to the context check them. Those experts are busy, often senior,
spread across UN agencies, NGOs, academia and governments, and they do not sign up to portals. Today the check happens
through an analyst's own emails and conversations, which leaves no record, no timing, no way to see bias, and no
feedback to the expert. We want a way to ask a vetted panel a precise question, get an answer in under a minute through
whatever channel the expert already uses, store it so it cannot be changed afterwards, reveal all answers together,
and learn, quietly and without confronting anyone, how reliable each answer is and where an expert's confidence
outruns their knowledge.

Constraints that matter: no expert account, ever; one screen, no scrolling; nothing that looks like a test; the expert
must never see a score about themselves unless they opt in; the analyst stays in control; everything must also work for
an expert on a basic phone in a place with poor connectivity.

## 2. Who the experts are (assumptions we are making)

- Mostly 40–65, senior, in UN agencies, NGOs, research institutes, line ministries, sometimes journalists or local
  civil society. Some are field staff with a phone and WhatsApp; some are desk analysts with Outlook and Teams.
- Email is universal but slow; WhatsApp is near-universal in the field; Signal in security-sensitive contexts; SMS
  where data is poor; Teams and Slack inside large organisations; voice (calls, voice notes) is preferred by many
  senior people and by anyone who does not type comfortably in English or French.
- They respond to a person, not to a system. They respond when the question is specific, when the ask is small, when
  they see what happened with their answer, and when they are not ranked or exposed.
- They are not naive about surveys. Anything that looks like a test or a quiz damages trust. Anything that looks like
  a dashboard about them ends participation.

If any of these assumptions is wrong, say so in the review.

## 3. The current design (v3.3, what is being built this weekend)

### 3.1 Reach: the channels

The analyst's address book is the registry. The expert's first contact is a question, not an invitation to join. The
system sends the same question through the expert's preferred channel, and every message carries a magic link (one
token per expert per pulse) that opens the one-screen card. Answers from any channel resolve to the same record.

| Channel | How the question arrives | How the answer comes back |
| --- | --- | --- |
| Email | Plain text, under 2 KB, from the analyst's name, reply template at the bottom | Click the link, or reply in the template ("70 4 likely") parsed by the inbound handler |
| WhatsApp | Message with the link and the template; voice notes accepted | Tap, type, or send a voice note; transcribed and confirmed back in one line |
| Signal | Same as WhatsApp | Same |
| SMS | Short message with the link and the numeric template | Numeric reply "70 4", or the link |
| Scheduled call | ICS invite to the expert and the analyst | Analyst enters the answer, flagged "entered on behalf, with consent" |
| Partner API | An organisation's credential posts answers for its own experts | Structured POST |

Rules: send at 08:00 in the expert's time zone, never a Friday afternoon locally; hard cap of one pulse per expert per
7 days; one reminder after 24 hours with social proof ("6 of 8 have answered"); "pause" by one word for 30 days; a
48-hour answer window; the reveal happens once five or more answers are in. Preferences (channel, hour, language,
mask) are learned from the first reply and editable by the analyst.

Closing the loop, automatically, in the expert's language and channel: within a day of the reveal, "7 of 8 answered;
group 0.69; you said 0.80; the analyst kept High and added your note on Adré to the triggers." On resolution, the
outcome report. Yearly, a thank-you with early access to the global risk analysis. No ranking anywhere.

### 3.2 The card: one screen, four items

Looks like a note from a colleague. Completes in under 60 seconds with at most five taps. Large type, high contrast,
under 50 KB, works on 2G.

- Line 1 (two sentences): who is asking and why now, with the evidence ("ACAPS's severity index for Displacement from
  Sudan to Chad rose 6.1 → 6.9 in April, the largest move of 123 crises.")
- Item A, likelihood: five words (very unlikely · unlikely · even · likely · very likely) as large tap targets, with an
  optional number field for people who think in percentages. ACAPS's own band is not shown.
- Item B, confidence: three words (not sure · fairly sure · sure).
- Item C, panel: "Most of the panel will say…" (unlikely · even · likely).
- Item D, one line: "What are we missing?" with a saw / read / heard tag; optional.
- Occasionally, in place of or below D: one seed item or one trigger pick (see 3.3), always one tap.
- Always visible, small: "Outside my area" and "Not enough evidence". Both are real answers and are never scored.
- Mask shown once on the first answer (named · nickname · anonymous), then remembered.
- Submit → one line: "Thanks. ACAPS currently rates this High. You'll hear how the group saw it within a day." Nothing
  else. No dashboard, no history page for the expert.
- Optional round 2: the same screen with the anonymised spread drawn as five bars and "Still your answer?" (keep ·
  revise) plus an optional line.
- No timer, no progress bar, no emoji, no gamification.

### 3.3 What the card measures without saying so

All computed server-side, never shown to the expert as a judgement, disclosed in one paragraph in the first contact
("some items help us calibrate"). Reported only as sentences to the vetting committee, and to the expert if they opt in.

- Seed questions (Cooke's classical model, 1991): about one pulse in three carries one short factual item whose answer
  ACAPS already knows from its data ("roughly how many arrivals per day did ACAPS record in late September: under 100,
  100–300, over 300?"). Accuracy on seed items is actual knowledge of the context; stated confidence is perceived
  knowledge; the gap between them, per pseudonym, is the knowledge-gap measure.
- Meta-knowledge item (item C): accuracy at predicting the panel identifies informed experts without a track record
  (Prelec, Seung & McCoy 2017; Martinie, Wilkening & Howe 2020) and feeds the surprisingly-popular aggregation, which
  we run only as a labelled experiment alongside the plain mean.
- Test–retest: occasionally the same judgement is asked in a different form two pulses apart (five words vs a number);
  the difference is a reliability measure.
- Response time and edit count: very fast extreme answers and heavy editing are noted, not judged.
- Calibration over time: every forecast is scored (Brier) against the real outcome once ACAPS resolves the question;
  overconfidence is Brier against stated confidence.
- Round-2 shift: how far an expert moves toward the group after seeing the spread (anchoring susceptibility).
- Source mix: share of saw / read / heard over time.
- Abstention rate.
- Overclaiming foil (behind a flag, off by default, requires ACAPS's explicit consent and disclosure): one in ten seed
  items would refer to a plausible but non-existent report; "yes, I saw it" measures overclaiming (Paulhus et al. 2003).
  Never on in the demo; we recommend ACAPS decide.

### 3.4 Biases we address, and how

| Bias | Mechanism |
| --- | --- |
| Anchoring on ACAPS's rating | Rating hidden until after submission |
| Herding | Commit-and-reveal; round 2 shows only an anonymised spread |
| Overclaiming (heard reported as seen) | Saw / read / heard tag before free text |
| Forced guessing | "Outside my area" and "Not enough evidence" as real answers |
| Loud majority averaging away an informed minority | Dissenter's reason shown beside the mean; surprisingly-popular as experiment |
| Overconfidence | Outcome scoring; group outcome report to all; private calibration opt-in |
| Packed panels | Committee vetting, affiliation tags, cap of 3 of 8 from one affiliation type |
| Acquiescence / straight-lining | Noted from response patterns; descriptive only |

### 3.5 What we do not claim

Hiding the rating removes the displayed anchor; it cannot make judgement cognitively independent. Commit-and-reveal
proves timing and consistency, not truth and not confidentiality from the operator. Masks give confidentiality from
peers and the public, not from ACAPS. Integrity notes describe patterns; they never diagnose a person. Scores are for
forecasts, not people; they never gate approval or removal in the pilot.

## 4. Options considered and not adopted (so far), with reasons

| Option | Why not (yet) |
| --- | --- |
| Expert portal with login, profile, history | Experts do not sign up; the mentor confirmed ACAPS works by email and conversation |
| Native mobile app | Install friction; many experts will not install anything for one question a month |
| Continuous slider 0–100 as the only input | Forces false precision; five words plus an optional number instead |
| Full Delphi with three rounds | Too slow for a 48-hour window; one optional round 2 instead |
| Public leaderboard or reputation score | Ends participation; scores are committee-side only |
| Timer on the card | Produces speed, not thought; only the jury exercise has one |
| Visible "6 of 8 said likely" before answering | Pure herding; counts appear only in round 2, as a spread, after commitment |
| Automatic weighting by past accuracy as the primary aggregate | Opaque and punitive-looking; equal-weight mean is primary, weights are shrunk and capped as a secondary view |
| Persuasion techniques (scarcity, urgency, loss framing) | Manipulative toward a professional panel; we use only reciprocity (feedback) and social proof (response count) |
| Facebook / LinkedIn messaging as channels | Off-platform professional contact feels intrusive; not excluded for the future |

## 5. Options not yet in the design that may be better (the point of this review)

These are candidates. We want a judgement on each, and we want to hear about ones we have not thought of.

### 5.1 Channels

1. **Phone call with keypad answers (IVR).** A short recorded call in the expert's language at their hour: "Press 1 to 5
   for very unlikely to very likely." For experts who never type and for places where data is unreliable. Cheap
   (Twilio or a local gateway); answer lands in the same record. We think this is the single largest coverage gain.
2. **Missed-call or flash-call trigger.** The expert gives a missed call to a number to say "call me back now" or "send
   the question now". Zero cost to the expert, common in South Asia and East Africa.
3. **USSD menu.** Works on any phone with no data. Text-only, 182 characters per screen. Covers the last 10 percent.
4. **Microsoft Teams and Slack direct message.** Large agencies live in Teams. An adaptive card inside Teams can carry
   the whole five-item card. Likely the right channel for UN desk staff.
5. **Telegram.** Used widely in some regions (Central Asia, Middle East, Eastern Europe). Same handling as WhatsApp.
6. **Outlook voting buttons / email with one-click answer links.** Each likelihood word is a link; one click records the
   answer and opens an optional one-line reply. Removes the "open the card" step for the email-first majority.
7. **Calendar-slot pulses.** For experts who prefer rhythm: a standing 10-minute slot ("your Chad question, Tuesdays
   09:00") with the card pre-loaded, rather than ad-hoc messages.
8. **Field liaison entry.** A trusted local partner relays the question in person (community leaders, local NGO staff)
   and enters the answer, flagged as relayed. Extends the panel beyond people with phones.
9. **Paper and photo.** A printable one-page version; the expert photographs the filled sheet; the analyst or an OCR
   step enters it, flagged. Rarely needed, cheap to offer.

### 5.2 Elicitation formats

10. **Interval elicitation (four-step, Speirs-Bridge et al. 2010).** Lowest plausible, highest plausible, best estimate,
    and how sure you are the truth is inside. Documented to reduce overconfidence compared with a single point plus a
    confidence word. Costs two more taps. Could replace items A and B for experts who choose numbers.
11. **Frequency framing.** "Out of 10 situations like this one, in how many would the displacement exceed X by March?"
    Frequencies are judged better than probabilities by most people (Gigerenzer & Hoffrage 1995). Could be the default
    wording of item A with the five words mapped to it.
12. **Pairwise comparison.** "Is this more likely than the Niger scenario we asked about last month?" Relative judgements
    are easier and more consistent than absolute ones. Produces a ranking across risks per expert; useful for the
    cross-crisis alert ranking. Cannot replace the probability but could be the seed item form.
13. **Dialectical bootstrapping (Herzog & Hertwig 2009).** Ask once, then "assume your first answer was off; why might
    that be, and what would you say now?" The average of the two is more accurate than either. One more tap, optional,
    and gives us the test–retest measure in a single pulse instead of two.
14. **"Consider the opposite" prompt.** One line before the free text: "What is the strongest reason this would NOT
    happen?" Reduces confirmation bias (Lord, Lepper & Preston 1984). Could alternate with "What are we missing?"
15. **Trigger ranking instead of probability on some pulses.** "Which of these three triggers would move your view
    most?" Experts find this natural; it feeds the analyst's trigger list directly.
16. **IDEA protocol structure (Hanea et al. 2017).** Investigate, Discuss, Estimate, Aggregate: a formal version of our
    round 1 → anonymised spread → round 2. We already follow it loosely; the question is whether to say so and align
    the steps exactly.

### 5.3 Reliability and knowledge-gap measurement

17. **Cooke's informativeness alongside calibration.** With interval answers we can score both how often the truth
    falls inside an expert's intervals and how narrow the intervals are. The classical model weights by both. We would
    report both as sentences, never as weights, in the pilot.
18. **Cross-channel consistency.** The same expert answering by voice and by card on different pulses: does the channel
    change the answer? A reliability measure and a channel-quality check.
19. **Confidence-interval coverage over time** as the overconfidence measure, instead of or alongside Brier vs stated
    confidence.
20. **Known-unknown items.** "Does ACAPS currently track X for this crisis?" (yes / no / not sure) where ACAPS does or
    does not. Measures awareness of the evidence base, separately from factual knowledge.
21. **Affiliation-level bias reports.** Compare answers across affiliation tags (UN vs NGO vs academic) at the panel
    level, never individually. Shows the committee whether a viewpoint systematically leans; informs panel composition.
22. **Recency and news salience.** Match answer timing and free-text claims against the news cycle (ReliefWeb,
    ACLED cached) to note when a panel's shift follows a headline rather than new field evidence. Descriptive.
23. **Acquiescence and straight-lining detection.** Same answer across items and pulses regardless of question; noted.

### 5.4 Engagement, specifically for senior and non-technical experts

24. **A named human sender always.** Every message comes from the analyst by name, with their photo in the email
    signature and a direct reply path that reaches a person, not a parser.
25. **Reciprocity that is concrete.** Early access to the monthly risk analysis, a one-line credit ("the Chad panel")
    in the published report with consent, and the yearly thank-you. No points, no badges.
26. **Identity without exposure.** "You are one of eight on the Chad panel" in the first message; membership is the
    status, and it is private.
27. **Standing consent and a one-line charter.** The first contact includes a short charter: what we ask, how often,
    what we store, who sees what, how to stop. Senior people respond to clear terms.
28. **Language.** Questions in the expert's working language (English, French, Arabic, Spanish, Portuguese first);
    the parser accepts answers in any of them; the free line is kept in the original and translated for the analyst
    with the original attached.
29. **Analyst-side nudges, not expert-side.** The system tells the analyst who has not answered and suggests a personal
    message; it never sends a third automated reminder.

## 6. Privacy, consent and data minimisation

- Stored about an expert: contact details, tags, preferences, mask, answers, commitment hashes, derived measures.
  Never stored: free-text that identifies third parties without need; audio after transcription confirmation (deleted
  within 24 hours by default); location beyond time zone.
- Lawful basis for a real deployment: legitimate interest of ACAPS plus explicit consent collected in the first
  contact; right to erasure handled by deleting identity-registry rows and keeping answers under a pseudonym only.
- The identity registry is encrypted at rest (hybrid ML-KEM-768) with logged access; anonymous answers are stored
  without identity at all.
- Disclosure: aggregates only at n ≥ 5; k-anonymity is a disclosure rule, not an anonymity guarantee, and the card
  says so.

## 7. What a real deployment would still need

Channel contracts (WhatsApp Business API approval, SMS gateway in each country, telephony), ACAPS's data-protection
review, translation quality checks, a decision on the overclaiming foil, a committee for vetting and for reading the
pattern reports, and a pilot with one crisis and one panel for three months before anything touches a published rating.

## 8. Citations used (to be verified by our research lane before any slide)

Cooke 1991, Experts in Uncertainty; Tetlock & Gardner 2015, Superforecasting; Prelec, Seung & McCoy 2017, Nature;
Palley & Soll 2019, Management Science; Martinie, Wilkening & Howe 2020, Journal of Experimental Psychology: General;
Pennycook & Rand 2021/2022 (accuracy prompts); Paulhus, Harms, Bruce & Lysy 2003 (overclaiming); Speirs-Bridge et al.
2010, Risk Analysis (four-step interval elicitation); Hanea et al. 2017, Methods in Ecology and Evolution (IDEA);
Herzog & Hertwig 2009, Psychological Science (dialectical bootstrapping); Gigerenzer & Hoffrage 1995, Psychological
Review (frequency formats); Lord, Lepper & Preston 1984, JPSP (consider the opposite); Tversky & Kahneman 1974;
Dalkey & Helmer 1963 (Delphi).

## 9. Questions for the reviewer

1. Channel coverage: which of options 1–9 would materially raise the response rate among senior humanitarian experts,
   and which are not worth building? Is there a channel we have missed entirely?
2. The card: is five words plus an optional number the right primary input, or should we adopt the four-step interval
   (option 10) or frequency framing (option 11) as the default? What would you drop to keep it to one screen?
3. Seed questions: is "one factual item in roughly one pulse in three, disclosed in general terms in the first contact"
   acceptable to a professional panel, or will it read as a test and damage trust? How would you word the disclosure?
4. The knowledge-gap measure (seed accuracy vs stated confidence): is it sound, and what sample size per expert do you
   consider the minimum before a sentence about it should be shown to a committee?
5. The overclaiming foil: should it exist even behind a flag, or is a fictitious reference to a report inconsistent
   with the trust we are asking for?
6. Round 2 and the meta-knowledge item: do they introduce herding or gaming that outweighs their value?
7. Which of options 12–23 would you add, in what order, and which are measurement theatre?
8. Senior and non-technical experts: what in 5.4 is missing, and what in the current design would make a 60-year-old
   UN protection adviser stop answering after the second pulse?
9. Ethics: anything here that a humanitarian data-responsibility reviewer (for example following the OCHA Centre for
   Humanitarian Data guidance) would object to?
10. Over-claims: list every sentence in sections 3 and 5 that promises more than the mechanism can deliver.
11. If you had to cut this to the three changes with the highest impact on answer quality and response rate for the
    pilot, which three?

Please score the current v3.3 design 1–10 on: response rate it would achieve with real experts; quality of the
elicited judgement; fairness and trust from the expert's side; and measurement validity of the reliability and
knowledge-gap reports. One line of justification each.
