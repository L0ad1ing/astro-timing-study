# KP Readers — progress log (resume from the last entry)

Source: K.S. Krishnamurti, Krishnamurti Padhdhati Readers I-VI, OCR text supplied by the author (2026-10-03) from
`Downloads/kp-readers (1)`, copied to data/sources/kp/reader1..6.txt (local, gitignored). Paraphrase + citation only.
Citations give the Reader and the printed page number where the OCR shows it (page footers like '68 PREDICTIVE STELLAR
ASTROLOGY'), otherwise the text line ('R3 l.4847').
Reader I casting the horoscope; II fundamental principles; III predictive stellar astrology; IV marriage, married
life, children; V transits (Gocharapala Nirnayam; its first ~140 pp. repeat Reader III's theory); VI horary.
The folder also has KP e-zines, Navratnamala, 'KP sublord SPK' and 'Astro secrets' - later authors, not used.

## Engine (src/rules/kp_core.py)
- Ayanamsa: Krishnamurti (R1 pp. 56-58: coincidence 291 A.D., Newcomb's rate) = swisseph SIDM_KRISHNAMURTI.
- Houses: Placidus (R1 'method in common use is that followed by Placidus', Raphael's tables), cusp to cusp (R4 p. 111).
- Star and sub lords: R3 pp. 10-12; checked against the book's examples (Bharani's first sub Venus, 20/120 -> Sun;
  Sagittarius 26-40..30 = Sun, Moon, Mars, Rahu subs, R3 pp. 64-65).
- Significators (R4 p. 111; R3 the 'rule is ever universal' passage): (1) planets in the star of an occupant,
  (2) occupants, (3) planets in the star of the lord, (4) the lord. Nodes act for conjoined planets / sign lord
  (R3 pp. 41-42).

## Log
- 2026-10-03 — Read: R3 pp. 3-14 (system, sub division), pp. 41-44 (star significations by lagna), pp. 62-69 (role
  of sub), pp. 131-141 (benefic/malefic; cusp sub-lord as significator of house pairs). R4 pp. 71-74 (marriage
  promised / delayed - traditional rules quoted). R4 p. 111 significators. kp_core built and checked.
- 2026-10-03 — Also read: R3 pp. 155-169 (longevity, badhaka, maraka, mode/place of death), 203-204 (8th cusp, debts),
  229-230 (mother: 4th as lagna), 258-259 (4th cusp vehicle, education), 279-281 (6th cusp disease, hospital),
  321 (12th cusp foreign), 341 (self-acquisition 2-6-10), 360-363 (10th/5th cusp professions), 384-385 (regaining
  position 10-11; retirement 1-5-9), 405-407 (imprisonment 2 & 12, release 2 & 11). R4 pp. 107-126 (marriage: 7th cusp
  sub lord; significators of 2-7-11 with sub filter; transit confirmation), 176 (promotion 2-6-10-11), 191-192
  (divorce 1-6-12), 210-217 (children 2-5-11), 231. R6 (father: 9th as lagna), p. 214 (litigation 2-6-11).
- ENCODED rules/kp/core.py (69 rules: promises by cusp sub lords, timing by significator periods for marriage,
  divorce, children, job, promotion, retirement, death, accident, illness, imprisonment, litigation, deaths of
  mother/father/spouse, awards). Engine atoms kp_csl, kp_csl_star, kp_csl_lordship, kp_sig, kp_dasha,
  kp_badhaka_dasha, kp_cusp_chain_dasha, kp_transit_star; Chart.kp / kp_date (KP Moon, own birth moment).
  0 errors on 300 real charts. Author's reading (private artifact) now includes a KP section.
- NOT YET READ in full: R2 (fundamental principles), the rest of R3 (practical chapters on finance, house, disease
  details, education, profession lists), R4 remainder (married life, love, second marriage, children details), R5
  (transits), R6 (horary - mostly untestable). NEXT: continue chapter by chapter; then pre-register the KP test.
- R3 pp. 170-212 read and encoded: rules/kp/r3_finance_health.py (60). New atoms kp_cusp_star_lordship, kp_majority_8_12, kp_no_cure, kp_lord_dasha, kp_jup_on_dasha_sign, kp_planet_sig_both, kp_dasha_sig_pair etc. NEXT: R3 l.13640 (brothers).
- R3 pp. 216-447 read and encoded: rules/kp/r3_life.py (66). Note: rules of the form 'the cusp sub lord signifies X' fire for 80-92% of charts (KP significators cover ~4-6 houses per planet) - faithful but weakly discriminating. R3 now fully read (pp. 448-490 traditional dasa results quoted and disclaimed by the author; horary chapters logged). NEXT: R4 remainder.
- R4 read (lines 1-17272) and encoded: rules/kp/r4_marriage_children.py (29). Mars dosha with exceptions (cancel effect), Punarphoo, separation, second marriage, 11th-cusp harmony, partner's death, safe delivery, lagna sub lord by house. Partner and love description tables logged (descriptive). NEXT: R5.
- R5 read and encoded: rules/kp/r5_transits.py (14): transit star/sub rule, DBA point trigger (p. 162), ashtama Sani, retrograde. kp_core validated against R5's worked chart (test_kp_chart_matches_reader5_example). NEXT: R2, R6, R1.
- R2 read (lines 1-21495; significations of signs, houses, planets - descriptive) and encoded: rules/kp/r2_nodes.py (14,
  node rules pp. 452-462, house connections p. 282). R6 read (horary; query-chart methods logged) and encoded:
  rules/kp/r6_horary.py (6, longevity/accident sub-lord rules pp. 156-159 applied natally). R1 = calculations (engine).
- *** KP READERS COMPLETE (2026-10-03): 258 rules (171 natal, 87 timing with events) across core, r2_nodes,
  r3_finance_health, r3_life, r4_marriage_children, r5_transits, r6_horary. Whole rule base 4,312.
  NEXT: pre-registered KP test (docs/prereg_kp_engine.md).
- 2026-10-03 — PRE-REGISTERED KP TEST (docs/prereg_kp_engine.md, b19b6f8 + amendment bcc244f):
  PRIMARY (KP alone, 87 timing rules; docs/results_engine_KP Readers_20261003_1719.json): 0 of 18 pass; Death dC +0.003
  [-0.008, 0.013], Marriage -0.011; per rule 266 tests, 0 FDR-significant, p<.05 5 for vs 7 against.
  SECONDARY 1 (AA births; results_engine_KP Readers_AA_20261003_1722.json): 0 of 18; per rule 248 tests, 0 FDR, 3 vs 9.
  Learned combination (secondary, not decisive): Death_of_relative RULES 0.500 vs DEMO 0.461, Bonferroni [0.0045, 0.073],
  placebo 0.479 (all ratings); AA: [0.0043, 0.089], placebo 0.491 - AA is a subset of the same half, so not independent;
  the prereg gives secondary analyses no confirmation path - it would need its own pre-registered half-1 test.
  SECONDARY 2 (all three books): stopped by the system for low memory in phase 1 - not yet run.
- SECONDARY 2 (all three books, 2,579 timing rules; results_engine_BPHS+Phaladeepika+KP Readers_20261003_1811.json): 0 of
  18; per rule 9,912 tests, 0 FDR-significant, p<.05 213 for vs 226 against. (AbraxasV3 paused for the run, restarted.)
- KP learned-model lead, single pre-registered half-1 confirmation (prereg_kp_relative_confirm.md,
  results_kp_relative_confirm_*.json): RULES C 0.488 [0.458, 0.514], dC vs DEMO +0.020 [-0.022, 0.062] - NOT confirmed.
- Write-up: docs/writeup_classical_rule_engine.md (all three books, all tests).

## Full page-by-page pass (user, 2026-10-03: "Do both" - read every Reader fully, then the later KP books separately)
Module rules/kp/r3_full.py (source label stays 'KP Readers'; ids KP3F-*). These rules were added AFTER the KP test;
the pre-registered results above cover only the 258 first-pass rules.
- R3 lines 14330-18660 (pp. 236-309): house, vehicles (quoted traditional combinations), vehicle accidents, education,
  mathematics, law, engineering, medicine, philosophy, music, competitive exams, scholarship, farming, loan clearing,
  disease nature by the 6th sub lord's sign (Sun/Moon/Mars/Mercury tables; the book gives no Jupiter/Venus/Saturn tables),
  nodes in 2/12, traditional marriage-promise and late-marriage lists (quoted). 123 rules. Engine: new atom conj_orb.
  Logged untestable per range in the module's UNTESTABLE list.
- R3 lines 18660-24600 (pp. 309-405): overseas study, profession by 10th-cusp sign/star/sub (Aries pairs, Sun sub lord by house),
  business (planets in 7, Saturn sub), music (5th sub lord), retirement, pension, ministers (quoted), friends and losses via
  lords in the star of other lords, gifts, imprisonment (quoted). Total r3_full 234. Atoms: kp_cusp_lords, kp_occ_in_star_of_lord,
  kp_csl_starlord_sign, kp_csl_pos, kp_cusplord_sub, kp_lord_in_star_of_lord, kp_csl_retro.
- R3 lines 24600-32362 (pp. 405-end): KP imprisonment, spiritual life, Q&A (truthfulness, spending, partners, speculation, books),
  Road to Success (12 sign sketches from the lagna sub lord's star lord), owned-house placement 6/8/12 from itself; horary,
  horas, rectification, annual charts, Ashtakavarga (rejected) and glossary logged. r3_full = 283 rules; atom kp_star_sub.
- R3 early ranges (lines 1-8310, 13700-14060): front matter, star zones, 249-sub table (descriptive, logged); brothers and
  mother (pp. 225-231) encoded. READER III COMPLETE: r3_full = 303 rules. Fire-rate check on 150 charts: no errors; 74 rules
  never fired (rare combinations - disease table, Aries meridian pairs, Aries-lagna Sun table); KP3F-PL-01 fired in 95%
  (misread "and" as "or") - corrected to all four planets. NEXT: R4, R5, R6, R2, R1 full read.
- R4 full pass (all 17,272 lines; module rules/kp/r4_full.py, 157 rules, ids KP4F-*): further Mars-dosha exceptions (cancel
  KP4-MD-01), Saturn-Moon delays, married life without Western aspects, the 7th-sub-lord partner table (84 cells, for readings),
  career partner, chaste partner, lagna sub lord temperament, denial via the 7th sub lord's star, love by the 5th sub lord's
  sign (12), son-in-law, divorce/desertion/kidnapping/return timing, child promise/denial lists (quoted), Beeja/Kshetra, adoption,
  Kerala santana tithi, short-lived child, impotence (quoted), first-issue rule. Atoms: kp_sub_sig, santana_tithi_kerala.
  Fire-rate check: no errors; 15 never fired (gender-gated rules - the check script has no gender - and rare cells).
  NEXT: R5, R6, R2, R1 full read.
- R5 full pass (rules/kp/r5_full.py, 36 rules): the Moon in the 8th by lagna (house it owns) and nakshatra, timed to Moon
  periods (pp. 383-388); Moon with many planets in 8. Rest = R3 theory repeated, the K.P. transit procedure (r5_transits),
  elections and a 1964 Saturn forecast (logged).
- R6 full pass (rules/kp/r6_full.py, 66 rules): the "How to judge?" sign tables (appearance/character, health, money, love by
  the sign of the star lord of the 1st/6th/2nd/5th-7th cusp sub lords; horary tables applied to natal charts as K.P. does),
  cusp sub lord in a combust planet's star by cusp (timed to the sub lord's periods), Sun conjunctions and short-life
  combinations (Western, quoted). Atoms: kp_csl_star_combust, kp_csl_dasha. The worked horaries (pp. 160-end) logged.
- R2 full pass (rules/kp/r2_full.py, 131 rules): ascendant-sign descriptions (appearance/character, health, money, profession,
  marriage, children; pp. 116-265), planet-in-house statements of the house chapter (traditional/Western, unafflicted forms
  only; pp. 266-345), Rahu and Ketu in each house (Kalidasa, pp. 454-458), the Sun's profession combinations (pp. 350-352).
  Logged: history, definitions, house significations, planet karakatvas, Uranus/Neptune.
- R1 full pass: casting the horoscope (time, ephemeris, ayanamsa, houses, dasa balance), Hindu and Western aspects and
  "principles of judgment" (aspect strength and quality - method), worked casting example. No outcome rules; logged.
- FULL READ OF READERS I-VI COMPLETE (2026-10-04).

## "KP modern" rule set (user, 2026-10-03: test the later KP books separately) - rules/kp_modern/, source label 'KP modern'
Books copied to data/sources/kp_modern/ (gitignored). Citations = book + source-text line (OCR keeps few printed pages).
- Sub-Lord Speaks (spk.py, 13 rules): lines 1-2,160 and 24,136-end read paragraph by paragraph; the case studies in
  between scanned for rule statements (not read case by case). Principle: a period lord's SUB LORD decides (illness 6,
  danger 8, confinement 12; marriage 2-7-11, children 2-5-11, service 2-6-10-11, loss of service 9, divorce 6-10-12, love
  fails 4-6-12); cusp sub lords signifying 1/2/3/6/10/11 divert a house's evils; 11th sub lord in 10 weakens badhaka.
- Navaratnamala (navratnamala.py, 45 rules): the KP House Grouping Tables read paragraph by paragraph (source lines
  10,135-12,750; OCR columns often scrambled - only readable entries encoded, as natal promise by cusp sub lord plus timing by
  joint significators, 24 events); medical studies scanned for their stated conclusions (4 encoded, approximated); lists
  and calculation tables logged.
- Astrology for Beginners (beginners.py, 18 rules): scanned whole for rule statements, passages read in context; new:
  Fortuna (Asc+Moon-Sun) sub lord's significations = field of luck (12) and Fortuna's house; child via Jupiter-star planet in
  the 11th lord's sub; 7th significator in sub of 2/11 vs 6/12; lagna lord in a maraka sub gives death; lord of 2 in 6.
  Atoms: kp_fortuna, kp_period_star_is. The rest repeats the Readers (logged).
- Astro Secrets & KP (astrosecrets.py, 51 rules): part 1 theory chapters (lines 1-8,700) read by paragraph and rule scan -
  lagna-lord grades, 2nd-cusp wealth "vessels", cuspal sub lords by house, badhaka lord, Saturn benefic / Jupiter malefic
  conditions, Saturn-aspected 6th lord and imprisonment, accident; parts 2-6 scanned for rule statements, encoding only
  those not already in the Readers (a cusp-by-cusp digest, lines 33,850-35,260). Atom: kp_csl_starlord_house; kp_planet_house
  accepts 'kplord:N'; kp_star_sub resolves refs.
- KP E-zine 2007-2021 (ezine.py, 90 rules; 13 timing): NOT read in full (1.95M OCR lines). Method: condensed to paragraphs,
  every sentence with a condition word + a K.P. term + an outcome cue extracted and de-duplicated (1,850 statements), and all
  1,850 read. Encoded only what is new relative to the Readers: 5/8 added for marriage, joint DBA coverage (kp_dba_cover),
  cusp sub-sub lords (kp_cssl), 9th cusp for second marriage, divorce initiators, Punarphoo delay, foreign-stay duration by
  the 12th sub lord's sign quality, education grades by the 4th/9th/11th sub lords, loans and speculative loss, property,
  politics, friends, longevity and accident grades. Horary, ruling-planet, rectification, mundane, election and share-market
  statements skipped (logged as untestable). Fire check over 150 charts: none never fires; EZ-CO-01 fires in 95%+ as written.
- KP modern total: 217 rules, 46 timing rules on the tested events. Pre-registered in docs/prereg_kp_modern_engine.md.
