# Pre-registration - Saravali vol. I rule engine (committed before any run)

Requested by the author (2026-10-04): Saravali, from the scan he supplied, encoded and tested like the other books.

## The rule set
Saravali of Kalyana Varma, R. Santhanam's translation (1983), VOL. I ONLY (chapters 1-26; vol. II not supplied):
1,016 rules (docs/saravali_progress_log.md), 989 natal and 27 timing. Timing rules on the tested events: 25 -
Death 23 (fateful degrees of the Moon - death at the age equal to the degree; Jupiter's fatal ages by house; "death in
the year of the sign"; the mahadasa of a debilitated planet), Career_Peak 1 (mahadasa of an exalted planet), Illness 1
(mahadasa of a planet in an inimical sign). Vol. I contains no dasha chapter, so 15 of the 18 types have no rules.

## Design
Identical to docs/prereg_kp_modern_engine.md and the earlier books: half 0, the same 18 event types and case-control
sets, Olympic prize events removed, the same engine score, primary dC = C(actual) - C(mismatched chart), 2,000 paired
bootstraps, Bonferroni over 18 (types without rules still count), PASS = Bonferroni lower bound > 0 AND C(actual) 95%
interval above 0.5 AND clean placebo; half-1 confirmation for any PASS. Command:
`python scripts/run_bphs_engine.py --sources Saravali --prereg docs/prereg_saravali_engine.md`.

## Notes stated in advance
- The Death rules are age-specific: a person whose Moon or Jupiter placement names an age scores only on dates at that
  age, so most sets will be ties (no rule fires on any date) and contribute C = 0.5.
- The person's own dates are the controls, so the age-specific rules are compared with the same person at other ages;
  the mismatched chart controls for the age distribution of deaths.

## Expectations (mine, before running)
No type passes; Death dC within +-0.01 (most sets tied).
