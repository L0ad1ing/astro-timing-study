# astro-timing-study — Technical Architecture

Written 2026-10-01 against the code as of the 23-method study (~3,000 lines of Python, 11 modules, 6 scripts,
29 tests). The later continuous-harmonic and rule-mining work (`src/harmonic_features.py`, `src/discovery_v2/`)
is summarised in the README and specified in `docs/prereg_harmonic.md` and `docs/prereg_discovery_v2.md`.
Commit hashes mentioned in docs refer to the private development history; this repository is a snapshot.

This document describes the whole repository as the code actually behaves, including the places where
docstrings, conventions or safeguards fall short. Every number in the results sections comes from the
JSON files in `docs/`.

---

## 0. What the system is

Two products share one calculation core:

1. **A research harness** that asks whether astrological timing techniques distinguish the date of a real life
   event from the same person's ordinary dates. It runs on ~75,000 dated events of famous people
   (Astro-Databank), using a case-crossover design, person-grouped cross-validation, and falsification tests.
2. **A consultation engine** that turns a birth chart plus a date into a structured state report and has a
   local language model talk through it, with safeguards enforced in code.

```
Astro-Databank (Parse DB) ─┐
                           ├─> preprocessing.py ─> case-control sets ─┬─> features.py (706 binary) ─> models.py / validation.py
typed birth data ──────────┘        (persons)                         ├─> rao.py (11 Rao parameters) ─> run_rao.py
                                                                      ├─> methods.py (23 methods)    ─> run_methods.py
                                                                      └─> bcp_chain.py               ─> bcp_chain_test.py
person + date ─> context_builder.state_report ─> consultation_agent (retrieve → Ollama → guards → log) ─> interactive_cli / blind_test
```

Dependencies (`requirements.txt`): numpy ≥ 2.0, scipy ≥ 1.13, lightgbm ≥ 4.5, pyswisseph ≥ 2.10, pytest ≥ 8,
plus `requests` for the Ollama HTTP call.

---

## 1. Core architecture and data pipeline

### 1.1 Source data

| Store | Table / file | Used for |
|---|---|---|
| `data/astro_master_data.db` (override: env `ASTRO_SOURCE_DB`; see `data/README.md`) | `ml_features`, rows with `event_label = 'born on'` | One birth record per person: sidereal natal longitudes `natal_<planet>_deg` for Sun…Rahu, `natal_asc_deg`, `birth_time_known`, `rodden_rating`, `birth_lat`, `birth_lon`, `birth_jd` |
| same | `ml_features`, all other rows | Dated events: `name, event_category, event_date, birth_jd, event_label` |
| same | `charts.raw_html` | Gender (regex `Gender\s*:\s*([MF])`) for Rao's P6, cached in `data/cache/gender.json` |
| typed in | — | `interactive_cli.person_from_birth` computes the natal positions itself |

The database is opened read-only (`file:...?mode=ro`). Archive natal positions are precomputed in the Parse
DB; for typed-in births the engine computes them (§1.4).

### 1.2 Parsing birth data (`preprocessing.py`)

Astro-Databank writes coordinates and zones in its own compact notation. These parsers are used by the
Parse ETL that fills the DB; `tests/test_parity.py` keeps them identical to the Abraxas originals.

- **`parse_coordinates(text)`** first tries the anchored form `40n42, 73w4859 Timezone`, i.e. degrees +
  hemisphere letter + up to 4 digits of `MMSS`, using `_dms(deg, tail)` = deg + MM/60 + SS/3600. Southern and
  western hemispheres become negative. If that fails, it searches for the lat and lon tokens separately and
  returns (0, 0) when nothing is found. *History:* an earlier parser read `73w4859` and `10e0` as 0.0, which
  gave 28% of people wrong birth times. That was fixed on 2026-09-30, the DB was repaired, and a backup was kept.
- **`parse_utc_offset(text)`** reads hours east of UT from `Timezone ... h4w` (standard zone, hours + minutes,
  e.g. `h5e30` = +5.5) or `m12e35` (local mean time, degrees + minutes of longitude, divided by 15).
  West is negative. It returns `None` when no zone is found.

### 1.3 Events → case-control sets

`case_control_sets(source, halves, categories)` is the single entry point for every batch test.

1. **Load people** (`load_people`): an array of natal longitudes in `NATAL` order
   `[Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ascendant]`. The Ascendant is set to NaN when
   `birth_time_known` is false.
2. **Load events** (`load_events`) with `EVENT_FILTER`, which removes scraped non-events: "born on",
   page-footer text, relationship links, "compare to chart of", roles played, "(born", "Update of", "(has as)".
3. **Recategorise** (`refine_category`):
   - The source's `Other` bucket is mapped by exact label through `NEW_EVENT_LABELS` into Prize, Job_Start,
     Job_End, Trial, Relationship_Begin and Relationship_End.
   - The source's `Death` is split: "sentenced to death" and "suicide attempt" are dropped, "non-fatal" becomes
     Accident, regex `death of …|(his|her) (father|…) died` becomes `Death_of_relative`, and everything else
     is the person's own `Death`.
4. **Per event filters:**
   - The person must have all 8 planetary longitudes.
   - The event must be at age 1–110 years, with `YEAR = 365.2422` days.
   - The event must not fall within 1.5 days of a birthday. Placeholder dates made up 7% of events against
     under 1% expected.
   - Duplicates on `(name, category, date)` are removed.
5. **Control dates:** the same calendar date offset by −3, −1, +1 and +3 years, using `round(k × 365.2422)` days.
   For own death the offsets are −4, −3, −2 and −1, because a person has no dates after death.
6. **Mask:** a control date is valid only if age ≥ 1, it is on or before the person's recorded death, and it is
   on or before `STUDY_CUTOFF = 2026-09-30`. A set is kept only if it has the case plus at least 2 valid
   controls. `complete` means all 4 controls are valid, which is used as the right-censoring check.
7. **Time of day:** every event and control date is converted with `jd_noon(d)`, giving the Julian Day at
   12:00 UT. Event times are unknown, so all transits are computed for noon UT. Birth moments are exact.
8. **Splits:** `half = crc32(name) & 1` and `fold = (crc32 >> 1) % 5`, which is a fixed, reproducible
   GroupKFold by person. **Half 1 is retired** for model fitting because it had been evaluated too often.
   Tests that fit nothing (Rao table, 23 methods, BCP chain) use both halves.

Each output set is a dict with keys `name, category, half, fold, jds[5], mask[5], complete, birth_jd, natal,
rating, death_jd, label, lat, lon`. Index 0 of `jds` is always the event.

### 1.4 Swiss Ephemeris chart generation

- **Configuration** (`features._swe`): `swe.set_sid_mode(SIDM_LAHIRI)`, flags `FLG_SIDEREAL | FLG_MOSEPH`.
  Moshier is the built-in analytic ephemeris, so no data files are needed. The node is `MEAN_NODE`, and Ketu is
  Rahu + 180°.
- **Typed-in natal chart** (`person_from_birth`):
  1. JD = `swe.julday(y, m, d, hour + min/60 − tz)`.
  2. Sidereal longitudes come from `calc_ut`.
  3. The Ascendant is `houses_ex(bjd, lat, lon, b"W", FLG_SIDEREAL)[1][0]`. `W` is whole-sign; the house
     system doesn't affect the Ascendant degree.
- **Houses** are whole-sign everywhere: house = `(sign(planet) − sign(Ascendant)) mod 12 + 1`. No method in
  the repository uses Placidus or any other quadrant cusps. The Midheaven degree, where used, is
  `houses_ex(...)[1][1]`.
- **Tropical positions** (`methods.Person`):
  - Each sidereal natal longitude plus `get_ayanamsa_ut(birth_jd)`.
  - Uranus, Neptune and Pluto are calculated tropically from Moshier directly.
  - The tropical Ascendant is the sidereal Ascendant plus the ayanamsa.
  - Transits for Western methods use `_tropical()` (Moshier, with speed).
- **Sect:** day chart if `(Sun_trop − Asc_trop) mod 360 > 180`, meaning the Sun is in the upper half of the
  ecliptic circle measured from the Ascendant.
- **Lots:**
  - Fortune = Asc + Moon − Sun by day, or Asc + Sun − Moon by night.
  - Spirit is the reverse.
- **Caches:**

  | Cache | Location | Scope |
  |---|---|---|
  | `features._sky` | JD → 6 sidereal transit longitudes | Process-wide |
  | `rao._sky9` | JD → transit signs + retrograde set | Process-wide |
  | Per-person annual charts | `ctx["sr"]`, `Person._sr`, `Person._tajika` | Per person |
  | Feature matrices | `.npz` in `data/cache`, keyed by a hash of set keys + featurizer + feature schema | On disk |

  `methods.evaluate` otherwise calls `calc_ut` directly for each date (no JD matrix).

### 1.5 The 706-feature vector (`features.py`)

This is the input to the LightGBM models, ported unchanged from the Abraxas research code. Parity is checked
by `test_identical_features`. One `person_context(s)` is computed once per person (positions, BAV tables,
Chara timeline, karakas). Then `features(ctx, jd)` returns a uint8 vector:

| Group | Count | Content |
|---|---|---|
| T | 216 | Transiting Mercury, Venus, Mars, Jupiter, Saturn, Rahu × natal 9 points × {conj, square, trine, opp}. Orbs: 2° for Mercury/Venus/Mars, 3° for Jupiter/Saturn/Rahu. The transiting Sun is excluded because it is identical on same-calendar-date controls; the Moon is excluded because event times are unknown. |
| D | 54 | Vimshottari MD lord (9), AD lord (9), houses the MD lord rules (12), houses the AD lord rules (12), AD lord's natal house (12) |
| G | 144 | Each transiting planet's house from the natal Moon (72) and from the Lagna (72) |
| A | 48 | Transiting planets in degree aspect to the natal MD and AD lords |
| L | 24 | The AD lord's own current transit house, from the Moon and from the Lagna |
| X | 12 | K.N. Rao double transit: houses that both Jupiter (occupies, 5th, 7th, 9th) and Saturn (occupies, 3rd, 7th, 10th) influence |
| S | 3 | Sade Sati (Saturn 12th/1st/2nd from the Moon); Saturn 4th from the Moon; Saturn 8th from the Moon |
| K | 6 | Saturn in a sign where its own BAV ≤ 3; Jupiter BAV ≥ 5; Jupiter or Saturn in a sign with SAV > 30 or < 25 |
| P | 33 | Pratyantardasha lord (9), its natal house (12), houses it rules (12) |
| V | 48 | Transiting Jupiter and Saturn counted from the D9 and D10 Lagnas |
| C | 30 | Chara MD sign's house (12), AD sign's house (12), whether the MD/AD sign holds or Jaimini-aspects AK, AmK or DK (6) |
| Y | 40 | Yogini MD (8) and AD (8), houses the MD lord rules (12), AD lord's natal house (12) |
| J | 48 | Tajika annual Lagna from natal Lagna; Muntha from the annual Lagna and from the natal Lagna; Muntha lord from the annual Lagna |

House-based features are zero when the birth time is unknown. `TECHNIQUES` maps group letters to technique
families (transits = TGALXSV, vimshottari = DP, ashtakavarga = K, chara = C, yogini = Y, tajika = J).

### 1.6 Core astrological algorithms (shared by every layer)

#### Vimshottari (`vimshottari_at`)

1. Nakshatra position `nak = moon / 13°20′`. The starting lord is `int(nak) mod 9` in
   `DASHA_LORDS = [Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury]`, with years
   `[7, 20, 6, 10, 7, 18, 16, 19, 17]`.
2. Elapsed time `t = frac(nak) × years[i] + (jd − birth)/365.25`. Mahadashas are walked forward until `t`
   falls inside one.
3. Antardashas run from the MD lord and last `MD_years × AD_years / 120`.
4. Pratyantars use the same rule one level down.
5. `context_builder.vimshottari_periods` repeats the walk with absolute JDs to give from/to dates.
   `test_vimshottari_periods_agree_with_features` checks that the two agree.

#### Yogini (`yogini_at`)

- Eight yoginis (Moon 1, Sun 2, Jupiter 3, Mars 4, Mercury 5, Saturn 6, Venus 7, Rahu 8 years) in a 36-year
  cycle.
- The start index is `(nakshatra + 1 + 3) mod 8`, with 0 mapped to the eighth yogini.
- Sub-periods last `MD × AD / 36`.

#### Jaimini Chara dasha

- **Timeline** (`chara_timeline`):
  - Signs run from the Lagna, forward if the 9th sign from the Lagna is savya (Aries, Taurus, Gemini, Libra,
    Scorpio, Sagittarius) and backward otherwise.
  - Years per sign (`chara_years`) count from the sign to its lord, forward for savya signs and backward
    otherwise, minus 1. Add 1 if the lord is exalted and subtract 1 if it is debilitated. The lord in its own
    sign gives 12. The result is clamped to 1–12.
  - Scorpio (Mars/Ketu) and Aquarius (Saturn/Rahu) take the stronger co-lord (`_chara_lord`):
    1. If one co-lord occupies the sign, the other is taken.
    2. Otherwise, the co-lord with more planets conjunct it.
    3. Otherwise, the co-lord with the higher degree.
  - The second cycle gives each sign `12 − first`.
- **Two antardasha conventions exist in the code:**
  - `features.chara_at`: forward from the sign after the MD sign, with the direction set by the MD sign. Used
    only by the 706 features.
  - `rao.chara_rao`: from the MD sign itself, backward. This is the book's usage and reproduces case 1's
    Sagittarius/Aries. Used by the Rao parameters, the V3 method and the state report.
- **Karakas** (`chara_karakas`): the seven planets ranked by degree within their sign, giving AK, AmK, BK, MK,
  PiK, GK and DK.
- **Jaimini sign aspects** (`jaimini_aspects`):
  - Movable signs aspect fixed signs except the adjacent one.
  - Fixed signs aspect movable signs except the adjacent one.
  - Dual signs aspect the other dual signs.

#### Ashtakavarga (`bav_tables`)

- The BPHS contribution tables are in `BAV`. For each of the 7 planets, each reference point (7 planets +
  Lagna) gives a bindu to the listed houses counted from itself.
- SAV is the sum across planets per sign.
- Totals are 48, 49, 39, 54, 56, 52 and 39, with SAV 337, checked by `test_bav_totals_match_bphs`. The same
  check caught wrong Mars and Saturn Lagna rows in the Parse copy, which has since been fixed.

#### Divisional charts

- **D9:** `int(lon / 3°20′) mod 12`.
- **D10:** odd signs count from the sign itself, even signs from the 9th sign, plus `int(degree / 3)`.

#### Tajika annual chart (`solar_return`, `annual_chart`)

1. The sidereal solar return is found by Newton-style iteration, `jd += Δλ / 0.9856`, starting at
   `birth + k × 365.2564` days, with at most 5 steps and a tolerance of 1e-5°.
2. The annual Lagna is the sidereal Ascendant at the return moment, for the birth place.
3. `k` is completed sidereal years, stepped back by 1 if this year's return is still ahead.
4. Muntha = natal Lagna sign + k.

---

## 2. Technique library mechanics (`methods.py`)

### 2.1 Contract

`evaluate(person, jd)` returns a dict per method. Most methods return a tuple `(houses: set[int], planets:
set[str])`, meaning what that technique "switches on" on that date. Four return flag dicts instead (N1, N2,
M1, M2). Nothing is returned for a person without a birth time (`has_lagna` false).

`flagged(result, method, category)` turns that into a yes/no for an event type, or `None` if the method doesn't
apply:

- **House/planet methods:** True if the activated houses include a target house, or the activated planets
  include the event's significator.
- **N1 tara:** for positive events (Marriage, Birth_Child, Career_Peak, Prize, Job_Start) True on taras 2, 4,
  6, 8 or 9; for all other events True on taras 3, 5 or 7. Tara 1 (Janma) is never a flag.
- **N2:** Jupiter on the birth-star trine for positive events; Saturn for the rest.
- **M1, M2:** only for Illness, Accident and own Death.

**Targets** (`TARGETS`, pre-registered):

| Event | Target houses | Significator |
|---|---|---|
| Marriage, Divorce, Death of mate | 7 | Venus |
| Birth of a child | 5 | Jupiter |
| Career peak, Prize, Job start | 10 | Sun |
| Arrest, Trial | 12, 6 | Saturn |
| Illness | 6 | Saturn |
| Accident | 8 | Mars |
| Death of father | 9 | Sun |
| Death of mother | 4 | Moon |
| Own death | 8 | Saturn |

Two helpers convert planets into houses:

- **`sid_houses(planets)`** (Vedic): the houses each planet rules **and** the house it occupies, from the
  sidereal Lagna.
- **`trop_rules(planets)`** (Western, Hellenistic, Medieval): only the houses the planets rule, from the
  tropical Lagna.

### 2.2 The 23 methods, exactly as coded

Ages: `age = int((jd − birth)/365.2425)` (completed years) unless noted.

**Vedic (sidereal, Lahiri)**

| ID | Calculation | Houses switched on | Planets |
|---|---|---|---|
| V1 Vimshottari | MD and AD lords from `vimshottari_at` | `sid_houses([MD, AD])` | {MD, AD} |
| V2 BCP chain | The precomputed BFS from `active_house(age) = ((max(1, age) − 1) mod 12) + 1` (§2.3) | Houses at step ≤ 2 | Planets at step ≤ 2 |
| V3 Chara | AD sign from `rao.chara_rao` | The AD sign's house, plus every house the AD sign Jaimini-aspects | Natal planets in the AD sign |
| V4 Tajika Muntha | `k = int(age in sidereal years, 365.2564)`, Muntha = Lagna + k | Muntha's house | Muntha's sign lord |
| V5 Double transit | Jupiter's set {occupied, 5th, 7th, 9th} ∩ Saturn's set {occupied, 3rd, 7th, 10th}, sign-based | Houses in the intersection | Natal planets in those signs |
| V6 Jupiter transit | Jupiter's set alone | Its houses | Natal planets in those signs |

**Tajika**

| ID | Calculation | Houses | Planets |
|---|---|---|---|
| TJ2 Annual Lagna | Sidereal return Ascendant (needs birth lat/lon) | Its house from the natal Lagna | Its sign lord |
| TJ3 Mudda dasha | Start index = (birth-star number + completed years − 2) mod 9, counted from Ketu; Vimshottari order, each lord's share of the year = its Vimshottari years / 120; lord at the elapsed fraction since this year's return | `sid_houses([lord])` | {lord} |

**Nakshatra**

| ID | Calculation | Output |
|---|---|---|
| N1 Tara | `(nak(transit Moon) − nak(birth Moon)) mod 27 mod 9 + 1`: 1 Janma, 2 Sampat, 3 Vipat, 4 Kshema, 5 Pratyari, 6 Sadhaka, 7 Vadha, 8 Mitra, 9 Param Mitra | Flag by event polarity (above) |
| N2 Janma transit | Is transiting Saturn or Jupiter in the birth star or its trines (+9, +18 stars)? | Flag: Jupiter for positive events, Saturn for others |
| N3 Star lord | Lord of the nakshatra the natal AD planet occupies | `sid_houses([lord])`, {lord} |

**Western (tropical)**

Natal points are the 7 planets, the Ascendant and the MC (when birth lat/lon are known). Hits are converted
with `trop_rules`, plus house 1 for an Ascendant hit and house 10 for an MC hit. All orbs are 1°.

| ID | Calculation |
|---|---|
| W1 Secondary progressions | Progressed JD = birth + (jd − birth)/365.2422 (a day for a year). Progressed Sun or Moon conj/sq/tri/opp a natal point. |
| W2 Solar arc | arc = progressed Sun − natal Sun. Every natal point + arc in hard aspect (0/90/180) to a *different* natal point. |
| W3 Solar return | Tropical return for completed tropical years, Ascendant from `houses_ex` at the birth place. Switches on the natal house of the return Ascendant and that sign's ruler. |
| W4 Outer transits | Transiting Jupiter, Saturn, Uranus, Neptune or Pluto conj/sq/tri/opp a natal point. |

**Hellenistic (tropical)**

| ID | Calculation | Houses | Planets |
|---|---|---|---|
| H1 Profection | Profected sign = tropical Lagna + age | The profected house, plus houses ruled by the Lord of the Year | {LOY} |
| H2 Zodiacal releasing, Spirit | `zr_l2` from the Lot of Spirit's sign | The L2 sign's house | L2 sign ruler |
| H3 Zodiacal releasing, Fortune | Same, from the Lot of Fortune | The L2 sign's house | L2 sign ruler |

How `zr_l2` works:

- **L1 periods** last the sign's minor years `[15, 8, 20, 25, 19, 20, 8, 15, 12, 27, 30, 12]` (Aries…Pisces).
  Years are 365.25 days; Valens used 360.
- **L2 periods** last 1/12 of the L2 sign's own years, moving forward through the signs from the L1 sign.
- **Loosening of the bond:** after 12 L2 steps the sequence jumps to the sign opposite L1.

**Medieval (tropical)**

| ID | Calculation | Houses | Planets |
|---|---|---|---|
| MD1 Firdaria | 75-year cycle. Day order: Sun 10, Venus 8, Mercury 13, Moon 9, Saturn 11, Jupiter 12, Mars 7, Rahu 3, Ketu 2. Night order starts at the Moon. Each planetary period splits into 7 equal sub-periods in Chaldean order, starting from the period ruler; the nodes have no sub-periods. | `trop_rules([ruler, sub])` | {ruler, sub} |
| MD2 Distribution | Ascendant directed at 0.98565° per year; the lord of the Egyptian bound it has reached | `trop_rules([bound lord])` | {bound lord} |
| MD3 LOY transit | Where the profection Lord of the Year is transiting now | Its tropical house | (none) |

**Medical** (only for Illness, Accident and own Death)

| ID | Calculation |
|---|---|
| M1 Medical transits | Transiting Saturn or Mars within 1.5° of a conj/sq/opp to the tropical Ascendant ruler, Sun or Moon |
| M2 Vedic medical | Death: MD or AD lord rules the 2nd or 7th (maraka). Illness: rules the 6th or 8th. Accident: rules the 8th, or the MD/AD lord occupies the 8th. |

### 2.3 The author's BCP chain method (`bcp_chain.py`)

- **`Chart(lagna, signs)`** builds a breadth-first search from each of the 12 possible active houses when it
  is created.
  - A house node links to its lord and to the planets in it.
  - A planet node links to the house it sits in and to the houses it rules.
  - Each node's step count is the shortest path from the active house.
- **Score:** the closest target house earns a weight from `WEIGHT = {0: 3, 1: 2, 2: 2, 3: 1, 4: 1}`. That is
  3 for MAIN, 2 for SECONDARY, 1 for FAINT and 0 for background.
- **Cycle ruler:** `CYCLE_RULERS = [Moon, Mercury, Venus, Sun, Mars, Jupiter, Saturn]` by 12-year cycle
  (ages 1–12 Moon … 73–84 Saturn).
- **`story(active, age)`** writes the narrative by template from `houses.json` and `planets.json`, with no
  language model. It covers:
  - the main house
  - its lord and where the lord sits
  - other houses the lord rules
  - occupants of the main house
  - planets conjunct the lord
  - the cycle ruler
- **Conventions:**
  - **Completed age** (default) is `((age − 1) mod 12) + 1`, matching Alif's `bhriguChakra.ts`.
  - **Running year** (`--running-year`) is `(age mod 12) + 1`.

### 2.4 K.N. Rao marriage parameters (`rao.py`)

Rao's eight parameters (P1–P8) and three observations (O1–O3) are coded as binary features.

**Benchmarks.** They are checked against the book's case studies: Bill Clinton, and Hillary Clinton using the
book's 20:00 birth time. Four tests cover the derived values and the parameters.

**Operational choices.** Where the book is ambiguous, the code makes these choices:

- **PAC** means position, aspect or conjunction, using Parashari sign aspects. Every planet aspects the 7th;
  Mars also the 4th and 8th, Jupiter and the nodes the 5th and 9th, Saturn the 3rd and 10th.
- **Arudha padas** skip the "same or 7th → 10th" exception.
- **Retrograde rule:** a retrograde transiting Jupiter or Saturn also acts from the previous sign.
- **P7** fires on "the Sun, or at least 6 of the 9 grahas, in houses 12/1/2 or 6/7/8".
- **P6** needs the person's gender: Venus for men, Mars for women.

| Code | Rule |
|---|---|
| P1 | MD and AD lords connected to the marriage-givers (PAC set in D1 ∪ D9, Venus, or disposited by them) |
| P2 | Chara AD sign on the 1–7 axis with, or Jaimini-aspecting, DK, DK in D9, DP, UP, the 7L in D1 or the 7L in D9 |
| P3 | Transiting Jupiter PAC on Vivah Saham (sign of LL longitude + 7L longitude) |
| P4 | Saturn **and** Jupiter both PAC on any of Lagna, 7H, LL, 7L or VS |
| P5 | Transiting LL and 7L in mutual PAC |
| P6 | Transiting Jupiter PAC on natal Venus (male) or Mars (female) |
| P7 | Planet cluster around the 1/7 axis |
| P8 | LL transiting houses 6/7/8, or 7L transiting 12/1/2 |
| O1 | Transiting Moon PAC on Lagna or 7H, or in the sign of LL or 7L |
| O2 | Saturn Jaimini-aspecting the DK, or on the 1–7 axis with it |
| O3 | MD, AD or PD lord in the D9 5–11 axis set |

---

## 3. State and consultation layer

### 3.1 `context_builder.state_report(person, jd)`

The state report is plain JSON with no interpretation. Input: natal array, `birth_jd`, optional
`lat`/`lon`/`gender`/`name`. Age = (jd − birth)/365.2425, and `years = int(age)`.

| Key | Content | Notes |
|---|---|---|
| `natal` | Lagna, Moon sign, Moon nakshatra; per planet: sign, degree in sign, house | Sidereal |
| `vimshottari` | maha / antar / pratyantar: lord, from, to | 365.25-day years |
| `yogini` | maha, antar | |
| `sade_sati` | active, phase (rising, peak, setting), Saturn's house from the Moon | |
| `bhrigu_chakra` | active house, sign, lord, occupants, `aspected_by` (Parashari sign aspects), `trigger_dates` | Needs a birth time |
| `profection` | sign, house, Lord of the Year, its natal house, its current transit sign | **Sidereal** Lagna; H1 in methods is tropical |
| `chara` | maha sign, antar sign (Rao convention), DK, AK | |
| `tajika` | annual Lagna, Muntha sign, Muntha house | Needs lat/lon |
| `ashtakavarga` | For Jupiter and Saturn: transit sign, own bindus there, SAV there | |
| `exact_transits` | Mars (1°), Jupiter, Saturn, Rahu, Ketu (1.5°) to natal planets, Ascendant and MC; conj, sextile, square, trine, opposition; orb; applying or separating | Applying is judged by stepping one day of speed; sorted by orb |

**BCP trigger dates** = last birthday + (planet degree within its sign × 365.25/30) days. They are given for
the lord, the occupants and the aspecting planets.

### 3.2 Knowledge base (`src/knowledge_base/`)

| File | Content |
|---|---|
| `planets.json` | Per planet: significations, including the `dasha_theme` used by BCP stories |
| `houses.json` | One signification line per house |
| `rules.jsonl` | 12 rules, each `{id, technique, tags, text}`: vim-1, vim-2, chara-1, yogini-1, bcp-1, bcp-2, prof-1, tajika-1, transit-1, transit-2, transit-3, av-1 |
| `evidence.md` | What the tests found, injected verbatim into every prompt |

### 3.3 `consultation_agent.py`

**Backend.** `OllamaBackend(model="qwen3:8b")` POSTs to `localhost:11434/api/chat` with:
- `format = SCHEMA`, a JSON-schema-constrained structured output
- `temperature 0.4`, `num_ctx 8192`, timeout 600 s

Any object with `.chat(system, user, schema)` can stand in; the tests use a fake.

**Output schema:** `summary`; `themes[{theme, basis, cites[]}]`;
`windows[{from, to, claim, basis, source ∈ {chart, user}, confidence}]`; `questions[]`.

**Retrieval** (`retrieve(state, kb, question, k=8)`):

1. **Active planets:** the Vimshottari lords, the BCP lord and occupants, the Lord of the Year, and the planets
   in exact transits.
2. **Active houses:** the BCP house, the profection house, and the LOY's natal house.
3. **Techniques present:** always vimshottari, yogini and transit, plus bcp, profection, tajika, chara and
   ashtakavarga when their keys are in the state.
4. **Rule ranking:** rules for those techniques are ranked by how many words they share with the user's
   messages and the active planet names. The top 8 are kept.
5. **Significations:** those of the active planets and houses are added.

**Prompt** (`Consultation.turn`), in this order:
1. The full state JSON
2. The retrieved rules as `[id] text`
3. Planet significations
4. House significations
5. `evidence.md`
6. Everything the user has said so far

The system prompt (`SYSTEM`) requires facts only from the state report, citations, themes as possibilities
rather than predictions, windows only on report dates, confidence ≤ 0.3, `source = "user"` when a window was
narrowed by the user, and reflective questions without fishing.

**Code-level guards, applied after every model reply:**

| Guard | Exact behaviour |
|---|---|
| Allowed dates | `allowed_dates(state)` = the six Vimshottari from/to dates plus the BCP trigger dates. A window is kept only if both `from` and `to` are in that set and `from ≤ to`. Otherwise it moves to `dropped_windows`, and the reader is told how many were removed. |
| Confidence cap | `confidence = min(confidence, 0.3)` on every kept window |
| Source check | If the user hasn't said anything yet, every kept window is forced to `source = "chart"` |
| Citation filter | Every theme's `cites` list is reduced to ids that exist in `rules.jsonl` |
| Prediction log | Kept windows are appended to `data/consultations/predictions.jsonl` with consultation id, person, timestamp, state date and `outcome: null` |

**Limits of the guards:**

- Only **windows** are checked. Theme and summary text is free prose and is not fact-checked against the
  state report.
- A theme whose citations are all invalid is kept, with an empty list.
- After the user has spoken, `source = "user"` versus `"chart"` is whatever the model says.
- The module docstring says profection-year dates are allowed. The code doesn't include them, or the Chara
  and Tajika boundaries.
- There is no scorer yet that fills in `outcome` in the prediction log.

**`render()`** prints the summary, then themes with their citations, then "Test windows" with a standing
caveat and a `(narrowed from what you said)` marker, then the count of removed windows, then the questions.

### 3.4 Entry points

- **`python -m src.interactive_cli --name "Clinton, Hillary" --date 1975-10-11`**, or
  `--birth "YYYY-MM-DD HH:MM" --tz <hours east> --lat --lon [--gender M|F] [--model]`.
  - It prints the state JSON, then the first consultation, then loops on input.
  - `state` reprints the facts, and `quit` ends the session.
  - The date is evaluated at noon UT.
- **`scripts/blind_test.py`** (§4.5).

---

## 4. Empirical testing and validation harness

### 4.1 Design principles

- **Case-crossover:** each person is their own control. The event date is compared with the same person's
  same calendar date in other years. Natal chart, birth quality and fame are held constant. The same calendar
  date also cancels the transiting Sun and season.
- **Pre-registration:** the hypothesis, targets, analyses and expected results are written down and committed
  *before* each run.

  | Pre-registration | Commit |
  |---|---|
  | `prereg_new_events.md` | — |
  | `prereg_rao.md` | 81c426f |
  | `prereg_bcp_chain.md` | a6ff4a8, plus running-year addendum 252fc35 |
  | `prereg_methods.md` | 469eb54, plus medieval/Tajika/nakshatra addendum b213685 |

  Each results JSON records the pre-registration it answers.
- **Person-grouped cross-validation:** a set is only ever scored by a model that never saw that person.
- **Falsification tests are mandatory** (§4.2). A result counts only if they pass.
- **Multiple comparisons:** a method × event cell counts only if its confidence interval excludes 1 **and**
  it replicates in both data halves.

### 4.2 Machine-learning pipeline (`models.py`, `validation.py`, `scripts/run_pipeline.py`)

**Model.** LightGBM LambdaRank, where each case-control set is one ranking query and the event date is labelled
1. Parameters:
- `learning_rate 0.03`, `max_depth 4`, `num_leaves 15`, `min_child_samples 150`
- `feature_fraction 0.5`, `bagging 0.8 every round`, `lambda_l2 5`, `seed 7`, 300 rounds
- metric NDCG@1

**Columns.** `AGE_CLOCK_COLUMNS` (the 12 "Muntha in house h from natal Lagna" columns, which are exactly
age mod 12) are dropped by default. Dasha features stay in because they are the technique under test, which is
why the placebo window test is mandatory.

**Metric.** C-index = P(event date outscores a same-person control), with ties counting half and a
500-resample bootstrap 95% CI.

| Test | What it does | Pass condition |
|---|---|---|
| `placebo_c_index` | The control 1 year before the event becomes the fake "event" and is compared with the remaining controls; the real event is removed | ≈ 0.50 |
| `window_test` | A 5-year stretch containing the event is split into 20 quarters; each quarter is scored as the mean of 3 dates (1/6, 1/2 and 5/6 through it), with random tie-breaking because period features are constant for months. The stretch starts at a random offset; for own death it ends at the death. | top-1 vs 5%, top-3 vs 15% |
| `placebo_window_test` | The same stretches shifted 2 years earlier, with the target quarter kept in the same position | **Required.** Fails if the lower CI bound of the hit rate is above chance. This caught the own-death "breakthrough" (11.8% top window) on 2026-09-30, which was the dasha sequence identifying the latest period of life. |
| `mismatched_chart_c` | All features recomputed from a random other person's natal positions, keeping the person's own birth moment, so age and the dasha clock are unchanged; 3 permutations | ≈ 0.50 (verdict fails above 0.52) |
| `subgroup_c` | Rodden AA vs A, and complete-control sets only | Consistent with the whole |
| `lockbox_save` / `lockbox_verify` | The final model is frozen with a SHA-256 of its file, its parameters, the feature-schema hash, the code commit and the rule "evaluate only on events after 2026-09-30; do not retrain" | Checksum and schema unchanged |

**Verdict order in `run_pipeline`:**
1. Fails the placebo window test, then
2. fails the mismatched-chart test, then
3. window signal above chance, then
4. no window signal.

Event types with fewer than 150 sets are skipped.

### 4.3 Rao evaluation (`scripts/run_rao.py`)

- **Part 1, the book's table with controls.** For each parameter, how often it holds on the wedding date
  versus the same person's control dates. The comparison uses a Mantel-Haenszel matched odds ratio with a
  Robins-Breslow-Greenland 95% CI (`matched_or`).
- **Part 2, three LambdaRank variants:** Rao-only (11 features), full (706 minus the age clock), and full
  plus Rao. Each runs the full falsification suite.

### 4.4 Multi-method evaluation (`scripts/run_methods.py`)

1. **Data.** Both halves, known birth times, event types in `TARGETS`. Own death is randomly sampled down to
   5,000 events (seed 3).
2. **Evaluation.** Every method is run on every valid date of every set.
3. **Per method × event type:** event-date flag rate, control flag rate, matched odds ratio and CI, and
   whether it replicates in both halves (CI excludes 1 in each half, in the same direction).
4. **Agreement:** the phi correlation between every pair of methods on control dates, pooled across event
   types. This measures overlap built into the methods themselves, not shared truth.
5. **Consensus:** k = the number of applicable methods flagging a date. C = P(event k > control k), with ties
   counting half. There is also a placebo version, where the control 1 year before the event plays the event.

### 4.5 BCP chain and personal blind tests

- **`bcp_chain_test.py`**: for each event, P(the event year's chain score > a control year's score), plus
  how often the target house is the MAIN story in event years versus control years. Relatives' deaths are
  mapped to the 9th (father), 4th (mother), 7th (mate), 5th (child) or 3rd (sibling) house.
- **`bcp_chain_personal.py`**:
  - Covers ages 18–44 of one chart, given on the command line.
  - About half the ages, chosen with `SystemRandom`, show the real chain story. The rest show a decoy active
    house whose lord differs from the real one.
  - The person scores each 0–3. The key is saved and not printed.
- **`blind_test.py`**:
  - The person names a period without saying what happened. The engine writes a reading at the middle of that period
    and at the same date in each decoy year.
  - Readings are shuffled with `SystemRandom` and labelled A–D.
  - `scrub()` removes ISO dates, years, decades and ages before the readings are shown.
  - The key and the raw outputs are saved to `data/consultations/blind_key_*.json`. Chance = 1 in the number
    of periods.

### 4.6 Automated tests (`python -m pytest tests`, 29 tests)

| File | What it guards |
|---|---|
| `test_parity.py` | Same sets selected and identical features as the Abraxas research code |
| `test_rules.py` | BAV totals, Jaimini aspects, Chara years, D9/D10, Vimshottari and Yogini starts, feature layout |
| `test_rao.py` | Clinton case studies: derived values and parameters |
| `test_models_validation.py` | A planted signal is learned out-of-fold; pure noise gives chance; the placebo catches a time-drift artifact and passes a genuine signal; the age clock is excluded; the lock-box detects tampering; new event types load |
| `test_consultation.py` | State report facts; Vimshottari dates agree with the features; invented dates are dropped, confidence capped and windows logged; user notes reach the model; the source can't be "user" before the user speaks |
| `test_methods.py` | Zodiacal releasing periods, firdaria order, bounds/tara/mudda, all 23 methods present and sane on a real chart |

### 4.7 Results to date

**Earlier 706-feature models** (Abraxas, summarised in `evidence.md`): first reported as within-person C ≈ 0.53–0.55
for marriage, death of a relative and arrest. **Withdrawn 2026-10-04:** those folds were grouped by person only, which
leaks shared event dates (13–41% of events share an exact date with someone else's). With folds grouped by person and
event month the same model gives 0.472–0.510 across 11 types, equal to the wrong-chart control (0.487–0.523). Window prediction was near chance: top-1 about 5–7% (chance 5%),
top-3 15–20% (chance 15%).

**New event types** (`results_20260930_1733.json`, training half; person-grouped folds, so subject to the leak above):

| Event | Sets | C [95% CI] | Placebo C | Window top-1 / top-3 | Placebo window passed | Mismatched C | Verdict |
|---|---|---|---|---|---|---|---|
| Prize | 724 | 0.531 [0.504, 0.558] | 0.492 | 6.9% / 16.3% | yes | 0.504 | no window signal |
| Job start | 541 | 0.513 [0.483, 0.541] | 0.504 | 8.6% / 18.6% | yes | 0.501 | window above chance (C itself not significant; not replicated) |
| Job end | 320 | 0.518 [0.482, 0.554] | 0.503 | 4.4% / 12.0% | yes | 0.523 | fails mismatched-chart test |
| Trial | 293 | 0.545 [0.503, 0.585] | 0.490 | 7.0% / 17.7% | yes | 0.490 | no window signal |
| Relationship begin / end | 110 / 59 | — | — | — | — | — | too few events |

**K.N. Rao** (`results_rao_20260930_1801.json`, 3,663 marriages, 3,657 with known gender):

| Parameter | On wedding dates | On control dates | Matched OR [95% CI] |
|---|---|---|---|
| P1 Vimshottari connection | 99.6% | 99.6% | 0.77 [0.29, 2.07] |
| P2 Chara connection | 93.8% | 94.1% | 0.96 [0.81, 1.13] |
| P3 Jupiter on Vivah Saham | 43.7% | 44.0% | 0.99 [0.92, 1.06] |
| P4 Double transit | 81.4% | 81.8% | 0.96 [0.87, 1.07] |
| P5 Piya Milan | 30.9% | 31.6% | 0.97 [0.90, 1.05] |
| P6 Karaka activation | 44.3% | 43.2% | 1.04 [0.97, 1.12] |
| P7 Planet cluster | 55.4% | 56.2% | 0.91 [0.76, 1.08] |
| P8 Lord swap | 44.0% | 45.6% | 0.92 [0.85, 1.01] |
| O1 Moon trigger | 30.7% | 30.2% | 1.02 [0.95, 1.10] |
| O2 Saturn on DK | 50.9% | 51.4% | 0.97 [0.89, 1.05] |
| O3 D9 5–11 axis | 97.7% | 97.3% | 1.24 [0.95, 1.61] |
| **Six or more of P1–P8** | **34.3%** | **34.3%** | **1.00 [0.92, 1.09]** |

The models gave C = 0.500 for Rao-only, 0.514 for full and 0.512 for full plus Rao. All passed the placebo
window test, and windows were at chance (top-3 14.5–15.5%).

**BCP chain** (both halves). P(event year scores closer than a control year):

- **Completed age:**
  - Marriage 0.501 (n = 7,349)
  - Prize 0.505
  - Arrest 0.498
  - Career peak 0.517 [0.502, 0.534]
  - Illness 0.520 [0.493, 0.546]
  - Relationship end 0.559 [0.502, 0.618] (n = 110)
  - Every other type between 0.47 and 0.51
- **Running year:**
  - Marriage 0.499
  - Prize 0.498
  - Arrest 0.487
  - Job start 0.515 [0.499, 0.530]

With 18 event types tested per convention, one or two intervals just clearing 0.5 is what chance produces.

**23 methods** (`results_methods_20261001_1005.json`):

- **Per cell:** 15 of 300 method × event cells had a CI excluding 1, against about 15 expected by chance at
  5%. **None replicated in both halves.** Examples:
  - Divorce: V2 BCP chain OR 1.27 and V3 Chara OR 1.19.
  - Job start: H2 zodiacal releasing OR 1.32.
  - Death: V2 BCP chain OR 0.92, i.e. *less* often flagged on death dates.
- **Consensus:** 0.49–0.52 for every event type. The mean number of methods flagging was essentially equal on
  event and control dates (marriage 6.25 vs 6.22; death 6.65 vs 6.71). Divorce reached 0.529 [0.502, 0.553],
  1 of 14 types, and is driven by the two unreplicated cells above.
- **Built-in agreement on control dates:**

  | Method pair | Phi |
  |---|---|
  | V5 double transit ↔ V6 Jupiter transit | 0.46 |
  | V4 Tajika Muntha ↔ H1 profection | 0.46 (both advance one sign a year) |
  | W1 progressions ↔ W2 solar arc | 0.18 |
  | H2 ↔ H3 zodiacal releasing | 0.13 |
  | All other pairs | ≈ 0.1 or below |

**Personal blind tests** (one volunteer chart with a verified birth time): 1 hit in 4 blind period tests, which is chance level.

**Overall (corrected 2026-10-04):** no chart-specific signal once folds are grouped by date as well as person (the
earlier 0.53–0.55 was shared-date leakage), and no ability to pick the right window. No single classical rule, no rule set (Rao) and no consensus of 23 methods beat the same
person's ordinary dates.

---

## 5. Known gaps and inconsistencies (unfiltered)

1. **Stale docstring in `methods.py`:** it says "fourteen" techniques and labels H3 as firdaria. The code has
   23 methods, with H3 as zodiacal releasing from Fortune and firdaria as MD1.
2. **Two Chara antardasha conventions:** forward from the next sign in `features.chara_at`, backward from the
   MD sign in `rao.chara_rao`. The 706-feature models use the first; Rao, V3 and the state report use the
   second.
3. **Profection zodiac differs:** the state report profects the sidereal Lagna, while H1 and MD3 profect the
   tropical Lagna. The two can disagree on the sign for the same date.
4. **Consultation guards cover dated windows only.** Themes and summary are not fact-checked, and
   `allowed_dates` omits the profection, Tajika and Chara boundaries despite the module docstring.
5. **No outcome scorer:** `predictions.jsonl` collects windows with `outcome: null`, and nothing scores them
   yet.
6. **Noon UT for events:** methods that depend on the Moon (N1 tara, Rao O1) can be off by a whole tara or sign
   because the Moon moves about 13° a day.
7. **One target convention:** each event type has one house set and one significator. Other traditional
   mappings (2nd/11th for marriage, 7th from the 7th, D9 for marriage) are not tested in `methods.py`.
8. **Birth-time dependence:** every house-based method needs a known birth time, so people without one are
   excluded. Rodden AA and A are pooled except in `subgroup_c`.
9. **No ephemeris precompute:** `methods.evaluate` calls the Swiss Ephemeris live for each date, apart from the
   per-person return caches. A full 23-method run takes tens of minutes, which is slow but works.
10. **Parity tests need the Abraxas checkout** (`tests/test_parity.py`). They are skipped or fail on a machine
    without it.
11. **Ambiguous hemisphere tokens** in Astro-Databank text fall back to (0, 0) silently in
    `parse_coordinates`. The Parse DB has been repaired, but any new import should check for zero
    coordinates.

---

## 6. File map

| Path | Lines | Role |
|---|---|---|
| `src/preprocessing.py` | 217 | Parsers, event cleaning, case-control sets, splits |
| `src/features.py` | 442 | Ephemeris setup, dasha/Chara/Yogini/Tajika/BAV/divisional algorithms, 706 features |
| `src/methods.py` | 345 | `Person` (sidereal + tropical), 23 methods, `evaluate`, `flagged`, targets |
| `src/bcp_chain.py` | 102 | BCP chain BFS, scoring, cycle rulers, template stories |
| `src/rao.py` | 224 | K.N. Rao P1–P8, O1–O3, PAC, padas, Rao Chara convention |
| `src/models.py` | 138 | Feature matrices and cache, LambdaRank, C-index, bootstrap, grouped CV |
| `src/validation.py` | 174 | Placebo C, window and placebo window tests, mismatched charts, subgroups, lock-box |
| `src/context_builder.py` | 163 | State report |
| `src/consultation_agent.py` | 168 | Schema, prompt, retrieval, Ollama backend, guards, log, render |
| `src/interactive_cli.py` | 76 | Person loaders and the chat loop |
| `src/knowledge_base/` | — | planets.json, houses.json, rules.jsonl (12 rules), evidence.md |
| `scripts/run_pipeline.py` | 82 | ML pipeline per event type, verdicts, lock-box |
| `scripts/run_rao.py` | 146 | Rao book table with controls, three model variants |
| `scripts/run_methods.py` | 132 | 23-method per-cell, agreement and consensus analysis |
| `scripts/bcp_chain_test.py` | 75 | BCP chain on Astro-Databank, both conventions |
| `scripts/bcp_chain_personal.py` | 39 | Blind real/decoy BCP stories for one chart |
| `scripts/blind_test.py` | 81 | Blind target/decoy consultation readings |
| `tests/` | 390 | 29 tests (§4.6) |
| `docs/prereg_*.md` | — | Four pre-registrations, each committed before its run |
| `docs/results_*.json` | — | Raw outputs of every run cited above |
