"""
src/rao.py — K.N. Rao's marriage-timing parameters (P1-P8) and observations (O1-O3) as binary features.

Source: "Astrology and Timing of Marriage (a Scientific Approach)", Bharatiya Vidya Bhavan research under
K.N. Rao, Chapter 2 (definitions, quoted in each function) and the case studies (used as benchmarks in
tests/test_rao.py: case 1 Bill Clinton, case 2 Hillary Clinton, both married 11-10-1975).

The book's evidence is the share of 218 marriages in which each parameter applied (P1 100%, P2 96%,
P3 77%, P4 85%, P5 98%, P6 68%, P7 70%, P8 59%; "85.78% of cases six or more parameters apply") — with
no comparison dates. This module lets the same parameters be evaluated on the same people's ordinary
dates (case-crossover), which is the test the book does not make.

Operational choices (where the text is not explicit; stated so they can be challenged):
  - PAC = Position (occupies the sign), Aspect (Parashari graha drishti by sign: every planet the 7th;
    Mars also 4th/8th, Jupiter 5th/9th, Saturn 3rd/10th, Rahu/Ketu 5th/9th), Conjunction (same sign).
  - "Planets associated with" Lagna/LL/7H/7L = planets in PAC with them.
  - Arudha padas without the "same or 7th house -> 10th" exception: that reproduces the book's UP/DP in
    case 1 (UP Leo with the 12th lord in the 12th). In case 2 the book's UP and DP labels appear swapped.
  - Chara karakas from the seven planets Sun..Saturn by degree in sign (DK = lowest).
  - P7 "Sun and/or most planets around Lagna or 7H": Sun, or at least 6 of the 9 grahas, in houses
    12/1/2 or 6/7/8 of the transit (case 2: Sun in the 4th with 5 planets near the angles = "scattered").
  - Retrograde transiting Jupiter/Saturn also act from the previous sign (case 2, P3).
  - Chara antardashas run from the mahadasha sign itself, backward (reproduces case 1's Sag/Aries).
  - P8 "in/near": LL transiting houses 6/7/8, or 7L transiting 12/1/2.
  - O1 Moon: transiting Moon in PAC with Lagna, 7H, LL or 7L (the book also accepts Karakamsha Lagna;
    not included). Event dates have no time: all transits at noon UT.
Needs a known birth time (Lagna); P6 needs gender (M -> Venus, F -> Mars).
"""
from __future__ import annotations

import math

import numpy as np

from src import features as F
from src.preprocessing import NATAL

NAMES = ["rao_p1_vim_dasha_conn", "rao_p2_chara_dasha_conn", "rao_p3_vivah_saham_transit", "rao_p4_double_transit",
         "rao_p5_piya_milan", "rao_p6_karaka_activation", "rao_p7_planet_cluster", "rao_p8_lord_swap",
         "rao_o1_moon_trigger", "rao_o2_saturn_dk", "rao_o3_d9_5_11_axis"]
N = len(NAMES)
GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
EXTRA_ASPECTS = {"Mars": (4, 8), "Jupiter": (5, 9), "Saturn": (3, 10), "Rahu": (5, 9), "Ketu": (5, 9)}


def _sign(lon: float) -> int:
    return int((lon % 360) // 30)


def aspects(planet: str, frm: int, to: int) -> bool:
    """Parashari sign aspect of `planet` standing in sign `frm` on sign `to`."""
    h = (to - frm) % 12 + 1
    return h == 7 or h in EXTRA_ASPECTS.get(planet, ())


def pac(planet: str, p_sign: int, target_sign: int) -> bool:
    """Position/conjunction (same sign) or aspect on the target sign."""
    return p_sign == target_sign or aspects(planet, p_sign, target_sign)


def mutual_pac(a: str, sa: int, b: str, sb: int) -> bool:
    return sa == sb or aspects(a, sa, sb) or aspects(b, sb, sa)


def pada(house_sign: int, lord_sign: int) -> int:
    """Arudha: as far from the lord as the lord is from the house (no exception rule; see module doc)."""
    return (lord_sign + (lord_sign - house_sign) % 12) % 12


# ── Natal context ────────────────────────────────────────────────────────────

def context(s: dict, gender: str | None) -> dict | None:
    nat = s["natal"]
    asc = nat[NATAL.index("Ascendant")]
    if math.isnan(asc):
        return None
    lon = {p: float(nat[NATAL.index(p)]) for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")}
    lon["Ketu"] = (lon["Rahu"] + 180) % 360
    d1 = {p: _sign(v) for p, v in lon.items()}
    d9 = {p: F.d9_sign(v) for p, v in lon.items()}
    lag, lag9 = _sign(asc), F.d9_sign(asc)
    ll, l7 = F.SIGN_LORD[lag], F.SIGN_LORD[(lag + 6) % 12]
    ll9, l79 = F.SIGN_LORD[lag9], F.SIGN_LORD[(lag9 + 6) % 12]
    dk = F.chara_karakas(lon)["DK"]
    ctx = {"lon": lon, "d1": d1, "d9": d9, "lagna": lag, "lagna9": lag9, "LL": ll, "7L": l7, "LL9": ll9, "7L9": l79,
           "DK": dk, "DKN": d9[dk], "gender": gender, "birth_jd": s["birth_jd"],
           "VS": _sign(lon[ll] + lon[l7]),
           "UP": pada((lag + 11) % 12, d1[F._chara_lord((lag + 11) % 12, lon)]),
           "DP": pada((lag + 6) % 12, d1[F._chara_lord((lag + 6) % 12, lon)]),
           "chara": F.chara_timeline(lon, asc, s["birth_jd"])}
    ctx["marriage_givers_d1"] = _connected_set(d1, lag, ll, l7)
    ctx["marriage_givers_d9"] = _connected_set(d9, lag9, ll9, l79)
    ctx["d9_5_11"] = _axis_set(d9, lag9, (4, 10))
    return ctx


def _connected_set(signs: dict, lag: int, ll: str, l7: str) -> set[str]:
    """Planets with PAC to Lagna, 7H, LL or 7L — the lords themselves included — in one chart.
    'Planets associated with them' (Parameter 1)."""
    seventh = (lag + 6) % 12
    out = {ll, l7}
    for p in GRAHAS:
        sp = signs[p]
        if pac(p, sp, lag) or pac(p, sp, seventh) or mutual_pac(p, sp, ll, signs[ll]) or mutual_pac(p, sp, l7, signs[l7]):
            out.add(p)
    return out


def _axis_set(signs: dict, lag: int, houses: tuple[int, ...]) -> set[str]:
    """Planets with PAC to the given houses (0-based from Lagna) or to those houses' lords."""
    out = set()
    targets = [(lag + h) % 12 for h in houses]
    lords = [F.SIGN_LORD[t] for t in targets]
    for p in GRAHAS:
        sp = signs[p]
        if any(pac(p, sp, t) for t in targets) or any(p == L or mutual_pac(p, sp, L, signs[L]) for L in lords):
            out.add(p)
    return out


# ── Transits ─────────────────────────────────────────────────────────────────

_sky9: dict[float, dict] = {}


def transit_signs(jd: float) -> dict[str, int]:
    if jd not in _sky9:
        swe, flags = F._swe()
        ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
               "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
        calc = {p: swe.calc_ut(jd, i, flags | swe.FLG_SPEED)[0] for p, i in ids.items()}
        signs = {p: _sign(c[0]) for p, c in calc.items()}
        signs["Ketu"] = _sign(calc["Rahu"][0] + 180)
        signs["_retro"] = {p for p in ("Jupiter", "Saturn") if calc[p][3] < 0}
        signs["_nak"] = {p: int((c[0] % 360) // (360 / 27)) for p, c in calc.items()}   # 0 = Ashwini
        signs["_nak"]["Ketu"] = int(((calc["Rahu"][0] + 180) % 360) // (360 / 27))
        _sky9[jd] = signs
    return _sky9[jd]


def transit_pac(planet: str, t: dict, target: int) -> bool:
    """PAC of a transiting planet on a sign; a retrograde Jupiter/Saturn also acts from the previous sign
    (case 2: "Jupiter through retrogation is aspecting VS")."""
    if pac(planet, t[planet], target):
        return True
    return planet in t["_retro"] and pac(planet, (t[planet] - 1) % 12, target)


# ── The parameters ───────────────────────────────────────────────────────────

def features(ctx: dict | None, jd: float) -> np.ndarray:
    out = np.zeros(N, np.uint8)
    if ctx is None:
        return out
    t = transit_signs(jd)
    lag, seventh = ctx["lagna"], (ctx["lagna"] + 6) % 12
    ll, l7 = ctx["LL"], ctx["7L"]
    md, ad, pd = (F.DASHA_LORDS[i] for i in F.vimshottari_at(ctx["lon"]["Moon"], ctx["birth_jd"], jd))
    givers = ctx["marriage_givers_d1"] | ctx["marriage_givers_d9"]

    # P1 "the MD and AD lords ought to have PAC connection with Lagna, LL, 7H, 7L or the planets associated
    #    with them in Rashi (D1) and Navamsha (D9)" (Venus counted as the natural marriage giver, as in case 1)
    out[0] = all(x in givers or x == "Venus" or _disposited_by(x, ctx, givers | {"Venus"}) for x in (md, ad))

    # P2 "the AD rashi should establish a connection by being in 1-7 axis with DK, DKN, DP, UPL or 7L
    #    [of D1 or D9] or by giving them Jaimini Drishti"
    cur = chara_rao(ctx["chara"], jd)
    if cur:
        ad_sign = cur[1]
        targets = {ctx["d1"][ctx["DK"]], ctx["DKN"], ctx["DP"], ctx["UP"], ctx["d1"][l7], ctx["d9"][ctx["7L9"]]}
        out[1] = any(ad_sign in (x, (x + 6) % 12) or F.jaimini_aspects(ad_sign, x) for x in targets)

    # P3 "Jupiter's aspects in transit on Vivah Saham" (VS = sign of LL longitude + 7L longitude)
    out[2] = transit_pac("Jupiter", t, ctx["VS"])

    # P4 "Saturn and Jupiter activating Lagna, 7H, LL, 7L or VS" through PAC — both of them
    targets = [lag, seventh, ctx["d1"][ll], ctx["d1"][l7], ctx["VS"]]
    out[3] = any(transit_pac("Saturn", t, x) for x in targets) and any(transit_pac("Jupiter", t, x) for x in targets)

    # P5 (Piya Milan) "LL and the 7L of native making a connection in transit"
    out[4] = ll != l7 and mutual_pac(ll, t[ll], l7, t[l7])

    # P6 "transiting Jupiter activates natal Venus in male charts and natal Mars in female charts"
    if ctx["gender"] in ("M", "F"):
        karaka = "Venus" if ctx["gender"] == "M" else "Mars"
        out[5] = transit_pac("Jupiter", t, ctx["d1"][karaka])

    # P7 "Sun and/or most planets around Lagna or 7H" (houses 12/1/2 or 6/7/8 of the transit)
    around = lambda s: (s - lag) % 12 + 1 in (12, 1, 2, 6, 7, 8)             # noqa: E731
    out[6] = around(t["Sun"]) or sum(around(t[p]) for p in GRAHAS) >= 6

    # P8 "LL transiting in/near 7H or 7L transiting in/near Lagna"
    out[7] = (t[ll] - lag) % 12 + 1 in (6, 7, 8) or (t[l7] - lag) % 12 + 1 in (12, 1, 2)

    # O1 role of the transiting Moon: PAC with Lagna, 7H, LL or 7L
    m = t["Moon"]
    out[8] = pac("Moon", m, lag) or pac("Moon", m, seventh) or m in (ctx["d1"][ll], ctx["d1"][l7])

    # O2 "Saturn activates DK by aspecting it (Jaimini aspect) or by being in 1-7 axis from it"
    dk = ctx["d1"][ctx["DK"]]
    sats = {t["Saturn"]} | ({(t["Saturn"] - 1) % 12} if "Saturn" in t["_retro"] else set())
    out[9] = any(F.jaimini_aspects(x, dk) or x in (dk, (dk + 6) % 12) for x in sats)

    # O3 "PAC relationship of MD/AD/PD lords with 5-11 houses/lords of D9"
    out[10] = any(x in ctx["d9_5_11"] for x in (md, ad, pd))
    return out


def chara_rao(timeline: list[tuple], jd: float) -> tuple[int, int] | None:
    """(MD sign, AD sign) with antardashas from the MD sign itself, counted backward (the book's usage)."""
    for start, end, md in timeline:
        if start <= jd < end:
            k = min(11, int((jd - start) / ((end - start) / 12)))
            return md, (md - k) % 12
    return None


def _disposited_by(planet: str, ctx: dict, givers: set[str]) -> bool:
    """Case 1 counts 'MD lord Rahu is posited in the sign of Venus' as a connection: the planet sits in a
    sign owned by a marriage-giving planet (D1 or D9)."""
    return F.SIGN_LORD[ctx["d1"][planet]] in givers or F.SIGN_LORD[ctx["d9"][planet]] in givers


def count_parameters(f: np.ndarray) -> int:
    """How many of P1-P8 apply (the book's summary statistic)."""
    return int(f[:8].sum())
