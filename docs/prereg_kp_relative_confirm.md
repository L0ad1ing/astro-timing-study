# Pre-registration — confirmation of the KP learned-model lead on relatives' deaths (committed before any run)

## The lead
In the pre-registered KP test (docs/prereg_kp_engine.md; results_engine_KP Readers_20261003_1719.json) a secondary
analysis - LightGBM LambdaRank on the 87 KP timing-rule indicators, 5 folds grouped by person and event month - beat the
age + calendar year + sex model for Death_of_relative: C 0.500 vs 0.461, dC +0.039, Bonferroni interval [0.0045, 0.073],
placebo 0.479. The AA-only subset gave [0.0043, 0.089]. Both runs use half 0, so they are not independent. The KP
prereg gave secondary analyses no confirmation step; this file adds one, once.

## Test (single, decided now)
- Training: all half-0 Death_of_relative sets (as in the KP test: known birth time, the same case-control construction).
- Models: RULES = LightGBM LambdaRank (models.PARAMS) on the 87 KP timing-rule firing indicators; DEMO = the same on age,
  calendar year, sex. Both fitted once on all half-0 sets.
- Test data: half-1 Death_of_relative sets whose event year-month does not occur among half-0 Death_of_relative events
  (the date-leak guard used for every confirmation since the harmonic study).
- Outcome: dC = mean per-set C(RULES) - C(DEMO) on the test sets, paired bootstrap 2,000.
- CONFIRMED only if: dC 95% lower bound > 0 AND RULES C 95% interval above 0.5 AND the placebo (the -1y control as
  pseudo-event, scored by RULES) has a 95% interval including 0.5 or below.
- Reported in any case; no other event type, subset or model variant will be tried on half 1.

## Expectation (mine, before running)
Not confirmed: dC within +-0.02. A secondary hit among 18 event types x 2 variants with an age-dominated baseline is
the kind of lead that has failed every earlier confirmation in this project.
