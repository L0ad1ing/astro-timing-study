"""
scripts/run_harmonic_pipeline.py — continuous harmonic features vs an age-only baseline (docs/prereg_harmonic.md).

Per event type, training half only: AGE and HARMONIC models (5-fold person-grouped CV, out-of-fold scores),
paired ΔC with Bonferroni interval, ablations (SKY / NATAL / KIN), placebo C, window and placebo window tests,
mismatched charts for the NATAL model, and SHAP (LightGBM TreeSHAP) per fold model with cross-fold stability.
SHAP is computed here rather than in a separate script so it uses exactly the fold models whose C is reported.
Candidates are frozen in lockbox/harmonic/ for a single confirmation run on half 1 (--confirm).

Usage: python -m scripts.run_harmonic_pipeline [--resume docs/results_harmonic_<ts>.json] [--confirm]
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import harmonic_features as H          # noqa: E402
from src import models as Mo                    # noqa: E402
from src import preprocessing as P              # noqa: E402
from src import validation as V                 # noqa: E402

CATS = ["Death", "Marriage", "Death_of_relative", "Prize", "Arrest", "Career_Peak", "Job_Start", "Divorce", "Job_End",
        "Trial", "Illness", "Accident"]
DEATH_SAMPLE = 3000
BOOT = 2000
LOCK = ROOT / "lockbox" / "harmonic"


def paired_delta(ca: np.ndarray, cb: np.ndarray, n_tests: int, seed: int = 0) -> dict:
    """ΔC = mean(cb - ca) over sets, with 95% and Bonferroni percentile intervals."""
    d = cb - ca
    rng = np.random.default_rng(seed)
    boot = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(BOOT)])
    a = 0.05 / n_tests * 100 / 2
    return {"delta_c": round(float(d.mean()), 4),
            "ci95": [round(float(np.percentile(boot, 2.5)), 4), round(float(np.percentile(boot, 97.5)), 4)],
            "ci_bonferroni": [round(float(np.percentile(boot, a)), 4), round(float(np.percentile(boot, 100 - a)), 4)]}


def shap_folds(models, X, M, folds, cols, names) -> dict:
    tops = []
    for k, m in zip(np.unique(folds), models):
        va = folds == k
        tops.append(H.shap_importance(m, X[va], M[va], cols, names, top=20))
    count = Counter(n for t in tops for n, _ in t)
    return {"per_fold_top20": tops, "stable_in_4_of_5_folds": sorted(n for n, c in count.items() if c >= 4)}


def sets_for(halves) -> list[dict]:
    sets = [s for s in P.case_control_sets(P.SOURCE_DB, halves=halves, categories=CATS)
            if not math.isnan(s["natal"][P.NATAL.index("Ascendant")])]
    rng = np.random.default_rng(1)
    death = [i for i, s in enumerate(sets) if s["category"] == "Death"]
    drop = set(rng.choice(death, size=max(0, len(death) - DEATH_SAMPLE), replace=False).tolist())
    return [s for i, s in enumerate(sets) if i not in drop]


def freeze(model, cat: str, hf, cols, extra: dict) -> dict:
    LOCK.mkdir(parents=True, exist_ok=True)
    f = LOCK / f"{cat}.lgb.txt"
    model.save_model(str(f))
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    entry = {"file": f.name, "sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "featurizer": hf.name,
             "columns_hash": hashlib.sha256("\n".join(hf.names[i] for i in cols).encode()).hexdigest()[:16],
             "params": Mo.PARAMS, "rounds": Mo.ROUNDS, "code_commit": commit,
             "frozen_at": datetime.now(timezone.utc).isoformat(), **extra}
    mp = LOCK / "manifest.json"
    man = json.loads(mp.read_text()) if mp.exists() else {"rule": "Evaluate once on half 1. Do not retrain.", "models": {}}
    man["models"][cat] = entry
    mp.write_text(json.dumps(man, indent=2))
    return entry


def run_category(cat: str, cs: list[dict], n_tests: int) -> tuple[dict, object]:
    hf, ab = H.HarmonicFeaturizer(), H.AgeBaseline()
    folds = np.array([s["fold"] for s in cs])
    Xa, Ma = Mo.matrix(cs, featurizer=ab)
    oof_a, _ = Mo.cross_validated_scores(Xa, Ma, folds, ab.default_columns())
    ca = Mo.per_set_c(oof_a, Ma)
    X, M = Mo.matrix(cs, featurizer=hf)
    cols = hf.default_columns()
    oof_h, models = Mo.cross_validated_scores(X, M, folds, cols)
    ch = Mo.per_set_c(oof_h, M)
    res = {"sets": len(cs),
           "age_c": {"c": round(float(ca.mean()), 4), "ci": Mo.bootstrap_ci(ca)},
           "harmonic_c": {"c": round(float(ch.mean()), 4), "ci": Mo.bootstrap_ci(ch)},
           "delta": paired_delta(ca, ch, n_tests)}
    groups, ablations, natal_models = hf.groups(), {}, None
    for g in ("sky", "natal", "kin"):
        gc = np.intersect1d(groups[g], cols)
        oof_g, mg = Mo.cross_validated_scores(X, M, folds, gc)
        cg = Mo.per_set_c(oof_g, M)
        ablations[g] = {"c": round(float(cg.mean()), 4), "ci": Mo.bootstrap_ci(cg),
                        "delta_vs_age": paired_delta(ca, cg, n_tests)["delta_c"]}
        if g == "natal":
            natal_models, natal_cols = mg, gc
    res["ablations"] = ablations
    res["placebo_c"] = V.placebo_c_index(models, X, M, folds, cat, cols)
    res["window"] = V.window_test(models, cs, folds, seed=11, columns=cols, contexts={}, featurizer=hf)
    res["placebo_window"] = V.placebo_window_test(models, cs, folds, seed=11, columns=cols, contexts={}, featurizer=hf)
    rng = np.random.default_rng(5)
    idx = rng.choice(len(cs), size=min(1500, len(cs)), replace=False)
    res["mismatched_natal"] = V.mismatched_chart_c(natal_models, [cs[i] for i in idx], folds[idx], rng, natal_cols,
                                                   featurizer=hf)
    res["shap"] = shap_folds(models, X, M, folds, cols, hf.names)
    best = max(ablations, key=lambda g: ablations[g]["c"])
    pc = res["placebo_c"]
    checks = {"delta_bonferroni_above_0": res["delta"]["ci_bonferroni"][0] > 0,
              "placebo_c_ok": pc["ci"][0] <= 0.5,
              "placebo_window_passed": res["placebo_window"]["passed"],
              "mismatched_ok": best != "natal" or res["mismatched_natal"]["mean"] <= 0.52}
    res["checks"], res["best_ablation"] = checks, best
    res["verdict"] = "CANDIDATE" if all(checks.values()) else "no gain over age" if not checks["delta_bonferroni_above_0"] \
        else "fails: " + ", ".join(k for k, v in checks.items() if not v)
    final = Mo.fit(X, M, cols) if res["verdict"] == "CANDIDATE" else None
    return res, final


def confirm() -> None:
    man = json.loads((LOCK / "manifest.json").read_text())
    hf, ab = H.HarmonicFeaturizer(), H.AgeBaseline()
    cols = hf.default_columns()
    sets = sets_for((1,))
    report = {"run_at": datetime.now(timezone.utc).isoformat(), "half": "confirmation (1)", "categories": {}}
    import lightgbm as lgb
    for cat, e in man["models"].items():
        f = LOCK / e["file"]
        assert hashlib.sha256(f.read_bytes()).hexdigest() == e["sha256"], f"{cat}: model file changed"
        model = lgb.Booster(model_file=str(f))
        cs = [s for s in sets if s["category"] == cat]
        X, M = Mo.matrix(cs, featurizer=hf)
        ch = Mo.per_set_c(Mo.score(model, X, M, cols), M)
        Xa, Ma = Mo.matrix(cs, featurizer=ab)
        folds = np.array([s["fold"] for s in cs])
        oof_a, _ = Mo.cross_validated_scores(Xa, Ma, folds, ab.default_columns())
        ca = Mo.per_set_c(oof_a, Ma)
        report["categories"][cat] = {"sets": len(cs), "harmonic_c": round(float(ch.mean()), 4),
                                     "age_c": round(float(ca.mean()), 4), "delta": paired_delta(ca, ch, 1)}
        print(cat, report["categories"][cat], flush=True)
    out = ROOT / "docs" / f"results_harmonic_confirm_{datetime.now():%Y%m%d_%H%M}.json"
    out.write_text(json.dumps(report, indent=2))
    print("written", out)


def main() -> None:
    if "--confirm" in sys.argv:
        return confirm()
    sets = sets_for((0,))
    report = {"run_at": datetime.now(timezone.utc).isoformat(), "prereg": "docs/prereg_harmonic.md", "half": "training (0)",
              "featurizer": H.HarmonicFeaturizer().name, "n_columns": int(len(H.HarmonicFeaturizer().default_columns())),
              "categories": {}}
    out = ROOT / "docs" / f"results_harmonic_{datetime.now():%Y%m%d_%H%M}.json"
    if "--resume" in sys.argv:                      # continue an interrupted run in its own results file
        out = Path(sys.argv[sys.argv.index("--resume") + 1])
        report = json.loads(out.read_text())
        report.setdefault("resumed_at", []).append(datetime.now(timezone.utc).isoformat())
    for cat in CATS:
        if cat in report["categories"]:
            continue
        cs = [s for s in sets if s["category"] == cat]
        res, final = run_category(cat, cs, len(CATS))
        if final is not None:
            res["lockbox"] = freeze(final, cat, H.HarmonicFeaturizer(), H.HarmonicFeaturizer().default_columns(),
                                    {"training_sets": len(cs), "cv_delta": res["delta"]})
        report["categories"][cat] = res
        out.write_text(json.dumps(report, indent=2))
        d, ab = res["delta"], res["ablations"]
        print(f"{cat} [{res['sets']}]: AGE {res['age_c']['c']} | HARMONIC {res['harmonic_c']['c']} | dC {d['delta_c']} "
              f"bonf {d['ci_bonferroni']} | sky {ab['sky']['c']} natal {ab['natal']['c']} kin {ab['kin']['c']} | "
              f"placebo C {res['placebo_c']['placebo_c']} | window top3 {res['window']['top3']} placebo-window "
              f"{'pass' if res['placebo_window']['passed'] else 'FAIL'} | mismatched natal {res['mismatched_natal']['mean']} "
              f"| stable SHAP {len(res['shap']['stable_in_4_of_5_folds'])} -> {res['verdict']}", flush=True)
    print("written", out)


if __name__ == "__main__":
    main()
