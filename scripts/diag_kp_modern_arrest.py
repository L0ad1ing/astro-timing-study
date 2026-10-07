"""POST-HOC diagnostics for the confirmed KP-modern Arrest result (not pre-registered; they cannot change the verdict
of docs/prereg_kp_modern_arrest_confirm.md). Checks: shared event dates within and across halves, a bootstrap clustered
by event date, the result on half-1 events whose date does not occur in half 0, and which rules carry the score."""
import json, sys, collections
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import run_bphs_engine as RB
from src import models as Mo
from src.rules import engine as E


def main():
    src = ("KP modern",)
    rules = [r for r in E.load_rules()[0] if r["kind"] == "timing" and RB._src_ok(r, src)]
    rel = RB.relevance(rules)
    dirs = np.array([1 if r["predicts"]["direction"] == "+" else -1 for r in rules], np.float32)
    out = {}
    day = lambda jd: int(jd + 0.5)
    S0, F0 = RB.compute(0, 4, 0, src)
    S1, F1 = RB.compute(1, 4, 0, src)
    i0, i1 = RB.sets_of("Arrest", S0), RB.sets_of("Arrest", S1)
    d0 = collections.Counter(day(S0[i]["jds"][0]) for i in i0)
    d1 = collections.Counter(day(S1[i]["jds"][0]) for i in i1)
    out["half0_sets"], out["half1_sets"] = len(i0), len(i1)
    out["half1_sets_sharing_a_date_within_half1"] = sum(1 for i in i1 if d1[day(S1[i]["jds"][0])] > 1)
    out["half1_sets_whose_date_is_in_half0"] = sum(1 for i in i1 if day(S1[i]["jds"][0]) in d0)
    out["half1_distinct_dates"] = len(d1)


    def cs(sets, fired, ids):
        Sa, Ma, ka = RB.scores(ids, sets, fired, "Arrest", rel, "actual", "weighted", dirs)
        Sm, Mm, km = RB.scores(ids, sets, fired, "Arrest", rel, "mismatched", "weighted", dirs)
        k = ka & km
        return Mo.per_set_c(Sa[k], Ma[k]), Mo.per_set_c(Sm[k], Mm[k]), np.array(ids)[k]


    ca, cm, kept = cs(S1, F1, i1)
    dates = np.array([day(S1[i]["jds"][0]) for i in kept])
    rng = np.random.default_rng(1)
    ud = np.unique(dates)
    groups = {u: np.where(dates == u)[0] for u in ud}
    bs_d, bs_c = [], []
    for _ in range(2000):
        pick = np.concatenate([groups[u] for u in rng.choice(ud, len(ud))])
        bs_d.append((ca[pick] - cm[pick]).mean()); bs_c.append(ca[pick].mean())
    out["half1_date_clustered"] = {"c_actual": round(float(ca.mean()), 4), "c_ci": [round(float(np.percentile(bs_c, q)), 4) for q in (2.5, 97.5)],
                                   "dC": round(float((ca - cm).mean()), 4), "dC_ci": [round(float(np.percentile(bs_d, q)), 4) for q in (2.5, 97.5)]}
    # one set per date (the first), and dates unseen in half 0
    first = {}
    for j, u in enumerate(dates):
        first.setdefault(u, j)
    one = np.array(sorted(first.values()))
    unseen = np.array([j for j in one if dates[j] not in d0])
    for name, idx in (("half1_one_set_per_date", one), ("half1_one_per_date_unseen_in_half0", unseen)):
        a, m = ca[idx], cm[idx]
        bd = [(a[p] - m[p]).mean() for p in (rng.integers(0, len(idx), len(idx)) for _ in range(2000))]
        bc = [a[p].mean() for p in (rng.integers(0, len(idx), len(idx)) for _ in range(2000))]
        out[name] = {"n": int(len(idx)), "c_actual": round(float(a.mean()), 4), "c_ci": [round(float(np.percentile(bc, q)), 4) for q in (2.5, 97.5)],
                     "dC": round(float((a - m).mean()), 4), "dC_ci": [round(float(np.percentile(bd, q)), 4) for q in (2.5, 97.5)]}
    # rules relevant to Arrest and how often each fires on event vs control dates (actual chart), half 1
    idx_r = [j for j, r in enumerate(rules) if r["predicts"].get("event") == "Arrest"]
    rows = []
    for j in idx_r:
        ev, ct = [], []
        for i in kept:
            f = F1[i]["actual"]
            if not f or f[0] is None:
                continue
            bits = [np.unpackbits(x[2])[:len(rules)][j] if x is not None else 0 for x in f]
            ev.append(bits[0]); ct.extend(bits[1:])
        rows.append({"rule": rules[j]["id"], "text": rules[j]["text"][:110], "event_rate": round(float(np.mean(ev)), 3), "control_rate": round(float(np.mean(ct)), 3)})
    out["arrest_rules_half1"] = rows
    p = ROOT / "docs" / "results_kp_modern_arrest_diagnostics.json"
    p.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
