"""
scripts/run_discovery_v2.py — mine geometric rules on training months, test once on held-out months
(docs/prereg_discovery_v2.md). Writes docs/results_discovery_v2_<ts>.json and src/discovery_v2/discovered_rules.json.

Usage: python -m scripts.run_discovery_v2 [--only Accident]
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_rao import genders                      # noqa: E402
from src import harmonic_features as H                   # noqa: E402
from src import models as Mo                             # noqa: E402
from src import preprocessing as P                       # noqa: E402
from src.discovery_v2 import leak_free_splitter as S     # noqa: E402
from src.discovery_v2 import matched_controls as MC      # noqa: E402
from src.discovery_v2 import rule_evaluator as E         # noqa: E402
from src.discovery_v2 import rule_miner as RM            # noqa: E402

CATS = ["Marriage", "Death_of_relative", "Prize", "Arrest", "Career_Peak", "Job_Start", "Divorce", "Job_End", "Trial",
        "Illness", "Accident"]
TOP_K, ALPHA = 20, 0.01
OUT_RULES = ROOT / "src" / "discovery_v2" / "discovered_rules.json"


def main() -> None:
    cats = [sys.argv[sys.argv.index("--only") + 1]] if "--only" in sys.argv else CATS
    sets = [s for s in MC.matched_sets((0, 1), cats) if not math.isnan(s["natal"][P.NATAL.index("Ascendant")])]
    sex = genders(sorted({s["name"] for s in sets}))
    for s in sets:
        s["sex"] = sex.get(s["name"])
    hf, demo = H.HarmonicFeaturizer(), E.Demographic()
    cols = hf.default_columns()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    report = {"run_at": datetime.now(timezone.utc).isoformat(), "prereg": "docs/prereg_discovery_v2.md", "code_commit": commit,
              "test_months": S.TEST_MONTHS, "categories": {}}
    out = ROOT / "docs" / f"results_discovery_v2_{datetime.now():%Y%m%d_%H%M}.json"
    tested = []
    for cat in cats:
        cs = [s for s in sets if s["category"] == cat]
        tr_i, te_i, info = S.split(cs)
        aud = S.audit(cs, tr_i, te_i)
        assert not any(aud.values()), f"{cat}: leak in split {aud}"
        r = {"sets": len(cs), "train_sets": int(len(tr_i)), "test_sets": int(len(te_i)), "dropped": info, "audit": aud}
        if len(tr_i) < 150 or len(te_i) < 75:
            r["verdict"] = "too few sets"
            report["categories"][cat] = r
            print(cat, "too few sets", len(tr_i), len(te_i), flush=True)
            continue
        tr, te = [cs[i] for i in tr_i], [cs[i] for i in te_i]
        # demographic baseline: out-of-fold on training (for selection), fit on training -> test
        Xb, Mb = Mo.matrix(tr, featurizer=demo)
        oof_b, _ = Mo.cross_validated_scores(Xb, Mb, np.array([s["fold"] for s in tr]), demo.default_columns())
        base_model = Mo.fit(Xb, Mb, demo.default_columns())
        # mine on training only
        X, M = Mo.matrix(tr, featurizer=hf)
        cands = RM.univariate_rules(X, M, cols) + RM.tree_rules(X, M, cols)
        chosen = RM.select(cands, X, M, oof_b, k=TOP_K)
        del X
        # holdout, once
        Xt, Mt = Mo.matrix(te, featurizer=hf)
        Xbt, Mbt = Mo.matrix(te, featurizer=demo)
        base_t = np.where(Mt, Mo.score(base_model, Xbt, Mbt, demo.default_columns()), 0.0)
        r["candidates_scored"] = len(cands)
        r["baseline_holdout_c"] = round(E.c_index(np.where(Mt, base_t, -np.inf), Mt), 4)
        rules = []
        for c in chosen:
            ex = E.exposure(Xt, c["rule"])
            fit = E.clogit(np.stack([ex.astype(float), base_t], axis=2), Mt)
            mh = E.mh_vector(ex[:, :, None], Mt)
            d = {"text": E.describe(c["rule"], hf.names),
                 "conditions": [[hf.names[f], op, round(t, 6)] for f, op, t in c["rule"]],
                 "direction": "risk" if c["train_beta"] > 0 else "protective", **{k: v for k, v in c.items() if k != "rule"},
                 "test_beta": round(float(fit["beta"][0]), 4), "test_z": round(float(fit["z"][0]), 3),
                 "test_p": float(fit["p"][0]),
                 "test_odds_ratio": None if not np.isfinite(mh["log_or"][0]) else round(float(np.exp(mh["log_or"][0])), 3),
                 "test_rate_event": round(float(ex[:, 0].mean()), 4),
                 "test_rate_control": round(float((ex[:, 1:] & Mt[:, 1:]).sum() / Mt[:, 1:].sum()), 4),
                 "same_sign": bool(np.sign(fit["beta"][0]) == np.sign(c["train_beta"]))}
            rules.append(d)
            tested.append((cat, d))
        r["rules"] = rules
        report["categories"][cat] = r
        out.write_text(json.dumps(report, indent=2, default=float))
        best = min(rules, key=lambda d: d["test_p"])
        print(f"{cat:18s} train {len(tr):5d} test {len(te):5d} | candidates {len(cands)} | baseline holdout C "
              f"{r['baseline_holdout_c']} | best holdout rule p {best['test_p']:.3g} (same sign {best['same_sign']}): "
              f"{best['text'][:90]}", flush=True)
        del Xt
    n = len(tested)
    q = E.bh(np.array([d["test_p"] for _, d in tested])) if n else np.array([])
    survivors = []
    for (cat, d), qq in zip(tested, q):
        d["bh_q"] = round(float(qq), 4)
        d["survives"] = bool(d["same_sign"] and d["test_p"] < ALPHA / n)
        if d["survives"]:
            survivors.append({"event_type": cat, **d})
    report["n_rules_tested"] = n
    report["bonferroni_threshold"] = ALPHA / n if n else None
    report["survivors"] = len(survivors)
    out.write_text(json.dumps(report, indent=2, default=float))
    OUT_RULES.write_text(json.dumps({"generated_at": report["run_at"], "prereg": report["prereg"], "code_commit": commit,
                                     "results": out.name, "n_rules_tested": n,
                                     "rule": f"same sign as training and two-sided p < {ALPHA}/{n}, adjusted for age, "
                                             "calendar year and sex, on held-out months",
                                     "rules": survivors}, indent=2, default=float))
    print(f"\n{n} rules tested on held-out months; Bonferroni threshold {report['bonferroni_threshold']}; "
          f"survivors: {len(survivors)}; BH q < 0.05: {int((q < 0.05).sum()) if n else 0}")
    print("written", out, "and", OUT_RULES)


if __name__ == "__main__":
    main()
