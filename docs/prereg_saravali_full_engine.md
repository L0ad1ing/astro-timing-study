# Pre-registration - Saravali complete (vols. I-II) rule engine (committed before any run)

Requested by the author (2026-10-04): vol. II supplied; encode the whole book and test it like the others. Supersedes
nothing: the vol. I test (docs/prereg_saravali_engine.md, 0/18) stands as run.

## The rule set
Saravali of Kalyana Varma, R. Santhanam tr., chapters 1-55: 2,510 rules (docs/saravali_progress_log.md), 2,360 natal and
150 timing; 92 timing rules on tested events: Death 33, Illness 21, Career_Peak 18, Arrest 5, Job_End 3, Divorce 2,
Relationship_End 2, Marriage 2, Death_of_relative 2, Accident 1, Relationship_Begin 1, Trial 1, Death of mate 1 (no rules
for Birth_Child, Prize, Job_Start, Death of father, Death of mother). Most vol. II timing rules run on Saravali's own
Moola dasa (src/rules/sar_moola.py), built for this purpose; its construction choices are stated in the module and
were fixed before this test. Also new for vol. II: Saravali rays (sar_rays.py), Saravali Ashtakavarga (sar_av.py).

## Design
Identical to docs/prereg_saravali_engine.md and the earlier books: half 0, the same 18 types and case-control sets,
Olympic prize events removed, the same engine score, primary dC = C(actual) - C(mismatched chart), 2,000 paired
bootstraps, Bonferroni over 18 (types without rules count), PASS = Bonferroni lower bound > 0 AND C(actual) 95% interval
above 0.5 AND clean placebo; half-1 confirmation for any PASS. For the mismatched chart the Moola dasa is built from the
donor's natal positions on the person's own birth moment (as for every dasa in these tests).
`python scripts/run_bphs_engine.py --sources Saravali --prereg docs/prereg_saravali_full_engine.md`

## Expectations (mine, before running)
No type passes; dC within +-0.02 for Death, Illness and Career_Peak.

## Amendment (2026-10-04, after the run of 12:19)
A check of the calculations against the scans found two encoding errors: (1) six timing rules (ch. 5 v. 47-50 'stages'
in a planet's dasa x5, ch. 35 v. 41's timed clause and ch. 36-38's dasa clause) used Vimshottari periods instead of
Saravali's Moola dasa - written before the Moola engine existed; (2) Mars's Ashtakavarga from Saturn included the 4th
(copied from BPHS; the translation's list has no 4th). Both fixed; the same analysis is re-run unchanged as a corrected
run. The verdict of record stays the original run; the corrected run is reported beside it.
