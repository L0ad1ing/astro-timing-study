"""
src/interactive_cli.py — a multi-turn consultation in the terminal.

  python -m src.interactive_cli --name "Clinton, Hillary" --date 1975-10-11
  python -m src.interactive_cli --birth "1879-03-14 11:30" --tz 0.6658 --lat 48.4 --lon 9.9833 --gender M

Shows the computed state, then the consultation; type a reply to continue, "state" to see the facts again,
"quit" to end. Dated windows are logged to data/consultations/predictions.jsonl for later scoring.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date, datetime

from src import consultation_agent as A
from src import context_builder as C
from src import features as F
from src import preprocessing as P


def person_from_dataset(name: str) -> dict:
    people = P.load_people(P.SOURCE_DB)
    if name not in people:
        raise SystemExit(f"{name!r} not found (use the Astro-Databank form, e.g. 'Clinton, Hillary')")
    with sqlite3.connect(f"file:{P.SOURCE_DB}?mode=ro", uri=True) as c:
        bjd = c.execute("SELECT birth_jd FROM ml_features WHERE name = ? AND event_label = 'born on'", (name,)).fetchone()[0]
    p = people[name]
    return {"name": name, "natal": p["natal"], "birth_jd": float(bjd), "lat": p["lat"], "lon": p["lon"]}


def person_from_birth(birth: str, tz: float, lat: float, lon: float) -> dict:
    swe, fl = F._swe()
    dt = datetime.strptime(birth, "%Y-%m-%d %H:%M")
    bjd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 - tz)
    ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
           "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    natal = [swe.calc_ut(bjd, ids[p], fl)[0][0] for p in P.NATAL[:-1]]
    natal.append(swe.houses_ex(bjd, lat, lon, b"W", swe.FLG_SIDEREAL)[1][0])
    import numpy as np
    return {"name": "you", "natal": np.array(natal), "birth_jd": bjd, "lat": lat, "lon": lon}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name")
    ap.add_argument("--birth", help="YYYY-MM-DD HH:MM local time")
    ap.add_argument("--tz", type=float, default=0.0, help="hours east of UT at birth")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--gender", choices=["M", "F"])
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--model", default="qwen3:8b")
    a = ap.parse_args()
    person = person_from_dataset(a.name) if a.name else person_from_birth(a.birth, a.tz, a.lat, a.lon)
    person["gender"] = a.gender
    state = C.state_report(person, P.jd_noon(date.fromisoformat(a.date)))
    print(json.dumps(state, indent=1))
    session = A.Consultation(person, state, A.OllamaBackend(a.model))
    print("\n" + A.render(session.turn()))
    while True:
        try:
            reply = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if reply.lower() in ("quit", "exit", "q"):
            break
        if reply.lower() == "state":
            print(json.dumps(state, indent=1))
            continue
        print("\n" + A.render(session.turn(reply)))


if __name__ == "__main__":
    main()
