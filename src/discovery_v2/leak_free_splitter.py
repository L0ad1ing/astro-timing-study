"""
src/discovery_v2/leak_free_splitter.py — a holdout that shares no person, year-month or date with training.

Test = sets whose event falls in TEST_MONTHS (Feb, May, Aug, Nov); training = the other eight months. Every date in a
set shares the event's calendar date (controls are whole years away), so the partitions cannot share a year-month or
an exact date — the leak that made harmonic "candidates" look real (shared award nights, co-defendants, spouses).
Controls are offset by round(k × 365.2422) days and can slip one day across a month boundary: a set whose dates fall
on both sides is dropped. A person is kept on the side of their earliest event; their sets on the other side are dropped.
"""
from __future__ import annotations

import numpy as np

from src import features as F

TEST_MONTHS = (2, 5, 8, 11)


def ymd(jd: float) -> tuple[int, int, int]:
    swe, _ = F._swe()
    y, m, d, _h = swe.revjul(jd)
    return int(y), int(m), int(d)


def set_side(s: dict) -> str:
    sides = {"test" if ymd(jd)[1] in TEST_MONTHS else "train" for jd, ok in zip(s["jds"], s["mask"]) if ok}
    return sides.pop() if len(sides) == 1 else "drop"


def split(sets: list[dict]) -> tuple[np.ndarray, np.ndarray, dict]:
    side = [set_side(s) for s in sets]
    home: dict[str, str] = {}
    for i in sorted(range(len(sets)), key=lambda i: sets[i]["jds"][0]):
        if side[i] != "drop":
            home.setdefault(sets[i]["name"], side[i])
    train = np.array([i for i, s in enumerate(sets) if side[i] == "train" and home.get(s["name"]) == "train"], int)
    test = np.array([i for i, s in enumerate(sets) if side[i] == "test" and home.get(s["name"]) == "test"], int)
    info = {"straddling_month_boundary": side.count("drop"),
            "person_on_other_side": len(sets) - side.count("drop") - len(train) - len(test)}
    return train, test, info


def audit(sets: list[dict], train: np.ndarray, test: np.ndarray) -> dict:
    def dates(idx):
        return {ymd(jd) for i in idx for jd, ok in zip(sets[i]["jds"], sets[i]["mask"]) if ok}
    dtr, dte = dates(train), dates(test)
    return {"shared_persons": len({sets[i]["name"] for i in train} & {sets[i]["name"] for i in test}),
            "shared_year_months": len({d[:2] for d in dtr} & {d[:2] for d in dte}),
            "shared_dates": len(dtr & dte)}
