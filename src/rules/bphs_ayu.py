"""
src/rules/bphs_ayu.py — longevity per BPHS vol. 1 ch. 45 (G.C. Sharma tr., Sagar; book pp. 575-607).

pindayu(chart)      v. 4-13: planets give their full years (Sun 19, Moon 25, Mars 15, Mercury 12, Jupiter 15, Venus 21,
                    Saturn 20) at deep exaltation, half at deep debilitation, in proportion between (arc from the
                    exaltation point; arcs under 180 deg are taken from 360). Reductions (v. 9-11, notes p. 585: only the
                    largest applies): combust 1/2 (not Venus/Saturn); in an enemy's sign 1/3 (natural enmity, not when
                    retrograde); in the visible half from the 12th backwards: malefic 1, 1/2, 1/3, 1/4, 1/5, 1/6 of its
                    years in the 12th..7th, benefic half of that, only the strongest of several in a house. The Lagna
                    adds its sign number + proportional fraction (v. 14-15, notes p. 586: Aries = 0). Krooda-udaya
                    harana (malefic in the Lagna, v. 12-13) is not applied (logged). Houses are whole-sign (the book's
                    example uses bhava cusps - logged).
ayu_class(chart)    v. 33-40: pairs (Lagna lord, 8th lord), (Saturn, Moon), (Lagna, Hora Lagna): both movable, or fixed
                    and dual -> long; movable+fixed or both dual -> medium; movable+dual or both fixed -> short. The span
                    found by two or three pairs is taken; if all differ, the Lagna/Hora pair, unless the Moon is in the
                    1st or 7th, then the Saturn/Moon pair. Spans (ch. 46 v. 10-14): short to 32, medium 32-64, long
                    64-100, full beyond.
"""
from __future__ import annotations

from src.rules import bphs_core as BC

FULL = {'Sun': 19, 'Moon': 25, 'Mars': 15, 'Mercury': 12, 'Jupiter': 15, 'Venus': 21, 'Saturn': 20}
SEVEN = list(FULL)
MOVABLE, FIXED, DUAL = {0, 3, 6, 9}, {1, 4, 7, 10}, {2, 5, 8, 11}
SPAN = {'short': (0, 32), 'medium': (32, 64), 'long': (64, 100)}


def raw_pinda(p: str, lon: float) -> float:
    r = (lon - (BC.EXALT_SIGN[p] * 30 + BC.DEEP_DEG[p])) % 360
    if r < 180:
        r = 360 - r
    return FULL[p] * r / 360


def pindayu(c) -> dict:
    out = {}
    by_house: dict[int, list[str]] = {}
    for p in SEVEN:
        by_house.setdefault(c.house_of(p), []).append(p)
    strongest = {h: max(ps, key=lambda q: c.shadbala[q]['total']) for h, ps in by_house.items()}
    vis_frac = {12: 1, 11: 1 / 2, 10: 1 / 3, 9: 1 / 4, 8: 1 / 5, 7: 1 / 6}
    for p in SEVEN:
        y = raw_pinda(p, c.lon[p])
        cuts = [0.0]
        if c.combust[p] and p not in ('Venus', 'Saturn'):
            cuts.append(y / 2)
        retro = c.st['vec'][p][__import__('src.strength', fromlist=['PLANET_FEATURES']).PLANET_FEATURES.index('retro')]
        if BC.natural(p, __import__('src.features', fromlist=['SIGN_LORD']).SIGN_LORD[c.signs[p]]) == 'enemy' and not retro:
            cuts.append(y / 3)
        h = c.house_of(p)
        if h in vis_frac and strongest.get(h) == p:
            f = vis_frac[h] * (0.5 if p in c.benefics else 1)
            cuts.append(y * f)
        out[p] = y - max(cuts)
    out['Lagna'] = (c.st['asc'] % 360) / 30
    out['total'] = sum(v for k, v in out.items())
    return out


def _cls(a: int, b: int) -> str:
    s = {('M', 'M'): 'long', ('F', 'D'): 'long', ('D', 'F'): 'long', ('M', 'F'): 'medium', ('F', 'M'): 'medium',
         ('D', 'D'): 'medium', ('M', 'D'): 'short', ('D', 'M'): 'short', ('F', 'F'): 'short'}
    k = lambda x: 'M' if x in MOVABLE else 'F' if x in FIXED else 'D'
    return s[(k(a), k(b))]


def hora_lagna(c) -> int | None:
    """Ch. 6 notes: ghatis from sunrise x 2/5 sign added to the Sun's longitude (12 deg per ghati)."""
    d = c.day
    if d is None:
        return None
    ghatis = (c.bjd - d['sunrise']) * 60
    return int(((c.lon['Sun'] + ghatis * 12) % 360) // 30)


def ayu_class(c) -> str | None:
    pairs = [_cls(c.signs[c.lord(1)], c.signs[c.lord(8)]), _cls(c.signs['Saturn'], c.signs['Moon'])]
    hl = hora_lagna(c)
    if hl is not None:
        pairs.append(_cls(c.lagna, hl))
    for cls in ('long', 'medium', 'short'):
        if pairs.count(cls) >= 2:
            return cls
    if len(pairs) < 3:
        return None
    return pairs[1] if c.house_of('Moon') in (1, 7) else pairs[2]
