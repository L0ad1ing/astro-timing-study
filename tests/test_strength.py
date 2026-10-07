"""tests/test_strength.py — planetary strength and dignity features (src/strength.py)."""
import math

import numpy as np

from src import strength as S
from src import features as F
from src.interactive_cli import person_from_birth

EINSTEIN = person_from_birth("1879-03-14 11:30", 0.6658, 48.4, 9.9833)   # Friday morning, Ulm (AA)


def _idx(name):
    return S.PLANET_FEATURES.index(name)


def test_exaltation_debilitation_and_uchcha():
    assert S.dignity('Sun', 10.0) == 'exalted' and math.isclose(S.uchcha_bala('Sun', 10.0), 60)
    assert S.dignity('Saturn', 20.0) == 'debilitated' and math.isclose(S.uchcha_bala('Saturn', 20.0), 0)
    assert math.isclose(S.uchcha_bala('Sun', 100.0), 30)            # 90 deg from deep exaltation
    assert S.dignity('Sun', 125.0) == 'moolatrikona'                 # Leo 5
    assert S.dignity('Sun', 145.0) == 'own'                          # Leo 25
    assert S.dignity('Jupiter', 95.0) == 'exalted' and S.dignity('Jupiter', 275.0) == 'debilitated'


def test_natural_and_compound_friendship():
    assert S.natural_relation('Sun', 'Saturn') == 'enemy'
    assert S.natural_relation('Moon', 'Mars') == 'neutral'
    assert S.natural_relation('Rahu', 'Venus') == 'friend'           # Rahu uses Saturn's friendships
    # Mars and Jupiter are natural friends; Jupiter 2nd from Mars -> great friend; 7th -> neutral
    assert S.compound_relation('Mars', 'Jupiter', 0, 1) == 'great_friend'
    assert S.compound_relation('Mars', 'Jupiter', 0, 6) == 'neutral'
    assert S.compound_relation('Sun', 'Saturn', 0, 6) == 'great_enemy'


def test_baladi_and_cheshta():
    assert S.baladi(0, 3) == 0.25 and S.baladi(0, 15) == 1.0          # Aries (odd): infant, adult
    assert S.baladi(1, 3) == 0.0 and S.baladi(1, 27) == 0.25          # Taurus (even): reversed
    assert S.cheshta_proxy(True, -0.5) == 60 and S.cheshta_proxy(False, 1.0) == 15


def test_natal_strength_on_a_real_chart():
    st = S.natal_strength({**EINSTEIN, 'name': None})
    assert set(st['vec']) == set(S.GRAHAS)
    for p, v in st['vec'].items():
        assert v.shape == (S.NP,)
        core = v[:S.NP - len(S.SHADBALA_COLS)]
        assert np.isfinite(core).all(), p
        assert 0 <= v[_idx('uchcha')] <= 60 and 0 <= v[_idx('ishta')] <= 60
    # Einstein was born on a Friday after sunrise -> weekday lord Venus
    assert st['vec']['Venus'][_idx('vara_lord')] == 1
    assert sum(st['vec'][p][_idx('vara_lord')] for p in S.GRAHAS) == 1
    assert sum(st['vec'][p][_idx('hora_lord')] for p in S.GRAHAS) == 1


def test_yogakaraka_for_libra_lagna():
    # Libra lagna: Saturn rules the 4th (Capricorn) and 5th (Aquarius) -> yogakaraka
    s = dict(EINSTEIN, name=None, natal=EINSTEIN['natal'].copy())
    s['natal'][-1] = 6 * 30 + 10.0
    st = S.natal_strength(s)
    assert st['vec']['Saturn'][_idx('yogakaraka')] == 1
    assert st['vec']['Jupiter'][_idx('yogakaraka')] == 0


def test_featurizer_shape_and_age_clock_exclusion():
    sf = S.StrengthFeaturizer()
    ctx = sf.context({**EINSTEIN, 'name': None})
    v = sf.features(ctx, EINSTEIN['birth_jd'] + 365.25 * 30.3)
    assert v.shape == (F.N_FEATURES + S.N_STRENGTH,) and v.dtype == np.float32
    assert len(S.STRENGTH_NAMES) == S.N_STRENGTH
    # age-cycle slots: no houses-ruled mask and no lordship flags (both partly age clocks)
    assert not any(n.startswith(('year_lord rules', 'muntha_lord rules', 'bcp_lord rules')) for n in S.STRENGTH_NAMES)
    assert not any(n.startswith(('year_lord yogakaraka', 'bcp_lord yogakaraka')) for n in S.STRENGTH_NAMES)
    assert 'year_lord uchcha' in S.STRENGTH_NAMES and 'year_lord occupies house 4' in S.STRENGTH_NAMES
    assert any(n.startswith('vim_md rules house') for n in S.STRENGTH_NAMES)
    # only the precomputed Shadbala columns may be NaN (no database row in tests)
    nan_names = {S.STRENGTH_NAMES[i] for i in np.where(np.isnan(v[F.N_FEATURES:]))[0]}
    assert all(n.split(' ', 1)[1].startswith('sb_') for n in nan_names)
