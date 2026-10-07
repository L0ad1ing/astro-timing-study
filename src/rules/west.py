"""
src/rules/west.py — the Western (Hellenistic / 17th-century) chart used by the Vettius Valens and William Lilly rule
sets, and the evaluation of their 'w_' rule conditions (src/rules/engine.py dispatches every atom starting with 'w_'
here).

Zodiac: tropical (both authors). Positions: Swiss Ephemeris, Moshier, geocentric, apparent. Places: whole-sign from
the Ascendant's sign (Valens' practice: "the Place" = the sign). Aspects: by sign (Valens: sextile 3rd/11th, square
4th/10th, trine 5th/9th, opposition 7th; 'together' = same sign).

Choices stated here (each logged in docs/valens_progress_log.md):
- sect: a day birth when the Sun is above the horizon (ecliptic longitude between the Descendant and the Ascendant
  through MC);
- 'from the right' / superior aspect: a star is on the right of another when it is the earlier in zodiacal order of an
  aspect, i.e. when the other falls 3rd, 4th or 5th from it; 'superior aspect' (epidekateia) = the square from the
  right (the other is 4th from it, it is 10th from the other);
- 'under the rays': within 15 deg of the Sun; 'morning star' (rising before the Sun): longitude behind the Sun's;
- 'operative' places (chrematistikos): the angles, the 11th and 5th (Good Daimon, Good Fortune) and the 9th; the 2nd,
  3rd, 6th, 8th and 12th are inoperative (Valens II.5-15: the 2nd 'Gate of Hades', 3rd average, 6th, 8th, 12th bad);
- benefics Jupiter and Venus, malefics Saturn and Mars; the Moon and Mercury neither unless stated;
- terms: Valens I.3 as printed in Riley's translation (Libra Saturn 6, Mercury 5, Jupiter 8, Venus 7, Mars 4 - the
  translation's numbers, which differ from the usual Egyptian Libra 6/8/7/7/2).
"""
from __future__ import annotations

import functools

import swisseph as swe

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn',
         'Aquarius', 'Pisces']
SEVEN = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
IDS = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS, 'Mars': swe.MARS,
       'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN, 'Node': swe.MEAN_NODE}
FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED
DOMICILE = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn',
            'Jupiter']
EXALT = {'Sun': 0, 'Moon': 1, 'Mercury': 5, 'Venus': 11, 'Mars': 9, 'Jupiter': 3, 'Saturn': 6}
EXALT_DEG = {'Sun': 19, 'Moon': 3, 'Mercury': 15, 'Venus': 27, 'Mars': 28, 'Jupiter': 15, 'Saturn': 21}
BENEFICS, MALEFICS = ['Jupiter', 'Venus'], ['Saturn', 'Mars']
DAY_SECT, NIGHT_SECT = ['Sun', 'Jupiter', 'Saturn'], ['Moon', 'Venus', 'Mars']
# Valens II.1: triangle rulers (day first, night first, third)
TRIPLICITY = {0: ('Sun', 'Jupiter', 'Saturn'), 1: ('Venus', 'Moon', 'Mars'), 2: ('Saturn', 'Mercury', 'Jupiter'),
              3: ('Venus', 'Mars', 'Moon')}
# Valens I.3 (Riley pp. 6-8): (lord, degrees) in order
TERMS = [
    [('Jupiter', 6), ('Venus', 6), ('Mercury', 8), ('Mars', 5), ('Saturn', 5)],
    [('Venus', 8), ('Mercury', 6), ('Jupiter', 8), ('Saturn', 5), ('Mars', 3)],
    [('Mercury', 6), ('Jupiter', 6), ('Venus', 5), ('Mars', 7), ('Saturn', 6)],
    [('Mars', 7), ('Venus', 6), ('Mercury', 6), ('Jupiter', 7), ('Saturn', 4)],
    [('Jupiter', 6), ('Venus', 5), ('Saturn', 7), ('Mercury', 6), ('Mars', 6)],
    [('Mercury', 7), ('Venus', 10), ('Jupiter', 4), ('Mars', 7), ('Saturn', 2)],
    [('Saturn', 6), ('Mercury', 5), ('Jupiter', 8), ('Venus', 7), ('Mars', 4)],
    [('Mars', 7), ('Venus', 4), ('Mercury', 8), ('Jupiter', 5), ('Saturn', 6)],
    [('Jupiter', 12), ('Venus', 5), ('Mercury', 4), ('Saturn', 5), ('Mars', 4)],
    [('Mercury', 7), ('Jupiter', 7), ('Venus', 8), ('Saturn', 4), ('Mars', 4)],
    [('Mercury', 7), ('Venus', 6), ('Jupiter', 7), ('Mars', 5), ('Saturn', 5)],
    [('Venus', 12), ('Jupiter', 4), ('Mercury', 3), ('Mars', 9), ('Saturn', 2)],
]
assert all(sum(d for _, d in t) == 30 for t in TERMS)
# the stars' minimum (minor) periods, Valens IV / II.27
MINOR_YEARS = {'Saturn': 30, 'Jupiter': 12, 'Mars': 15, 'Sun': 19, 'Venus': 8, 'Mercury': 20, 'Moon': 25}
ASPECT_OF = {0: 'conj', 2: 'sextile', 10: 'sextile', 3: 'square', 9: 'square', 4: 'trine', 8: 'trine', 6: 'opp'}
ANGLE, SUCCEDENT, CADENT = (1, 4, 7, 10), (2, 5, 8, 11), (3, 6, 9, 12)
OPERATIVE = (1, 4, 5, 7, 9, 10, 11)
LOTS = ('Fortune', 'Daimon', 'Basis', 'Exaltation', 'Debt', 'Theft', 'Deceit', 'ForeignLands', 'Father', 'Marriage',
        'Children', 'Brothers', 'Accomplishment', 'Adultery', 'MoonDay3', 'MoonDay7', 'MoonDay40', 'Syzygy', 'Love', 'Necessity', 'CrisisPlace', 'CriticalPoint')


def term_lord(lon: float) -> str:
    s, d = int(lon // 30) % 12, lon % 30
    acc = 0
    for lord, n in TERMS[s]:
        acc += n
        if d < acc:
            return lord
    return TERMS[s][-1][0]


def _arc(a: float, b: float) -> float:
    """b - a, 0..360."""
    return (b - a) % 360


@functools.lru_cache(maxsize=200_000)
def sky(jd: float) -> dict[str, tuple[float, float]]:
    """Tropical longitude and daily speed of the seven stars and the mean node at jd (UT)."""
    out = {}
    for p, i in IDS.items():
        x = swe.calc_ut(jd, i, FLAGS)[0]
        out[p] = (x[0] % 360, x[3])
    return out


def syzygy(jd: float) -> tuple[float, str]:
    """(longitude, 'new'|'full') of the last new or full moon before jd: the Moon's place at it (for a full moon the
    Moon's place, as Valens II.33-34 / II.41 speak of 'the sign of the full moon')."""
    def elong(t):
        sk = sky(t)
        return _arc(sk['Sun'][0], sk['Moon'][0])
    e = elong(jd)
    t = jd - (e % 180) / 12.19
    for _ in range(8):                                   # Newton steps on the elongation
        d = (elong(t) + 90) % 180 - 90
        t -= d / 12.19
    return sky(t)['Moon'][0], ('new' if elong(t) < 90 or elong(t) > 270 else 'full')


class WChart:
    def __init__(self, bjd: float, lat: float, lon: float, gender: str | None = None, geo: tuple | None = None):
        """bjd: the native's birth moment (ages, periods and dates count from it). geo = (jd, lat, lon) of the natal
        geometry when it differs - the mismatched-chart control of the tests takes a donor's whole chart this way, as
        the KP charts do (engine 'kp_birth'), while the native's own birth moment still drives the dates."""
        pjd, lat, lon = geo or (bjd, lat, lon)
        self.bjd, self.pjd, self.lat, self.geo_lon, self.gender = bjd, pjd, lat, lon, gender
        sk = sky(pjd)
        self.lon = {p: v[0] for p, v in sk.items()}
        self.speed = {p: v[1] for p, v in sk.items()}
        cusps, ascmc = swe.houses_ex(pjd, lat, lon, b'R')            # Regiomontanus (Lilly); Asc/MC are system-free
        self.reg_cusps = [c % 360 for c in cusps[:12]]
        self.asc, self.mc = ascmc[0] % 360, ascmc[1] % 360
        self.lon['Asc'], self.lon['MC'] = self.asc, self.mc
        self.day = _arc(self.asc, self.lon['Sun']) >= 180            # above the horizon
        self.sect_light = 'Sun' if self.day else 'Moon'
        self.lon.update(self._lots())

    # ── points ──────────────────────────────────────────────────────────────────────────────────────
    def _lot(self, frm: float, to: float, base: float, reverse: bool = False) -> float:
        d = _arc(to, frm) if reverse else _arc(frm, to)
        return (base + d) % 360

    def _lots(self) -> dict[str, float]:
        L, a, day = self.lon, self.asc, self.day
        f = self._lot(L['Sun'], L['Moon'], a, not day)                # II.3: day Sun->Moon from Asc, night reversed
        dm = self._lot(L['Moon'], L['Sun'], a, not day)               # II.22: day Moon->Sun, night reversed
        # II.22: Basis - from the nearer Lot to the other, counted from the Ascendant (distance <= 180)
        basis = (a + min(_arc(f, dm), _arc(dm, f))) % 360
        out = {'Fortune': f, 'Daimon': dm, 'Basis': basis,
               'Exaltation': (a + _arc(L['Sun'], 0.0)) % 360 if day else (a + _arc(L['Moon'], 30.0)) % 360,   # II.18
               'Debt': self._lot(L['Mercury'], L['Saturn'], a),                                         # II.23
               'Theft': self._lot(L['Mercury'], L['Mars'], L['Saturn'], not day),                       # II.24
               'Deceit': self._lot(L['Sun'], L['Mars'], a, not day),                                    # II.25
               'ForeignLands': self._lot(L['Saturn'], L['Mars'], a),                                    # II.29
               'Father': self._lot(L['Sun'], L['Saturn'], a) if day else self._lot(L['Venus'], L['Moon'], a),  # II.31
               'Marriage': self._lot(L['Jupiter'], L['Venus'], a, not day),                             # II.37
               'Children': self._lot(L['Jupiter'], L['Venus'] if self.gender == 'F' else L['Mercury'], a),   # II.39
               'Brothers': self._lot(L['Saturn'], L['Jupiter'], a, not day)}                            # II.40
        out['Accomplishment'] = (f + 300) % 360                       # II.20: the 11th place from Fortune
        out['Adultery'] = (out['Marriage'] + 180) % 360               # II.37
        # I.15: the Moon's 3rd, 7th and 40th days - one sign, a square and the opposition from its natal place
        out.update({'MoonDay3': (L['Moon'] + 30) % 360, 'MoonDay7': (L['Moon'] + 90) % 360,
                    'MoonDay40': (L['Moon'] + 180) % 360})
        out['Syzygy'] = syzygy(self.pjd)[0]                            # the new or full moon before birth
        # IV.25 marginal notes: Love - day from Fortune to Daimon counted from the Ascendant (night reversed);
        # Necessity - day from Daimon to Fortune (night reversed)
        out['Love'] = self._lot(f, dm, a, not day)
        out['Necessity'] = self._lot(dm, f, a, not day)
        # V.1 the Crisis-Producing Place: day from Saturn to Mars counted from the Ascendant (night reversed)
        out['CrisisPlace'] = self._lot(L['Saturn'], L['Mars'], a, not day)
        # V.2: from Saturn to the ruler of the pre-natal lunation, counted from the Ascendant
        out['CriticalPoint'] = self._lot(L['Saturn'], L[DOMICILE[int(out['Syzygy'] // 30) % 12]], a)
        return out

    def sign(self, p: str) -> int:
        return int(self.lon[p] // 30) % 12

    def house(self, p: str, base: str = 'Asc') -> int:
        """Whole-sign place of p counted from base (a point name)."""
        return (self.sign(p) - self.sign(base)) % 12 + 1

    def ruler(self, p: str) -> str:
        return DOMICILE[self.sign(p)]

    def aspect(self, p: str, q: str) -> str | None:
        return ASPECT_OF.get((self.sign(q) - self.sign(p)) % 12)

    def on_right(self, p: str, q: str) -> bool:
        """p casts its aspect onto q from the right (p is earlier in zodiacal order: q falls 3rd/4th/5th from p)."""
        return (self.sign(q) - self.sign(p)) % 12 in (2, 3, 4)

    def superior(self, p: str, q: str) -> bool:
        """p is in superior aspect to q (square from the right: p in the 10th from q)."""
        return (self.sign(p) - self.sign(q)) % 12 == 9

    def under_rays(self, p: str) -> bool:
        return p not in ('Sun', 'Asc', 'MC') and abs(((self.lon[p] - self.lon['Sun']) + 180) % 360 - 180) < 15

    def morning(self, p: str) -> bool:
        """Rising before the Sun (morning star): its longitude lies behind the Sun's."""
        return 0 < _arc(self.lon[p], self.lon['Sun']) < 180

    def retro(self, p: str) -> bool:
        return self.speed.get(p, 1.0) < 0

    def waxing(self) -> bool:
        return _arc(self.lon['Sun'], self.lon['Moon']) < 180

    def dignities(self, p: str) -> set[str]:
        s, out = self.sign(p), set()
        if p in SEVEN:
            if DOMICILE[s] == p:
                out.add('domicile')
            if DOMICILE[(s + 6) % 12] == p:
                out.add('detriment')
            if EXALT.get(p) == s:
                out.add('exalted')
            if EXALT.get(p) is not None and (EXALT[p] + 6) % 12 == s:
                out.add('fall')
            if p in TRIPLICITY[s % 4]:
                out.add('triplicity')
            if term_lord(self.lon[p]) == p:
                out.add('term')
            if not out & {'domicile', 'exalted', 'triplicity', 'term'}:
                out.add('peregrine')
            if (p in DAY_SECT and self.day) or (p in NIGHT_SECT and not self.day) or p == 'Mercury':
                out.add('own_sect')
            else:
                out.add('contrary_sect')
        return out


def wchart(c) -> WChart:
    """The Western chart of an engine Chart (cached on it)."""
    if not hasattr(c, '_west'):
        s = c.s
        c._west = WChart(s['birth_jd'], s['lat'], s['lon'], s.get('gender'), s.get('kp_birth'))
    return c._west


# ── references ──────────────────────────────────────────────────────────────────────────────────────
POINTS = set(SEVEN) | {'Node', 'Asc', 'MC'} | set(LOTS)


def refs(w: WChart, ref) -> set[str]:
    """A point name, 'benefics', 'malefics', 'ruler:<point>' (domicile ruler of its sign), 'term:<point>' (its term
    lord), 'tripl:<n>' (n-th triangle ruler of the sect light, 1-3), 'exalt_ruler:<point>' (ruler of its sign's
    exaltation-holder: the star exalted there), or a list of these."""
    if isinstance(ref, list):
        return set().union(*(refs(w, r) for r in ref)) if ref else set()
    if ref == 'benefics':
        return set(BENEFICS)
    if ref == 'malefics':
        return set(MALEFICS)
    if ref in POINTS:
        return {ref}
    kind, _, arg = ref.partition(':')
    if kind == 'ruler':
        return {w.ruler(p) for p in refs(w, arg)}
    if kind == 'term':
        return {term_lord(w.lon[p]) for p in refs(w, arg)}
    if kind == 'tripl':
        t = TRIPLICITY[w.sign(w.sect_light) % 4]
        first, second = (t[0], t[1]) if w.day else (t[1], t[0])
        return {(first, second, t[2])[int(arg) - 1]}
    raise ValueError(f'unknown western ref {ref!r}')


def _check_ref(ref) -> None:
    if isinstance(ref, list):
        for r in ref:
            _check_ref(r)
        return
    if not isinstance(ref, str):
        raise ValueError(f'bad western ref {ref!r}')
    if ref in POINTS or ref in ('benefics', 'malefics'):
        return
    kind, _, arg = ref.partition(':')
    if kind in ('ruler', 'term'):
        return _check_ref(arg)
    if kind == 'tripl' and arg in ('1', '2', '3'):
        return
    raise ValueError(f'unknown western ref {ref!r}')


ASPECT_KINDS = {'conj', 'sextile', 'square', 'trine', 'opp'}
DIGNITIES = {'domicile', 'exalted', 'detriment', 'fall', 'triplicity', 'term', 'peregrine', 'own_sect',
             'contrary_sect'}
NATAL_ATOMS = {'w_in_house', 'w_in_sign', 'w_with', 'w_aspect', 'w_right', 'w_superior', 'w_sect', 'w_dignity',
               'w_under_rays', 'w_morning', 'w_retro', 'w_waxing', 'w_angularity', 'w_operative', 'w_term',
               'w_gender', 'w_same', 'w_deg', 'w_n_aspecting', 'w_moon_phase', 'w_orb', 'w_syzygy'}
TIMING_ATOMS = {'w_transit_from', 'w_transmit', 'w_prof', 'w_zr', 'w_critical_year', 'w_life_node', 'w_year_of_life',
                'w_transit_orb', 'w_degree_tx', 'w_decennial', 'w_moon9'}


def check(atom: str, a, timing: bool) -> None:
    if atom.startswith('w_l_'):                  # William Lilly's apparatus: src/rules/lilly.py
        from src.rules import lilly
        return lilly.check(atom, a, timing)
    if atom not in NATAL_ATOMS | TIMING_ATOMS:
        raise ValueError(f'unknown western atom {atom!r}')
    if atom in TIMING_ATOMS and not timing:
        raise ValueError(f'{atom} is only allowed in timing rules')
    if atom in ('w_in_house', 'w_angularity', 'w_operative'):
        _check_ref(a[0])
        if len(a) > 2:
            _check_ref(a[2])
    if atom == 'w_in_house' and not all(isinstance(h, int) and 1 <= h <= 12 for h in a[1]):
        raise ValueError(f'bad house in {atom} {a}')
    if atom == 'w_angularity' and a[1] not in ('angle', 'succedent', 'cadent'):
        raise ValueError(f'bad angularity {a}')
    if atom == 'w_in_sign':
        _check_ref(a[0])
        if not all(isinstance(s, int) and 0 <= s <= 11 for s in a[1]):
            raise ValueError(f'bad sign in {a}')
    if atom in ('w_with', 'w_right', 'w_superior', 'w_same'):
        _check_ref(a[0]), _check_ref(a[1])
    if atom == 'w_aspect':
        _check_ref(a[0]), _check_ref(a[1])
        if not set(a[2]) <= ASPECT_KINDS:
            raise ValueError(f'bad aspect kinds {a}')
    if atom == 'w_n_aspecting':
        _check_ref(a[0]), _check_ref(a[1])
    if atom == 'w_dignity':
        _check_ref(a[0])
        if not set(a[1]) <= DIGNITIES:
            raise ValueError(f'bad dignity {a}')
    if atom in ('w_under_rays', 'w_morning', 'w_retro'):
        _check_ref(a)
    if atom == 'w_sect' and a not in ('day', 'night'):
        raise ValueError(f'bad sect {a}')
    if atom == 'w_term':
        _check_ref(a[0]), _check_ref(a[1])
    if atom == 'w_deg':
        _check_ref(a[0])
    if atom in ('w_transmit', 'w_prof', 'w_zr', 'w_critical_year', 'w_life_node') + ('w_year_of_life', 'w_transit_orb', 'w_degree_tx', 'w_decennial', 'w_moon9'):
        return _check_timing(atom, a)
    if atom == 'w_transit_from':
        if a[0] not in SEVEN:
            raise ValueError(f'bad transiting star {a}')
        if not all(isinstance(h, int) and 1 <= h <= 12 for h in a[1]):
            raise ValueError(f'bad house in {a}')
        _check_ref(a[2])
    if atom == 'w_moon_phase' and not (0 <= a[0] < a[1] <= 360):
        raise ValueError(f'bad moon phase {a}')


def evaluate(c, atom: str, a, jd: float | None = None) -> bool:
    if atom.startswith('w_l_'):
        from src.rules import lilly
        return lilly.evaluate(c, atom, a, jd)
    w = wchart(c)
    if atom == 'w_in_house':                     # [refs, [houses], base point (default Asc)]
        base = a[2] if len(a) > 2 else 'Asc'
        bases = refs(w, base)
        return any(w.house(p, b) in a[1] for p in refs(w, a[0]) for b in bases if p != b or base == 'Asc')
    if atom == 'w_in_sign':
        return any(w.sign(p) in a[1] for p in refs(w, a[0]))
    if atom == 'w_with':                         # together in one sign (distinct points)
        return any(p != q and w.sign(p) == w.sign(q) for p in refs(w, a[0]) for q in refs(w, a[1]))
    if atom == 'w_same':                         # the two references name the same star
        return bool(refs(w, a[0]) & refs(w, a[1]))
    if atom == 'w_aspect':                       # [refs, refs, kinds]
        return any(p != q and w.aspect(p, q) in a[2] for p in refs(w, a[0]) for q in refs(w, a[1]))
    if atom == 'w_n_aspecting':                  # [target, by, n]: at least n of 'by' together with or aspecting target
        t = refs(w, a[0])
        return sum(1 for q in refs(w, a[1]) if any(q != p and w.aspect(q, p) for p in t)) >= a[2]
    if atom == 'w_right':
        return any(p != q and w.on_right(p, q) for p in refs(w, a[0]) for q in refs(w, a[1]))
    if atom == 'w_superior':
        return any(p != q and w.superior(p, q) for p in refs(w, a[0]) for q in refs(w, a[1]))
    if atom == 'w_sect':
        return w.day == (a == 'day')
    if atom == 'w_dignity':
        return any(w.dignities(p) & set(a[1]) for p in refs(w, a[0]))
    if atom == 'w_under_rays':
        return any(w.under_rays(p) for p in refs(w, a))
    if atom == 'w_morning':
        return any(p in SEVEN and p != 'Sun' and w.morning(p) for p in refs(w, a))
    if atom == 'w_retro':
        return any(w.retro(p) for p in refs(w, a))
    if atom == 'w_waxing':
        return w.waxing() == bool(a)
    if atom == 'w_moon_phase':                   # [lo, hi]: Moon's elongation from the Sun in degrees
        e = _arc(w.lon['Sun'], w.lon['Moon'])
        return a[0] <= e < a[1]
    if atom == 'w_angularity':                   # [refs, angle|succedent|cadent, base]
        base = a[2] if len(a) > 2 else 'Asc'
        hs = {'angle': ANGLE, 'succedent': SUCCEDENT, 'cadent': CADENT}[a[1]]
        return any(w.house(p, b) in hs for p in refs(w, a[0]) for b in refs(w, base))
    if atom == 'w_operative':                    # [refs, true|false, base]
        base = a[2] if len(a) > 2 else 'Asc'
        return any((w.house(p, b) in OPERATIVE) == bool(a[1]) for p in refs(w, a[0]) for b in refs(w, base))
    if atom == 'w_term':                         # [point, lords]: the term of point's degree belongs to one of lords
        return any(term_lord(w.lon[p]) in refs(w, a[1]) for p in refs(w, a[0]))
    if atom == 'w_deg':                          # [point, sign, lo, hi]
        return any(w.sign(p) == a[1] and a[2] <= w.lon[p] % 30 < a[3] for p in refs(w, a[0]))
    if atom == 'w_gender':
        return w.gender == a
    if atom == 'w_orb':                          # [p, q, angle, orb]: within orb degrees of the exact aspect
        return any(p != q and abs(abs(((w.lon[q] - w.lon[p]) + 180) % 360 - 180) - a[2]) <= a[3]
                   for p in refs(w, a[0]) for q in refs(w, a[1]))
    if atom == 'w_syzygy':                       # the pre-natal lunation was a new / full moon
        return syzygy(w.pjd)[1] == a
    if atom in ('w_transmit', 'w_prof', 'w_zr', 'w_critical_year', 'w_life_node') + ('w_year_of_life', 'w_transit_orb', 'w_degree_tx', 'w_decennial', 'w_moon9'):
        if jd is None:
            raise ValueError(f'{atom} needs a date')
        return _eval_timing(w, atom, a, jd)
    if atom == 'w_transit_from':                 # [star, [houses], natal base]: its sign on the date counted from base
        if jd is None:
            raise ValueError('transit condition needs a date')
        t = int(sky(jd)[a[0]][0] // 30)
        return any((t - w.sign(b)) % 12 + 1 in a[1] for b in refs(w, a[2]))
    raise ValueError(f'unknown western atom {atom!r}')


# ── timing: Valens' operative year, zodiacal releasing, critical years, length of life ─────────────────────
YEAR = 365.2422
# IV.4-6, IV.10: the years each sign allots in the releasing from the Lots (its ruler's minimum period; Capricorn 27)
ZR_YEARS = [15, 8, 20, 25, 19, 20, 8, 15, 12, 27, 30, 12]
# III.15: critical years by the Lot of Fortune's sign
CRIT_SIGN = [9, 22, 20, 25, 12, 8, 30, 15, 12, 8, 30, 15]


def age_years(w: WChart, jd: float) -> float:
    return (jd - w.bjd) / YEAR


def year_offset(w: WChart, jd: float) -> int:
    """IV.11: the year of life (completed years + 1) divided by 12; the remainder r sends the year from a star to the
    sign r-th from it counting inclusively, i.e. (completed years) mod 12 signs on."""
    return int(age_years(w, jd)) % 12


def receivers(w: WChart, sign: int) -> set[str]:
    """The stars in a sign receive the year; an empty sign passes it to its ruler (IV.11: 'if the count ends at an
    empty place, they will be transmitting to the rulers of these signs' - applied to every transmitter, logged)."""
    inside = {p for p in SEVEN if w.sign(p) == sign}
    if w.sign('Asc') == sign:
        inside.add('Asc')
    return inside or {DOMICILE[sign]}


def zr_level1(start: int, t: float) -> tuple[int, float, int | None]:
    """(sign, start time in years, previous sign) of the first-level releasing period running at t years."""
    sign, acc, prev = start, 0.0, None
    while acc + ZR_YEARS[sign] <= t:
        acc += ZR_YEARS[sign]
        prev, sign = sign, (sign + 1) % 12
    return sign, acc, prev


def zr_sub(sign0: int, t_rel: float, unit: float) -> tuple[int, float]:
    """Sub-period within a period of sign0 that began t_rel ago: signs from sign0 in order, each its ZR_YEARS x unit;
    after the twelve signs, continue from the sign opposite sign0 (IV.4: 'the remaining time from the sign in
    opposition')."""
    order = [(sign0 + k) % 12 for k in range(12)] + [(sign0 + 6 + k) % 12 for k in range(12)]
    acc = 0.0
    for s in order:
        d = ZR_YEARS[s] * unit
        if t_rel < acc + d:
            return s, acc
        acc += d
    return order[-1], acc


def zr_start(w: WChart, lot: str) -> int:
    """IV.4: health from the Lot of Fortune; occupation from Daimon - from the sign after it when both share a sign."""
    f, d = w.sign('Fortune'), w.sign('Daimon')
    if lot == 'Fortune':
        return f
    return (d + 1) % 12 if d == f else d


def zr_period(w: WChart, lot: str, level: int, jd: float) -> tuple[int, int | None]:
    t = age_years(w, jd)
    s1, a1, prev = zr_level1(zr_start(w, lot), t)
    if level == 1:
        return s1, prev
    s2, _ = zr_sub(s1, t - a1, 1 / 12)
    return s2, s1


TEST_KEYS = {'ruler', 'houses', 'base', 'operative', 'contains', 'not_contains', 'beheld_by', 'not_beheld_by',
             'ruler_angular', 'ruler_house', 'ruler_afflicted', 'prev_ruler', 'prev_sign', 'sign', 'transited_by'}


def _sign_test(w: WChart, sign: int, test: dict, prev: int | None = None, jd: float | None = None) -> bool:
    """Conditions on a sign reached by a time-lord method; all given keys must hold. ruler (refs); houses ([..]
    counted from 'base', default Asc); operative (bool); contains / not_contains (refs: stars in the sign);
    beheld_by / not_beheld_by (refs: a star together with or in sign aspect to it); ruler_angular (bool, from the
    Ascendant); ruler_house ([..]); ruler_afflicted (bool: a malefic together with or aspecting the ruler and no
    benefic); prev_ruler (refs: the ruler of the sign the period came from); prev_sign ([..]); sign ([..])."""
    ruler = DOMICILE[sign]
    base = test.get('base', 'Asc')
    hb = lambda s: (s - w.sign(base)) % 12 + 1
    occupants = {p for p in SEVEN if w.sign(p) == sign}
    seen = lambda ps: any(q in SEVEN and (w.sign(q) == sign or ASPECT_OF.get((sign - w.sign(q)) % 12)) for q in ps)
    if 'ruler' in test and ruler not in refs(w, test['ruler']):
        return False
    if 'houses' in test and hb(sign) not in test['houses']:
        return False
    if 'operative' in test and (hb(sign) in OPERATIVE) != test['operative']:
        return False
    if 'contains' in test and not occupants & refs(w, test['contains']):
        return False
    if 'not_contains' in test and occupants & refs(w, test['not_contains']):
        return False
    if 'beheld_by' in test and not seen(refs(w, test['beheld_by'])):
        return False
    if 'not_beheld_by' in test and seen(refs(w, test['not_beheld_by'])):
        return False
    if 'ruler_angular' in test and (w.house(ruler) in ANGLE) != test['ruler_angular']:
        return False
    if 'ruler_house' in test and w.house(ruler) not in test['ruler_house']:
        return False
    if 'ruler_afflicted' in test:
        aff = (any(m != ruler and w.aspect(m, ruler) for m in MALEFICS)
               and not any(b != ruler and w.aspect(b, ruler) for b in BENEFICS))
        if aff != test['ruler_afflicted']:
            return False
    if 'prev_ruler' in test and (prev is None or DOMICILE[prev] not in refs(w, test['prev_ruler'])):
        return False
    if 'prev_sign' in test and (prev is None or prev not in test['prev_sign']):
        return False
    if 'sign' in test and sign not in test['sign']:
        return False
    if 'transited_by' in test:                   # [star, kinds]: the star's transit sign on the date relative to it
        star, kinds = test['transited_by']
        t = int(sky(jd)[star][0] // 30)
        if ASPECT_OF.get((sign - t) % 12) not in kinds:
            return False
    return True


def _check_test(t: dict) -> None:
    if not isinstance(t, dict) or not set(t) <= TEST_KEYS:
        raise ValueError(f'bad sign test {t}')
    if 'transited_by' in t and (t['transited_by'][0] not in SEVEN or not set(t['transited_by'][1]) <= ASPECT_KINDS):
        raise ValueError(f'bad transit test {t}')
    for k in ('ruler', 'contains', 'not_contains', 'beheld_by', 'not_beheld_by', 'prev_ruler', 'base'):
        if k in t:
            _check_ref(t[k])


def _check_timing(atom: str, a) -> None:
    if atom == 'w_transmit':                     # [from refs, to refs]
        _check_ref(a[0]), _check_ref(a[1])
    elif atom == 'w_prof':                       # [from point, test]
        _check_ref(a[0])
        _check_test(a[1])
    elif atom == 'w_zr':                         # [Fortune|Daimon, 1|2, test]
        if a[0] not in ('Fortune', 'Daimon') or a[1] not in (1, 2):
            raise ValueError(f'bad releasing {a}')
        _check_test(a[2])
    elif atom == 'w_critical_year':
        if a not in ('fortune_sign', 'malefic_to_fortune'):
            raise ValueError(f'bad critical-year kind {a}')
    elif atom == 'w_life_node':                  # [window years]
        if not 0 < a[0] <= 3:
            raise ValueError(f'bad window {a}')
    elif atom == 'w_year_of_life':               # {'in': [years]} or {'every': n}: the current year of life
        if not (isinstance(a, dict) and (set(a) == {'in'} or set(a) == {'every'})):
            raise ValueError(f'bad year-of-life {a}')
    elif atom == 'w_transit_orb':                # [transiting star, natal point(s), orb deg]
        if a[0] not in SEVEN or not 0 < a[2] <= 5:
            raise ValueError(f'bad transit orb {a}')
        _check_ref(a[1])
    elif atom == 'w_degree_tx':                  # [from star, to star]
        if a[0] not in SEVEN or a[1] not in SEVEN:
            raise ValueError(f'bad degree transmission {a}')
    elif atom == 'w_decennial':                  # [level 1|2, refs, optional prev refs]
        if a[0] not in (1, 2):
            raise ValueError(f'bad decennial level {a}')
        _check_ref(a[1])
        if len(a) > 2:
            _check_ref(a[2])
    elif atom == 'w_moon9':                      # sign test
        _check_test(a)


def _eval_timing(w: WChart, atom: str, a, jd: float) -> bool:
    if atom == 'w_transmit':
        off = year_offset(w, jd)
        to = refs(w, a[1])
        return any(receivers(w, (w.sign(p) + off) % 12) & to for p in refs(w, a[0]))
    if atom == 'w_prof':                         # the sign the year comes to from a point (prev = the point's sign)
        off = year_offset(w, jd)
        return any(_sign_test(w, (w.sign(p) + off) % 12, a[1], w.sign(p), jd) for p in refs(w, a[0]))
    if atom == 'w_zr':
        sign, prev = zr_period(w, a[0], a[1], jd)
        return _sign_test(w, sign, a[2], prev, jd)
    if atom == 'w_critical_year':
        n = int(age_years(w, jd)) + 1                # the current year of life
        if a == 'fortune_sign':
            return n % CRIT_SIGN[w.sign('Fortune')] == 0
        steps = set()
        for m in MALEFICS:
            d = (w.sign('Fortune') - w.sign(m)) % 12  # the Lot counted from the malefic
            # III.15: opposition 7; trine on the right 9 / left 5; square right 10 / left 4; sextile right 11 / left 3;
            # in the sign preceding the Lot 12; in contact (same sign) 2
            steps.add({6: 7, 4: 9, 8: 5, 3: 10, 9: 4, 2: 11, 10: 3, 1: 12, 0: 2}.get(d))
        return any(k and n % k == 0 for k in steps)
    if atom == 'w_life_node':
        y = life_node_years(w)
        return y is not None and abs(age_years(w, jd) - y) <= a[0]
    if atom == 'w_year_of_life':
        n = int(age_years(w, jd)) + 1
        return n in a['in'] if 'in' in a else n % a['every'] == 0
    if atom == 'w_transit_orb':
        t = sky(jd)[a[0]][0]
        return any(abs(((t - w.lon[q]) + 180) % 360 - 180) <= a[2] for q in refs(w, a[1]))
    if atom == 'w_degree_tx':
        return degree_tx_hit(w, a[0], a[1], jd)
    if atom == 'w_decennial':
        l1, l2, prev = decennial(w, jd)
        lord = l1 if a[0] == 1 else l2
        if lord not in refs(w, a[1]):
            return False
        if len(a) > 2:
            other = l1 if a[0] == 2 else prev
            return other is not None and other in refs(w, a[2])
        return True
    if atom == 'w_moon9':
        return _sign_test(w, moon9_sign(w, jd), a, None, jd)
    raise ValueError(atom)


def oblique_ascension(lon: float, lat: float, eps: float = 23.44) -> float:
    """Oblique ascension (deg) of an ecliptic point at geographic latitude lat."""
    import math
    l, e, f = math.radians(lon), math.radians(eps), math.radians(lat)
    ra = math.degrees(math.atan2(math.sin(l) * math.cos(e), math.cos(l))) % 360
    dec = math.asin(math.sin(e) * math.sin(l))
    x = max(-1.0, min(1.0, math.tan(f) * math.tan(dec)))
    return (ra - math.degrees(math.asin(x))) % 360


def life_node_years(w: WChart) -> float | None:
    """III.12-13: the distance from the pre-natal new/full moon to the ascending node in the order of the signs,
    counted from the Ascendant in the order of the signs for day births (toward MC, against the order, for night
    births); the rising times of the arc from the Ascendant to that point are the years of life. (Valens uses it when
    the nativity lacks a controller or houseruler; applied to every chart here - logged.) Births above 66 deg
    latitude: no value."""
    if abs(w.lat) >= 66:
        return None
    d = _arc(w.lon['Syzygy'], w.lon['Node'])
    if w.day:
        end = (w.asc + d) % 360
        y = (oblique_ascension(end, w.lat) - oblique_ascension(w.asc, w.lat)) % 360
    else:
        end = (w.asc - d) % 360
        y = (oblique_ascension(w.asc, w.lat) - oblique_ascension(end, w.lat)) % 360
    return y if y <= 120 else None              # an 'excessive' count: the text's correction is underdetermined


# ── Valens Books V, VI, IX: degree contacts, the 10-year-9-month periods, the 9-year zones, years of life ─────────
# VI.1: days per degree of each star's period (the Sun 19 days per degree, etc.)
DAYS_PER_DEG = {'Sun': 19, 'Moon': 25, 'Saturn': 30, 'Jupiter': 12, 'Mars': 15, 'Venus': 8, 'Mercury': 20}
MINOR_MONTHS = MINOR_YEARS                       # VI.5: within a 129-month period each star takes its period in months


def decennial_order(w: WChart) -> list[str]:
    """VI.5: the apheta is the sect light if well situated (here: not in a place preceding an angle - a choice), else
    the other light, else the star following the Ascendant; the rest follow in zodiacal order of their positions."""
    def ok(p):
        return w.house(p) not in CADENT
    first = next((p for p in ([w.sect_light, 'Moon' if w.day else 'Sun']) if ok(p)), None)
    if first is None:
        first = min(SEVEN, key=lambda p: _arc(w.asc, w.lon[p]))
    rest = sorted((p for p in SEVEN if p != first), key=lambda p: _arc(w.lon[first], w.lon[p]))
    return [first] + rest


def decennial(w: WChart, jd: float) -> tuple[str, str, str | None]:
    """(first-level lord, second-level lord, previous first-level lord) at jd."""
    order = decennial_order(w)
    months = age_years(w, jd) * 12
    k, rem = int(months // 129), months % 129
    lord = order[k % 7]
    prev = order[(k - 1) % 7] if k > 0 else None
    i = order.index(lord)
    acc = 0.0
    for s in order[i:] + order[:i]:
        acc += MINOR_MONTHS[s]
        if rem < acc:
            return lord, s, prev
    return lord, order[i - 1], prev


def degree_tx_hit(w: WChart, a: str, b: str, jd: float, deg_window: float = 3.0) -> bool:
    """VI.1: a star 'reaches' another after (zodiacal arc from it to the other) x its days-per-degree, repeated in
    cycles; the contact is felt within 3 degrees either side (VI.1)."""
    arc = _arc(w.lon[a], w.lon[b])
    if arc < 1:
        return False
    per = arc * DAYS_PER_DEG[a]
    t = jd - w.bjd
    win = deg_window * DAYS_PER_DEG[a]
    k = max(1, round(t / per))
    return abs(t - k * per) <= win


def moon9_sign(w: WChart, jd: float) -> int:
    """IX.3: nine years to each sign from the Moon's sign in the order of the signs (108 years in all)."""
    return (w.sign('Moon') + int(age_years(w, jd) // 9)) % 12
