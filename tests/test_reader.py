"""tests/test_reader.py — the reading engine: firing, scaling, cancellation, reversal, combination."""
from pathlib import Path

import pytest

from src.interactive_cli import person_from_birth
from src.rules.reader import Reader

EINSTEIN = {**person_from_birth("1879-03-14 11:30", 0.6658, 48.4, 9.9833), 'name': None}
ALWAYS = {'in_house': [['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'], list(range(1, 13))]}


def R(id, domain, direction, **extra):
    return {'id': id, 'source': 's', 'ref': f'ref-{id}', 'kind': 'natal', 'text': id, 'when': ALWAYS,
            'predicts': {'domain': domain, 'direction': direction}, 'status': 'verified', **extra}


def test_cancel_reverse_weaken_and_combine():
    rules = [R('A', 'wealth', '+'), R('B', 'wealth', '+'), R('C', 'health', '-'), R('D', 'health', '+'),
             R('X', 'meta', '+', effect={'type': 'cancels', 'targets': {'ids': ['A']}}),
             R('Y', 'meta', '+', effect={'type': 'reverses', 'targets': {'ids': ['C']}}),
             R('Z', 'meta', '+', effect={'type': 'weakens', 'targets': {'domain': 'wealth'}, 'factor': 0.5})]
    o = Reader(rules).read(EINSTEIN, synthesize=False).outcomes()
    assert o['wealth']['score'] == 0.5 and len(o['wealth']['overruled']) == 1      # A cancelled, B halved
    assert o['health']['score'] == 2                                                # C reversed to +, plus D


def test_cancelled_rule_cannot_act():
    rules = [R('A', 'wealth', '+'),
             R('X', 'meta', '+', effect={'type': 'cancels', 'targets': {'ids': ['Y']}}),
             R('Y', 'meta', '+', effect={'type': 'cancels', 'targets': {'ids': ['A']}})]
    o = Reader(rules).read(EINSTEIN, synthesize=False).outcomes()
    assert o['wealth']['score'] == 1


def test_scale_by_dignity():
    rules = [R('A', 'wealth', '+', scale={'dignity_of': 'Sun'})]
    f = Reader(rules).read(EINSTEIN).fired[0]
    assert 0 <= f.weight <= 1 and f.notes


@pytest.mark.skipif(not (Path(__file__).resolve().parents[1] / 'rules').is_dir(),
                    reason='the rule base (rules/) is not in the public copy: it paraphrases copyrighted translations')
def test_full_rule_base_reads_a_real_chart():
    r = Reader()
    natal = r.read(EINSTEIN)
    dated = r.read(EINSTEIN, EINSTEIN['birth_jd'] + 365.25 * 26.2)
    assert natal.fired and len(dated.fired) > len(natal.fired)
    assert isinstance(dated.text(), str) and dated.outcomes()
