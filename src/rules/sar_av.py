"""
src/rules/sar_av.py — Ashtakavarga after Saravali ch. 53 (R. Santhanam tr., vol. 2 pp. 830-834).

Benefic points (bindus) each planet's chart receives from the seven planets and the Lagna, as listed in v. 2-8. They
differ from BPHS ch. 66 (src/rules/bphs_av.REKHA) in: the Moon's chart from the Moon (no 9th), from Mars (adds 9th),
from Mercury (1,3,5,6,9,10,11) and from Jupiter (1,4,7,8,10,11,12); Mercury's chart from Mars and Saturn (12th for 11th);
Saturn's chart from the Lagna (no 6th); Mars's chart from Saturn (no 4th - the
translation's list; the 4th had been copied from BPHS, corrected 2026-10-04 on checking every list against the scan).
Used unreduced (Saravali gives no reductions).
"""
SAR = {
    'Sun': {'Sun': [1, 2, 4, 7, 8, 9, 10, 11], 'Moon': [3, 6, 10, 11], 'Mars': [1, 2, 4, 7, 8, 9, 10, 11], 'Mercury': [3, 5, 6, 9, 10, 11, 12],
            'Jupiter': [5, 6, 9, 11], 'Venus': [6, 7, 12], 'Saturn': [1, 2, 4, 7, 8, 9, 10, 11], 'Lagna': [3, 4, 6, 10, 11, 12]},
    'Moon': {'Sun': [3, 6, 7, 8, 10, 11], 'Moon': [1, 3, 6, 7, 10, 11], 'Mars': [2, 3, 5, 6, 9, 10, 11], 'Mercury': [1, 3, 5, 6, 9, 10, 11],
             'Jupiter': [1, 4, 7, 8, 10, 11, 12], 'Venus': [3, 4, 5, 7, 9, 10, 11], 'Saturn': [3, 5, 6, 11], 'Lagna': [3, 6, 10, 11]},
    'Mars': {'Sun': [3, 5, 6, 10, 11], 'Moon': [3, 6, 11], 'Mars': [1, 2, 4, 7, 8, 10, 11], 'Mercury': [3, 5, 6, 11],
             'Jupiter': [6, 10, 11, 12], 'Venus': [6, 8, 11, 12], 'Saturn': [1, 7, 8, 9, 10, 11], 'Lagna': [1, 3, 6, 10, 11]},
    'Mercury': {'Sun': [5, 6, 9, 11, 12], 'Moon': [2, 4, 6, 8, 10, 11], 'Mars': [1, 2, 4, 7, 8, 9, 10, 12], 'Mercury': [1, 3, 5, 6, 9, 10, 11, 12],
                'Jupiter': [6, 8, 11, 12], 'Venus': [1, 2, 3, 4, 5, 8, 9, 11], 'Saturn': [1, 2, 4, 7, 8, 9, 10, 12], 'Lagna': [1, 2, 4, 6, 8, 10, 11]},
    'Jupiter': {'Sun': [1, 2, 3, 4, 7, 8, 9, 10, 11], 'Moon': [2, 5, 7, 9, 11], 'Mars': [1, 2, 4, 7, 8, 10, 11], 'Mercury': [1, 2, 4, 5, 6, 9, 10, 11],
                'Jupiter': [1, 2, 3, 4, 7, 8, 10, 11], 'Venus': [2, 5, 6, 9, 10, 11], 'Saturn': [3, 5, 6, 12], 'Lagna': [1, 2, 4, 5, 6, 7, 9, 10, 11]},
    'Venus': {'Sun': [8, 11, 12], 'Moon': [1, 2, 3, 4, 5, 8, 9, 11, 12], 'Mars': [3, 4, 6, 9, 11, 12], 'Mercury': [3, 5, 6, 9, 11],
              'Jupiter': [5, 8, 9, 10, 11], 'Venus': [1, 2, 3, 4, 5, 8, 9, 10, 11], 'Saturn': [3, 4, 5, 8, 9, 10, 11], 'Lagna': [1, 2, 3, 4, 5, 8, 9, 11]},
    'Saturn': {'Sun': [1, 2, 4, 7, 8, 10, 11], 'Moon': [3, 6, 11], 'Mars': [3, 5, 6, 10, 11, 12], 'Mercury': [6, 8, 9, 10, 11, 12],
               'Jupiter': [5, 6, 11, 12], 'Venus': [6, 11, 12], 'Saturn': [3, 5, 6, 11], 'Lagna': [1, 3, 4, 10, 11]},
}


def bindus(c) -> dict[str, list[int]]:
    """{planet: [bindus in sign 0..11]} for the seven planets' charts."""
    pos = {**{p: c.signs[p] for p in SAR}, 'Lagna': c.lagna}
    out = {}
    for p, rows in SAR.items():
        row = [0] * 12
        for q, hs in rows.items():
            for h in hs:
                row[(pos[q] + h - 1) % 12] += 1
        out[p] = row
    return out
