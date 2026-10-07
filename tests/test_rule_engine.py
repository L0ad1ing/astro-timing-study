"""tests/test_rule_engine.py — the classical rule engine (src/rules/engine.py) and the rule files."""
from pathlib import Path

import pytest

from src import features as F
from src.interactive_cli import person_from_birth
from src.rules import engine as E

EINSTEIN = {**person_from_birth("1879-03-14 11:30", 0.6658, 48.4, 9.9833), 'name': None}


@pytest.fixture(scope='module')
def chart():
    return E.Chart(EINSTEIN)


@pytest.mark.skipif(not (Path(__file__).resolve().parents[1] / 'rules').is_dir(),
                    reason='the rule base (rules/) is not in the public copy: it paraphrases copyrighted translations')
def test_all_rule_files_load_and_validate():
    rules, yogas = E.load_rules()
    assert len(rules) >= 131                                  # ch. 49 (84) + ch. 50 (47)
    assert len({r['id'] for r in rules}) == len(rules)
    assert all(r['status'] in ('draft', 'verified') for r in rules)
    # every rule in the main set comes from a text and cites a page
    assert all((r['source'].startswith(('BPHS', 'Phaladeepika', 'KP Readers', 'Saravali', 'Valens', 'Lilly')) or r['source'].endswith('(quoted in BPHS notes)')) and ' p. ' in r['ref']
               or r['source'] == 'KP modern' and ', source line ' in r['ref']      # later K.P. books: OCR line, few printed pages
               for r in rules)
    # the memory-based pilot rules live apart and still validate
    pilot, pilot_yogas = E.load_rules(*sorted((E.RULES_DIR / '_not_from_text').glob('parashari_*.jsonl')))
    assert len(pilot) == 45


def test_references_on_a_known_chart(chart):
    assert chart.lagna == 2                                   # Gemini (sidereal)
    assert E.refs(chart, 'lord:7') == {'Jupiter'}             # Sagittarius
    assert E.refs(chart, 'lord:1') == {'Mercury'}
    assert E.refs(chart, 'dispositor:lord:7') == {F.SIGN_LORD[chart.signs['Jupiter']]}
    for p in E.refs(chart, 'occupants:10'):
        assert chart.house_of(p) == 10
    jup_sign = chart.signs['Jupiter']
    assert E.refs(chart, 'with:lord:7') == {p for p in E.GRAHAS if p != 'Jupiter' and chart.signs[p] == jup_sign}
    assert 'Jupiter' not in E.refs(chart, 'assoc:lord:7')
    for p in E.refs(chart, 'assoc:lord:7'):
        assert E._associated(chart, p, 'Jupiter')


def test_natal_atoms_added_for_chapter_49(chart):
    for p in E.GRAHAS:
        assert E.evaluate(chart, {'is': [p, p]})
        assert E.evaluate(chart, {'combust': p}) == chart.combust[p]
    assert E.evaluate(chart, {'is': ['Mercury', 'lord:1']})        # Gemini Lagna
    assert not E.evaluate(chart, {'is': ['Venus', 'lord:1']})
    waxing = E.evaluate(chart, {'moon_phase': 'waxing'})
    assert waxing != E.evaluate(chart, {'moon_phase': 'waning'})
    assert waxing == ((chart.lon['Moon'] - chart.lon['Sun']) % 360 < 180)
    all_classes = sorted(E.DIGNITY_CLASSES)
    for p in ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'):
        assert E.evaluate(chart, {'varga_dignity': ['D9', p, all_classes]})
    with pytest.raises(ValueError):
        E.validate_rule({'id': 'X', 'source': 's', 'ref': 'r', 'kind': 'natal', 'text': 't', 'status': 'draft',
                         'when': {'moon_phase': 'full'}, 'predicts': {'domain': 'x', 'direction': '+'}})


def test_kalachakra_atoms_follow_the_dasha_module(chart):
    from src.rules import bphs_dasha as BD
    for years in (5, 20, 40):
        jd = EINSTEIN['birth_jd'] + 365.25 * years
        k = BD.kalachakra(chart.lon['Moon'], chart.bjd, jd)
        if k is None:
            assert not E.evaluate(chart, {'kc': {'pos': list(range(1, 10))}}, jd)
            continue
        assert E.evaluate(chart, {'kc': {'amsa': [k['amsa']], 'pos': [k['pos']], 'sign': [k['sign']]}}, jd)
        assert not E.evaluate(chart, {'kc': {'pos': [p for p in range(1, 10) if p != k['pos']]}}, jd)
        assert E.evaluate(chart, {'kc': {'house': [(k['sign'] - chart.lagna) % 12 + 1]}}, jd)
    assert E.evaluate(chart, {'kc_natal': {'amsa': [chart.kc['amsa']]}})


def test_chara_atom_follows_the_dasha_module(chart):
    from src.rules import bphs_dasha as BD
    for years in (3, 15, 30, 50):
        jd = EINSTEIN['birth_jd'] + 365.25 * years
        ch = BD.chara(chart.signs, chart.lagna, chart.bjd, jd)
        if ch is None:
            continue
        assert E.evaluate(chart, {'chara': {'sign': [ch['sign']], 'ad_sign': [ch['ad_sign']], 'index': [ch['index']]}}, jd)
        assert not E.evaluate(chart, {'chara': {'sign': [(ch['sign'] + 1) % 12]}}, jd)
        n = (chart.signs['Saturn'] - ch['sign']) % 12 + 1
        assert E.evaluate(chart, {'chara': {'from_holds': [[n], 'Saturn']}}, jd)


def test_dasha_and_transit_atoms_match_the_core_calculations(chart):
    jd = EINSTEIN['birth_jd'] + 365.25 * 26.2                 # 1905
    md, ad, _ = (F.DASHA_LORDS[i] for i in F.vimshottari_at(chart.lon['Moon'], chart.bjd, jd))
    assert E.evaluate(chart, {'dasha': [['MD'], md]}, jd)
    assert E.evaluate(chart, {'dasha': [['AD'], ad]}, jd)
    other = next(p for p in E.GRAHAS if p not in (md, ad))
    assert not E.evaluate(chart, {'dasha': [['MD', 'AD'], other]}, jd)
    t = chart.date(jd)['transit']
    house_of_jupiter = (t['Jupiter'] - chart.lagna) % 12 + 1
    assert E.evaluate(chart, {'transit': ['Jupiter', f'house:{house_of_jupiter}', 'occupies']}, jd)
    assert E.evaluate(chart, {'not': {'transit': ['Jupiter', f'house:{house_of_jupiter % 12 + 1}', 'occupies']}}, jd) \
        or 'Jupiter' in t['_retro']


def test_every_rule_evaluates_on_a_real_chart(chart):
    rules, yogas = E.load_rules()
    jd = EINSTEIN['birth_jd'] + 365.25 * 40
    for r in rules:
        v = E.evaluate(chart, r['when'], jd if r['kind'] == 'timing' else None, yogas)
        assert isinstance(v, bool)
    for name, cond in yogas.items():
        assert isinstance(E.evaluate(chart, cond, None, yogas), bool)


def test_validation_rejects_bad_rules():
    good = {'id': 'X', 'source': 's', 'ref': 'r', 'kind': 'timing', 'text': 't', 'status': 'draft',
            'when': {'dasha': [['MD'], 'lord:7']}, 'predicts': {'event': 'Marriage', 'direction': '+'}}
    E.validate_rule(good)
    for bad in (
        {**good, 'when': {'dasha': [['XX'], 'lord:7']}},
        {**good, 'when': {'dasha': [['MD'], 'lord:13']}},
        {**good, 'when': {'flies': 1}},
        {**good, 'predicts': {'event': 'Lottery', 'direction': '+'}},
        {**good, 'kind': 'natal', 'predicts': {'domain': 'x', 'direction': '+'}},   # dasha in a natal rule
        {**good, 'status': 'probably'},
    ):
        with pytest.raises(ValueError):
            E.validate_rule(bad)


def test_rule_featurizer():
    rules, yogas = E.load_rules()
    fz = E.RuleFeaturizer(rules, yogas)
    v = fz.features(fz.context(EINSTEIN), EINSTEIN['birth_jd'] + 365.25 * 30)
    assert v.shape == (fz.n,) and set(v.tolist()) <= {0.0, 1.0}
    assert fz.n == sum(r['kind'] == 'timing' and bool(r['predicts'].get('event')) for r in rules)


def test_panchanga_atoms(chart):
    e = (chart.lon['Moon'] - chart.lon['Sun']) % 360
    tithi = int(e // 12) + 1
    assert E.evaluate(chart, {'tithi': [tithi]}) and not E.evaluate(chart, {'tithi': [tithi % 30 + 1]})
    nak = int((chart.lon['Moon'] % 360) // (360 / 27)) + 1
    assert E.evaluate(chart, {'nakshatra': [[nak]]})
    assert E.evaluate(chart, {'nakshatra': [[nak], [1, 2, 3, 4]]})
    parts = [p for p in range(1, 7) if E.evaluate(chart, {'tithi_part': [tithi, 6, [p]]})]
    assert len(parts) == 1
    for g in ('tithi', 'nakshatra', 'lagna'):
        assert isinstance(E.evaluate(chart, {'gandanta': g}), bool)
