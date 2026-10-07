# Pre-registration - half-1 check of the KP-modern arrest near-miss (committed before any run)

Requested by the author (2026-10-04, "check the arrest too").

## The lead
In the pre-registered KP-modern test (docs/prereg_kp_modern_engine.md; results_engine_KP modern_20261004_0553.json),
Arrest (620 half-0 sets) beat the mismatched chart after Bonferroni (weighted dC +0.042, Bonferroni [+0.003, +0.081])
but failed the chance criterion (C 0.516 [0.497, 0.536]); the wrong-chart C was 0.474. AA births: dC +0.046
[-0.001, +0.089]. Under the pre-registered rule this is a FAIL, so no confirmation was due; this file adds one check, once.

## Test (single, decided now)
- Data: half 1 (never used by any KP-modern analysis), Arrest sets built exactly as in half 0 (all ratings).
- Rules and score: the same 51 KP-modern timing rules and the same weighted engine score (run_bphs_engine.analyse,
  Arrest only, n_tests = 1). The engine score has no fitted parameters, so no date-leak guard is needed.
- CONFIRMED only if all three hold: weighted dC 95% lower bound > 0, C(actual) 95% interval above 0.5, and a clean
  placebo (placebo dC 95% lower bound <= 0) - the primary test's criteria with no multiple-testing correction.
- Reported in any case. No other type, subset, rule subset or score variant will be tried on half 1.

## Expectation (mine, before running)
Not confirmed: dC within +-0.03 and C near 0.5. A lead that fails the chance criterion, with a below-chance wrong-chart
C carrying much of the gap, looks like noise in the control.
