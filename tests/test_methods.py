"""tests/test_methods.py — period systems and the isolated methods (src/methods.py)."""
import numpy as np

from src import methods as M
from src.interactive_cli import person_from_birth


def test_zodiacal_releasing_periods():
    # From Aries (15 years): L1 Aries until 15; L2 starts in Aries for 15 months, then Taurus 8 months ...
    assert M.zr_l2(0, 0.0, 365.25 * 1.0) == (0, 0)
    assert M.zr_l2(0, 0.0, 365.25 * 1.3) == (0, 1)
    assert M.zr_l2(0, 0.0, 365.25 * 15.1)[0] == 1          # L1 moves to Taurus after 15 years
    # Loosening of the bond: an L1 longer than one full L2 round (211 months) jumps to the opposite sign.
    l1 = 10                                                 # Aquarius, 30 years
    t = (sum(M.ZR_YEARS) / 12 + 0.01) * 365.25
    assert M.zr_l2(l1, 0.0, t) == (10, 4)


def test_firdaria_order():
    assert M.firdaria(True, 0.0, 1.0) == ("Sun", "Sun")
    assert M.firdaria(True, 0.0, 365.25 * (10 / 7) + 1) == ("Sun", "Venus")   # Chaldean after Sun: Venus
    assert M.firdaria(False, 0.0, 1.0) == ("Moon", "Moon")
    assert M.firdaria(True, 0.0, 365.25 * 71.5)[0] == "Rahu"                 # 10+8+13+9+11+12+7 = 70
    assert M.firdaria(True, 0.0, 365.25 * 75.5) == ("Sun", "Sun")            # cycle repeats


def test_methods_on_a_real_chart():
    s = person_from_birth("1879-03-14 11:30", 0.6658, 48.4, 9.9833)   # Albert Einstein, Ulm (AA)
    p = M.Person(s)
    assert p.lag_sid == 2 and p.lag_trop == 3               # Gemini sidereal, Cancer tropical
    r = M.evaluate(p, s["birth_jd"] + 44.3 * 365.25)
    assert set(r) == set(M.METHODS)
    assert r["H1_profection"][1] == {M.F.SIGN_LORD[(3 + 44) % 12]}
    for m in M.METHODS:
        for cat in M.TARGETS:
            v = M.flagged(r, m, cat)
            assert v is None or isinstance(v, bool)
    assert M.flagged(r, "M1_medical_transits", "Marriage") is None


def test_bounds_tara_mudda():
    assert all(b[-1][1] == 30 for b in M.BOUNDS)
    assert M.bound_lord(3.0) == "Jupiter" and M.bound_lord(29.0) == "Saturn"       # Aries 0-6 Jupiter, 25-30 Saturn
    assert M.bound_lord(185.0) == "Saturn"                                         # Libra 0-6 Saturn
    assert M.tara(0.0, 0.0) == 1 and M.tara(13.4, 0.0) == 2 and M.tara(6 * 360 / 27 + 1, 0.0) == 7
    assert M.tara(9 * 360 / 27 + 1, 0.0) == 1                                      # 10th star = Janma again
    # Mudda: Ashwini (1) + 0 years - 2 = -1 -> 8 -> 8th from Ketu = Saturn
    assert M.mudda_lord(0.0, 0, 0.0) == "Saturn"
    assert M.mudda_lord(0.0, 1, 0.0) == "Mercury"


def test_all_methods_present_on_real_chart():
    s = person_from_birth("1879-03-14 11:30", 0.6658, 48.4, 9.9833)   # Albert Einstein, Ulm (AA)
    p = M.Person(s)
    r = M.evaluate(p, s["birth_jd"] + 44.3 * 365.25)
    assert set(r) == set(M.METHODS)
    assert M.flagged(r, "N1_tara", "Marriage") in (True, False)
