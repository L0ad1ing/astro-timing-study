# Pre-registration - Vettius Valens, Anthologies, rule engine (committed before any run)

Requested by the author (2026-10-04): "Valens and Lilly are fine" - encode both books and test each like the others.

## The rule set
Vettius Valens, Anthologies, Books I-IX (M. Riley's translation): 688 rules (docs/valens_progress_log.md), 368 natal
and 320 timing. Timing rules by target: Positive 73, Negative 42, Illness 35, Career_Peak 28, Trial 25, Marriage 17,
Birth_Child 15, Arrest 13, Accident 12, Death_of_relative 12, Death of father 10, Death of mother 10, Death 6, Job_End 4,
Relationship_Begin 4, Divorce 4, Death of mate 4, Relationship_End 4, Prize 2 (none for Job_Start; Positive/Negative
count toward every positive/negative type as before). Engine: src/rules/west.py - tropical zodiac, whole-sign places,
the operative year (IV.11-25), zodiacal releasing from Fortune and Daimon (IV.4-10), the 10-year-9-month periods
(VI.5), degree-interval transmissions (VI.1), critical years (III.15, V.2, V.12, IX.4), transits by degree (V.9),
the nine-year zones (IX.3), the node length-of-life count (III.13). Every construction choice is stated in the module
and the log and was fixed before this test; two methods reproduce Valens' own worked examples (IV.4, IV.8, VI.5).

## Design
Identical to the earlier books (docs/prereg_saravali_full_engine.md): half 0, the same 18 types and case-control sets,
Olympic prize events removed, the same engine score, primary dC = C(actual) - C(mismatched chart), 2,000 paired
bootstraps, Bonferroni over 18 (types without rules count), PASS = Bonferroni lower bound > 0 AND C(actual) 95% interval
above 0.5 AND clean placebo; half-1 confirmation for any PASS. Mismatched chart for the Western rules: the donor's
whole natal chart (positions, angles, Lots from the donor's birth moment and place, as for KP), with the native's own
birth moment driving ages, periods and dates.
`python scripts/run_bphs_engine.py --sources Valens --prereg docs/prereg_valens_engine.md`

## Expectations (mine, before running)
No type passes; dC within +-0.02 for Death, Illness and Career_Peak.
