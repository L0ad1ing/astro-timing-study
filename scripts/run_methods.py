"""
scripts/run_methods.py — every method alone, their agreement, and consensus (docs/prereg_methods.md).
Both data halves (no fitting). Own death sampled to 5,000 events.
"""
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import methods as M                 # noqa: E402
from src import models as Mo                 # noqa: E402
from src import preprocessing as P           # noqa: E402
from scripts.run_rao import matched_or       # noqa: E402

CATS = ["Marriage", "Divorce", "Birth_Child", "Career_Peak", "Prize", "Job_Start", "Arrest", "Trial", "Illness",
        "Accident", "Death_of_relative", "Death"]


def label_of(s):
    if s["category"] != "Death_of_relative":
        return s["category"]
    low = s["label"].lower()
    for k, v in (("father", "Death of father"), ("mother", "Death of mother"), ("mate", "Death of mate")):
        if f"death of {k}" in low:
            return v
    return None


def main():
    rng = np.random.default_rng(3)
    sets = [s for s in P.case_control_sets(P.SOURCE_DB, halves=(0, 1), categories=CATS)
            if not math.isnan(s["natal"][P.NATAL.index("Ascendant")]) and label_of(s) in M.TARGETS]
    death = [i for i, s in enumerate(sets) if s["category"] == "Death"]
    drop = set(rng.choice(death, size=max(0, len(death) - 5000), replace=False).tolist())
    sets = [s for i, s in enumerate(sets) if i not in drop]
    print(len(sets), "sets", flush=True)
    persons = {}
    by_label: dict = {}
    for n, s in enumerate(sets):
        p = persons.setdefault(s["name"], M.Person(s))
        lab = label_of(s)
        k = len(s["jds"])
        X = np.full((k, len(M.METHODS)), np.nan)
        for j, jd in enumerate(s["jds"]):
            if not s["mask"][j]:
                continue
            r = M.evaluate(p, jd)
            for mi, m in enumerate(M.METHODS):
                v = M.flagged(r, m, lab)
                if v is not None:
                    X[j, mi] = float(v)
        d = by_label.setdefault(lab, {"X": [], "mask": [], "half": []})
        d["X"].append(X)
        d["mask"].append(s["mask"])
        d["half"].append(s["half"])
        if (n + 1) % 2000 == 0:
            print(f"  {n + 1}/{len(sets)}", flush=True)

    report = {"run_at": datetime.now().isoformat(), "prereg": "docs/prereg_methods.md @ 469eb54 + b213685",
              "methods": M.METHODS, "per_event": {}, "agreement": {}, "consensus": {}}
    pooled_ctrl = []
    for lab, d in by_label.items():
        X = np.array(d["X"])                       # (sets, dates, methods)
        mask = np.array(d["mask"])
        half = np.array(d["half"])
        cells = {}
        for mi, m in enumerate(M.METHODS):
            col = X[:, :, mi]
            if np.isnan(col[:, 0]).all():
                continue
            ok = ~np.isnan(col[:, 0])
            case, ctrl = col[ok, 0], np.nan_to_num(col[ok, 1:])
            cm = mask[ok, 1:] & ~np.isnan(col[ok, 1:])
            res = {"event_rate": round(float(case.mean()), 3),
                   "control_rate": round(float((ctrl * cm).sum() / cm.sum()), 3), **matched_or(case, ctrl, cm)}
            reps = []
            for h in (0, 1):
                sel = ok & (half == h)
                if sel.sum() > 30:
                    reps.append(matched_or(col[sel, 0], np.nan_to_num(col[sel, 1:]), mask[sel, 1:] & ~np.isnan(col[sel, 1:])))
            res["replicates_in_both_halves"] = bool(len(reps) == 2 and all(r.get("ci") and (r["ci"][0] > 1 or r["ci"][1] < 1) for r in reps)
                                                    and len({r["ci"][0] > 1 for r in reps}) == 1)
            cells[m] = res
        report["per_event"][lab] = {"events": int(len(X)), "methods": cells}
        # consensus: number of applicable methods flagging
        kcount = np.nansum(X, axis=2)
        valid = mask[:, 1:]
        def cidx(ev, ctr, vmask):
            w = ((ev[:, None] > ctr) & vmask).sum(1) + 0.5 * ((ev[:, None] == ctr) & vmask).sum(1)
            return w / vmask.sum(1)
        c = cidx(kcount[:, 0], kcount[:, 1:], valid)
        order = [4, 3, 2, 1] if lab == "Death" else [2, 1, 3, 4]
        kp = kcount[:, order]
        vp = mask[:, order][:, 1:] & mask[:, order][:, :1]
        keep = mask[:, order][:, 0] & (vp.sum(1) >= 2)
        cp = cidx(kp[keep, 0], kp[keep, 1:], vp[keep])
        report["consensus"][lab] = {"c": round(float(c.mean()), 4), "ci": Mo.bootstrap_ci(c),
                                    "placebo_c": round(float(cp.mean()), 4),
                                    "mean_methods_flagging_event": round(float(kcount[:, 0].mean()), 2),
                                    "mean_methods_flagging_controls": round(float(np.nanmean(np.where(valid, kcount[:, 1:], np.nan))), 2)}
        pooled_ctrl.append(np.where(valid[:, :, None], X[:, 1:, :], np.nan).reshape(-1, len(M.METHODS)))
    # agreement on control dates, pooled over event types (methods applicable everywhere)
    Z = np.concatenate(pooled_ctrl)
    for i, a in enumerate(M.METHODS):
        for j, b in enumerate(M.METHODS):
            if j <= i:
                continue
            ok = ~np.isnan(Z[:, i]) & ~np.isnan(Z[:, j])
            if ok.sum() > 500 and Z[ok, i].std() > 0 and Z[ok, j].std() > 0:
                report["agreement"][f"{a}|{b}"] = round(float(np.corrcoef(Z[ok, i], Z[ok, j])[0, 1]), 3)
    out = ROOT / "docs" / f"results_methods_{datetime.now():%Y%m%d_%H%M}.json"
    out.write_text(json.dumps(report, indent=1))
    print("written", out)
    for lab, d in report["consensus"].items():
        print(f"CONSENSUS {lab:16s} C {d['c']} {d['ci']} placebo {d['placebo_c']} | methods flagging: event {d['mean_methods_flagging_event']} vs controls {d['mean_methods_flagging_controls']}")
    sig = [(lab, m, r) for lab, d in report["per_event"].items() for m, r in d["methods"].items() if r.get("ci") and (r["ci"][0] > 1 or r["ci"][1] < 1)]
    print(f"\nNominal cells (CI excludes 1): {len(sig)} of {sum(len(d['methods']) for d in report['per_event'].values())}")
    for lab, m, r in sorted(sig, key=lambda x: -abs(math.log(x[2]['odds_ratio']))):
        print(f"  {lab:16s} {m:26s} OR {r['odds_ratio']} {r['ci']}  event {r['event_rate']} vs ctrl {r['control_rate']}  both halves: {r['replicates_in_both_halves']}")
    top = sorted(report["agreement"].items(), key=lambda kv: -abs(kv[1]))[:12]
    print("\nStrongest built-in agreement (phi on control dates):")
    for k, v in top:
        print(f"  {k:55s} {v}")


if __name__ == "__main__":
    main()
