"""
src/rules/bphs_strength.py — Shadbala as BPHS vol. 1 ch. 29 gives it (G.C. Sharma tr., Sagar; book pp. 385-414).
All values in virupas (60 = 1 rupa). shadbala(chart) -> {planet: {component: value, ..., 'total': v, 'ratio': v/need}}.

Sthana:  uchcha (v. 1: distance from deep debilitation / 3); saptavargaja (v. 2-4: in D1, D2, D3, D7, D9, D12, D30 -
         moolatrikona 45, own 30, great friend 20, friend 15, neutral 10, enemy 4, great enemy 2; moolatrikona only in
         the rashi, compound friendship from the natal positions); ojayugma (v. 4.5: Moon/Venus in even sign and even
         navamsa, others odd: 15 each); kendradi (v. 5: 60/30/15); drekkana (v. 6: male Sun/Mars/Jupiter 1st, neuter
         Mercury/Saturn 2nd, female Moon/Venus 3rd decanate: 15).
Dig:     v. 7: distance from the 4th (Sun, Mars), 7th (Jupiter, Mercury), 10th (Venus, Moon), Lagna (Saturn) cusp,
         folded, / 3 (equal houses from the Lagna degree).
Kala:    natonnata (v. 8-9: Sun, Jupiter, Venus 2 x ghatis from midnight; Moon, Mars, Saturn 60 minus that; Mercury
         60), paksha (v. 10-11: Moon-Sun elongation folded / 3 for benefics, 60 minus for malefics), tribhaga (v. 12),
         dina and hora lords (v. 13: 45, 60), ayana (v. 15-17 notes formula: (23deg27' +/- declination) / 46deg54' x 60;
         north adds for Sun, Mars, Jupiter, Venus, south for Saturn, Moon; Mercury always adds; the Sun's doubled).
Cheshta: v. 18: Sun = its ayana bala, Moon = its paksha bala; Mars-Saturn by motion class (v. 21-23: vakra 60,
         anuvakra 30, vikala 15, manda 15, mandatara 7.5, sama 30, chara 45, atichara 30) - classes from the daily
         speed against the mean speed (thresholds are the engine's, logged).
Naisargika: v. 14: Sun 60, Moon 51.43, Venus 42.86, Jupiter 34.29, Mercury 25.71, Mars 17.14, Saturn 8.57.
Drik:    v. 19: + 1/4 of benefic and - 1/4 of malefic sphuta drishti; Mercury's and Jupiter's drishti added in full.
Required totals (v. 32-33): Sun 390, Moon 360, Mars 300, Mercury 420, Jupiter 390, Venus 330, Saturn 300.
NOT computed (logged): varsha and masa lords (need the Surya Siddhanta ahargana; the book's table is abbreviated),
planetary war (v. 20), Bhava bala (v. 26-31).
"""
from __future__ import annotations

from src import features as F
from src.rules import bphs_core as BC

SEVEN = BC.SEVEN
NEED = {'Sun': 390, 'Moon': 360, 'Mars': 300, 'Mercury': 420, 'Jupiter': 390, 'Venus': 330, 'Saturn': 300}
NAISARGIKA = {'Sun': 60, 'Moon': 51.43, 'Venus': 42.86, 'Jupiter': 34.29, 'Mercury': 25.71, 'Mars': 17.14, 'Saturn': 8.57}
VARGA_PTS = {'moolatrikona': 45, 'own': 30, 'exalted': 30, 'great_friend': 20, 'friend': 15, 'neutral': 10,
             'enemy': 4, 'great_enemy': 2, 'debilitated': 2}
MEAN_SPEED = {'Mars': 0.524, 'Mercury': 0.9856, 'Jupiter': 0.0831, 'Venus': 0.9856, 'Saturn': 0.0335}
DIG_HOUSE = {'Sun': 4, 'Mars': 4, 'Jupiter': 7, 'Mercury': 7, 'Venus': 10, 'Moon': 10, 'Saturn': 1}
MALE, NEUTER = {'Sun', 'Mars', 'Jupiter'}, {'Mercury', 'Saturn'}
ODD_SIGN = lambda s: s % 2 == 0          # Aries (0) is odd


def _sign(x):
    return int((x % 360) // 30)


def hora(lon):                           # vol. 1 ch. 7: odd sign 1st half Sun (Leo), 2nd Moon (Cancer); even reversed
    s, d = _sign(lon), lon % 30
    first = d < 15
    return 4 if (ODD_SIGN(s) == first) else 3


def drekkana(lon):
    s, d = _sign(lon), lon % 30
    return (s + 4 * int(d // 10)) % 12


def trimsamsa(lon):                      # odd: Mars 5, Saturn 5, Jupiter 8, Mercury 7, Venus 5 -> Ar Aq Sg Ge Li
    s, d = _sign(lon), lon % 30
    if ODD_SIGN(s):
        for lim, sign in ((5, 0), (10, 10), (18, 8), (25, 2), (30, 6)):
            if d < lim:
                return sign
    for lim, sign in ((5, 1), (12, 5), (20, 11), (25, 9), (30, 7)):
        if d < lim:
            return sign
    return s


VARGA = {'D1': lambda x: _sign(x), 'D2': hora, 'D3': drekkana, 'D7': lambda x: _d7(x), 'D9': F.d9_sign,
         'D12': lambda x: (_sign(x) + int((x % 30) // 2.5)) % 12, 'D30': trimsamsa}


def _d7(x):
    s, part = _sign(x), int((x % 30) // (30 / 7))
    return ((s if s % 2 == 0 else (s + 6) % 12) + part) % 12


def _varga_dignity(p, vsign, natal_signs, rashi_lon=None):
    if rashi_lon is not None:
        return BC.dignity(p, rashi_lon, natal_signs)
    if vsign in BC.OWN_SIGNS[p]:
        return 'own'
    lord = F.SIGN_LORD[vsign]
    return BC.compound(p, lord, natal_signs[p], natal_signs[lord])


def shadbala(c) -> dict[str, dict]:
    """c: src.rules.engine.Chart."""
    swe, flags = F._swe()
    lon, signs = c.lon, {p: c.signs[p] for p in SEVEN}
    asc = c.st['asc'] % 360
    day = c.day
    ids = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS, 'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
           'Venus': swe.VENUS, 'Saturn': swe.SATURN}
    speed = {p: swe.calc_ut(c.bjd, i, flags | swe.FLG_SPEED)[0][3] for p, i in ids.items()}
    decl = {p: swe.calc_ut(c.bjd, i, swe.FLG_MOSEPH | swe.FLG_EQUATORIAL)[0][1] for p, i in ids.items()}
    elong = (lon['Moon'] - lon['Sun']) % 360
    elong_f = elong if elong <= 180 else 360 - elong
    out = {}
    for p in SEVEN:
        r = {}
        d = (lon[p] - (BC.EXALT_SIGN[p] * 30 + BC.DEEP_DEG[p] + 180)) % 360
        r['uchcha'] = (d if d <= 180 else 360 - d) / 3
        sv = 0.0
        for name, fn in VARGA.items():
            vs = fn(lon[p])
            dig = _varga_dignity(p, vs, signs, lon[p] if name == 'D1' else None)
            if name != 'D1' and dig == 'moolatrikona':
                dig = 'own'
            sv += VARGA_PTS.get(dig, 10)
        r['saptavargaja'] = sv
        fem = p in ('Moon', 'Venus')
        r['ojayugma'] = 15 * ((not ODD_SIGN(signs[p])) == fem) + 15 * ((not ODD_SIGN(F.d9_sign(lon[p]))) == fem)
        h = (signs[p] - c.lagna) % 12 + 1
        r['kendradi'] = 60 if h in (1, 4, 7, 10) else 30 if h in (2, 5, 8, 11) else 15
        dk = int((lon[p] % 30) // 10)
        r['drekkana'] = 15 if dk == (0 if p in MALE else 1 if p in NEUTER else 2) else 0
        cusp = (asc + (DIG_HOUSE[p] - 1) * 30) % 360
        dd = abs(((lon[p] - cusp) + 180) % 360 - 180)
        r['dig'] = (180 - dd) / 3
        # kala
        if day is not None:
            noon = (day['sunrise'] + day['sunset']) / 2 if day['day_birth'] else None
            if day['day_birth']:
                hrs_from_noon = abs(c.bjd - noon) * 24
            else:
                midnight = (day['sunset'] + day['next_sunrise']) / 2
                hrs_from_noon = 12 - abs(c.bjd - midnight) * 24
            unnata = max(0.0, (12 - hrs_from_noon) * 2.5)        # ghatis from midnight, 0-30
            dayb = min(60.0, 2 * unnata)
            r['natonnata'] = 60 if p == 'Mercury' else dayb if p in ('Sun', 'Jupiter', 'Venus') else 60 - dayb
            if day['day_birth']:
                third = int(3 * (c.bjd - day['sunrise']) / (day['sunset'] - day['sunrise']))
                lord3 = ['Mercury', 'Sun', 'Saturn'][min(third, 2)]
            else:
                third = int(3 * (c.bjd - day['sunset']) / (day['next_sunrise'] - day['sunset']))
                lord3 = ['Moon', 'Venus', 'Mars'][min(third, 2)]
            r['tribhaga'] = 60 if p in ('Jupiter', lord3) else 0
            r['dina'] = 45 if p == day['weekday_lord'] else 0
            hours = int((c.bjd - day['sunrise']) * 24)
            chaldean = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon']
            hl = chaldean[(chaldean.index(day['weekday_lord']) + hours) % 7]
            r['hora'] = 60 if p == hl else 0
        else:
            r.update(natonnata=0, tribhaga=60 if p == 'Jupiter' else 0, dina=0, hora=0)
        ben = p in c.benefics
        r['paksha'] = elong_f / 3 if ben else 60 - elong_f / 3
        north = decl[p] >= 0
        adds = True if p == 'Mercury' else (north if p in ('Sun', 'Mars', 'Jupiter', 'Venus') else not north)
        ay = (23.45 + (abs(decl[p]) if adds else -abs(decl[p]))) / 46.9 * 60
        r['ayana'] = 2 * ay if p == 'Sun' else ay
        # cheshta
        if p == 'Sun':
            r['cheshta'] = r['ayana']
        elif p == 'Moon':
            r['cheshta'] = r['paksha']
        else:
            v, m = speed[p], MEAN_SPEED[p]
            if v < 0:
                r['cheshta'] = 60
            elif v < 0.05 * m:
                r['cheshta'] = 15                  # vikala (stationary)
            elif v < 0.5 * m:
                r['cheshta'] = 7.5                 # mandatara
            elif v < 0.9 * m:
                r['cheshta'] = 15                  # manda
            elif v <= 1.1 * m:
                r['cheshta'] = 30                  # sama
            elif v <= 1.5 * m:
                r['cheshta'] = 45                  # chara
            else:
                r['cheshta'] = 30                  # atichara
        r['naisargika'] = NAISARGIKA[p]
        drik = 0.0
        for q in SEVEN:
            if q == p:
                continue
            dv = BC.drishti(q, lon[q], lon[p])
            drik += dv if q in ('Jupiter', 'Mercury') else (dv / 4 if q in c.benefics else -dv / 4)
        r['drik'] = drik
        r['total'] = sum(v for k, v in r.items() if k not in ('ishta', 'kashta'))
        # vol. 1 ch. 30 v. 2-6: (uchcha rashmi - 1) x 10 = uchcha bala, (cheshta rashmi - 1) x 10 = cheshta bala;
        # ishta = their sum / 2, kashta = 60 - ishta
        r_ishta = (r['uchcha'] + r['cheshta']) / 2
        r['ratio'] = r['total'] / NEED[p]
        r['ishta'], r['kashta'] = r_ishta, 60 - r_ishta
        out[p] = r
    return out
