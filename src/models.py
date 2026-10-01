"""
src/models.py — feature matrices and the LightGBM LambdaRank model.

Each case-control set is one ranking query (the event date should rank first among its dates).
Cross-validation is grouped by person: fold = (crc32(name) >> 1) % 5 from preprocessing.split_ids,
which is GroupKFold with a fixed, reproducible assignment (a person's events are always in one fold).

Time-drift guard: no feature is calendar year or age. Two feature families are nonetheless clocks —
"Muntha in house h from natal Lagna" is exactly age mod 12, and dasha lords follow a fixed sequence
through life. AGE_CLOCK_COLUMNS lists the pure age clock (dropped by default); dasha features are the
technique under test and stay in, which is why validation.placebo_window_test is mandatory: it is the
check that caught dasha sequence order passing for "timing" (own death, 2026-09-30).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from src import features as F

PARAMS = {"objective": "lambdarank", "metric": "ndcg", "ndcg_eval_at": [1], "learning_rate": 0.03,
          "max_depth": 4, "num_leaves": 15, "min_child_samples": 150, "feature_fraction": 0.5,
          "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 5.0, "verbose": -1, "seed": 7}
ROUNDS = 300
AGE_CLOCK_COLUMNS = np.array([i for i, n in enumerate(F.FEATURE_NAMES) if n.startswith("Muntha in house")
                              and n.endswith("from natal Lagna")])
DEFAULT_COLUMNS = np.setdiff1d(np.arange(F.N_FEATURES), AGE_CLOCK_COLUMNS)


def schema_hash(columns: np.ndarray = DEFAULT_COLUMNS) -> str:
    return hashlib.sha256("\n".join(F.FEATURE_NAMES[i] for i in columns).encode()).hexdigest()[:16]


# ── Feature matrices ─────────────────────────────────────────────────────────

class Featurizer:
    """How to turn a person + date into features. Default: the 706 features of src/features.py."""
    name, n = "full", F.N_FEATURES

    def context(self, s: dict):
        return F.person_context(s)

    def features(self, ctx, jd: float) -> np.ndarray:
        return F.features(ctx, jd)


FULL = Featurizer()


def matrix(sets: list[dict], cache: Path | None = None, contexts: dict | None = None,
           featurizer: Featurizer = FULL) -> tuple[np.ndarray, np.ndarray]:
    """(X, mask): X is (sets, dates, n_features) over each set's case and control dates (uint8, or the
    featurizer's `dtype` — float32 for harmonic_features).
    Cached by the set keys and the featurizer."""
    key = hashlib.sha256(("|".join(f"{s['name']}:{s['category']}:{s['jds'][0]}" for s in sets)
                          + featurizer.name + str(featurizer.n)
                          + schema_hash(np.arange(F.N_FEATURES))).encode()).hexdigest()[:16]
    if cache:
        path = Path(cache) / f"X_{key}.npz"
        if path.exists():
            z = np.load(path)
            return z["X"], z["mask"]
    contexts = contexts if contexts is not None else {}
    X = np.zeros((len(sets), max(len(s["jds"]) for s in sets), featurizer.n), getattr(featurizer, "dtype", np.uint8))
    M = np.zeros(X.shape[:2], bool)
    for i, s in enumerate(sets):
        ctx = contexts.setdefault(s["name"], featurizer.context(s))
        for j, jd in enumerate(s["jds"]):
            X[i, j] = featurizer.features(ctx, jd)
        M[i, :len(s["jds"])] = s["mask"]
    if cache:
        Path(cache).mkdir(parents=True, exist_ok=True)
        np.savez_compressed(Path(cache) / f"X_{key}.npz", X=X, mask=M)
    return X, M


def _dataset(X: np.ndarray, M: np.ndarray, columns: np.ndarray):
    import lightgbm as lgb
    n, k, _ = X.shape
    y = np.zeros((n, k))
    y[:, 0] = 1
    rows = X[:, :, columns].reshape(n * k, -1)[M.reshape(-1)].astype(np.float32)
    return lgb.Dataset(rows, label=y.reshape(-1)[M.reshape(-1)], group=M.sum(axis=1))


# ── Model ────────────────────────────────────────────────────────────────────

def fit(X: np.ndarray, M: np.ndarray, columns: np.ndarray = DEFAULT_COLUMNS, params: dict | None = None,
        rounds: int = ROUNDS):
    import lightgbm as lgb
    return lgb.train({**PARAMS, **(params or {})}, _dataset(X, M, columns), num_boost_round=rounds)


def score(model, X: np.ndarray, M: np.ndarray, columns: np.ndarray = DEFAULT_COLUMNS) -> np.ndarray:
    """Model scores per date; -inf where the date is masked out."""
    n, k, _ = X.shape
    s = np.full((n, k), -np.inf)
    s[M] = model.predict(X[:, :, columns].reshape(n * k, -1)[M.reshape(-1)].astype(np.float32))
    return s


def score_dates(model, feats: np.ndarray, columns: np.ndarray = DEFAULT_COLUMNS) -> np.ndarray:
    return model.predict(feats[:, columns].astype(np.float32))


def c_index(scores: np.ndarray, M: np.ndarray) -> float:
    """P(event date outscores a same-person control date); ties count half."""
    s = np.where(M, scores, -np.inf)
    valid = M[:, 1:]
    wins = ((s[:, :1] > s[:, 1:]) & valid).sum(1) + 0.5 * ((s[:, :1] == s[:, 1:]) & valid).sum(1)
    return float((wins / valid.sum(1)).mean())


def bootstrap_ci(values: np.ndarray, stat=np.mean, n: int = 500, seed: int = 0) -> list[float]:
    rng = np.random.default_rng(seed)
    b = [stat(values[rng.integers(0, len(values), len(values))]) for _ in range(n)]
    return [round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]


def per_set_c(scores: np.ndarray, M: np.ndarray) -> np.ndarray:
    s = np.where(M, scores, -np.inf)
    valid = M[:, 1:]
    wins = ((s[:, :1] > s[:, 1:]) & valid).sum(1) + 0.5 * ((s[:, :1] == s[:, 1:]) & valid).sum(1)
    return wins / valid.sum(1)


def cross_validated_scores(X: np.ndarray, M: np.ndarray, folds: np.ndarray, columns: np.ndarray = DEFAULT_COLUMNS,
                           params: dict | None = None) -> tuple[np.ndarray, list]:
    """Out-of-fold scores (each set scored by a model that never saw its person) and the fold models."""
    out = np.full(M.shape, -np.inf)
    models = []
    for k in np.unique(folds):
        tr, va = folds != k, folds == k
        m = fit(X[tr], M[tr], columns, params)
        out[va] = score(m, X[va], M[va], columns)
        models.append(m)
    return out, models
