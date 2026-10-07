"""
src/strength.py — planetary strength and dignity features (docs/prereg_strength.md).

natal_strength(s)        per-planet natal strength vectors (PLANET_FEATURES), sidereal Lahiri, whole-sign houses
StrengthFeaturizer       706 existing features + the strength profile of every planet that timing activates on
                         a date (dasha / yogini / chara / profection / Muntha / Mudda / Bhrigu Chakra lords) + the
                         condition of the transiting planets on the date

Classical sources: BPHS for natural friendship, exaltation and debilitation degrees, moolatrikona ranges, uchcha /
dig / paksha / nathonnatha bala, ishta and kashta phala; standard combustion orbs; baladi avasthas.
Rahu uses Saturn's friendships, Ketu Mars's; Rahu is exalted in Taurus, Ketu in Scorpio.
"""
from __future__ import annotations

import math

import numpy as np

from src import features as F
from src import methods as Me
from src import rao as R
from src import models as Mo
from src.preprocessing import NATAL

GRAHAS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
SEVEN = GRAHAS[:7]

# Deep exaltation (sidereal longitude) and exaltation sign.
DEEP_EXALT = {'Sun': 10, 'Moon': 33, 'Mars': 298, 'Mercury': 165, 'Jupiter': 95, 'Venus': 357, 'Saturn': 200,
              'Rahu': 50, 'Ketu': 230}
EXALT_SIGN = {p: int(d // 30) for p, d in DEEP_EXALT.items()}
DEBIL_SIGN = {p: (s + 6) % 12 for p, s in EXALT_SIGN.items()}
# Moolatrikona: (sign, from degree, to degree)
MOOLATRIKONA = {'Sun': (4, 0, 20), 'Moon': (1, 4, 30), 'Mars': (0, 0, 12), 'Mercury': (5, 16, 20),
                'Jupiter': (8, 0, 10), 'Venus': (6, 0, 15), 'Saturn': (10, 0, 20)}
OWN_SIGNS = {p: {s for s in range(12) if F.SIGN_LORD[s] == p} for p in SEVEN}
OWN_SIGNS['Rahu'] = {10}
OWN_SIGNS['Ketu'] = {7}

# Natural friendship (BPHS). Anything not listed as friend or enemy is neutral.
NAT_FRIENDS = {'Sun': {'Moon', 'Mars', 'Jupiter'}, 'Moon': {'Sun', 'Mercury'}, 'Mars': {'Sun', 'Moon', 'Jupiter'},
               'Mercury': {'Sun', 'Venus'}, 'Jupiter': {'Sun', 'Moon', 'Mars'}, 'Venus': {'Mercury', 'Saturn'},
               'Saturn': {'Mercury', 'Venus'}}
NAT_ENEMIES = {'Sun': {'Venus', 'Saturn'}, 'Moon': set(), 'Mars': {'Mercury'}, 'Mercury': {'Moon'},
               'Jupiter': {'Mercury', 'Venus'}, 'Venus': {'Sun', 'Moon'}, 'Saturn': {'Sun', 'Moon', 'Mars'}}
FRIENDSHIP_OF = {**{p: p for p in SEVEN}, 'Rahu': 'Saturn', 'Ketu': 'Mars'}

DIGNITY_SCORE = {'exalted': 5, 'moolatrikona': 4, 'own': 3.5, 'great_friend': 3, 'friend': 2, 'neutral': 1,
                 'enemy': 0, 'great_enemy': -1, 'debilitated': -2}
COMBUST_ORB = {'Moon': 12, 'Mars': 17, 'Mercury': 14, 'Jupiter': 11, 'Venus': 10, 'Saturn': 15}
COMBUST_ORB_RETRO = {'Mercury': 12, 'Venus': 8}
MEAN_SPEED = {'Sun': 0.9856, 'Moon': 13.176, 'Mercury': 0.9856, 'Venus': 0.9856, 'Mars': 0.524, 'Jupiter': 0.0831,
              'Saturn': 0.0335, 'Rahu': -0.0530, 'Ketu': -0.0530}
# Directional strength is full at: Jupiter, Mercury east (Asc); Sun, Mars south (MC); Saturn west (Desc); Moon, Venus
# north (IC). Offsets from the Ascendant degree (MC approximated as Asc - 90 in whole-sign terms).
DIG_POINT_OFFSET = {'Jupiter': 0, 'Mercury': 0, 'Sun': 270, 'Mars': 270, 'Saturn': 180, 'Moon': 90, 'Venus': 90}
DAY_STRONG = {'Sun', 'Jupiter', 'Venus'}
NIGHT_STRONG = {'Moon', 'Mars', 'Saturn'}
CHALDEAN = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon']
WEEKDAY_LORD = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']   # Sunday..Saturday
MALEFICS = {'Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'}

PLANET_FEATURES = [
    'd1_dignity', 'd9_dignity', 'vargottama', 'exalted', 'debilitated', 'own_or_mt', 'friendly_sign', 'enemy_sign',
    'uchcha', 'dig', 'paksha', 'nathonnatha', 'speed_ratio', 'retro', 'cheshta', 'declination', 'ishta', 'kashta',
    'combust', 'war', 'baladi', 'benefic_aspects', 'malefic_aspects', 'benefic_conj', 'malefic_conj',
    'rules_trikona', 'rules_dusthana', 'rules_kendra', 'yogakaraka', 'house_from_lagna', 'house_from_moon',
    'vara_lord', 'hora_lord',
    # full Shadbala precomputed in the source database (Sun..Saturn; NaN otherwise)
    'sb_sthana', 'sb_dig', 'sb_kala', 'sb_chesta', 'sb_naisargika', 'sb_drik', 'sb_total',
]
NP = len(PLANET_FEATURES)
SHADBALA_COLS = ['sthana_bala', 'dig_bala', 'kala_bala', 'chesta_bala', 'naisargika_bala', 'drik_bala', 'total']
_SHADBALA: dict | None = None


def shadbala_table(source=None) -> dict:
    """{name: {planet: [7 values]}} from the source database's `shadbala` table (loaded once)."""
    global _SHADBALA
    if _SHADBALA is None:
        import sqlite3
        from src.preprocessing import SOURCE_DB
        _SHADBALA = {}
        try:
            with sqlite3.connect(f"file:{source or SOURCE_DB}?mode=ro", uri=True) as c:
                for row in c.execute(f"SELECT name, planet, {', '.join(SHADBALA_COLS)} FROM shadbala"):
                    _SHADBALA.setdefault(row[0], {})[row[1]] = [math.nan if v is None else float(v) for v in row[2:]]
        except Exception:
            pass   # no table / no database (e.g. unit tests): features stay NaN
    return _SHADBALA


def _sign(lon: float) -> int:
    return int((lon % 360) // 30)


def _dist(a: float, b: float) -> float:
    return abs(((a - b) + 180) % 360 - 180)


def natural_relation(p: str, q: str) -> str:
    f = FRIENDSHIP_OF[p]
    if q == f or q in NAT_FRIENDS[f]:
        return 'friend'
    return 'enemy' if q in NAT_ENEMIES[f] else 'neutral'


def compound_relation(p: str, q: str, p_sign: int, q_sign: int) -> str:
    """Panchadha maitri: natural + temporal (q in houses 2,3,4,10,11,12 from p = temporal friend)."""
    nat = natural_relation(p, q)
    temporal_friend = ((q_sign - p_sign) % 12 + 1) in (2, 3, 4, 10, 11, 12)
    table = {('friend', True): 'great_friend', ('friend', False): 'neutral', ('neutral', True): 'friend',
             ('neutral', False): 'enemy', ('enemy', True): 'neutral', ('enemy', False): 'great_enemy'}
    return table[(nat, temporal_friend)]


def dignity(p: str, lon: float, signs: dict | None = None) -> str:
    """Dignity class of planet p at sidereal longitude lon. With `signs` (planet -> sign) the friendship is compound
    (natal); without, natural only (transits, divisional charts)."""
    s, deg = _sign(lon), lon % 30
    if s == EXALT_SIGN[p]:
        return 'exalted'
    if s == DEBIL_SIGN[p]:
        return 'debilitated'
    mt = MOOLATRIKONA.get(p)
    if mt and s == mt[0] and mt[1] <= deg < mt[2]:
        return 'moolatrikona'
    if s in OWN_SIGNS[p]:
        return 'own'
    lord = F.SIGN_LORD[s]
    if signs is None:
        return natural_relation(p, lord)
    return compound_relation(p, lord, signs[p], signs[lord])


def uchcha_bala(p: str, lon: float) -> float:
    return (180 - _dist(lon, DEEP_EXALT[p])) / 3


def cheshta_proxy(retro: bool, ratio: float) -> float:
    if retro:
        return 60.0
    r = abs(ratio)
    return 45.0 if r < 0.2 else 30.0 if r < 0.8 else 15.0 if r <= 1.2 else 7.5


def baladi(sign: int, deg: float) -> float:
    """Potency by age state: infant .25, youth .5, adult 1, old .1, dead 0; reversed in even signs."""
    k = min(4, int(deg // 6))
    if sign % 2 == 1:      # even sign (Taurus, Cancer...): order reversed
        k = 4 - k
    return [0.25, 0.5, 1.0, 0.1, 0.0][k]


def _vara_hora(bjd: float, lat: float | None, lon: float | None) -> tuple[str | None, str | None]:
    """Weekday lord (from the sunrise before birth) and planetary-hour lord at birth. None if unavailable."""
    if lat is None or lon is None:
        return None, None
    swe, _ = F._swe()
    geo = (lon, lat, 0.0)

    def rise_set(start: float, which: int) -> float | None:
        try:
            res = swe.rise_trans(start, swe.SUN, which, geo, 0, 0, swe.FLG_MOSEPH)
            t = res[1][0]
            return t if res[0] == 0 and t > 0 else None
        except Exception:
            return None
    sunrise = rise_set(bjd - 1.0, swe.CALC_RISE)
    if sunrise is None:
        return None, None
    while True:
        nxt = rise_set(sunrise + 0.01, swe.CALC_RISE)
        if nxt is None or nxt > bjd:
            break
        sunrise = nxt
    sunset = rise_set(sunrise + 0.01, swe.CALC_SET)
    next_rise = rise_set(sunrise + 0.01, swe.CALC_RISE)
    if sunset is None or next_rise is None:
        return None, None
    local_day = math.floor(sunrise + 0.5 + lon / 360.0)
    vara = WEEKDAY_LORD[int((local_day + 1) % 7)]
    if bjd < sunset:
        idx = int((bjd - sunrise) / ((sunset - sunrise) / 12))
    else:
        idx = 12 + int((bjd - sunset) / ((next_rise - sunset) / 12))
    hora = CHALDEAN[(CHALDEAN.index(vara) + min(23, max(0, idx))) % 7]
    return vara, hora


def natal_strength(s: dict) -> dict:
    """{planet: np.array(NP)} plus helpers, for one person (needs a known Ascendant)."""
    swe, flags = F._swe()
    nat = s['natal']
    lon = {p: float(nat[NATAL.index(p)]) for p in ('Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu')}
    lon['Ketu'] = (lon['Rahu'] + 180) % 360
    asc = float(nat[NATAL.index('Ascendant')])
    lagna, bjd = _sign(asc), s['birth_jd']
    signs = {p: _sign(v) for p, v in lon.items()}
    moon_sign = signs['Moon']
    ids = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS, 'Mars': swe.MARS,
           'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE}
    speed, decl = {}, {}
    for p, i in ids.items():
        speed[p] = swe.calc_ut(bjd, i, flags | swe.FLG_SPEED)[0][3]
        decl[p] = swe.calc_ut(bjd, i, swe.FLG_MOSEPH | swe.FLG_EQUATORIAL)[0][1]
    speed['Ketu'], decl['Ketu'] = speed['Rahu'], -decl['Rahu']
    elong = (lon['Moon'] - lon['Sun']) % 360
    paksha_raw = (elong if elong <= 180 else 360 - elong) / 3
    waxing = elong < 180
    benefic = {p: p in ('Jupiter', 'Venus', 'Mercury') or (p == 'Moon' and waxing) for p in GRAHAS}
    day_birth = ((lon['Sun'] - asc) % 360) > 180
    vara, hora = _vara_hora(bjd, s.get('lat'), s.get('lon'))
    sb = shadbala_table().get(s.get('name'), {}) if s.get('name') else {}
    out = {}
    for p in GRAHAS:
        L, sg = lon[p], signs[p]
        d1 = dignity(p, L, signs)
        d9 = dignity(p, (F.d9_sign(L) * 30 + 15))   # sign-level navamsa dignity, natural friendship
        retro = speed[p] < 0 if p not in ('Rahu', 'Ketu') else False
        ratio = speed[p] / MEAN_SPEED[p]
        uch = uchcha_bala(p, L)
        chesta = cheshta_proxy(retro, ratio)
        dig = (180 - _dist(L, asc + DIG_POINT_OFFSET[p])) / 3 if p in DIG_POINT_OFFSET else 30.0
        paksha = paksha_raw if benefic[p] else 60 - paksha_raw
        nath = 60.0 if p == 'Mercury' else (60.0 if (p in DAY_STRONG) == day_birth else 0.0) if p in SEVEN else 30.0
        orb = COMBUST_ORB_RETRO.get(p, COMBUST_ORB.get(p)) if retro else COMBUST_ORB.get(p)
        combust = bool(orb) and _dist(L, lon['Sun']) <= orb
        war = p in ('Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn') and any(
            q != p and _dist(L, lon[q]) <= 1.0 for q in ('Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'))
        aspecting = [q for q in GRAHAS if q != p and signs[q] != sg and R.aspects(q, signs[q], sg)]
        conj = [q for q in GRAHAS if q != p and signs[q] == sg]
        ruled = [h for h in range(1, 13) if F.SIGN_LORD[(lagna + h - 1) % 12] == p] if p in SEVEN else []
        rk = any(h in (1, 4, 7, 10) for h in ruled)
        out[p] = np.array([
            DIGNITY_SCORE[d1], DIGNITY_SCORE[d9], float(F.d9_sign(L) == sg), float(d1 == 'exalted'),
            float(d1 == 'debilitated'), float(d1 in ('own', 'moolatrikona')), float(d1 in ('friend', 'great_friend')),
            float(d1 in ('enemy', 'great_enemy')), uch, dig, paksha, nath, ratio, float(retro), chesta, decl[p],
            math.sqrt(max(0.0, uch * chesta)), math.sqrt(max(0.0, (60 - uch) * (60 - chesta))),
            float(combust), float(war), baladi(sg, L % 30),
            sum(benefic[q] for q in aspecting), sum(not benefic[q] for q in aspecting),
            sum(benefic[q] for q in conj), sum(not benefic[q] for q in conj),
            float(any(h in (1, 5, 9) for h in ruled)), float(any(h in (6, 8, 12) for h in ruled)), float(rk),
            float(any(h in (4, 7, 10) for h in ruled) and any(h in (5, 9) for h in ruled)),
            float((sg - lagna) % 12 + 1), float((sg - moon_sign) % 12 + 1),
            float(vara == p), float(hora == p),
            *sb.get(p, [math.nan] * len(SHADBALA_COLS)),
        ], dtype=np.float32)
    return {'vec': out, 'lon': lon, 'signs': signs, 'lagna': lagna, 'asc': asc, 'bjd': bjd, 'benefic': benefic}


# ── Date-varying features ────────────────────────────────────────────────────

SLOTS = ['vim_md', 'vim_ad', 'vim_pd', 'yog_md', 'yog_ad', 'chara_ad_lord', 'year_lord', 'muntha_lord', 'mudda_lord',
         'bcp_lord']
# For these the planet is chosen by age (profected / Muntha / Bhrigu Chakra house), so anything about which houses it
# rules is partly an age clock: one ruled house IS the age-determined house. Their houses-ruled mask and lordship
# flags are dropped; strength, dignity and occupied house stay.
AGE_CYCLE_SLOTS = {'year_lord', 'muntha_lord', 'bcp_lord'}
LORDSHIP_FLAGS = ['rules_trikona', 'rules_dusthana', 'rules_kendra', 'yogakaraka']
_KEEP_AGE_CYCLE = np.array([i for i, f in enumerate(PLANET_FEATURES) if f not in LORDSHIP_FLAGS])
TRANSIT = ['Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu']


def _slot_names() -> list[str]:
    names = []
    for slot in SLOTS:
        names += [f'{slot} {f}' for f in PLANET_FEATURES if slot not in AGE_CYCLE_SLOTS or f not in LORDSHIP_FLAGS]
        if slot not in AGE_CYCLE_SLOTS:
            names += [f'{slot} rules house {h}' for h in range(1, 13)]
        names += [f'{slot} occupies house {h}' for h in range(1, 13)]
    names += [f'transit {p} {f}' for p in TRANSIT for f in ('dignity', 'retro', 'combust')]
    return names


STRENGTH_NAMES = _slot_names()
N_STRENGTH = len(STRENGTH_NAMES)


def _transit_conditions(jd: float) -> np.ndarray:
    swe, flags = F._swe()
    ids = {'Sun': swe.SUN, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
           'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE}
    pos = {p: swe.calc_ut(jd, i, flags | swe.FLG_SPEED)[0] for p, i in ids.items()}
    out = []
    for p in TRANSIT:
        L, sp = pos[p][0], pos[p][3]
        retro = sp < 0 and p != 'Rahu'
        orb = COMBUST_ORB_RETRO.get(p, COMBUST_ORB.get(p)) if retro else COMBUST_ORB.get(p)
        out += [DIGNITY_SCORE[dignity(p, L)], float(retro), float(bool(orb) and _dist(L, pos['Sun'][0]) <= orb)]
    return np.array(out, dtype=np.float32)


class StrengthFeaturizer(Mo.Featurizer):
    """706 existing features + activated-planet strength profiles + transit conditions (float32)."""
    name = 'full+strength-v1'
    n = F.N_FEATURES + N_STRENGTH
    dtype = np.float32

    def context(self, s: dict) -> dict:
        base = F.person_context(s)
        st = natal_strength(s)
        moon = st['lon']['Moon']
        return {'base': base, 'st': st, 'moon': moon, 'chara': base['chara'], 'mudda': {}}

    def _mudda(self, ctx: dict, jd: float) -> str:
        bjd, sun = ctx['st']['bjd'], ctx['st']['lon']['Sun']
        k = max(0, int((jd - bjd) / 365.2564))
        if k not in ctx['mudda']:
            ctx['mudda'][k] = (F.solar_return(sun, bjd, k), F.solar_return(sun, bjd, k + 1))
        start, nxt = ctx['mudda'][k]
        if start > jd and k > 0:
            k -= 1
            if k not in ctx['mudda']:
                ctx['mudda'][k] = (F.solar_return(sun, bjd, k), F.solar_return(sun, bjd, k + 1))
            start, nxt = ctx['mudda'][k]
        frac = min(0.999999, max(0.0, (jd - start) / max(1.0, nxt - start)))
        return Me.mudda_lord(ctx['moon'], k, frac)

    def date_strength(self, ctx: dict, jd: float) -> np.ndarray:
        st = ctx['st']
        lagna, bjd = st['lagna'], st['bjd']
        md, ad, pd = (F.DASHA_LORDS[i] for i in F.vimshottari_at(ctx['moon'], bjd, jd))
        ymd, yad = (F.YOGINI_LORDS[i] for i in F.yogini_at(ctx['moon'], bjd, jd))
        cur = R.chara_rao(ctx['chara'], jd)
        chara_lord = F._chara_lord(cur[1], st['lon']) if cur else md
        age = int((jd - bjd) / 365.2425)
        year_lord = F.SIGN_LORD[(lagna + age) % 12]
        muntha_lord = F.SIGN_LORD[(lagna + max(0, int((jd - bjd) / 365.2564))) % 12]
        bcp_lord = F.SIGN_LORD[(lagna + ((max(1, age) - 1) % 12)) % 12]
        lords = [md, ad, pd, ymd, yad, chara_lord, year_lord, muntha_lord, self._mudda(ctx, jd), bcp_lord]
        parts = []
        for slot, lord in zip(SLOTS, lords):
            parts.append(st['vec'][lord] if slot not in AGE_CYCLE_SLOTS else st['vec'][lord][_KEEP_AGE_CYCLE])
            if slot not in AGE_CYCLE_SLOTS:
                rules = np.zeros(12, np.float32)
                for h in range(1, 13):
                    if F.SIGN_LORD[(lagna + h - 1) % 12] == lord:
                        rules[h - 1] = 1
                parts.append(rules)
            occ = np.zeros(12, np.float32)
            occ[(st['signs'][lord] - lagna) % 12] = 1
            parts.append(occ)
        parts.append(_transit_conditions(jd))
        return np.concatenate(parts)

    def features(self, ctx: dict, jd: float) -> np.ndarray:
        return np.concatenate([F.features(ctx['base'], jd).astype(np.float32), self.date_strength(ctx, jd)])


STRENGTH_COLUMNS = np.concatenate([Mo.DEFAULT_COLUMNS, F.N_FEATURES + np.arange(N_STRENGTH)])
