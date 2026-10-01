"""tests/test_discovery_v2.py — leak-free split, control filter, matched statistics, rule text."""
import math

import numpy as np

from scripts.run_rao import matched_or
from src import preprocessing as P
from src.discovery_v2 import leak_free_splitter as S
from src.discovery_v2 import matched_controls as MC
from src.discovery_v2 import rule_evaluator as E


def _set(name, y, m, d, offsets=(-3, -1, 1, 3)):
    from datetime import date, timedelta
    ev = date(y, m, d)
    jds = [P.jd_noon(ev)] + [P.jd_noon(ev + timedelta(days=round(k * P.YEAR))) for k in offsets]
    return {"name": name, "jds": jds, "mask": [True] * 5, "birth_jd": jds[0] - 30 * 365.25}


def test_split_shares_no_person_month_or_date():
    sets = [_set("a", 1990, 2, 10), _set("b", 1990, 2, 10), _set("c", 1991, 3, 5), _set("a", 1995, 7, 1),
            _set("d", 1980, 11, 20), _set("e", 1984, 6, 15), _set("f", 1984, 1, 31)]
    tr, te, info = S.split(sets)
    assert S.audit(sets, tr, te) == {"shared_persons": 0, "shared_year_months": 0, "shared_dates": 0}
    assert {sets[i]["name"] for i in te} == {"a", "b", "d"}          # Feb and Nov events
    assert 3 not in tr                                               # 'a' lives on the test side (first event in Feb)
    assert info["person_on_other_side"] == 1


def test_control_filter_masks_years_with_other_events():
    s = _set("a", 2000, 6, 1)
    events = {"a": np.array([s["jds"][2] + 10, s["jds"][0]])}         # something 10 days after the -1y control
    out = MC.filter_controls([s], events)
    assert out[0]["mask"] == [True, True, False, True, True]
    assert MC.filter_controls([s], {"a": np.array(s["jds"][1:4]) + 5}) == []   # fewer than 2 controls left


def test_mh_vector_matches_matched_or():
    rng = np.random.default_rng(0)
    E_ = rng.random((400, 5)) < 0.3
    E_[:, 0] |= rng.random(400) < 0.15
    M = np.ones((400, 5), bool)
    M[::7, 4] = False
    v = E.mh_vector(E_[:, :, None], M)
    ref = matched_or(E_[:, 0].astype(float), E_[:, 1:].astype(float), M[:, 1:])
    assert math.isclose(math.exp(v["log_or"][0]), ref["odds_ratio"], rel_tol=1e-3)
    lo = math.exp(v["log_or"][0] - 1.96 * v["se"][0])
    assert math.isclose(lo, ref["ci"][0], rel_tol=1e-2)


def test_clogit_recovers_a_planted_effect_and_adjusts_for_a_confounder():
    rng = np.random.default_rng(1)
    n = 3000
    age = rng.normal(size=(n, 5))
    rule = (rng.random((n, 5)) < 0.3).astype(float)
    logits = 1.0 * age + 0.7 * rule
    p = np.exp(logits - logits.max(1, keepdims=True))
    p /= p.sum(1, keepdims=True)
    pick = np.array([rng.choice(5, p=row) for row in p])
    order = np.array([[i] + [j for j in range(5) if j != i] for i in pick])
    X = np.stack([np.take_along_axis(rule, order, 1), np.take_along_axis(age, order, 1)], axis=2)
    fit = E.clogit(X, np.ones((n, 5), bool))
    assert abs(fit["beta"][0] - 0.7) < 0.15 and abs(fit["beta"][1] - 1.0) < 0.15 and fit["p"][0] < 1e-6


def test_describe_and_bh():
    names = ["transit Mars to natal Venus cos4", "Mars speed ratio"]
    assert E.describe(((0, ">=", math.cos(math.radians(20))),), names) == \
        "transit Mars to natal Venus within ±5.0° of a multiple of 90°"
    assert E.describe(((1, "<=", 0.1),), names) == "Mars speed ratio <= 0.1"
    q = E.bh(np.array([0.001, 0.04, 0.03, 0.5]))
    assert np.allclose(q, [0.004, 0.0533, 0.0533, 0.5], atol=1e-3)
