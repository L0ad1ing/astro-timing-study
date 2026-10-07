# Classical texts encoded in full and tested: BPHS, Phaladeepika, the KP Readers and the later KP literature

## Summary
Three complete sources of Indian predictive astrology were read page by page and turned into a rule engine: Brihat
Parasara Hora Sastra (both volumes, G.C. Sharma's translation, gaps filled from R. Santhanam's), Mantreswara's
Phaladeepika (all 28 chapters, V. Subrahmanya Sastri's translation) and K.S. Krishnamurti's KP Readers I-VI, plus the later
K.P. literature as a separate set ("KP modern"). Every rule carries its citation and is stored as data (rules/*.jsonl):
5,222 rules, of which 2,710 are timing rules that
name a datable life event. The engine fires the rules on a chart and a date, weighs them by the books' own strength
principles (dignity, Shadbala, avasthas), and applies the books' cancellations, reversals and modifications between rules
(15 rules act on others).

Each book was then put through the same pre-registered test on Astro-Databank: about 27,000 real life events in the
training half (each against the same person's control dates one and three years away), 18 event types, scored against
the same chart with the natal positions of a random other person (same birth moment, same dates). None of the books
times any event type better than a wrong chart. Rule by rule, the significant results split evenly between the book's
claimed direction and the opposite.

## What was encoded
| Book | Rules | Timing rules | Notes |
|---|---|---|---|
| BPHS (vols. 1-2) | 2,697 | 1,924 | Every chapter; computational chapters became engine primitives (all dashas incl. Kalachakra and Chara, Ashtakavarga with reductions, Shadbala, avasthas, arudhas, argala, karakas, Nabhasa yogas, Pindayu), each checked against the book's worked examples |
| Phaladeepika | 1,357 | 568 | All 28 adhyayas; its own vargas, Vaiseshikamsa, three-pair longevity, Mandi, Ashtakavarga (common tables, verified), gochara with vedha, star transits and Lattas |
| KP Readers I-VI | 951 | 167 | Krishnamurti ayanamsa, Placidus cusps, star and sub lords, the four-level significators; checked against Reader V's worked chart (cusps within 10', planets within 2'). First pass 258 rules (core method); then all six Readers read in full incl. worked examples and letters (2026-10-03/04) |
| KP modern | 217 | 51 | Sub-Lord Speaks, KP Navaratnamala house-grouping tables, KP Astrology for Beginners, Astro Secrets & KP, KP E-zine 2007-2021. Coverage stated per book in docs/kp_progress_log.md; the e-zine was not read in full (1,850 extracted rule statements were). Adds cusp sub-sub lords and joint-period coverage |
| Saravali (vols. I-II, ch. 1-55) | 2,510 | 150 | R. Santhanam's translation (1983), scans supplied by the author, OCR'd locally; page of every rule from the scan's verse headings. Adds its own engines: Saravali Ashtakavarga (tables differ from BPHS), rays, and Moola dasa (strongest of Lagna/Sun/Moon first; kendra-panaphara-apoklima order; sub-periods by the Brihat Jataka shares). Mostly natal; timing rules are Moola dasa/sub-period results, fatal ages, and Ashtakavarga transits |
| Vettius Valens, Anthologies I-IX | 688 | 320 | M. Riley's translation (skyscript PDF). Tropical, whole-sign; its own time-lord engines: the operative year (IV.11-25), zodiacal releasing from Fortune and Daimon (IV.4-10), the 10-year-9-month periods (VI.5), degree-interval transmissions (VI.1), critical years, transits, nine-year zones, the node length-of-life count; three methods reproduce Valens' own worked examples (IV.4, IV.8, VI.5) |
| William Lilly, Christian Astrology Book III (1647) | 1,249 | 593 | The whole book on nativities, from the 1647 scan (OCR). Its own engine: Regiomontanus houses, Lilly's dignities, orbs and fortitude scores, hyleg and anareta, primary directions (Regiomontanus circles of position, Naibod key; arcs to the Ascendant and MC checked against the hand formulas), annual profections and the Lord of the Year, solar revolutions with planetary returns, transits |

Logged but not encoded (each with its page): remedies, horary and moment-of-question methods, results needing data a
birth record lacks (the letters of a name, the father's chart, the partner's chart), purely descriptive significations,
traditional rules that the author himself quotes and rejects, and a few passages missing from the scans.

## The test (identical for all three books)
- Data: Astro-Databank, half 0 (half 1 held back for confirmation), known birth times; 27,352 case-control sets.
- Event types: death, marriage, divorce, birth of a child, career peak, prize, new job, job loss, arrest, trial, illness,
  accident, relationship begin/end, death of a relative, and father/mother/spouse separately.
- Score: the engine's signed, weighted sum of the fired rules relevant to the event type; per-set C = share of control
  dates the event date outscores.
- Null: the same set scored with a random other person's chart (own birth moment and dates kept); for KP the donor's
  birth moment and place define the cusps. Age, calendar and life stage are identical in both; only the chart differs.
- PASS: Bonferroni (18 types) lower bound of dC > 0, C above 0.5, clean placebo; then a single half-1 confirmation.
- Secondary: unweighted and direct-only variants; each rule alone (FDR 5%); a learned combination of all rule indicators
  vs age + calendar year + sex.

## Results
| Run | Pre-registration | Types passing | Per rule (p<.05): for / against book | FDR-significant |
|---|---|---|---|---|
| BPHS | prereg_bphs_engine.md | 0 / 18 | 143 / 143 | 0 |
| Phaladeepika | prereg_phaladeepika_engine.md | 0 / 18 | 65 / 76 | 0 for, 2 against |
| BPHS + Phaladeepika | (same, secondary) | 0 / 18 | 208 / 219 | 0 |
| KP Readers | prereg_kp_engine.md | 0 / 18 | 5 / 7 | 0 |
| KP Readers, AA births | (same, secondary) | 0 / 18 | 3 / 9 | 0 |
| All three books | prereg_kp_engine.md (secondary) | 0 / 18 | 213 / 226 | 0 |
| KP modern | prereg_kp_modern_engine.md | 0 / 18 | 2 / 2 | 0 |
| KP modern, AA births | (same, secondary) | 0 / 18 | 2 / 3 | 0 |
| KP Readers, full read | (same, secondary) | 0 / 18 | 20 / 23 | 0 |
| Saravali vol. I | prereg_saravali_engine.md | 0 / 18 (15 types without rules) | 1 / 1 | 0 |
| Saravali complete | prereg_saravali_full_engine.md | 0 / 18 | 13 / 7 | 0 |
| Saravali complete, corrected (amendment) | (same) | 0 / 18 | 14 / 6 | 0 |
| Valens | prereg_valens_engine.md | 0 / 18 | 25 / 31 | 0 |
| Lilly | prereg_lilly_engine.md | 0 / 18 | 53 / 57 | 0 |

Death (17,976 sets), the largest type: C(actual) - C(wrong chart) = +0.002 (BPHS), -0.005 (Phaladeepika), +0.003 (KP).
KP modern came closest on arrests: it beat the wrong chart after correction (dC +0.042, Bonferroni [+0.003, +0.081]) but
its C did not clear chance (0.516 [0.497, 0.536]), so the pre-registered rule failed it; on AA births dC +0.046
[-0.001, +0.089]. The wrong-chart C was below 0.5 (0.474), which accounts for much of the gap.

**Arrest, checked on half 1 (pre-registered, docs/prereg_kp_modern_arrest_confirm.md): CONFIRMED.** 615 held-back
arrest sets: C 0.520 [0.504, 0.540], wrong chart 0.488, dC +0.032 [+0.005, +0.059], placebo clean. This is the first
pre-registered confirmation in the project. Post-hoc robustness (docs/results_kp_modern_arrest_diagnostics.json; these
cannot change the verdict): bootstrap clustered by event date dC [+0.005, +0.062]; clustered by person (511 people)
dC [+0.003, +0.059], C [0.500, 0.539]; one set per date dC [+0.002, +0.062] but C [0.498, 0.539]; only dates never
seen in half 0 dC +0.030 [-0.001, +0.063]. The score is carried by two "12th house" period rules (Navaratnamala's
imprisonment grouping 2-3-8-12, fires on 63% of arrest dates vs 54% of the same people's other dates; Sub-Lord Speaks'
period sub lord signifying 12, 37% vs 31%). Reading: a small effect (C 0.52) that passed its pre-registered test and
mostly survives clustering, but sits at the edge of every interval and is one hit among several dozen rule-set x event
tests run in this project; both Astro-Databank halves are now used, so it needs an independent dataset to settle.
The one direction that cleared the correction was against the books: Phaladeepika's rules pointed away from new-job dates
(dC -0.060, Bonferroni interval wholly below 0), also in the combined run.
Complete Saravali (vols. I-II): no type passed; the largest was illness (dC +0.054, Bonferroni [-0.041, +0.142]); 545
single-rule tests, 0 FDR-significant either way, 13 vs 7 at p<.05 (about what chance gives). Its learned model beat age + year + sex
on career peaks (C 0.522 vs 0.443, Bonferroni [+0.027, +0.137], placebo 0.477) - a secondary lead whose margin comes mostly from
the demographic model sitting below 0.5; not confirmed (results_engine_Saravali_20261004_1219.json).
A later check against the scans found six dasa rules running on Vimshottari instead of Saravali's Moola dasa and one
Ashtakavarga entry copied from BPHS; corrected re-run (amendment in the pre-registration, results_engine_Saravali_20261004_1849.json):
still 0 / 18 (illness dC +0.049 [-0.044, +0.142]); learned models beat age + year + sex on career peaks and relatives'
deaths, both against demographic baselines below 0.5 (0.443, 0.461) - leads only.
Valens (results_engine_Valens_20261004_1957.json): no type passed; death dC -0.001 [-0.011, +0.011], the largest
positive was relationship end (+0.054, n=59, interval [-0.150, +0.267]); 1,130 single-rule tests, 0 FDR-significant,
25 for vs 31 against at p<.05. Learned model: relatives' deaths beat age + year + sex (dC +0.036 [+0.001, +0.071]) but
only because the demographic model sat at 0.461 - the rules model itself was 0.497; relationship begin went the other
way (dC -0.098 [-0.182, -0.014]). As predicted before running: nothing.
Lilly (results_engine_Lilly_20261004_2250.json; a first run was stopped by low memory at 7,000 sets and restarted
unchanged): no type passed; death dC +0.005 [-0.006, +0.015], marriage +0.006 [-0.018, +0.030], career peak -0.001;
the largest was death of father (+0.045 [-0.023, +0.109]); 2,301 single-rule tests, 0 FDR-significant, 53 for vs 57
against at p<.05. Learned model: relatives' deaths again beat age + year + sex (dC +0.039 [+0.003, +0.078]) with the rules
model at exactly 0.500 against a demographic 0.461 - the same artefact as Valens, not a lead. As predicted: nothing.

Leads from secondary analyses, each checked: Phaladeepika's learned model for job loss (placebo 0.54, vanished in the
combined run); KP's learned model for relatives' deaths (beat age + year + sex on half 0, all ratings and AA; pre-registered single half-1 confirmation, docs/prereg_kp_relative_confirm.md: C 0.488 [0.458, 0.514], dC +0.020 [-0.022, 0.062] - not confirmed).

## Every rule, every check (docs/prereg_full_programme.md, 2026-10-04/05)
Asked to test "everything", with the blind spots of the design listed first, every rule of the seven books was put
through a pre-registered programme (390 type-level tests): AA-rated births only (birth-time quality); control dates at
half-year offsets (so rules tied to the Sun's place or season are no longer identical on event and control dates);
Lilly with a +-1-year direction window and with Ptolemy's 1-degree-a-year key; all seven books in a single score; and,
for the first time, the natal rules - 1,914 rules with an outcome recorded in Astro-Databank (age at death for 15,816
people, violent vs natural death for 5,511, marriage, several marriages, divorce, age at first marriage, widowhood,
early loss of father or mother, children, a child's death, arrest, illness), each person's real chart against a chart
of someone born within two years. No test passed. Single rules ran at chance everywhere (14,562 timing-rule tests in
the all-books run: 322 for, 338 against at p<.05, none after correction). One natal rule crossed the FDR line (BPHS
45.74, short life; z 4.3) - a lead whose mechanism (Saturn combust) is partly a season-of-birth marker; it would need
its own check on the held-back half. The other 3,982 natal rules (wealth, status, character, fame...) have no outcome in
this data and remain untested.

## What this does and does not show
It shows that these three systems, applied completely and as written, do not time the events recorded in Astro-Databank
lives, under a design that removes age, calendar and shared-date artefacts. It does not test the books' descriptive
statements about character, appearance or relatives (no graded outcome data), the horary methods, or a practitioner's
judgement in selecting among rules. The weighting formula that turns many rules into one score is the engine's own
reading of the books' principles; the unweighted variant gave the same answer.

## The engine as a reading tool
The same engine produces full readings: every prediction the three books make for a chart, with its citation, the
placement that triggers it, the rules that cancel it, comparisons with 300 other charts, and the timeline of periods.
For readings a centred version of the weighting is used (an average planet counts equally for good and bad results);
the tests used the original formula as pre-registered.

## Reproduce
`python -m rules.build`; `python -m scripts.run_bphs_engine --sources <books> --prereg <file>`; results in docs/results_*.
Source texts are not distributed (copyright); rules store paraphrases with page citations.
