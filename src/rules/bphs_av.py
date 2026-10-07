"""
src/rules/bphs_av.py — Ashtakavarga exactly as BPHS ch. 68 gives it (G.C. Sharma tr., Sagar 1995, vol. 2 pp. 505-530).

REKHA[planet][contributor] = houses, counted from the contributor's natal sign, where the contributor gives a rekha
(auspicious line) in that planet's Ashtakavarga. Transcribed from the Rekhaprada chakras (pp. 521-527) and checked
against the Bindu chakras (pp. 510-529, complements) and the verses; totals Sun 48, Moon 49, Mars 39, Mercury 54,
Jupiter 56, Venus 52, Saturn 39, Ascendant 49.

Differences from the commonly used tables (and from src/features.py BAV), all confirmed by both chakras, the verse
and R. Santhanam's translation: Moon's AV - Moon gives a rekha in the 9th, Mars does not; Jupiter in the 2nd, not
the 12th. Venus's AV - Mars in the 4th, not the 5th. Ascendant's AV: book p. 530 is missing from the scan; table
from Santhanam vol. 2 p. 864-865, which matches the complement of Sharma's Bindu chakra on p. 529.
"""
from __future__ import annotations

CONTRIB = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Lagna']

REKHA = {
    'Sun': {'Sun': [1, 2, 4, 7, 8, 9, 10, 11], 'Moon': [3, 6, 10, 11], 'Mars': [1, 2, 4, 7, 8, 9, 10, 11],
            'Mercury': [3, 5, 6, 9, 10, 11, 12], 'Jupiter': [5, 6, 9, 11], 'Venus': [6, 7, 12],
            'Saturn': [1, 2, 4, 7, 8, 9, 10, 11], 'Lagna': [3, 4, 6, 10, 11, 12]},
    'Moon': {'Sun': [3, 6, 7, 8, 10, 11], 'Moon': [1, 3, 6, 7, 9, 10, 11], 'Mars': [2, 3, 5, 6, 10, 11],
             'Mercury': [1, 3, 4, 5, 7, 8, 10, 11], 'Jupiter': [1, 2, 4, 7, 8, 10, 11],
             'Venus': [3, 4, 5, 7, 9, 10, 11], 'Saturn': [3, 5, 6, 11], 'Lagna': [3, 6, 10, 11]},
    'Mars': {'Sun': [3, 5, 6, 10, 11], 'Moon': [3, 6, 11], 'Mars': [1, 2, 4, 7, 8, 10, 11], 'Mercury': [3, 5, 6, 11],
             'Jupiter': [6, 10, 11, 12], 'Venus': [6, 8, 11, 12], 'Saturn': [1, 4, 7, 8, 9, 10, 11],
             'Lagna': [1, 3, 6, 10, 11]},
    'Mercury': {'Sun': [5, 6, 9, 11, 12], 'Moon': [2, 4, 6, 8, 10, 11], 'Mars': [1, 2, 4, 7, 8, 9, 10, 11],
                'Mercury': [1, 3, 5, 6, 9, 10, 11, 12], 'Jupiter': [6, 8, 11, 12], 'Venus': [1, 2, 3, 4, 5, 8, 9, 11],
                'Saturn': [1, 2, 4, 7, 8, 9, 10, 11], 'Lagna': [1, 2, 4, 6, 8, 10, 11]},
    'Jupiter': {'Sun': [1, 2, 3, 4, 7, 8, 9, 10, 11], 'Moon': [2, 5, 7, 9, 11], 'Mars': [1, 2, 4, 7, 8, 10, 11],
                'Mercury': [1, 2, 4, 5, 6, 9, 10, 11], 'Jupiter': [1, 2, 3, 4, 7, 8, 10, 11],
                'Venus': [2, 5, 6, 9, 10, 11], 'Saturn': [3, 5, 6, 12], 'Lagna': [1, 2, 4, 5, 6, 7, 9, 10, 11]},
    'Venus': {'Sun': [8, 11, 12], 'Moon': [1, 2, 3, 4, 5, 8, 9, 11, 12], 'Mars': [3, 4, 6, 9, 11, 12],
              'Mercury': [3, 5, 6, 9, 11], 'Jupiter': [5, 8, 9, 10, 11], 'Venus': [1, 2, 3, 4, 5, 8, 9, 10, 11],
              'Saturn': [3, 4, 5, 8, 9, 10, 11], 'Lagna': [1, 2, 3, 4, 5, 8, 9, 11]},
    'Saturn': {'Sun': [1, 2, 4, 7, 8, 10, 11], 'Moon': [3, 6, 11], 'Mars': [3, 5, 6, 10, 11, 12],
               'Mercury': [6, 8, 9, 10, 11, 12], 'Jupiter': [5, 6, 11, 12], 'Venus': [6, 11, 12],
               'Saturn': [3, 5, 6, 11], 'Lagna': [1, 3, 4, 6, 10, 11]},
    'Lagna': {'Sun': [3, 4, 6, 10, 11, 12], 'Moon': [3, 6, 10, 11, 12], 'Mars': [1, 3, 6, 10, 11],
              'Mercury': [1, 2, 4, 6, 8, 10, 11], 'Jupiter': [1, 2, 4, 5, 6, 7, 9, 10, 11],
              'Venus': [1, 2, 3, 4, 5, 8, 9], 'Saturn': [1, 3, 4, 6, 10, 11], 'Lagna': [3, 6, 10, 11]},
}
TOTALS = {'Sun': 48, 'Moon': 49, 'Mars': 39, 'Mercury': 54, 'Jupiter': 56, 'Venus': 52, 'Saturn': 39, 'Lagna': 49}


def bav(signs: dict[str, int], lagna: int) -> dict[str, list[int]]:
    """Rekhas in each sign (0 = Aries) of each Ashtakavarga. signs: natal sign of the seven planets."""
    ref = {**{p: signs[p] for p in CONTRIB if p != 'Lagna'}, 'Lagna': lagna}
    out = {}
    for planet, table in REKHA.items():
        row = [0] * 12
        for c, houses in table.items():
            for h in houses:
                row[(ref[c] + h - 1) % 12] += 1
        out[planet] = row
    return out


TRIADS = [(0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)]
OWNERS = {'Mars': (0, 7), 'Venus': (1, 6), 'Mercury': (2, 5), 'Jupiter': (8, 11), 'Saturn': (9, 10)}
RASHI_MANA = [7, 10, 8, 4, 10, 5, 7, 8, 9, 5, 11, 12]                    # Table 36-A (ch. 71 v. 2-3)
GRAHA_MANA = {'Sun': 5, 'Moon': 5, 'Mars': 8, 'Mercury': 5, 'Jupiter': 10, 'Venus': 7, 'Saturn': 5}   # 36-B


def trikona_shodhana(row: list[int]) -> list[int]:
    """Ch. 69 v. 3-5: in each triad of trinal signs subtract the least; a triad with a zero is untouched;
    equal values all go to zero (which the subtraction already does)."""
    out = list(row)
    for t in TRIADS:
        m = min(row[s] for s in t)
        for s in t:
            out[s] = row[s] - m
    return out


def ekadhipatya_shodhana(row: list[int], occupied: set[int]) -> list[int]:
    """Ch. 70 v. 1-5 (rules as summarised on p. 549). occupied = signs holding any of the seven planets (Rahu and
    Ketu not counted, p. 548). Cancer and Leo are never reduced."""
    out = list(row)
    for a, b in OWNERS.values():
        if out[a] == 0 or out[b] == 0:
            continue                                          # rule I(iii)
        oa, ob = a in occupied, b in occupied
        if oa and ob:
            continue                                          # rule I(ii)
        if oa != ob:                                          # rule II
            occ, un = (a, b) if oa else (b, a)
            if out[occ] >= out[un]:
                out[un] = 0
            else:
                # v. 3 Sanskrit: 'unena samam anyasmin sodhayed grahavarjite' - make the planetless sign equal to
                # the lesser (occupied) figure. The translation gives two other versions (p. 547: subtract; p. 549:
                # raise the occupied one) - logged in docs/BPHS_ENGINE_NOTES.md.
                out[un] = out[occ]
        else:                                                 # rule III
            if out[a] == out[b]:
                out[a] = out[b] = 0
            else:
                lo = min(out[a], out[b])
                out[a] = out[b] = lo
    return out


def shodhya_pinda(reduced: list[int], signs: dict[str, int]) -> tuple[int, int]:
    """Ch. 71 v. 1-4: rashi pinda = sum(reduced x sign multiplier); graha pinda = sum over the seven planets of the
    reduced figure in their sign x planet multiplier. Shodhya pinda = rashi + graha."""
    rashi = sum(r * m for r, m in zip(reduced, RASHI_MANA))
    graha = sum(reduced[signs[p]] * GRAHA_MANA[p] for p in GRAHA_MANA)
    return rashi, graha


AYU_DAYS = {0: 2, 1: 1.5, 2: 1, 3: 0.5, 4: 7.5}               # ch. 73 v. 1-4, Table-37 (days)
AYU_YEARS = {5: 2, 6: 4, 7: 6, 8: 8}                              # (years)


def ayu_years(row: list[int]) -> float:
    """Ch. 73: span contributed by one Ashtakavarga (years; days at 365.25 per year)."""
    return sum(AYU_YEARS.get(r, 0) + AYU_DAYS.get(r, 0) / 365.25 for r in row)


class AV:
    """Everything ch. 68-72 derive from a birth chart: raw rekhas, reduced rows and Shodhya pinda per planet."""
    PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

    def __init__(self, signs: dict[str, int], lagna: int):
        self.signs, self.lagna = signs, lagna
        self.rekhas = bav(signs, lagna)
        occupied = {signs[p] for p in self.PLANETS}
        self.trikona = {p: trikona_shodhana(self.rekhas[p]) for p in self.PLANETS}
        self.reduced = {p: ekadhipatya_shodhana(self.trikona[p], occupied) for p in self.PLANETS}
        self.pinda = {p: sum(shodhya_pinda(self.reduced[p], signs)) for p in self.PLANETS}

    def point(self, planet: str, house: int) -> tuple[set[int], set[int]]:
        """Ch. 72 v. 7-42: rekhas in the given house from the planet (its own AV) x Shodhya pinda; remainder by 27 =
        nakshatra from Ashwini (0 -> 27th), by 12 = sign from Aries (0 -> 12th, p. 564); with their trines
        (nakshatras 10th and 19th, signs 5th and 9th). Returns (nakshatra indexes, sign indexes), 0-based."""
        r = self.rekhas[planet][(self.signs[planet] + house - 1) % 12]
        prod = r * self.pinda[planet]
        n = (prod % 27 - 1) % 27
        s = (prod % 12 - 1) % 12
        return {n, (n + 9) % 27, (n + 18) % 27}, {s, (s + 4) % 12, (s + 8) % 12}

    @property
    def samudaya(self) -> list[int]:
        """Ch. 74 v. 1-2 and example p. 579: rekhas of all eight Ashtakavargas (including the Ascendant's) per sign;
        example 93 totals 45 36 36 28 26 30 28 33 27 33 30 34."""
        return [sum(self.rekhas[p][s] for p in self.rekhas) for s in range(12)]

    def ayu(self) -> float:
        """Ch. 73: half the sum of the spans of all eight Ashtakavargas (incl. the Ascendant's)."""
        return sum(ayu_years(self.rekhas[p]) for p in self.rekhas) / 2

    def saturn_years(self) -> dict[str, int]:
        """Ch. 72 v. 37-40: rekhas in Saturn's AV summed from the Lagna to Saturn (inclusive) and from Saturn to the
        Lagna; their sum. Checked against example 93 (17 + 29 = 46)."""
        row, a, b = self.rekhas['Saturn'], self.lagna, self.signs['Saturn']
        l2s = sum(row[(a + i) % 12] for i in range((b - a) % 12 + 1))
        s2l = sum(row[(b + i) % 12] for i in range((a - b) % 12 + 1))
        return {'lagna_to_saturn': l2s, 'saturn_to_lagna': s2l, 'total': l2s + s2l}


def sav(b: dict[str, list[int]]) -> list[int]:
    """Samudaya (sum) of the seven planets' Ashtakavargas (the Lagna's own AV is not added; see ch. 74)."""
    return [sum(b[p][s] for p in CONTRIB if p != 'Lagna') for s in range(12)]
