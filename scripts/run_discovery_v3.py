"""Discovery v3 (docs/prereg_discovery_v3.md): book-free search, real chart vs a donor born within +-15 days, same dates.

    python scripts/run_discovery_v3.py discover        # half 0: D1 recurrence test + D2 candidate mining
    python scripts/run_discovery_v3.py confirm         # half 1: the D2 candidates, once
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

os.environ["ASTRO_OFFSETS"] = "half"                     # half-year control dates (prereg)
import numpy as np                                        # noqa: E402
import swisseph as swe                                    # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_bphs_engine as RB                 # noqa: E402
from src import preprocessing as P                        # noqa: E402

YEAR = P.YEAR
F = swe.FLG_MOSEPH
TRANSIT = [swe.SUN, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.MEAN_NODE, swe.URANUS, swe.NEPTUNE, swe.PLUTO]
TNAMES = ['Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Node', 'Uranus', 'Neptune', 'Pluto']
NNAMES = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Node', 'Asc', 'MC']
NATAL_IDS = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.MEAN_NODE]
ASP = np.array([0, 60, 90, 120, 180.0])
ANAMES = ['conj', 'sextile', 'square', 'trine', 'opp']
SELF_T = np.zeros((10, 10), bool)
for i, t in enumerate(TNAMES):
    if t in NNAMES:
        SELF_T[i, NNAMES.index(t)] = True
SELF_P = np.zeros((2, 10), bool)
SELF_P[0, 0] = SELF_P[1, 1] = True
LORDS = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
VY = np.array([7, 20, 6, 10, 7, 18, 16, 19, 17.0])

# feature names (fixed order)
MASK_T = np.repeat(~SELF_T[:, :, None], 5, axis=2).ravel()
MASK_P = np.repeat(~SELF_P[:, :, None], 5, axis=2).ravel()
NAMES = [f'transit {t} {a} natal {n}' for t in TNAMES for n in NNAMES for a in ANAMES]
NAMES = [x for x, m in zip(NAMES, MASK_T) if m]
NAMES += [x for x, m in zip([f'progressed {t} {a} natal {n}' for t in ('Sun', 'Moon') for n in NNAMES for a in ANAMES], MASK_P) if m]
N_GEO = len(NAMES)
NAMES += [f'mahadasha {l}' for l in LORDS] + [f'antardasha {l}' for l in LORDS] + [f'dasha {a}-{b}' for a in LORDS for b in LORDS]
NF = len(NAMES)

_sky, _nat = {}, {}


def sky(jd):
    if jd not in _sky:
        _sky[jd] = np.array([swe.calc_ut(jd, b, F)[0][0] for b in TRANSIT])
    return _sky[jd]


def natal(bjd, lat, lon):
    k = (bjd, lat, lon)
    if k not in _nat:
        pos = [swe.calc_ut(bjd, b, F)[0][0] for b in NATAL_IDS]
        _, ascmc = swe.houses_ex(bjd, lat, lon, b'O')            # Asc/MC are house-system-free; Porphyry works at any latitude
        pos += [ascmc[0], ascmc[1]]
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        moon_sid = swe.calc_ut(bjd, swe.MOON, F | swe.FLG_SIDEREAL)[0][0]
        nak = moon_sid / (360 / 27)
        idx = int(nak) % 9
        elapsed = (nak - int(nak)) * VY[idx]
        _nat[k] = (np.array(pos), idx, elapsed)
    return _nat[k]


def dasha(idx, elapsed, age):
    t = age + elapsed
    t %= 120.0
    i = idx
    while t >= VY[i]:
        t -= VY[i]
        i = (i + 1) % 9
    md = i
    j = md
    while True:
        d = VY[md] * VY[j] / 120
        if t < d:
            return md, j
        t -= d
        j = (j + 1) % 9


def within(a, b, orb):
    d = np.abs((a[:, None] - b[None, :] + 180) % 360 - 180)            # 0..180
    return (np.abs(d[:, :, None] - ASP[None, None, :]) <= orb)


def vec(jd, bjd_own, chart, pbjd):
    pos, idx, elapsed = chart
    age = (jd - bjd_own) / YEAR
    t = within(sky(jd), pos, 2.0).ravel()[MASK_T]
    pj = pbjd + age * 1.0                                 # a day for a year after the chart's own birth moment
    prog = np.array([swe.calc_ut(pj, swe.SUN, F)[0][0], swe.calc_ut(pj, swe.MOON, F)[0][0]])
    p = within(prog, pos, 1.0).ravel()[MASK_P]
    md, ad = dasha(idx, elapsed, age)
    d = np.zeros(99, bool)
    d[md] = True
    d[9 + ad] = True
    d[18 + md * 9 + ad] = True
    return np.concatenate([t, p, d])


def donors(sets, seed):
    """Per person: another person born within +-15 days (widened to 30 if none)."""
    ppl = {}
    for s in sets:
        ppl.setdefault(s['name'], (s['birth_jd'], s['lat'], s['lon']))
    names = sorted(ppl, key=lambda n: ppl[n][0])
    b = np.array([ppl[n][0] for n in names])
    rng = np.random.default_rng(seed)
    out = {}
    for i, n in enumerate(names):
        for w in (15, 30, 60):
            lo, hi = np.searchsorted(b, b[i] - w), np.searchsorted(b, b[i] + w)
            cand = [j for j in range(lo, hi) if j != i]
            if cand:
                out[n] = ppl[names[int(rng.choice(cand))]]
                break
    return out


def set_vectors(sets, dmap):
    """Per set: (real matrix, donor matrix) of shape (dates, NF) and validity mask."""
    out = []
    for s in sets:
        own = natal(s['birth_jd'], s['lat'], s['lon'])
        dn = dmap.get(s['name'])
        if dn is None:
            out.append(None)
            continue
        don = natal(*dn)
        R = np.array([vec(j, s['birth_jd'], own, s['birth_jd']) for j in s['jds']])
        D = np.array([vec(j, s['birth_jd'], don, dn[0]) for j in s['jds']])
        out.append((R, D, np.array(s['mask'])))
    return out


def deltas(vs):
    """Per set: delta = (event - mean controls) real - same donor, vector over features."""
    out = []
    for v in vs:
        if v is None:
            out.append(None)
            continue
        R, D, m = v
        c = m.copy()
        c[0] = False
        if c.sum() == 0:
            out.append(None)
            continue
        ur = R[0].astype(float) - R[c].mean(0)
        ud = D[0].astype(float) - D[c].mean(0)
        out.append(ur - ud)
    return out


def d1(sets, vs, rng, n_boot=2000):
    by = defaultdict(list)
    for k, (s, v) in enumerate(zip(sets, vs)):
        if v is None:
            continue
        t = s['sub'] if s['category'] == 'Death_of_relative' and s['sub'] else s['category']
        by[(s['name'], t)].append(k)
    per_person = defaultdict(list)
    for (name, t), ks in by.items():
        if len(ks) < 2:
            continue
        for a in range(len(ks)):
            for b in range(a + 1, len(ks)):
                if sets[ks[a]]['jds'][0] == sets[ks[b]]['jds'][0]:
                    continue
                Ra, Da = vs[ks[a]][0][0], vs[ks[a]][1][0]
                Rb, Db = vs[ks[b]][0][0], vs[ks[b]][1][0]

                def sim(x, y):
                    g = slice(0, N_GEO)
                    u = np.logical_or(x[g], y[g]).sum()
                    j = np.logical_and(x[g], y[g]).sum() / u if u else 0.0
                    dd = (np.argmax(x[N_GEO:N_GEO + 9]) == np.argmax(y[N_GEO:N_GEO + 9])) + \
                         (np.argmax(x[N_GEO + 9:N_GEO + 18]) == np.argmax(y[N_GEO + 9:N_GEO + 18]))
                    return (j + dd / 2) / 2
                per_person[name].append(sim(Ra, Rb) - sim(Da, Db))
    vals = np.array([np.mean(v) for v in per_person.values()])
    boots = [vals[rng.integers(0, len(vals), len(vals))].mean() for _ in range(n_boot)]
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return {'people': len(vals), 'pairs': int(sum(len(v) for v in per_person.values())), 'mean_diff': float(vals.mean()),
            'ci95': [float(lo), float(hi)], 'pass': bool(lo > 0)}


def type_index(sets):
    out = {}
    for t in RB.TYPES:
        out[t] = RB.sets_of(t, sets)
    return out


def zstats(dl, idx):
    X = np.array([dl[k] for k in idx if dl[k] is not None])
    if len(X) < 30:
        return None
    nz = (X != 0).sum(0)
    m = X.mean(0)
    se = X.std(0, ddof=1) / math.sqrt(len(X))
    z = np.where(se > 0, m / np.where(se > 0, se, 1), 0.0)
    return X, m, z, nz


def discover():
    sets = RB.load(0)
    print('sets', len(sets), flush=True)
    dmap = donors(sets, 21)
    vs = set_vectors(sets, dmap)
    print('vectors done', flush=True)
    rng = np.random.default_rng(5)
    res = {'d1': d1(sets, vs, rng)}
    print('D1', res['d1'], flush=True)
    dl = deltas(vs)
    cands = []
    ti = type_index(sets)
    for t, idx in ti.items():
        r = zstats(dl, idx)
        if r is None:
            continue
        X, m, z, nz = r
        ok = np.where(nz >= 30)[0]
        top = ok[np.argsort(-np.abs(z[ok]))][:10]
        for f in top:
            cands.append({'type': t, 'feature': NAMES[f], 'f': int(f), 'z_half0': round(float(z[f]), 3),
                          'delta_half0': round(float(m[f]), 5), 'sets': int(len(X)), 'nonzero': int(nz[f]),
                          'direction': '+' if z[f] > 0 else '-'})
        print(f'{t:20s} n={len(X):6d} top |z| {abs(z[top[0]]):.2f} ({NAMES[top[0]]})', flush=True)
    allz = []
    for t, idx in ti.items():
        r = zstats(dl, idx)
        if r is not None:
            allz.extend(np.abs(r[2][r[3] >= 30]).tolist())
    res['n_tests_half0'] = len(allz)
    res['max_abs_z_half0'] = float(max(allz))
    res['candidates'] = cands
    stamp = f'{datetime.now():%Y%m%d_%H%M}'
    (ROOT / 'docs' / f'results_discovery_v3_half0_{stamp}.json').write_text(json.dumps(res, indent=2))
    (ROOT / 'docs' / 'discovery_v3_candidates.json').write_text(json.dumps(cands, indent=2))
    print('candidates', len(cands), 'written')


def confirm():
    cands = json.loads((ROOT / 'docs' / 'discovery_v3_candidates.json').read_text())
    sets = RB.load(1)
    print('sets', len(sets), flush=True)
    dmap = donors(sets, 22)
    vs = set_vectors(sets, dmap)
    dl = deltas(vs)
    ti = type_index(sets)
    from scipy.stats import norm
    alpha = 0.05 / len(cands)
    rng = np.random.default_rng(9)
    out = []
    for c in cands:
        idx = [k for k in ti[c['type']] if dl[k] is not None]
        x = np.array([dl[k][c['f']] for k in idx])
        sgn = 1 if c['direction'] == '+' else -1
        m = x.mean()
        se = x.std(ddof=1) / math.sqrt(len(x))
        z = sgn * m / se if se > 0 else 0.0
        p = float(norm.sf(z))
        # bootstrap clustered by event date
        dates = defaultdict(list)
        for k, xi in zip(idx, x):
            dates[sets[k]['jds'][0]].append(xi)
        keys = list(dates)
        bs = []
        for _ in range(2000):
            pick = rng.integers(0, len(keys), len(keys))
            vals = [v for i in pick for v in dates[keys[i]]]
            bs.append(sgn * np.mean(vals))
        lo = float(np.quantile(bs, alpha))
        ok = p < alpha and lo > 0
        out.append({**c, 'n_half1': len(x), 'delta_half1': round(float(m), 5), 'z_half1': round(float(z), 3), 'p_half1': p,
                    'date_cluster_lo': round(lo, 5), 'confirmed': bool(ok)})
        print(f"{c['type']:20s} {c['feature']:45s} z0 {c['z_half0']:+.2f} -> z1 {z:+.2f} p {p:.4f} {'CONFIRMED' if ok else ''}", flush=True)
    stamp = f'{datetime.now():%Y%m%d_%H%M}'
    res = {'run_at': datetime.now(timezone.utc).isoformat(), 'alpha_each': alpha, 'confirmed': sum(o['confirmed'] for o in out),
           'candidates': out, 'p05_same_direction': sum(1 for o in out if o['p_half1'] < 0.05)}
    (ROOT / 'docs' / f'results_discovery_v3_half1_{stamp}.json').write_text(json.dumps(res, indent=2))
    print('confirmed', res['confirmed'], 'of', len(out), '; p<.05 in the claimed direction', res['p05_same_direction'])


if __name__ == '__main__':
    {'discover': discover, 'confirm': confirm}[sys.argv[1]]()
