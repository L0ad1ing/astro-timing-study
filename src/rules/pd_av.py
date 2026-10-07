"""
src/rules/pd_av.py — Phaladeepika ch. XXIII-XXIV Ashtakavarga (1961 printing pp. 310-334).

The bindu tables of XXIII v. 3-9 were checked cell by cell against src/features.BAV (the common tables) and are
identical; they differ from BPHS's (src/rules/bphs_av.REKHA) in Moon's AV (Moon 9th, Mars 9th, Jupiter 2nd/12th) and
Venus's AV (Mars 4th/5th). Reductions (XXIV v. 16-22) and the rasi/graha multipliers (v. 24-26) are the BPHS ones,
so bphs_av's functions are reused with the Phaladeepika table. Samudaya = the seven planets' AVs (XXIV v. 34-35:
total 337).
"""
from __future__ import annotations

from src import features as F
from src.rules import bphs_av as BAV

PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']


class PDAV:
    def __init__(self, signs: dict[str, int], lagna: int):
        self.signs, self.lagna = signs, lagna
        ref = {**{p: signs[p] for p in PLANETS}, 'Lagna': lagna}
        self.bindus = {}
        for planet in PLANETS:
            row = [0] * 12
            for c, houses in F.BAV[planet].items():
                for h in houses:
                    row[(ref[c] + h - 1) % 12] += 1
            self.bindus[planet] = row
        occupied = {signs[p] for p in PLANETS}
        self.reduced = {p: BAV.ekadhipatya_shodhana(BAV.trikona_shodhana(self.bindus[p]), occupied) for p in PLANETS}
        self.pinda = {p: sum(BAV.shodhya_pinda(self.reduced[p], signs)) for p in PLANETS}
        self.sav = [sum(self.bindus[p][s] for p in PLANETS) for s in range(12)]

    def star(self, planet: str, house: int, base: str = 'planet') -> set[int]:
        """XXIV v. 1-3, 7, 13: Sodhya pinda x bindus in the house from the planet (base 'planet') or from the Lagna
        ('lagna'), remainder by 27 = nakshatra from Ashwini (0 -> 27th); with its trines. 0-based indexes."""
        b = self.signs[planet] if base == 'planet' else self.lagna
        r = self.bindus[planet][(b + house - 1) % 12]
        n = (self.pinda[planet] * r % 27 - 1) % 27
        return {n, (n + 9) % 27, (n + 18) % 27}

    def sign_mult(self, planet: str, mult: int) -> set[int]:
        """XXIV v. 5-6: Sodhya pinda x mult, remainder by 12 = sign from Aries; with its trines."""
        s = (self.pinda[planet] * mult % 12 - 1) % 12
        return {s, (s + 4) % 12, (s + 8) % 12}

    def calamity_years(self, planet: str) -> list[int]:
        """XXIV v. 41-42: Samudaya figures from the Lagna to the planet (inclusive) x 7 / 27 -> the year; the same from
        the planet to the Lagna. Returned as the quotients (years of age)."""
        a, b = self.lagna, self.signs[planet]
        l2p = sum(self.sav[(a + i) % 12] for i in range((b - a) % 12 + 1))
        p2l = sum(self.sav[(b + i) % 12] for i in range((a - b) % 12 + 1))
        return [l2p * 7 // 27, p2l * 7 // 27]

    def benefic_year(self, benefics: list[str]) -> int:
        """XXIV v. 43: Samudaya figures in the houses occupied by benefics, x 7 / 27."""
        return sum(self.sav[s] for s in {self.signs[p] for p in benefics}) * 7 // 27
