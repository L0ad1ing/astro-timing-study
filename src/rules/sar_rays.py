"""
src/rules/sar_rays.py — planetary rays after Saravali ch. 36 (R. Santhanam tr., vol. 2 pp. 662-669).

Base (v. 2, 5): rays at deep exaltation Sun 10, Moon 9, Mars 5, Mercury 5, Jupiter 7, Venus 8, Saturn 5 (Manindha;
the other school's uniform 7 is not used); nil at deep debilitation; proportional in between - the same arithmetic as
BPHS ch. 75 (src/rules/bphs_rays.raw_rays).
Rectification (v. 7-9): x3 in its own dwadasamsa, own sign, exaltation or retrogression; x2 in a friend's dwadasamsa;
less 1/16 in an enemy's dwadasamsa or when debilitated; a combust planet other than Venus and Saturn loses all rays.
'Just turned retrograde x2 / just turned direct less 1/8' needs the station date - not used (logged).
"""
from src.rules import bphs_core as BC
from src import features as F
from src.rules.bphs_rays import raw_rays

SEVEN = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']


def d12_sign(lon: float) -> int:
    return (int(lon % 360 // 30) + int((lon % 30) // 2.5)) % 12


def rays(planet: str, lon: float, dignity: str, combust: bool, retro: bool) -> float:
    if combust and planet not in ('Venus', 'Saturn'):
        return 0.0
    r = raw_rays(planet, lon)
    lord12 = F.SIGN_LORD[d12_sign(lon)]
    if lord12 == planet or dignity in ('exalted', 'own', 'moolatrikona') or (retro and planet not in ('Sun', 'Moon')):
        return r * 3
    rel = BC.natural(planet, lord12)
    if rel == 'friend':
        return r * 2
    if rel == 'enemy' or dignity == 'debilitated':
        return r * 15 / 16
    return r
