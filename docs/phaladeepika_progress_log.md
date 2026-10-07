# Phaladeepika — progress log (resume from the last entry)

Source: Phaladeepika of Mantreswara, tr. V. Subrahmanya Sastri (Bangalore, 1937), DLI scan
archive.org/details/in.ernet.dli.2015.406048 -> data/sources/phaladeepika.pdf (438 PDF pages, local, gitignored).
The scan's OCR text is unusable (Hindi OCR on English); pages are read as images (data/sources/render2.py, two-up).
Book page = PDF page - 30 at the start (PDF 31 = book 1); the offset drifts (PDF 300 = book 278), so every rule
cites the printed book page. Errata list on PDF 30 (book p. 142: 'disorders), hernia, fever'; p. 199 'acquisition').
Second DLI copy in.ernet.dli.2015.312465 for missing pages. Paraphrase + citation only (as for BPHS).

Rules: rules/phaladeepika/chNN.py -> rules/phaladeepika_chNN.jsonl (registered in rules/build.py CHAPTERS).

## Log
- 2026-10-03 — Ch. I (pp. 1-9) read: definitions (body parts of the signs, sign natures, lords, exaltation,
  moolatrikona, house names). SCAN DEFECT: book pp. 6-7 (v. 11-15) missing - jumps p. 5 -> p. 8; fill from copy
  312465. Moolatrikona (v. 7) differs slightly from BPHS for Venus (Libra first 5 deg?) - check on the second copy.
- Ch. II (pp. 10-23) read: planetary significations (v. 1-7 Sun..Saturn: what to judge from each), descriptions,
  places, friendships (v. 21-22 = BPHS natural friendship), aspects (v. 23 = BPHS incl. specials and partials),
  benefic/malefic (v. 27 = BPHS), Rahu friends Mercury/Saturn/Venus, Mars neutral (v. 35), weak/strong placement
  (v. 36). No predictive rules; significations kept as data for readings.
- Ch. III (pp. 24-33) read: 10 vargas (D1, D2, D3, D7, D9, D10, D12, D16, D30, D60 - book's own D16 and D30 rules),
  Vaiseshikamsa (v. 7-9: 2..9 good vargas = Parijata..Iravata) and weak-varga results (v. 10), Shadvarga results
  (v. 11), hora (v. 12), decanate types (v. 13-15), Mandi (v. 16), Moon's navamsa (v. 17), Deeptadi avasthas
  (v. 18-20: used by the dasha chapters).
- Ch. IV (pp. 33-43) read: Shadbala outline (same required rupas as BPHS, v. 22-23 -> engine Shadbala reused),
  Moon's kriya/avastha/vela (v. 12-19, from the elapsed part of the Moon's nakshatra; v. 20: mainly for muhurta),
  bhava bala (v. 24).
- Ch. V (pp. 43-46) read: profession from the navamsa lord of the 10th lord (from Lagna, Moon or Sun, whichever is
  strongest), v. 1-9.
- Ch. VI (p. 46-) reading: Pancha mahapurusha, Sunapha/Anapha/Durudhara/Kemadruma, Subha/Papa vesi/vasi/kartari,
  Amala, Mahabhagya, Kesari, Sakata, Adhama/Sama/Varishta, Vasumat, Amala, Pushkala... (to p. 54 so far).
- Ch. VI (pp. 46-72) read and ENCODED with I-V: rules/phaladeepika/ch01_05.py (32) + ch06.py (82). Engine:
  src/rules/pd_varga.py (ten vargas per the book, Vaiseshikamsa, Krura shashtyamsa, Moon's 12 avasthas,
  Deeptadi avasthas); engine atoms n_in_house_from, pd_vaiseshika, pd_weak_vargas, pd_lagna_krura60,
  moon_avastha12, lagna_hora, deeptadi, parivartana; refs mlord:N, navlord:<ref>, pd_profession. Checked on 300
  real charts: no evaluation errors. NEXT: Ch. VII Maharajayogas (p. 72-), PDF 101.
- Ch. VII (pp. 72-81) read and encoded: rules/phaladeepika/ch07.py (42). 1937 pp. 80-81 MISSING in both DLI
  copies (same scan); v. 25-30 read from the 1961 printing (archive.org 'phala-deepika-of-mantreshwar-adhyayas-
  1-28...-1961-kri-9', CC-0 KRI scan, pp. 95-97; local data/sources/phaladeepika_1961.pdf). Ch. I v. 11-15 (pp. 6-7)
  read there too (1961 pp. 6-9): house names only. New atoms retro, planet_nakshatra, lagna_vargottama,
  n_aspecting_house; ref exaltlord:<ref>. NEXT: Ch. VIII (p. 82, PDF 109).
- SOURCE SWITCH from Ch. VIII: the 1937 scan also lacks pp. 88-89, so the 1961 printing (same Sastri translation,
  complete, cleaner; data/sources/phaladeepika_1961.pdf, book p. N = PDF p. N + 42 around ch. VIII) is the primary
  text from here; citations give the 1961 page. Ch. VIII (1961 pp. 98-116) read and encoded: ch08.py (203 rules:
  9 planets x 12 houses + sign/phase clauses), each scaled by v. 34-35 (reader scale 'bhava_of'). NEXT: Ch. IX
  (1961 p. 117, PDF 159).
- Ch. IX-XII (1961 pp. 117-154) read and encoded: ch09_12.py (150 rules). Timing rules: IX v. 15-19 (dasha of a planet
  by dignity / combustion; v. 20 retrograde = exalted, vargottama = own), X v. 12-14 (marriage: dasha of 7th-house
  planets, transits of the Lagna lord / Venus / 7th lord / Jupiter), XII v. 25-29 (childbirth: dashas, Jupiter and
  Lagna-lord transits, the sphuta-nakshatra mahadasha). Engine: transits may name chart refs ('lord:7'); targets
  'navfrom:<ref>:N'; refs lordfrom:<ref>:N, strongest:a|b|c; atoms pd_trimsamsa_lord, pd_sphuta (Beeja/Kshetra),
  pd_santana (santana tithi/karana), dasha_sphuta_nak. NEXT: Ch. XIII longevity (1961 p. 154, PDF 196).
- Ch. XIII-XIV (1961 pp. 154-180) read and encoded: ch13_14.py (38). PD's own three-pair longevity (pd_varga.ayu_class;
  table vs prose conflict for pair C logged), Moon's mrityubhaga, Saturn over the (Sa+Ju+Su+Mo) sign by round (v. 18,
  atom transit_sphuta), Lagna-lord transit through 6/8/12/1 (v. 19), v. 22-23 protections as weaken/cancel effects on
  PD-13 negatives; XIV diseases. NEXT: Ch. XV (1961 p. 181, PDF 223).
- Ch. XV-XVII (1961 pp. 181-219) read and encoded: ch15.py (102: the general bhava rules applied to all 12 houses,
  v. 7 destroying/helping dashas mapped to events), ch16.py (40: house-by-house; v. 31-33 bhava transits), ch17.py
  (32: death by transits - Saturn/Jupiter/Sun/Moon over the rasi/navamsa of the 8th lord, Gulika, 22nd drekkana,
  and longitude sums). Engine: transit_conj, transit_point (sums of longitudes, rasi/navamsa/d12/d3, trines,
  via-lord), refs drek22/drek22m/drek1/weakest, target owned:<ref>. Note: XVI v. 31 transit triggers fire on ~80%
  of dates (the book's union of five conditions with trines) - faithful but barely discriminating.
  NEXT: Ch. XVIII two-planet conjunctions (1961 p. 220, PDF 262).
- Ch. XVIII (1961 pp. 220-229) encoded: ch18.py (139: two-planet conjunctions; the Moon in each sign / navamsa
  aspected by each planet, one-word results mapped by meaning; v. 17 navamsa-lord-strong cancels the sign results).
- Ch. XIX-XX (1961 pp. 229-264) encoded: ch19_20.py (131 timing rules: each planet's mahadasha (two lists), bhava
  lords' dashas strong/weak, dasha-bhukti enmity and 6/8/12 relations, fatal dashas (weakest of 8th-house factors,
  v. 31-32, 40, 50, 55, 58), functional nature (v. 41-53), transits during a dasha (v. 34-38, 59-61)). Engine:
  dasha_lord_transit, moon_from_dasha_lord, sun_on_dasha_sign, md_index; refs naklord:N, gulikalord.
  NEXT: Ch. XXI bhuktis and antaras (1961 p. 264, PDF 306).
- Ch. XXI (1961 pp. 264-292) encoded: ch21.py (161: all 81 MD x AD results, mapped to events).
- Ch. XXII-XXIV (1961 pp. 292-334) encoded: ch22_24.py (32). XXII Kalachakra = BPHS (gati jumps reused); tara,
  naisargika and three ayurdaya systems logged. XXIII-XXIV Ashtakavarga: src/rules/pd_av.py - PD's bindu tables
  verified identical to the common tables (features.BAV), differing from BPHS's in Moon's and Venus's AV; reductions and
  multipliers as BPHS; Samudaya of the seven = 337 (checked). Atoms pd_av_star, pd_av_sign, pd_av_transit,
  pd_sav_transit, pd_av_year, pd_sav_cmp. NEXT: Ch. XXV upagrahas (1961 p. 334, PDF 376).
- Ch. XXV-XXVIII (1961 pp. 334-388) encoded: ch25_28.py (173). XXV Mandi by PD's own ghatika table
  (bphs_time.pd_mandi; PD rules in ch. XVII/XX now use 'Mandi', BPHS rules keep 'Gulika'), Mandi/Upaketu in houses,
  Mandi conjunctions; XXVI gochara from the Moon with vedha (engine GOCHARA_VEDHA), house results with events, star
  transits from the natal star (limb tables), Lattas; XXVII ascetic yogas. The Sarvatobhadra appendix (pp. 367-382)
  is the translator's addition from other works (Horaratna) and needs name letters - logged. src/rao.py transit
  record now carries Ketu's nakshatra.
- *** PHALADEEPIKA COMPLETE (2026-10-03): all 28 adhyayas read; 1,357 rules (789 natal, 568 timing with events).
  Whole rule base 4,054. All rules evaluate without errors on 300 real charts. NEXT: pre-registered test of
  Phaladeepika (and BPHS + Phaladeepika together), same design as docs/prereg_bphs_engine.md.
- 2026-10-03 — PRE-REGISTERED TESTS (docs/prereg_phaladeepika_engine.md, commits 0196366/7dbf2b6):
  PRIMARY Phaladeepika alone (568 timing rules; docs/results_engine_Phaladeepika_20261003_1004.json): 0 of 18 types
  pass; Job_Start dC -0.060, Bonferroni interval wholly below 0 (the rules point AWAY from new-job dates); per rule
  2,642 tests, 0 FDR-significant in the book's direction and 2 against; p<.05 65 for vs 76 against. Learned
  (secondary): Job_End RULES 0.552 vs DEMO 0.457, Bonferroni [0.024, 0.181], but placebo 0.540 [0.492, 0.582] and not
  reproduced in the combined run (+0.036, n.s.) - not a finding (secondary, no confirmation path in the prereg).
  SECONDARY BPHS + Phaladeepika (2,492 rules; results_engine_BPHS+Phaladeepika_20261003_1009.json): 0 of 18 pass
  (Job_Start again below 0: -0.069 [-0.128, -0.012]); per rule 9,646 tests, 0 FDR-significant; 208 for vs 219 against.
  Expectation met: no support for either book.
