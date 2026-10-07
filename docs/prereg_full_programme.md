# Pre-registration - testing every rule of every book (committed before any of these runs)

Requested by the author (2026-10-04): "I would love all the rules tested like everything", after the question of
what could skew the earlier tests (blind spots listed in the reply: annual-cycle rules invisible to whole-year
controls; birth-time precision; construction choices never varied; natal rules never tested).

Books: BPHS, Phaladeepika, KP Readers, KP modern, Saravali, Valens, Lilly (9,669 rules: 3,773 timing, 5,896 natal).
Data: Astro-Databank half 0 only (half 1 stays held back for confirming any PASS).

## Part T - every timing rule, robustness runs (same engine, same score, same statistics as before)
T1 Birth-time quality: each book and all books together restricted to AA-rated births (`--ratings AA`).
T2 Annual-cycle blind spot: control dates at half-year offsets instead of whole years (Death -4.5, -3.5, -2.5,
   -1.5; others -2.5, -0.5, +1.5, +3.5 years), each book. Rules keyed to the Sun's place or the time of year now
   differ between event and control dates; seasonality of events is removed by the mismatched-chart comparison.
T3 Construction choices (Lilly, the book with the most free parameters): directions operate within +-1 year (instead
   of +-0.5) and Ptolemy's key 1 deg = 1 year (instead of Naibod); one run each.
T4 All seven books in one score (all timing rules together), all ratings.
Decision rule for every run: as before - PASS = Bonferroni (18 types) lower bound of dC > 0, C above 0.5, clean
placebo. Across Part T there are about 25 runs: a PASS in any single run is reported as a lead and goes to a single
half-1 confirmation (pre-registered separately); it is not a finding on half 0 alone.

## Part N - every testable natal rule
Each natal rule predicts a domain with a sign (+/-). Domains with an outcome in Astro-Databank, per person (people
with a known birth time; one record per person):
| outcome | rule domains | definition |
|---|---|---|
| long life | longevity | age at death, among people with a recorded death (born before 1940, to limit right-censoring) |
| violent death | violent_death, death_manner, accident_risk, accident | death by accident, homicide, suicide, war/terrorism or execution vs by disease or heart attack (other causes excluded) |
| married | marriage, marriage_early | at least one marriage recorded |
| several marriages | marriages_many | two or more marriages recorded, among the married |
| divorce | marriage (with sign reversed: '-' marriage rules predict divorce) | a divorce recorded, among the married |
| widowhood | widowhood, spouse_death | death of the spouse recorded |
| early loss of father / mother | father / mother | the parent's death recorded before the native's 18th birthday (sign: '-' rules predict it) |
| children | children | a child's birth recorded ('+'); a child's death recorded ('-' rules predict it) |
| imprisonment | imprisonment, legal, Arrest | an arrest recorded |
| illness | health | an illness recorded ('-' rules predict it) |
Not testable with this data (logged, counted): wealth, status, character, fame, learning and the other domains.
Score: per person and outcome, the signed weighted sum of that book's fired natal rules in those domains (same
weights as the reader). Statistic: C = AUC of the score for the outcome (for age at death: the probability that of
two people the one with the higher score lived longer). Null: the same person's outcome scored with a donor's chart -
a random other person born within +-2 years (so slow planets and era are matched), the person's own sex. Primary
dC = C(real) - C(donor), 2,000 person bootstraps, Bonferroni over the outcomes; PASS as in Part T. Per-rule tests:
each rule's fire rate among people with vs without the outcome, real minus donor, Fisher/permutation p, FDR 5%.
Caveat stated in advance: "recorded" outcomes are incomplete (absence of a record is not absence of the event); this
dilutes but does not bias the comparison, since recording does not depend on which chart is used.

## Expectations (mine, before running)
No run in Part T or Part N passes; per-rule tests at chance.

## Amendment 1 (2026-10-04, before any Part N data was examined) - signs per domain
Checked by reading samples of each domain's rules (no outcome data looked at):
- '+' means favourable for the domain in every book, so: longevity '+' = long life; marriage '+' = married ('-' =
  unmarried or a bad marriage, and predicts divorce among the married); children '+' = children ('-' = few/none,
  and predicts a child's death); father/mother '-' = misfortune to the parent (predicts early loss); health '-'
  predicts illness; imprisonment/legal/Arrest '-' predicts arrest ('+' = release); accident_risk and Lilly's
  accident '-' predict violent death; marriages_many '+' = several marriages.
- Exceptions where the sign marks the event itself: widowhood '+' = the spouse dies (BPHS, Phaladeepika, KP), but
  Saravali's widowhood rules use '-' for it (sign flipped for Saravali); Lilly's spouse_death '+' and violent_death
  '+' = the event happens.
- Saravali's death_manner rules (all '-') name a manner of death: those whose text names a violent cause (weapon, fire,
  water/drowning, fall, poison, accident, murder/killed, execution/hanged/beheaded, suicide, war, beast/animal,
  vehicle, thieves) predict violent death; the rest (disease, fever, the named organ, natural causes) predict
  natural death.
- Lilly's marriage_early is tested on a 12th outcome: age at first recorded marriage below the median (+ = early).

## Results (2026-10-05, run 23:48-04:13; AbraxasV3 paused for the runs with the author's OK, restarted after)
No run passed. 390 type-level tests, 0 PASS.
- N natal (results_natal_20261005_0045.json): 35,682 people, 1,914 testable natal rules (3,982 untestable with this
  data). 85 book x outcome tests, none passes; age at death (15,816 people) within +-0.004 of the donor chart for every
  book. Per rule 2,542 tests: 64 for / 53 against at p<.05; 1 FDR-significant in the claimed direction - BPHS vol. 1
  45.74 (3rd lord and Mars, or 8th lord and Saturn, combust or with malefics: short life), z = +4.3, p = 1.5e-5. A lead
  only: it partly turns on Saturn's combustion (season of birth, which the donor design does not match and which has a
  small known link to longevity). Its half-1 check needs its own pre-registration.
- T1 AA only: all seven books 0/18 (per rule at chance in each: BPHS 137/147, PD 68/71, KP 14/20, KP modern 2/3,
  Saravali 13/4, Valens 22/35, Lilly 43/57; 0 FDR anywhere).
- T3 Lilly variants: +-1-year window 0/18 (56/64); Ptolemy's key 0/18 (57/62).
- T2 half-year controls: all seven books 0/18 (BPHS 165/149, PD 80/76, KP 20/14, KP modern 3/4, Saravali 19/15,
  Valens 14/32, Lilly 63/67; 0 FDR).
- T4 all seven books in one score: 0/18; death dC +0.004 [-0.007, +0.015]; per rule 14,562 tests, 0 FDR, 322 for / 338
  against at p<.05.
Expectation stated beforehand (no pass, per rule at chance) met.
