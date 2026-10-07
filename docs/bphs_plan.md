# BPHS — whole-book plan (G.C. Sharma tr., Sagar 1995, 2 vols)

Goal (user, 2026-10-02): the whole book analysed and implemented — every page read, every rule encoded from the
text with a page citation, nothing from memory. Progress is tracked here and in `rules/coverage.json`.

Every chapter is read in full. What happens to it depends on its kind:
- **T** timing rules (dashas, transits) → `rules/bphs/chNN.py` → testable on event dates now.
- **N** natal rules (birth chart → life domain) → natal rules; testable once graded outcomes exist.
- **C** computation (how to calculate a dasha, varga, bala, ashtakavarga…) → an engine primitive in `src/`, with
  tests against the book's worked examples where it gives them.
- **X** read, nothing testable on our data (remedies, rituals, body marks, horary, mythology) → logged in the ledger
  with what the chapter contains, so the coverage is complete.

Order: vol. 2 first (timing), then vol. 1 (natal + the primitives the natal rules need).

## Volume 2 (PDF page = book page + 24)
| ch | title | book pp | kind | status |
|---|---|---|---|---|
| 48 | Dasa systems (Vimshottari, Ashtottari, Kalachakra, Chara, Yogini, etc.) | 1-110 | C+T | read; KC + Chara implemented; 92 rules; Shoola/Tara pending |
| 49 | Results of the Dasas | 111-132 | T | read; 84 rules; primitive-dependent notes pending |
| 50 | Dasas of house lords | 133-143 | T | done; 47 rules |
| 51 | Kalachakra Dasa results | 144-157 | T | done; 134 rules |
| 52 | Chara Dasa results | 158-177 | T | read; 80 rules; strength/argala/maraka-dependent rules pending |
| 53 | Computation of Antardasas | 178-187 | C | read; Chara AD implemented (variant a); 2 rules (in ch52 file) |
| 54 | Antardasas in Sun MD | 188-215 | T | done; 100 rules |
| 55 | Antardasas in Moon MD | 216-234 | T | done except missing scan p. 219; rules in ch55.py |
| 56 | Antardasas in Mars MD | 235-256 | T | done |
| 57 | Antardasas in Rahu MD | 257-281 | T | done |
| 58 | Antardasas in Jupiter MD | 282-305 | T | done |
| 59 | Antardasas in Saturn MD | 306-328 | T | done |
| 60 | Antardasas in Mercury MD | 329-354 | T | done except missing scan p. 353 |
| 61 | Antardasas in Ketu MD | 355-378 | T | done |
| 62 | Antardasas in Venus MD | 379-400 | T | done except missing scan p. 395 |
| 63 | Pratyantardashas | 401-428 | T | done; 81 AD/PD pairs |
| 64 | Sookshma dashas | 429-452 | T | done; 81 PD/SD pairs; SD level added |
| 65 | Prana dashas | 453-471 | T | done; 81 SD/PR pairs |
| 66 | Kalachakra antardashas | 472-497 | T+C | done; KC AD implemented, tested vs examples 89-92 |
| 67 | Kalachakra navamsa-sign dashas | 498-504 | T | read; duplicate of ch. 51 (no new rules) |
| 68 | Ashtakavarga | 505-530 | C | done; src/rules/bphs_av.py |
| 69 | Trikona Shodhana | 531-545 | C | done; tested vs example 93 |
| 70 | Ekadhipatya Shodhana | 546-549 | C | done |
| 71 | Pinda Shodhana | 550-553 | C | done |
| 72 | Results of Ashtakavarga | 554-571 | T+N | done; 22 rules; AV transit atoms |
| 73 | Longevity from Ashtakavarga | 572-577 | T | done |
| 74 | Samudaya Ashtakavarga | 578-588 | T | done; 27 rules (with ch. 73 in ch73.py) |
| 75 | Planetary rays | 589-601 | C+N | done; 18 natal rules |
| 76 | Sudarshana Chakra (yearly/monthly dashas) | 602-618 | T+C | done; 42 rules; sud atom |
| 77 | Pancha Mahapurusha yogas | 619-634 | N+T | done; 11 rules (death ages testable) |
| 78 | Five elements | 635-639 | T | done; 13 rules |
| 79 | Gunas | 640-649 | X | read; nothing testable |
| 80 | Lost horoscope | 650-658 | X | read; horary |
| 81 | Yogas for asceticism | 659-663 | N | done; 6 natal rules |
| 82 | Female horoscope | 664-694 | N | done; 23 natal + 1 event rule; gender atom |
| 83 | Parts of a woman's body | 695-713 | X | read; physiognomy |
| 84 | Body marks | 714-717 | X | read; physiognomy |
| 85 | Curses of previous birth (childlessness) | 718-738 | N | done; 62 natal rules (27 from Santhanam) |
| 86 | Propitiation of planets | 739-744 | X | read; ritual |
| 87-98 | Inauspicious births and remedies (Amavasya, Krishna-Chaturdashi, Bhadra, relatives' nakshatras, Sankranti, eclipses, Gandanta, Abhukta Moola, Jyeshtha, Tritara, abnormal births) | 745-778 | N+X | done; 18 rules; tithi/nakshatra/gandanta atoms |
| 99 | Horary | 779-793 | X | read; added text, not BPHS |
| 100 | Epilogue | 794-797 | X | read |

**Volume 2 complete 2026-10-02.**

**Volume 1 complete 2026-10-03 (PDF = book + 11).**

## Volume 1
| ch | title | book pp | kind |
|---|---|---|---|
| 1-2 | Creation, incarnations | 1-11 | X |
| 3 | Planetary characters (dignities, friendships, upagrahas, Gulika) | 12-49 | C |
| 4 | Signs | 50-60 | C |
| 5 | Planetary positions, bhavas | 61-86 | C |
| 6 | Special ascendants, Varnada dasa | 87-96 | C+N |
| 7 | Sixteen divisions | 97-138 | C |
| 8 | Divisional consideration, Vimshopaka | 139-156 | C+N |
| 9 | Aspects of signs | 157-162 | C |
| 10 | Surroundings at birth | 163-170 | N |
| 11 | Evils at birth (short life, parents) | 171-185 | N |
| 12 | Antidotes | 186-188 | N |
| 13 | Judgement of houses | 189-193 | N |
| 14-25 | Effects of houses 1-12 (incl. timing of marriage, illness, wife's death, father's death) | 194-274 | N (+T) |
| 26 | Effects of house lords in houses (144 combinations) | 275-340 | N |
| 27 | Non-luminous planets (Dhuma, Gulika...) | 341-358 | N |
| 28 | Planetary aspects | 359-384 | C |
| 29 | Strengths (Shadbala, Bhavabala) | 385-414 | C |
| 30 | Ishta and Kashta | 415-418 | C+N |
| 31 | Bhava padas (Arudha) | 419-429 | C+N |
| 32 | Upapada | 430-439 | C+N |
| 33 | Argala | 440-444 | C+N |
| 34 | Karakas | 445-454 | C |
| 35 | Karakamsa | 455-472 | N |
| 36 | Yogakarakas / functional nature by Lagna | 473-494 | C+N |
| 37 | Nabhasa yogas | 495-517 | N |
| 38 | Many other yogas | 518-537 | N |
| 39 | Lunar yogas | 538-542 | N |
| 40 | Solar yogas | 543-544 | N |
| 41 | Raja yogas | 545-555 | N |
| 42 | Royal association | 556-559 | N |
| 43 | Wealth | 560-570 | N |
| 44 | Penury | 571-574 | N |
| 45 | Longevity | 575-607 | C+N |
| 46 | Marakas | 608-617 | T+N |
| 47 | Avasthas | 618-end | C+N |
