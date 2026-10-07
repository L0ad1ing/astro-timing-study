"""Part N of docs/prereg_full_programme.md: every testable natal rule against life outcomes recorded in
Astro-Databank, real chart vs a donor's chart (another person born within +-2 years), half 0.

    python scripts/run_natal.py --workers 3 [--limit N] [--sources all|BPHS,...]

Phase 1 (cached in data/cache/natal_half0.pkl): for every person with a known birth time, the fired natal rules (index,
final signed weight from the Reader, which applies cancellations and strength scaling) on the real chart, a donor chart
and a second donor chart (placebo). Phase 2: per book and outcome, C(real) - C(donor) with person bootstraps;
per-rule paired tests (real vs donor fire, against the outcome), FDR 5%."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
import re
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import preprocessing as P                                     # noqa: E402
from src.rules import engine as E                                      # noqa: E402
from scripts.run_rao import genders                                    # noqa: E402

YEAR = P.YEAR
BOOKS = ['BPHS', 'Phaladeepika', 'KP Readers', 'KP modern', 'Saravali', 'Valens', 'Lilly']
VIOLENT_LABEL = re.compile(r'Accident|Homicide|Suicide|War|Terror|Execution', re.I)
NATURAL_LABEL = re.compile(r'Disease|Heart Attack', re.I)
VIOLENT_TEXT = re.compile(r'weapon|fire|water|drown|fall|poison|accident|murder|kill|execut|hang|behead|suicide|war\b|'
                          r'beast|animal|vehicle|thie', re.I)


def book_of(r):
    s = r['source']
    if 'BPHS' in s:
        return 'BPHS'
    return s if s in BOOKS else None


# ── outcomes ─────────────────────────────────────────────────────────────────────────────────────────
def load_outcomes():
    """Per person: dict of raw facts from every event row (labels included; the timing filter is not applied)."""
    out = defaultdict(lambda: {'marriages': [], 'divorce': 0, 'arrest': 0, 'illness': 0, 'child': 0, 'child_death': 0,
                               'widow': 0, 'father_death_jd': None, 'mother_death_jd': None, 'death_jd': None,
                               'death_cause': None, 'bjd': None})
    with sqlite3.connect(f'file:{P.SOURCE_DB}?mode=ro', uri=True) as c:
        rows = c.execute('SELECT name, event_category, event_date, birth_jd, event_label FROM ml_features '
                         "WHERE event_label != 'born on'").fetchall()
    for name, cat, ev, bjd, label in rows:
        o = out[name]
        if bjd is not None:
            o['bjd'] = float(bjd)
        label = label or ''
        try:
            j = P.jd_noon(date.fromisoformat(str(ev)[:10])) if ev else None
        except ValueError:
            j = None
        if cat == 'Death':
            if label.startswith('Death of Mate'):
                o['widow'] = 1
            elif label.startswith('Death of Father'):
                o['father_death_jd'] = j if o['father_death_jd'] is None or (j and j < o['father_death_jd']) else o['father_death_jd']
            elif label.startswith('Death of Mother'):
                o['mother_death_jd'] = j if o['mother_death_jd'] is None or (j and j < o['mother_death_jd']) else o['mother_death_jd']
            elif label.startswith('Death of Child'):
                o['child_death'] = 1
            elif label.startswith('Death of') or label.startswith('Sentenced'):
                pass
            elif j is not None:
                if o['death_jd'] is None or j < o['death_jd']:
                    o['death_jd'] = j
                if VIOLENT_LABEL.search(label):
                    o['death_cause'] = 'violent'
                elif NATURAL_LABEL.search(label) and o['death_cause'] != 'violent':
                    o['death_cause'] = 'natural'
        elif cat == 'Marriage' and j is not None:
            o['marriages'].append(j)
        elif cat == 'Divorce':
            o['divorce'] = 1
        elif cat == 'Arrest':
            o['arrest'] = 1
        elif cat == 'Illness':
            o['illness'] = 1
        elif cat == 'Birth_Child':
            o['child'] = 1
    return out


def outcome_values(o, bjd):
    """outcome -> value (None = not eligible). Binary outcomes 0/1; 'long_life' is age at death (continuous)."""
    v = {}
    born = (bjd - 2415020.5) / YEAR + 1900
    if o['death_jd'] and born < 1940:
        v['long_life'] = (o['death_jd'] - bjd) / YEAR
    if o['death_jd'] and o['death_cause']:
        v['violent_death'] = 1 if o['death_cause'] == 'violent' else 0
    v['married'] = 1 if o['marriages'] else 0
    if o['marriages']:
        v['several_marriages'] = 1 if len(set(int(m) for m in o['marriages'])) >= 2 else 0
        v['divorce'] = o['divorce']
        v['first_marriage_age'] = (min(o['marriages']) - bjd) / YEAR
    v['widowhood'] = o['widow']
    for k in ('father', 'mother'):
        dj = o[f'{k}_death_jd']
        v[f'{k}_lost_young'] = 1 if dj is not None and (dj - bjd) / YEAR < 18 else 0
    v['children'] = o['child']
    v['child_death'] = o['child_death']
    v['arrest'] = o['arrest']
    v['illness'] = o['illness']
    return v


# outcome -> list of (domain, sign rule) ; sign rule maps (book, direction, text) -> +1 (predicts outcome / larger
# value), -1 (predicts against), 0 (not relevant)
def _plus(b, d, t):
    return 1 if d == '+' else -1


def _minus(b, d, t):
    return 1 if d == '-' else -1


def _widow(b, d, t):
    if b == 'Saravali':
        return 1 if d == '-' else -1
    return 1 if d == '+' else -1


def _death_manner(b, d, t):
    return 1 if VIOLENT_TEXT.search(t) else -1


OUTCOMES = {
    'long_life': [('longevity', _plus)],
    'violent_death': [('violent_death', _plus), ('accident_risk', _minus), ('accident', _minus), ('death_manner', _death_manner)],
    'married': [('marriage', _plus)],
    'several_marriages': [('marriages_many', _plus)],
    'divorce': [('marriage', _minus)],
    'first_marriage_age': [('marriage_early', _minus)],          # '+' = early = a smaller age
    'widowhood': [('widowhood', _widow), ('spouse_death', _plus)],
    'father_lost_young': [('father', _minus)],
    'mother_lost_young': [('mother', _minus)],
    'children': [('children', _plus)],
    'child_death': [('children', _minus)],
    'arrest': [('imprisonment', _minus), ('legal', _minus), ('Arrest', _minus)],
    'illness': [('health', _minus)],
}
CONTINUOUS = {'long_life', 'first_marriage_age'}


# ── phase 1 ──────────────────────────────────────────────────────────────────────────────────────────
_R = None


def _init():
    global _R
    from src.rules.reader import Reader
    _R = Reader([r for r in E.load_rules()[0] if r['kind'] == 'natal'])
    _R.idx = {r['id']: i for i, r in enumerate(_R.rules)}


def _fire(person):
    try:
        rd = _R.read(E.Chart(person), None, kinds=('natal',))
    except Exception:
        return None
    idx = np.array([_R.idx[f.rule['id']] for f in rd.fired], np.int16)
    w = np.array([(1 if f.direction == '+' else -1) * f.weight for f in rd.fired], np.float32)
    return idx, w


def _work(job):
    p, d1, d2 = job
    out = []
    for extra in ({}, d1, d2):
        q = dict(p)
        if extra:
            q['natal'] = extra['natal']
            q['kp_birth'] = (extra['birth_jd'], extra['lat'], extra['lon'])
        out.append(_fire(q))
    return out


def people_half0(limit=0):
    ppl = P.load_people()
    outc = load_outcomes()
    rows = []
    for name, rec in ppl.items():
        o = outc.get(name)
        if o is None or o['bjd'] is None or rec['lat'] is None or math.isnan(rec['natal'][P.NATAL.index('Ascendant')]):
            continue
        if P.split_ids(name)[0] != 0:
            continue
        rows.append({'name': name, 'natal': rec['natal'], 'birth_jd': o['bjd'], 'lat': rec['lat'], 'lon': rec['lon'],
                     'rating': rec['rating'], 'jds': [o['bjd']], 'mask': [True], 'category': None, 'label': ''})
    rows.sort(key=lambda r: r['birth_jd'])
    if limit:
        rows = rows[::max(1, len(rows) // limit)][:limit]
    sex = genders([r['name'] for r in rows])
    for r in rows:
        r['sex'] = r['gender'] = sex.get(r['name'])
    return rows, outc


def donors_for(rows, seed):
    """A random other person born within +-2 years (rows sorted by birth)."""
    rng = np.random.default_rng(seed)
    b = np.array([r['birth_jd'] for r in rows])
    lo = np.searchsorted(b, b - 2 * YEAR)
    hi = np.searchsorted(b, b + 2 * YEAR)
    out = []
    for i in range(len(rows)):
        for _ in range(20):
            j = int(rng.integers(lo[i], hi[i]))
            if j != i:
                break
        out.append(j)
    return out


def compute(workers, limit):
    rows, outc = people_half0(limit)
    nat = [r for r in E.load_rules()[0] if r['kind'] == 'natal']
    fp = hashlib.sha256(json.dumps([(r['id'], r['when'], r['predicts']) for r in nat], sort_keys=True, default=str).encode()).hexdigest()
    path = ROOT / 'data' / 'cache' / f"natal_half0{f'_limit{limit}' if limit else ''}.pkl"
    key = [fp] + [r['name'] for r in rows]
    if path.exists():
        z = pickle.loads(path.read_bytes())
        if z['key'] == key:
            return rows, outc, z['fired'], nat
    d1, d2 = donors_for(rows, 11), donors_for(rows, 12)
    pick = lambda r: {k: r[k] for k in ('natal', 'birth_jd', 'lat', 'lon')}
    jobs = [(r, pick(rows[a]), pick(rows[b])) for r, a, b in zip(rows, d1, d2)]
    fired, t = [], time.time()
    with Pool(workers, initializer=_init) as pool:
        for i, res in enumerate(pool.imap(_work, jobs, chunksize=8)):
            fired.append(res)
            if i % 1000 == 0:
                print(f'  {i}/{len(jobs)} people, {time.time() - t:.0f}s', flush=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pickle.dumps({'key': key, 'fired': fired}))
    return rows, outc, fired, nat


# ── phase 2 ──────────────────────────────────────────────────────────────────────────────────────────
def cstat(score, y, continuous):
    """C: AUC for a binary outcome; for a continuous one, the probability that of two people the higher score has the
    larger value (Harrell-style, ties half), via Kendall's tau-b ~ (tau+1)/2."""
    score, y = np.asarray(score, float), np.asarray(y, float)
    if continuous:
        from scipy.stats import kendalltau
        t = kendalltau(score, y).statistic
        return 0.5 if t != t else (t + 1) / 2
    pos, neg = score[y == 1], score[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float('nan')
    from scipy.stats import rankdata
    r = rankdata(np.concatenate([pos, neg]))
    return (r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def analyse(rows, outc, fired, nat, books, n_boot=2000):
    meta = [(book_of(r), r['predicts'].get('domain'), r['predicts'].get('direction'), r['text']) for r in nat]
    vals = [outcome_values(outc[r['name']], r['birth_jd']) for r in rows]
    n_out = len(OUTCOMES)
    rng = np.random.default_rng(3)
    report = {}
    for book in books:
        bk = set(BOOKS) if book == 'all' else {book}
        rep = report[book] = {}
        for oc, doms in OUTCOMES.items():
            dmap = dict(doms)
            sign = np.zeros(len(nat))
            for i, (b, dom, d, t) in enumerate(meta):
                if b in bk and dom in dmap:
                    sign[i] = dmap[dom](b, d, t)
            if not sign.any():
                continue
            idx_p = [k for k, v in enumerate(vals) if oc in v and all(f is not None for f in fired[k])]
            if len(idx_p) < 200:
                continue
            y = np.array([vals[k][oc] for k in idx_p], float)
            cont = oc in CONTINUOUS
            if oc == 'first_marriage_age':          # '+' = early: predict a smaller age -> score against -age
                y = -y
            if not cont and (y.sum() < 20 or (len(y) - y.sum()) < 20):
                continue

            rdir = np.array([1.0 if m[2] == '+' else -1.0 for m in meta])

            def score(k, which):
                ix, w = fired[k][which]
                # w carries the fired direction (a rule reversed by another flips); sign[] is set for the rule's own
                # direction, so the contribution is w * (rule direction) * sign
                return float(w.dot(rdir[ix] * sign[ix])) if len(ix) else 0.0
            S = np.array([[score(k, j) for j in range(3)] for k in idx_p])
            c_real, c_don, c_plc = (cstat(S[:, j], y, cont) for j in range(3))
            boots, bplc = [], []
            for _ in range(n_boot):
                b = rng.integers(0, len(idx_p), len(idx_p))
                boots.append(cstat(S[b, 0], y[b], cont) - cstat(S[b, 1], y[b], cont))
                bplc.append(cstat(S[b, 2], y[b], cont) - cstat(S[b, 1], y[b], cont))
            boots = np.array(boots)
            a = 0.05 / n_out
            lo, hi = np.nanquantile(boots, [a / 2, 1 - a / 2])
            creal_b = []
            for _ in range(500):
                b = rng.integers(0, len(idx_p), len(idx_p))
                creal_b.append(cstat(S[b, 0], y[b], cont))
            clo = float(np.nanquantile(creal_b, 0.025))
            plc = float(np.nanmean(bplc))
            passed = lo > 0 and clo > 0.5 and abs(plc) < max(0.01, (hi - lo) / 4)
            rep[oc] = {'n': len(idx_p), 'events': None if cont else int(y.sum()), 'rules': int((sign != 0).sum()),
                       'c_real': round(c_real, 4), 'c_donor': round(c_don, 4), 'c_placebo': round(c_plc, 4),
                       'dC': round(c_real - c_don, 4), 'bonf': [round(lo, 4), round(hi, 4)], 'c_real_lo95': round(clo, 4),
                       'placebo_dC': round(plc, 4), 'pass': bool(passed)}
            print(f"{book:13s} {oc:19s} n={len(idx_p):6d} C {c_real:.4f} vs donor {c_don:.4f} dC {c_real - c_don:+.4f} "
                  f"bonf [{lo:+.4f}, {hi:+.4f}] placebo {plc:+.4f} -> {'PASS' if passed else 'no signal'}", flush=True)
    # per-rule paired tests (all books): fire on the real chart minus fire on the donor chart, against the outcome
    from scipy.stats import norm
    tests = []
    for oc, doms in OUTCOMES.items():
        dmap = dict(doms)
        idx_p = [k for k, v in enumerate(vals) if oc in v and all(f is not None for f in fired[k])]
        if len(idx_p) < 200:
            continue
        y = np.array([vals[k][oc] for k in idx_p], float)
        if oc == 'first_marriage_age':
            y = -y
        if oc in CONTINUOUS:
            y = (y > np.median(y)).astype(float)
        yc = y - y.mean()
        rel = [i for i, (b, dom, d, t) in enumerate(meta) if b in BOOKS and dom in dmap]
        F = np.zeros((len(idx_p), len(nat)), np.int8)
        G = np.zeros((len(idx_p), len(nat)), np.int8)
        for row, k in enumerate(idx_p):
            F[row, fired[k][0][0]] = 1
            G[row, fired[k][1][0]] = 1
        for i in rel:
            dlt = F[:, i].astype(float) - G[:, i]
            if np.abs(dlt).sum() < 20:
                continue
            T = float(yc.dot(dlt))
            se = math.sqrt(float((yc ** 2).dot(dlt ** 2)))
            if se == 0:
                continue
            z = T / se
            s = dmap[meta[i][1]](*[meta[i][0], meta[i][2], meta[i][3]])
            tests.append({'id': nat[i]['id'], 'outcome': oc, 'z_claimed': round(z * s, 3),
                          'p': float(2 * norm.sf(abs(z)))})
    ps = np.array([t['p'] for t in tests])
    order = np.argsort(ps)
    m = len(ps)
    thresh = 0.0
    for rank, j in enumerate(order, 1):
        if ps[j] <= 0.05 * rank / m:
            thresh = ps[j]
    fdr_for = sum(1 for t in tests if t['p'] <= thresh and t['z_claimed'] > 0) if thresh else 0
    fdr_against = sum(1 for t in tests if t['p'] <= thresh and t['z_claimed'] < 0) if thresh else 0
    p05_for = sum(1 for t in tests if t['p'] < 0.05 and t['z_claimed'] > 0)
    p05_against = sum(1 for t in tests if t['p'] < 0.05 and t['z_claimed'] < 0)
    print(f'per rule: {m} tests; FDR-significant for {fdr_for}, against {fdr_against}; p<.05 for {p05_for}, against {p05_against}')
    report['per_rule'] = {'tests': m, 'fdr_for': fdr_for, 'fdr_against': fdr_against, 'p05_for': p05_for,
                          'p05_against': p05_against,
                          'smallest': sorted(tests, key=lambda t: t['p'])[:25]}
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--sources', default='all')
    args = ap.parse_args()
    t0 = time.time()
    rows, outc, fired, nat = compute(args.workers, args.limit)
    print(f'phase 1 done: {len(rows)} people in {time.time() - t0:.0f}s', flush=True)
    books = BOOKS + ['all'] if args.sources == 'all' else args.sources.split(',')
    rep = analyse(rows, outc, fired, nat, books, n_boot=200 if args.limit else 2000)
    stamp = f'{datetime.now():%Y%m%d_%H%M}'
    out = ROOT / ('data' if args.limit else 'docs') / f"results_natal_{stamp}{'_smoke' if args.limit else ''}.json"
    untestable = sorted({r['predicts'].get('domain') for r in nat} - {d for v in OUTCOMES.values() for d, _ in v})
    out.write_text(json.dumps({'run_at': datetime.now(timezone.utc).isoformat(), 'prereg': 'docs/prereg_full_programme.md',
                               'people': len(rows), 'natal_rules': len(nat),
                               'testable_rules': sum(1 for r in nat if r['predicts'].get('domain') in {d for v in OUTCOMES.values() for d, _ in v}),
                               'untestable_domains': untestable, 'results': rep}, indent=2))
    print('written', out)


if __name__ == '__main__':
    main()
