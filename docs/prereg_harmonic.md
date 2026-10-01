# Pre-registration — continuous harmonic features (written and committed before any run)

Requested by the author (2026-10-01): replace rule-based features with continuous planetary geometry
(src/harmonic_features.py) and look for any signal with LightGBM + SHAP, under the existing falsification harness.

## Question
Do continuous harmonic features (angles between bodies, encoded as cos/sin of harmonics 1, 2, 3, 4, 5, 6, 8; speeds,
declinations) rank a person's event date above the same person's control dates better than **a model that knows
only the person's age**?

The comparison with age is the point. Slow-planet geometry is partly an age clock, and a flexible model can use
age alone to beat control dates when events cluster at certain ages (marriage in the late 20s). Beating 0.50 is
not enough; a result has to beat the age baseline.

## Data
- Astro-Databank, **training half (0) only**, known birth times, case-control sets from
  `preprocessing.case_control_sets` (event vs the same calendar date −3, −1, +1, +3 years; own death −4..−1).
- Event types with ≥ 150 sets: Death (randomly sampled to 3,000, seed 1), Marriage, Death_of_relative, Prize,
  Arrest, Career_Peak, Job_Start, Divorce, Job_End, Trial, Illness, Accident — 12 types.
  Relationship_Begin (110), Relationship_End (59), Birth_Child (45) are too small and are not run.

## Models (LightGBM LambdaRank, `models.PARAMS`, 5-fold person-grouped CV, out-of-fold scores)
1. **AGE**: `AgeBaseline` (one feature: age in years).
2. **HARMONIC**: `HarmonicFeaturizer()` default columns (2,396: no Moon, no heliocentric; the 84 same-planet
   slow-body "age clock" columns dropped).
3. Ablations of HARMONIC, C-index only: SKY (630 transit-to-transit), NATAL (transit-to-natal, minus the clocks),
   KIN (30 speed/declination/out-of-bounds).

## Primary outcome
Per event type: ΔC = C(HARMONIC) − C(AGE), on the same sets, from per-set C values, with a paired bootstrap
(2,000 resamples). With 12 event types, the Bonferroni interval is the 0.21%–99.79% percentile interval.

## A result is a CANDIDATE only if all of these hold
1. Bonferroni ΔC interval lower bound > 0.
2. Placebo C (control −1 year as the fake event): 95% interval includes 0.50, or lies below it.
3. Placebo window test (`validation.placebo_window_test`, stretch shifted 2 years earlier): passed.
4. If NATAL is the best ablation: mismatched-chart C for the NATAL model ≤ 0.52. (Not applicable to SKY/KIN:
   those features are the same for everyone on a date.)

Descriptive (not pass/fail): window test top-1/top-3; top-20 SHAP features per fold model, and features appearing in
the top 20 of at least 4 of 5 folds (a real signal should be stable across folds).

## Confirmation
Any CANDIDATE: a model trained on the whole training half is frozen (file SHA-256, feature-name hash, parameters, code
commit) in `lockbox/harmonic/`, then evaluated **once** on half 1 with the same ΔC test (95% interval).
Half 1 has never been used to fit or tune a harmonic model. No retraining, no feature changes after this commit.

## Expectations (mine, before running)
- AGE C above 0.50 for age-concentrated events (marriage, job start, prize, career peak), roughly 0.51–0.55.
- HARMONIC C close to AGE C; ΔC within ±0.01 for nearly all types; **no CANDIDATE**.
- If HARMONIC does beat AGE, most likely through residual age information in slow-planet cross-pairs or through the
  calendar (sky features), which the placebo window test is designed to expose.
- SHAP top features unstable across folds (different features each fold).

## Not in this test
Moon features (event times unknown), heliocentric angles, personal telemetry (Module 3: one person's correlated
time series; needs its own design and pre-registration).
