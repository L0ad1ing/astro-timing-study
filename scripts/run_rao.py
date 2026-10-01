"""
scripts/run_rao.py — K.N. Rao's marriage parameters on real marriages vs the same people's other dates.
Pre-registered: docs/prereg_rao.md. Training half only.

Part 1 (the book's own statistic, with controls): how often each parameter holds on the wedding date vs on
the same person's dates 3 and 1 years before and 1 and 3 years after (matched odds ratio).
Part 2: LightGBM LambdaRank on Rao features only / full features / full + Rao, each with out-of-fold
C-index, placebo C, window test, mandatory placebo window test and mismatched charts.
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import features as F                   # noqa: E402
from src import models as Mo                    # noqa: E402
from src import preprocessing as P              # noqa: E402
from src import rao as R                        # noqa: E402
from src import validation as V                 # noqa: E402

CHARTS_DB = P.SOURCE_DB                          # raw Astro-Databank pages (table `charts`)


def genders(names: list[str]) -> dict[str, str | None]:
    path = ROOT / "data" / "cache" / "gender.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    todo = [n for n in names if n not in cache]
    if todo:
        with sqlite3.connect(f"file:{CHARTS_DB}?mode=ro", uri=True) as c:
            for n in todo:
                row = c.execute("SELECT raw_html FROM charts WHERE name = ?", (n,)).fetchone()
                m = re.search(r"Gender\s*:\s*([MF])\b", re.sub(r"<[^>]+>", " ", row[0])) if row else None
                cache[n] = m.group(1) if m else None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache))
    return {n: cache.get(n) for n in names}


class RaoF(Mo.Featurizer):
    name, n = "rao", R.N

    def __init__(self, gender: dict):
        self.gender = gender

    def context(self, s):
        return R.context(s, self.gender.get(s["name"]))

    def features(self, ctx, jd):
        return R.features(ctx, jd)


class FullRaoF(RaoF):
    name, n = "full+rao", F.N_FEATURES + R.N

    def context(self, s):
        return (F.person_context(s), R.context(s, self.gender.get(s["name"])))

    def features(self, ctx, jd):
        return np.concatenate([F.features(ctx[0], jd), R.features(ctx[1], jd)])


def matched_or(case: np.ndarray, ctrl: np.ndarray, mask: np.ndarray) -> dict:
    """Mantel-Haenszel odds ratio for a binary exposure, one case vs its controls (Robins-Breslow-Greenland CI)."""
    exposed = (ctrl * mask).sum(1)
    n_ctrl = mask.sum(1)
    n = 1 + n_ctrl
    num_i, den_i = case * (n_ctrl - exposed) / n, (1 - case) * exposed / n
    Rr, S = num_i.sum(), den_i.sum()
    if Rr == 0 or S == 0:
        return {"odds_ratio": None}
    Pp, Q = (case + n_ctrl - exposed) / n, (1 - case + exposed) / n
    var = ((Pp * num_i).sum() / (2 * Rr ** 2) + ((Pp * den_i).sum() + (Q * num_i).sum()) / (2 * Rr * S)
           + (Q * den_i).sum() / (2 * S ** 2))
    se = math.sqrt(var)
    return {"odds_ratio": round(Rr / S, 3), "ci": [round(math.exp(math.log(Rr / S) - 1.96 * se), 3),
                                                   round(math.exp(math.log(Rr / S) + 1.96 * se), 3)]}


def book_table(X: np.ndarray, M: np.ndarray) -> dict:
    ctrl_mask = M[:, 1:]
    out = {}
    cols = {n: X[:, :, i] for i, n in enumerate(R.NAMES)}
    cols["six_or_more_of_P1_P8"] = (X[:, :, :8].sum(2) >= 6).astype(np.uint8)
    for name, col in cols.items():
        case, ctrl = col[:, 0].astype(float), col[:, 1:].astype(float)
        out[name] = {"wedding_dates": round(float(case.mean()), 3),
                     "control_dates": round(float((ctrl * ctrl_mask).sum() / ctrl_mask.sum()), 3),
                     **matched_or(case, ctrl, ctrl_mask)}
    return out


def evaluate(featurizer, columns, sets, folds, contexts) -> dict:
    X, M = Mo.matrix(sets, cache=ROOT / "data" / "cache", contexts=contexts, featurizer=featurizer)
    oof, models = Mo.cross_validated_scores(X, M, folds, columns)
    c = Mo.per_set_c(oof, M)
    rng = np.random.default_rng(5)
    idx = rng.choice(len(sets), size=min(1500, len(sets)), replace=False)
    res = {"c_index": round(float(c.mean()), 4), "c_ci": Mo.bootstrap_ci(c),
           "placebo_c": V.placebo_c_index(models, X, M, folds, "Marriage", columns),
           "window": V.window_test(models, sets, folds, 11, columns=columns, contexts=contexts, featurizer=featurizer),
           "placebo_window": V.placebo_window_test(models, sets, folds, 11, columns=columns, contexts=contexts,
                                                   featurizer=featurizer),
           "mismatched": V.mismatched_chart_c(models, [sets[i] for i in idx], folds[idx], rng, columns,
                                              featurizer=featurizer)}
    return res, X, M


def main() -> None:
    sets = [s for s in P.case_control_sets(P.SOURCE_DB, halves=(0,), categories=["Marriage"])
            if not math.isnan(s["natal"][P.NATAL.index("Ascendant")])]
    g = genders(sorted({s["name"] for s in sets}))
    folds = np.array([s["fold"] for s in sets])
    report = {"run_at": datetime.now(timezone.utc).isoformat(), "prereg": "docs/prereg_rao.md @ 81c426f",
              "sets": len(sets), "gender_known": sum(1 for s in sets if g.get(s["name"]) in ("M", "F"))}
    rao = RaoF(g)
    variants = {"rao_only": (rao, np.arange(R.N)),
                "full": (Mo.FULL, Mo.DEFAULT_COLUMNS),
                "full_plus_rao": (FullRaoF(g), np.concatenate([Mo.DEFAULT_COLUMNS, F.N_FEATURES + np.arange(R.N)]))}
    for name, (fz, cols) in variants.items():
        res, X, M = evaluate(fz, cols, sets, folds, {})
        if name == "rao_only":
            report["book_table"] = book_table(X, M)
            for k, v in report["book_table"].items():
                print(f"  {k:28s} wedding {v['wedding_dates']:.3f} | controls {v['control_dates']:.3f} | OR {v.get('odds_ratio')} {v.get('ci', '')}", flush=True)
        report[name] = res
        print(f"{name}: C {res['c_index']} {res['c_ci']} | placebo C {res['placebo_c']['placebo_c']} | window top1 "
              f"{res['window']['top1']} {res['window']['top1_ci']} top3 {res['window']['top3']} {res['window']['top3_ci']} | "
              f"placebo window top3 {res['placebo_window']['top3']} passed={res['placebo_window']['passed']} | "
              f"mismatched {res['mismatched']['mean']}", flush=True)
    out = ROOT / "docs" / f"results_rao_{datetime.now():%Y%m%d_%H%M}.json"
    out.write_text(json.dumps(report, indent=2))
    print("written", out)


if __name__ == "__main__":
    main()
