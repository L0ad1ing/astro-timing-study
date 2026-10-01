"""
src/preprocessing.py — from the Astro-Databank extract to case-control sets.

Ported from the Abraxas research code that produced every result so far (cognition/team/lab.py,
event_model*.py, window_test.py; Parse/etl_pipeline.py for the parsers). tests/test_parity.py checks
that this module selects the same sets.

Pipeline:
  1. Birth data: coordinates and the timezone stated by Astro-Databank (parse_coordinates,
     parse_utc_offset). The old parser read "73w4859" / "10e0" as 0.0 (28% of people had wrong
     birth times); fixed 2026-09-30.
  2. Events: one row per person, event type and date; scraped non-events removed (EVENT_FILTER);
     the source's "Death" split into own death / death of a relative (refine_category); events
     within 1.5 days of the birthday dropped (placeholder dates: 7% of events vs <1% expected).
  3. Case-control sets: event date + the same calendar date -3, -1, +1, +3 years (own death: -4..-1).
     Controls before age 1, after the person's recorded death, or after STUDY_CUTOFF are dropped; a set
     needs the case and at least two controls. `complete` marks sets with every control intact.
  4. Splits: half = crc32(name) & 1 (half 1 is RETIRED — evaluated too often), fold = (crc32 >> 1) % 5.

Event dates have no time of day: event-date positions are computed at noon UT. Birth moments are exact.
"""
from __future__ import annotations

import math
import os
import re
import sqlite3
import zlib
from datetime import date, timedelta
from pathlib import Path

import numpy as np

SOURCE_DB = Path(os.environ.get("ASTRO_SOURCE_DB", Path(__file__).resolve().parents[1] / "data" / "astro_master_data.db"))
STUDY_CUTOFF = date(2026, 9, 30)
YEAR = 365.2422
NATAL = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ascendant"]

EVENT_FILTER = """
  event_label != 'born on'
  AND event_label NOT LIKE '%This page was last edited%'
  AND event_label NOT LIKE '% relationship with %'
  AND event_label NOT LIKE '%compare to chart of%'
  AND event_label NOT LIKE '%role played of/by%'
  AND event_label NOT LIKE '%(born%'
  AND event_label NOT LIKE 'Update of%'
  AND event_label NOT LIKE '%(has as) %'
  AND event_label NOT LIKE '%(born)'
"""
CATEGORIES = ["Death", "Marriage", "Arrest", "Career_Peak", "Divorce", "Illness", "Birth_Child", "Accident",
              "Death_of_relative"]

# Event types added 2026-09-30 from the source's "Other" bucket, by exact Astro-Databank label.
NEW_EVENT_LABELS = {
    "Work : Prize": "Prize",
    "Work : New Job": "Job_Start", "Work : New Career": "Job_Start", "Work : Start Business": "Job_Start",
    "Work : Fired/Laid off/Quit": "Job_End", "Work : Retired": "Job_End",
    "Crime : Trial dates": "Trial", "Crime : Law suit": "Trial",
    "Relationship : Begin significant relationship": "Relationship_Begin",
    "Relationship : Meet a significant person": "Relationship_Begin",
    "Relationship : End significant relationship": "Relationship_End",
}
NEW_CATEGORIES = ["Prize", "Job_Start", "Job_End", "Trial", "Relationship_Begin", "Relationship_End"]
ALL_CATEGORIES = CATEGORIES + NEW_CATEGORIES
MACRO_THEMES = {"Acute_Crisis": ["Arrest", "Accident", "Illness"]}

_RELATIVE_DEATH = re.compile(r"death of |(his|her) (father|mother|wife|husband|son|daughter|brother|sister) died",
                             re.IGNORECASE)
_NOT_A_DEATH = re.compile(r"sentenced to death|suicide attempt", re.IGNORECASE)
VIOLENT_DEATH = re.compile(r"accident|homicide|suicide|war or terrorism|execution|killed|murdered|assassinat",
                           re.IGNORECASE)
NATURAL_DEATH = re.compile(r"by disease|heart attack|of cancer|natural causes|old age", re.IGNORECASE)


# ── Parsing (Astro-Databank page text) ───────────────────────────────────────

def _dms(deg: str, tail: str) -> float:
    tail = tail or ""
    minutes = float(tail[:2]) if tail else 0.0
    seconds = float(tail[2:4]) if len(tail) >= 4 else 0.0
    return float(deg) + minutes / 60.0 + seconds / 3600.0


def parse_coordinates(text: str) -> tuple[float, float]:
    """'..., 40n42, 73w4859 Timezone ...' -> (40.7, -73.8164). (0, 0) if absent."""
    m = re.search(r"(\d{1,2})([ns])(\d{0,4})\s*,\s*(\d{1,3})([ew])(\d{0,4})\s+Timezone", text, re.IGNORECASE)
    if m:
        lat = _dms(m.group(1), m.group(3)) * (-1 if m.group(2).lower() == "s" else 1)
        lon = _dms(m.group(4), m.group(6)) * (-1 if m.group(5).lower() == "w" else 1)
        return lat, lon
    lat_m = re.search(r"\b(\d{1,2})([ns])(\d{1,4})\b", text, re.IGNORECASE)
    lon_m = re.search(r"\b(\d{1,3})([ew])(\d{1,4})\b", text, re.IGNORECASE)
    lat = _dms(lat_m.group(1), lat_m.group(3)) * (-1 if lat_m.group(2).lower() == "s" else 1) if lat_m else 0.0
    lon = _dms(lon_m.group(1), lon_m.group(3)) * (-1 if lon_m.group(2).lower() == "w" else 1) if lon_m else 0.0
    return lat, lon


def parse_utc_offset(text: str) -> float | None:
    """Hours east of UT: 'h4w' -> -4, 'h5e30' -> +5.5; 'm12e35' (local mean time) -> +(12 deg 35')/15."""
    m = re.search(r"Timezone\s+(?:\S+\s+)?([hm])(\d{1,3})([ew])(\d{0,2})\b", text)
    if not m:
        return None
    kind, a, direction, b = m.groups()
    value = float(a) + (float(b) / 60.0 if b else 0.0)
    return (1 if direction == "e" else -1) * (value if kind == "h" else value / 15.0)


# ── Events ───────────────────────────────────────────────────────────────────

def refine_category(category: str | None, label: str) -> str | None:
    """The source category, corrected: 'Death' means the person's own death only; labelled events in
    'Other' get their own type (NEW_EVENT_LABELS)."""
    if category == "Other":
        return NEW_EVENT_LABELS.get(label.strip(), "Other")
    if category != "Death":
        return category
    if _NOT_A_DEATH.search(label):
        return None
    if "non-fatal" in label.lower():
        return "Accident"
    if _RELATIVE_DEATH.search(label):
        return "Death_of_relative"
    return "Death"


def jd_noon(d: date) -> float:
    return d.toordinal() + 1721424.5 + 0.5


def is_birthday_placeholder(age_years: float) -> bool:
    """Within 1.5 days of a birthday (age in YEAR-length years)."""
    return abs(age_years - round(age_years)) * YEAR < 1.5


def split_ids(name: str) -> tuple[int, int]:
    h = zlib.crc32(name.encode("utf-8"))
    return h & 1, (h >> 1) % 5


def load_people(source: Path = SOURCE_DB) -> dict[str, dict]:
    """Birth record per person: natal longitudes (NATAL order; Ascendant NaN if the time is unknown),
    rating, birth place."""
    ncols = ", ".join(f"natal_{p}_deg" for p in NATAL[:-1])
    people = {}
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as c:
        for r in c.execute(f"SELECT name, {ncols}, natal_asc_deg, birth_time_known, rodden_rating, birth_lat, birth_lon "
                           "FROM ml_features WHERE event_label = 'born on'"):
            vals = [float(v) if v is not None else math.nan for v in r[1:10]]
            if not r[10]:
                vals[-1] = math.nan
            people[r[0]] = {"natal": np.array(vals), "rating": r[11],
                            "lat": None if r[12] is None else float(r[12]),
                            "lon": None if r[13] is None else float(r[13])}
    return people


def load_events(source: Path = SOURCE_DB) -> list[tuple]:
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as c:
        return c.execute(f"SELECT name, event_category, event_date, birth_jd, event_label FROM ml_features "
                         f"WHERE {EVENT_FILTER} AND event_category IS NOT NULL "
                         "AND event_date IS NOT NULL AND birth_jd IS NOT NULL").fetchall()


def death_dates(rows: list[tuple]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, cat, ev, _, label in rows:
        if refine_category(cat, label or "") == "Death":
            try:
                j = jd_noon(date.fromisoformat(str(ev)[:10]))
            except ValueError:
                continue
            out[name] = min(j, out.get(name, j))
    return out


def control_offsets(category: str) -> tuple[int, ...]:
    return (-4, -3, -2, -1) if category == "Death" else (-3, -1, 1, 3)


def case_control_sets(source: Path = SOURCE_DB, halves=(0,), categories=CATEGORIES) -> list[dict]:
    """Case-control sets, one per usable (person, event type, date). Half 1 is retired: pass
    halves=(1,) only for lock-box-free diagnostics that were pre-registered."""
    people = load_people(source)
    rows = load_events(source)
    died = death_dates(rows)
    cutoff = jd_noon(STUDY_CUTOFF)
    seen, out = set(), []
    for name, cat, ev, bjd, label in rows:
        cat = refine_category(cat, label or "")
        if cat not in categories or name not in people:
            continue
        half, fold = split_ids(name)
        if half not in halves:
            continue
        nat = people[name]["natal"]
        ev = str(ev)[:10]
        if (name, cat, ev) in seen or np.isnan(nat[:8]).any():
            continue
        try:
            d = date.fromisoformat(ev)
        except ValueError:
            continue
        age = (jd_noon(d) - float(bjd)) / YEAR
        if not 1 <= age <= 110 or is_birthday_placeholder(age):
            continue
        seen.add((name, cat, ev))
        dates = [d] + [d + timedelta(days=round(k * YEAR)) for k in control_offsets(cat)]
        last = min(died.get(name, cutoff), cutoff)
        ok = [True] + [(jd_noon(x) - float(bjd)) / YEAR >= 1 and jd_noon(x) <= last for x in dates[1:]]
        if sum(ok) < 3:
            continue
        out.append({"name": name, "category": cat, "half": half, "fold": fold,
                    "jds": [jd_noon(x) for x in dates], "mask": ok, "complete": all(ok),
                    "birth_jd": float(bjd), "natal": nat, "rating": people[name]["rating"],
                    "death_jd": died.get(name), "label": (label or "").strip(),
                    "lat": people[name]["lat"], "lon": people[name]["lon"]})
    return out
