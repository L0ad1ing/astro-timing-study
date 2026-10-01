"""
src/features.py — binary features for one person on one date (706 per date).

Ported unchanged from the Abraxas research code (cognition/team/event_model.py, event_model_v2.py,
event_model_v3.py, techniques.py); tests/test_parity.py checks the output is identical.
Sidereal zodiac, Lahiri ayanamsa, Swiss Ephemeris (Moshier). Sign indexes: 0 = Aries.

Groups (GROUPS gives the column slices):
  T  degree aspects (conj/square/trine/opp; orbs 2 deg Mercury-Venus-Mars, 3 deg Jupiter-Saturn-Rahu)
     from transiting Mercury..Rahu to natal Sun..Rahu, Ascendant. No transiting Sun (identical on
     same-calendar-date controls) or Moon (event times unknown).
  D  Vimshottari mahadasha/antardasha: lords, houses they rule, AD lord's natal house (365.25-day years)
  G  gochara: each transiting planet's house from the natal Moon and from the Lagna
  A  transiting planets in degree aspect to the natal MD and AD lords
  L  the AD lord's own transit: house from natal Moon and from Lagna
  X  K.N. Rao double transit: houses Jupiter (occupies/aspects 5-7-9) and Saturn (3-7-10) both influence
  S  Sade Sati (Saturn 12/1/2 from Moon); Saturn 4th and 8th from Moon
  K  Ashtakavarga: Saturn in a sign with its BAV <= 3; Jupiter BAV >= 5; Jupiter/Saturn in SAV > 30 / < 25
  P  pratyantardasha: lord, its natal house, houses it rules
  V  transiting Jupiter and Saturn from the D9 and D10 Lagnas
  C  Jaimini Chara dasha (K.N. Rao): MD/AD sign houses from Lagna; MD/AD sign holds or aspects AK/AmK/DK
  Y  Yogini dasha: MD/AD yogini, MD lord's houses ruled, AD lord's natal house
  J  Tajika annual chart: annual Lagna from natal Lagna, Muntha from annual and natal Lagna, Muntha lord
House-based features need a known birth time (Ascendant); otherwise they are zero.
"""
from __future__ import annotations

import math

import numpy as np

from src.preprocessing import NATAL

# ── Constants ────────────────────────────────────────────────────────────────
TRANSITING = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu"]
ASPECTS = {"conjunct": 0, "square": 90, "trine": 120, "opposite": 180}
ORB = {"Mercury": 2.0, "Venus": 2.0, "Mars": 2.0, "Jupiter": 3.0, "Saturn": 3.0, "Rahu": 3.0}
SIGN_LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
             "Saturn", "Jupiter"]
DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
SEVEN = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
PLANETS9 = SEVEN + ["Rahu", "Ketu"]
SAVYA = {0, 1, 2, 6, 7, 8}
EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6, "Rahu": 2, "Ketu": 8}
DEBIL = {p: (s + 6) % 12 for p, s in EXALT.items()}
YOGINI_LORDS = ["Moon", "Sun", "Jupiter", "Mars", "Mercury", "Saturn", "Venus", "Rahu"]
YOGINI_YEARS = [1, 2, 3, 4, 5, 6, 7, 8]

# Bhinnashtakavarga (BPHS); totals 48/49/39/54/56/52/39, SAV 337.
BAV = {
    "Sun": {"Sun": [1, 2, 4, 7, 8, 9, 10, 11], "Moon": [3, 6, 10, 11], "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [3, 5, 6, 9, 10, 11, 12], "Jupiter": [5, 6, 9, 11], "Venus": [6, 7, 12],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Lagna": [3, 4, 6, 10, 11, 12]},
    "Moon": {"Sun": [3, 6, 7, 8, 10, 11], "Moon": [1, 3, 6, 7, 10, 11], "Mars": [2, 3, 5, 6, 9, 10, 11],
             "Mercury": [1, 3, 4, 5, 7, 8, 10, 11], "Jupiter": [1, 4, 7, 8, 10, 11, 12],
             "Venus": [3, 4, 5, 7, 9, 10, 11], "Saturn": [3, 5, 6, 11], "Lagna": [3, 6, 10, 11]},
    "Mars": {"Sun": [3, 5, 6, 10, 11], "Moon": [3, 6, 11], "Mars": [1, 2, 4, 7, 8, 10, 11],
             "Mercury": [3, 5, 6, 11], "Jupiter": [6, 10, 11, 12], "Venus": [6, 8, 11, 12],
             "Saturn": [1, 4, 7, 8, 9, 10, 11], "Lagna": [1, 3, 6, 10, 11]},
    "Mercury": {"Sun": [5, 6, 9, 11, 12], "Moon": [2, 4, 6, 8, 10, 11], "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
                "Mercury": [1, 3, 5, 6, 9, 10, 11, 12], "Jupiter": [6, 8, 11, 12],
                "Venus": [1, 2, 3, 4, 5, 8, 9, 11], "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
                "Lagna": [1, 2, 4, 6, 8, 10, 11]},
    "Jupiter": {"Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11], "Moon": [2, 5, 7, 9, 11], "Mars": [1, 2, 4, 7, 8, 10, 11],
                "Mercury": [1, 2, 4, 5, 6, 9, 10, 11], "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
                "Venus": [2, 5, 6, 9, 10, 11], "Saturn": [3, 5, 6, 12], "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11]},
    "Venus": {"Sun": [8, 11, 12], "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12], "Mars": [3, 5, 6, 9, 11, 12],
              "Mercury": [3, 5, 6, 9, 11], "Jupiter": [5, 8, 9, 10, 11], "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
              "Saturn": [3, 4, 5, 8, 9, 10, 11], "Lagna": [1, 2, 3, 4, 5, 8, 9, 11]},
    "Saturn": {"Sun": [1, 2, 4, 7, 8, 10, 11], "Moon": [3, 6, 11], "Mars": [3, 5, 6, 10, 11, 12],
               "Mercury": [6, 8, 9, 10, 11, 12], "Jupiter": [5, 6, 11, 12], "Venus": [6, 11, 12],
               "Saturn": [3, 5, 6, 11], "Lagna": [1, 3, 4, 6, 10, 11]},
}


# ── Names and layout ─────────────────────────────────────────────────────────

def _layout() -> tuple[list[str], dict[str, slice]]:
    blocks = {
        "T": [f"transiting {t} {a} natal {n}" for t in TRANSITING for n in NATAL for a in ASPECTS],
        "D": ([f"mahadasha of {p}" for p in DASHA_LORDS] + [f"antardasha of {p}" for p in DASHA_LORDS]
              + [f"mahadasha lord rules house {h}" for h in range(1, 13)]
              + [f"antardasha lord rules house {h}" for h in range(1, 13)]
              + [f"antardasha lord placed in house {h}" for h in range(1, 13)]),
        "G": ([f"transiting {t} in house {h} from natal Moon" for t in TRANSITING for h in range(1, 13)]
              + [f"transiting {t} in house {h} from Lagna" for t in TRANSITING for h in range(1, 13)]),
        "A": [f"transiting {t} {a} natal {lord} lord" for lord in ("mahadasha", "antardasha")
              for t in TRANSITING for a in ASPECTS],
        "L": ([f"transiting antardasha lord in house {h} from natal Moon" for h in range(1, 13)]
              + [f"transiting antardasha lord in house {h} from Lagna" for h in range(1, 13)]),
        "X": [f"double transit (Jupiter and Saturn) on house {h}" for h in range(1, 13)],
        "S": ["Sade Sati (Saturn in 12/1/2 from Moon)", "Saturn in 4th from Moon", "Saturn in 8th from Moon"],
        "K": ["transiting Saturn in a sign where its BAV <= 3", "transiting Jupiter in a sign where its BAV >= 5",
              "transiting Jupiter in a sign with SAV > 30", "transiting Jupiter in a sign with SAV < 25",
              "transiting Saturn in a sign with SAV > 30", "transiting Saturn in a sign with SAV < 25"],
        "P": ([f"pratyantardasha of {p}" for p in DASHA_LORDS]
              + [f"pratyantardasha lord placed in house {h}" for h in range(1, 13)]
              + [f"pratyantardasha lord rules house {h}" for h in range(1, 13)]),
        "V": [f"transiting {p} in house {h} from {d} Lagna" for d in ("D9", "D10") for p in ("Jupiter", "Saturn")
              for h in range(1, 13)],
        "C": ([f"Chara MD sign in house {h} from Lagna" for h in range(1, 13)]
              + [f"Chara AD sign in house {h} from Lagna" for h in range(1, 13)]
              + [f"Chara {lvl} sign holds or aspects {k}" for lvl in ("MD", "AD") for k in ("AK", "AmK", "DK")]),
        "Y": ([f"Yogini MD of {p}" for p in YOGINI_LORDS] + [f"Yogini AD of {p}" for p in YOGINI_LORDS]
              + [f"Yogini MD lord rules house {h}" for h in range(1, 13)]
              + [f"Yogini AD lord placed in house {h}" for h in range(1, 13)]),
        "J": ([f"annual Lagna in house {h} from natal Lagna" for h in range(1, 13)]
              + [f"Muntha in house {h} from annual Lagna" for h in range(1, 13)]
              + [f"Muntha in house {h} from natal Lagna" for h in range(1, 13)]
              + [f"Muntha lord in house {h} from annual Lagna" for h in range(1, 13)]),
    }
    names, groups, o = [], {}, 0
    for g, b in blocks.items():
        groups[g] = slice(o, o + len(b))
        names += b
        o += len(b)
    return names, groups


FEATURE_NAMES, GROUPS = _layout()
N_FEATURES = len(FEATURE_NAMES)
TECHNIQUES = {"transits": "TGALXSV", "vimshottari": "DP", "ashtakavarga": "K", "chara": "C",
              "yogini": "Y", "tajika": "J"}


def columns(groups: str) -> np.ndarray:
    return np.concatenate([np.arange(N_FEATURES)[GROUPS[g]] for g in groups])


# ── Ephemeris ────────────────────────────────────────────────────────────────
_sky: dict[float, np.ndarray] = {}


def _swe():
    import swisseph as swe
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe, swe.FLG_SIDEREAL | swe.FLG_MOSEPH


def transits(jd: float) -> np.ndarray:
    if jd not in _sky:
        swe, flags = _swe()
        ids = {"Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
               "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
        _sky[jd] = np.array([swe.calc_ut(jd, ids[t], flags)[0][0] for t in TRANSITING])
    return _sky[jd]


def _sign(lon: float) -> int:
    return int((lon % 360) // 30)


# ── Vimshottari ──────────────────────────────────────────────────────────────

def vimshottari_at(moon: float, birth_jd: float, jd: float) -> tuple[int, int, int]:
    """(MD, AD, PD) indexes into DASHA_LORDS."""
    nak = (moon % 360) / (360 / 27)
    i = int(nak) % 9
    t = (nak - int(nak)) * DASHA_YEARS[i] + (jd - birth_jd) / 365.25
    while t >= DASHA_YEARS[i]:
        t -= DASHA_YEARS[i]
        i = (i + 1) % 9
    j = i
    while t >= DASHA_YEARS[i] * DASHA_YEARS[j] / 120:
        t -= DASHA_YEARS[i] * DASHA_YEARS[j] / 120
        j = (j + 1) % 9
    ad_len = DASHA_YEARS[i] * DASHA_YEARS[j] / 120
    k = j
    while t >= ad_len * DASHA_YEARS[k] / 120:
        t -= ad_len * DASHA_YEARS[k] / 120
        k = (k + 1) % 9
    return i, j, k


# ── Ashtakavarga / divisional ────────────────────────────────────────────────

def bav_tables(natal: np.ndarray) -> dict | None:
    asc = natal[NATAL.index("Ascendant")]
    if math.isnan(asc):
        return None
    ref = {p: _sign(natal[NATAL.index(p)]) for p in SEVEN}
    ref["Lagna"] = _sign(asc)
    table = {}
    for planet in SEVEN:
        b = [0] * 12
        for r, houses in BAV[planet].items():
            for h in houses:
                b[(ref[r] + h - 1) % 12] += 1
        table[planet] = b
    table["SAV"] = [sum(table[p][s] for p in SEVEN) for s in range(12)]
    return table


def d9_sign(lon: float) -> int:
    return int((lon % 360) / (30 / 9)) % 12


def d10_sign(lon: float) -> int:
    s, k = _sign(lon), int(((lon % 360) % 30) // 3)
    return ((s if s % 2 == 0 else (s + 8) % 12) + k) % 12


# ── Jaimini Chara dasha ──────────────────────────────────────────────────────

def jaimini_aspects(a: int, b: int) -> bool:
    if a == b:
        return False
    kind = a % 3
    if kind == 0:
        return b % 3 == 1 and b != (a + 1) % 12
    if kind == 1:
        return b % 3 == 0 and b != (a - 1) % 12
    return b % 3 == 2


def chara_karakas(pos: dict[str, float]) -> dict[str, str]:
    ranked = sorted(SEVEN, key=lambda p: -(pos[p] % 30))
    return dict(zip(["AK", "AmK", "BK", "MK", "PiK", "GK", "DK"], ranked))


def _chara_lord(sign: int, pos: dict[str, float]) -> str:
    if sign not in (7, 10):
        return SIGN_LORD[sign]
    a, b = ("Mars", "Ketu") if sign == 7 else ("Saturn", "Rahu")
    if _sign(pos[a]) == sign:
        return b
    if _sign(pos[b]) == sign:
        return a
    count = {p: sum(1 for q in PLANETS9 if q != p and _sign(pos[q]) == _sign(pos[p])) for p in (a, b)}
    if count[a] != count[b]:
        return a if count[a] > count[b] else b
    return a if pos[a] % 30 >= pos[b] % 30 else b


def chara_years(sign: int, pos: dict[str, float]) -> int:
    lord = _chara_lord(sign, pos)
    ls = _sign(pos[lord])
    if ls == sign:
        return 12
    count = ((ls - sign) % 12) + 1 if sign in SAVYA else ((sign - ls) % 12) + 1
    years = count - 1 + (1 if ls == EXALT[lord] else -1 if ls == DEBIL[lord] else 0)
    return max(1, min(12, years))


def chara_timeline(pos: dict[str, float], asc: float, birth_jd: float, span_years: float = 115) -> list[tuple]:
    lagna = _sign(asc)
    step = 1 if (lagna + 8) % 12 in SAVYA else -1
    seq = [(lagna + i * step) % 12 for i in range(12)]
    first = {s: chara_years(s, pos) for s in seq}
    out, t, cycle = [], birth_jd, 0
    while t < birth_jd + span_years * 365.25 and cycle < 12:
        for s in seq:
            y = first[s] if cycle % 2 == 0 else 12 - first[s]
            if y > 0:
                out.append((t, t + y * 365.25, s))
                t += y * 365.25
        cycle += 1
    return out


def chara_at(timeline: list[tuple], jd: float) -> tuple[int, int] | None:
    for start, end, md in timeline:
        if start <= jd < end:
            k = min(11, int((jd - start) / ((end - start) / 12)))
            step = 1 if md in SAVYA else -1
            return md, (md + (k + 1) * step) % 12
    return None


# ── Yogini ───────────────────────────────────────────────────────────────────

def yogini_at(moon: float, birth_jd: float, jd: float) -> tuple[int, int]:
    nak = (moon % 360) / (360 / 27)
    i = (int(nak) + 1 + 3) % 8
    i = 7 if i == 0 else i - 1
    t = ((nak - int(nak)) * YOGINI_YEARS[i] + (jd - birth_jd) / 365.25) % 36
    while t >= YOGINI_YEARS[i]:
        t -= YOGINI_YEARS[i]
        i = (i + 1) % 8
    j = i
    while t >= YOGINI_YEARS[i] * YOGINI_YEARS[j] / 36:
        t -= YOGINI_YEARS[i] * YOGINI_YEARS[j] / 36
        j = (j + 1) % 8
    return i, j


# ── Tajika ───────────────────────────────────────────────────────────────────

def solar_return(natal_sun: float, birth_jd: float, years: int) -> float:
    swe, flags = _swe()
    jd = birth_jd + years * 365.2564
    for _ in range(5):
        diff = ((natal_sun - swe.calc_ut(jd, swe.SUN, flags)[0][0] + 180) % 360) - 180
        jd += diff / 0.9856
        if abs(diff) < 1e-5:
            break
    return jd


def annual_chart(natal_sun: float, birth_jd: float, jd: float, lat: float, lon: float, cache: dict) -> dict:
    swe, flags = _swe()
    k = max(0, int((jd - birth_jd) / 365.2564))
    if solar_return(natal_sun, birth_jd, k) > jd and k > 0:
        k -= 1
    if k not in cache:
        ret = solar_return(natal_sun, birth_jd, k)
        ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
               "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN}
        cache[k] = {"years": k, "lagna": swe.houses_ex(ret, lat, lon, b"W", swe.FLG_SIDEREAL)[1][0],
                    "positions": {p: swe.calc_ut(ret, i, flags)[0][0] for p, i in ids.items()}}
    return cache[k]


# ── Person context and the feature vector ────────────────────────────────────

def person_context(s: dict) -> dict:
    """Everything fixed for a person (computed once): positions, BAV, Chara timeline, karakas."""
    nat = s["natal"]
    pos = {p: nat[NATAL.index(p)] for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")}
    pos["Ketu"] = (pos["Rahu"] + 180) % 360
    asc = nat[NATAL.index("Ascendant")]
    ctx = {"natal": nat, "pos": pos, "asc": asc, "birth_jd": s["birth_jd"], "lat": s.get("lat"), "lon": s.get("lon"),
           "bav": bav_tables(nat), "sr": {}}
    if not math.isnan(asc):
        ctx["chara"] = chara_timeline(pos, asc, s["birth_jd"])
        ctx["karakas"] = chara_karakas(pos)
    return ctx


def _aspect_hits(sky: np.ndarray, natal: np.ndarray) -> np.ndarray:
    sep = np.abs(((sky[:, None] - natal[None, :]) + 180) % 360 - 180)
    orbs = np.array([ORB[t] for t in TRANSITING])[:, None, None]
    hit = np.abs(sep[:, :, None] - np.array(list(ASPECTS.values()))[None, None, :]) <= orbs
    return (hit & ~np.isnan(natal)[None, :, None]).reshape(-1)


def _lord_lon(lord: str, pos: dict[str, float]) -> float:
    return pos["Ketu"] if lord == "Ketu" else pos[lord]


def features(ctx: dict, jd: float) -> np.ndarray:
    """The N_FEATURES binary vector for this person on this date."""
    out = np.zeros(N_FEATURES, np.uint8)
    nat, pos, asc, bjd = ctx["natal"], ctx["pos"], ctx["asc"], ctx["birth_jd"]
    has_lagna = not math.isnan(asc)
    a = _sign(asc) if has_lagna else None
    moon_s = _sign(pos["Moon"])
    sky = transits(jd)
    md, ad, pd = vimshottari_at(pos["Moon"], bjd, jd)

    out[GROUPS["T"]] = _aspect_hits(sky, nat)

    d0 = GROUPS["D"].start
    out[d0 + md] = out[d0 + 9 + ad] = 1
    if has_lagna:
        for h in range(12):
            out[d0 + 18 + h] = SIGN_LORD[(a + h) % 12] == DASHA_LORDS[md]
            out[d0 + 30 + h] = SIGN_LORD[(a + h) % 12] == DASHA_LORDS[ad]
        out[d0 + 42 + (_sign(_lord_lon(DASHA_LORDS[ad], pos)) - a) % 12] = 1

    g0 = GROUPS["G"].start
    for i, lon in enumerate(sky):
        out[g0 + i * 12 + (_sign(lon) - moon_s) % 12] = 1
        if has_lagna:
            out[g0 + 72 + i * 12 + (_sign(lon) - a) % 12] = 1

    a0 = GROUPS["A"].start
    for k, lord in enumerate((DASHA_LORDS[md], DASHA_LORDS[ad])):
        target = _lord_lon(lord, pos)
        for i, t in enumerate(TRANSITING):
            sep = abs(((sky[i] - target) + 180) % 360 - 180)
            for j, ang in enumerate(ASPECTS.values()):
                out[a0 + k * 24 + i * 4 + j] = abs(sep - ang) <= ORB[t]

    ad_lord = DASHA_LORDS[ad]
    ad_now = (sky[TRANSITING.index("Rahu")] + 180) if ad_lord == "Ketu" else \
        (sky[TRANSITING.index(ad_lord)] if ad_lord in TRANSITING else None)
    if ad_now is not None:
        out[GROUPS["L"].start + (_sign(ad_now) - moon_s) % 12] = 1
        if has_lagna:
            out[GROUPS["L"].start + 12 + (_sign(ad_now) - a) % 12] = 1

    jup, sat = _sign(sky[TRANSITING.index("Jupiter")]), _sign(sky[TRANSITING.index("Saturn")])
    if has_lagna:
        ju_on = {jup} | {(jup + k - 1) % 12 for k in (5, 7, 9)}
        sa_on = {sat} | {(sat + k - 1) % 12 for k in (3, 7, 10)}
        for s in ju_on & sa_on:
            out[GROUPS["X"].start + (s - a) % 12] = 1

    s0 = GROUPS["S"].start
    h_sat = (sat - moon_s) % 12 + 1
    out[s0], out[s0 + 1], out[s0 + 2] = h_sat in (12, 1, 2), h_sat == 4, h_sat == 8

    bav = ctx["bav"]
    if bav:
        k0 = GROUPS["K"].start
        out[k0:k0 + 6] = [bav["Saturn"][sat] <= 3, bav["Jupiter"][jup] >= 5, bav["SAV"][jup] > 30,
                          bav["SAV"][jup] < 25, bav["SAV"][sat] > 30, bav["SAV"][sat] < 25]

    p0 = GROUPS["P"].start
    out[p0 + pd] = 1
    if has_lagna:
        lord = DASHA_LORDS[pd]
        out[p0 + 9 + (_sign(_lord_lon(lord, pos)) - a) % 12] = 1
        for h in range(12):
            out[p0 + 21 + h] = SIGN_LORD[(a + h) % 12] == lord
        v0 = GROUPS["V"].start
        for di, lagna in enumerate((d9_sign(asc), d10_sign(asc))):
            for pi, s in enumerate((jup, sat)):
                out[v0 + di * 24 + pi * 12 + (s - lagna) % 12] = 1

    c0 = GROUPS["C"].start
    if has_lagna:
        cur = chara_at(ctx["chara"], jd)
        if cur:
            cmd, cad = cur
            out[c0 + (cmd - a) % 12] = 1
            out[c0 + 12 + (cad - a) % 12] = 1
            for li, s in enumerate((cmd, cad)):
                for ki, k in enumerate(("AK", "AmK", "DK")):
                    ks = _sign(pos[ctx["karakas"][k]])
                    out[c0 + 24 + li * 3 + ki] = ks == s or jaimini_aspects(s, ks)

    y0 = GROUPS["Y"].start
    ymd, yad = yogini_at(pos["Moon"], bjd, jd)
    out[y0 + ymd] = out[y0 + 8 + yad] = 1
    if has_lagna:
        for h in range(12):
            out[y0 + 16 + h] = SIGN_LORD[(a + h) % 12] == YOGINI_LORDS[ymd]
        out[y0 + 28 + (_sign(pos[YOGINI_LORDS[yad]]) - a) % 12] = 1

    t0 = GROUPS["J"].start
    if has_lagna and ctx["lat"] is not None and ctx["lon"] is not None:
        ch = annual_chart(pos["Sun"], bjd, jd, ctx["lat"], ctx["lon"], ctx["sr"])
        vl = _sign(ch["lagna"])
        muntha = (a + ch["years"]) % 12
        out[t0 + (vl - a) % 12] = 1
        out[t0 + 12 + (muntha - vl) % 12] = 1
        out[t0 + 24 + (muntha - a) % 12] = 1
        out[t0 + 36 + (_sign(ch["positions"][SIGN_LORD[muntha]]) - vl) % 12] = 1
    return out
