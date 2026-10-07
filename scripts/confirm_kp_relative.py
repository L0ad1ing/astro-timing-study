"""
scripts/confirm_kp_relative.py — the single half-1 confirmation in docs/prereg_kp_relative_confirm.md.

Usage: python -m scripts.confirm_kp_relative [--workers 6]
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

from scripts.harmonic_date_leak_check import month                  # noqa: E402
from scripts.run_bphs_engine import compute, sets_of, _src_ok       # noqa: E402
from scripts.run_harmonic_pipeline import paired_delta              # noqa: E402
from src import models as Mo                                         # noqa: E402
from src import validation as V                                      # noqa: E402
from src.discovery_v2.rule_evaluator import Demographic              # noqa: E402
from src.rules import engine as E                                    # noqa: E402

T = 'Death_of_relative'
SOURCES = ('KP Readers',)


def matrix(sets, fired, ids, n_rules):
    X = np.zeros((len(ids), 5, n_rules), np.uint8)
    M = np.zeros((len(ids), 5), bool)
    for a, i in enumerate(ids):
        for j, f in enumerate(fired[i]['actual']):
            if f is not None:
                X[a, j] = np.unpackbits(f[2])[:n_rules]
                M[a, j] = True
    return X, M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=6)
    args = ap.parse_args()
    rules = [r for r in E.load_rules()[0] if r['kind'] == 'timing' and _src_ok(r, SOURCES)]
    n = len(rules)
    s0, f0 = compute(0, args.workers, 0, SOURCES)
    s1, f1 = compute(1, args.workers, 0, SOURCES)
    i0 = sets_of(T, s0)
    seen = {month(s0[i]['jds'][0]) for i in i0}
    i1 = [i for i in sets_of(T, s1) if month(s1[i]['jds'][0]) not in seen]
    X0, M0 = matrix(s0, f0, i0, n)
    X1, M1 = matrix(s1, f1, i1, n)
    cols = np.arange(n)
    rules_m = Mo.fit(X0, M0, cols)
    demo = Demographic()
    Xd0, Md0 = Mo.matrix([s0[i] for i in i0], featurizer=demo)
    Xd1, Md1 = Mo.matrix([s1[i] for i in i1], featurizer=demo)
    demo_m = Mo.fit(Xd0, Md0, demo.default_columns())
    cr = Mo.per_set_c(Mo.score(rules_m, X1, M1, cols), M1)
    cd = Mo.per_set_c(Mo.score(demo_m, Xd1, Md1, demo.default_columns()), Md1)
    d = paired_delta(cd, cr, 1)
    plc = V.placebo_c_index([rules_m], X1, M1, np.zeros(len(i1), int), 'x', cols)
    out = {'run_at': datetime.now(timezone.utc).isoformat(), 'prereg': 'docs/prereg_kp_relative_confirm.md',
           'train_sets': len(i0), 'test_sets': len(i1), 'rules_c': round(float(cr.mean()), 4), 'rules_c_ci': Mo.bootstrap_ci(cr),
           'demo_c': round(float(cd.mean()), 4), 'delta': d, 'placebo': plc}
    out['confirmed'] = bool(d['ci95'][0] > 0 and out['rules_c_ci'][0] > 0.5 and plc['ci'][0] <= 0.5)
    path = ROOT / 'docs' / f'results_kp_relative_confirm_{datetime.now():%Y%m%d_%H%M}.json'
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
