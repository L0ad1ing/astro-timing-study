"""
src/rules/bphs_avastha.py — planetary states, BPHS vol. 1 ch. 47 (G.C. Sharma tr., Sagar; book pp. 618-651).

baladi(p, lon)  v. 3-4: in odd signs 0-6-12-18-24-30 deg = Bala, Kumara, Yuva, Vriddha, Mrita (reversed in even signs);
                results 1/4, 1/2, full, very little (0.1 here), nil.
jagradadi(dig)  v. 5-6: own/exalted = awake (full), friend/neutral = dreaming (medium), enemy/debilitated = asleep (nil).
lajjitadi(c, p) v. 11-18: Lajjita (in the 5th with Rahu/Ketu, Saturn or Mars), Garvita (exalted/moolatrikona), Kshudhita
                (enemy's sign, with or aspected by an enemy, or with Saturn), Trashita (watery sign aspected by an enemy and
                no benefic), Mudita (friend's sign, with or aspected by a friend, or with Jupiter), Kshobhita (with the Sun
                and aspected by malefics or an enemy).
Shayanadi (v. 30-37) needs the first letter of the native's name - not computable from the data (logged).
"""
from __future__ import annotations

from src import features as F
from src.rules import bphs_core as BC

BALADI_SHARE = {'Bala': .25, 'Kumara': .5, 'Yuva': 1.0, 'Vriddha': .1, 'Mrita': 0.0}
JAGRAT_SHARE = {'awake': 1.0, 'dreaming': .5, 'asleep': 0.0}
WATERY = {3, 7, 11}


def baladi(lon: float) -> str:
    s, d = int((lon % 360) // 30), lon % 30
    names = ['Bala', 'Kumara', 'Yuva', 'Vriddha', 'Mrita']
    i = min(int(d // 6), 4)
    return names[i] if s % 2 == 0 else names[4 - i]


def jagradadi(dig: str) -> str:
    if dig in ('exalted', 'moolatrikona', 'own'):
        return 'awake'
    if dig in ('friend', 'great_friend', 'neutral'):
        return 'dreaming'
    return 'asleep'


def lajjitadi(c, p: str) -> set[str]:
    from src.rules import engine as E
    out = set()
    others = [q for q in E.GRAHAS if q != p]
    with_ = {q for q in others if c.signs[q] == c.signs[p]}
    aspecting = {q for q in others if E._aspects_sign(q, c.signs[q], c.signs[p])}
    rel = lambda q: BC.natural(p, q) if p in BC.NAT else 'neutral'
    if c.house_of(p) == 5 and with_ & {'Rahu', 'Ketu', 'Saturn', 'Mars'}:
        out.add('Lajjita')
    if c.dig[p] in ('exalted', 'moolatrikona'):
        out.add('Garvita')
    lord = F.SIGN_LORD[c.signs[p]]
    if (lord != p and rel(lord) == 'enemy') or any(rel(q) == 'enemy' for q in with_ | aspecting) or 'Saturn' in with_:
        out.add('Kshudhita')
    if c.signs[p] in WATERY and any(rel(q) == 'enemy' for q in aspecting) and not (aspecting & c.benefics):
        out.add('Trashita')
    if (lord != p and rel(lord) == 'friend') or any(rel(q) == 'friend' for q in with_ | aspecting) or 'Jupiter' in with_:
        out.add('Mudita')
    if 'Sun' in with_ and (aspecting & c.malefics or any(rel(q) == 'enemy' for q in aspecting)):
        out.add('Kshobhita')
    return out
