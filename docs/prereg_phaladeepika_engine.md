# Pre-registration — Phaladeepika rule engine, and BPHS + Phaladeepika together (committed before any run)

Requested by the author (2026-10-03): continue with the other classical texts and test them the same way.
Phaladeepika (Mantreswara, tr. V. Subrahmanya Sastri) was read in full, all 28 adhyayas (docs/phaladeepika_progress_log.md):
1,357 rules, 568 timing rules that predict a datable event.

## Design
Identical to docs/prereg_bphs_engine.md (same data, half 0, the same 18 event types and label subsets, the same
case-control sets, Olympic-Games prize events removed, the same engine score, mismatched-chart null with numpy seed
7, primary dC with 2,000 paired bootstraps and Bonferroni over 18, the same PASS rule and the same placebo, the same
secondary analyses and confirmation on half 1). Script: scripts/run_bphs_engine.py with --sources.

Two runs, decided now:
- PRIMARY: `--sources Phaladeepika` - only rules read from the Phaladeepika text (568 timing rules). The 5 rules
  from BPHS translator's notes that quote Phaladeepika are not included.
- SECONDARY: `--sources BPHS,Phaladeepika` - both books in one engine (2,492 timing rules), cross-book effects active.
  A PASS here is reported as a finding only if it also confirms on half 1, same rule.

Rules that need data the set lacks simply do not fire (e.g. Mandi needs the birth place; it is present for nearly
all sets). Phaladeepika timing rule groups: dasha results by dignity, bhava lords and every MD x AD pair (XIX-XXI),
marriage and childbirth timing (X, XII), death by transits (XIII, XVII), Ashtakavarga transits and years (XXIII-
XXIV), gochara from the Moon with vedha, star transits and Lattas (XXVI), Kalachakra gatis (XXII), bhava transits (XVI).

## Notes stated in advance
- XVI v. 31 transit triggers and XX v. 36 fire on ~80% of dates (the book's own unions of conditions); they add
  little discrimination by construction.
- Many XXVI rules depend only on the sky and the natal Moon; the mismatched-chart null changes the natal Moon, so
  they are tested properly.

## Expectations (mine, before running)
No type passes in either run; dC within +-0.03; per-rule significant counts about equal in both directions.

## Disclosure
A 300-set smoke test (every-n-th sample of half 0) was run once to check the code before this file was committed
(output in data/, marked invalid). Nothing in the design was changed after it.
