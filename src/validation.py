"""
src/validation.py — falsification tests every run must pass, and the lock-box.

All tests use out-of-fold models: a set is only ever scored by the model trained without its person's fold.

  placebo_c_index       a control date is treated as the "event" (the real event removed). A model that
                        detects events scores ~0.50; one exploiting date position scores like the real test.
  window_test           rank the 20 quarters of a 5-year stretch containing the event; hit = the event's
                        quarter is 1st / in the top 3 (chance 5% / 15%). Random tie-breaking (period-based
                        features are constant for months, so exact ties are common).
  placebo_window_test   MANDATORY. The same stretch shifted 2 years earlier, where nothing happened; the
                        "target" quarter keeps its position. Fails if its hit rate is above chance (95%
                        interval lower bound > chance) — the model is reading time position, not events.
                        This caught the own-death "breakthrough" on 2026-09-30.
  mismatched_chart_c    every feature recomputed from another person's natal positions (own birth moment
                        and place kept, so age and the dasha clock are unchanged). Should fall to ~0.50.
  subgroup_c            AA vs A birth-time ratings; complete-control sets only (right-censoring check).
  lockbox_save/verify   freeze model, parameters, feature schema and checksums for evaluation only on
                        events after the study cutoff.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from src import features as F
from src import models as Mo
from src import preprocessing as P

QUARTERS, SPAN = 20, 5 * P.YEAR
Q = SPAN / QUARTERS
PLACEBO_SHIFT = 2 * P.YEAR
CHANCE_TOP1, CHANCE_TOP3 = 1 / QUARTERS, 3 / QUARTERS


def _fold_models(models: list, folds: np.ndarray) -> dict:
    return dict(zip(np.unique(folds), models))


# ── Case-control level ───────────────────────────────────────────────────────

def placebo_c_index(models: list, X: np.ndarray, M: np.ndarray, folds: np.ndarray, category: str,
                    columns=Mo.DEFAULT_COLUMNS) -> dict:
    """Pseudo-event = the control 1 year before the event, compared with the remaining controls."""
    order = [4, 3, 2, 1] if category == "Death" else [2, 1, 3, 4]      # slots of [-1y, others]
    Xp, Mp = X[:, order, :], M[:, order]
    keep = Mp[:, 0] & (Mp[:, 1:].sum(1) >= 2)
    fm = _fold_models(models, folds)
    scores = np.full(Mp.shape, -np.inf)
    for k, m in fm.items():
        sel = keep & (folds == k)
        if sel.any():
            scores[sel] = Mo.score(m, Xp[sel], Mp[sel], columns)
    c = Mo.per_set_c(scores[keep], Mp[keep])
    return {"placebo_c": round(float(c.mean()), 4), "ci": Mo.bootstrap_ci(c), "sets": int(keep.sum())}


def mismatched_chart_c(models: list, sets: list[dict], folds: np.ndarray, rng: np.random.Generator,
                       columns=Mo.DEFAULT_COLUMNS, permutations: int = 3, featurizer=Mo.FULL) -> dict:
    fm = _fold_models(models, folds)
    pool = [s["natal"] for s in sets]
    results = []
    for _ in range(permutations):
        donors = rng.integers(0, len(pool), len(sets))
        per_set = []
        for i, s in enumerate(sets):
            ctx = featurizer.context({**s, "natal": pool[donors[i]]})
            feats = np.array([featurizer.features(ctx, jd) for jd in s["jds"]])
            sc = np.full(len(s["jds"]), -np.inf)
            m = np.array(s["mask"])
            sc[m] = Mo.score_dates(fm[folds[i]], feats[m], columns)
            per_set.append(Mo.per_set_c(sc[None, :], m[None, :])[0])
        results.append(float(np.mean(per_set)))
    return {"mismatched_c": [round(r, 4) for r in results], "mean": round(float(np.mean(results)), 4)}


def subgroup_c(oof_scores: np.ndarray, M: np.ndarray, sets: list[dict]) -> dict:
    out = {}
    rating = np.array([s["rating"] for s in sets])
    complete = np.array([s["complete"] for s in sets])
    for label, sel in (("AA", rating == "AA"), ("A", rating == "A"), ("complete_controls", complete)):
        if sel.sum() >= 50:
            c = Mo.per_set_c(oof_scores[sel], M[sel])
            out[label] = {"c": round(float(c.mean()), 4), "ci": Mo.bootstrap_ci(c), "sets": int(sel.sum())}
    return out


# ── Window level ─────────────────────────────────────────────────────────────

def _stretch(s: dict, rng: np.random.Generator, shift: float) -> tuple[float, int] | None:
    """Start JD of a 5-year stretch containing the (shifted) event, and the event's quarter."""
    ev = s["jds"][0] - shift
    lo = s["birth_jd"] + P.YEAR
    hi = min(P.jd_noon(P.STUDY_CUTOFF), s["death_jd"] or np.inf)
    if s["category"] == "Death":
        start = ev - SPAN + 1
    else:
        start = min(max(ev - rng.uniform(0, SPAN), lo), hi - SPAN)
    if start < lo or start + SPAN > hi + 1 or not (start <= ev < start + SPAN):
        return None
    return start, int((ev - start) // Q)


def window_test(models: list, sets: list[dict], folds: np.ndarray, seed: int, shift: float = 0.0,
                columns=Mo.DEFAULT_COLUMNS, contexts: dict | None = None, featurizer=Mo.FULL) -> dict:
    """Top-1 / top-3 quarter hit rates. The same seed gives the same event positions, so a placebo run
    (shift > 0) mirrors the real run exactly, two years earlier."""
    rng = np.random.default_rng(seed)
    tie = np.random.default_rng(seed + 1)
    fm = _fold_models(models, folds)
    contexts = contexts if contexts is not None else {}
    ranks = []
    for i, s in enumerate(sets):
        w = _stretch(s, rng, shift)
        if w is None:
            continue
        start, target = w
        ctx = contexts.setdefault(s["name"], featurizer.context(s))
        jds = [start + q * Q + f * Q for q in range(QUARTERS) for f in (1 / 6, 1 / 2, 5 / 6)]
        feats = np.array([featurizer.features(ctx, jd) for jd in jds])
        q = Mo.score_dates(fm[folds[i]], feats, columns).reshape(QUARTERS, 3).mean(1)
        q = q + tie.random(QUARTERS) * 1e-9 * (np.abs(q).max() + 1)
        ranks.append(int((q > q[target]).sum() + 1))
    r = np.array(ranks)
    return {"events": int(len(r)),
            "top1": round(float(np.mean(r <= 1)), 4), "top1_ci": Mo.bootstrap_ci((r <= 1).astype(float)),
            "top3": round(float(np.mean(r <= 3)), 4), "top3_ci": Mo.bootstrap_ci((r <= 3).astype(float))}


def placebo_window_test(models: list, sets: list[dict], folds: np.ndarray, seed: int, columns=Mo.DEFAULT_COLUMNS,
                        contexts: dict | None = None, featurizer=Mo.FULL) -> dict:
    res = window_test(models, sets, folds, seed, shift=PLACEBO_SHIFT, columns=columns, contexts=contexts,
                      featurizer=featurizer)
    res["passed"] = bool(res["top1_ci"][0] <= CHANCE_TOP1 and res["top3_ci"][0] <= CHANCE_TOP3)
    return res


# ── Lock-box ─────────────────────────────────────────────────────────────────

def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lockbox_save(model, category: str, out_dir: Path, columns=Mo.DEFAULT_COLUMNS, extra: dict | None = None) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    mf = out_dir / f"{category}.lgb.txt"
    model.save_model(str(mf))
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                cwd=Path(__file__).resolve().parents[1]).stdout.strip()
    except Exception:
        commit = "unknown"
    manifest_path = out_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"models": {}}
    manifest.update(cutoff=P.STUDY_CUTOFF.isoformat(), code_commit=commit,
                    rule="Evaluate only on events dated after the cutoff (or people added after it). Do not retrain.")
    manifest["models"][category] = {"file": mf.name, "sha256": _sha(mf), "params": Mo.PARAMS, "rounds": Mo.ROUNDS,
                                    "feature_schema": Mo.schema_hash(columns), "n_features": int(len(columns)),
                                    "frozen_at": datetime.now(timezone.utc).isoformat(), **(extra or {})}
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest["models"][category]


def lockbox_verify(out_dir: Path) -> dict[str, bool]:
    """True per model if its file still matches the frozen checksum and the feature schema is unchanged."""
    manifest = json.loads((Path(out_dir) / "manifest.json").read_text())
    return {cat: _sha(Path(out_dir) / m["file"]) == m["sha256"] and m["feature_schema"] == Mo.schema_hash()
            for cat, m in manifest["models"].items()}
