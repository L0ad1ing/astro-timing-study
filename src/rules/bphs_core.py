"""
src/rules/bphs_core.py — planetary dignity, friendship and natural benefic/malefic exactly as BPHS vol. 1 ch. 3 gives
them (G.C. Sharma tr., Sagar; book pp. 12-49, PDF + 11). Used by the rule engine. src/strength.py (the earlier studies'
general-knowledge version) is left unchanged so those results stay reproducible; differences are listed in
docs/BPHS_ENGINE_NOTES.md.
"""
from __future__ import annotations

from src import features as F

SEVEN = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

# v. 49-50 (p. 36-37): exaltation signs and deepest degrees; debilitation the 7th sign, same degree
EXALT_SIGN = {'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6}
DEEP_DEG = {'Sun': 10, 'Moon': 3, 'Mars': 28, 'Mercury': 15, 'Jupiter': 5, 'Venus': 27, 'Saturn': 20}
# Rahu/Ketu exaltation is not given in vol. 1 ch. 3. Vol. 2 ch. 49 v. 35: translation says Rahu Scorpio / Ketu Taurus,
# the printed Sanskrit Rahu Taurus / Ketu Scorpio - the Sanskrit is used (logged).
EXALT_SIGN.update({'Rahu': 1, 'Ketu': 7})
DEBIL_SIGN = {p: (s + 6) % 12 for p, s in EXALT_SIGN.items()}

# v. 51-54 (p. 37): moolatrikona (sign, from deg, to deg). In Taurus the first 3 deg are the Moon's exaltation and the
# rest her moolatrikona; in Virgo the first 15 deg are Mercury's exaltation, the next 5 moolatrikona, the last 10 own.
MOOLATRIKONA = {'Sun': (4, 0, 20), 'Moon': (1, 3, 30), 'Mars': (0, 0, 12), 'Mercury': (5, 15, 20),
                'Jupiter': (8, 0, 10), 'Venus': (6, 0, 15), 'Saturn': (10, 0, 20)}
EXALT_PORTION = {'Moon': (0, 3), 'Mercury': (0, 15)}     # only part of the sign counts as exaltation

OWN_SIGNS = {p: {s for s in range(12) if F.SIGN_LORD[s] == p} for p in SEVEN}
OWN_SIGNS['Rahu'], OWN_SIGNS['Ketu'] = {10}, {7}           # vol. 2 ch. 48 v. 157

# v. 55 and table p. 39: natural relationships, including the separate tables for Rahu and Ketu
NAT = {
    'Sun': ({'Moon', 'Mars', 'Jupiter'}, {'Venus', 'Saturn'}),
    'Moon': ({'Sun', 'Mercury'}, set()),
    'Mars': ({'Sun', 'Moon', 'Jupiter'}, {'Mercury'}),
    'Mercury': ({'Sun', 'Venus'}, {'Moon'}),
    'Jupiter': ({'Sun', 'Moon', 'Mars'}, {'Mercury', 'Venus'}),
    'Venus': ({'Mercury', 'Saturn'}, {'Moon', 'Sun'}),
    'Saturn': ({'Mercury', 'Venus'}, {'Sun', 'Moon', 'Mars'}),
    'Rahu': ({'Jupiter', 'Venus', 'Saturn'}, {'Sun', 'Moon', 'Mars'}),
    'Ketu': ({'Mars', 'Venus', 'Saturn'}, {'Sun', 'Moon'}),
}
TEMP_FRIEND_HOUSES = {2, 3, 4, 10, 11, 12}                  # v. 56
COMPOUND = {('friend', True): 'great_friend', ('neutral', True): 'friend', ('enemy', True): 'neutral',
            ('friend', False): 'neutral', ('neutral', False): 'enemy', ('enemy', False): 'great_enemy'}   # v. 57-58
# v. 59-60 (p. 42): share of auspicious results by dignity (combust / enemy / debilitated give none)
RESULT_SHARE = {'exalted': 1, 'moolatrikona': .75, 'own': .5, 'great_friend': .25, 'friend': .25,
                'neutral': .125, 'enemy': 0, 'great_enemy': 0, 'debilitated': 0}


def natural(p: str, q: str) -> str:
    friends, enemies = NAT[p]
    return 'friend' if q in friends else 'enemy' if q in enemies else 'neutral'


def compound(p: str, q: str, p_sign: int, q_sign: int) -> str:
    return COMPOUND[(natural(p, q), (q_sign - p_sign) % 12 + 1 in TEMP_FRIEND_HOUSES)]


def dignity(p: str, lon: float, signs: dict | None = None) -> str:
    """Dignity class. With signs (planet -> sign) friendship is compound (natal); without, natural only."""
    s, deg = int((lon % 360) // 30), lon % 30
    if s == EXALT_SIGN[p] and (p not in EXALT_PORTION or EXALT_PORTION[p][0] <= deg < EXALT_PORTION[p][1]):
        return 'exalted'
    if s == DEBIL_SIGN[p]:
        return 'debilitated'
    mt = MOOLATRIKONA.get(p)
    if mt and s == mt[0] and mt[1] <= deg < mt[2]:
        return 'moolatrikona'
    if s in OWN_SIGNS[p]:
        return 'own'
    lord = F.SIGN_LORD[s]
    if lord == p:
        return 'own'
    if signs is None or p not in signs or lord not in signs:
        return natural(p, lord)
    return compound(p, lord, signs[p], signs[lord])


def benefics_malefics(lon: dict[str, float], signs: dict[str, int]) -> tuple[set[str], set[str]]:
    """v. 11 (p. 16-17): Sun, Saturn, Mars, the decreasing Moon, Rahu, Ketu are malefic; the full Moon, Mercury,
    Jupiter, Venus benefic; Mercury conjunct a malefic becomes malefic. The decreasing Moon per the notes: from the
    8th tithi of the dark half to the 8th of the bright half (elongation 264 deg -> 84 deg)."""
    mal = {'Sun', 'Saturn', 'Mars', 'Rahu', 'Ketu'}
    elong = (lon['Moon'] - lon['Sun']) % 360
    if not 84 <= elong < 264:
        mal.add('Moon')
    if any(signs[m] == signs['Mercury'] for m in mal):
        mal.add('Mercury')
    ben = {p for p in ('Moon', 'Mercury', 'Jupiter', 'Venus') if p not in mal}
    return ben, mal


# vol. 1 ch. 8 notes (p. 152-153): combustion distance from the Sun; retrograde Mercury and Venus 1 deg less
COMBUST_ORB = {'Moon': 12, 'Mars': 17, 'Mercury': 14, 'Jupiter': 11, 'Venus': 10, 'Saturn': 16}
COMBUST_RETRO_LESS = {'Mercury': 1, 'Venus': 1}


def combust(p: str, lon: dict[str, float], retro: bool = False) -> bool:
    if p not in COMBUST_ORB:
        return False
    orb = COMBUST_ORB[p] - (COMBUST_RETRO_LESS.get(p, 0) if retro else 0)
    d = abs(((lon[p] - lon['Sun']) + 180) % 360 - 180)
    return d < orb


# ── vol. 1 ch. 28: planetary aspects ─────────────────────────────────────────────────────────────────────────
# v. 2-5 (p. 359-360): every planet aspects the 7th fully; Saturn also the 3rd and 10th, Jupiter the 5th and 9th,
# Mars the 4th and 8th. Nothing is said of Rahu and Ketu here - they aspect only the 7th in this engine (the earlier
# study code gave them 5/9 from K.N. Rao's practice; logged).
FULL_ASPECT = {'Saturn': (3, 10), 'Jupiter': (5, 9), 'Mars': (4, 8)}


def full_aspect(planet: str, frm: int, to: int) -> bool:
    h = (to - frm) % 12 + 1
    return h == 7 or h in FULL_ASPECT.get(planet, ())


def drishti(planet: str, aspector_lon: float, aspected_lon: float) -> float:
    """Sphuta drishti in virupas (0-60), v. 6-12 (pp. 360-375). d = aspected - aspector."""
    d = (aspected_lon - aspector_lon) % 360
    s, x = int(d // 30), d % 30
    if planet == 'Saturn':                         # v. 9-10 (Sanskrit 'dvigunah'; rules per the notes p. 368)
        if s == 1: return 2 * x
        if s == 9: return 2 * (30 - x)
        if s == 2: return 60 - x / 2               # verse: halved and deducted from 60 (the notes say 60 - x; logged)
        if s == 8: return 30 + x
    if planet == 'Mars':                           # v. 11 (p. 374)
        if s in (3, 7): return 60 - x
        if s == 2: return 1.5 * x + 15
        if s == 6: return 60.0
    if planet == 'Jupiter':                        # v. 12 (p. 375)
        if s in (3, 7): return x / 2 + 45
        if s in (4, 8): return 60 - x
    if d < 30 or d >= 300: return 0.0               # v. 6-8 general rule
    if s == 1: return x / 2
    if s == 2: return x + 15
    if s == 3: return (120 - d) / 2 + 30
    if s == 4: return 150 - d
    if s == 5: return 2 * x
    return (300 - d) / 2


# ── vol. 1 ch. 31: Arudha (Pada) of a house ──────────────────────────────────────────────────────────────────
def arudha(house_sign: int, lord_sign: int) -> int:
    """v. 1-5: count from the house to its lord, the same count again from the lord. The pada cannot fall in the house
    itself or the 7th from it: falling in the house -> take the 10th from it; falling in the 7th -> take the 4th from it
    (so the lord in the 4th from the house gives the 4th... per v. 5 the lord in the 4th makes the 4th the pada; the
    lord in the 7th makes the 10th from the house... see the notes; implemented as the verse's two exceptions)."""
    n = (lord_sign - house_sign) % 12
    pada = (lord_sign + n) % 12
    if pada == house_sign:                     # lord in the house itself -> 10th; lord in the 7th -> 4th (notes p. 422)
        pada = (house_sign + (9 if n == 0 else 3)) % 12
    elif pada == (house_sign + 6) % 12:        # lord in the 4th or 10th -> the 4th from the house (v. 4-5)
        pada = (house_sign + 3) % 12
    return pada
