"""
src/rules/bphs_rays.py — planetary rays, BPHS ch. 75 (G.C. Sharma tr., Sagar 1995, vol. 2 pp. 589-601).

Rays at deep exaltation (Table-38): Sun 10, Moon 9, Mars 5, Mercury 5, Jupiter 7, Venus 8, Saturn 5; nil at deep
debilitation; proportional in between (v. 1-2): arc from the deep-debilitation point (folded to <= 180 deg) x
full rays / 180 deg. Deep debilitation points from the notes (p. 591-592).
Moderation (v. 3-7, 'some other Acharyas'): exalted x3, moolatrikona x2, own sign x3/2 (Sanskrit 'tribhna
dvisambhakta'; the translation's '/12' is a misprint - logged), great friend x4/3, friend x6/5, enemy /2,
great enemy x2/5, neutral unchanged; combust planets other than Mercury and Venus lose all rays.
The dignity classes come from src/strength.py until vol. 1 ch. 3 replaces them (logged).
"""
FULL = {'Sun': 10, 'Moon': 9, 'Mars': 5, 'Mercury': 5, 'Jupiter': 7, 'Venus': 8, 'Saturn': 5}
DEEP_DEBIL = {'Sun': 190, 'Moon': 213, 'Mars': 118, 'Mercury': 345, 'Jupiter': 275, 'Venus': 177, 'Saturn': 20}
MODERATE = {'exalted': 3, 'moolatrikona': 2, 'own': 1.5, 'great_friend': 4 / 3, 'friend': 1.2, 'neutral': 1,
            'enemy': 0.5, 'great_enemy': 0.4, 'debilitated': 1}


def raw_rays(planet: str, lon: float) -> float:
    d = (lon - DEEP_DEBIL[planet]) % 360
    if d > 180:
        d = 360 - d
    return d * FULL[planet] / 180


def rays(planet: str, lon: float, dignity: str, combust: bool) -> float:
    if combust and planet not in ('Mercury', 'Venus'):
        return 0.0
    return raw_rays(planet, lon) * MODERATE.get(dignity, 1)
