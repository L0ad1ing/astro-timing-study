# BPHS rule engine — notes on the text

What this is: a rule engine that encodes *Brihat Parasara Hora Sastra* (BPHS) as testable rules, chapter by chapter,
from the pages of the book — not from memory or modern practice. This file records what was found in the text while
doing it: how the book was read, where it contradicts itself, where the scan is defective, and every judgement call
made in turning prose into code. It is meant to be read alongside `rules/coverage.json` (per-chapter ledger) and
`docs/bphs_progress_log.md` (chronological work log).

## Not Parashara's text
The translator states (vol. 2 p. 797) that vol. 1 ch. 5 (planetary positions), vol. 1 ch. 10 (surroundings at birth)
and vol. 2 ch. 99 (horary) were added from other treatises. Rules from those chapters, if any, are flagged.

## Sources
| Source | Use |
|---|---|
| G.C. Sharma (tr.), *Brihat Parasara Hora Sastra*, 2 vols, Sagar Publications, New Delhi, 1995 (archive.org scan) | Primary text. Every rule cites verse and page. |
| R. Santhanam (tr.), *Brihat Parasara Hora Sastra*, 2 vols, Ranjan Publications (archive.org `BPHSEnglish`) | Fills pages missing from the Sharma scan; cross-checks disputed readings. |
| The printed Sanskrit in Sharma's edition | Consulted where the English is doubtful; differences are logged, see below. |

Rules are stored as paraphrases with citations only (the translations are copyrighted). Source PDFs are not in the repo.

## Method
- Every page of each chapter is rendered and read in full before its rules are written.
- **Verses** → source `BPHS`. **Translator's notes** → `BPHS - G.C. Sharma notes`. **Other classics quoted in the
  notes** → `<text> (quoted in BPHS notes)`. **Santhanam fill-ins** → `BPHS - R. Santhanam tr.`. Each kind can be
  tested separately.
- Chapters that are pure computation become engine code tested against the book's own tables and worked examples.
- What cannot be encoded (remedies, outcomes not in the data such as wealth or travel, conditions that need a
  primitive not yet built) is listed per chapter in the ledger — nothing is dropped silently.
- **Translation vs Sanskrit:** where they plainly differ, the translation is encoded and the Sanskrit reading is
  written into the rule text and listed below, so both readings can be tested.
- Event mapping (outcome words → the event types in the data): disease/fever → Illness; death of native → Death;
  wife → Death of mate; father/mother → Death of father/mother; brothers/relatives → Death_of_relative; wrath or
  punishment of the king → Arrest; fire, water, weapons, poison, snakes, animals → Accident; authority, ministership,
  command → Career_Peak; recognition from the king → Prize; wealth, success, happiness → Positive; enemies, losses,
  distress → Negative; opposition from the wife → Divorce.

## Engine conventions adopted from the text (`rules/bphs/_antar.py` and per chapter)
- Good houses = kendra, trikona, 11th, because the verses list exactly these as the auspicious placements.
- "From the dasha lord" = counted from the mahadasha lord's sign.
- "Beginning / middle / end" of a period = its first, middle and last third.
- "Benefic navamsa / auspicious vargas" = Navamsa sign ruled by a natural benefic.
- Rahu owns Aquarius and Ketu Scorpio for lordship (ch. 48 v. 157).
- **From vol. 1 ch. 3 (src/rules/bphs_core.py), replacing the earlier general-knowledge tables in the rule engine:**
  - benefic/malefic per chart (v. 11): the Moon is malefic from the 8th tithi of the dark half to the 8th of the bright
    half (notes), Mercury is malefic when conjunct a malefic; rules written with the natural lists resolve to these;
  - the Moon is exalted only in Taurus 0-3 deg (moolatrikona 3-30), Mercury only in Virgo 0-15 (moolatrikona 15-20,
    own 20-30) - the old tables made the whole sign exalted, so neither ever counted as moolatrikona;
  - Rahu and Ketu have their own natural friendships (p. 39) instead of borrowing Saturn's and Mars's.
  The earlier studies' src/strength.py is unchanged so their published numbers stay reproducible.
- Divisional charts D9, D7, D10, D12: the engine's rules checked against vol. 1 ch. 7 tables - identical.
- Combustion (vol. 1 ch. 8 notes): Moon 12, Mars 17, Mercury 14, Jupiter 11, Venus 10, Saturn 16 deg (the earlier
  engine had Saturn 15), retrograde Mercury and Venus 1 deg less (earlier 2).
- Planetary aspects (vol. 1 ch. 28 v. 2-5): full 7th for all, Saturn 3/10, Jupiter 5/9, Mars 4/8; the book gives Rahu and Ketu
  no special aspect (the earlier study code had 5/9 from K.N. Rao). Sphuta drishti (degree-based value) implemented.
- Sunrise-based quantities (Gulika, Pranapada, day/night birth, weekday) from Swiss Ephemeris rise times.
- Shadbala (vol. 1 ch. 29) in src/rules/bphs_strength.py; the rules' 'strong'/'weak' now mean the book's requirement
  (Sun 390, Moon 360, Mars 300, Mercury 420, Jupiter 390, Venus 330, Saturn 300 virupas) instead of a dignity proxy.
  Approximations logged: cheshta class thresholds, equal-house cusps for dig bala; varsha/masa lords and war omitted.
- **Still general-knowledge:** functional nature / Yogakaraka (ch. 36).

## Computations implemented and checked against the book
| Computation | Chapter | Checked against |
|---|---|---|
| Vimshottari MD/AD/PD/sookshma/prana | 48, 53, 63-65 | p. 12 example, Tables 28-31 |
| Kalachakra dasha, Deha/Jeeva, motions, antardashas | 48, 66 | Tables 14A/14B, 20, 22, 33; examples 8, 89-92 |
| Chara dasha years, order, antardashas | 48, 52-53 | Example 9, Table-24 (10 of 12 entries — see conflicts) |
| Ashtakavarga (all eight) | 68 | Rekha and Bindu chakras, verse totals 48/49/39/54/56/52/39/49 |
| Trikona and Ekadhipatya shodhana, Rashi/Graha/Shodhya pinda | 69-71 | Example 93: reduced rows and pindas 65 + 58 = 123 |
| Planetary rays (raw, before moderation) | 75 | Example 94: Sun, Mars, Mercury, Venus, Saturn; the book writes rays as units and thirtieths |
| Ashtakavarga longevity (Table-37) and Samudaya | 73-74 | Sun's span 12 y 10.5 d (p. 574); Samudaya totals and Ascendant row (p. 579) |
| Ashtakavarga transit points (rekhas x pinda, mod 27 and 12, with trines); Saturn's years | 72 | Example 93: Sun, Mars, Mercury, Jupiter, Saturn rows; pindas 123/146/102/94; points for Mercury and Jupiter; years 17 + 29 = 46 |

## Where the book contradicts itself (and what was encoded)
| Place | Conflict | Encoded |
|---|---|---|
| Ch. 48 Table 14B | Rohini pada 3 labelled "Gem"; its sequence, its years and Table 22 all say Virgo | Virgo |
| Ch. 48 Table 18A vs v. 77 | Table gives the Ardra group Rohini's sequences; the verse says Mrigashira's | Verse |
| Ch. 48 Table-24 | Aquarius 12 and Pisces 1 years contradict v. 159 and the notes (5 and 12) | Verses |
| Ch. 48 | No statement of what follows the 9th Kalachakra or 12th Chara dasha | Left undefined (not invented) |
| Ch. 48 p. 12 vs p. 18 | 360-day year in one example; calendar years in the timeline | Calendar years (360 days only converts fractions) |
| Ch. 52-53 | Three different statements of how Chara antardashas run | Ch. 52 v. 90 with equal twelfths; others logged |
| Ch. 63 p. 537 vs p. 522 | Translator's worked Ashtakavarga example uses the common Moon table; his own chakra, the verse and Santhanam do not | Verse/chakra |
| Ch. 66 v. 41 and v. 44 | Saturn named twice for the Capricorn amsa | Both encoded, logged |
| Ch. 70 v. 3 | Occupied sign smaller than the unoccupied one: the translation says (p. 547) subtract, and (p. 549) raise the occupied one; the Sanskrit says make the unoccupied one equal to the smaller | Sanskrit (the worked example does not exercise this case) |
| Ch. 69-72 worked example 93 | The translator's Moon and Venus Ashtakavargas use the common tables, against his own chakras and the verses (so his Moon pinda 77 and Venus pinda 97 differ from the engine's) | Chakras and verses |
| Ch. 72 example, Saturn | The example keeps Aries at 3 although Aries and Scorpio are equal and unoccupied, which its own Ekadhipatya rule III reduces to zero (pinda 155 vs 134) | Rule as stated |
| Ch. 72 p. 563 | Remainder 11 named "Uttara Phalguni"; the 11th nakshatra is Purva Phalguni, and the trines given (P. Ashadha, Bharani) belong to 11 | Purva Phalguni |
| Ch. 72 v. 36 | Wife's distress from the 7th from Venus: the verse says "as before" (Saturn's transit); the notes say Venus's own transit | Both encoded |
| Ch. 74 v. 3 | Translation: more than 30 rekhas gives 'medium' results; the Sanskrit (trimshadhika... shubhaprada) gives auspicious for >30 and medium for 25-30 | Sanskrit |
| Ch. 75 example 94 | Subtracts the Moon's debilitation as Sagittarius 3 deg; its own table says Scorpio 3 deg | Table |
| Ch. 75 v. 4 | Own sign: translation multiplies rays by 3/12; Sanskrit tribhna dvisambhakta = 3/2 | Sanskrit |
| Ch. 52 v. 6 vs v. 15 | Malefics in the 11th from the dasha sign: beneficial vs obstacles | Both encoded |

## Ashtakavarga: the book differs from the commonly used tables
Three contributions differ from the tables most software uses (and from this project's earlier code). Each one is
confirmed by the verse, the Rekha chakra, the Bindu chakra, and Santhanam's translation:
- Moon's Ashtakavarga: the Moon gives a rekha in the 9th from itself; Mars does **not** give one in the 9th.
- Moon's Ashtakavarga: Jupiter gives one in the 2nd, not the 12th.
- Venus's Ashtakavarga: Mars gives one in the 4th, not the 5th.

## Translation vs printed Sanskrit (selected; full list in the ledger)
| Verse | Translation | Sanskrit | Encoded |
|---|---|---|---|
| 49.23 | debilitated waning Moon: gain of wealth | dhana-hani (loss) | logged (wealth not in data) |
| 49.35 | Rahu exalted Scorpio, Ketu Taurus | Rahu Taurus, Ketu Scorpio | translation; resolve with vol. 1 ch. 3 |
| 49.49-51 | omits combustion for Jupiter | lists asta (combust) | translation |
| 51.25 | Sagittarius amsa, Aries dasha: worries about wealth | dhana-labha (gain) | translation, marked |
| 54.11 | benefics in the 8th from the dasha lord | 9th (bhagya) | translation, marked |
| 54.52 | Mercury with malefics | saumya (benefics) | translation, marked |
| 55.44 | Saturn (in the Mercury section) | no planet named | Mercury |
| 61.40-41 | Ketu (in the Mars section) | bhaume (Mars) | Mars |
| 63.67 | Ketu AD / Sun PD: marriage | vivada (dispute), not vivaha | dispute |
| 64.73 | Saturn (in the Ketu PD, Mercury slot) | budhe (Mercury) | Mercury |
| Several, ch. 54-62 | "in the 2nd/7th" | "lord of the 2nd/7th" | translation, marked |

## Defects in the scan of Sharma vol. 2 (archive.org; MD5 8beb6173…; Scribd copies are the same scan)
| Book page | In its place | Content lost | Resolution |
|---|---|---|---|
| 219 | p. 103 | Moon MD: Moon/Moon and Mars AD verses | Santhanam vol. 2 pp. 640-641 |
| 318 | p. 57 | notes only | none needed |
| 353 | p. 269 | Mercury MD: Saturn AD v. 65-70 | Santhanam pp. 716-717 |
| 395 | p. 119 | Venus MD: Saturn AD v. 52-57 | Santhanam pp. 737-738 |
| 409 | front matter p. xv | worked example only | none needed |
| 449 | p. 429 | notes only | none needed |
| 555 | p. 141 | ch. 72 v. 6-9 (Ashtakavarga results) | Santhanam |
| 704, 708, 709 | pp. 4, 278, 551 | ch. 83 physiognomy verses | none needed |
| 722, 726-727, 729, 734-735 | pp. 256, 448, 499, 89, 467, 715 | ch. 85 childlessness yogas | Santhanam vol. 2 ch. 83 pp. 991-998 |
| 741-742, 754-755, 757-758 | pp. 656, 467, 22, 139, 648, 675 | ch. 86, 91, 92 ritual verses | none needed (ritual, checked in Santhanam) |
| 643 | p. 567 | ch. 79 v. 14-18 (cosmology) | none needed |
| 651 | p. 40 | ch. 80 v. 3-7 (horary method) | none needed |
| 619 | p. 73 | ch. 77 v. 1-2 (yoga definitions) | Santhanam |
| 622 | p. 332 | ch. 77 v. 8-12 (Bhadra) | Santhanam |
| 603 | p. 63 | ch. 76 v. 4-6 (structure; the figure on p. 604 survives) | none needed |
| 596 | p. 6 | ch. 75 worked arithmetic for Jupiter/Venus | none needed |
| 572 | p. 525 | ch. 73 v. 1-4 (Table-37 survives) | Santhanam |
| 588 | p. 99 | ch. 74 v. 30-31 (muhurta instruction) | Santhanam |
| 559-560 | pp. 306, 367 | ch. 72 v. 19-23 | Santhanam |
| 571 | p. 35 | end of ch. 72 v. 43-44 | Santhanam (no further verses) |
| 530 | p. 299 | Ascendant's Rekha list | Santhanam pp. 864-865 = complement of Sharma's Bindu chakra p. 529 |

## Ashtakavarga conventions
- The Samudaya includes the Ascendant's own Ashtakavarga (ch. 74 example, p. 579), so sign totals run to about 32 on average.
- Ch. 73 longevity is a point estimate; encoded as death within one year of it (the text gives no tolerance).
- "More rekhas" = rekhas outnumber dots in that sign (5 or more of the 8 marks), because the book says each sign carries
  8 marks in all (p. 537); "more dots" = 3 or fewer.
- Remainder 0 counts as the 27th nakshatra / 12th sign (the book's own example, p. 564).
- Nakshatra trines are the 10th and 19th; sign trines the 5th and 9th (both stated in the notes and examples).
- "Afflicted / Arishta dasha" in ch. 72 is encoded as the MD or AD of the 6th/8th/12th lord (father) or of a maraka,
  the 2nd/7th lord (native) - the chapter does not define it further; to be revisited with vol. 1 ch. 46.

## Sudarshana (ch. 76)
- Running sign = starting sign + completed years (one house a year), and + months elapsed within the year for the
  monthly level, from each of the Lagna, Moon and Sun. The Moon and Sun circles are applied only when they occupy a
  different sign from the Lagna (v. 19-20).

## Ages stated in the text
- Ch. 77 gives fixed ages at death for the five Mahapurusha yogas (70 or 100); encoded as death within the year
  after that age. Fixed-age statements are a sharp test: they either cluster or they do not.

## Panchanga atoms (ch. 87-98)
- Tithi = elongation of the Moon from the Sun / 12 deg (1-30, Krishna Chaturdashi = 29, Amavasya = 30); parts of a tithi
  by elongation. Gandanta windows are given in ghatis; converted at the mean rate of each quantity (a tithi or a
  nakshatra ~ 60 ghatis; half a ghati of Lagna ~ 0.25 deg) - an approximation, logged.

## Natal rules
- Natal statements (character, renunciation, the husband, children, widowhood, status) are stored with `kind: natal` and a
  domain; they are tested against graded outcomes, not event dates. Ch. 82 applies only to women (new `gender` atom).

## Santhanam's reading of ch. 85
- Santhanam notes that 'childlessness' in this chapter means lack of a male issue (vol. 2 p. 992). Rules keep the
  general domain 'children'; the narrower reading is noted for the outcome questionnaire.

## Testability caveats recorded while reading
- Sookshma and prana results (ch. 64-65) apply to periods of days or hours; the book itself says they need an exact,
  rectified birth time. Expect them to work only, if at all, for the best-rated birth times.
- Chapter 67 restates chapter 51; it is logged but not encoded twice, so the same statements are not double-counted.
- Many results concern things the event data cannot see (wealth, travel, education, cattle); these are listed per
  chapter as untestable rather than mapped loosely.
