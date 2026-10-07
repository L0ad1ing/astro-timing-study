# Pre-registration - William Lilly, Christian Astrology Book III, rule engine (committed before any run)

Requested by the author (2026-10-04): "Valens and Lilly are fine" - encode both books and test each like the others.

## The rule set
Christian Astrology (1647) Book III, the whole book (pp. 524-748): 1,249 rules (docs/lilly_progress_log.md), 656
natal and 593 timing. Engine src/rules/lilly.py: Regiomontanus houses, Lilly's dignities, orbs and fortitude scores,
hyleg and anareta, primary directions (Regiomontanus, direct, Naibod key, +-0.5 yr), annual profections, Lord of the
Year, solar revolutions, planetary returns, transits. Every construction choice is stated in the module and the log
and was fixed before this test.

## Design
Identical to the earlier books (docs/prereg_valens_engine.md): half 0, the same 18 types and case-control sets,
Olympic prize events removed, the same engine score, primary dC = C(actual) - C(mismatched chart), 2,000 paired
bootstraps, Bonferroni over 18, PASS = Bonferroni lower bound > 0 AND C(actual) 95% interval above 0.5 AND clean
placebo; half-1 confirmation for any PASS. Mismatched chart: the donor's whole geometry (positions, cusps, directions
from the donor's birth moment and place), the native's own birth moment driving ages, profections, revolutions and
dates.
`python scripts/run_bphs_engine.py --sources Lilly --prereg docs/prereg_lilly_engine.md`

## Expectations (mine, before running)
No type passes; dC within +-0.02 for Death, Marriage and Career_Peak.
