# William Lilly, Christian Astrology Book III - encoding log

Source: Christian Astrology (London, 1647), Book III (nativities), pp. 524-748; archive.org scan, OCR'd twice
(data/sources/western/lilly_v13.txt used throughout; lilly_djvu.txt for pp. 588-590 where the first is illegible).
Books I-II only for the apparatus Book III relies on (dignity table p. 104, orbs p. 107, fortitudes table p. 115,
checked against the Houlding edition text, lilly_2022.txt). Paraphrase + citation only; sources gitignored.

## Engine (src/rules/lilly.py, 'w_l_' atoms dispatched from src/rules/west.py)
- Tropical; Regiomontanus houses; a point within 5 deg before a cusp belongs to that house.
- Dignities after Ptolemy as Lilly tables them (triplicity Fire Sun/Jupiter, Earth Venus/Moon, Air Saturn/Mercury,
  Water Mars; Ptolemy's terms; Chaldean faces); the p. 115 fortitude/debility scores; mutual reception.
- Orbs p. 107 (Saturn 10, Jupiter 12, Mars 7.5, Sun 17, Venus 8, Mercury 7, Moon 12.5), aspects within the moieties;
  to a non-planet point the planet's moiety (choice). Partile = within 1 deg.
- Part of Fortune = Asc + Moon - Sun day and night. Combust 8.5, under beams 17, cazimi 17'.
- Hyleg p. 527-529; anareta p. 529-530; Lord of the Geniture = highest total score (p. 532); temperament p. 532-534
  (testimony count; ties broken by the sign ascending - choice); significator of manners p. 535.
- Primary directions: Regiomontanus circles of position (vectorised; verified against hand-computed OA/RA arcs to the
  Ascendant and MC), direct only, Naibod key 0 deg 59'08" (Lilly's preferred measure, p. 712); promittors: bodies
  with latitude, zodiacal aspects without latitude, term beginnings, cusps, Node/Tail/PF/Asc/MC, 30 fixed stars
  (J2000 precessed at 50.29"/yr, latitudes fixed). A direction operates within +-0.5 yr of its arc (choice).
  Births at |lat| >= 66: no directions.
- Annual profections: every point + 30 deg per completed year (p. 715); Lord of the Year = lord of the profected
  Ascendant's sign (first lord only - choice); revolution = the last solar return before the date, erected for the
  birthplace; planetary returns within the returning planet's moiety (choice); transits within 1 deg (Moon 6,
  Mercury/Venus 1.5 - choice); alfridaries 7 years each (no judgements given).
- p. 708: marriage/new relationships only predicted in the 16th-75th year, a child in the 16th-60th (ages a choice).
- Mismatched-chart control: the donor's whole geometry (kp_birth), the native's own birth moment for ages/dates.

## Rules (1,249: 656 natal, 593 timing)
b3_intro 108 (CII-CVIII), b3_wit_wealth 148 (CIX-CXIX), b3_kin_health 83 (CXX-CXXVII, 6th house), b3_marriage 132
(CXXVIII-CXXXVII), b3_children_travel 73 (5th, 9th), b3_honour_friends 83 (10th, 11th), b3_enemies_death 58 (12th,
8th), b3_directions 427 (CLVI-CLXV: Asc, MC, Sun, Moon, PF to bodies/aspects/terms/cusps/stars), b3_annual 137
(CLXVI-CLXXIV). Direction passages are split into one rule per distinct testable accident; Lilly's stated
conditions (e.g. "death if Saturn be anareta", "if age permit he marries") are encoded as conditions.
Timing targets: Positive 146, Negative 94, Career_Peak 62, Illness 54, Marriage 35, Trial 33, Death 22, Arrest 22,
Job_Start 17, Accident 17, Job_End 16, Birth_Child 13, Relationship_End 9, Death of mother 9, Death of father 8,
Death of mate 7, Relationship_Begin 5, Prize 5, Death_of_relative 3, Divorce 2; 14 domain-only.
Not encoded (logged per module): comparisons of two nativities, rectification, descriptive lists (colour, trades,
dreams, countries), stars outside the engine's list, illegible OCR passages, sexual-conduct configurations.

- LILLY COMPLETE (Book III): 1,249 rules.

## Test (2026-10-04, pre-registered docs/prereg_lilly_engine.md, e1aaef0)
First run killed by the OS for low memory at 7,000/27,352 sets (AbraxasV3/Ollama holding ~3.3 GB); rerun unchanged
with Abraxas paused: results_engine_Lilly_20261004_2250.json - 0 / 18 types pass (expected). Death dC +0.005,
Marriage +0.006, Career_Peak -0.001; per rule 2,301 tests, 0 FDR, 53 for / 57 against at p<.05. Learned
Death_of_relative dC +0.039 vs a demographic baseline of 0.461 (rules 0.500) - artefact, not pursued.
