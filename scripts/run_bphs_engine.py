"""
scripts/run_bphs_engine.py — the BPHS rule engine on every checkable event type (docs/prereg_bphs_engine.md).

Phase 1 (parallel): for every case-control set, run the reader on each date with the person's chart and with a
mismatched chart (random other person's natal longitudes, own birth moment kept); store the fired timing rules with
their final signed weights. Cached in data/cache/bphs_engine_half<h>.pkl.
Phase 2: engine-score C per type vs mismatched (primary), placebo, unweighted / direct-only, per-rule FDR,
learned combination vs DEMO; confirmation on half 1 for any PASS.

Usage: python -m scripts.run_bphs_engine [--workers 14]
"""
from __future__ import annotations

import argparse
import os
import json
import math
import pickle
import hashlib
import re
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.discovery_v2_parity_check import games                 # noqa: E402
from scripts.harmonic_date_leak_check import grouped_folds           # noqa: E402
from scripts.run_harmonic_pipeline import paired_delta               # noqa: E402
from scripts.run_rao import genders                                  # noqa: E402
from src import models as Mo                                         # noqa: E402
from src import preprocessing as P                                   # noqa: E402
from src.discovery_v2.rule_evaluator import Demographic              # noqa: E402
from src.rules import engine as E                                    # noqa: E402

BASE_CATS = ["Death", "Marriage", "Divorce", "Birth_Child", "Career_Peak", "Prize", "Job_Start", "Job_End", "Arrest",
             "Trial", "Illness", "Accident", "Relationship_Begin", "Relationship_End", "Death_of_relative"]
SUBTYPES = {"Death of father": re.compile(r"death of father|(his|her) father died", re.I),
            "Death of mother": re.compile(r"death of mother|(his|her) mother died", re.I),
            "Death of mate": re.compile(r"death of mate|(his|her) (wife|husband) died", re.I)}
TYPES = BASE_CATS + list(SUBTYPES)
POSITIVE = set(E.POSITIVE_EVENTS)

# ── phase 1 ────────────────────────────────────────────────────────────────────────────────────────────────────
_R = None


def _init(sources=("BPHS",)):
    global _R
    from src.rules.reader import Reader
    _R = Reader()
    _R.rules = [r for r in _R.rules if r["kind"] == "timing" and _src_ok(r, sources)]
    _R.idx = {r["id"]: i for i, r in enumerate(_R.rules)}
    _R.rel = relevance(_R.rules)


def _set_mask(s):
    """Rules that can enter any score for this set (its type, its relative subset, the pooled rules)."""
    t = s["sub"] if s["category"] == "Death_of_relative" and s["sub"] else s["category"]
    d, p = rule_mask(s["category"], s, _R.rel)
    d2, p2 = _R.rel[t]
    return d | p | d2 | p2


def _fire(chart, jd, keep):
    """Compact record of one date: (indices and final signed weights of the fired rules this set's scores use,
    packed bitmap of every fired timing rule for the per-rule and learned analyses)."""
    rd = _R.read(chart, jd, kinds=("timing",))
    idx = np.array([_R.idx[f.rule["id"]] for f in rd.fired], np.int16)
    w = np.array([(1 if f.direction == "+" else -1) * f.weight for f in rd.fired], np.float32)
    bits = np.zeros(len(_R.rules), bool)
    bits[idx] = True
    sel = keep[idx]
    return idx[sel], w[sel], np.packbits(bits)


def _work(job):
    s, donor = job
    out = {"actual": [], "mismatched": []}
    keep = _set_mask(s)
    # the mismatched chart takes the donor's natal longitudes and, for KP, the donor's birth moment and place for the
    # cusps and KP positions (kp_birth); the person's own birth moment still drives the dasas and the dates
    for key, extra in (("actual", {}), ("mismatched", {"natal": donor["natal"],
                                                        "kp_birth": (donor["birth_jd"], donor["lat"], donor["lon"])})):
        try:
            c = E.Chart({**s, **extra})
        except Exception:
            out[key] = [None] * len(s["jds"])
            continue
        for jd, ok in zip(s["jds"], s["mask"]):
            out[key].append(_fire(c, jd, keep) if ok else None)
    return out


def _src_ok(r: dict, sources) -> bool:
    """The rule's book: 'BPHS' covers BPHS rules and notes quoted in BPHS; 'Phaladeepika' its own."""
    # 'BPHS' = everything encoded from the BPHS volumes, incl. other texts quoted in its notes (as in the BPHS test);
    # 'Phaladeepika' = only rules read from the Phaladeepika text itself
    return any((s == "BPHS" and "BPHS" in r["source"]) or (s != "BPHS" and r["source"] == s) for s in sources)


def subtype(label: str) -> str | None:
    for k, rx in SUBTYPES.items():
        if rx.search(label):
            return k
    return None


def load(half: int) -> list[dict]:
    sets = [s for s in P.case_control_sets(P.SOURCE_DB, halves=(half,), categories=BASE_CATS)
            if not math.isnan(s["natal"][P.NATAL.index("Ascendant")])]
    sets = [s for s in sets if not (s["category"] == "Prize" and games(s["jds"][0]))]
    sex = genders(sorted({s["name"] for s in sets}))
    for s in sets:
        s["sex"] = s["gender"] = sex.get(s["name"])
        s["sub"] = subtype(s["label"]) if s["category"] == "Death_of_relative" else None
    return sets


def compute(half: int, workers: int, limit: int = 0, sources=("BPHS",)) -> tuple[list[dict], list[dict]]:
    tag = ("" if tuple(sources) == ("BPHS",) else "_" + "+".join(sources)) + os.environ.get("ASTRO_RUN_TAG", "")
    path = ROOT / "data" / "cache" / f"bphs_engine_half{half}{tag}{f'_limit{limit}' if limit else ''}.pkl"
    sets = load(half)
    if limit:
        sets = [s for i, s in enumerate(sets) if i % max(1, len(sets) // limit) == 0][:limit]
    from src.rules import engine as _E                # the key also fingerprints the rule set, so a rebuilt book is never read from a stale cache
    rules_now = [r for r in _E.load_rules()[0] if r["kind"] == "timing" and _src_ok(r, sources)]
    fp = hashlib.sha256(json.dumps([(r["id"], r["when"], r["predicts"]) for r in rules_now], sort_keys=True, default=str).encode()).hexdigest()
    key = [fp] + [(s["name"], s["category"], s["jds"][0]) for s in sets]
    if path.exists():
        z = pickle.loads(path.read_bytes())
        if z["key"] == key:
            return sets, z["fired"]
    rng = np.random.default_rng(7)
    donors = rng.integers(0, len(sets), len(sets))
    jobs = [(s, {k: sets[d][k] for k in ("natal", "birth_jd", "lat", "lon")}) for s, d in zip(sets, donors)]
    t, fired = time.time(), []
    with Pool(workers, initializer=_init, initargs=(tuple(sources),)) as pool:
        for i, r in enumerate(pool.imap(_work, jobs, chunksize=8)):
            fired.append(r)
            if i % 1000 == 0:
                print(f"  half {half}: {i}/{len(jobs)} sets, {time.time() - t:.0f}s", flush=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pickle.dumps({"key": key, "fired": fired}))
    return sets, fired


# ── phase 2 ────────────────────────────────────────────────────────────────────────────────────────────────────
def relevance(rules: list[dict]) -> dict:
    """type -> (direct rule mask, pooled Positive/Negative mask); for pooled Death_of_relative the subset masks are
    added per set."""
    ev = np.array([r["predicts"].get("event") for r in rules], object)
    out = {}
    for t in TYPES:
        direct = ev == t
        if t in SUBTYPES:
            direct = direct | (ev == "Death_of_relative")
        pooled = ev == ("Positive" if t in POSITIVE else "Negative")
        out[t] = (direct, pooled)
    return out


def sets_of(t, sets):
    if t in SUBTYPES:
        return [i for i, s in enumerate(sets) if s["category"] == "Death_of_relative" and s["sub"] == t]
    return [i for i, s in enumerate(sets) if s["category"] == t]


def rule_mask(t, s, rel):
    direct, pooled = rel[t]
    if t == "Death_of_relative" and s["sub"]:
        direct = direct | rel[s["sub"]][0]
    return direct, pooled


def scores(idx_list, sets, fired, t, rel, which, mode, dirs):
    """(n, 5) matrix of engine scores; -inf where masked. mode: weighted | unweighted | direct."""
    S = np.full((len(idx_list), 5), -np.inf)
    M = np.zeros((len(idx_list), 5), bool)
    for a, i in enumerate(idx_list):
        direct, pooled = rule_mask(t, sets[i], rel)
        m = direct if mode == "direct" else (direct | pooled)
        for j, f in enumerate(fired[i][which]):
            if f is None:
                continue
            ix, w = f[0], f[1]
            sel = m[ix]
            S[a, j] = float((dirs[ix[sel]] if mode == "unweighted" else w[sel]).sum())
            M[a, j] = True
    keep = M[:, 0] & (M[:, 1:].sum(1) >= 2)
    return S, M, keep


def placebo(S, M, cat):
    order = [4, 3, 2, 1] if cat == "Death" else [2, 1, 3, 4]
    Sp, Mp = S[:, order], M[:, order]
    keep = Mp[:, 0] & (Mp[:, 1:].sum(1) >= 2)
    return Sp, Mp, keep


def per_rule(sets, fired, rules, rel, n_rules):
    """Per rule x type: mean over sets of [fire(event) - mean fire(controls)] for actual minus mismatched."""
    from scipy import stats
    dirs = np.array([1 if r["predicts"]["direction"] == "+" else -1 for r in rules])
    res = []
    for t in TYPES:
        ids = sets_of(t, sets)
        if len(ids) < 30:
            continue
        D = []
        for i in ids:
            row = []
            for which in ("actual", "mismatched"):
                fs = fired[i][which]
                if fs[0] is None or sum(f is not None for f in fs[1:]) < 2:
                    row = None
                    break
                B = np.zeros((5, n_rules), np.float32)
                ok = np.zeros(5, bool)
                for j, f in enumerate(fs):
                    if f is not None:
                        B[j] = np.unpackbits(f[2])[:n_rules]
                        ok[j] = True
                row.append(B[0] - B[1:][ok[1:]].mean(0))
            if row is not None:
                D.append(row[0] - row[1])
        D = np.array(D)
        direct, pooled = rel[t]
        for k in np.where(direct | pooled)[0]:
            d = D[:, k]
            if not d.any():
                continue
            tt, p = stats.ttest_1samp(d, 0.0)
            res.append({"rule": rules[k]["id"], "type": t, "n": len(d), "mean": float(d.mean()), "t": float(tt),
                        "p": float(p), "claimed": int(dirs[k])})
    ps = np.array([r["p"] for r in res])
    order = np.argsort(ps)
    m = len(ps)
    thresh = 0.05 * np.arange(1, m + 1) / m
    passed = np.zeros(m, bool)
    below = np.where(ps[order] <= thresh)[0]
    if len(below):
        passed[order[: below.max() + 1]] = True
    agree = sum(1 for r, ok in zip(res, passed) if ok and np.sign(r["mean"]) == r["claimed"])
    oppose = sum(1 for r, ok in zip(res, passed) if ok and np.sign(r["mean"]) != r["claimed"])
    raw_agree = sum(1 for r in res if r["p"] < .05 and np.sign(r["mean"]) == r["claimed"])
    raw_oppose = sum(1 for r in res if r["p"] < .05 and np.sign(r["mean"]) != r["claimed"])
    top = sorted((dict(r, fdr=bool(ok)) for r, ok in zip(res, passed)), key=lambda r: r["p"])[:25]
    return {"tests": m, "fdr_agree": agree, "fdr_oppose": oppose, "p05_agree": raw_agree, "p05_oppose": raw_oppose,
            "top": top}


def learned(sets, fired, t, n_rules):
    ids = sets_of(t, sets)
    cs = [sets[i] for i in ids]
    X = np.zeros((len(ids), 5, n_rules), np.uint8)
    M = np.zeros((len(ids), 5), bool)
    for a, i in enumerate(ids):
        for j, f in enumerate(fired[i]["actual"]):
            if f is not None:
                X[a, j] = np.unpackbits(f[2])[:n_rules]
                M[a, j] = True
    folds = grouped_folds(cs)
    cols = np.arange(n_rules)
    oof, models = Mo.cross_validated_scores(X, M, folds, cols)
    demo = Demographic()
    Xd, Md = Mo.matrix(cs, featurizer=demo)
    oofd, _ = Mo.cross_validated_scores(Xd, Md, folds, demo.default_columns())
    cr, cd = Mo.per_set_c(oof, M), Mo.per_set_c(oofd, Md)
    from src import validation as V
    return {"sets": len(cs), "rules_c": round(float(cr.mean()), 4), "demo_c": round(float(cd.mean()), 4),
            "delta_vs_demo": paired_delta(cd, cr, len(TYPES)),
            "placebo_c": V.placebo_c_index(models, X, M, folds, t if t == "Death" else "x", cols)}


def analyse(sets, fired, rules, report_types=TYPES, n_tests=len(TYPES)):
    rel = relevance(rules)
    dirs = np.array([1 if r["predicts"]["direction"] == "+" else -1 for r in rules], np.float32)
    out = {}
    for t in report_types:
        ids = sets_of(t, sets)
        if len(ids) < 10:
            out[t] = {"sets": len(ids), "verdict": "too few sets"}
            continue
        cat = sets[ids[0]]["category"]
        r = {"sets": len(ids)}
        for mode in ("weighted", "unweighted", "direct"):
            Sa, Ma, ka = scores(ids, sets, fired, t, rel, "actual", mode, dirs)
            Sm, Mm, km = scores(ids, sets, fired, t, rel, "mismatched", mode, dirs)
            k = ka & km
            ca, cm = Mo.per_set_c(Sa[k], Ma[k]), Mo.per_set_c(Sm[k], Mm[k])
            d = paired_delta(cm, ca, n_tests)
            entry = {"n": int(k.sum()), "c_actual": round(float(ca.mean()), 4), "c_actual_ci": Mo.bootstrap_ci(ca),
                     "c_mismatched": round(float(cm.mean()), 4), "delta": d,
                     "ties_all_dates": round(float(np.mean([len(set(row[m])) == 1 for row, m in zip(Sa[k], Ma[k])])), 3)}
            if mode == "weighted":
                Spa, Mpa, kpa = placebo(Sa, Ma, cat)
                Spm, Mpm, kpm = placebo(Sm, Mm, cat)
                kp = kpa & kpm
                pa, pm = Mo.per_set_c(Spa[kp], Mpa[kp]), Mo.per_set_c(Spm[kp], Mpm[kp])
                entry["placebo_delta"] = paired_delta(pm, pa, 1)
                checks = {"beats_mismatched_bonferroni": d["ci_bonferroni"][0] > 0,
                          "above_chance": entry["c_actual_ci"][0] > 0.5,
                          "placebo_clean": entry["placebo_delta"]["ci95"][0] <= 0}
                entry["checks"] = checks
                r["verdict"] = "PASS" if all(checks.values()) else \
                    "no signal" if not checks["beats_mismatched_bonferroni"] else \
                    "fails: " + ", ".join(k_ for k_, v in checks.items() if not v)
            r[mode] = entry
        out[t] = r
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--limit", type=int, default=0, help="smoke test on this many sets (results not valid)")
    ap.add_argument("--sources", default="BPHS", help="comma list: BPHS, Phaladeepika")
    ap.add_argument("--prereg", default="docs/prereg_bphs_engine.md")
    ap.add_argument("--ratings", default="", help="comma list of Rodden ratings to keep (e.g. AA); default all")
    args = ap.parse_args()
    t0 = time.time()
    sources = tuple(args.sources.split(","))
    rules = [r for r in E.load_rules()[0] if r["kind"] == "timing" and _src_ok(r, sources)]
    n_rules = len(rules)
    stamp = f"{datetime.now():%Y%m%d_%H%M}"
    out_path = ROOT / ("data" if args.limit else "docs") / f"results_engine_{'+'.join(sources)}{os.environ.get('ASTRO_RUN_TAG', '')}{'_' + args.ratings if args.ratings else ''}_{stamp}{'_smoke' if args.limit else ''}.json"
    report = {"run_at": datetime.now(timezone.utc).isoformat(), "prereg": args.prereg, "sources": list(sources),
              "timing_rules": n_rules, "event_rules": sum(1 for r in rules if r["predicts"].get("event"))}

    sets, fired = compute(0, args.workers, args.limit, sources)
    if args.ratings:
        keep_r = set(args.ratings.split(","))
        idx = [i for i, s in enumerate(sets) if str(s.get("rating") or "").strip() in keep_r]
        sets, fired = [sets[i] for i in idx], [fired[i] for i in idx]
        report["ratings"] = sorted(keep_r)
    report["phase1_seconds"] = round(time.time() - t0)
    report["sets_half0"] = len(sets)
    print(f"phase 1 done: {len(sets)} sets in {time.time() - t0:.0f}s", flush=True)

    report["primary"] = analyse(sets, fired, rules)
    out_path.write_text(json.dumps(report, indent=2))
    for t, r in report["primary"].items():
        if "weighted" not in r:
            print(f"{t:20s} n={r['sets']:5d}  {r['verdict']}", flush=True)
            continue
        w, u, dd = r["weighted"], r["unweighted"], r["direct"]
        print(f"{t:20s} n={w['n']:5d}  C {w['c_actual']:.4f} vs mismatched {w['c_mismatched']:.4f}  "
              f"dC {w['delta']['delta_c']:+.4f} bonf {w['delta']['ci_bonferroni']}  placebo dC "
              f"{w['placebo_delta']['delta_c']:+.4f} | unweighted dC {u['delta']['delta_c']:+.4f} | direct dC "
              f"{dd['delta']['delta_c']:+.4f}  -> {r['verdict']}", flush=True)

    print("per-rule tests...", flush=True)
    report["per_rule"] = per_rule(sets, fired, rules, relevance(rules), n_rules)
    pr = report["per_rule"]
    print(f"per rule: {pr['tests']} tests; FDR-significant in claimed direction {pr['fdr_agree']}, opposite "
          f"{pr['fdr_oppose']}; p<.05 claimed {pr['p05_agree']}, opposite {pr['p05_oppose']}", flush=True)
    out_path.write_text(json.dumps(report, indent=2))

    report["learned"] = {}
    for t in TYPES:
        if len(sets_of(t, sets)) < 50:
            continue
        r = report["learned"][t] = learned(sets, fired, t, n_rules)
        out_path.write_text(json.dumps(report, indent=2))
        print(f"learned {t:20s} n={r['sets']:5d}  RULES {r['rules_c']}  DEMO {r['demo_c']}  dC "
              f"{r['delta_vs_demo']['delta_c']:+.4f} bonf {r['delta_vs_demo']['ci_bonferroni']}  placebo "
              f"{r['placebo_c']['placebo_c']}", flush=True)

    passes = [t for t, r in report["primary"].items() if r.get("verdict") == "PASS"]
    report["confirmation"] = {}
    if passes and not args.limit:
        sets1, fired1 = compute(1, args.workers, 0, sources)
        conf = analyse(sets1, fired1, rules, passes, 1)
        for t in passes:
            w = conf[t].get("weighted")
            ok = bool(w and w["delta"]["ci95"][0] > 0)
            report["confirmation"][t] = {**conf[t], "confirmed": ok}
            print(f"CONFIRM {t}: {'CONFIRMED' if ok else 'not confirmed'} {w and w['delta']}", flush=True)
    report["total_seconds"] = round(time.time() - t0)
    out_path.write_text(json.dumps(report, indent=2))
    print("written", out_path, flush=True)


if __name__ == "__main__":
    main()
