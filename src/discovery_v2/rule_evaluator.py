"""
src/discovery_v2/rule_evaluator.py — rules, their exposure, matched statistics and the demographic baseline.

A rule is a tuple of conditions (feature index, op, threshold), op in {"<=", ">", ">="}; NaN never satisfies one.
  mh_vector       Mantel-Haenszel matched odds ratio for many binary exposures at once (Robins-Breslow-Greenland SE)
  clogit          conditional logistic regression, strata = case-control sets (Newton-Raphson)
  Demographic     baseline featurizer: age, calendar year, sex
  describe        plain-language rule text (cos k ≥ t → "within ±x° of a multiple of 360/k°")
  bh              Benjamini-Hochberg q-values
"""
from __future__ import annotations

import math
import re

import numpy as np
from scipy import stats


# ── Rules ────────────────────────────────────────────────────────────────────

def exposure(X: np.ndarray, rule: tuple) -> np.ndarray:
    """(n, k) bool: dates where every condition holds."""
    E = np.ones(X.shape[:2], bool)
    for f, op, t in rule:
        v = X[:, :, f]
        E &= (v <= t) if op == "<=" else (v > t) if op == ">" else (v >= t)
    return E


def describe(rule: tuple, names: list[str]) -> str:
    parts = []
    for f, op, t in rule:
        name = names[f]
        m = re.match(r"(.*) cos(\d+)$", name)
        if m and op in (">=", ">"):
            k = int(m.group(2))
            parts.append(f"{m.group(1)} within ±{math.degrees(math.acos(max(-1, min(1, t)))) / k:.1f}° of a multiple of "
                         f"{360 / k:g}°")
        elif m:
            k = int(m.group(2))
            parts.append(f"{m.group(1)} more than {math.degrees(math.acos(max(-1, min(1, t)))) / k:.1f}° from every "
                         f"multiple of {360 / k:g}°")
        else:
            parts.append(f"{name} {op} {t:.4g}")
    return " AND ".join(parts)


# ── Matched statistics ───────────────────────────────────────────────────────

def mh_vector(E: np.ndarray, mask: np.ndarray) -> dict:
    """E: (n, k, R) bool exposures, slot 0 = event. Returns log OR, SE and z per rule (NaN where undefined)."""
    case = E[:, 0, :].astype(float)
    cm = mask[:, 1:]
    exposed = (E[:, 1:, :] & cm[:, :, None]).sum(1).astype(float)
    nc = cm.sum(1).astype(float)[:, None]
    n = 1 + nc
    num, den = case * (nc - exposed) / n, (1 - case) * exposed / n
    r, s = num.sum(0), den.sum(0)
    p, q = (case + nc - exposed) / n, (1 - case + exposed) / n
    with np.errstate(divide="ignore", invalid="ignore"):
        var = ((p * num).sum(0) / (2 * r ** 2) + ((p * den).sum(0) + (q * num).sum(0)) / (2 * r * s)
               + (q * den).sum(0) / (2 * s ** 2))
        log_or = np.log(r / s)
        se = np.sqrt(var)
        z = log_or / se
    bad = (r == 0) | (s == 0)
    log_or[bad], se[bad], z[bad] = np.nan, np.nan, np.nan
    return {"log_or": log_or, "se": se, "z": z}


def clogit(X: np.ndarray, mask: np.ndarray, iters: int = 50) -> dict:
    """X: (n, k, p) covariates (finite on valid dates), slot 0 = event. Returns beta, se, z, two-sided p."""
    X = np.where(mask[:, :, None], X, 0.0).astype(np.float64)
    beta = np.zeros(X.shape[2])
    for _ in range(iters):
        eta = np.where(mask, X @ beta, -np.inf)
        eta -= eta.max(1, keepdims=True)
        w = np.exp(eta) * mask
        w /= w.sum(1, keepdims=True)
        xbar = (w[:, :, None] * X).sum(1)
        grad = (X[:, 0, :] - xbar).sum(0)
        d = X - xbar[:, None, :]
        H = np.einsum("nk,nkp,nkq->pq", w, d, d) + 1e-9 * np.eye(len(beta))
        step = np.linalg.solve(H, grad)
        beta += step
        if np.abs(step).max() < 1e-9:
            break
    se = np.sqrt(np.clip(np.diag(np.linalg.inv(H)), 0, None))
    z = np.divide(beta, se, out=np.zeros_like(beta), where=se > 0)
    return {"beta": beta, "se": se, "z": z, "p": 2 * stats.norm.sf(np.abs(z))}


def bh(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(q)
    out[order] = np.minimum(q, 1)
    return out


def c_index(scores: np.ndarray, mask: np.ndarray) -> float:
    s = np.where(mask, scores, -np.inf)
    valid = mask[:, 1:]
    wins = ((s[:, :1] > s[:, 1:]) & valid).sum(1) + 0.5 * ((s[:, :1] == s[:, 1:]) & valid).sum(1)
    return float((wins / valid.sum(1)).mean())


# ── Demographic baseline ─────────────────────────────────────────────────────

class Demographic:
    """Age, calendar year (decimal) and sex (1 male, 0 female, NaN unknown) — the bar every rule must clear."""
    name, n, dtype = "demographic", 3, np.float32
    names = ["age in years", "calendar year", "sex (1 = male)"]

    def context(self, s: dict) -> dict:
        return {"birth_jd": s["birth_jd"], "sex": {"M": 1.0, "F": 0.0}.get(s.get("sex"), np.nan)}

    def features(self, ctx: dict, jd: float) -> np.ndarray:
        return np.array([(jd - ctx["birth_jd"]) / 365.2422, 2000.0 + (jd - 2451545.0) / 365.2422, ctx["sex"]], np.float32)

    def default_columns(self) -> np.ndarray:
        return np.arange(3)
