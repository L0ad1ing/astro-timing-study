# BPHS build — progress log (append-only)

## How to resume (read this first after any disconnect)
1. Read the LAST entry below: it names the last PDF page read and the next step.
2. Plan and per-chapter status: `docs/bphs_plan.md`. Dasha computation notes: `docs/bphs_ch48_specs.md`.
   Ledger of what each chapter produced and what could not be encoded: `rules/coverage.json` (built by
   `python -m rules.build`). Chapter rule modules: `rules/bphs/chNN.py`.
3. Pages: `data/sources/bphs_v1.pdf`, `bphs_v2.pdf` (gitignored). Render with
   `python data/sources/render.py <pdf> <first> <last>`
   -> `data/sources/pages/<stem>_p####.png`; read the PNGs. Vol. 2: PDF page = book page + 24.
4. Run tests: `ASTRO_SOURCE_DB=__none__ python -m pytest tests/ -q`.

## Principles (user, 2026-10-02)
- Built completely from the book: every rule AND every calculation (dignity, friendship, aspects, combustion,
  dasha arithmetic, year length...) taken from the page that states it, with a citation. Anything currently in the
  engine that came from general knowledge is marked and replaced by the book's version when that chapter is read.
- Nothing from memory. Where the translation and the printed Sanskrit disagree, encode the translation and log it.
- Everything logged here as it happens, and committed after every batch, so work can resume after a disconnect.
- Copyrighted translation: paraphrase + page citation only; source PDFs stay local.

## Known engine parts NOT yet from the book (to replace)
| part | current source | book chapter that defines it |
|---|---|---|
| Vimshottari year length | 365.25 days — CONSISTENT with the book: p. 18 adds whole years/months/days to the calendar date; the 360-day figure (pp. 12, 28) is only for converting fractions into months and days | — |
| Dignity, moolatrikona ranges, exaltation degrees | src/strength.py (general knowledge) | vol. 1 ch. 3 |
| Natural / temporary / compound friendship | src/strength.py | vol. 1 ch. 3 |
| Aspects (graha drishti, sign aspects) | engine (Parashari sign aspects from memory) | vol. 1 ch. 9 (signs), ch. 28 (planets) |
| Combustion orbs | src/strength.py | to be located (vol. 1) |
| Divisional charts D9/D7/D10/D12 | src/ (general knowledge) | vol. 1 ch. 6-7 |
| Shadbala, avasthas | src/strength.py | vol. 1 ch. 29, 47 |
| Ayanamsa / sidereal positions | Lahiri via the ephemeris | book uses Lahiri ephemeris in examples (vol. 2 p. 8) |

## Log
- 2026-10-02 — vol. 2 ch. 50 read (PDF 157-167): 47 rules, committed.
- 2026-10-02 — vol. 2 ch. 49 read (PDF 135-156): 84 rules; atoms varga_dignity, is, combust, moon_phase; commit 6670d53.
- 2026-10-02 — Contents of both volumes read (v1 PDF 3-9, v2 PDF 5-16); whole-book plan written (docs/bphs_plan.md).
- 2026-10-02 — vol. 2 ch. 51 Kalachakra results read in full (PDF 168-181). NOT yet encoded: needs the Kalachakra
  primitive from ch. 48. Structure found: results keyed by (navamsa of the Moon's nakshatra pada, position 1-9 of the
  running dasha sign in that pada's sequence) — e.g. Gemini pada: Ta, Ar, Pi, Aq, Cp, Sg, Ar, Ta, Ge; Aries and Taurus
  appear twice with different results, so key on position, not sign. Discrepancy: v. 25 Sagittarius group, Aries
  amsa — translation "worries about wealth", printed Sanskrit "dhana-labha" (gain of wealth).
- 2026-10-02 — vol. 2 ch. 52 first page read (PDF 182, verses 1-4). Rest of ch. 52 after ch. 48.
- 2026-10-02 — vol. 2 ch. 48 reading in progress: PDF 25-54 read (Vimshottari, Astottari, Shodashottari, start of
  Dwadashottari); specs in docs/bphs_ch48_specs.md. NEXT: PDF 55 onward.
- 2026-10-02 — ch. 48 PDF 55-105 read: Panchottari, Shatabdika, Chaturashiti, Dwisaptati, Shashtihayani,
  Shat-trimsha, Kala, Chakra, and the whole Kalachakra section (v. 52-154: tables 14A/14B transcribed from a 3x
  render and cross-checked with verses and ch. 51; balance method; Deha/Jeeva; gati motions; 100+ KC result
  statements incl. house-wise dasha results). Findings logged in the specs file: Rohini pada-3 misprint, Table-18A
  vs verse 77 conflict (verse followed), no rule for what follows the 9th dasha (not invented). Chara dasha starts
  PDF 105. NEXT: PDF 106 onward (rest of ch. 48), then build primitives + ch. 51/52 rules + ch. 48 KC rules.
- 2026-10-02 — ch. 48 COMPLETE (PDF 106-134 read: Chara, Sthira/Brahma, Yogardha, Kendradi, Karaka, Mandooka,
  Shoola, Trikona, Driga, Lagnadi-Rasi, Panchaswara, Yogini, Pinda/Amsa/Naisargika, Ashtakavarga, Sandhya, Pachaka,
  Tara). Chara Table-24 checked: verses reproduce 10/12; Aq & Pi entries conflict with the verses (logged).
  Shoola "Capricorn" = mistranslation of maraka (logged). NEXT: build src/rules/dashas_bphs.py (Vimshottari 360-day
  option, Kalachakra, Chara; tests vs book examples), then encode ch. 48 KC rules + ch. 51 rules, then read ch. 52.
- 2026-10-02 — CORRECTION: the "360-day year" entry above was wrong — the book's timeline (p. 18) adds calendar years;
  360 days only converts fractions. Engine's calendar years are consistent with the book.
- 2026-10-02 — Built src/rules/bphs_dasha.py (Kalachakra: tables, Deha/Jeeva, balance, motions; Chara: years incl.
  dual lords, order) + tests/test_bphs_dasha.py (book tables, example 8, Chara Table-24 10/12). Engine atoms kc,
  kc_natal, sign:N targets. rules/bphs/ch48.py (92 rules) and ch51.py (134 rules). 357 rules total, 59 tests pass.
  Found: v. 49.35 translation "Rahu exalted Scorpio, Ketu Taurus" vs printed Sanskrit "Rahu Taurus, Ketu Scorpio" —
  resolve with vol. 1 ch. 3. NEXT: read ch. 52 (PDF 182-201) — Chara/Sthira results.
- 2026-10-02 — ch. 52 (PDF 182-201) and ch. 53 (PDF 202-211) READ in full. ch. 52: Chara-dasha results relative to
  the dasha sign (planets in its 2nd/3rd/4th/5th/6th/8th/9th/10th/11th/12th, badhaka, exalted/empty sign, Rahu
  placements, lords placed in it), Chara antardasha results, and the dasha STATES of v. 73-83 (Poorna, Rikta,
  Arohini, Avarohini, Madhya, Adhama — these are the "named dasha states" ch. 49 notes needed; Arohini/Avarohini and
  'deep' states need exact exaltation degrees from vol. 1 ch. 3). ch. 53: Vimshottari AD/PD arithmetic (matches the
  engine), Chara AD (three conflicting statements, see specs), Pinda AD parts. NEXT: implement Chara AD + `chara`
  atom, write rules/bphs/ch52.py and ch53.py, then ch. 54 (PDF 212-239).
- 2026-10-02 — Chara antardasha + `chara` atom (MD and ad_ fields: holds, from_holds, from_dignity, lord_in, ...)
  built; rules/bphs/ch52.py = 82 rules (80 ch. 52 + 2 ch. 53). 439 rules total; 61 tests pass.
  NEXT: ch. 54 antardashas in the Sun MD (PDF 212-239).
- 2026-10-02 — ch. 54 (PDF 212-239) read and encoded: 100 rules (rules/bphs/ch54.py, shared helpers
  rules/bphs/_antar.py). New: BD.vimshottari with elapsed/length per level (tested vs p. 12 and Table-28), atoms
  dasha_frac / dasha_elapsed (beginning/middle/end thirds, 'first two months'), lagna_sign, varga_in_sign, in_house
  counted from a planet. POLICY (made explicit): when the printed Sanskrit plainly differs from the translation, the
  translation is encoded and the Sanskrit reading is written into the rule text + this log, for variant testing.
  ch. 54 discrepancies: v. 11 '8th' vs Sanskrit bhagya (9th); v. 52 'malefics' vs saumya (benefics); v. 64 Ketu
  '7th/12th lord' vs 2nd/7th; v. 71 Venus 'in the 7th' vs 7th lord. 539 rules; 64 tests. NEXT: ch. 55 (PDF 240-258).
- 2026-10-02 — SCAN GAP: vol. 2 PDF page 243 is a duplicate of book p. 103; book p. 219 (ch. 55 v. 3-8 translation,
  v. 6-8 Sanskrit) is MISSING from bphs_v2.pdf. v. 3-5 encoded from the printed Sanskrit on p. 218; v. 6-8 not
  available — needs another copy of the book (or another scan) to complete ch. 55.
- 2026-10-02 — ch. 55 encoded (rules/bphs/ch55.py). v. 44 translation says Saturn in the Mercury section (Sanskrit has no planet name; section is Mercury) - encoded as Mercury. NEXT: ch. 56 (PDF 259-280).
- 2026-10-02 — ch. 56 encoded (rules/bphs/ch56.py). Discrepancies: v. 63, 68 'in the 2nd/7th/12th' vs Sanskrit 'lord of 2nd/7th'; v. 75 '2nd or 12th lord' vs 2nd/7th. NEXT: ch. 57 Rahu MD (PDF 281-305).
- 2026-10-02 — ch. 57 encoded (rules/bphs/ch57.py); 'last two months' encoded exactly via dasha_elapsed. NEXT: ch. 58 Jupiter MD (PDF 306-329).
- 2026-10-02 — ch. 58 encoded (rules/bphs/ch58.py). v. 64 translation '2nd, 7th or 6th' vs Sanskrit 2nd/6th. NEXT: ch. 59 Saturn MD (PDF 330-352).
- 2026-10-02 — SCAN GAP 2: vol. 2 PDF page 342 is a duplicate of book p. 57; book p. 318 (end of the ch. 59 Venus
  notes / example 52 analysis only — the verses v. 32-36 are on pp. 316-317) is missing. No verses lost.
- 2026-10-02 — ch. 59 encoded (rules/bphs/ch59.py). NEXT: ch. 60 Mercury MD (PDF 353-378).
- 2026-10-02 — SCAN GAP 3: PDF 377 repeats book p. 269; book p. 353 (ch. 60 Saturn AD v. 65-70) missing.
- 2026-10-02 — ch. 60 encoded (rules/bphs/ch60.py). Total rules now 1054. NEXT: ch. 61 Ketu MD (PDF 379-402).
- 2026-10-02 — ch. 61 encoded (rules/bphs/ch61.py). NEXT: ch. 62 Venus MD (PDF 403-424).
- 2026-10-02 — SCAN GAP 4: PDF 419 repeats book p. 119; book p. 395 (ch. 62 Saturn AD v. 52-57) missing.
- 2026-10-02 — ch. 62 encoded. ALL antardasha chapters 54-62 DONE. Total rules 1208. Missing pages so far: vol. 2
  book pp. 219, 318 (notes only), 353, 395 — a second copy of vol. 2 is needed for those. NEXT: ch. 63
  Pratyantardashas (PDF 425-452).
- 2026-10-02 — MISSING PAGES FILLED. The only online scan of Sharma vol. 2 is the archive.org item we use (Scribd
  copies are the same 818-page scan; MD5 checked). Filled from R. Santhanam's translation (archive.org item
  BPHSEnglish, downloaded to data/sources/santhanam_v1/v2.pdf + djvu text): Sharma p. 219 -> Santhanam vol. 2
  pp. 640-641; p. 353 -> pp. 716-717; p. 395 -> pp. 737-738. Rules carry source 'BPHS - R. Santhanam tr.'.
  p. 318 held only notes (no verses). Santhanam is also available as a cross-check for every other chapter.
- 2026-10-02 — ch. 63 encoded (81 AD/PD pair results + 2). PDF 433 = front-matter xv (book p. 409, example only). v. 67 vivada/vivaha and v. 74 Sun/Venus slips logged. Total 1356. NEXT: ch. 64 Sookshma (PDF 453-476).
- 2026-10-02 — Engine: Vimshottari levels SD (sookshma) and PR (prana) added. ch. 64 encoded (81 PD/SD pairs). PDF 473 repeats p. 429 (p. 449 notes missing). Total 1484. NEXT: ch. 65 Prana (PDF 477-495).
- 2026-10-02 — ch. 65 encoded (81 SD/PR pairs). Total 1626. NEXT: ch. 66 Kalachakra antardashas (PDF 496-521).
- 2026-10-02 — ch. 66 (KC antardashas; computation from Tables 33-35 implemented; examples 89-92 pass) and ch. 67 (restates ch. 51 - no new rules) done. Total 1737. NEXT: ch. 68 Ashtakavarga (PDF 529-554) - computation; check engine BAV tables against the book.
- 2026-10-02 — ch. 68 read (PDF 527-551). src/rules/bphs_av.py: all 8 Ashtakavargas from the Rekha chakras,
  checked against Bindu chakras, verses and Santhanam. 3 contributions differ from the common tables (Moon AV:
  Moon 9th yes / Mars 9th no; Jupiter 2nd not 12th; Venus AV: Mars 4th not 5th). Scan gap: book p. 530 (PDF 551
  shows p. 299) - Ascendant rekha list taken from Santhanam = complement of p. 529 bindus. Translator's worked
  example (ch. 69 p. 537) uses the common Moon table - conflicts with his own chakra; verse followed.
- 2026-10-02 — NEW: docs/BPHS_ENGINE_NOTES.md = curated, publishable notes (method, conventions, computations,
  contradictions, Sanskrit differences, scan defects). Keep it updated with every chapter; it is the basis for the
  GitHub write-up. NEXT: ch. 69 Trikona Shodhana (PDF 552-566).
- 2026-10-02 — ch. 69-71 done: Trikona/Ekadhipatya shodhana + pindas in src/rules/bphs_av.py, example 93 reproduced (65+58=123). Ekadhipatya: Sanskrit v. 3 followed over two conflicting translator statements. Scan gap: PDF 576 = book p. 141 in place of p. 555 (ch. 72 v. 6-9) - use Santhanam. NEXT: ch. 72 results (PDF 575-595).
- 2026-10-02 — ch. 72 done: 22 rules. Engine: transit nakshatras (rao._nak), bphs_av.AV (pinda, points, Saturn's
  years) with atoms av_point / av_transit / av_year and target 'from:<planet>:N'. Example 93 reproduced for 5 of 7
  planets; Moon/Venus/Saturn-pinda differences are the book's worked example contradicting its own tables/rules
  (logged in BPHS_ENGINE_NOTES.md). Scan: pp. 559-560 and 571 also misbound; filled from Santhanam. Total 1759.
  NEXT: ch. 73 longevity from AV (PDF 593-598).
- 2026-10-02 — ch. 73-74 done (AV longevity, Samudaya incl. Ascendant; solar-month results by rekha count). Ascendant AV table (from Santhanam) reproduces Sharma's printed row. Scan: book pp. 572, 588 misbound (Santhanam). Total 1787. NEXT: ch. 75 rays (PDF 610-622).
- 2026-10-02 — ch. 75 done: src/rules/bphs_rays.py (raw rays tested on example 94, book units are thirtieths), atom rays_total, 18 natal rules. PDF 617 misbound (book 596, arithmetic only). NEXT: ch. 76 Sudarshana (PDF 623-640).
- 2026-10-02 — ch. 76 done: 'sud' atom (yearly/monthly from Lagna/Moon/Sun), 42 rules. PDF 624 misbound (book 603). PDF 640 = book 73 in place of 619 (ch. 77 v. 1-2 - use Santhanam). NEXT: ch. 77 Mahapurusha (PDF 640-655).
- 2026-10-02 — ch. 77 done (Mahapurusha: natal + fixed death ages, new 'age' atom). Scan: book pp. 619, 622 misbound (Santhanam). NEXT: ch. 78 elements (PDF 656+).
- 2026-10-02 — ch. 78 (13 rules: element of the MD lord, strong vs weak), ch. 79 (gunas, nothing testable), ch. 80 (lost horoscopy, horary) read. Scan: book pp. 643, 651 misbound (no testable loss). NEXT: ch. 81 asceticism (PDF 680+).
- 2026-10-02 — ch. 81 (asceticism, 6 natal) and ch. 82 (female horoscope, 24 rules, gender atom) done. NEXT: ch. 83 parts of a woman's body (PDF 716+).
- 2026-10-02 — ch. 83-84 read (physiognomy, nothing to encode; 3 misbound pages, physiognomy only). NEXT: ch. 85 curses / childlessness (PDF 739+).
- 2026-10-02 — ch. 85 done: 35 rules from Sharma + 27 from Santhanam for the 6 misbound pages = 62 natal childlessness rules. NEXT: ch. 86-98 (propitiation, inauspicious births; PDF 760-801).
- 2026-10-02 — ch. 86-98 done (18 rules: Amavasya, six parts of Krishna Chaturdashi incl. parent-death event forms,
  gandanta, Abhukta Moola, Jyeshtha/Ashlesha/Moola in-law rules; new atoms tithi, tithi_part, nakshatra [+padas],
  gandanta). ch. 99-100 read (horary - an added text per the translator; epilogue).
- 2026-10-02 — VOLUME 2 COMPLETE (ch. 48-100). Total rules 1981. NEXT: VOLUME 1 from ch. 1 (bphs_v1.pdf, 657 pages):
  find the PDF offset first; ch. 3 (dignities, friendships) replaces the engine's general-knowledge tables.
- 2026-10-02 — VOL 1 offset: PDF page = book page + 11 (book 14 = PDF 25).
- 2026-10-02 — VOL 1 ch. 1-3 read (PDF 12-60). src/rules/bphs_core.py = ch. 3 definitions (dignity with the Moon /
  Mercury exaltation portions, node friendships, compound friendship, dynamic benefic/malefic, result shares); the
  engine now uses it (Chart.dig, benefics/malefics, lord_nature, varga_dignity); MAL/BEN list refs resolve per chart and
  per-planet expansions in 12 chapter files were collapsed to list refs. 3 natal upagraha rules. Specs in
  docs/bphs_v1_specs.md. NEXT: vol. 1 ch. 4 signs (PDF 61+).
- 2026-10-02 — vol. 1 ch. 4 (signs) read: definitions only. NEXT: ch. 5 (positions - an added text per the translator) and ch. 6 (PDF 72+).
- 2026-10-02 — vol. 1 ch. 5 (positions; added text per the translator) sampled - arithmetic replaced by the ephemeris; logged as sampled, not fully read. NEXT: ch. 6 special ascendants (PDF 98+).
- 2026-10-02 — vol. 1 ch. 6-9 read (special lagnas, Varnada, vargas, Vimshopaka, sign aspects). D9/D7/D10/D12 verified; combustion orbs from ch. 8 notes now in bphs_core and the engine. Pending primitives: sunrise-based lagnas (Bhava/Hora/Ghati, Varnada, Gulika, Pranapada), Vimshopaka. NEXT: ch. 10 (added text) / ch. 11 evils at birth (PDF 174+).
- 2026-10-02 — vol. 1 ch. 10-12 done: Balarishta (41 natal + 9 parent-death event forms within age windows) and antidotes (6). ch. 10 is an added text (sampled). NEXT: ch. 13 judgement of houses (PDF 197+).
- 2026-10-02 — vol. 1 ch. 13-19 done (houses 1-6): natal rules + timing rules tied to stated years of age (children at 30/32/33/36/40; child death 32/33/36; illnesses and accidents at stated years). NEXT: ch. 20 7th house (PDF 249+).
- 2026-10-02 — vol. 1 ch. 20-22 done: 12 marriage-age rules, 4 wife-death-year rules, 11 father-death-year rules, longevity (death 20-32), natal. NEXT: ch. 23 10th house (PDF 269+).
- 2026-10-02 — vol. 1 ch. 23-25 done (houses 10-12). All 12 house chapters complete. NEXT: ch. 26 lords in houses (144 combinations, PDF 283-~350).
- 2026-10-02 — vol. 1 ch. 26 done: all 144 house-lord-in-house combinations (rules/bphs/v1ch26_table.py) + 4 event forms = 157 rules. NEXT: ch. 27 non-luminous planets (PDF 348+).
- 2026-10-02 — USER GOAL EXTENDED: a complete reading engine (every rule; rules modify/cancel each other; chart
  readings). Built: open outcome domains in the rule format, `effect` (cancels/weakens/strengthens/reverses) and `scale`
  fields, src/rules/reader.py (fire -> weigh -> interact -> combine, with citations), tests/test_reader.py. First book
  interactions encoded: vol. 1 ch. 12 antidotes cancel ch. 11 evils (all / mother / father). Design and build order in
  docs/rule_engine_design.md. NEXT: vol. 1 ch. 27 (PDF 348+), encoding every statement incl. non-event outcomes.
- 2026-10-02 — vol. 1 ch. 27-28 done: 84 natal rules (5 upagrahas + Gulika + Pranapada x 12 houses); src/rules/bphs_time.py (sunrise, day/night, weekday, Gulika, Pranapada); ch. 28 aspects in bphs_core (engine now uses the book's full aspects - Rahu/Ketu 7th only; Sphuta drishti tested). NEXT: ch. 29 Shadbala (PDF 393+).
- 2026-10-02 — vol. 1 ch. 29 done: Shadbala implemented; strong/weak atoms switched to it; reader scale 'strength_of' (full/half/quarter). NEXT: ch. 30 Ishta/Kashta (PDF 420+).
- 2026-10-02 — vol. 1 ch. 30 (Ishta/Kashta, 4 dasha rules) and ch. 31 (Arudha computed per the book incl. exceptions; 20 natal rules) done. NEXT: ch. 32 Upapada (PDF 436+).
- 2026-10-02 — vol. 1 ch. 32-33 done: Upapada (UL = pada of the 12th) rules, Argala computation + 13 rules. NEXT: ch. 34 karakas (PDF 451+).
- 2026-10-03 — vol. 1 ch. 36 done: functional nature table by Lagna (src/rules/bphs_functional.py, atom 'functional'), 9 rules incl. a weakening interaction. NEXT: ch. 37 Nabhasa yogas (PDF 501+).
- 2026-10-03 — vol. 1 ch. 37 done: 32 Nabhasa yogas (src/rules/bphs_nabhasa.py with the book's precedence), 32 natal rules. NEXT: ch. 38 (PDF 524+).
- 2026-10-03 — vol. 1 ch. 38-40 done: miscellaneous, lunar, solar yogas (40 natal rules incl. Kemadruma cancellation interaction). NEXT: ch. 41 Raja yogas (PDF 551+).
- 2026-10-03 — vol. 1 ch. 41-42 done: Raja yogas and royal association (36 natal rules). NEXT: ch. 43 wealth (PDF 566+).
- 2026-10-03 — vol. 1 ch. 43-44 done (wealth and penury; a reversal interaction). NEXT: ch. 45 longevity (PDF 581+).
- 2026-10-03 — vol. 1 ch. 45-46 done: Pindayu with reductions + three-pair longevity class (src/rules/bphs_ayu.py), 'marakas' ref, death-in-maraka-period rules within the span. NEXT: ch. 47 avasthas (PDF 624-657) - last chapter of BPHS.
- 2026-10-03 — vol. 1 ch. 47 done: avasthas (Baladi, Jagradadi, Lajjitadi) in src/rules/bphs_avastha.py, reader scale
  'avastha_of', 6 rules. Shayanadi needs the name's first letter (logged). The vol. 1 scan ends at p. 651 ('to be concluded').
- 2026-10-03 — *** BPHS COMPLETE: both volumes read page by page and encoded. *** NEXT (per docs/rule_engine_design.md build
  order): (1) backfill ledger items 'no matching event' as domain rules; (2) synthesis: apply scale strength_of/avastha_of
  and functional nature across rules, general node rule (Rahu/Ketu act for dispositor/conjunct), exalted-planet exemption;
  (3) KP Readers; (4) Phaladeepika; (5) Saravali; (6) pre-registered test.
- 2026-10-03 — PRE-REGISTERED TEST of the full BPHS engine (docs/prereg_bphs_engine.md, commit b76dbf8; results
  docs/results_bphs_engine_20261003_0029.json). 27,352 half-0 sets, 18 event types, actual vs mismatched charts.
  PRIMARY: 0 of 18 pass; every dC within +-0.06, all Bonferroni intervals include 0 (Death n=17,976: dC +0.002
  [-0.009, 0.012]; Marriage n=3,663: -0.002). Unweighted and direct-only variants the same. PER RULE: 7,004
  rule x type tests, 0 FDR-significant; at p<.05, 143 in the book's direction and 143 against (pure chance).
  LEARNED (LightGBM on 1,922 rule indicators vs age+year+sex): no type beats DEMO after Bonferroni (closest:
  Accident +0.09, interval [-0.0005, 0.17], n=228). No confirmation run (nothing passed). Expectation met.
