# Pre-registration - Discovery v3: a fresh, book-free search for timing patterns (committed before any run)

Requested by the author (2026-10-05): after every rule of seven books failed (docs/prereg_full_programme.md), "come up
with new predictions" - option 2: search the data directly, find candidates on one half, test them once on the other.

## Lessons built in (from earlier searches, docs/results_harmonic*, results_discovery_v2*)
- Shared-date leakage and calendar cycles (award nights, Olympics): every comparison is the person's real chart against
  a donor chart ON THE SAME DATES, so anything about the date itself cancels.
- Age disguised as astrology: a donor born within +-15 days of the native (slow planets nearly identical, so planetary
  returns and other age-locked cycles cancel); features where a body aspects its own natal place are excluded.
- Annual cycles: control dates at half-year offsets (as T2 of the programme), so Sun-related features vary.

## Data
Astro-Databank case-control sets (the 18 event types, Olympic prize dates removed, known birth times), control dates
at half-year offsets (Death -4.5..-1.5; others -2.5, -0.5, +1.5, +3.5 years). Discovery on half 0 only; confirmation
on half 1 only, once. Disclosure: half 1 has already served two earlier single pre-registered confirmations (KP-modern
arrest, KP relative deaths); it has never been used for discovery.

## Features (per date, per chart; tropical zodiac, Moshier, event dates at noon UT)
- Transits: Sun, Mercury, Venus, Mars, Jupiter, Saturn, mean Node, Uranus, Neptune, Pluto (the Moon is left out: noon
  dates fix it only to +-6.5 deg) in conjunction, sextile, square, trine or opposition, within 2 deg, to the natal Sun,
  Moon, Mercury, Venus, Mars, Jupiter, Saturn, Node, Ascendant, MC - excluding a body to its own natal place.
- Secondary progressions (a day for a year): the progressed Sun and Moon in those aspects within 1 deg to the natal
  points (excluding each to its own natal place).
- Vimshottari periods from the sidereal (Lahiri) Moon: mahadasha lord (9), antardasha lord (9), the pair (81).
About 700 binary features.

## D1 - is there any personal pattern at all? (single global test, half 0)
People with two or more events of the same type. For each pair of their same-type events: similarity of the two
dates' feature vectors (Jaccard over transits and progressions, plus agreement of mahadasha and antardasha lords)
computed against the real chart minus the same computed against the donor chart. Statistic: the mean over people of
their mean pair difference; 2,000 person bootstraps. PASS: 95% interval above 0. A PASS goes to half 1 once.

## D2 - specific new rules
For a feature f and type t, per set: u = f(event) - mean f(valid controls), on the real chart and the donor chart;
delta = u_real - u_donor; T = mean delta over the type's sets, z = T / SE. Discovery (half 0): per type, the 10
features with the largest |z| among those with delta != 0 in at least 30 sets (the sign of z is the candidate's claimed
direction). Confirmation (half 1): the same statistic for each candidate, one-sided in its claimed direction;
CONFIRMED if p < 0.05 / (number of candidates) (Bonferroni, about 180) and the interval from a bootstrap clustered by
event date also excludes 0. Anything confirmed is reported as a new candidate rule needing an independent dataset; a
tripwire report gives each candidate's correlation with age and calendar year.

## Expectations (mine, before running)
D1 does not pass; in D2 nothing confirms (the half-0 top z-scores will look impressive - about 3.5-4 is what ~12,000
null tests produce).

## Results (2026-10-05)
- D1 (half 0, results_discovery_v3_half0_*.json): 675 people with repeated same-type events, 816 pairs; similarity
  real minus donor +0.003 [-0.005, +0.012] - no pass (repeat events are not more alike against the native's own chart).
- D2: half-0 top |z| 2.8-4.1 per type (null-sized for ~12,000 tests); 166 candidates frozen (commit 6cf7be2) before
  half 1. Half 1 (results_discovery_v3_half1_*.json): 0 of 166 confirmed at the Bonferroni level.
- Post hoc (not pre-registered, reported for completeness): the statistic is calibrated on half 1 (sd of z over all
  5,671 feature x type tests 1.03); 18 candidates reached p<.05 in their claimed direction vs about 9 expected and 7
  in the opposite direction; mean candidate z on half 1 +0.20. Candidates within a type overlap (dasha lord / lord pair),
  so this aggregate excess is weaker than it looks; no individual pattern replicated. Expectation met.
