# BPHS ch. 48 — dasha computations, as the book states them (vol. 2 pp. 1-110, PDF 25-134)
Working notes while reading; each item cites the book page. Paraphrased, no translation text.

## General (pp. 1-4)
- 32 dasha types listed (Table-1 p. 4): Vimshottari, Astottari, Shodashottari, Dwadashottari, Panchottari, Shatabdika,
  Chaturashiti-sama, Dwisaptati-sama, Shashtihayani, Shattrimshat-sama, Kala, Chakra, Kalachakra, Chara, Sthira,
  Brahma-graha, Yogardha, Kendradi, Karaka, Mandooka, Shoola, Trikona, Driga, Rashi, Panchaswara, Yogini, Pinda,
  Amsa, Naisargika, Ashtakavarga, Sandhya, Pachaka, Tara. Vimshottari is the main one (v. 3, 14); Kalachakra
  "greatest recognition" among the others (v. 6).

## Vimshottari (pp. 3-18)
- Lords from Krittika: Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu, Venus, three cycles (v. 12-13).
- Years 6, 10, 7, 18, 16, 19, 17, 7, 20 = 120 (v. 15).
- Balance: elapsed = years x bhayaata / bhabhoga (v. 16) — i.e. the fraction of the nakshatra traversed.
- **Year length: the worked example (p. 12) uses 19 years = 6840 days, i.e. 360-day years** (1120 days = 3y 1m 10d).
  Our engine uses 365.25 — test both.
- Matches src/features.py vimshottari except the year length.

## Astottari (pp. 19-26)
- Use when Rahu is in a kendra or trikona from the Lagna lord but not in the Lagna (v. 17); some say: birth in the
  day in Krishna paksha or at night in Shukla paksha (v. 23); notes p. 20: Shukla -> Vimshottari, Krishna -> Astottari.
- Starts from Ardra; lords and nakshatra counts: Sun 4 (Ardra-Ashlesha), Moon 3, Mars 4, Mercury 3, Saturn 4
  (incl. Abhijit), Jupiter 3, Rahu 4, Venus 3 (v. 18-19, Table-5 p. 22). Years Sun 6, Moon 15, Mars 8, Mercury 17,
  Saturn 10, Jupiter 19, Rahu 12, Venus 21 = 108 (v. 20).
- Period split equally among the lord's nakshatras (v. 21-22, Table-5).
- Abhijit = last quarter of Uttara Ashadha + first 1/15 of Shravana (253'20"); U.Ashadha shrinks to 600', Shravana to
  746'40" (p. 20, 23). Saturn: P.Ashadha, U.Ashadha, Abhijit, Shravana each 2y6m.
- Balance from bhayaata/bhabhoga of the birth nakshatra, plus the remaining nakshatras of the same lord (pp. 23-26).
- p. 28 note: "360 days in a year, 30 days each month" — explicit year length for dasha arithmetic.

## Shodashottari (pp. 28-30)
- Use when Lagna is in the Moon's hora in Krishna paksha, or in the Sun's hora in Shukla paksha (v. 24).
- Count nakshatras from Pushya to the birth nakshatra, divide by 8; remainder -> lord in order Sun, Mars, Jupiter,
  Saturn, Ketu, Moon, Mercury, Venus (no Rahu) (v. 25-26). Years 11, 12, 13, 14, 15, 16, 17, 18 = 116.
- Table-6 p. 30: Sun = Pushya, Vishakha, Shatabhisha, Mrigashira; Mars = Ashlesha, Anuradha, P.Bhadra, Ardra;
  Jupiter = Magha, Jyeshtha, U.Bhadra, Punarvasu; Saturn = P.Phalguni, Moola, Revati; Ketu = U.Phalguni, P.Ashadha,
  Ashwini; Moon = Hasta, U.Ashadha, Bharani; Mercury = Chitra, Shravana, Krittika; Venus = Swati, Dhanishta, Rohini.
- Balance as Vimshottari (whole lord period over one nakshatra) — example p. 29.

## Dwadashottari (p. 30-)
- Use when the Lagna falls in a Navamsa of Venus (v. 27).
- Count from the birth nakshatra to Revati, divide by 8; remainder -> lord in order Sun, Jupiter, Ketu, Mercury,
  Rahu, Mars, Saturn, Moon (no Venus); years 7, 9, 11, 13, 15, 17, 19, 21 = 112 (v. 27-28).
  (Translation's printed list "6, 7, 9, 11..." vs the stated +2 rule and the Sanskrit "saptataḥ" (from 7): the years
  start at 7.) Table-7 p. 31 confirms Sun 7 ... Moon 21 = 112, counted in reverse from Revati: Sun = Revati, Moola,
  P.Phalguni, Krittika; Jupiter = U.Bhadra, Jyeshtha, Magha, Bharani; Ketu = P.Bhadra, Anuradha, Ashlesha, Ashwini;
  Mercury = Shatabhisha, Vishakha, Pushya; Rahu = Dhanishta, Swati, Punarvasu; Mars = Shravana, Chitra, Ardra;
  Saturn = U.Ashadha, Hasta, Mrigashira; Moon = P.Ashadha, U.Phalguni, Rohini.

## Generic pattern for the conditional nakshatra dashas (pp. 30-39)
Each: start nakshatra, count direction, lord order, years; lord = (count from start to birth nakshatra) mod n;
balance as Vimshottari (bhayaata/bhabhoga of the birth nakshatra x full period). Conditions and data:
| dasha | use when | start, direction | lords (years) | total |
|---|---|---|---|---|
| Panchottari (v. 29-31, Table-8 p. 32) | Cancer Lagna AND Cancer Dwadashamsa Lagna | Anuradha, forward, mod 7 | Sun 12, Mercury 13, Saturn 14, Mars 15, Venus 16, Moon 17, Jupiter 18 | 105 |
| Shatabdika (v. 32-34, Table-9 p. 33) | Lagna vargottama (same sign in D1 and D9) | Revati, forward, mod 7 | Sun 5, Moon 5, Venus 10, Mercury 10, Jupiter 20, Mars 20, Saturn 30 | 100 |
| Chaturashiti-sama (v. 35-36, Table-10 p. 35) | 10th lord in the 10th | Swati, forward, mod 7 | Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, 12 each | 84 |
| Dwisaptati-sama (v. 37-39, Table-11 p. 36) | Lagna lord in the 7th, or 7th lord in the Lagna | Moola, forward, mod 8 | Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, 9 each | 72 |
| Shashtihayani (v. 40-41, Table-12 p. 38) | Sun in the Lagna | Ashwini, groups of 3,4,3,4... with Abhijit (28 nakshatras) | Jupiter 10 (Ashwini-Krittika), Sun 10 (Rohini-Punarvasu), Mars 10 (Pushya-Magha), Moon 6 (P.Phalguni-Chitra), Mercury 6 (Swati-Anuradha), Venus 6 (Jyeshtha-U.Ashadha), Saturn 6 (Abhijit-Dhanishta), Rahu 6 (Shatabhisha-Revati) | 60 |
| Shat-trimsha-sama (v. 42-43, Table-13 p. 39) | day birth with Lagna in the Sun's hora, or night birth with Lagna in the Moon's hora | Shravana, forward, mod 8 | Moon 1, Sun 2, Jupiter 3, Mars 4, Mercury 5, Saturn 6, Venus 7, Rahu 8 | 36 |
Shashtihayani splits the lord's period equally over its nakshatras (like Astottari), example p. 37-38.
Worked examples to test against: Shodashottari p. 29 (Mrigashira, factor 1230/3610 -> Sun, 3y8m29d expired);
Shatabdika p. 34 (Mars, 6.82y expired); Chaturashiti p. 35 (Mercury, 4y1m3d); Shashtihayani p. 37-38 (Sun, 6y7m23d bal).
No separate results chapter is given for these; they would carry the ch. 49/50 planet results for natives who
qualify — a testing variant, not new rules.

## Kala dasha (v. 44-49, pp. 39-42)
- Day split: 5 ghatis either side of sunrise = Khanda (morning sandhya), either side of sunset = Sudha; between
  them (day) = Poorna, night between them = Mugdha (20 ghatis each; 60 ghatis = 24 h).
- Poorna/Mugdha birth: ghatis elapsed in that segment x 2 / 15 = factor (years). Khanda/Sudha: elapsed x 4 / 15.
- Dasha of the nth planet (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu) = factor x n.
- Notes p. 41: the cycle starts from the weekday lord (Monday birth -> Moon first) — translator's reading; the verse
  says Sun to Rahu in natural order. Example-6 p. 41-42 (Monday, 2 gh 25 pal after sunrise -> factor 1y11m22d).
- Notes p. 42: other editions multiply by 6 (Poorna) / 12 (Khanda) and divide by 45 — same result.
- No results chapter -> not needed for rules; logged.

## Chakra dasha (v. 50-51, p. 43)
- Sign dashas, 10 years each, in zodiacal order; start sign: night birth -> Lagna sign; day birth -> sign of the
  Lagna lord; twilight (sandhya) birth -> 2nd house sign. No results chapter; logged.

## Kalachakra (v. 52-, pp. 44-)
- Nakshatras in groups of three alternate between the Savya and Apasavya chakra, starting Ashwini, Bharani,
  Krittika = Savya; Rohini, Mrigashira, Ardra = Apasavya; ... Savya holds 15, Apasavya 12 (v. 56-58).
  Savya: Ashwini, Bharani, Krittika, Punarvasu, Pushya, Ashlesha, Hasta, Chitra, Swati, Moola, P.Ashadha, U.Ashadha,
  P.Bhadra, U.Bhadra, Revati. Apasavya: Rohini, Mrigashira, Ardra, Magha, P.Phalguni, U.Phalguni, Vishakha, Anuradha,
  Jyeshtha, Shravana, Dhanishta, Shatabhisha.
- Tables 14A/14B (pp. 46-47), transcribed from a 3x render and checked (row years sum to the stated total; the
  Savya rows equal the ch. 51 verse sequences exactly):
  Sign years: Ar 7, Ta 16, Ge 9, Cn 21, Le 5, Vi 9, Li 16, Sc 7, Sg 10, Cp 4, Aq 4, Pi 10.
  SAVYA, by amsa of the pada (Aries..Pisces), 9 dasha signs (first = Deha, last = Jeeva), total years:
    Ar: Ar Ta Ge Cn Le Vi Li Sc Sg (100)   Ta: Cp Aq Pi Sc Li Vi Cn Le Ge (85)
    Ge: Ta Ar Pi Aq Cp Sg Ar Ta Ge (83)    Cn: Cn Le Vi Li Sc Sg Cp Aq Pi (86)
    Le: Sc Li Vi Cn Le Ge Ta Ar Pi (100)   Vi: Aq Cp Sg Ar Ta Ge Cn Le Vi (85)
    Li: Li Sc Sg Cp Aq Pi Sc Li Vi (83)    Sc: Cn Le Ge Ta Ar Pi Aq Cp Sg (86)
    Sg = Ar row, Cp = Ta row, Aq = Ge row, Pi = Cn row.
  Savya group 1 (Ashwini, Punarvasu, Hasta, Moola, P.Bhadra) padas 1-4 = amsas Ar Ta Ge Cn; group 2 (Bharani,
  Pushya, Chitra, P.Ashadha, U.Bhadra) = Le Vi Li Sc; group 3 (Krittika, Ashlesha, Swati, U.Ashadha, Revati) = Sg Cp
  Aq Pi — i.e. the pada's own navamsa sign.
  APASAVYA: each row is the reversed Savya sequence of a "mirror" amsa (first = Jeeva, last = Deha):
    Rohini group (Rohini, Magha, Vishakha, Shravana) padas 1-4 labelled Sc, Li, "Gem", Le;
    Mrigashira group (Mrigashira, P.Phalguni, Anuradha, Dhanishta) Cn, Ge, Ta, Ar;
    Ardra group (Ardra, U.Phalguni, Jyeshtha, Shatabhisha) Pi, Aq, Cp, Sg.
    Rule: label = (7 - own navamsa index) mod 12. PRINT ERROR: Rohini pada 3 is labelled "Gem" but its sequence
    (Vi Le Cn Ge Ta Ar Sg Cp Aq) and years (85) are the reversed Virgo row — the mirror rule gives Virgo.
  ch. 51 results are keyed by amsa label and savya position; for Apasavya the native runs the sequence in reverse,
  so apasavya position p = savya position 10-p (same sign). This mapping is my reading of the tables; logged.
- Verses 60-81 (pp. 48-51) state the sequences pada by pada for Ashwini, Bharani, Rohini, Mrigashira; all agree with
  Tables 14A/14B. v. 73 translation lists Rohini pada 1 lords "9,10,11,12,1,2,3,5 and 7" — the table and the
  Sanskrit give ...5, 4 (Cancer = Deha); the "7" is a print error. v. 77: the remaining Apasavya nakshatras
  (Mrigashira, Ardra, P.Phalguni, U.Phalguni, Anuradha, Jyeshtha, Dhanishta, Shatabhisha) follow Mrigashira.
- CONFLICT: translator's Table 18A (p. 57) footer assigns the "3rd spur" (Ardra group) to the Rohini sequences;
  verse 77 and Table 14B give the Ardra group Mrigashira's sequences. Encoded per the verse (and the mirror rule,
  which yields the same: Pi/Aq/Cp/Sg savya rows = Cn/Ge/Ta/Ar rows). Table 17A/18A years typos: Leo "2", Sagittarius "16".
- v. 85-86 (p. 59): paramayu = sum of the 9 sign years of the birth pada. v. 87-88 (p. 60): pada navamsa = (nakshatras
  passed from Ashwini mod 3) x 4 + pada, counted from Aries (= natural navamsa; Savya). Table-22 (p. 74) gives the
  Apasavya labels = mirror rule, incl. Virgo for Rohini pada 3 (confirms 14B "Gem" is a misprint). Notes p. 73 also
  say the Apasavya allotment runs in reverse from Scorpio.
- v. 89 (p. 61): paramayu Ar/Le/Sg amsa 100, Ta/Vi/Cp 85, Ge/Li/Aq 83, Cn/Sc/Pi 86.
- v. 90-92 (pp. 61-64): expired years = (elapsed part of the pada / whole pada) x paramayu; the expired years are
  consumed through the 9 signs in order; the sign containing that point runs at birth with the remainder as balance.
  v. 93: same via longitude: (arc of the Moon into its pada / 200') x paramayu. Examples: Kritika pada 1, factor
  0.6056 -> 4y0m13d expired, Aries/Mars balance 2y11m17d (p. 62, Table-20 cycle to 2047); Example 8 (Moon 0s26d47m,
  7' into Kritika pada 1 -> 3.5 y expired, Mars balance 3y6m) (pp. 64-65).
- GAP: the book does not say what follows the 9th dasha of the pada (Table-20 simply ends). Engine returns no
  Kalachakra dasha after the pada's sequence is exhausted; rules then do not fire. Logged, not invented.
- v. 94-95 (p. 65): Savya: first sign = Deha, last = Jeeva; Apasavya: first = Jeeva, last = Deha. Notes: Deha/Jeeva
  only for Mahadashas.
- v. 96-100 (pp. 66-67) gati (motion) of the sign dasha: Mandooka = Virgo-Cancer, Leo-Gemini; Markati = Cancer-Leo;
  Simhavalokana = Pisces-Scorpio, Sagittarius-Aries. The Sanskrit names unordered pairs (duals); results are given
  for every motion in both Savya and Apasavya (v. 101-108), which only occurs if the pairs are taken in either
  direction (Apasavya runs the reversed sequences) -> encoded as unordered pairs; logged. First dasha at birth has no
  motion (no previous sign).
- v. 101-108 (pp. 68-69) motion results: Savya Mandooka: fear, pain among friends, father distressed, fear of poison,
  weapons, fire, fever, thieves; Mandooka in Leo/Gemini: death of mother, own death, fear of authorities, dreaded
  disease. Savya Markati: loss of wealth/animals, death of father or elders. Savya Simhavalokana: trouble to animals,
  loss of friends' affection, falls, poison/weapons/fire, vehicle falls, fever, loss of dwelling. Apasavya Mandooka:
  trouble to wife and children, fever, fall in status. Apasavya Markati: fear of water, loss of position, death of
  father, punishment by authorities, wandering. Apasavya Simhavalokana: loss of service/rank, death of father or near
  relation.
- v. 109-111 (p. 70) directional special effects: Pisces->Scorpio fever; Virgo->Cancer destruction of brothers and
  friends; Leo->Gemini illness to wife; Cancer->Leo death of the native; Sagittarius->Aries death of brother or father;
  dasha signs occupied by malefics/benefics give bad/good results.
- v. 114-119 (p. 71) directional travel results (journeys in given directions) — journey-conditional, untestable,
  except: Sagittarius->Scorpio: comforts, fame, woman (marriage) (v. 118).
- v. 120-122 (p. 72) natal, by the Kalachakra amsa of birth: Ar brave/thief, Ta wealthy, Ge learned, Cn kingship,
  Le honoured by king, Vi scholar, Li minister, Sc pauper, Sg highly educated, Cp sinful, Aq businessman, Pi wealthy.
- v. 123-128 (pp. 75-76) Deha/Jeeva occupation (natal, and for the period): Sun, Mars, Saturn, Rahu in Deha or
  Jeeva -> death anticipated (more than one: disastrous); malefics in Deha -> disease; in Jeeva -> mental suffering;
  3 malefics -> early death, 4 -> death; malefics in both -> persecution by king, theft, death; Sun there -> fire;
  waning Moon -> drowning; Mars -> weapons; Mercury -> inflammatory disease; Saturn -> spleen; Rahu/Ketu -> poison;
  Mercury/Jupiter/Venus there -> comforts, freedom from disease; mixed -> mixed.
- v. 129-130 (p. 76): dasha of a sign ruled by a malefic -> distress; by a benefic -> auspicious; malefic sign with a
  benefic planet, or benefic sign with a malefic planet -> mixed.
- v. 131-154 (pp. 76-80) dasha sign by house from the Lagna (benefic sign = full good / malefic sign = opposite or
  partial, as stated per house): 1st health, comforts; exalted/own-sign planet in it -> honour, high status (v. 132);
  2nd meals, wife and children, wealth; 3rd brothers, courage, recognition from king; 4th relatives, property,
  conveyance; 5th birth of children, sound health, appreciation; 6th wrath of king, fire/poison/weapons, jaundice,
  diarrhoea (malefic sign full, benefic reversed); 7th marriage, birth of children, commendation (benefic full,
  malefic partial); 8th change of residence, death of relatives, poverty, danger from enemies (malefic full, benefic
  mitigated); 9th marriage, children, wealth (benefic full, malefic partial); 10th recognition, authority (benefic
  full, malefic mixed); 11th happiness, king's affection, good health; 12th failure, body pains, loss of occupation
  (malefic full, benefic marginal).
## Chara (v. 155-167, pp. 81-88)
- Years of a sign = count from the sign to its lord's sign, minus 1 (example p. 85: count 5 -> 4 years); counting
  forward for signs of the odd "quarters" (Ar Ta Ge, Li Sc Sg), backward for even (Cn Le Vi, Cp Aq Pi) (v. 155-156,
  Table-23). Lord in its own sign -> 12 years (notes p. 86, both directions).
- Scorpio: Mars and Ketu; Aquarius: Saturn and Rahu (v. 157). Both lords in the sign -> 12 years; one in the sign,
  the other elsewhere -> count to the one elsewhere; both elsewhere -> count to the stronger (v. 158-161).
  Stronger = conjunct with more planets; tie -> by sign: dual > fixed > movable; tie -> the one giving more years
  (v. 161-163). Exalted lord has priority; +1 year if the lord is exalted, -1 if debilitated (v. 164-165).
- Order: from the Lagna, forward if the 9th house sign is in an odd quarter, backward if even (v. 167).
- Example 10 (p. 86-87, Capricorn Lagna; Jup Pi, Moon Ar, Sun/Mars/Mer Ta, Ven Cn, Ket Le, Sat Vi, Rah Aq) Table-24:
  Cp 4, Sg 3, Sc 6, Li 9, Vi 4, Le 3, Cn 3, Ge 11, Ta 2, Ar 1, Pi 1, Aq 12. The verse rules reproduce 10 of 12;
  CONFLICTS: Aquarius (Rahu in Aq, Saturn in Vi: v. 159 -> count to Saturn, backward = 5; table 12) and Pisces
  (Jupiter in own sign -> 12 per notes p. 86; table 1). Verses followed; test asserts the 10.
- Notes p. 87-88: a degree-proportional variant; p. 88: the text's whole-sign count is the classical rule — used.

- Chara antardashas — THREE statements in the book: (a) ch. 52 v. 90 (p. 176): from the sign holding the dasha
  sign's lord, 12 signs in seriatim; (b) ch. 53 v. 5-6 (p. 182): each = dasha years / 12, starting from the stronger
  of the dasha sign and its 7th, forward if that sign is odd, backward if even; (c) ch. 53 v. 7-12 (p. 183-184):
  movable dasha sign -> seriatim; fixed -> every 6th sign; dual -> kendras from it, then kendras from its 9th...
  Implemented: (a) with (b)'s equal twelfths — the only version computable without sign strength (vol. 1). Logged.
- Paka = the dasha sign; Bhoga = a second sign defined by distance (ch. 53 v. 10-12, unclear); malefics in them ->
  bodily pain and mental distress (v. 12) — encoded for the Paka only.

## Sthira / Brahma-graha (v. 168-173, pp. 89-92)
- Movable signs 7 years, fixed 8, dual 9; starts from the sign of the Brahma-graha; forward if that sign is odd,
  backward if even (v. 168-169; notes p. 90).
- Brahma = the strongest of the lords of the 6th, 8th, 12th from the stronger of Lagna / 7th, placed in an odd sign
  and in the 6 houses behind (v. 171-173; notes p. 91 give the house lists). Further alternatives (8th lord from the
  Atmakaraka, Saturn/Rahu/Ketu exceptions, greater longitude) and a long strength cascade (notes pp. 90-91).
- Example 11 p. 91-92: 7th stronger (has a planet); Brahma = Mars (8th lord from Atmakaraka Moon), Taurus, backward.
- Ch. 52 gives results for "Chara, Sthira etc." — build after reading ch. 52 fully.

## Other sign dashas (pp. 92-104) — computation noted; results only where a results chapter gives them
- Yogardha (v. 174): years = (Chara + Sthira)/2, from the stronger of Lagna/7th. Example p. 93 Cancer 3+7 /2 = 5.
- Kendradi (v. 175-177): kendra, panaphara, apoklima signs from the stronger of Lagna/7th, ordered by strength,
  forward/backward by odd/even; years as Chara; Karaka-Kendradi variant from the Atmakaraka; examples pp. 94-95.
- Karaka (v. 178): from the Atmakaraka in karaka order; years = count from Lagna to the karaka (Lagna -> 12).
  Example p. 97-98 (karaka order Moon, Sun, Jupiter, Mars, Rahu, Saturn, Venus, Mercury).
- Mandooka/Trikoota (v. 179-180): from the stronger of Lagna/7th, jumping every third sign; Sthira years.
- Shoola (v. 181-182): from the stronger of the 2nd/8th; Sthira years. RULE: death in the dasha of the strong
  maraka sign — translation says "strong Capricorn sign" but the Sanskrit is "bali-maraka-bhe" (strong maraka
  sign): logged; needs maraka signs (vol. 1 ch. 46).
- Trikona (v. 183-184): from the strongest of 1/5/9, Chara years. Driga (v. 185-187): 9th, 10th, 11th and the signs
  each aspects (sign aspects per vol. 1 ch. 9), Sthira years. Lagnadi-Rasi (v. 188-190): start sign = Lagna
  longitude + 12 x (bhayaata/bhabhoga) signs; Sthira years; balance by degrees (example p. 103-104).
- Panchaswara (v. 191-194): from the first letter of the name — no names in our data; X.
- Yogini (v. 195-199): Mangala 1 (Moon), Pingala 2 (Sun), Dhanya 3 (Jupiter), Bhramari 4 (Mars), Bhadrika 5
  (Mercury), Ulka 6 (Saturn), Siddha 7 (Venus), Sankata 8 (Rahu); (birth nakshatra no. + 3) mod 8 -> first, balance
  by bhayaata/bhabhoga; example p. 106-107 (Kritika -> Ulka, balance 5y11m10d).
- Pinda/Amsa/Naisargika (v. 200-202): years = the pindayu/amsayu/naisargika ayu of each planet (vol. 1 ch. 45);
  from the strongest of Lagna/Sun/Moon then planets in its kendras, panapharas, apoklimas.
- Ashtakavarga dasha (v. 203): by ashtakavarga strength (ch. 63-69 per notes).
- Sandhya (v. 204): 10 years each sign from the Lagna; Pachaka (v. 205-206) subdivision; Table-26.
- Tara (v. 207-209): like Vimshottari but the periods are named Janma, Sampat, Vipat, Kshema, Pratyak, Sadhana,
  Naidhana, Mitra, Parama-mitra, starting from the strongest planet in a kendra; "results according to the name"
  (sampat wealth, vipat calamity, kshema welfare, pratyak obstacle, sadhana accomplishment, naidhana death, mitra /
  parama-mitra friend); applies only when planets occupy kendras. Needs the strength definition (vol. 1 ch. 29).
- v. 210: antardasha results to come (ch. 53 ff).

- v. 84 (p. 52, Table-15): sign years via their lords — Sun 5 (Leo), Moon 21 (Cancer), Mars 7, Mercury 9, Jupiter 10,
  Venus 16, Saturn 4.
