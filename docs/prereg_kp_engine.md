# Pre-registration — KP Readers rule engine (committed before any run)

Requested by the author (2026-10-03): complete the KP Readers and test them like BPHS and Phaladeepika.
K.S. Krishnamurti's KP Readers I-VI were read (docs/kp_progress_log.md): 258 rules, 87 timing rules that predict a
datable event (marriage, divorce, children, job start/end, promotion, deaths, illness, accident, arrest, litigation,
prizes), built on src/rules/kp_core.py (Krishnamurti ayanamsa, Placidus cusps, star and sub lords, significators;
validated against Reader V's worked chart).

## Design
Identical to docs/prereg_bphs_engine.md and docs/prereg_phaladeepika_engine.md: half 0, the same 18 event types, the same
case-control sets, Olympic-Games prize events removed, the same engine score (signed weighted sum of the relevant fired
rules, with the reader's weighting and effects), primary dC = C(actual) - C(mismatched chart), 2,000 paired bootstraps,
Bonferroni over 18, PASS = Bonferroni lower bound > 0 AND C(actual) 95% interval above 0.5 AND clean placebo;
confirmation on half 1 for any PASS. Secondary: unweighted and direct-only variants, per-rule FDR, learned combination
vs age + year + sex.

KP-specific, decided now:
- The mismatched chart takes a random other person's natal longitudes AND their birth moment and place for the KP
  chart (cusps, KP positions); the person's own birth moment still drives the dasas and the dates.
- PRIMARY: `--sources "KP Readers"` (87 timing rules), all Rodden ratings in the sets (AA 21,583 / A 4,262 / B 1,768
  sets in half 0, before the Ascendant filter).
- SECONDARY 1: the same, AA-rated births only (`--ratings AA`) - KP depends on the exact minute of birth (cusp sub lords
  change every few minutes), so AA is the fairest subset. Reported, and a PASS there also needs half-1 confirmation on
  AA births.
- SECONDARY 2: all three books together (`--sources "BPHS,Phaladeepika,KP Readers"`).

## Notes stated in advance
- KP significators are broad (a planet typically signifies 4-6 houses), so the conjoined-period conditions hold for a
  large share of dates (for the author's chart, 49% of life for marriage and children windows); low discrimination is a
  property of the method as written.
- Even AA times are usually rounded to the minute or 5 minutes; a time error of a few minutes can change a cusp sub lord.

## Expectations (mine, before running)
No type passes in any run; dC within +-0.03; per-rule significant counts about equal in both directions.

## Amendment (2026-10-03, before any result was produced)
The first run stopped in phase 1 with a Swiss Ephemeris error: Placidus cusps cannot be computed for births near the
poles (|latitude| above about 66 degrees), where the method is undefined. The engine now returns no KP chart for such
births, so no KP rule fires for them (the same as KP being inapplicable). No result of any kind had been produced.
Nothing else in the design changed.
