# Pre-registration — planetary strength and dignity, all at once (written and committed before any run)

Requested by the author (2026-10-02): earlier tests ignored whether an activated planet is strong or weak
(friend/enemy sign, exaltation, debilitation...), which classical astrology says decides whether its results are
good or bad. If strong and weak activations push in opposite directions, pooled tests could cancel out. Rather
than pick rules, every standard strength/dignity factor is given to the model, which learns the combinations.

## Strength features (src/strength.py), per planet, from the natal chart (sidereal Lahiri, whole-sign houses)
- Dignity class in D1 and D9 (exalted, moolatrikona, own, great friend, friend, neutral, enemy, great enemy,
  debilitated), via compound (panchadha) friendship = natural (BPHS) + temporal (2,3,4,10,11,12 from the planet);
  numeric dignity score for D1 and D9; vargottama.
- Shadbala components: uchcha bala (exact degree from deep exaltation), dig bala (directional), paksha bala (Moon
  phase, benefic/malefic sense), nathonnatha (day/night), cheshta proxy (speed ratio, retrograde), declination
  (ayana proxy), vara-lord and hora-lord flags (sunrise-based), drik bala proxy (benefic and malefic sign aspects
  received, benefic and malefic conjunctions).
- Full Shadbala as precomputed in the source database (table `shadbala`: sthana, dig, kala, chesta, naisargika,
  drik bala and total, Sun..Saturn), included as given (NaN for Rahu/Ketu and for people without a row). Kala bala
  there covers the temporal components (abda/masa/vara/hora, tribhaga, ayana) that the proxies above do not.
- Ishta phala = sqrt(uchcha x cheshta), kashta phala = sqrt((60-uchcha)(60-cheshta)), cheshta proxy 0-60.
- Combustion (classical orbs), planetary war (Mars..Saturn within 1 deg), baladi avastha (age state by degree,
  odd/even sign), functional nature by Lagna (rules a trikona, a dusthana 6/8/12, a kendra; yogakaraka).
- Natal house from Lagna and from the Moon.
Rahu is treated with Saturn's friendships and Ketu with Mars's (common convention); exaltation Rahu Taurus,
Ketu Scorpio.

## Date-varying features (what can differ between a person's event date and their control dates)
For each activation slot on the date — Vimshottari MD, AD, PD lords; Yogini MD, AD lords; Chara AD sign lord
(Rao convention); Lord of the Year (sidereal profection); Tajika Muntha lord; Mudda dasha lord; Bhrigu Chakra
active-house lord — that planet's full natal strength vector plus the houses it rules and occupies (12 + 12).
Exception: for the three age-cycle slots (Lord of the Year, Muntha lord, Bhrigu Chakra lord) the houses-ruled
mask and the planet's lordship flags (rules a trikona / dusthana / kendra, yogakaraka) are left out, because one of
the houses each rules is by definition the age-determined house (an age clock, the trap models.AGE_CLOCK_COLUMNS
exists for); their strength, dignity and occupied house stay in.
Plus, for transiting Sun, Mercury, Venus, Mars, Jupiter, Saturn, Rahu on the date: dignity score, retrograde,
combustion. These are added to the 706 existing features (models.DEFAULT_COLUMNS).

## Test 1 — timing (primary)
- Data: Astro-Databank, training half (0), known birth times, case-control sets (event vs the same person's
  same calendar date -3, -1, +1, +3 years). Event types (11): Marriage, Death_of_relative, Prize, Arrest,
  Career_Peak, Job_Start, Divorce, Job_End, Trial, Illness, Accident.
- Models (LightGBM LambdaRank, models.PARAMS), 5 folds grouped by person AND event calendar month
  (scripts/harmonic_date_leak_check.grouped_folds): BASE = 706 features; STRENGTH = 706 + strength features;
  DEMO = age + calendar year + sex (discovery_v2.rule_evaluator.Demographic).
- Primary outcome per event type: dC = C(STRENGTH) - C(BASE), paired bootstrap (2,000), Bonferroni over 11
  (0.23%-99.77% interval). Also reported: C(STRENGTH) - C(DEMO).
- CANDIDATE only if: Bonferroni dC vs BASE lower bound > 0, AND dC vs DEMO 95% lower bound > 0, AND placebo C
  (control -1y as event) 95% interval includes 0.5 or lies below, AND mismatched-chart C for STRENGTH (strength
  features recomputed from a random other person's natal chart, own birth moment kept) does not keep the gain
  (mismatched dC vs BASE 95% interval includes 0).
- Confirmation (once, per candidate): model fit on all of half 0, scored on half 1 sets whose event year-month
  does not occur among half-0 events of that type; for Prize, events within +-3 days of an Olympic Games are
  removed (the known artifact, docs/results_discovery_v2_parity_check.json). Pass: dC vs BASE 95% lower bound > 0.

## Test 2 — the mother example: NOT RUN (decided before any run)
The author's claim is graded, not binary: a weak Moon / 4th lord pulls toward a distant mother (little affection,
leaving home early), a strong one toward an over-protective mother (sheltering, staying long). Age at mother's death
does not measure that, and Astro-Databank cannot: of 81,644 biography pages only 13 mention a cold/distant mother and
19 a close/devoted one (regex scan, 2026-10-02). A graded test needs self-reported data (e.g. a 1-7 closeness scale)
from people with verified birth times; proposed separately.

## Expectations (mine, before running)
Test 1: dC vs BASE within +-0.01 for every type; no CANDIDATE. Ashtakavarga, also a classical strength system,
showed nothing earlier. 
