# Vettius Valens, Anthologies - encoding log

Source: M. Riley's translation (made public 2010; PDF from skyscript.co.uk, local copy in data/sources/western/,
gitignored). Citations: book.chapter, Riley's printed page, Kroll page where marked. Paraphrase + citation only.
Engine: src/rules/west.py (tropical zodiac, whole-sign places, sign aspects; choices listed in its docstring).
Requested by the author 2026-10-04 ("Valens and Lilly are fine").

- Book I read (pp. 1-24), rules/valens/b1.py, 187 rules: Ascendant signs, the term of the rising degree, the Moon's
  3rd/7th/40th days, the node, the transit table (I.21 - counted from each star's natal sign, a choice), 19 pairs and
  32 triples of stars ('together' or in trine, per II.16). Computation chapters and conception logged.
- Book II read (pp. 25-57), rules/valens/b2.py, 187 rules: triangle rulers, the star allotted the Lot, the twelve
  places, configurations (II.16), the Lots (Fortune, Daimon, Basis, Exaltation, Accomplishment, Debt, Theft, Deceit,
  Foreign Lands, Father, Marriage, Children, Brothers), parents, free/slave, injuries, marriage, children, brothers,
  violent death. New engine pieces: pre-natal lunation point (Syzygy), exact-orb atom. Sexual-conduct/incest
  configurations deliberately not encoded (as for Phaladeepika XI). Abraham's travel distribution (II.29) logged
  (travel is not a test event).
- Books III-IV read (pp. 58-94), rules/valens/b3_4.py, 174 rules. New engine timing (src/rules/west.py): the operative
  year (IV.11: the year sent (completed years mod 12) signs on, to the stars there or the ruler of an empty sign -
  the empty-sign rule applied to every transmitter, a choice), zodiacal releasing from the Lot of Fortune and Daimon
  at two levels with the 'loosing' to the opposite sign after a full cycle (IV.4; Daimon from the next sign when the
  Lots share one), III.15 critical years, III.13 length of life from the new/full moon to the node by rising times
  (oblique ascension at the birth latitude; counts over 120 years treated as no prediction). Checked against Valens'
  own examples: IV.8 (Lot in Leo: 62 years to Scorpio, then Sagittarius) and IV.4 (Gemini 20 years: after 17y7m the
  sub-periods restart from Sagittarius) reproduce. Rules: IV.5/7/10 releasing judgements, IV.11-16 operative-year
  places, IV.17-24 the full table of transmissions (each star to each star and the Ascendant), IV.25 the Lots.
  Length-of-life methods needing open judgements (control, houseruler deductions), the quarter periods, Critodemus'
  28-year scheme and Seuthos' month/day logged.
- Books V-IX read (pp. 95-172), rules/valens/b5_9.py, 140 rules. New engine timing: the Crisis-Producing Place and
  V.2 critical point, years of life (Critodemus' table V.12; IX.4), transits within 3 deg to natal points (V.9 'degree
  motions'), VI.1 degree-interval transmissions (arc x days per degree, in cycles, +-3 deg), VI.5 the 10-year-9-month
  periods (apheta = sect light unless preceding an angle, then the other light, then the star after the Ascendant;
  order and sub-periods reproduce Valens' own VI.5 example), IX.3 nine-year zones from the Moon. VII (sums of rising
  times and periods fitted to events), VIII (tables), IX.6-19 (length-of-life calculations, obscure), the operative
  month/day and Initiatives logged.
- VALENS COMPLETE (Books I-IX): 688 rules (b1 187, b2 187, b3_4 174, b5_9 140).

## Test (2026-10-04, pre-registered docs/prereg_valens_engine.md)
results_engine_Valens_20261004_1957.json: 0 / 18 types pass (expectation stated before the run: none). Death dC -0.001;
per rule 1,130 tests, 0 FDR-significant, 25 for / 31 against at p<.05. Learned model: relatives' deaths dC +0.036
[+0.001, +0.071] vs a demographic model at 0.461 (rules model 0.497) - secondary, not a lead worth confirming;
relationship begin dC -0.098 (against).
