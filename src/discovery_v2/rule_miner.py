"""
src/discovery_v2/rule_miner.py — candidate geometric rules from the training partition only.

  univariate_rules   every feature ≤ its 10th / 25th or ≥ its 75th / 90th training percentile
  tree_rules         every leaf path of a depth-2 LightGBM LambdaRank ensemble (two-condition rules)
  select             MH z on training → top `pre` → conditional-logistic z adjusted for the baseline score → top `k`
"""
from __future__ import annotations

import numpy as np

from src import models as Mo
from src.discovery_v2 import rule_evaluator as E

QUANTILES = (0.10, 0.25, 0.75, 0.90)


def univariate_rules(X: np.ndarray, M: np.ndarray, cols: np.ndarray, chunk: int = 150) -> list[tuple[tuple, float]]:
    out = []
    for a in range(0, len(cols), chunk):
        c = cols[a:a + chunk]
        V = X[:, :, c]
        q = np.nanquantile(V[M], QUANTILES, axis=0)                  # (4, chunk)
        for qi, lvl in enumerate(QUANTILES):
            op = "<=" if lvl < 0.5 else ">="
            Ex = (V <= q[qi]) if op == "<=" else (V >= q[qi])
            z = E.mh_vector(Ex, M)["z"]
            out += [(((int(f), op, float(t)),), float(zz)) for f, t, zz in zip(c, q[qi], z) if np.isfinite(zz)]
    return out


def tree_rules(X: np.ndarray, M: np.ndarray, cols: np.ndarray, rounds: int = 200) -> list[tuple[tuple, float]]:
    model = Mo.fit(X, M, cols, params={"max_depth": 2, "num_leaves": 4, "min_child_samples": 50}, rounds=rounds)
    paths: set[tuple] = set()

    def walk(node, conds):
        if "leaf_index" in node:
            if conds:
                paths.add(tuple(conds))
            return
        f, t = int(cols[node["split_feature"]]), float(node["threshold"])
        walk(node["left_child"], conds + [(f, "<=", t)])
        walk(node["right_child"], conds + [(f, ">", t)])

    for tree in model.dump_model()["tree_info"]:
        walk(tree["tree_structure"], [])
    rules = sorted(paths)
    out = []
    for a in range(0, len(rules), 200):
        batch = rules[a:a + 200]
        z = E.mh_vector(np.stack([E.exposure(X, r) for r in batch], axis=2), M)["z"]
        out += [(r, float(zz)) for r, zz in zip(batch, z) if np.isfinite(zz)]
    return out


def select(cands: list[tuple[tuple, float]], X: np.ndarray, M: np.ndarray, base: np.ndarray, pre: int = 200,
           k: int = 20) -> list[dict]:
    seen, top = set(), []
    for r, z in sorted(cands, key=lambda c: -abs(c[1])):
        if r not in seen:
            seen.add(r)
            top.append((r, z))
        if len(top) == pre:
            break
    base = np.where(M, base, 0.0)
    scored = []
    for r, z in top:
        ex = E.exposure(X, r).astype(float)
        fit = E.clogit(np.stack([ex, base], axis=2), M)
        scored.append({"rule": r, "train_mh_z": round(z, 3), "train_adj_z": round(float(fit["z"][0]), 3),
                       "train_beta": round(float(fit["beta"][0]), 4),
                       "train_rate_event": round(float(ex[:, 0].mean()), 4),
                       "train_rate_control": round(float((ex[:, 1:] * M[:, 1:]).sum() / M[:, 1:].sum()), 4)})
    return sorted(scored, key=lambda d: -abs(d["train_adj_z"]))[:k]
