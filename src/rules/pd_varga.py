"""
src/rules/pd_varga.py — Phaladeepika ch. III (tr. V. Subrahmanya Sastri, 1937, pp. 24-33): the ten vargas, the
Vaiseshikamsa count, Krura/Saumya shashtyamsas and the Deeptadi avasthas; ch. IV v. 12-16 Moon's avastha.

Book's own conventions (v. 4-6):
  D2  hora: odd sign first half the Sun's (Leo), second half the Moon's (Cancer); even sign reversed.
  D3  decanate: the sign itself, its 5th, its 9th.            D7: odd from the sign, even from its 7th.
  D9  from Aries / Capricorn / Libra / Cancer (as usual).     D10: odd from the sign, even from its 9th.
  D12 from the sign itself.
  D16 odd sign: parts 1-12 the signs from the sign onward, 13-16 the deities Brahma, Vishnu, Hara, Ravi (no sign);
      even sign 'reversed' - read here as the same sequence in reverse order (parts 1-4 deities). Interpretation.
  D30 odd sign: Mars 5, Saturn 5, Jupiter 8, Mercury 7, Venus 5 degrees; even sign reversed. The book names lords,
      not signs; for dignity the lord's odd (even) sign is used - engine convention, the usual Parasari one.
  D60 the book gives only the Krura/Saumya parts (v. 5); the sign is taken as the sign + part (engine convention).
Vaiseshikamsa (v. 7): a varga counts when the planet is in its own, exaltation or a friend's sign there
(natural friendship, ch. II v. 21-22). Weak varga (v. 10): debilitation or an enemy's sign there.
"""
from __future__ import annotations

from src import features as F
from src.rules import bphs_core as BC

SEVEN = BC.SEVEN
_D30_ODD = [(5, 'Mars', 0), (10, 'Saturn', 10), (18, 'Jupiter', 8), (25, 'Mercury', 2), (30, 'Venus', 6)]
_D30_EVEN = [(5, 'Venus', 1), (12, 'Mercury', 5), (20, 'Jupiter', 11), (25, 'Saturn', 9), (30, 'Mars', 7)]
KRURA_ODD = {1, 2, 8, 9, 10, 11, 12, 15, 16, 30, 31, 32, 33, 34, 35, 39, 40, 42, 43, 44, 48, 51, 52, 59}


def _odd(s: int) -> bool:
    return s % 2 == 0           # Aries (0) is an odd sign


def varga_sign(v: str, lon: float) -> int | None:
    lon %= 360
    s, d = int(lon // 30), lon % 30
    if v == 'D1':
        return s
    if v == 'D2':
        first = d < 15
        return 4 if first == _odd(s) else 3
    if v == 'D3':
        return (s + 4 * int(d // 10)) % 12
    if v == 'D7':
        k = int(d // (30 / 7))
        return (s + k) % 12 if _odd(s) else (s + 6 + k) % 12
    if v == 'D9':
        return F.d9_sign(lon)
    if v == 'D10':
        k = int(d // 3)
        return (s + k) % 12 if _odd(s) else (s + 8 + k) % 12
    if v == 'D12':
        return (s + int(d // 2.5)) % 12
    if v == 'D16':
        k = int(d // (30 / 16)) + 1                     # 1..16
        pos = k if _odd(s) else 17 - k
        return (s + pos - 1) % 12 if pos <= 12 else None
    if v == 'D30':
        for hi, _, sign in (_D30_ODD if _odd(s) else _D30_EVEN):
            if d < hi:
                return sign
        return None
    if v == 'D60':
        return (s + int(d * 2)) % 12
    raise ValueError(v)


VARGAS = ['D1', 'D2', 'D3', 'D7', 'D9', 'D10', 'D12', 'D16', 'D30', 'D60']


def _sign_quality(p: str, sign: int) -> str:
    if sign == BC.EXALT_SIGN[p] or F.SIGN_LORD[sign] == p:
        return 'good'
    if sign == BC.DEBIL_SIGN[p]:
        return 'weak'
    rel = BC.natural(p, F.SIGN_LORD[sign])
    return 'good' if rel == 'friend' else 'weak' if rel == 'enemy' else 'neutral'


def counts(p: str, lon: float) -> tuple[int, int]:
    """(good vargas, weak vargas) of the ten for one of the seven planets."""
    g = w = 0
    for v in VARGAS:
        s = varga_sign(v, lon)
        if s is None:
            continue
        q = _sign_quality(p, s)
        g += q == 'good'
        w += q == 'weak'
    return g, w


def krura_shashtyamsa(lon: float) -> bool:
    lon %= 360
    s, d = int(lon // 30), lon % 30
    k = int(d * 2) + 1
    return (k if _odd(s) else 61 - k) in KRURA_ODD


def moon_avastha12(moon_lon: float) -> int:
    """Ch. IV v. 12: elapsed part of the Moon's nakshatra in vighatikas / 300 -> 1..12 (by longitude)."""
    frac = (moon_lon % (360 / 27)) / (360 / 27)
    return int(frac * 12) + 1


def deeptadi(c, p: str) -> str:
    """Ch. III v. 18-19 (p. 32-33) for the seven planets: Deepta exalted, Sukhita moolatrikona, Swastha own sign,
    Mudita friend's sign, Bheeta debilitated, Dukhita enemy's sign, Vikala combust, otherwise Santa (neutral).
    v. 20: full good result in Deepta, none in Vikala, proportionally in between."""
    if p not in SEVEN:
        return 'Santa'
    if c.combust.get(p):
        return 'Vikala'
    d = c.dig[p]
    return {'exalted': 'Deepta', 'moolatrikona': 'Sukhita', 'own': 'Swastha', 'great_friend': 'Mudita',
            'friend': 'Mudita', 'debilitated': 'Bheeta', 'enemy': 'Dukhita', 'great_enemy': 'Dukhita'}.get(d, 'Santa')


def trimsamsa_lord(lon: float) -> str | None:
    """Ch. III v. 4: lord of the trimsamsa (odd sign Mars 5, Saturn 5, Jupiter 8, Mercury 7, Venus 5; even reversed)."""
    lon %= 360
    s, d = int(lon // 30), lon % 30
    for hi, lord, _ in (_D30_ODD if _odd(s) else _D30_EVEN):
        if d < hi:
            return lord
    return None


def sphuta_parity(lons: list[float]) -> str:
    """Ch. XII v. 14: sum of longitudes; 'odd' if both its sign and navamsa are odd, 'even' if both even, else 'mixed'."""
    x = sum(lons) % 360
    a, b = _odd(int(x // 30)), _odd(F.d9_sign(x))
    return 'odd' if a and b else 'even' if not a and not b else 'mixed'


CHIDRA = {4, 6, 8, 9, 12, 14}


def santana(moon: float, sun: float) -> dict:
    """Ch. XII v. 15: 5 x Moon - 5 x Sun -> tithi (1-30) and karana; bright half 1-15."""
    ang = (5 * moon - 5 * sun) % 360
    tithi = int(ang // 12) + 1
    k = int(ang // 6)                                   # half-tithi 0..59
    sthira = k in (57, 58, 59, 0)
    vishti = not sthira and (k - 1) % 7 == 6
    num = tithi if tithi <= 15 else tithi - 15
    return {'tithi': tithi, 'bright': tithi <= 15, 'amavasya': tithi == 30,
            'chidra': num in CHIDRA, 'vishti': vishti, 'sthira': sthira}


def _mobility(s: int) -> str:
    return 'C' if s % 3 == 0 else 'S' if s % 3 == 1 else 'U'


_AYU = {('C', 'C'): 'long', ('C', 'S'): 'medium', ('C', 'U'): 'short', ('S', 'U'): 'long', ('S', 'C'): 'medium',
        ('S', 'S'): 'short', ('U', 'S'): 'long', ('U', 'U'): 'medium', ('U', 'C'): 'short'}


def ayu_class(c) -> str:
    """Ch. XIII v. 14 (1961 pp. 161-162): three pairs - (A) the drekkana signs of the Lagna and the Moon, (B) the navamsa
    signs of the Lagna lord and the Moon-sign lord, (C) their dwadasamsa signs (the table; the prose names the 8th
    lord for C - the table is followed). Majority of the three; all different -> medium (engine convention)."""
    ll, ml = F.SIGN_LORD[c.lagna], F.SIGN_LORD[c.moon_sign]
    pairs = [(varga_sign('D3', c.st['asc']), varga_sign('D3', c.lon['Moon'])),
             (varga_sign('D9', c.lon[ll]), varga_sign('D9', c.lon[ml])),
             (varga_sign('D12', c.lon[ll]), varga_sign('D12', c.lon[ml]))]
    votes = [_AYU[(_mobility(a), _mobility(b))] for a, b in pairs]
    for k in ('long', 'medium', 'short'):
        if votes.count(k) >= 2:
            return k
    return 'medium'


MRITYU_MOON = [26, 12, 13, 25, 24, 11, 26, 14, 13, 25, 5, 12]       # ch. XIII v. 10, Aries..Pisces


def moon_mrityubhaga(moon: float) -> bool:
    s, d = int((moon % 360) // 30), (moon % 360) % 30
    return int(d) + 1 == MRITYU_MOON[s]
