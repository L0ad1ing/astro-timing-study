"""
scripts/harmonic_date_leak_check.py — POST-HOC (not pre-registered) check of the harmonic "candidates".

docs/results_harmonic_20261001_1108.json gave five CANDIDATES, but the sky-only block (identical for everyone on a
date) matched the full model, and mismatched charts barely lowered the score. Suspected cause: many people share an
exact event date (same awards night, co-defendants, both spouses, siblings), and person-grouped folds put them in
different folds, so the model can recognise a date's sky from someone else's event.

1. Re-run AGE / HARMONIC / SKY with folds grouped by person AND by event calendar month (union-find over both),
   so no date - or any date within the same month - is shared between training and validation.
2. Run the pre-registered half-1 confirmation of the frozen lock-box models, split into events whose calendar month
   occurs among that event type's training-half events ("seen") and those whose month does not ("unseen").
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_harmonic_pipeline as R  # noqa: E402
from src import harmonic_features as H          # noqa: E402
from src import models as Mo                    # noqa: E402
from src.context_builder import _date           # noqa: E402


def month(jd: float) -> str:
    return _date(jd)[:7]


def grouped_folds(cs: list[dict], k: int = 5) -> np.ndarray:
    parent = list(range(len(cs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    first: dict = {}
    for i, s in enumerate(cs):
        for key in (("p", s["name"]), ("m", month(s["jds"][0]))):
            if key in first:
                parent[find(i)] = find(first[key])
            else:
                first[key] = i
    comps = defaultdict(list)
    for i in range(len(cs)):
        comps[find(i)].append(i)
    size, folds = [0] * k, np.zeros(len(cs), int)
    for members in sorted(comps.values(), key=len, reverse=True):
        f = int(np.argmin(size))
        folds[members] = f
        size[f] += len(members)
    return folds


def cv_c(X, M, folds, cols) -> np.ndarray:
    oof, _ = Mo.cross_validated_scores(X, M, folds, cols)
    return Mo.per_set_c(oof, M)


def main() -> None:
    hf, ab = H.HarmonicFeaturizer(), H.AgeBaseline()
    cols, sky = hf.default_columns(), np.intersect1d(hf.groups()["sky"], hf.default_columns())
    train = R.sets_for((0,))
    report = {"run_at": datetime.now(timezone.utc).isoformat(), "post_hoc": True,
              "reason": "sky-only block matched the full model; suspected shared-date leakage", "grouped_cv": {},
              "confirmation_half1": {}}
    out = ROOT / "docs" / f"results_harmonic_leakcheck_{datetime.now():%Y%m%d_%H%M}.json"
    for cat in R.CATS:
        cs = [s for s in train if s["category"] == cat]
        folds = grouped_folds(cs)
        Xa, Ma = Mo.matrix(cs, featurizer=ab)
        X, M = Mo.matrix(cs, featurizer=hf)
        ca, ch, cs_ = cv_c(Xa, Ma, folds, ab.default_columns()), cv_c(X, M, folds, cols), cv_c(X, M, folds, sky)
        r = {"sets": len(cs), "fold_sizes": np.bincount(folds).tolist(), "age_c": round(float(ca.mean()), 4),
             "harmonic_c": round(float(ch.mean()), 4), "sky_c": round(float(cs_.mean()), 4),
             "delta": R.paired_delta(ca, ch, len(R.CATS))}
        report["grouped_cv"][cat] = r
        out.write_text(json.dumps(report, indent=2))
        print(f"GROUPED {cat:18s} n={len(cs):5d} AGE {r['age_c']} HARMONIC {r['harmonic_c']} SKY {r['sky_c']} "
              f"dC {r['delta']['delta_c']} bonf {r['delta']['ci_bonferroni']}", flush=True)
        del X, M

    import lightgbm as lgb
    man = json.loads((R.LOCK / "manifest.json").read_text())
    half1 = R.sets_for((1,))
    for cat, e in man["models"].items():
        f = R.LOCK / e["file"]
        assert hashlib.sha256(f.read_bytes()).hexdigest() == e["sha256"], f"{cat}: model file changed"
        model = lgb.Booster(model_file=str(f))
        seen_months = {month(s["jds"][0]) for s in train if s["category"] == cat}
        cs = [s for s in half1 if s["category"] == cat]
        X, M = Mo.matrix(cs, featurizer=hf)
        ch = Mo.per_set_c(Mo.score(model, X, M, cols), M)
        Xa, Ma = Mo.matrix(cs, featurizer=ab)
        ca = cv_c(Xa, Ma, np.array([s["fold"] for s in cs]), ab.default_columns())
        seen = np.array([month(s["jds"][0]) in seen_months for s in cs])
        r = {"sets": len(cs), "all": R.paired_delta(ca, ch, 1), "harmonic_c_all": round(float(ch.mean()), 4),
             "age_c_all": round(float(ca.mean()), 4)}
        for label, sel in (("seen_month", seen), ("unseen_month", ~seen)):
            r[label] = {"sets": int(sel.sum()), "harmonic_c": round(float(ch[sel].mean()), 4),
                        "age_c": round(float(ca[sel].mean()), 4), "delta": R.paired_delta(ca[sel], ch[sel], 1)}
        report["confirmation_half1"][cat] = r
        out.write_text(json.dumps(report, indent=2))
        print(f"CONFIRM {cat:18s} all dC {r['all']['delta_c']} {r['all']['ci95']} | seen-month n={r['seen_month']['sets']} "
              f"dC {r['seen_month']['delta']['delta_c']} {r['seen_month']['delta']['ci95']} | unseen-month "
              f"n={r['unseen_month']['sets']} dC {r['unseen_month']['delta']['delta_c']} {r['unseen_month']['delta']['ci95']}",
              flush=True)
    print("written", out)


if __name__ == "__main__":
    main()
