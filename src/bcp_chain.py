"""
src/bcp_chain.py — The author's Bhrigu Chakra chain method (pre-registered: docs/prereg_bcp_chain.md).

  - Active house for completed age a: ((a - 1) mod 12) + 1 — the MAIN story.
  - Links: a house -> its lord and the planets in it; a planet -> the house it sits in and the houses it rules.
    Steps from the active house rank importance: 0 MAIN, 1-2 SECONDARY, 3-4 FAINT, more = background.
  - Cycle ruler for each 12-year cycle, in order of speed: Moon (ages 1-12), Mercury, Venus, Sun, Mars, Jupiter,
    Saturn (73-84).
Stories are assembled from the house and planet significations by code (no language model), so the wording
cannot drift toward whatever fits.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from src import features as F

KB = Path(__file__).resolve().parent / "knowledge_base"
HOUSES = json.loads((KB / "houses.json").read_text(encoding="utf-8"))
PLANETS = json.loads((KB / "planets.json").read_text(encoding="utf-8"))
CYCLE_RULERS = ["Moon", "Mercury", "Venus", "Sun", "Mars", "Jupiter", "Saturn"]
GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
WEIGHT = {0: 3, 1: 2, 2: 2, 3: 1, 4: 1}


def active_house(age: int) -> int:
    return ((max(1, age) - 1) % 12) + 1


def cycle_ruler(age: int) -> str:
    return CYCLE_RULERS[min(len(CYCLE_RULERS) - 1, (max(1, age) - 1) // 12)]


class Chart:
    def __init__(self, lagna: int, signs: dict[str, int]):
        """lagna: sign index of the Ascendant; signs: sign index per graha (Ketu optional)."""
        self.lagna = lagna
        self.signs = dict(signs)
        self.signs.setdefault("Ketu", (signs["Rahu"] + 6) % 12)
        self._steps = {a: self._bfs(a) for a in range(1, 13)}

    def house_of(self, planet: str) -> int:
        return (self.signs[planet] - self.lagna) % 12 + 1

    def rules(self, planet: str) -> list[int]:
        return [h for h in range(1, 13) if F.SIGN_LORD[(self.lagna + h - 1) % 12] == planet]

    def lord_of(self, house: int) -> str:
        return F.SIGN_LORD[(self.lagna + house - 1) % 12]

    def occupants(self, house: int) -> list[str]:
        return [p for p in GRAHAS if self.house_of(p) == house]

    def _bfs(self, active: int) -> dict[str, dict]:
        seen = {("H", active): 0}
        q = deque([("H", active)])
        while q:
            node = q.popleft()
            d = seen[node]
            if node[0] == "H":
                nxt = [("P", self.lord_of(node[1]))] + [("P", p) for p in self.occupants(node[1])]
            else:
                nxt = [("H", self.house_of(node[1]))] + [("H", h) for h in self.rules(node[1])]
            for n in nxt:
                if n not in seen:
                    seen[n] = d + 1
                    q.append(n)
        return {"houses": {h: d for (k, h), d in seen.items() if k == "H"},
                "planets": {p: d for (k, p), d in seen.items() if k == "P"}}

    def steps(self, active: int) -> dict[int, int]:
        return self._steps[active]["houses"]

    def score(self, active: int, targets: list[int]) -> int:
        """MAIN 3 / SECONDARY 2 / FAINT 1 / background 0 for the closest target house."""
        st = self.steps(active)
        return max(WEIGHT.get(st.get(h, 99), 0) for h in targets)

    def story(self, active: int, age: int | None = None) -> str:
        lord = self.lord_of(active)
        sits = self.house_of(lord)
        others = [h for h in self.rules(lord) if h != active]
        occ = self.occupants(active)
        co = [p for p in GRAHAS if p != lord and self.signs[p] == self.signs[lord]]
        lines = [f"MAIN — house {active}: {HOUSES[str(active)]}.",
                 f"Through its lord {lord} ({PLANETS[lord]['dasha_theme']}), sitting in house {sits}: {HOUSES[str(sits)]}."]
        if others:
            lines.append(f"{lord} also rules house {', '.join(map(str, others))}: "
                         + "; ".join(HOUSES[str(h)] for h in others) + ".")
        if occ:
            lines.append("In the main house: " + "; ".join(
                f"{p} (rules {', '.join(map(str, self.rules(p))) or 'no house'}: {PLANETS[p]['dasha_theme']})" for p in occ) + ".")
        if co:
            lines.append(f"With {lord}: " + "; ".join(
                f"{p} (rules {', '.join(map(str, self.rules(p))) or 'no house'})" for p in co) + ".")
        if age is not None:
            cr = cycle_ruler(age)
            lines.append(f"Cycle ruler {cr} (ages {12 * ((max(1, age) - 1) // 12) + 1}-{12 * ((max(1, age) - 1) // 12) + 12}): "
                         f"{PLANETS[cr]['dasha_theme']}; sits in house {self.house_of(cr)}.")
        return " ".join(lines)
