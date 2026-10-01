"""
scripts/run_pipeline.py — end to end for chosen event types, on the TRAINING half only (half 1 is retired).

Per event type: case-control sets -> features -> 5-fold person-grouped CV (out-of-fold scores) ->
C-index, placebo C, subgroups (AA/A, complete controls), window test, MANDATORY placebo window test,
mismatched charts (sampled) -> final model on the whole training half frozen in the lock-box.
A result counts only if the placebo window test passes and the mismatched-chart C is ~0.50.

Usage: python scripts/run_pipeline.py Prize Job_Start ... [--mismatch-sample 1500] [--no-lockbox]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import models as Mo                     # noqa: E402
from src import preprocessing as P               # noqa: E402
from src import validation as V                  # noqa: E402


def run_category(cat: str, sets: list[dict], args, contexts: dict) -> dict:
    X, M = Mo.matrix(sets, cache=ROOT / "data" / "cache", contexts=contexts)
    folds = np.array([s["fold"] for s in sets])
    oof, models = Mo.cross_validated_scores(X, M, folds)
    c = Mo.per_set_c(oof, M)
    res = {"sets": len(sets), "c_index": round(float(c.mean()), 4), "c_ci": Mo.bootstrap_ci(c),
           "placebo_c": V.placebo_c_index(models, X, M, folds, cat),
           "subgroups": V.subgroup_c(oof, M, sets),
           "window": V.window_test(models, sets, folds, seed=11, contexts=contexts),
           "placebo_window": V.placebo_window_test(models, sets, folds, seed=11, contexts=contexts)}
    rng = np.random.default_rng(5)
    idx = rng.choice(len(sets), size=min(args.mismatch_sample, len(sets)), replace=False)
    res["mismatched"] = V.mismatched_chart_c(models, [sets[i] for i in idx], folds[idx], rng)
    w, pw = res["window"], res["placebo_window"]
    res["verdict"] = (
        "FAILS placebo (time drift)" if not pw["passed"] else
        "FAILS mismatched-chart test" if res["mismatched"]["mean"] > 0.52 else
        "window signal above chance" if w["top3_ci"][0] > V.CHANCE_TOP3 or w["top1_ci"][0] > V.CHANCE_TOP1 else
        "no window signal")
    if not args.no_lockbox:
        final = Mo.fit(X, M)
        res["lockbox"] = V.lockbox_save(final, cat, ROOT / "lockbox",
                                        extra={"training_sets": len(sets), "cv_c_index": res["c_index"]})
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("categories", nargs="*", default=P.NEW_CATEGORIES)
    ap.add_argument("--mismatch-sample", type=int, default=1500)
    ap.add_argument("--no-lockbox", action="store_true")
    args = ap.parse_args()
    sets = P.case_control_sets(P.SOURCE_DB, halves=(0,), categories=args.categories)
    report = {"run_at": datetime.now(timezone.utc).isoformat(), "half": "training (0)",
              "chance": {"top1": V.CHANCE_TOP1, "top3": V.CHANCE_TOP3}, "categories": {}}
    contexts: dict = {}
    for cat in args.categories:
        cs = [s for s in sets if s["category"] == cat]
        if len(cs) < 150:
            report["categories"][cat] = {"sets": len(cs), "verdict": "too few events"}
            print(cat, "too few events", len(cs), flush=True)
            continue
        report["categories"][cat] = run_category(cat, cs, args, contexts)
        r = report["categories"][cat]
        print(f"{cat} [{r['sets']}]: C {r['c_index']} {r['c_ci']} | placebo C {r['placebo_c']['placebo_c']} | "
              f"window top1 {r['window']['top1']} top3 {r['window']['top3']} | placebo window top3 "
              f"{r['placebo_window']['top3']} | mismatched {r['mismatched']['mean']} -> {r['verdict']}", flush=True)
    out = ROOT / "docs" / f"results_{datetime.now():%Y%m%d_%H%M}.json"
    out.write_text(json.dumps(report, indent=2))
    print("written", out)


if __name__ == "__main__":
    main()
