"""tests/test_rao.py — K.N. Rao's marriage parameters against the book's case studies
("Astrology and Timing of Marriage", Ch. 3): case 1 Bill Clinton, case 2 Hillary Clinton, married 11-10-1975.

Hillary is computed from the book's birth data (20:00 CST, Chicago). Astro-Databank now gives 18:45 from
the birth certificate, which changes her Lagna from Gemini to Taurus; the test checks the method, so it
uses the book's data. Known, documented differences from the book are asserted explicitly below."""
from datetime import date

import numpy as np
import pytest

from src import features as F
from src import preprocessing as P
from src import rao as R

SIGNS = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
WED = P.jd_noon(date(1975, 10, 11))


def _natal(bjd, lat, lon):
    swe, fl = F._swe()
    ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
           "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    return np.array([swe.calc_ut(bjd, ids[p], fl)[0][0] for p in P.NATAL[:-1]]
                    + [swe.houses_ex(bjd, lat, lon, b"W", swe.FLG_SIDEREAL)[1][0]])


@pytest.fixture(scope="module")
def cases():
    swe, _ = F._swe()
    bill_jd = swe.julday(1946, 8, 19, 8.5 + 6)          # book: 08:30, Hope (Arkansas), CST
    hill_jd = swe.julday(1947, 10, 27, 2.0)             # book: 20:00 CST, Chicago
    bill = R.context({"natal": _natal(bill_jd, 33.67, -93.59), "birth_jd": bill_jd}, "M")
    hill = R.context({"natal": _natal(hill_jd, 41.85, -87.65), "birth_jd": hill_jd}, "F")
    return {"bill": (bill, bill_jd), "hillary": (hill, hill_jd)}


def _derived(ctx, bjd):
    md, ad, pd = (F.DASHA_LORDS[i] for i in F.vimshottari_at(ctx["lon"]["Moon"], bjd, WED))
    cm, ca = R.chara_rao(ctx["chara"], WED)
    return {"lagna": SIGNS[ctx["lagna"]], "VS": SIGNS[ctx["VS"]], "DK": ctx["DK"], "DKN": SIGNS[ctx["DKN"]],
            "UP": SIGNS[ctx["UP"]], "DP": SIGNS[ctx["DP"]], "vim": (md, ad, pd), "chara": (SIGNS[cm], SIGNS[ca])}


def test_case1_bill_clinton_derived_values(cases):
    assert _derived(*cases["bill"]) == {"lagna": "Vir", "VS": "Cap", "DK": "Jupiter", "DKN": "Lib", "UP": "Leo",
                                        "DP": "Tau", "vim": ("Rahu", "Saturn", "Venus"), "chara": ("Sag", "Ari")}


def test_case1_bill_clinton_parameters(cases):
    f = dict(zip(R.NAMES, R.features(cases["bill"][0], WED)))
    book = {"p1": 1, "p2": 1, "p3": 0, "p4": 1, "p5": 1, "p6": 1, "p7": 1, "p8": 0, "o2": 0, "o3": 1}
    assert {k: f[n] for n in R.NAMES for k in book if n.startswith(f"rao_{k}_")} == book
    assert f["rao_o1_moon_trigger"] == 0      # book: 1 via Karakamsha Lagna, which is not implemented


def test_case2_hillary_clinton_derived_values(cases):
    d = _derived(*cases["hillary"])
    assert {k: v for k, v in d.items() if k != "chara"} == {"lagna": "Gem", "VS": "Gem", "DK": "Moon", "DKN": "Leo",
                                                             "UP": "Pis", "DP": "Lib", "vim": ("Mercury", "Jupiter", "Mercury")}
    assert d["chara"][0] == "Cap"             # book Cap/Pis: MD matches; the wedding falls in the MD's last
                                              # weeks, where our period boundaries give Aqu instead of Pis


def test_case2_hillary_clinton_parameters(cases):
    f = dict(zip(R.NAMES, R.features(cases["hillary"][0], WED)))
    book = {"p1": 1, "p2": 1, "p3": 1, "p5": 1, "p6": 1, "p7": 0, "p8": 0, "o1": 1, "o3": 1}
    assert {k: f[n] for n in R.NAMES for k in book if n.startswith(f"rao_{k}_")} == book
    # Documented differences: the book marks P4 and O2 as met; no rule stated in the book reproduces them.
    assert f["rao_p4_double_transit"] == 0 and f["rao_o2_saturn_dk"] == 0
