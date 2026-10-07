"""
src/rules/reader.py — turn the rule base into a reading for one chart (and optionally one date).

    from src.rules.reader import Reader
    r = Reader()                               # loads every rule file once
    reading = r.read(person, jd=None)          # natal reading; pass a jd for a dated (dasha/transit) reading
    print(reading.text())

Steps (the 'engine that makes everything work together'):
 1. fire    - evaluate every rule's condition on the chart (natal rules) and on the date (timing rules);
 2. weigh   - each fired rule starts at weight 1; rules with a `scale` are multiplied by the book's result share
              for the named planet's dignity (vol. 1 ch. 3 v. 59-60: exalted 1, moolatrikona 3/4, own 1/2,
              friend 1/4, neutral 1/8, enemy/debilitated 0 for good results - and the reverse for bad results);
 3. interact- fired rules that carry an `effect` act on the other fired rules they select: cancels (weight 0),
              weakens / strengthens (x factor), reverses (flips the direction). Every change is recorded with
              the citing rule, so a reading can show why a rule was overruled;
 4. combine - surviving rules are grouped by outcome (domain or event); each outcome gets a net score
              (sum of + weights minus - weights) and the list of rules for and against, with their citations.
Shadbala-based scaling, functional benefic/malefic and avasthas join step 2 when vol. 1 ch. 29, 36 and 47 are built.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.rules import bphs_core as BC
from src.rules import engine as E

GOOD_SHARE = BC.RESULT_SHARE
BAD_SHARE = {'exalted': 0, 'moolatrikona': .25, 'own': .5, 'great_friend': .75, 'friend': .75, 'neutral': .875,
             'enemy': 1, 'great_enemy': 1, 'debilitated': 1}


@dataclass
class Fired:
    rule: dict
    weight: float = 1.0
    direction: str = '+'
    notes: list[str] = field(default_factory=list)

    @property
    def outcome(self) -> str:
        p = self.rule['predicts']
        return p.get('domain') or p.get('event')


@dataclass
class Reading:
    fired: list[Fired]
    jd: float | None

    def outcomes(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for f in self.fired:
            o = out.setdefault(f.outcome, {'score': 0.0, 'for': [], 'against': [], 'overruled': []})
            if f.weight == 0:
                o['overruled'].append(f)
                continue
            sign = 1 if f.direction == '+' else -1
            o['score'] += sign * f.weight
            (o['for'] if sign > 0 else o['against']).append(f)
        return dict(sorted(out.items(), key=lambda kv: -abs(kv[1]['score'])))

    def text(self, top: int = 20, per: int = 4) -> str:
        lines = []
        for name, o in list(self.outcomes().items())[:top]:
            if name in E.EVENTS:      # events: + means the event is indicated, not that it is good
                verdict = 'indicated' if o['score'] > 0 else 'contra-indicated' if o['score'] < 0 else 'balanced'
            else:
                verdict = 'favourable' if o['score'] > 0 else 'adverse' if o['score'] < 0 else 'mixed'
            lines.append(f"{name}: {verdict} "
                         f"(net {o['score']:+.2f}; {len(o['for'])} for, {len(o['against'])} against, "
                         f"{len(o['overruled'])} cancelled)")
            for f in sorted(o['for'] + o['against'], key=lambda f: -f.weight)[:per]:
                lines.append(f"   {f.direction} {f.weight:.2f}  {f.rule['text']}  [{f.rule['ref']}]"
                             + (f"  ({'; '.join(f.notes)})" if f.notes else ''))
            for f in o['overruled'][:2]:
                lines.append(f"   x cancelled: {f.rule['text']}  ({'; '.join(f.notes)})")
        return '\n'.join(lines)


def _selects(sel: dict, r: dict) -> bool:
    p = r['predicts']
    if 'ids' in sel and r['id'] not in sel['ids']:
        return False
    if 'id_prefix' in sel and not any(r['id'].startswith(x) for x in ([sel['id_prefix']] if isinstance(sel['id_prefix'], str) else sel['id_prefix'])):
        return False
    if 'domain' in sel and p.get('domain') not in (sel['domain'] if isinstance(sel['domain'], list) else [sel['domain']]):
        return False
    if 'event' in sel and p.get('event') not in (sel['event'] if isinstance(sel['event'], list) else [sel['event']]):
        return False
    if 'direction' in sel and p.get('direction') != sel['direction']:
        return False
    if 'kind' in sel and r['kind'] != sel['kind']:
        return False
    if 'chapter' in sel and f"-{sel['chapter']}-" not in r['id']:
        return False
    return True


# ── synthesis: automatic weighting of rules that do not carry their own scale ───────────────────────────────
# The book's principles (vol. 1 ch. 3 v. 59-60; ch. 26 v. 145-148; ch. 29 v. 32-33; ch. 47 v. 3-6): a planet gives its
# good results in proportion to its dignity and strength, its bad results in proportion to its affliction, scaled by its
# avastha. The formula combining them is the engine's (not stated in the book as one formula):
#   delivery(p) = mean(dignity share, min(Shadbala ratio, 1.5) / 1.5) x Baladi share (Yuva = 1)
#   good outcome  : weight x (0.5 + delivery)      bad outcome : weight x (1.5 - delivery)
# averaged over the planets the rule names (directly, or as house lords / dasha lords). Range 0.5 - 1.5.
BAD_PLUS_DOMAINS = {'widowhood', 'twin', 'renunciation'}
# Centred variant (readings, 2026-10-03): the formula above gives an average planet (mean delivery 0.249 over 400 real
# charts) 0.75 for good and 1.25 for bad outcomes, tilting every reading negative. centred=True uses
#   good: 1 + (delivery - 0.249)   bad: 1 - (delivery - 0.249)   so an average planet weighs 1.0 either way.
# The pre-registered tests used the original formula (centred=False, the default).
MEAN_DELIVERY = 0.249   # domains where '+' means the misfortune occurs


def _planets_in(c, cond, jd) -> set[str]:
    out = set()
    if isinstance(cond, dict):
        for k, v in cond.items():
            out |= _planets_in(c, v, jd)
    elif isinstance(cond, list):
        for v in cond:
            out |= _planets_in(c, v, jd)
    elif isinstance(cond, str):
        if cond in E.GRAHAS:
            out.add(cond)
        elif cond.startswith(('lord:', 'karaka:', 'dispositor:')):
            try:
                out |= E.refs(c, cond)
            except Exception:
                pass
    return out


def _is_good(f: 'Fired') -> bool:
    p = f.rule['predicts']
    if p.get('event'):
        bad = p['event'] in E.NEGATIVE_EVENTS or p['event'] == 'Negative'
        return (not bad) == (f.direction == '+')
    if p.get('domain') in BAD_PLUS_DOMAINS:
        return f.direction == '-'
    return f.direction == '+'


def _auto_weight(c, f: 'Fired', jd, centred: bool = False) -> None:
    from src.rules import bphs_avastha as BV
    ps = [p for p in _planets_in(c, f.rule['when'], jd) if p in c.shadbala]
    if not ps:
        return
    vals = []
    for p in ps:
        dig = GOOD_SHARE.get(c.dig[p], .125)
        stren = min(c.shadbala[p]['ratio'], 1.5) / 1.5
        delivery = (dig + stren) / 2 * max(BV.BALADI_SHARE[BV.baladi(c.lon[p])], .25)
        if centred:
            vals.append(1 + (delivery - MEAN_DELIVERY) if _is_good(f) else 1 - (delivery - MEAN_DELIVERY))
        else:
            vals.append(0.5 + delivery if _is_good(f) else 1.5 - delivery)
    w = sum(vals) / len(vals)
    f.weight *= w
    f.notes.append(f'synthesis x{w:.2f} ({", ".join(sorted(ps))})')


class Reader:
    def __init__(self, rules: list[dict] | None = None):
        if rules is None:
            rules, self.yogas = E.load_rules()
        else:
            self.yogas = {}
        self.rules = rules

    def read(self, person: dict, jd: float | None = None, kinds=('natal', 'timing'), synthesize: bool = True,
             centred: bool = False) -> Reading:
        c = person if isinstance(person, E.Chart) else E.Chart(person)      # a built Chart can be reused across dates
        fired: list[Fired] = []
        for r in self.rules:
            if r['kind'] not in kinds or (r['kind'] == 'timing' and jd is None):
                continue
            try:
                ok = E.evaluate(c, r['when'], jd if r['kind'] == 'timing' else None, self.yogas)
            except (KeyError, ValueError):
                ok = False
            if ok:
                fired.append(Fired(r, 1.0, r['predicts']['direction']))
        # 2. weigh by the dignity of the named planet
        for f in fired:
            sc = f.rule.get('scale')
            if sc and 'strength_of' in sc:         # vol. 1 ch. 26 v. 145-148: full / half / quarter by strength
                ps = [q for q in E.refs(c, sc['strength_of']) if q in c.shadbala]
                if ps:
                    ratio = c.shadbala[sorted(ps)[0]]['ratio']
                    share = 1 if ratio >= 1 else .5 if ratio >= .75 else .25
                    f.weight *= share
                    f.notes.append(f'x{share:g} for Shadbala {ratio:.2f} of {sorted(ps)[0]}')
            if sc and 'avastha_of' in sc:          # vol. 1 ch. 47 v. 3-6: Baladi x Jagradadi shares
                from src.rules import bphs_avastha as BV
                ps = sorted(E.refs(c, sc['avastha_of']))
                if ps:
                    q = ps[0]
                    share = BV.BALADI_SHARE[BV.baladi(c.lon[q])] * BV.JAGRAT_SHARE[BV.jagradadi(c.dig[q])]
                    f.weight *= share
                    f.notes.append(f'x{share:g} for the avasthas of {q}')
            if sc and 'bhava_of' in sc:            # Phaladeepika VIII v. 34-35: full at the bhava's middle (the
                ps = sorted(E.refs(c, sc['bhava_of']))   # Lagna's degree in the planet's sign), less away from it
                if ps:
                    dist = abs(c.lon[ps[0]] % 30 - c.st['asc'] % 30)
                    share = round(1 - dist / 30, 3)
                    f.weight *= share
                    f.notes.append(f'x{share:g} for {ps[0]} {dist:.0f} deg from the bhava middle')
            if sc and 'dignity_of' in sc:
                ps = E.refs(c, sc['dignity_of'])
                if ps:
                    d = c.dig[sorted(ps)[0]]
                    share = (GOOD_SHARE if f.direction == '+' else BAD_SHARE).get(d, 1)
                    f.weight *= share
                    f.notes.append(f'scaled x{share:g} for {d} {sorted(ps)[0]}')
            if not sc and synthesize:
                _auto_weight(c, f, jd, centred)
        # 3. interactions: cancellations first, then reversals, then weakening/strengthening
        order = {'cancels': 0, 'reverses': 1, 'weakens': 2, 'strengthens': 2}
        actors = sorted((f for f in fired if 'effect' in f.rule), key=lambda f: order[f.rule['effect']['type']])
        for a in actors:
            e = a.rule['effect']
            if a.weight == 0:
                continue                                       # a cancelled rule cannot act
            for f in fired:
                if f is a or not _selects(e['targets'], f.rule):
                    continue
                if e['type'] == 'cancels':
                    f.weight = 0
                elif e['type'] == 'reverses':
                    f.direction = '-' if f.direction == '+' else '+'
                else:
                    f.weight *= e['factor']
                f.notes.append(f"{e['type']} by {a.rule['id']} [{a.rule['ref']}]")
        return Reading(fired, jd)
