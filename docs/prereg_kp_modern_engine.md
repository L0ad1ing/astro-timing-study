# Pre-registration - "KP modern" rule set, and KP Readers after the full read (committed before any run)

Requested by the author (2026-10-03, "Do both"): read all six KP Readers in full (done; docs/kp_progress_log.md) and add
the later K.P. literature as a separate rule set tested the same way.

## The rule sets
- **KP modern** (source label `KP modern`, 217 rules, 46 timing rules on the tested events): Sub-Lord Speaks (13),
  KP Navaratnamala house-grouping tables (45), KP Astrology for Beginners (18), Astro Secrets & KP (51), KP E-zine
  2007-2021 (90). How each book was read is stated in each module's docstring and in docs/kp_progress_log.md; the e-zine
  was NOT read in full (1,850 extracted rule statements were read). The 46 timing rules cover 16 of the 18 types (none
  for Death of mother or Death of mate).
- **KP Readers, full read** (source label `KP Readers`, 951 rules): the full read added natal rules mainly (for the
  reading engine); timing rules on the tested events went from 65 (docs/prereg_kp_engine.md) to 71.

## Design
Identical to docs/prereg_kp_engine.md (itself identical to the BPHS and Phaladeepika runs): half 0, the same 18 event
types and case-control sets, Olympic-Games prize events removed, the same engine score, primary dC = C(actual) -
C(mismatched chart) with the mismatched chart taking the donor's natal longitudes and birth moment and place for the KP
chart, 2,000 paired bootstraps, Bonferroni over 18, PASS = Bonferroni lower bound > 0 AND C(actual) 95% interval above
0.5 AND clean placebo; confirmation on half 1 for any PASS. Secondary per-rule FDR and learned-combination outputs as before.

- PRIMARY: `--sources "KP modern"`, all ratings.
- SECONDARY 1: `--sources "KP modern" --ratings AA`.
- SECONDARY 2: `--sources "KP Readers"` re-run on the full-read rule set, all ratings. Because only 6 timing rules
  changed, the earlier KP result is expected to repeat; this run checks that.
- Types with no rules in a set are reported as "no rules" and still count in the Bonferroni divisor of 18.

## Notes stated in advance
- Many modern rules use conjoined-period conditions (each of the dasa, bhukti and antara lords signifies the houses, or
  together they cover every house). For broad KP significators such conditions hold on a large share of dates, as with
  the Readers.
- One e-zine natal rule (EZ-CO-01) holds in 95%+ of charts as written; natal rules do not enter the event test.
- The e-zine rules are a selection made by me from extracted statements; that selection was fixed by this commit.

## Expectations (mine, before running)
No type passes in either run; dC within +-0.03 for every type with at least 1,000 sets; per-rule significant counts
about equal in both directions.

## Amendment (2026-10-04, before any KP Readers result was produced)
The KP Readers re-run (secondary 2) crashed: the runner's phase-1 cache was keyed by source name and set list only, so it
loaded the 87-rule cache from the 2026-10-03 KP Readers run for the 167-rule full-read set. The cache key now also holds a
fingerprint of the timing rules (ids, conditions, predictions). The KP modern runs (primary and secondary 1) had no earlier
cache and were computed fresh, so they stand. Nothing else in the design changed.
