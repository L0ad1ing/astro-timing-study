"""tests/test_parity.py — the repo reproduces the author's earlier private research prototype ("Abraxas") exactly
(set selection and all 706 features), so results from either are the same study. Skipped unless that prototype
(env ABRAXAS_DIR) and the data are present."""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

from src import features as F
from src import preprocessing as P

ABRAXAS = Path(os.environ.get("ABRAXAS_DIR", "__absent__"))
pytestmark = pytest.mark.skipif(not (ABRAXAS.exists() and P.SOURCE_DB.exists()), reason="needs Abraxas + source DB")


@pytest.fixture(scope="module")
def both():
    sys.path.insert(0, str(ABRAXAS))
    from cognition.team import event_model_v4 as v4
    old = v4.people_sets(P.SOURCE_DB, half=0, cats=["Arrest", "Divorce"])
    new = P.case_control_sets(P.SOURCE_DB, halves=(0,), categories=["Arrest", "Divorce"])
    return v4, old, new


def test_same_sets_selected(both):
    _, old, new = both
    key = lambda s, c: (s["name"], s[c], tuple(round(j, 6) for j in s["jds"]), tuple(s["mask"]))
    assert sorted(key(s, "cat") for s in old) == sorted(key(s, "category") for s in new)


def test_identical_features(both):
    v4, old, new = both
    by_key = {(s["name"], s["jds"][0], s["category"]): s for s in new}
    rng = np.random.default_rng(0)
    for s in rng.choice(old, size=60, replace=False):
        n = by_key[(s["name"], s["jds"][0], s["cat"])]
        ctx = F.person_context(n)
        for jd in s["jds"]:
            a, b = v4.v4_features(s, jd), F.features(ctx, jd)
            assert a.shape == b.shape == (F.N_FEATURES,)
            diff = np.flatnonzero(a != b)
            assert diff.size == 0, [F.FEATURE_NAMES[i] for i in diff[:5]]
