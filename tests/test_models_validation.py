"""tests/test_models_validation.py — the model and the falsification tests on synthetic data where the
right answer is known (including a deliberate time-drift artifact the placebo must catch)."""
import numpy as np

from src import models as Mo
from src import preprocessing as P
from src import validation as V

NF = Mo.F.N_FEATURES


def _synthetic(n, rng, plant_event=None, plant_latest=False, category="Marriage"):
    X = (rng.random((n, 5, NF)) < 0.05).astype(np.uint8)
    M = np.ones((n, 5), bool)
    if plant_event is not None:                       # a real "astrological" signal on the event date
        X[:, 0, plant_event] = (rng.random(n) < 0.5)
    if plant_latest:                                  # a clock: fires more often the later the date
        # recency rank per slot. Death slots [event,-4,-3,-2,-1]; others [event,-3,-1,+1,+3]
        recency = [4, 0, 1, 2, 3] if category == "Death" else [2, 0, 1, 3, 4]
        for slot, r in enumerate(recency):
            X[:, slot, 7] = rng.random(n) < 0.1 + 0.2 * r
    return X, M, rng.integers(0, 5, n)


def test_model_learns_a_planted_signal_out_of_fold():
    rng = np.random.default_rng(0)
    col = int(Mo.DEFAULT_COLUMNS[3])
    X, M, folds = _synthetic(3000, rng, plant_event=col)
    oof, _ = Mo.cross_validated_scores(X, M, folds)
    assert Mo.c_index(oof, M) > 0.6


def test_no_signal_gives_chance():
    rng = np.random.default_rng(1)
    X, M, folds = _synthetic(2000, rng)
    oof, _ = Mo.cross_validated_scores(X, M, folds)
    assert abs(Mo.c_index(oof, M) - 0.5) < 0.04


def test_placebo_catches_a_time_drift_artifact():
    rng = np.random.default_rng(2)
    X, M, folds = _synthetic(3000, rng, plant_latest=True, category="Death")
    oof, models = Mo.cross_validated_scores(X, M, folds)
    assert Mo.c_index(oof, M) > 0.6                               # looks like a real effect...
    pl = V.placebo_c_index(models, X, M, folds, "Death")
    assert pl["placebo_c"] > 0.58                                 # ...and the placebo exposes it (no event there)


def test_placebo_passes_a_genuine_event_signal():
    rng = np.random.default_rng(3)
    col = int(Mo.DEFAULT_COLUMNS[5])
    X, M, folds = _synthetic(3000, rng, plant_event=col)
    _, models = Mo.cross_validated_scores(X, M, folds)
    pl = V.placebo_c_index(models, X, M, folds, "Marriage")
    assert abs(pl["placebo_c"] - 0.5) < 0.04


def test_age_clock_is_excluded_by_default():
    assert len(Mo.AGE_CLOCK_COLUMNS) == 12
    assert not set(Mo.AGE_CLOCK_COLUMNS) & set(Mo.DEFAULT_COLUMNS)


def test_lockbox_roundtrip_and_tamper_detection(tmp_path):
    rng = np.random.default_rng(4)
    X, M, _ = _synthetic(500, rng, plant_event=int(Mo.DEFAULT_COLUMNS[0]))
    m = Mo.fit(X, M, rounds=20)
    V.lockbox_save(m, "Marriage", tmp_path)
    assert V.lockbox_verify(tmp_path) == {"Marriage": True}
    with open(tmp_path / "Marriage.lgb.txt", "a") as fh:
        fh.write("\n# tampered")
    assert V.lockbox_verify(tmp_path) == {"Marriage": False}


def test_new_event_types():
    assert P.refine_category("Other", "Work : Prize") == "Prize"
    assert P.refine_category("Other", "Work : Fired/Laid off/Quit ") == "Job_End"
    assert P.refine_category("Other", "Crime : Law suit") == "Trial"
    assert P.refine_category("Other", "Relationship : Meet a significant person") == "Relationship_Begin"
    assert P.refine_category("Other", "Work : Published/ Exhibited/ Released") == "Other"
    assert P.refine_category("Marriage", "Married") == "Marriage"
