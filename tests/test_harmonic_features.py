"""tests/test_harmonic_features.py — continuous harmonic features (src/harmonic_features.py)."""
import math

import numpy as np

from src import harmonic_features as H
from src import models as Mo
from src.interactive_cli import person_from_birth

EINSTEIN = person_from_birth("1879-03-14 11:30", 0.6658, 48.4, 9.9833)   # Albert Einstein, Ulm (AA)
NK = 2 * len(H.HARMONICS)


def _col(names, name):
    return names.index(name)


def test_encoding_peaks_on_aspects():
    e = H.encode(np.array([0.0, 180.0, 120.0, 90.0, 72.0, 60.0, 45.0]))
    cos = e[:, 0::2]                                  # columns: cos k for k in HARMONICS
    k = list(H.HARMONICS)
    assert np.allclose(cos[0], 1)                     # conjunction: every harmonic peaks
    assert math.isclose(cos[1, k.index(2)], 1)        # opposition
    assert math.isclose(cos[2, k.index(3)], 1)        # trine
    assert math.isclose(cos[3, k.index(4)], 1)        # square
    assert math.isclose(cos[4, k.index(5)], 1)        # quintile
    assert math.isclose(cos[5, k.index(6)], 1)        # sextile
    assert math.isclose(cos[6, k.index(8)], 1)        # octile
    assert cos[3, k.index(1)] < 1e-9                  # a square is not a conjunction
    assert np.allclose(np.abs(e) <= 1, True)


def test_vector_shape_names_and_values():
    hf = H.HarmonicFeaturizer()
    nb = len(H.TRANSIT_BODIES)
    assert hf.n == len(hf.names) == (nb * (nb - 1) // 2 + nb * len(H.NATAL_POINTS)) * NK + nb * 3
    v = hf.features(hf.context(EINSTEIN), EINSTEIN["birth_jd"] + 365.25 * 30)
    assert v.dtype == np.float32 and v.shape == (hf.n,) and np.isfinite(v).all()
    assert H.HarmonicFeaturizer(include_moon=True, helio=True).n > hf.n


def test_same_planet_angle_is_zero_at_birth():
    hf = H.HarmonicFeaturizer()
    v = hf.features(hf.context(EINSTEIN), EINSTEIN["birth_jd"])
    for b in H.TRANSIT_BODIES:
        target = "Node" if b == "Node" else b
        assert math.isclose(v[_col(hf.names, f"transit {b} to natal {target} cos1")], 1, abs_tol=1e-4)


def test_sky_is_shared_and_natal_part_is_personal():
    hf = H.HarmonicFeaturizer()
    other = person_from_birth("1946-08-19 08:51", -5, 33.6678, -93.5915)
    jd = 2461000.0
    a, b = hf.features(hf.context(EINSTEIN), jd), hf.features(hf.context(other), jd)
    g = hf.groups()
    assert np.array_equal(a[g["sky"]], b[g["sky"]]) and np.array_equal(a[g["kin"]], b[g["kin"]])
    assert not np.allclose(a[g["natal"]], b[g["natal"]])


def test_unknown_birth_time_gives_nan_angles_only():
    hf = H.HarmonicFeaturizer()
    p = dict(EINSTEIN, natal=EINSTEIN["natal"].copy())
    p["natal"][-1] = np.nan
    v = hf.features(hf.context(p), EINSTEIN["birth_jd"] + 4000)
    missing = np.array([("natal Ascendant " in n) or ("natal Midheaven " in n) for n in hf.names])
    assert np.isnan(v[missing]).all() and np.isfinite(v[~missing]).all()


def test_age_clocks_are_dropped_by_default():
    hf = H.HarmonicFeaturizer()
    clock = hf.age_clock_columns()
    assert len(clock) == len(H.SLOW) * NK
    assert all(hf.names[c].split(" to natal ")[0].split()[-1] in H.SLOW for c in clock)
    assert not set(clock) & set(hf.default_columns())
    assert "transit Saturn to natal Jupiter cos1" in [hf.names[c] for c in hf.default_columns()]


def test_float_matrix_and_shap_on_a_planted_signal():
    hf = H.HarmonicFeaturizer()
    s = {"name": "me", "category": "Marriage", "natal": EINSTEIN["natal"], "birth_jd": EINSTEIN["birth_jd"],
         "lat": EINSTEIN["lat"], "lon": EINSTEIN["lon"], "mask": [True] * 5,
         "jds": [EINSTEIN["birth_jd"] + 365.25 * y for y in (30, 27, 29, 31, 33)]}
    X, M = Mo.matrix([s], featurizer=hf)
    assert X.dtype == np.float32 and X.shape == (1, 5, hf.n)
    assert np.allclose(X[0, 0], hf.features(hf.context(s), s["jds"][0]))
    # SHAP recovers a column planted on event dates
    rng = np.random.default_rng(0)
    Xs = rng.normal(size=(600, 5, 20)).astype(np.float32)
    Xs[:, 0, 7] += 2.0
    Ms = np.ones((600, 5), bool)
    model = Mo.fit(Xs, Ms, np.arange(20), params={"min_child_samples": 20}, rounds=50)
    top = H.shap_importance(model, Xs, Ms, np.arange(20), [f"f{i}" for i in range(20)], top=1)
    assert top[0][0] == "f7"


def test_age_baseline():
    ab = H.AgeBaseline()
    assert math.isclose(ab.features(ab.context(EINSTEIN), EINSTEIN["birth_jd"] + 365.2422 * 40)[0], 40, rel_tol=1e-6)
