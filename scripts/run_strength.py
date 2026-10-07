"""
scripts/run_strength.py — do planetary strength and dignity features add timing signal? (docs/prereg_strength.md)

Per event type, training half, folds grouped by person AND event month:
  BASE = 706 features, STRENGTH = 706 + 613 strength/dignity features, DEMO = age + calendar year + sex.
  dC(STRENGTH - BASE) with Bonferroni over 11 types; dC(STRENGTH - DEMO); placebo C; mismatched charts
  (per-set dC on the same donors, so the strength gain itself is tested). Candidates are confirmed once on half 1
  (event months unseen in half 0; Olympic-Games prize events removed).

Usage: python -m scripts.run_strength
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.discovery_v2_parity_check import games                 # noqa: E402
from scripts.harmonic_date_leak_check import grouped_folds, month    # noqa: E402
from scripts.run_harmonic_pipeline import paired_delta               # noqa: E402
from scripts.run_rao import genders                                  # noqa: E402
from src import models as Mo                                         # noqa: E402
from src import preprocessing as P                                   # noqa: E402
from src import strength as S                                        # noqa: E402
from src import validation as V                                      # noqa: E402
from src.discovery_v2.rule_evaluator import Demographic              # noqa: E402

CATS = ["Marriage", "Death_of_relative", "Prize", "Arrest", "Career_Peak", "Job_Start", "Divorce", "Job_End", "Trial",
        "Illness", "Accident"]
BASE_COLS, STR_COLS = Mo.DEFAULT_COLUMNS, S.STRENGTH_COLUMNS


def load(halves) -> list[dict]:
    sets = [s for s in P.case_control_sets(P.SOURCE_DB, halves=halves, categories=CATS)
            if not math.isnan(s["natal"][P.NATAL.index("Ascendant")])]
    sex = genders(sorted({s["name"] for s in sets}))
    for s in sets:
        s["sex"] = sex.get(s["name"])
    return sets


def per_set_scores(model, feats: np.ndarray, mask: np.ndarray, cols) -> np.ndarray:
    sc = np.full(len(mask), -np.inf)
    sc[mask] = Mo.score_dates(model, feats[mask], cols)
    return sc


def mismatched(models_b, models_s, cs, folds, sf, rng, n=1500) -> dict:
    """Strength + base features recomputed from a random other person's natal chart (own birth moment and place
    kept); returns the per-set STRENGTH - BASE C difference on those donor charts."""
    idx = rng.choice(len(cs), size=min(n, len(cs)), replace=False)
    fb, fs = dict(zip(np.unique(folds), models_b)), dict(zip(np.unique(folds), models_s))
    db, ds = [], []
    for i in idx:
        s = cs[i]
        donor = cs[rng.integers(0, len(cs))]
        ctx = sf.context({**s, "natal": donor["natal"], "name": donor["name"]})
        feats = np.array([sf.features(ctx, jd) for jd in s["jds"]])
        m = np.array(s["mask"])
        db.append(Mo.per_set_c(per_set_scores(fb[folds[i]], feats, m, BASE_COLS)[None, :], m[None, :])[0])
        ds.append(Mo.per_set_c(per_set_scores(fs[folds[i]], feats, m, STR_COLS)[None, :], m[None, :])[0])
    return {"sets": int(len(idx)), "base_c": round(float(np.mean(db)), 4), "strength_c": round(float(np.mean(ds)), 4),
            "delta": paired_delta(np.array(db), np.array(ds), 1)}


def main() -> None:
    sf, demo = S.StrengthFeaturizer(), Demographic()
    train = load((0,))
    report = {"run_at": datetime.now(timezone.utc).isoformat(), "prereg": "docs/prereg_strength.md",
              "n_strength_features": S.N_STRENGTH, "categories": {}, "confirmation": {}}
    out = ROOT / "docs" / f"results_strength_{datetime.now():%Y%m%d_%H%M}.json"
    finals = {}
    for cat in CATS:
        cs = [s for s in train if s["category"] == cat]
        folds = grouped_folds(cs)
        X, M = Mo.matrix(cs, featurizer=sf)
        oof_b, models_b = Mo.cross_validated_scores(X, M, folds, BASE_COLS)
        oof_s, models_s = Mo.cross_validated_scores(X, M, folds, STR_COLS)
        Xd, Md = Mo.matrix(cs, featurizer=demo)
        oof_d, _ = Mo.cross_validated_scores(Xd, Md, folds, demo.default_columns())
        cb, cst, cd = Mo.per_set_c(oof_b, M), Mo.per_set_c(oof_s, M), Mo.per_set_c(oof_d, Md)
        r = {"sets": len(cs), "base_c": round(float(cb.mean()), 4), "strength_c": round(float(cst.mean()), 4),
             "demo_c": round(float(cd.mean()), 4),
             "delta_vs_base": paired_delta(cb, cst, len(CATS)), "delta_vs_demo": paired_delta(cd, cst, 1),
             "placebo_c": V.placebo_c_index(models_s, X, M, folds, cat, STR_COLS)}
        r["mismatched"] = mismatched(models_b, models_s, cs, folds, sf, np.random.default_rng(5))
        checks = {"beats_base_bonferroni": r["delta_vs_base"]["ci_bonferroni"][0] > 0,
                  "beats_demo": r["delta_vs_demo"]["ci95"][0] > 0,
                  "placebo_ok": r["placebo_c"]["ci"][0] <= 0.5,
                  "gain_lost_on_mismatched_charts": r["mismatched"]["delta"]["ci95"][0] <= 0}
        r["checks"] = checks
        r["verdict"] = "CANDIDATE" if all(checks.values()) else \
            "no gain over the 706-feature model" if not checks["beats_base_bonferroni"] else \
            "fails: " + ", ".join(k for k, v in checks.items() if not v)
        if r["verdict"] == "CANDIDATE":
            finals[cat] = (Mo.fit(X, M, BASE_COLS), Mo.fit(X, M, STR_COLS), {month(s["jds"][0]) for s in cs})
        report["categories"][cat] = r
        out.write_text(json.dumps(report, indent=2))
        d = r["delta_vs_base"]
        print(f"{cat:18s} n={len(cs):5d}  BASE {r['base_c']}  STRENGTH {r['strength_c']}  DEMO {r['demo_c']}  "
              f"dC {d['delta_c']:+.4f} bonf {d['ci_bonferroni']}  placebo {r['placebo_c']['placebo_c']}  "
              f"mismatched dC {r['mismatched']['delta']['delta_c']:+.4f}  -> {r['verdict']}", flush=True)
        del X, M

    if finals:
        test = load((1,))
        for cat, (mb, ms, seen) in finals.items():
            cs = [s for s in test if s["category"] == cat and month(s["jds"][0]) not in seen
                  and not (cat == "Prize" and games(s["jds"][0]))]
            X, M = Mo.matrix(cs, featurizer=sf)
            cb = Mo.per_set_c(Mo.score(mb, X, M, BASE_COLS), M)
            cst = Mo.per_set_c(Mo.score(ms, X, M, STR_COLS), M)
            r = {"sets": len(cs), "base_c": round(float(cb.mean()), 4), "strength_c": round(float(cst.mean()), 4),
                 "delta": paired_delta(cb, cst, 1)}
            r["confirmed"] = r["delta"]["ci95"][0] > 0
            report["confirmation"][cat] = r
            out.write_text(json.dumps(report, indent=2))
            print(f"CONFIRM {cat}: n={len(cs)} dC {r['delta']['delta_c']:+.4f} {r['delta']['ci95']} -> "
                  f"{'CONFIRMED' if r['confirmed'] else 'not confirmed'}", flush=True)
    print("written", out)


if __name__ == "__main__":
    main()
