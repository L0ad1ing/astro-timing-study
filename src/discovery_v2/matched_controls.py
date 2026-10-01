"""
src/discovery_v2/matched_controls.py — same-person, same-calendar-date controls with no other recorded event nearby.

Wraps preprocessing.case_control_sets (event vs the same calendar date −3, −1, +1, +3 years; own death −4..−1),
which stays unchanged so the parity tests against the Abraxas code still hold. Adds one filter: a control date within
EXCLUDE_DAYS of any other recorded event of that person (any type) is masked out, so controls are years in which,
as far as the record shows, nothing major happened around that date. Sets need ≥ 2 remaining controls.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

import numpy as np

from src import preprocessing as P

EXCLUDE_DAYS = 30


def person_event_jds(source=P.SOURCE_DB) -> dict[str, np.ndarray]:
    out: dict[str, list[float]] = defaultdict(list)
    for name, cat, ev, _bjd, label in P.load_events(source):
        if P.refine_category(cat, label or "") is None:
            continue
        try:
            out[name].append(P.jd_noon(date.fromisoformat(str(ev)[:10])))
        except ValueError:
            continue
    return {k: np.array(v) for k, v in out.items()}


def filter_controls(sets: list[dict], events: dict[str, np.ndarray], exclude_days: float = EXCLUDE_DAYS) -> list[dict]:
    out = []
    for s in sets:
        others = events.get(s["name"])
        mask = list(s["mask"])
        if others is not None and others.size:
            for j in range(1, len(s["jds"])):
                if mask[j] and np.any(np.abs(others - s["jds"][j]) <= exclude_days):
                    mask[j] = False
        if sum(mask[1:]) >= 2:
            out.append({**s, "mask": mask, "complete": all(mask)})
    return out


def matched_sets(halves=(0, 1), categories=P.ALL_CATEGORIES, exclude_days: float = EXCLUDE_DAYS,
                 source=P.SOURCE_DB) -> list[dict]:
    return filter_controls(P.case_control_sets(source, halves=halves, categories=categories),
                           person_event_jds(source), exclude_days)
