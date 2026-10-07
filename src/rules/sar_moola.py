"""
src/rules/sar_moola.py — Moola dasa after Saravali ch. 40-42 (R. Santhanam tr., vol. 2 pp. 699-724).

Dasa givers: the seven planets and the Lagna.
First dasa (ch. 41 v. 3-5, Satya): the strongest of the Lagna, the Sun and the Moon. Strength = Shadbala ratio; the
Lagna's strength is its lord's (ch. 5 v. 19-20, Chudamani). Then the givers in kendras, then panapharas, then apoklimas
(houses from the Lagna; the Lagna itself counts as a kendra), the strongest first within each group, ties by more years.
Years (ch. 41 v. 1 with ch. 40 v. 2-3): the longevity method chosen by the same strongest of the three -
  Lagna -> Amsayu (ch. 40 v. 4-12): navamsas traversed from Aries, twelves expunged (longitude in minutes / 200);
     x2 if vargottama, in own sign, own decanate or own navamsa; x3 if retrograde or exalted (both may apply, v. 7;
     Chudamani's limit by kendra/panaphara/apoklima, v. 8, not applied); enemy's sign: a third lost; combust: half lost
     (not Venus/Saturn); Chakrardha harana as in Pindayu (12th..7th: 1, 1/2 .. 1/6, benefics half); the Lagna gives its
     navamsas traversed and, when its lord is strong, adds the signs it has traversed (v. 5).
  Sun -> Pindayu (ch. 40 v. 13-19) as computed for BPHS ch. 45 (src/rules/bphs_ayu.pindayu: same table and arithmetic).
  Moon -> Nisargayu (ch. 40 v. 20): Sun 20, Moon 1, Mars 2, Mercury 9, Jupiter 18, Venus 20, Saturn 50; the Lagna 0
     (no years given; it then has no dasa).
The sequence repeats when life outlasts it (not stated in the text - a choice, logged).
Sub periods (ch. 42 v. 1-5, the Brihat Jataka share method): within a dasa the lord itself takes 1 share (as in
Brihat Jataka 8; the text lists only the others), a planet with the lord 1/2, in the 5th/9th from it 1/3, in the 7th
1/7, in the 4th/8th 1/4; if several planets share such a place only the strongest counts (v. 2); planets elsewhere take
no sub period. Order: the lord first, then by strength (Satya, v. 4). For the Lagna's dasa the reference is the Lagna.
"""
from __future__ import annotations

from src import features as F
from src import strength as S
from src.rules import bphs_core as BC
from src.rules import bphs_ayu as BA

SEVEN = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
NISARGA = {'Sun': 20, 'Moon': 1, 'Mars': 2, 'Mercury': 9, 'Jupiter': 18, 'Venus': 20, 'Saturn': 50, 'Lagna': 0}
YEAR = 365.2425


def _ratio(c, g):
    p = c.lord(1) if g == 'Lagna' else g
    return c.shadbala[p]['ratio'] if p in c.shadbala else 0.0


def _retro(c, p):
    return p not in ('Sun', 'Moon') and bool(c.st['vec'][p][S.PLANET_FEATURES.index('retro')])


def amsayu(c) -> dict:
    out = {}
    by_house = {}
    for p in SEVEN:
        by_house.setdefault(c.house_of(p), []).append(p)
    strongest = {h: max(ps, key=lambda q: _ratio(c, q)) for h, ps in by_house.items()}
    vis = {12: 1, 11: 1 / 2, 10: 1 / 3, 9: 1 / 4, 8: 1 / 5, 7: 1 / 6}
    d9 = c.varga['D9'][0]
    for p in SEVEN:
        lon = c.lon[p] % 360
        y = (lon * 60 / 200) % 12
        own_sign = F.SIGN_LORD[c.signs[p]] == p
        drek = (c.signs[p] + 4 * int((lon % 30) // 10)) % 12
        if c.dig[p] in ('own', 'moolatrikona') or own_sign or d9[p] == c.signs[p] or F.SIGN_LORD[d9[p]] == p or F.SIGN_LORD[drek] == p:
            y *= 2
        if _retro(c, p) or c.dig[p] == 'exalted':
            y *= 3
        if BC.natural(p, F.SIGN_LORD[c.signs[p]]) == 'enemy':
            y -= y / 3
        if c.combust[p] and p not in ('Venus', 'Saturn'):
            y -= y / 2
        h = c.house_of(p)
        if h in vis and strongest.get(h) == p:
            y -= y * vis[h] * (0.5 if p in c.benefics else 1)
        out[p] = y
    asc = c.st['asc'] % 360
    out['Lagna'] = (asc * 60 / 200) % 12 + (int(asc // 30) if _ratio(c, 'Lagna') >= 1 else 0)
    return out


def years(c) -> tuple[str, dict]:
    first = max(['Lagna', 'Sun', 'Moon'], key=lambda g: _ratio(c, g))
    if first == 'Lagna':
        return first, amsayu(c)
    if first == 'Sun':
        pin = BA.pindayu(c)
        return first, {g: pin[g] for g in SEVEN + ['Lagna']}
    return first, dict(NISARGA)


def order(c, first: str, yrs: dict) -> list[str]:
    def grp(g):
        h = 1 if g == 'Lagna' else c.house_of(g)
        return 0 if h in (1, 4, 7, 10) else 1 if h in (2, 5, 8, 11) else 2
    rest = [g for g in SEVEN + ['Lagna'] if g != first and yrs.get(g, 0) > 0]
    rest.sort(key=lambda g: (grp(g), -_ratio(c, g), -yrs[g]))
    return [first] + rest


def subs(c, lord: str) -> list[tuple[str, float]]:
    ref = c.lagna if lord == 'Lagna' else c.signs[lord]
    places = {1: 1 / 2, 5: 1 / 3, 9: 1 / 3, 7: 1 / 7, 4: 1 / 4, 8: 1 / 4}
    shares = {lord: 1.0}
    for k, f in places.items():
        cand = [p for p in SEVEN if p != lord and (c.signs[p] - ref) % 12 + 1 == k]
        if cand:
            shares[max(cand, key=lambda q: _ratio(c, q))] = f
    tot = sum(shares.values())
    ordered = [lord] + sorted((p for p in shares if p != lord), key=lambda q: -_ratio(c, q))
    return [(p, shares[p] / tot) for p in ordered]


def sequence(c) -> list[dict]:
    first, yrs = years(c)
    seq, t = [], c.bjd
    lords = order(c, first, yrs)
    total = sum(yrs[g] for g in lords)
    if total <= 0:
        return []
    while t < c.bjd + 130 * YEAR:
        for g in lords:
            span = yrs[g] * YEAR
            sub, s0 = [], t
            for p, share in subs(c, g):
                sub.append((p, s0, s0 + span * share))
                s0 += span * share
            seq.append({'lord': g, 'start': t, 'end': t + span, 'subs': sub})
            t += span
    return seq


def at(c, jd: float) -> dict:
    if not hasattr(c, '_moola'):
        c._moola = sequence(c)
    for d in c._moola:
        if d['start'] <= jd < d['end']:
            ad = next((p for p, a, b in d['subs'] if a <= jd < b), d['lord'])
            return {'MD': d['lord'], 'AD': ad, 'md_start': d['start'], 'md_end': d['end']}
    return {'MD': None, 'AD': None}
