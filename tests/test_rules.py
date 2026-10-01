"""tests/test_rules.py — astrological rules in src/features.py checked against their classical definitions."""
import math

import numpy as np

from src import features as F

POS = {"Sun": 10.0, "Moon": 40.0, "Mars": 100.0, "Mercury": 25.0, "Jupiter": 250.0, "Venus": 350.0,
       "Saturn": 190.0, "Rahu": 70.0}
P9 = {**POS, "Ketu": 250.0}


def test_bav_totals_match_bphs():
    assert {p: sum(len(h) for h in F.BAV[p].values()) for p in F.SEVEN} == \
        {"Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54, "Jupiter": 56, "Venus": 52, "Saturn": 39}
    t = F.bav_tables(np.array([10, 40, 70, 100, 130, 160, 190, 220, 250.0]))
    assert sum(t["SAV"]) == 337


def test_jaimini_aspects():
    assert {b for b in range(12) if F.jaimini_aspects(0, b)} == {4, 7, 10}
    assert {b for b in range(12) if F.jaimini_aspects(1, b)} == {3, 6, 9}
    assert {b for b in range(12) if F.jaimini_aspects(2, b)} == {5, 8, 11}


def test_chara_years():
    assert F.chara_years(0, P9) == 2          # Mars in Cancer: 4 - 1 = 3, debilitated -> 2
    assert F.chara_years(1, P9) == 11         # Venus in Pisces: 11 - 1 = 10, exalted -> 11
    assert F.chara_years(3, P9) == 3          # Cancer counts backward to Taurus: 3 - 1 = 2, Moon exalted -> 3


def test_divisional_signs():
    assert F.d9_sign(0.0) == 0 and F.d9_sign(30.0) == 9
    assert F.d10_sign(0.0) == 0 and F.d10_sign(30.0) == 9


def test_vimshottari_and_yogini_starts():
    assert F.vimshottari_at(0.0, 2451545.0, 2451545.0) == (0, 0, 0)          # Ashwini: Ketu/Ketu/Ketu
    assert F.YOGINI_LORDS[F.yogini_at(0.0, 2451545.0, 2451545.0)[0]] == "Mars"  # Ashwini -> Bhramari
    assert F.yogini_at(5.5 * 360 / 27, 2451545.0, 2451545.0)[0] == 0          # Ardra -> Mangala


def test_feature_layout():
    assert F.N_FEATURES == 706 and len(set(F.FEATURE_NAMES)) == 706
    ctx = F.person_context({"natal": np.array([10, 40, 70, 100, 130, 160, 190, 220, math.nan]),
                            "birth_jd": 2445131.0})
    f = F.features(ctx, 2445131.0 + 1e4)
    assert f[F.GROUPS["J"]].sum() == 0 and f[F.GROUPS["C"]].sum() == 0      # no birth time: no houses
