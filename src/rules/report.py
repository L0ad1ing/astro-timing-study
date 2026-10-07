"""
src/rules/report.py — a structured reading from the rule engine (natal synthesis + current period + timeline).

    from src.rules.report import build
    data = build(person, now_jd, years_ahead=10)     # dict, JSON-serialisable

Everything in the output is either a fired rule (with its citation) or a chart fact computed by the engine.
"""
from __future__ import annotations

from src import features as F
from src.rules import bphs_ayu as BA
from src.rules import bphs_dasha as BD
from src.rules import bphs_functional as BF
from src.rules import engine as E
from src.rules.reader import Reader, _is_good

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn',
         'Aquarius', 'Pisces']
AREAS = {   # display grouping of outcome domains/events
    'Status & career': ['status', 'career', 'Career_Peak', 'Prize', 'fame', 'Job_Start', 'Job_End', 'profession', 'business'],
    'Wealth & expenses': ['wealth', 'expenditure', 'property', 'fortune', 'family_wealth'],
    'Marriage & partner': ['marriage', 'widowhood', 'spouse_health', 'husband', 'Marriage', 'Divorce', 'Death of mate', 'Relationship_Begin', 'Relationship_End'],
    'Children': ['children', 'Birth_Child', 'twin'],
    'Health & longevity': ['health', 'longevity', 'eyes', 'speech', 'Illness', 'Accident', 'accident_risk', 'Death', 'hardship'],
    'Family': ['mother', 'father', 'siblings', 'family', 'parents', 'relatives', 'home', 'Death of father', 'Death of mother', 'Death_of_relative', 'in_laws'],
    'Character & mind': ['character', 'conduct', 'intellect', 'learning', 'courage', 'appearance', 'spirituality', 'enemies', 'renunciation', 'travel'],
    'Legal & conflict': ['Arrest', 'Trial', 'legal'],
    'General period quality': ['Positive', 'Negative'],
}


def _fmt(f):
    return {'id': f.rule['id'], 'book': {'Phaladeepika': 'Phaladeepika', 'KP Readers': 'KP', 'KP modern': 'KP modern', 'Saravali': 'Saravali', 'Valens': 'Valens', 'Lilly': 'Lilly'}.get(f.rule['source'], 'BPHS'),
            'text': f.rule['text'], 'ref': f.rule['ref'], 'weight': round(f.weight, 2), 'good': _is_good(f),
            'outcome': f.outcome, 'notes': f.notes}


def _areas(reading):
    out = {}
    outs = reading.outcomes()
    for area, keys in AREAS.items():
        good, bad, cancelled = [], [], []
        for k in keys:
            o = outs.get(k)
            if not o:
                continue
            for f in o['for'] + o['against']:
                (good if _is_good(f) else bad).append(f)
            cancelled += o['overruled']
        g, b = sum(f.weight for f in good), sum(f.weight for f in bad)
        if not good and not bad and not cancelled:
            continue
        out[area] = {'good': round(g, 2), 'bad': round(b, 2), 'balance': round(g - b, 2),
                     'for': [_fmt(f) for f in sorted(good, key=lambda f: -f.weight)],
                     'against': [_fmt(f) for f in sorted(bad, key=lambda f: -f.weight)],
                     'cancelled': [_fmt(f) for f in cancelled]}
    return out


def _date(jd):
    y, m, d, _ = __import__('swisseph').revjul(jd)
    return f'{y:04d}-{m:02d}-{d:02d}'


def _ad_periods(c, start_jd, years):
    """Vimshottari antardasha boundaries from start_jd for `years`."""
    out, jd = [], start_jd
    end = start_jd + years * 365.25
    while jd < end:
        v = BD.vimshottari(c.lon['Moon'], c.bjd, jd)
        left = (v['AD']['length'] - v['AD']['elapsed']) * 365.25
        out.append({'start': jd, 'end': jd + left, 'md': v['MD']['lord'], 'ad': v['AD']['lord']})
        jd = jd + left + 0.5
    return out


def build(person: dict, now_jd: float, years_ahead: int = 10) -> dict:
    c = E.Chart(person)
    r = Reader()
    natal = r.read(person, kinds=('natal',))
    now = r.read(person, now_jd, kinds=('timing',))
    v = BD.vimshottari(c.lon['Moon'], c.bjd, now_jd)
    facts = {
        'lagna': SIGNS[c.lagna],
        'planets': {p: {'sign': SIGNS[c.signs[p]], 'house': c.house_of(p), 'degree': round(c.lon[p] % 30, 1),
                        'dignity': c.dig[p], 'combust': c.combust[p],
                        'strength': round(c.shadbala[p]['ratio'], 2) if p in c.shadbala else None,
                        'functional': BF.nature(c.lagna, p)} for p in E.GRAHAS},
        'karakas': {k: v_ for k, v_ in c.karakas.items() if k != 'PiK'},
        'karakamsa': SIGNS[c.karakamsa], 'arudha_lagna': SIGNS[c.pada(1)], 'upapada': SIGNS[c.pada(12)],
        'longevity_class': BA.ayu_class(c), 'pindayu_years': round(BA.pindayu(c)['total'], 1),
        'killers': sorted(E.refs(c, 'marakas')),
        'functional_yogakarakas': sorted(BF.FUNCTIONAL[c.lagna]['yogakaraka']),
    }
    timeline = []
    for per in _ad_periods(c, now_jd, years_ahead):
        mid = (per['start'] + per['end']) / 2
        rd = r.read(person, mid, kinds=('timing',))
        areas = _areas(rd)
        timeline.append({'start': _date(per['start']), 'end': _date(per['end']), 'md': per['md'], 'ad': per['ad'],
                         'areas': {a: {'balance': x['balance'], 'good': x['good'], 'bad': x['bad'],
                                       'top_for': x['for'][:3], 'top_against': x['against'][:3]} for a, x in areas.items()}})
    return {'facts': facts, 'natal': _areas(natal),
            'now': {'date': _date(now_jd), 'md': v['MD']['lord'], 'ad': v['AD']['lord'], 'pd': v['PD']['lord'],
                    'areas': _areas(now)},
            'timeline': timeline,
            'rule_count': len(r.rules)}
