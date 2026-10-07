"""
src/rules/bphs_nabhasa.py — the 32 Nabhasa yogas, BPHS vol. 1 ch. 37 (G.C. Sharma tr., Sagar; book pp. 495-517).
Only the seven planets count (Rahu and Ketu are not named). active(signs, lagna, benefics) returns the set of yogas
that apply, with the book's precedence: the Sankhya yogas only when no other Nabhasa yoga forms (v. 16-17); an Ashraya
yoga gives way to an Akriti yoga (notes p. 501, the Nauka-vs-Veena example p. 500).
"""
from __future__ import annotations

SEVEN = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
MOVABLE, FIXED, DUAL = {0, 3, 6, 9}, {1, 4, 7, 10}, {2, 5, 8, 11}


def active(signs: dict[str, int], lagna: int, benefics: set[str]) -> set[str]:
    sg = {signs[p] for p in SEVEN}
    hs = {(signs[p] - lagna) % 12 + 1 for p in SEVEN}
    house = {p: (signs[p] - lagna) % 12 + 1 for p in SEVEN}
    ben = [p for p in SEVEN if p in benefics and p != 'Moon']           # notes p. 497: the Moon not counted
    mal = [p for p in SEVEN if p not in benefics]
    out = set()
    ashraya = set()
    if sg <= MOVABLE: ashraya.add('Rajju')                             # v. 7
    if sg <= FIXED: ashraya.add('Musala')
    if sg <= DUAL: ashraya.add('Nala')
    kendra = {1, 4, 7, 10}
    if {house[p] for p in ben} and len({house[p] for p in ben} & kendra) >= 3 and not any(house[p] in kendra for p in mal):
        out.add('Maala')                                                # v. 8
    if len({house[p] for p in mal} & kendra) >= 3 and not any(house[p] in kendra for p in ben):
        out.add('Sarpa')
    for a, b in ((1, 4), (4, 7), (7, 10), (10, 1)):
        if hs <= {a, b} and len(hs) == 2:
            out.add('Gada')                                             # v. 9: two successive angles
    if hs <= {1, 7} and len(hs) == 2: out.add('Shakata')
    if hs <= {4, 10} and len(hs) == 2: out.add('Vihaga')
    if hs <= {1, 5, 9}: out.add('Shringataka')                          # v. 10
    for start in (2, 3, 4):
        if hs <= {start, start + 4, start + 8}: out.add('Hala')
    if {house[p] for p in ben} <= {1, 7} and ben and {house[p] for p in mal} <= {4, 10} and mal: out.add('Vajra')   # v. 11
    if {house[p] for p in mal} <= {1, 7} and mal and {house[p] for p in ben} <= {4, 10} and ben: out.add('Yava')
    if hs <= kendra and len(hs) == 4: out.add('Kamala')                 # v. 12
    if hs <= {2, 5, 8, 11} or hs <= {3, 6, 9, 12}: out.add('Vapi')
    for name, start in (('Yupa', 1), ('Shara', 4), ('Shakti', 7), ('Danda', 10)):        # v. 13
        if hs <= {(start + i - 1) % 12 + 1 for i in range(4)}: out.add(name)
    for name, start in (('Nauka', 1), ('Koota', 4), ('Chhatra', 7), ('Chaapa', 10)):     # v. 14
        if hs <= {(start + i - 1) % 12 + 1 for i in range(7)}: out.add(name)
    for start in (2, 3, 5, 6, 8, 9, 11, 12):                            # notes p. 512-513: seven houses from a non-angle
        if hs <= {(start + i - 1) % 12 + 1 for i in range(7)}: out.add('Ardha Chandra')
    if hs <= {1, 3, 5, 7, 9, 11} and len(hs) == 6: out.add('Chakra')    # v. 15
    if hs <= {2, 4, 6, 8, 10, 12} and len(hs) == 6: out.add('Samudra')
    if not out:
        out |= ashraya
    if not out:                                                         # v. 16-17 sankhya
        out.add({1: 'Gola', 2: 'Yuga', 3: 'Shoola', 4: 'Kedara', 5: 'Pasha', 6: 'Dama', 7: 'Veena'}[len(sg)])
    return out
