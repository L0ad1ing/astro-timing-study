"""
src/rules/lilly.py — the nativity as William Lilly judges it in Christian Astrology Book III (1647), and the evaluation
of the 'w_l_' rule conditions of the Lilly rule set (src/rules/west.py hands every atom starting with 'w_l_' here).

Lilly's own apparatus, from Books I and III (page numbers of the 1647 edition):
- zodiac tropical; houses Regiomontanus (Lilly's practice throughout); a planet within 5 degrees before a cusp is of
  the force of that house (Book I; Book III p. 529 uses the same 5 degrees for the 8th);
- essential dignities after Ptolemy as tabled p. 104: domicile, exaltation, triplicity (Fire Sun/Jupiter, Earth
  Venus/Moon, Air Saturn/Mercury, Water Mars day and night), Ptolemy's terms, the Chaldean faces;
- the table of fortitudes and debilities p. 115 (essential 5/4/3/2/1, detriment -5, fall -4, peregrine -5; the
  accidental scores by house, motion, orientality, the Sun, the benefics/malefics partile, besieging and the stars
  Regulus, Spica, Algol);
- orbs p. 107: Saturn 10, Jupiter 12, Mars 7.5, Sun 17, Venus 8, Mercury 7, Moon 12.5; two planets are in aspect when
  within the sum of half their orbs (the moiety);
- the Part of Fortune: Ascendant + Moon - Sun, by day and night alike (Lilly's practice in his figures);
- combust within 8 deg 30', under the beams within 17 deg, cazimi within 17' (Book I p. 113);
- the Hyleg p. 527-529; the Lord of the Geniture p. 532; directions measured by Naibod's key, 0 deg 59' 08" of the
  equator for a year (p. 651 ff.); profections 30 degrees a year (p. 715 ff.); revolutions (p. 734 ff.); returns of
  the planets in the revolution (p. 738-741); transits (p. 741); the alfridaries (p. 712 ff.).

Construction choices (stated before any test, logged in docs/lilly_progress_log.md):
- aspects to a point that is not a planet (Ascendant, MC, cusps, the Part of Fortune, stars) use the planet's moiety;
- primary directions: Regiomontanus position circles (the 'circle of position' Lilly uses after Regiomontanus and
  Argol), direct motion only; promittors are the bodies with their latitude, their zodiacal aspects (sextile, square,
  trine each side, opposition) without latitude, the beginnings of the terms, the twelve cusps and the fixed stars
  Lilly names, all directed to the five significators Ascendant, MC, Sun, Moon and Part of Fortune; births at |lat|
  >= 66 deg get no directions;
- a direction 'operates' within half a year either side of the moment its arc measures (Lilly: the effect is felt
  about the time, sooner or later as other configurations concur);
- the solar revolution is erected for the place of birth;
- fixed stars: J2000 positions precessed in longitude at 50.29" a year (latitudes held constant).
"""
from __future__ import annotations

import functools
import math

import numpy as np
import swisseph as swe

from src.rules import west as W

SEVEN = W.SEVEN
SIGNS = W.SIGNS
DOMICILE = W.DOMICILE
EXALT = W.EXALT
BENEFICS, MALEFICS = ['Jupiter', 'Venus'], ['Saturn', 'Mars']
# Book I p. 104, Ptolemy's terms as Lilly tables them: (lord, end degree)
TERMS = [
    [('Jupiter', 6), ('Venus', 14), ('Mercury', 21), ('Mars', 26), ('Saturn', 30)],
    [('Venus', 8), ('Mercury', 15), ('Jupiter', 22), ('Saturn', 26), ('Mars', 30)],
    [('Mercury', 7), ('Jupiter', 14), ('Venus', 21), ('Saturn', 25), ('Mars', 30)],
    [('Mars', 6), ('Jupiter', 13), ('Mercury', 20), ('Venus', 27), ('Saturn', 30)],
    [('Saturn', 6), ('Mercury', 13), ('Venus', 19), ('Jupiter', 25), ('Mars', 30)],
    [('Mercury', 7), ('Venus', 13), ('Jupiter', 18), ('Saturn', 24), ('Mars', 30)],
    [('Saturn', 6), ('Venus', 11), ('Jupiter', 19), ('Mercury', 24), ('Mars', 30)],
    [('Mars', 6), ('Jupiter', 14), ('Venus', 21), ('Mercury', 27), ('Saturn', 30)],
    [('Jupiter', 8), ('Venus', 14), ('Mercury', 19), ('Saturn', 25), ('Mars', 30)],
    [('Venus', 6), ('Mercury', 12), ('Jupiter', 19), ('Mars', 25), ('Saturn', 30)],
    [('Saturn', 6), ('Mercury', 12), ('Venus', 20), ('Jupiter', 25), ('Mars', 30)],
    [('Venus', 8), ('Jupiter', 14), ('Mercury', 20), ('Mars', 26), ('Saturn', 30)],
]
CHALDEAN = ['Mars', 'Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter']   # faces from 0 Aries
TRIPL = {0: ('Sun', 'Jupiter'), 1: ('Venus', 'Moon'), 2: ('Saturn', 'Mercury'), 3: ('Mars', 'Mars')}
ORB = {'Saturn': 10, 'Jupiter': 12, 'Mars': 7.5, 'Sun': 17, 'Venus': 8, 'Mercury': 7, 'Moon': 12.5}
MEAN_MOTION = {'Saturn': 2 / 60 + 1 / 3600, 'Jupiter': 4 / 60 + 59 / 3600, 'Mars': 31 / 60 + 27 / 3600,
               'Sun': 59 / 60 + 8 / 3600, 'Venus': 59 / 60 + 8 / 3600, 'Mercury': 59 / 60 + 8 / 3600,
               'Moon': 13 + 10 / 60 + 36 / 3600}
ASPECTS = {'conj': 0, 'sextile': 60, 'square': 90, 'trine': 120, 'opp': 180}
import os as _os
# docs/prereg_full_programme.md T3 variants: LILLY_KEY=ptolemy (1 deg = 1 year), LILLY_DIR_WINDOW=1.0
NAIBOD = 1.0 if _os.environ.get('LILLY_KEY') == 'ptolemy' else 59 / 60 + 8 / 3600     # degrees of RA per year
DIR_WINDOW = float(_os.environ.get('LILLY_DIR_WINDOW', '0.5'))
MAX_ARC = 110.0
# fixed stars Lilly uses (J2000 ecliptic longitude, latitude)
STARS = {
    'Regulus': (149.83, 0.46), 'Spica': (203.84, -2.05), 'Algol': (56.17, 22.43), 'Aldebaran': (69.79, -5.47),
    'Antares': (249.76, -4.57), 'Pleiades': (60.00, 4.05), 'Hyades': (65.80, -5.75), 'Pollux': (113.22, 6.68),
    'Castor': (110.23, 10.09), 'Arcturus': (204.23, 30.73), 'Fomalhaut': (333.87, -21.13), 'Sirius': (104.08, -39.61),
    'Procyon': (115.79, -16.02), 'Praesepe': (127.33, 1.2), 'Vindemiatrix': (189.93, 16.2),
    'DenebAlgedi': (293.55, -2.6), 'Markab': (353.48, 19.4), 'Scheat': (359.37, 31.1), 'Alphard': (147.28, -22.4),
    'Bellatrix': (80.95, -16.8), 'Betelgeuse': (88.75, -16.0), 'Rigel': (76.83, -31.1), 'Vega': (285.32, 61.7),
    'Altair': (301.78, 29.3), 'Ascelli': (127.7, 0.0), 'Capella': (81.85, 22.86), 'OrionBelt': (83.47, -24.5),
    'Dolphin': (317.38, 33.0), 'Deneb': (335.33, 59.9), 'Alphecca': (222.30, 44.3),
}
FIXED, MOVABLE, COMMON = (1, 4, 7, 10), (0, 3, 6, 9), (2, 5, 8, 11)
ANGLES, SUCC, CADENT = (1, 4, 7, 10), (2, 5, 8, 11), (3, 6, 9, 12)
HOUSE_SCORE = {1: 5, 10: 5, 7: 4, 4: 4, 11: 4, 2: 3, 5: 3, 9: 2, 3: 1, 12: -5, 8: -2, 6: -2}


def _d(a, b):
    """Signed shortest difference b - a in (-180, 180]."""
    return (b - a + 180) % 360 - 180


def term_lord(lon: float) -> str:
    s, deg = int(lon // 30) % 12, lon % 30
    for lord, end in TERMS[s]:
        if deg < end:
            return lord
    return TERMS[s][-1][0]


def face_lord(lon: float) -> str:
    return CHALDEAN[int(lon // 10) % 36 % 7]


def star_lon(name: str, jd: float) -> float:
    lon, _ = STARS[name]
    return (lon + 50.29 / 3600 * (jd - 2451545.0) / 365.25) % 360


class LChart:
    def __init__(self, w: W.WChart):
        self.w = w
        jd, lat = w.pjd, w.lat
        self.bjd, self.pjd, self.lat = w.bjd, jd, lat
        self.eps = swe.calc_ut(jd, swe.ECL_NUT)[0][0]
        self.lon = {p: w.lon[p] for p in SEVEN + ['Node', 'Asc', 'MC']}
        self.lon['Tail'] = (w.lon['Node'] + 180) % 360
        self.lon['PF'] = (w.asc + w.lon['Moon'] - w.lon['Sun']) % 360
        self.speed = dict(w.speed)
        self.blat = {p: swe.calc_ut(jd, W.IDS[p], swe.FLG_MOSEPH)[0][1] for p in SEVEN}
        cusps, ascmc = swe.houses_ex(jd, lat, w.geo_lon, b'R')
        self.cusps = [c % 360 for c in cusps[:12]]
        self.armc = ascmc[2]
        for i, c in enumerate(self.cusps):
            self.lon[f'cusp:{i + 1}'] = c
        for s in STARS:
            self.lon[f'star:{s}'] = star_lon(s, jd)
        self.day = w.day

    # ── places ─────────────────────────────────────────────────────────────────────────────────
    def house_of(self, lon: float) -> int:
        """Regiomontanus house, a point within 5 deg before a cusp counted in that house."""
        x = (lon + 5) % 360
        best = 12
        for i in range(12):
            a, b = self.cusps[i], self.cusps[(i + 1) % 12]
            if (x - a) % 360 < (b - a) % 360:
                best = i + 1
                break
        return best

    def house(self, p: str) -> int:
        return self.house_of(self.lon[p])

    def sign(self, p: str) -> int:
        return int(self.lon[p] // 30) % 12

    def lord(self, n: int) -> str:
        return DOMICILE[int(self.cusps[n - 1] // 30) % 12]

    def above(self, p: str) -> bool:
        return self.house(p) in (7, 8, 9, 10, 11, 12)

    # ── dignity ────────────────────────────────────────────────────────────────────────────────
    def essential(self, p: str) -> set[str]:
        if p not in SEVEN:
            return set()
        lon, s, out = self.lon[p], self.sign(p), set()
        if DOMICILE[s] == p:
            out.add('domicile')
        if DOMICILE[(s + 6) % 12] == p:
            out.add('detriment')
        if EXALT[p] == s:
            out.add('exalted')
        if (EXALT[p] + 6) % 12 == s:
            out.add('fall')
        t = TRIPL[s % 4]
        if (t[0] if self.day else t[1]) == p:
            out.add('triplicity')
        if term_lord(lon) == p:
            out.add('term')
        if face_lord(lon) == p:
            out.add('face')
        if not out & {'domicile', 'exalted', 'triplicity', 'term', 'face'}:
            out.add('peregrine')
        q = DOMICILE[s]
        if q != p and DOMICILE[self.sign(q)] == p:
            out.add('reception')
        ex = next((k for k, v in EXALT.items() if v == s), None)
        if ex and ex != p and EXALT[p] == self.sign(ex):
            out.add('reception')
        return out

    def ess_score(self, p: str) -> int:
        e = self.essential(p)
        sc = {'domicile': 5, 'exalted': 4, 'triplicity': 3, 'term': 2, 'face': 1,
              'detriment': -5, 'fall': -4, 'peregrine': -5}
        v = sum(sc[k] for k in e if k in sc)
        if 'reception' in e and 'domicile' not in e:
            v += 5 if DOMICILE[self.sign(DOMICILE[self.sign(p)])] == p else 4
        return v

    def sun_dist(self, p: str) -> float:
        return abs(_d(self.lon[p], self.lon['Sun']))

    def accidental(self, p: str) -> set[str]:
        if p not in SEVEN:
            return set()
        out = set()
        h = self.house(p)
        out.add('angular' if h in ANGLES else 'succedent' if h in SUCC else 'cadent')
        out.add('above' if self.above(p) else 'below')
        sp = self.speed[p]
        out.add('retro' if sp < 0 else 'direct')
        out.add('swift' if abs(sp) > MEAN_MOTION[p] else 'slow')
        if p == 'Moon':
            inc = (self.lon['Moon'] - self.lon['Sun']) % 360 < 180
            out.add('increasing' if inc else 'decreasing')
            out.add('occidental' if inc else 'oriental')
        elif p != 'Sun':
            ori = 0 < (self.lon['Sun'] - self.lon[p]) % 360 < 180   # rises before the Sun
            out.add('oriental' if ori else 'occidental')
        if p != 'Sun':
            d = self.sun_dist(p)
            if d <= 17 / 60:
                out.add('cazimi')
            elif d <= 8.5:
                out.add('combust')
            elif d <= 17:
                out.add('under_beams')
            else:
                out.add('free')
            if self.besieged(p):
                out.add('besieged')
        return out

    def besieged(self, p: str) -> bool:
        """Between the bodies of Saturn and Mars (Book I p. 114): the nearer malefic on each side, within 15 deg."""
        a = [(_d(self.lon[p], self.lon[m])) for m in MALEFICS if m != p]
        if len(a) < 2:
            return False
        return (a[0] > 0) != (a[1] > 0) and all(abs(x) <= 15 for x in a)

    def acc_score(self, p: str) -> int:
        if p not in SEVEN:
            return 0
        a, v = self.accidental(p), HOUSE_SCORE[self.house(p)]
        if p not in ('Sun', 'Moon'):
            v += 4 if 'direct' in a else -5
        v += 2 if 'swift' in a else -2
        if p in ('Saturn', 'Jupiter', 'Mars'):
            v += 2 if 'oriental' in a else -2
        if p in ('Mercury', 'Venus'):
            v += 2 if 'occidental' in a else -2
        if p == 'Moon':
            v += 2 if 'increasing' in a else -2
        if p != 'Sun':
            v += {'free': 5, 'cazimi': 5, 'combust': -5, 'under_beams': -4}.get(
                next((k for k in ('cazimi', 'combust', 'under_beams', 'free') if k in a), 'free'), 0)
            if 'besieged' in a:
                v -= 5
        for q in SEVEN:
            if q == p:
                continue
            d = abs(_d(self.lon[p], self.lon[q]))
            good, bad = q in BENEFICS, q in MALEFICS
            if d < 1:
                v += 5 if good else -5 if bad else 0
            elif abs(d - 120) < 1:
                v += 4 if good else 0
            elif abs(d - 60) < 1:
                v += 3 if good else 0
            elif abs(d - 180) < 1:
                v += -4 if bad else 0
            elif abs(d - 90) < 1:
                v += -3 if bad else 0
        d = abs(_d(self.lon[p], self.lon['Node']))
        if d < 1:
            v += 4
        elif abs(d - 180) < 1:
            v -= 4
        if abs(_d(self.lon[p], self.lon['star:Regulus'])) < 1:
            v += 6
        if abs(_d(self.lon[p], self.lon['star:Spica'])) < 1:
            v += 5
        if abs(_d(self.lon[p], self.lon['star:Algol'])) <= 5:
            v -= 5
        return v

    def score(self, p: str) -> int:
        return self.ess_score(p) + self.acc_score(p)

    # ── aspects ────────────────────────────────────────────────────────────────────────────────
    def orb(self, p: str, q: str) -> float:
        op, oq = ORB.get(p), ORB.get(q)
        if op and oq:
            return (op + oq) / 2
        return (op or oq or 2.0) / 2

    def aspect(self, p: str, q: str) -> str | None:
        """Aspect within the moieties (p. 107); the nearest kind."""
        d = abs(_d(self.lon[p], self.lon[q]))
        o = self.orb(p, q)
        best = None
        for k, ang in ASPECTS.items():
            e = abs(d - ang)
            if e <= o and (best is None or e < best[1]):
                best = (k, e)
        return best[0] if best else None

    def partile(self, p: str, q: str) -> str | None:
        d = abs(_d(self.lon[p], self.lon[q]))
        for k, ang in ASPECTS.items():
            if abs(d - ang) < 1:
                return k
        return None

    # ── Hyleg, Lord of the Geniture ────────────────────────────────────────────────────────────
    def aphetic(self, p: str) -> bool:
        """p. 528: houses 1 (only within 25 deg after the degree ascending), 7, 9, 10, 11."""
        h = self.house(p)
        if h == 1:
            return -5 <= _d(self.lon['Asc'], self.lon[p]) <= 25
        return h in (7, 9, 10, 11)

    def ess_in(self, p: str, lon: float) -> int:
        s = int(lon // 30) % 12
        v = 5 if DOMICILE[s] == p else 0
        v += 4 if EXALT[p] == s else 0
        t = TRIPL[s % 4]
        v += 3 if (t[0] if self.day else t[1]) == p else 0
        v += 2 if term_lord(lon) == p else 0
        v += 1 if face_lord(lon) == p else 0
        return v

    @functools.cached_property
    def hyleg(self) -> str:
        """p. 527-529: by day the Sun, else the Moon; by night the Moon, else the Sun, if in an aphetic place; else the
        planet with most essential dignities (at least three) in the places of the light of the time, the preceding
        lunation and the Ascendant (day) / Part of Fortune (night), if aphetic; else the Ascendant."""
        first, second = ('Sun', 'Moon') if self.day else ('Moon', 'Sun')
        for p in (first, second):
            if self.aphetic(p):
                return p
        places = [self.lon[first], self.w.lon['Syzygy'], self.lon['Asc'] if self.day else self.lon['PF']]
        cand = max(SEVEN, key=lambda p: (sum(self.ess_in(p, x) for x in places), self.score(p)))
        if sum(self.ess_in(cand, x) for x in places) >= 3 and self.aphetic(cand):
            return cand
        return 'Asc'

    @functools.cached_property
    def geniture(self) -> str:
        """p. 532: the planet with most essential and accidental dignities (ties: the more elevated)."""
        return max(SEVEN, key=lambda p: (self.score(p), self.above(p)))

    @functools.cached_property
    def anareta(self) -> set[str]:
        """p. 529-530: a planet in the 8th (5 deg before to 25 deg after the cusp), the lord of the 8th, a planet
        joined to the lord of the 8th, the dispositor of the lord of the 8th."""
        out = {self.lord(8)}
        c8 = self.cusps[7]
        out |= {p for p in SEVEN if -5 <= _d(c8, self.lon[p]) <= 25}
        l8 = self.lord(8)
        out |= {p for p in SEVEN if p != l8 and self.aspect(p, l8) == 'conj'}
        out.add(DOMICILE[self.sign(l8)])
        return out

    # ── primary directions ─────────────────────────────────────────────────────────────────────
    def _equ(self, lon, lat):
        e = math.radians(self.eps)
        l, b = np.radians(lon), np.radians(lat)
        dec = np.arcsin(np.sin(b) * math.cos(e) + np.cos(b) * math.sin(e) * np.sin(l))
        ra = np.arctan2(np.sin(l) * math.cos(e) - np.tan(b) * math.sin(e), np.cos(l))
        return np.degrees(ra) % 360, np.degrees(dec)

    def _mundane(self, ra, dec, armc):
        """Regiomontanus position, 0 at the Ascendant circle, 90 MC, 180 Descendant (degrees of the equator)."""
        f = math.radians(self.lat)
        H, d = np.radians(armc - ra), np.radians(dec)
        x, y, zp = np.cos(d) * np.cos(H), -np.cos(d) * np.sin(H), np.sin(d)
        Z = x * math.cos(f) + zp * math.sin(f)
        he = np.degrees(np.arctan2(-y, Z / math.cos(f)))
        return (he + 90) % 360

    @functools.cached_property
    def directions(self) -> dict[tuple[str, str, str], list[float]]:
        """(significator, promittor key, aspect) -> ages in years (Naibod) at which the direction is perfect (a key
        can hold several points: the dexter and sinister aspect, the terms of one planet in every sign)."""
        if abs(self.lat) >= 66:
            return {}
        keys, lons, lats = [], [], []
        for p in SEVEN:
            keys.append((p, 'conj'))
            lons.append(self.lon[p])
            lats.append(self.blat[p])
            for k, ang in (('sextile', 60), ('square', 90), ('trine', 120), ('opp', 180)):
                for sgn in ((1,) if ang == 180 else (1, -1)):
                    keys.append((p, k))
                    lons.append((self.lon[p] + sgn * ang) % 360)
                    lats.append(0.0)
        for s in range(12):
            start = 0
            for lord, end in TERMS[s]:
                keys.append((f'terms:{lord}', 'conj'))
                lons.append(s * 30 + start)
                lats.append(0.0)
                start = end
        for i in range(12):
            keys.append((f'cusp:{i + 1}', 'conj'))
            lons.append(self.cusps[i])
            lats.append(0.0)
        for s, (_, b) in STARS.items():
            keys.append((f'star:{s}', 'conj'))
            lons.append(self.lon[f'star:{s}'])
            lats.append(b)
        for p in ('Node', 'Tail', 'PF', 'Asc', 'MC'):              # the angles as promittors of a planet significator
            keys.append((p, 'conj'))
            lons.append(self.lon[p])
            lats.append(0.0)
        ra, dec = self._equ(np.array(lons), np.array(lats))
        grid = np.arange(0.0, MAX_ARC + 0.25, 0.25)
        M = self._mundane(ra[None, :], dec[None, :], self.armc + grid[:, None])     # (grid, prom)
        sig_lon = {'Asc': (self.lon['Asc'], 0.0), 'MC': (self.lon['MC'], 0.0), 'PF': (self.lon['PF'], 0.0)}
        sig_lon.update({p: (self.lon[p], self.blat[p]) for p in SEVEN})      # the lights, and a planet as Hyleg
        out: dict[tuple[str, str, str], list[float]] = {}
        for sig, (sl, sb) in sig_lon.items():
            if sig == 'Asc':
                ms = 0.0
            elif sig == 'MC':
                ms = 90.0
            else:
                sra, sdec = self._equ(np.array([sl]), np.array([sb]))
                ms = float(self._mundane(sra, sdec, self.armc)[0])
            rel = (M - ms + 180) % 360 - 180                          # < 0: not yet reached
            for j, (pk, asp) in enumerate(keys):
                if pk == sig:
                    continue
                col = rel[:, j]
                if col[0] >= 0:
                    continue                                          # already past the significator at birth
                idx = np.nonzero((col[:-1] < 0) & (col[1:] >= 0) & (col[1:] - col[:-1] < 90))[0]
                if not len(idx):
                    continue
                i = idx[0]
                a0, a1 = col[i], col[i + 1]
                arc = grid[i] + 0.25 * (-a0) / (a1 - a0)
                out.setdefault((sig, pk, asp), []).append(arc / NAIBOD)
        return out

    def dir_ages(self, sig: str, prom: str, asp: str) -> list[float]:
        return self.directions.get((sig, prom, asp), [])

    # ── revolutions ────────────────────────────────────────────────────────────────────────────
    def revolution_at(self, jd: float) -> dict:
        """The solar revolution in force at jd: the last return of the Sun to its radical place at or before jd,
        erected for the place of birth."""
        x = self.w.lon['Sun']
        t1 = swe.solcross_ut(x, jd - 366.5, swe.FLG_MOSEPH)
        t2 = swe.solcross_ut(x, t1 + 1, swe.FLG_MOSEPH)
        return self._rev(round(t2 if t2 <= jd else t1, 4))

    @functools.lru_cache(maxsize=512)
    def _rev(self, t: float) -> dict:
        sk = W.sky(t)
        cusps, ascmc = swe.houses_ex(t, self.lat, self.w.geo_lon, b'R')
        lon = {p: sk[p][0] for p in SEVEN}
        lon['Asc'], lon['MC'] = ascmc[0] % 360, ascmc[1] % 360
        return {'jd': t, 'lon': lon, 'cusps': [c % 360 for c in cusps[:12]]}

def lchart(c) -> LChart:
    w = W.wchart(c)
    if not hasattr(w, '_lilly'):
        w._lilly = LChart(w)
    return w._lilly


# ── temperament and the significator of manners (p. 532-536) ──────────────────────────────────────────
SIGN_Q = {0: ('hot', 'dry'), 1: ('cold', 'dry'), 2: ('hot', 'moist'), 3: ('cold', 'moist')}     # by triplicity
PLANET_Q = {('Saturn', True): ('cold', 'moist'), ('Saturn', False): ('dry',),
            ('Jupiter', True): ('hot', 'moist'), ('Jupiter', False): ('moist',),
            ('Mars', True): ('hot', 'dry'), ('Mars', False): ('dry',),
            ('Venus', True): ('hot', 'moist'), ('Venus', False): ('moist',),
            ('Mercury', True): ('hot',), ('Mercury', False): ('dry',)}


def _moon_q(L: LChart):
    e = (L.lon['Moon'] - L.lon['Sun']) % 360
    return [('hot', 'moist'), ('hot', 'dry'), ('cold', 'dry'), ('cold', 'moist')][int(e // 90)]


def _sun_q(L: LChart):
    return [('hot', 'moist'), ('hot', 'dry'), ('cold', 'dry'), ('cold', 'moist')][L.sign('Sun') // 3]


def _planet_q(L: LChart, p: str):
    if p == 'Sun':
        return _sun_q(L)
    if p == 'Moon':
        return _moon_q(L)
    return PLANET_Q[(p, 'oriental' in L.accidental(p))]


def temperament(L: LChart) -> str:
    """p. 532-534: testimonies of hot, cold, moist, dry from (1) the sign ascending and its lord, (2) planets in the
    Ascendant or partilly aspecting it, (3) the Moon and planets aspecting her within the moiety of their orbs, (4) the
    quarter of the year (the Sun's sign), (5) the Lord of the Geniture - each significator by its own quality and its
    sign's; a planet both Lord of the Geniture and of the Ascendant counted three times, a planet in the Ascendant
    twice (p. 534); Saturn or Mars in evil aspect to the Ascendant or the Moon add their qualities (p. 533).
    Opposed qualities cancel; the larger of hot/cold and of moist/dry decide (ties: the sign ascending decides)."""
    from collections import Counter
    t = Counter()

    def add(qs, k=1):
        for q in qs:
            t[q] += k
    asc_s = L.sign('Asc')
    add(SIGN_Q[asc_s % 4])
    la = L.lord(1)
    mult = 3 if la == L.geniture else 1
    add(_planet_q(L, la), mult)
    add(SIGN_Q[L.sign(la) % 4], mult)
    for p in SEVEN:
        if L.house(p) == 1:
            add(_planet_q(L, p), 2)
            add(SIGN_Q[L.sign(p) % 4], 2)
        elif L.partile(p, 'Asc'):
            add(_planet_q(L, p))
            add(SIGN_Q[L.sign(p) % 4])
    add(_moon_q(L))
    add(SIGN_Q[L.sign('Moon') % 4])
    for p in SEVEN:
        if p != 'Moon' and L.aspect(p, 'Moon'):
            add(_planet_q(L, p))
    add(_sun_q(L))
    if L.geniture != la:
        add(_planet_q(L, L.geniture))
        add(SIGN_Q[L.sign(L.geniture) % 4])
    for m in MALEFICS:
        if L.aspect(m, 'Asc') in ('square', 'opp') or L.aspect(m, 'Moon') in ('square', 'opp'):
            add(_planet_q(L, m))
    hot = t['hot'] > t['cold'] if t['hot'] != t['cold'] else SIGN_Q[asc_s % 4][0] == 'hot'
    moist = t['moist'] > t['dry'] if t['moist'] != t['dry'] else SIGN_Q[asc_s % 4][1] == 'moist'
    return {(True, True): 'sanguine', (True, False): 'choleric', (False, True): 'phlegmatic',
            (False, False): 'melancholic'}[(hot, moist)]


def manners_sig(L: LChart) -> set[str]:
    """p. 535-536: a planet in the Ascendant (several: all, the most powerful chief); none - the planet joined by
    body to Mercury or the Moon (the most fortified); none - the Lord of the Ascendant."""
    inside = [p for p in SEVEN if L.house(p) == 1 and p not in ('Sun', 'Moon')]
    if inside:
        return set(inside)
    joined = [p for p in SEVEN if p not in ('Mercury', 'Moon')
              and (L.aspect(p, 'Mercury') == 'conj' or L.aspect(p, 'Moon') == 'conj')]
    if joined:
        return {max(joined, key=L.score)}
    return {L.lord(1)}


# ── references ───────────────────────────────────────────────────────────────────────────────────────
POINTS = set(SEVEN) | {'Asc', 'MC', 'PF', 'Node', 'Tail'} | {f'cusp:{i}' for i in range(1, 13)} | \
    {f'star:{s}' for s in STARS}
SPECIAL = {'benefics', 'malefics', 'lights', 'light_time', 'hyleg', 'geniture', 'manners', 'anareta'}


def refs(L: LChart, ref) -> set[str]:
    """A point; 'benefics' / 'malefics' / 'lights' / 'light_time'; 'hyleg', 'geniture' (Lord of the Geniture),
    'manners' (significator of manners), 'anareta' (the killing planets); 'lord:N' (ruler of the sign on cusp N);
    'in:N' (planets in house N); 'disp:REF' (domicile ruler of REF's sign); 'term:REF' (term lord of REF's degree);
    'almuten:REF' (most essential dignities in REF's degree); or a list of these."""
    if isinstance(ref, list):
        return set().union(*(refs(L, r) for r in ref)) if ref else set()
    if ref in POINTS:
        return {ref}
    if ref == 'benefics':
        return set(BENEFICS)
    if ref == 'malefics':
        return set(MALEFICS)
    if ref == 'lights':
        return {'Sun', 'Moon'}
    if ref == 'light_time':
        return {'Sun' if L.day else 'Moon'}
    if ref == 'hyleg':
        return {L.hyleg}
    if ref == 'geniture':
        return {L.geniture}
    if ref == 'manners':
        return manners_sig(L)
    if ref == 'anareta':
        return set(L.anareta)
    kind, _, arg = ref.partition(':')
    if kind == 'lord':
        return {L.lord(int(arg))}
    if kind == 'in':
        return {p for p in SEVEN if L.house(p) == int(arg)}
    if kind == 'disp':
        return {DOMICILE[L.sign(p)] for p in refs(L, arg)}
    if kind == 'term':
        return {term_lord(L.lon[p]) for p in refs(L, arg)}
    if kind == 'almuten':
        return {max(SEVEN, key=lambda q: L.ess_in(q, L.lon[p])) for p in refs(L, arg)}
    raise ValueError(f'unknown Lilly ref {ref!r}')


def check_ref(ref) -> None:
    if isinstance(ref, list):
        for r in ref:
            check_ref(r)
        return
    if not isinstance(ref, str):
        raise ValueError(f'bad Lilly ref {ref!r}')
    if ref in POINTS or ref in SPECIAL:
        return
    kind, _, arg = ref.partition(':')
    if kind in ('lord', 'in') and arg.isdigit() and 1 <= int(arg) <= 12:
        return
    if kind in ('disp', 'term', 'almuten'):
        return check_ref(arg)
    raise ValueError(f'unknown Lilly ref {ref!r}')


ESS = {'domicile', 'exalted', 'triplicity', 'term', 'face', 'detriment', 'fall', 'peregrine', 'reception'}
ACC = {'angular', 'succedent', 'cadent', 'above', 'below', 'retro', 'direct', 'swift', 'slow', 'oriental',
       'occidental', 'increasing', 'decreasing', 'cazimi', 'combust', 'under_beams', 'free', 'besieged'}
KINDS = set(ASPECTS)
NATAL = {'w_l_house', 'w_l_sign', 'w_l_asp', 'w_l_partile', 'w_l_apply', 'w_l_ess', 'w_l_acc', 'w_l_score',
         'w_l_star', 'w_l_same', 'w_l_lunation', 'w_l_count', 'w_l_cusp_sign', 'w_l_temper', 'w_l_stronger',
         'w_l_ness', 'w_l_nacc', 'w_l_nsign', 'w_l_nasp'}
TIMING = {'w_l_dir', 'w_l_prof', 'w_l_lord_year', 'w_l_rev', 'w_l_transit', 'w_l_alf'}


def _houses(hs):
    if not (isinstance(hs, list) and hs and all(isinstance(h, int) and 1 <= h <= 12 for h in hs)):
        raise ValueError(f'bad houses {hs}')


def check(atom: str, a, timing: bool) -> None:
    if atom not in NATAL | TIMING:
        raise ValueError(f'unknown Lilly atom {atom!r}')
    if atom in TIMING and not timing:
        raise ValueError(f'{atom} is only allowed in timing rules')
    if atom in ('w_l_house', 'w_l_count'):
        check_ref(a[0]), _houses(a[1])
    elif atom == 'w_l_sign':
        check_ref(a[0])
        if not all(isinstance(x, int) and 0 <= x <= 11 for x in a[1]):
            raise ValueError(f'bad signs {a}')
    elif atom in ('w_l_asp', 'w_l_partile', 'w_l_apply'):
        check_ref(a[0]), check_ref(a[1])
        if not (a[2] and set(a[2]) <= KINDS):
            raise ValueError(f'bad aspect kinds {a}')
    elif atom == 'w_l_ess':
        check_ref(a[0])
        if not set(a[1]) <= ESS:
            raise ValueError(f'bad dignity {a}')
    elif atom == 'w_l_nasp':                     # [target, refs, n]: at least n of refs aspect the target (by orb)
        check_ref(a[0]), check_ref(a[1])
        if not isinstance(a[2], int):
            raise ValueError(f'bad aspect count {a}')
    elif atom == 'w_l_nsign':                    # [refs, signs, n]: at least n of refs in the signs
        check_ref(a[0])
        if not (all(0 <= x <= 11 for x in a[1]) and isinstance(a[2], int)):
            raise ValueError(f'bad sign count {a}')
    elif atom in ('w_l_ness', 'w_l_nacc'):         # [refs, classes, n]: at least n of refs have one of the classes
        check_ref(a[0])
        if not (set(a[1]) <= (ESS if atom == 'w_l_ness' else ACC) and isinstance(a[2], int)):
            raise ValueError(f'bad count {a}')
    elif atom == 'w_l_acc':
        check_ref(a[0])
        if not set(a[1]) <= ACC:
            raise ValueError(f'bad accidental {a}')
    elif atom == 'w_l_score':
        check_ref(a[0])
        if a[1] not in ('ess', 'acc', 'tot') or a[2] not in ('>=', '<='):
            raise ValueError(f'bad score {a}')
    elif atom == 'w_l_star':
        check_ref(a[0])
        if not set(a[1]) <= set(STARS) or not 0 < a[2] <= 10:
            raise ValueError(f'bad star {a}')
    elif atom in ('w_l_same', 'w_l_stronger'):
        check_ref(a[0]), check_ref(a[1])
    elif atom == 'w_l_lunation':
        if a[0] not in ('new', 'full') or not 0 < a[1] <= 15:
            raise ValueError(f'bad lunation {a}')
    elif atom == 'w_l_cusp_sign':
        if not (1 <= a[0] <= 12 and all(0 <= x <= 11 for x in a[1])):
            raise ValueError(f'bad cusp sign {a}')
    elif atom == 'w_l_temper':
        if a not in ('sanguine', 'choleric', 'phlegmatic', 'melancholic'):
            raise ValueError(f'bad temperament {a}')
    else:
        check_timing(atom, a)


def evaluate(c, atom: str, a, jd: float | None = None) -> bool:
    L = lchart(c)
    if atom == 'w_l_house':
        return any(L.house(p) in a[1] for p in refs(L, a[0]))
    if atom == 'w_l_count':                      # [refs, houses, n]: at least n of refs in the houses
        return sum(1 for p in refs(L, a[0]) if L.house(p) in a[1]) >= a[2]
    if atom == 'w_l_sign':
        return any(L.sign(p) in a[1] for p in refs(L, a[0]))
    if atom == 'w_l_asp':
        return any(p != q and L.aspect(p, q) in a[2] for p in refs(L, a[0]) for q in refs(L, a[1]))
    if atom == 'w_l_partile':
        return any(p != q and L.partile(p, q) in a[2] for p in refs(L, a[0]) for q in refs(L, a[1]))
    if atom == 'w_l_apply':
        return any(p != q and applying(L, p, q, a[2]) for p in refs(L, a[0]) for q in refs(L, a[1]))
    if atom == 'w_l_ess':
        return any(L.essential(p) & set(a[1]) for p in refs(L, a[0]))
    if atom == 'w_l_acc':
        return any(L.accidental(p) & set(a[1]) for p in refs(L, a[0]))
    if atom == 'w_l_nasp':
        t = refs(L, a[0])
        return sum(1 for q in refs(L, a[1]) if any(q != p and L.aspect(q, p) for p in t)) >= a[2]
    if atom == 'w_l_nsign':
        return sum(1 for p in refs(L, a[0]) if L.sign(p) in a[1]) >= a[2]
    if atom == 'w_l_ness':
        return sum(1 for p in refs(L, a[0]) if L.essential(p) & set(a[1])) >= a[2]
    if atom == 'w_l_nacc':
        return sum(1 for p in refs(L, a[0]) if L.accidental(p) & set(a[1])) >= a[2]
    if atom == 'w_l_score':
        f = {'ess': L.ess_score, 'acc': L.acc_score, 'tot': L.score}[a[1]]
        return any((f(p) >= a[3]) if a[2] == '>=' else (f(p) <= a[3]) for p in refs(L, a[0]) if p in SEVEN)
    if atom == 'w_l_star':
        return any(abs(_d(L.lon[p], L.lon[f'star:{s}'])) <= a[2] for p in refs(L, a[0]) for s in a[1])
    if atom == 'w_l_same':
        return bool(refs(L, a[0]) & refs(L, a[1]))
    if atom == 'w_l_stronger':                   # every planet of a[0] outscores every other planet of a[1]
        A, B = refs(L, a[0]) & set(SEVEN), refs(L, a[1]) & set(SEVEN)
        B = B - A
        return bool(A and B) and min(L.score(p) for p in A) > max(L.score(q) for q in B)
    if atom == 'w_l_lunation':                   # born within orb of the new / full moon
        e = abs(_d(L.lon['Sun'], L.lon['Moon']))
        return e <= a[1] if a[0] == 'new' else 180 - e <= a[1]
    if atom == 'w_l_cusp_sign':
        return int(L.cusps[a[0] - 1] // 30) % 12 in a[1]
    if atom == 'w_l_temper':
        if not hasattr(L, '_temper'):
            L._temper = temperament(L)
        return L._temper == a
    if jd is None:
        raise ValueError(f'{atom} needs a date')
    return eval_timing(L, atom, a, jd)


def applying(L: LChart, p: str, q: str, kinds) -> bool:
    """p applies to an aspect of q (within the moieties): the distance to the exact aspect shrinks over the next day."""
    if p not in SEVEN:
        return False
    k = L.aspect(p, q)
    if k not in kinds:
        return False
    ang = ASPECTS[k]
    d0 = abs(abs(_d(L.lon[p], L.lon[q])) - ang)
    lp = L.lon[p] + L.speed[p]
    lq = L.lon[q] + (L.speed.get(q, 0.0) if q in SEVEN else 0.0)
    return abs(abs(_d(lp, lq)) - ang) < d0


# ── timing ───────────────────────────────────────────────────────────────────────────────────────────
SIGNIFICATORS = {'Asc', 'MC', 'PF'} | set(SEVEN)


def prom_keys(L: LChart, ref) -> set[str]:
    """Promittor keys: points from refs(), plus 'terms:<planet>' (the beginnings of that planet's terms)."""
    if isinstance(ref, list):
        return set().union(*(prom_keys(L, r) for r in ref)) if ref else set()
    if isinstance(ref, str) and ref.startswith('terms:'):
        return {ref}
    return refs(L, ref)


def _check_prom(ref) -> None:
    if isinstance(ref, list):
        for r in ref:
            _check_prom(r)
        return
    if isinstance(ref, str) and ref.startswith('terms:'):
        if ref[6:] not in SEVEN:
            raise ValueError(f'bad terms promittor {ref}')
        return
    check_ref(ref)


def check_timing(atom: str, a) -> None:
    if atom == 'w_l_dir':                        # [significator refs, promittor refs, kinds]
        check_ref(a[0]), _check_prom(a[1])
        if not (a[2] and set(a[2]) <= KINDS):
            raise ValueError(f'bad direction kinds {a}')
    elif atom == 'w_l_prof':                     # [point, test]
        check_ref(a[0])
        if not (isinstance(a[1], dict) and set(a[1]) <= PROF_KEYS):
            raise ValueError(f'bad profection test {a}')
        if 'houses' in a[1]:
            _houses(a[1]['houses'])
        if 'fig_houses' in a[1]:
            _houses(a[1]['fig_houses'])
        if 'aspect_self' in a[1] and not set(a[1]['aspect_self']) <= KINDS:
            raise ValueError(f'bad profection aspect {a}')
        for k in ('sign_of', 'lord'):
            if k in a[1]:
                check_ref(a[1][k])
    elif atom == 'w_l_lord_year':                # [refs, optional state]
        check_ref(a[0])
        if len(a) > 1 and a[1] not in LY_STATES:
            raise ValueError(f'bad lord-of-the-year state {a}')
    elif atom == 'w_l_rev':                      # test dict
        if not (isinstance(a, dict) and set(a) <= REV_KEYS and a):
            raise ValueError(f'bad revolution test {a}')
        if 'asc_radix_house' in a:
            _houses(a['asc_radix_house'])
        if 'asc_aspect_radix_asc' in a and not set(a['asc_aspect_radix_asc']) <= KINDS:
            raise ValueError(f'bad revolution aspect {a}')
        if 'ret' in a:
            if a['ret'][0] not in SEVEN:
                raise ValueError(f'bad return {a}')
            check_ref(a['ret'][1])
        if 'sr_house' in a:
            check_ref(a['sr_house'][0]), _houses(a['sr_house'][1])
    elif atom == 'w_l_transit':                  # [star, refs, kinds, orb]
        if a[0] not in SEVEN or not (a[2] and set(a[2]) <= KINDS) or not 0 < a[3] <= 8:
            raise ValueError(f'bad transit {a}')
        check_ref(a[1])
    elif atom == 'w_l_alf':                      # [refs]: the alfridary lord
        check_ref(a[0])
    else:
        raise ValueError(f'{atom} not implemented')


PROF_KEYS = {'houses', 'fig_houses', 'aspect_self', 'sign_of', 'lord', 'contains_malefic', 'contains_benefic'}
LY_STATES = {'strong_both', 'weak_both', 'afflicted_both', 'strong_radix_weak_rev', 'weak_radix_strong_rev'}
REV_KEYS = {'asc_radix_house', 'asc_same', 'asc_aspect_radix_asc', 'asc_on_malefic', 'ret', 'lord_asc_combust', 'sr_house'}
ALF_DAY = ['Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars']
ALF_NIGHT = ['Moon', 'Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury']


def _years(L: LChart, jd: float) -> int:
    """Completed years: the profection year begins at the Sun's return (p. 716) - completed solar years of age."""
    return int((jd - L.bjd) / W.YEAR)


def prof_lon(L: LChart, point: str, jd: float) -> float:
    """p. 715: thirty degrees, one whole sign, to a solar year; every point keeps its degree, only the sign varies."""
    return (L.lon[point] + 30 * _years(L, jd)) % 360


def lord_year(L: LChart, jd: float) -> str:
    """p. 720: the Lord of the Year is the lord of the sign ascending in the profection (the first lord; when the
    middle of a sign ascends a second lord takes the later part of the year - the engine keeps the first)."""
    return DOMICILE[int(prof_lon(L, 'Asc', jd) // 30) % 12]


def sr_state(L: LChart, p: str, rev: dict) -> tuple[bool, bool]:
    """(strong, afflicted) of planet p in the revolution figure: strong = in its own house or exaltation or angular in
    the revolution's houses and not afflicted; afflicted = in conjunction, square or opposition (by moiety) with Saturn
    or Mars in the revolution."""
    lon = rev['lon']
    s = int(lon[p] // 30) % 12
    aff = False
    for m in MALEFICS:
        if m == p:
            continue
        d = abs(_d(lon[p], lon[m]))
        o = (ORB[p] + ORB[m]) / 2
        if d <= o or abs(d - 90) <= o or abs(d - 180) <= o:
            aff = True
    ang = _house_in(rev['cusps'], lon[p]) in ANGLES
    strong = (DOMICILE[s] == p or EXALT[p] == s or ang) and not aff
    return strong, aff


def _house_in(cusps, lon):
    x = (lon + 5) % 360
    for i in range(12):
        a, b = cusps[i], cusps[(i + 1) % 12]
        if (x - a) % 360 < (b - a) % 360:
            return i + 1
    return 12


def eval_timing(L: LChart, atom: str, a, jd: float) -> bool:
    age = (jd - L.bjd) / W.YEAR
    if atom == 'w_l_dir':
        for s in refs(L, a[0]):
            if s not in SIGNIFICATORS:
                continue
            for p in prom_keys(L, a[1]):
                if p == s:
                    continue
                for k in a[2]:
                    if any(abs(age - y) <= DIR_WINDOW for y in L.dir_ages(s, p, k)):
                        return True
        return False
    if atom == 'w_l_prof':
        t = a[1]
        for pt in refs(L, a[0]):
            if pt not in L.lon:
                continue
            pl = prof_lon(L, pt, jd)
            ps = int(pl // 30) % 12
            n = _years(L, jd) % 12
            ok = True
            if 'houses' in t:                    # the radix house (Regiomontanus) the profected degree falls in
                ok &= L.house_of(pl) in t['houses']
            if 'fig_houses' in t:                # the house of the profectional figure the point's radix sign holds
                ok &= (L.sign(pt) - (L.sign('Asc') + _years(L, jd))) % 12 + 1 in t['fig_houses']
            if 'aspect_self' in t:               # the profected point to its own radix place, by signs
                ok &= W.ASPECT_OF.get(n) in t['aspect_self']
            if 'sign_of' in t:                   # the profected point comes to the sign of a radix point
                ok &= any(L.sign(q) == ps for q in refs(L, t['sign_of']))
            if 'lord' in t:
                ok &= DOMICILE[ps] in refs(L, t['lord'])
            if 'contains_malefic' in t:          # the sign wherein an infortune was
                ok &= any(L.sign(m) == ps for m in MALEFICS) == bool(t['contains_malefic'])
            if 'contains_benefic' in t:
                ok &= any(L.sign(b) == ps for b in BENEFICS) == bool(t['contains_benefic'])
            if ok:
                return True
        return False
    if atom == 'w_l_lord_year':
        ly = lord_year(L, jd)
        if ly not in refs(L, a[0]):
            return False
        if len(a) == 1:
            return True
        rev = L.revolution_at(jd)
        rs, ra = sr_state(L, ly, rev)
        strong_r, weak_r = L.score(ly) >= 5, L.score(ly) <= -5
        aff_r = L.aspect(ly, 'Saturn') in ('conj', 'square', 'opp') or L.aspect(ly, 'Mars') in ('conj', 'square', 'opp')
        return {'strong_both': strong_r and rs, 'weak_both': weak_r and not rs, 'afflicted_both': aff_r and ra,
                'strong_radix_weak_rev': strong_r and not rs, 'weak_radix_strong_rev': weak_r and rs}[a[1]]
    if atom == 'w_l_rev':
        rev = L.revolution_at(jd)
        lon = rev['lon']
        ok = True
        if 'asc_radix_house' in a:               # the revolution's ascending degree in a radix house
            ok &= L.house_of(lon['Asc']) in a['asc_radix_house']
        if 'asc_same' in a:
            ok &= (int(lon['Asc'] // 30) == L.sign('Asc')) == bool(a['asc_same'])
        if 'asc_aspect_radix_asc' in a:
            ok &= W.ASPECT_OF.get((int(lon['Asc'] // 30) - L.sign('Asc')) % 12) in a['asc_aspect_radix_asc']
        if 'asc_on_malefic' in a:                # to the hostile beams (conjunction, square, opposition) of the infortunes
            hit = False
            for m in MALEFICS:
                for ml in (L.lon[m], lon[m]):
                    d = abs(_d(lon['Asc'], ml))
                    if min(d, abs(d - 90), abs(d - 180)) <= ORB[m] / 2:
                        hit = True
            ok &= hit == bool(a['asc_on_malefic'])
        if 'ret' in a:                           # [planet, refs]: the planet in the revolution on the radical place
            p = a['ret'][0]
            ok &= any(abs(_d(lon[p], L.lon[q])) <= ORB[p] / 2 for q in refs(L, a['ret'][1]))
        if 'lord_asc_combust' in a:
            la = DOMICILE[int(lon['Asc'] // 30) % 12]
            ok &= la not in ('Sun',) and abs(_d(lon[la], lon['Sun'])) <= 8.5
        if 'sr_house' in a:                      # [refs, houses]: planets in the revolution's own houses
            ok &= any(p in SEVEN and _house_in(rev['cusps'], lon[p]) in a['sr_house'][1] for p in refs(L, a['sr_house'][0]))
        return ok
    if atom == 'w_l_transit':
        t = W.sky(jd)[a[0]][0]
        for q in refs(L, a[1]):
            d = abs(_d(t, L.lon[q]))
            if any(abs(d - ASPECTS[k]) <= a[3] for k in a[2]):
                return True
        return False
    if atom == 'w_l_alf':                        # p. 733: seven years to each, day from the Sun, night from the Moon
        order = ALF_DAY if L.day else ALF_NIGHT
        return order[int(age // 7) % 7] in refs(L, a[0])
    raise ValueError(atom)
