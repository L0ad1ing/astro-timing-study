# Pre-registration — discovery v2: mined geometric rules, leak-free holdout (written and committed before any run)

Requested by the author (2026-10-01): mine interpretable geometric rules from continuous planetary features on a
training partition and keep only those that survive a leak-free holdout, against a demographic baseline, with
multiple-testing correction. Output: `src/discovery_v2/discovered_rules.json` (possibly empty).

## Data
- Astro-Databank, **both halves**, known birth times. Case-control sets from `preprocessing.case_control_sets`
  (event vs the same person's same calendar date −3, −1, +1, +3 years).
- **Control filter** (`discovery_v2.matched_controls`): a control date within 30 days of any other recorded event of
  that person (any type) is dropped; a set needs ≥ 2 remaining controls.
- Event types (11): Marriage, Death_of_relative, Prize, Arrest, Career_Peak, Job_Start, Divorce, Job_End, Trial,
  Illness, Accident. Own death is excluded: its controls all lie before the event, so any slowly changing feature
  separates them. Relationship_Begin/End and Birth_Child are too small. A type runs only with ≥ 150 training and
  ≥ 75 test sets.

## Leak-free split (`discovery_v2.leak_free_splitter`)
- **Test = sets whose event falls in February, May, August or November; training = the other eight months.**
  A set's event and controls share a calendar date, so no test date shares a year-month (or an exact date) with
  any training date. A set whose dates straddle a month boundary across sides (±1 day) is dropped.
- A person appears on one side only: the side of their earliest event of that type; their sets on the other side
  are dropped.
- An audit asserts zero shared persons, year-months and exact dates between the partitions.

## Features and candidate rules (training partition only)
- `HarmonicFeaturizer()` default columns (2,396: pairwise sky angles and transit-to-natal angles as cos/sin of
  harmonics 1–6 and 8, speeds, declinations, out-of-bounds; slow-planet same-planet age clocks removed).
- Univariate rules: each feature ≤ its training 10th / 25th percentile, or ≥ its 75th / 90th (≈ 9,600 rules).
- Two-condition rules: every leaf path of a depth-2 LightGBM LambdaRank ensemble (200 trees) fit on training.
- Ranking: Mantel-Haenszel matched z on training → top 200 → conditional-logistic z adjusted for the
  out-of-fold demographic baseline score → **top 20 per event type**, each with its direction (risk or protective).

## Demographic baseline (the bar to beat)
LightGBM LambdaRank on three features: age, calendar year (decimal) and sex (Astro-Databank gender). Fit on
training, scored on test. Calendar year lets the baseline absorb era and recording-density effects.

## Holdout test (once, per rule)
Conditional logistic regression on the test sets (strata = case-control sets), covariates: the rule indicator and the
baseline score. **A rule SURVIVES only if** its coefficient has the same sign as on training **and** its two-sided
p < 0.01 / N, where N = total rules tested on holdout (20 × number of event types run; 220 if all 11 run).
Also reported: Benjamini-Hochberg q-values, matched odds ratios, event and control rates, baseline holdout C.

## Expectations (mine, before running)
No rule survives. LightGBM already searched these features with hundreds of trees and found nothing once
shared-date leakage was blocked; a smaller rule set cannot find what a larger ensemble missed. Training z-scores of
selected rules will be large (selection on noise); their holdout effects will centre on zero.
