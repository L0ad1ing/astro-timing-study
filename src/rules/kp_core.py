"""
src/rules/kp_core.py — Krishnamurti Padhdhati primitives, from the KP Readers (K.S. Krishnamurti).

Reader I (Casting the horoscope) pp. 56-58: Krishnamurti ayanamsa (zodiacs coincide 291 A.D., precession at Newcomb's
  rate) - Swiss Ephemeris SIDM_KRISHNAMURTI; houses by the Placidus method with Raphael's tables (p. ~3314 of the
  text), cusp to cusp.
Reader III (Predictive Stellar Astrology) pp. 10-12: each star (13 deg 20') is divided into 9 subs in proportion to the
  Vimshottari years, the first sub ruled by the star lord and the rest in dasa order (Sun 40', Moon 1 deg 6'40",
  Mars/Ketu 46'40", Rahu 2 deg, Jupiter 1 deg 46'40", Saturn 2 deg 6'40", Mercury 1 deg 53'20", Venus 2 deg 13'20").
Reader IV (Marriage, Married life, Children) p. 111 and Reader III p. ~24535: significators of a house, strongest first:
  (1) planets in the star of an occupant of the house, (2) the occupants, (3) planets in the star of the lord of the
  house, (4) the lord; (5) planets conjoined with or aspecting the above (logged, not used: 'aspect' unspecified).
Reader III pp. 41-42: Rahu and Ketu act for the planet conjoined with them, then the planet aspecting them, then the
  lord of the sign they occupy (and their star lord).
"""
from __future__ import annotations

from src import features as F

LORDS = F.DASHA_LORDS                       # Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury
YEARS = F.DASHA_YEARS
NAK = 360 / 27
NINE = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
SWE_ID = {'Sun': 0, 'Moon': 1, 'Mercury': 2, 'Venus': 3, 'Mars': 4, 'Jupiter': 5, 'Saturn': 6, 'Rahu': 10}


def star_lord(lon: float) -> str:
    return LORDS[int((lon % 360) // NAK) % 9]


def sub_lord(lon: float) -> str:
    x = lon % 360
    k = int(x // NAK)
    pos = (x - k * NAK) / NAK * 120             # position within the star in 'years' of 120
    i = k % 9
    for j in range(9):
        y = YEARS[(i + j) % 9]
        if pos < y:
            return LORDS[(i + j) % 9]
        pos -= y
    return LORDS[(i + 8) % 9]


def sub_sub_lord(lon: float) -> str:
    """The sub-sub lord: the sub divided again in Vimshottari proportion, starting from the sub lord (modern K.P.)."""
    x = lon % 360
    k = int(x // NAK)
    pos = (x - k * NAK) / NAK * 120
    i = k % 9
    for j in range(9):
        y = YEARS[(i + j) % 9]
        if pos < y:
            s = (i + j) % 9                    # sub lord index; pos now within the sub, of length y
            q = pos / y * 120
            for m in range(9):
                z = YEARS[(s + m) % 9]
                if q < z:
                    return LORDS[(s + m) % 9]
                q -= z
            return LORDS[(s + 8) % 9]
        pos -= y
    return LORDS[(i + 8) % 9]


def sign_lord(lon: float) -> str:
    return F.SIGN_LORD[int((lon % 360) // 30)]


def kp_positions(bjd: float, lat: float, lon: float) -> dict:
    """Sidereal (Krishnamurti) longitudes of the nine and the 12 Placidus cusps (cusp[1] = ascendant)."""
    swe, _ = F._swe()
    swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
    flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    pos = {p: swe.calc_ut(bjd, i, flag)[0][0] % 360 for p, i in SWE_ID.items()}
    pos['Ketu'] = (pos['Rahu'] + 180) % 360
    cusps = swe.houses_ex(bjd, lat, lon, b'P', flag)[0]
    swe.set_sid_mode(swe.SIDM_LAHIRI)            # the rest of the engine is Lahiri
    c = [None] + [x % 360 for x in cusps[:12]]
    return {'lon': pos, 'cusp': c}


def house_of(lon: float, cusp: list) -> int:
    """Cusp-to-cusp house (Placidus)."""
    for h in range(1, 13):
        a, b = cusp[h], cusp[h % 12 + 1]
        if (lon - a) % 360 < (b - a) % 360:
            return h
    return 12


class KPChart:
    def __init__(self, bjd: float, lat: float, lon: float):
        k = kp_positions(bjd, lat, lon)
        self.lon, self.cusp = k['lon'], k['cusp']
        self.house = {p: house_of(self.lon[p], self.cusp) for p in NINE}
        self.star = {p: star_lord(self.lon[p]) for p in NINE}
        self.sub = {p: sub_lord(self.lon[p]) for p in NINE}
        self.csl = {h: sub_lord(self.cusp[h]) for h in range(1, 13)}          # cusp sub lords
        self.cusp_star = {h: star_lord(self.cusp[h]) for h in range(1, 13)}
        self.lord = {h: sign_lord(self.cusp[h]) for h in range(1, 13)}        # lord of the sign on the cusp
        self._sig = None

    def occupants(self, h: int) -> list[str]:
        return [p for p in NINE if self.house[p] == h]

    def _node_agent(self, node: str) -> list[str]:
        """Reader III pp. 41-42: conjoined planets, then aspecting, then the sign lord (and the star lord)."""
        s = int(self.lon[node] // 30)
        conj = [p for p in NINE if p not in ('Rahu', 'Ketu') and int(self.lon[p] // 30) == s]
        return conj + [sign_lord(self.lon[node]), self.star[node]]

    def significators(self, h: int) -> dict[str, int]:
        """Planet -> strongest level (1..4) at which it signifies house h."""
        out: dict[str, int] = {}

        def put(p, lvl):
            if p not in out or lvl < out[p]:
                out[p] = lvl
        occ = self.occupants(h)
        for p in NINE:
            if self.star[p] in occ:
                put(p, 1)
        for p in occ:
            put(p, 2)
        for p in NINE:
            if self.star[p] == self.lord[h]:
                put(p, 3)
        put(self.lord[h], 4)
        return out

    def signified(self, p: str) -> set[int]:
        """Houses a planet signifies (any level); the nodes also signify what their agents signify."""
        if self._sig is None:
            base = {q: set() for q in NINE}
            for h in range(1, 13):
                for q in self.significators(h):
                    base[q].add(h)
            for n in ('Rahu', 'Ketu'):
                for a in self._node_agent(n):
                    base[n] |= {h for h in range(1, 13) if a in self.significators(h) and self.significators(h)[a] <= 2} \
                        if a != self.star[n] else set()
            self._sig = base
        return self._sig[p]


def badhaka_house(asc_sign: int) -> int:
    """R3 pp. 160-161: movable lagna -> 11th, fixed -> 9th, common -> 7th."""
    return 11 if asc_sign % 3 == 0 else 9 if asc_sign % 3 == 1 else 7


def kp_dasha(moon_kp: float, bjd: float, jd: float) -> dict:
    """Vimshottari from the KP (Krishnamurti ayanamsa) Moon - R3 p. 10, R4 examples."""
    from src.rules import bphs_dasha as BD
    v = BD.vimshottari(moon_kp, bjd, jd)
    return {'MD': v['MD']['lord'], 'AD': v['AD']['lord'], 'PD': v['PD']['lord'], 'SD': v['SD']['lord']}


_TR: dict = {}


def kp_transit(jd: float) -> dict[str, float]:
    """KP (Krishnamurti ayanamsa) longitudes of the transiting nine at jd."""
    if jd not in _TR:
        swe, _ = F._swe()
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
        pos = {p: swe.calc_ut(jd, i, flag)[0][0] % 360 for p, i in SWE_ID.items()}
        pos['Ketu'] = (pos['Rahu'] + 180) % 360
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        if len(_TR) > 20000:
            _TR.clear()
        _TR[jd] = pos
    return _TR[jd]
