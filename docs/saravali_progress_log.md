# Saravali — progress log (resume from the last entry)

Source: Saravali of Kalyana Varma, English translation and notes by R. Santhanam (Ranjan Publications, New Delhi,
1983). Supplied by the author 2026-10-04 as a PDF of VOL. I ONLY (352 PDF pages; chapters 1-26, ending inside ch. 26
"Effects of Mercury"). Vol. II (ch. 27 onwards: Jupiter, Venus, Saturn in signs; bhavas; dashas; longevity; female
horoscopy; etc.) is NOT available - ask the author.
The PDF's text layer is garbage; OCR'd locally with Tesseract 300 dpi (data/sources/ocr_pdf.py ->
data/sources/saravali/saravali_v1_ocr.txt, gitignored); a filtered English-only copy (sar_clean.txt) is read, page
images checked where the OCR is doubtful. Book page = PDF page - 4. Paraphrase + citation only.

Rules: rules/saravali/chNN.py -> rules/saravali_chNN.jsonl (registered in rules/build.py CHAPTERS).

## Log
- 2026-10-04 — Ch. 1-7 read (pp. 17-90), ch03_07.py, 96 rules: vargottama Lagna, Gandanta birth, the nine
  planetary states (exalted/own/friendly/debilitated/combust), full Moon, mid-life happiness, dignity effects,
  retrograde benefics/malefics, all-strong benefics/malefics, planetary stages felt in their mahadasas (timing),
  odd/even signs, Saravali's own yoga-karaka definition (own/MT/exalted AND in kendras from the Lagna, two or more).
  Logged: body marks by decanate, rays/war/varga states, strength shares, muhurta lords.
- Ch. 8-9 read (pp. 86-114), ch08_09.py, 20 rules: birth-chart verses of the conception chapter (blindness, eyes,
  dumbness, stature, lameness); father absent/confined/dying abroad, mother's death or desertion, parents' happiness.
  Conception-chart and delivery-room verses logged. Ch. 9 v. 32-33 (birth "out of the father's loins")
  DELIBERATELY NOT ENCODED: untestable, and its main condition holds in most charts.
- Ch. 10 read (pp. 114-138), ch10.py, 111 rules: ~45 yogaja arishtas (infant/child death, age in the text), father's
  and mother's death, eyes, ears, long life (108/120 years), fateful degrees of the Moon (v. 111-114, page image),
  Jupiter's fatal ages by house (v. 115-118, page image). Timing (Death): fateful degrees -> age = degree; Jupiter
  in 3/4/5/7/9/10/11 -> ages 5/10/46/20/30/40/50; "the year of the sign" (v. 18, 25-26, 29-30). New engine atom
  deg_in_sign [ref, sign, lo, hi].
- Ch. 11-12 read (pp. 138-147), ch11_12.py, 21 rules: arishta cancellations through the Moon (full Moon aspected,
  deep exaltation + Venus, Adhi yoga, dispositor's aspect, ...) and other planets (bright Jupiter in the Lagna, Rahu in
  3/6/11 or in Aries/Taurus/Cancer rising, Jupiter and Venus in kendras, ...). Each cancels Saravali's natal
  early-death rules (SAR-10-*, SAR-03-GA*, domain longevity only - the notes, p. 147, limit them to longevity).
- Ch. 13 read (pp. 147-162), ch13.py, 35 rules: Sunapha, Anapha, Durudhura, Kemadruma by planet and pair; the Moon
  from the Sun (Adhama/Varishta); visible/invisible halves; benefics in upachayas.
- Ch. 14-15 read (pp. 160-171), ch14_15.py, 45 rules: Vesi/Vasi/Ubhayachari by planet; the 21 two-planet conjunctions.
- CITATION FIX: the pages typed by hand in ch. 3-12 were partly PDF pages (book = PDF - 4). Pages now come from a
  committed verse->page table (rules/saravali/pages.py, numbers only) generated from the verse headings of the OCR
  (scripts/saravali_versemap.py; numbered lists in the notes filtered out; unmatched verses take the nearest earlier
  verse's page). Checked against page images for ch. 10 v. 111 and v. 115. All Saravali citations now match the table.
- Ch. 16-19 read (pp. 163-196): ch16.py 61 rules (35 three-planet sets, parents, three benefics/malefics);
  ch17_19.py 97 rules (35 four-planet sets - v. 8, 17, 24 misprinted, set taken from the standard order; 22 printed
  five-planet verses for 21 sets - duplicates v. 7/8 and 13/20 encoded as printed and flagged; 7 six-planet sets;
  5-6 planets together).
- Ch. 20 read (pp. 197-206), ch20.py 53 rules: renunciation groups (v. 2-19) and Moon/Saturn renunciation yogas.
- versemap: chapter headings with the title on the next line or in brackets now detected (ch. 6, 17-20 were missing;
  ch. 6 v. 1-6 had a hand-typed PDF page). Ch. 24's heading is not on its own line - handle when reached.
- Ch. 21 read (pp. 207-237), ch21.py 51 rules: Saravali's results for the 32 Nabhasa yogas (definitions = BPHS, engine atom).
- Ch. 22 read (pp. 237-255), ch22.py 85 rules: the Sun in each sign and in each lord's signs aspected by each planet (Mercury/Venus aspects on the Sun never fire - partial aspects, see prolegomena).
- Ch. 23 read (pp. 255-286), ch23.py: the Moon in each sign and in each sign aspected by each planet; Taurus halves and the parents.
- Ch. 24 read (pp. 286-290), ch24.py 48 rules: the Moon in each planet's navamsa aspected by each planet (aspect in the rasi chart, notes p. 287). versemap: quoted chapter headings and '1-3..' verse headings detected.
- Ch. 25 read (pp. 291-320), ch25.py 80 rules: Mars in each sign and in each lord's signs aspected by each planet
  (v. 41 'Taurus/Libra' slip inside the Mercury-signs block encoded as Gemini/Virgo).
- Ch. 26 read (pp. 319-343), ch26.py 81 rules: Mercury in each sign and aspected (Sun/Venus aspects never fire).
- versemap: page overrides read from the scan for 12 OCR-mangled verse headings in ch. 25-26.
- VOL. I COMPLETE: 1,016 rules (989 natal, 27 timing; 25 on tested events - 23 Death, 1 Career_Peak, 1 Illness).
  Fire check over 150 charts: no errors. Vol. II (ch. 27-55, incl. the dasha and bhava chapters) needed for more.
- 2026-10-04 VOL. II supplied (Downloads/46053780-saravali-vol-2_compress.pdf, 485 PDF pages, ch. 27-55, book page =
  PDF + 361). Text layer usable but Tesseract cleaner: data/sources/saravali/saravali_v2_ocr.txt, sar2_clean.txt.
  Citations name vol. 2; versemap scans both volumes. Helper sign_and_aspects() for the planet-in-signs chapters.
- Ch. 27-29 read (vol. 2 pp. 363-478): Jupiter, Venus, Saturn in each sign and aspected (96 + 87 + 87 rules).
- Ch. 30 read (vol. 2 pp. 478-534), ch30.py 152 rules: the seven planets in the twelve houses (v. 68 Venus in the 7th misprinted - repeats v. 67 - not encoded).
- Ch. 31 read (pp. 534-550), ch31.py: the 21 two-planet conjunctions in the four angles; verse numbers after v. 41 inferred (OCR lost them), pages read at each pair's first line (versemap overrides).
- Ch. 32 read (pp. 552-575), ch32.py 150 rules: 9th house - lord, Jupiter there with single and paired aspects, afflictions, exaltation, and the 2/3/4-planet combinations in the 9th.
- Ch. 33 read (pp. 575-588), ch33.py 89 rules: planets in the 10th from the Moon (1-4 together), malefics there, malefics in 3/6 vs 8/12/1, livelihood by the sign on the 10th, income source by the planet in the 10th.
- Ch. 34 read (pp. 588-610), ch34.py 69 rules: aspects on the Lagna, Lagnadhi yoga, 2nd/3rd/5th/6th/7th/11th/12th house rules, misc disease yogas. Deliberately NOT encoded: v. 28, 30-36, 38 (children by a kinsman/widow/virgin/slave, 'abject' children). New engine atom navamsa_lagna [signs].
- Ch. 35 read (pp. 610-662), ch35.py 169 rules (168 natal Raja yogas + 1 timing: rulership in the dasa of the benefic aspecting a full exalted vargottama Moon). Qualifiers without an engine primitive dropped and stated per rule; garbled/untestable verses logged.
- Ch. 36-38 read (pp. 662-693), ch36_38.py 26 rules: rays (new src/rules/sar_rays.py, atom sar_rays_total; scale vs rectification mismatch noted), the five Mahapurusha yogas with their death ages (timing), v. 38.22 (weak luminaries: children and wealth in the planet's period). Gunas/elements logged.
- Ch. 39-40 read (pp. 693-706), ch39_40.py 21 rules: obstructions to Raja yogas (each cancels SAR-35 status/wealth +), Jupiter in Capricorn rising, 3+ debilitated; Pindayu timing (BPHS computation, same table), full/unlimited life. Amsayu/Nisargayu not computed (logged).
- Ch. 41-45 read (pp. 706-743), ch41_45.py 172 rules. NEW src/rules/sar_moola.py: Saravali's Moola dasa (first the strongest of Lagna/Sun/Moon, then kendra/panaphara/apoklima givers; years by Amsayu/Pindayu/Nisargayu chosen by that strongest; sub periods by the Brihat Jataka shares) with atoms moola and moola_start_transit - all choices stated in the module. Timing rules: favourable/adverse dasas per planet, the Moon at a dasa's start, the Lagna's dasa by decanate, placements, sub periods by position from the dasa lord, the 42 dasa/sub-period pairs, evil dasas (Mars-Saturn death etc.). Ch. 45 dignity results and counts (natal). Ch. 44 antidotes logged. versemap: em-dash verse headings (ch. 42 'SUN DASA—MOON BHUKTI') no longer filtered.
- Ch. 46-47 read (pp. 743-777), ch46_47.py 82 rules: female horoscopy (husband, widowhood, children, learning, renunciation; chastity/sexuality/character verses deliberately NOT encoded, as for Phaladeepika XI); manner and place of death (reading-only death_manner), incl. the 22nd-decanate table.
- Ch. 48-51 read (pp. 765-821), ch48_50.py 94 rules: rising sign, hora and decanate results (non-physical clauses mapped). Ch. 51 navamsas: physical description only - not encoded (logged). versemap overrides for ch. 48 (no heading in OCR).
- Ch. 52-55 read (pp. 821-852), ch52_55.py 68 rules: Saravali Ashtakavarga (NEW src/rules/sar_av.py - tables differ from BPHS in the Moon's, Mercury's and Saturn's charts) transit quality (timing), bindu-count results (natal), Brahma's chart. Lost horoscopy (ch. 52) and non-human births (ch. 55) logged.
- SARAVALI COMPLETE (vols. I-II, ch. 1-55): 2,510 rules. Full test suite passes; fire check over 150 charts: no errors.
- 2026-10-04 complete-book test (docs/prereg_saravali_full_engine.md; results_engine_Saravali_20261004_1219.json): 0 / 18 event types pass. Largest: Illness dC +0.054 (Bonferroni [-0.041, +0.142]). Per rule 545 tests, 0 FDR-significant, 13 for / 7 against at p<.05. Secondary learned model: Career_Peak beat demographics (Bonferroni [+0.027, +0.137]) but C only 0.522 and the demo baseline 0.443 - lead only, not confirmed.
- 2026-10-04 calculation check against the scans: chart positions, houses, dignities, aspects, navamsa, tithi, Vimshottari, Pindayu, Moola dasa dates and the author's bindu counts all re-derived independently and match. Errors found and fixed: ch. 5 v. 47-50 / ch. 35 / ch. 36-38 dasa clauses used Vimshottari (now Moola dasa); Mars AV from Saturn had a BPHS 4th (translation has none). Corrected re-run (results_engine_Saravali_20261004_1849.json): 0 / 18. Judgement calls kept and stated: BPHS combustion orbs (Saravali gives none; retro Mercury 13 deg), Kemadruma per the translation's 'or', Moola dasa kendras counted from the Lagna.
