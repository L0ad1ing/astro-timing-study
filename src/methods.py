"""
src/methods.py — fourteen timing techniques, isolated, each mapping (person, date) to activated houses/planets.
Pre-registered: docs/prereg_methods.md (commit 469eb54). Whole-sign houses throughout.

Vedic (sidereal, Lahiri): V1 Vimshottari, V2 BCP chain, V3 Chara dasha, V4 Tajika Muntha, V5 double transit,
  V6 Jupiter transit.
Western (tropical): W1 secondary progressions, W2 solar arc, W3 solar return, W4 outer-planet transits.
Hellenistic (tropical): H1 annual profections, H2 zodiacal releasing from the Lot of Spirit, H3 firdaria.
Medical: M1 transiting Saturn/Mars hard aspects to the Ascendant ruler or the lights (tropical);
  M2 Vedic maraka / 6th / 8th lord periods. Medical methods only apply to Illness, Accident and own Death.

Conventions to know: zodiacal releasing uses 365.25-day years (Valens used 360) and, at the loosening of the bond,
jumps to the sign opposite the L1 sign; firdaria nodes have no sub-periods; sect from the Sun's position relative to
the horizon on the ecliptic (above = day).
"""
from __future__ import annotations

import math

from src import bcp_chain as B
from src import features as F
from src import rao as R
from src.preprocessing import NATAL

SEVEN = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
CHALDEAN = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
ZR_YEARS = [15, 8, 20, 25, 19, 20, 8, 15, 12, 27, 30, 12]
FIRDARIA_DAY = [("Sun", 10), ("Venus", 8), ("Mercury", 13), ("Moon", 9), ("Saturn", 11), ("Jupiter", 12), ("Mars", 7),
                ("Rahu", 3), ("Ketu", 2)]
FIRDARIA_NIGHT = [("Moon", 9), ("Saturn", 11), ("Jupiter", 12), ("Mars", 7), ("Sun", 10), ("Venus", 8), ("Mercury", 13),
                  ("Rahu", 3), ("Ketu", 2)]
METHODS = ["V1_vimshottari", "V2_bcp_chain", "V3_chara", "V4_tajika_muntha", "V5_double_transit", "V6_jupiter_transit",
           "TJ2_annual_lagna", "TJ3_mudda_dasha", "N1_tara", "N2_janma_transit", "N3_star_lord",
           "W1_progressions", "W2_solar_arc", "W3_solar_return", "W4_outer_transits",
           "H1_profection", "H2_zodiacal_releasing", "H3_zr_fortune",
           "MD1_firdaria", "MD2_distribution", "MD3_lord_of_year_transit",
           "M1_medical_transits", "M2_vedic_medical"]
FAMILY = {"V": "Vedic", "TJ": "Tajika", "N": "Nakshatra", "W": "Western", "H": "Hellenistic", "MD": "Medieval", "M": "Medical"}
POSITIVE = {"Marriage", "Birth_Child", "Career_Peak", "Prize", "Job_Start"}
# Egyptian bounds: (ruler, end degree) per sign
BOUNDS = [[("Jupiter", 6), ("Venus", 12), ("Mercury", 20), ("Mars", 25), ("Saturn", 30)],
          [("Venus", 8), ("Mercury", 14), ("Jupiter", 22), ("Saturn", 27), ("Mars", 30)],
          [("Mercury", 6), ("Jupiter", 12), ("Venus", 17), ("Mars", 24), ("Saturn", 30)],
          [("Mars", 7), ("Venus", 13), ("Mercury", 19), ("Jupiter", 26), ("Saturn", 30)],
          [("Jupiter", 6), ("Venus", 11), ("Saturn", 18), ("Mercury", 24), ("Mars", 30)],
          [("Mercury", 7), ("Venus", 17), ("Jupiter", 21), ("Mars", 28), ("Saturn", 30)],
          [("Saturn", 6), ("Mercury", 14), ("Jupiter", 21), ("Venus", 28), ("Mars", 30)],
          [("Mars", 7), ("Venus", 11), ("Mercury", 19), ("Jupiter", 24), ("Saturn", 30)],
          [("Jupiter", 12), ("Venus", 17), ("Mercury", 21), ("Saturn", 26), ("Mars", 30)],
          [("Mercury", 7), ("Jupiter", 14), ("Venus", 22), ("Saturn", 26), ("Mars", 30)],
          [("Mercury", 7), ("Venus", 13), ("Jupiter", 20), ("Mars", 25), ("Saturn", 30)],
          [("Venus", 12), ("Jupiter", 16), ("Mercury", 19), ("Mars", 28), ("Saturn", 30)]]


def bound_lord(lon: float) -> str:
    deg, sgn = lon % 30, _sign(lon)
    return next(r for r, end in BOUNDS[sgn] if deg < end)


def nakshatra(lon: float) -> int:
    """0-based nakshatra index (0 = Ashwini)."""
    return int((lon % 360) / (360 / 27))


def tara(transit_moon: float, birth_moon: float) -> int:
    """1 Janma, 2 Sampat, 3 Vipat, 4 Kshema, 5 Pratyari, 6 Sadhaka, 7 Vadha, 8 Mitra, 9 Param Mitra."""
    return (nakshatra(transit_moon) - nakshatra(birth_moon)) % 27 % 9 + 1


def mudda_lord(birth_moon: float, years: int, frac_of_year: float) -> str:
    """Tajika Mudda dasha lord: start = (birth star no. + completed years - 2) mod 9 counted from Ketu; then the
    Vimshottari sequence with periods proportional to Vimshottari years over one year."""
    r = (nakshatra(birth_moon) + 1 + years - 2) % 9
    i = (r - 1) % 9
    t = frac_of_year * 120
    while t >= F.DASHA_YEARS[i]:
        t -= F.DASHA_YEARS[i]
        i = (i + 1) % 9
    return F.DASHA_LORDS[i]
TARGETS = {"Marriage": ([7], "Venus"), "Divorce": ([7], "Venus"), "Birth_Child": ([5], "Jupiter"),
           "Career_Peak": ([10], "Sun"), "Prize": ([10], "Sun"), "Job_Start": ([10], "Sun"),
           "Arrest": ([12, 6], "Saturn"), "Trial": ([12, 6], "Saturn"), "Illness": ([6], "Saturn"),
           "Accident": ([8], "Mars"), "Death of father": ([9], "Sun"), "Death of mother": ([4], "Moon"),
           "Death of mate": ([7], "Venus"), "Death": ([8], "Saturn")}
MEDICAL = {"Illness", "Accident", "Death"}
HARD = (0, 90, 180)
MAJOR = (0, 90, 120, 180)


def _sign(lon: float) -> int:
    return int((lon % 360) // 30)


def _sep(a: float, b: float) -> float:
    return abs(((a - b) + 180) % 360 - 180)


def _aspect(a: float, b: float, orb: float, angles=MAJOR) -> bool:
    s = _sep(a, b)
    return any(abs(s - x) <= orb for x in angles)


def _rules(planet: str, lagna: int) -> set[int]:
    return {h for h in range(1, 13) if F.SIGN_LORD[(lagna + h - 1) % 12] == planet}


def _house(lon: float, lagna: int) -> int:
    return (_sign(lon) - lagna) % 12 + 1


# ── Period systems ───────────────────────────────────────────────────────────

def zr_l2(lot_sign: int, birth_jd: float, jd: float) -> tuple[int, int]:
    """(L1 sign, L2 sign) of zodiacal releasing from a lot's sign."""
    t = (jd - birth_jd) / 365.25
    s, start = lot_sign, 0.0
    while start + ZR_YEARS[s] <= t:
        start += ZR_YEARS[s]
        s = (s + 1) % 12
    s2, t2, n = s, start, 0
    while True:
        d = ZR_YEARS[s2] / 12
        if t2 + d > t:
            return s, s2
        t2 += d
        n += 1
        s2 = (s + 6) % 12 if n == 12 else (s2 + 1) % 12          # loosening of the bond after a full round


def firdaria(day: bool, birth_jd: float, jd: float) -> tuple[str, str]:
    """(period ruler, sub-period ruler)."""
    seq = FIRDARIA_DAY if day else FIRDARIA_NIGHT
    t = ((jd - birth_jd) / 365.25) % 75
    for ruler, years in seq:
        if t < years:
            if ruler in ("Rahu", "Ketu"):
                return ruler, ruler
            k = int(t / (years / 7))
            i = CHALDEAN.index(ruler)
            return ruler, CHALDEAN[(i + k) % 7]
        t -= years
    return seq[-1][0], seq[-1][0]


# ── Person context ───────────────────────────────────────────────────────────

class Person:
    def __init__(self, s: dict):
        swe, flags = F._swe()
        nat = s["natal"]
        self.bjd, self.lat, self.lon_geo = s["birth_jd"], s.get("lat"), s.get("lon")
        self.sid = {p: float(nat[NATAL.index(p)]) for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")}
        self.sid["Ketu"] = (self.sid["Rahu"] + 180) % 360
        self.asc_sid = float(nat[NATAL.index("Ascendant")])
        self.has_lagna = not math.isnan(self.asc_sid)
        ayan = swe.get_ayanamsa_ut(self.bjd)
        self.trop = {p: (v + ayan) % 360 for p, v in self.sid.items()}
        for p, i in (("Uranus", swe.URANUS), ("Neptune", swe.NEPTUNE), ("Pluto", swe.PLUTO)):
            self.trop[p] = swe.calc_ut(self.bjd, i, swe.FLG_MOSEPH)[0][0]
        self.asc_trop = (self.asc_sid + ayan) % 360 if self.has_lagna else math.nan
        self.mc_trop = None
        if self.has_lagna and self.lat is not None and self.lon_geo is not None:
            self.mc_trop = swe.houses_ex(self.bjd, self.lat, self.lon_geo, b"W")[1][1]
        self.lag_sid = _sign(self.asc_sid) if self.has_lagna else None
        self.lag_trop = _sign(self.asc_trop) if self.has_lagna else None
        self.day = self.has_lagna and ((self.trop["Sun"] - self.asc_trop) % 360) > 180
        if self.has_lagna:
            sun, moon, a = self.trop["Sun"], self.trop["Moon"], self.asc_trop
            self.spirit = (a + sun - moon) % 360 if self.day else (a + moon - sun) % 360
            self.fortune = (a + moon - sun) % 360 if self.day else (a + sun - moon) % 360
            self.chart = B.Chart(self.lag_sid, {p: _sign(v) for p, v in self.sid.items() if p != "Ketu"})
            self.chara = F.chara_timeline(self.sid, self.asc_sid, self.bjd)
        self._sr: dict = {}
        self._tajika: dict = {}

    # helpers
    def sid_houses(self, planets) -> set[int]:
        out = set()
        for p in planets:
            out |= _rules(p, self.lag_sid) | {_house(self.sid[p], self.lag_sid)}
        return out

    def trop_rules(self, planets) -> set[int]:
        out = set()
        for p in planets:
            out |= _rules(p, self.lag_trop)
        return out


def _tropical(jd: float, names) -> dict[str, tuple[float, float]]:
    swe, _ = F._swe()
    ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
           "Venus": swe.VENUS, "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO}
    return {n: swe.calc_ut(jd, ids[n], swe.FLG_MOSEPH | swe.FLG_SPEED)[0][:4:3] for n in names}


def _tropical_return(natal_sun: float, birth_jd: float, years: int) -> float:
    swe, _ = F._swe()
    jd = birth_jd + years * 365.2422
    for _ in range(5):
        diff = ((natal_sun - swe.calc_ut(jd, swe.SUN, swe.FLG_MOSEPH)[0][0] + 180) % 360) - 180
        jd += diff / 0.9856
        if abs(diff) < 1e-5:
            break
    return jd


# ── The methods ──────────────────────────────────────────────────────────────

def evaluate(p: Person, jd: float) -> dict[str, tuple[set[int], set[str]] | dict]:
    """{method: (houses, planets)}; M1/M2 return {'M1': flags...} handled in flagged()."""
    out: dict = {}
    if not p.has_lagna:
        return out
    md, ad, _pd = (F.DASHA_LORDS[i] for i in F.vimshottari_at(p.sid["Moon"], p.bjd, jd))
    out["V1_vimshottari"] = (p.sid_houses([md, ad]), {md, ad})

    age = int((jd - p.bjd) / 365.2425)
    st = p.chart._steps[B.active_house(age)]
    out["V2_bcp_chain"] = ({h for h, d in st["houses"].items() if d <= 2}, {q for q, d in st["planets"].items() if d <= 2})

    cur = R.chara_rao(p.chara, jd)
    if cur:
        a = cur[1]
        hs = {(a - p.lag_sid) % 12 + 1} | {(s - p.lag_sid) % 12 + 1 for s in range(12) if F.jaimini_aspects(a, s)}
        out["V3_chara"] = (hs, {q for q, v in p.sid.items() if _sign(v) == a})

    k = max(0, int((jd - p.bjd) / 365.2564))
    muntha = (p.lag_sid + k) % 12
    out["V4_tajika_muntha"] = ({(muntha - p.lag_sid) % 12 + 1}, {F.SIGN_LORD[muntha]})

    t = R.transit_signs(jd)
    ju_on = {t["Jupiter"]} | {(t["Jupiter"] + x - 1) % 12 for x in (5, 7, 9)}
    sa_on = {t["Saturn"]} | {(t["Saturn"] + x - 1) % 12 for x in (3, 7, 10)}
    both = ju_on & sa_on
    out["V5_double_transit"] = ({(s - p.lag_sid) % 12 + 1 for s in both}, {q for q, v in p.sid.items() if _sign(v) in both})
    out["V6_jupiter_transit"] = ({(s - p.lag_sid) % 12 + 1 for s in ju_on}, {q for q, v in p.sid.items() if _sign(v) in ju_on})

    natal_pts = {q: p.trop[q] for q in SEVEN}
    natal_pts["Ascendant"] = p.asc_trop
    if p.mc_trop is not None:
        natal_pts["Midheaven"] = p.mc_trop

    def to_houses(hit):
        hs = p.trop_rules([q for q in hit if q in SEVEN])
        hs |= {1} if "Ascendant" in hit else set()
        hs |= {10} if "Midheaven" in hit else set()
        return hs, {q for q in hit if q in SEVEN}

    prog_jd = p.bjd + (jd - p.bjd) / 365.2422
    prog = _tropical(prog_jd, ["Sun", "Moon"])
    hit = {q for q, v in natal_pts.items() for pr in ("Sun", "Moon") if _aspect(prog[pr][0], v, 1.0)}
    out["W1_progressions"] = to_houses(hit)

    arc = (prog["Sun"][0] - p.trop["Sun"]) % 360
    hit = {q for q, v in natal_pts.items() for d, dv in natal_pts.items() if d != q and _aspect((dv + arc) % 360, v, 1.0, HARD)}
    out["W2_solar_arc"] = to_houses(hit)

    if p.lat is not None and p.lon_geo is not None:
        ky = max(0, int((jd - p.bjd) / 365.2422))
        if ky not in p._sr:
            ret = _tropical_return(p.trop["Sun"], p.bjd, ky)
            if ret > jd and ky > 0:
                ky -= 1
                ret = _tropical_return(p.trop["Sun"], p.bjd, ky)
            swe, _ = F._swe()
            p._sr[ky] = swe.houses_ex(ret, p.lat, p.lon_geo, b"W")[1][0]
        sr_asc = p._sr[ky]
        out["W3_solar_return"] = ({_house(sr_asc, p.lag_trop)}, {F.SIGN_LORD[_sign(sr_asc)]})

    tr = _tropical(jd, ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Mars"])
    hit = {q for q, v in natal_pts.items() for o in ("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto") if _aspect(tr[o][0], v, 1.0)}
    out["W4_outer_transits"] = to_houses(hit)

    prof = (p.lag_trop + age) % 12
    loy = F.SIGN_LORD[prof]
    out["H1_profection"] = ({(prof - p.lag_trop) % 12 + 1} | _rules(loy, p.lag_trop), {loy})

    _, l2 = zr_l2(_sign(p.spirit), p.bjd, jd)
    out["H2_zodiacal_releasing"] = ({(l2 - p.lag_trop) % 12 + 1}, {F.SIGN_LORD[l2]})

    _, l2f = zr_l2(_sign(p.fortune), p.bjd, jd)
    out["H3_zr_fortune"] = ({(l2f - p.lag_trop) % 12 + 1}, {F.SIGN_LORD[l2f]})

    fr, fs = firdaria(p.day, p.bjd, jd)
    out["MD1_firdaria"] = (p.trop_rules([fr, fs]), {fr, fs})
    dist = bound_lord(p.asc_trop + 0.98565 * (jd - p.bjd) / 365.2422)
    out["MD2_distribution"] = (p.trop_rules([dist]), {dist})
    loy_now = _tropical(jd, [loy])[loy][0] if loy in SEVEN else None
    out["MD3_lord_of_year_transit"] = ({_house(loy_now, p.lag_trop)} if loy_now is not None else set(), set())

    if p.lat is not None and p.lon_geo is not None:
        ch = F.annual_chart(p.sid["Sun"], p.bjd, jd, p.lat, p.lon_geo, p._tajika)
        vl = _sign(ch["lagna"])
        out["TJ2_annual_lagna"] = ({(vl - p.lag_sid) % 12 + 1}, {F.SIGN_LORD[vl]})
        start = F.solar_return(p.sid["Sun"], p.bjd, ch["years"])
        frac = min(0.999999, max(0.0, (jd - start) / 365.2564))
        ml = mudda_lord(p.sid["Moon"], ch["years"], frac)
        out["TJ3_mudda_dasha"] = (p.sid_houses([ml]), {ml})

    moon_now = _sid_moon(jd)
    out["N1_tara"] = {"tara": tara(moon_now, p.sid["Moon"])}
    birth_star = nakshatra(p.sid["Moon"])
    trines = {birth_star, (birth_star + 9) % 27, (birth_star + 18) % 27}
    sjup, ssat = _sid_lons(jd, ("Jupiter", "Saturn"))
    out["N2_janma_transit"] = {"saturn": nakshatra(ssat) in trines, "jupiter": nakshatra(sjup) in trines}
    star_lord = F.DASHA_LORDS[nakshatra(p.sid[ad]) % 9]
    out["N3_star_lord"] = (p.sid_houses([star_lord]), {star_lord})

    asc_ruler = F.SIGN_LORD[p.lag_trop]
    pts = [p.trop[asc_ruler], p.trop["Sun"], p.trop["Moon"]]
    out["M1_medical_transits"] = {"hit": any(_aspect(tr[m][0], v, 1.5, HARD) for m in ("Saturn", "Mars") for v in pts)}
    rules_md_ad = _rules(md, p.lag_sid) | _rules(ad, p.lag_sid)
    occ8 = {q for q in (md, ad) if _house(p.sid[q], p.lag_sid) == 8}
    out["M2_vedic_medical"] = {"Death": bool(rules_md_ad & {2, 7}), "Illness": bool(rules_md_ad & {6, 8}),
                               "Accident": bool(rules_md_ad & {8}) or bool(occ8)}
    return out


def _sid_lons(jd: float, names) -> tuple[float, ...]:
    swe, flags = F._swe()
    ids = {"Moon": swe.MOON, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN}
    return tuple(swe.calc_ut(jd, ids[n], flags)[0][0] for n in names)


def _sid_moon(jd: float) -> float:
    return _sid_lons(jd, ("Moon",))[0]


def flagged(result: dict, method: str, category: str) -> bool | None:
    """Does this method flag this event type on this date? None if not applicable."""
    if method not in result:
        return None
    r = result[method]
    if method == "M1_medical_transits":
        return r["hit"] if category in MEDICAL else None
    if method == "M2_vedic_medical":
        return r.get(category) if category in MEDICAL else None
    if method == "N1_tara":
        return r["tara"] in ((2, 4, 6, 8, 9) if category in POSITIVE else (3, 5, 7))
    if method == "N2_janma_transit":
        return r["jupiter"] if category in POSITIVE else r["saturn"]
    houses, planets = r
    targets, karaka = TARGETS[category]
    return bool(set(targets) & houses) or karaka in planets
