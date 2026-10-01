"""
scripts/bcp_chain_test.py — The author's BCP chain method on Astro-Databank (docs/prereg_bcp_chain.md, Test 2).
Event year vs the same person's years -3, -1, +1, +3: is the event's house closer to the MAIN story?
"""
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import bcp_chain as B                # noqa: E402
from src import preprocessing as P            # noqa: E402
from src import models as Mo                  # noqa: E402

TARGETS = {"Marriage": [7], "Divorce": [7], "Birth_Child": [5], "Career_Peak": [10], "Arrest": [12, 6], "Illness": [6],
           "Accident": [8], "Prize": [10, 11], "Job_Start": [10], "Job_End": [10, 12], "Trial": [6],
           "Relationship_Begin": [7, 5], "Relationship_End": [7]}
RELATIVE = {"father": [9], "mother": [4], "mate": [7], "child": [5], "sibling": [3]}


def targets_for(s):
    if s["category"] == "Death_of_relative":
        low = s["label"].lower()
        return next((v for k, v in RELATIVE.items() if f"death of {k}" in low), None), \
            next((f"Death of {k}" for k in RELATIVE if f"death of {k}" in low), None)
    return TARGETS.get(s["category"]), s["category"]


def main():
    running = "--running-year" in sys.argv
    active = (lambda a: (a % 12) + 1) if running else B.active_house
    cats = list(TARGETS) + ["Death_of_relative"]
    sets = P.case_control_sets(P.SOURCE_DB, halves=(0, 1), categories=cats)
    charts, per = {}, {}
    for s in sets:
        nat = s["natal"]
        asc = nat[P.NATAL.index("Ascendant")]
        if math.isnan(asc):
            continue
        tg, label = targets_for(s)
        if not tg:
            continue
        if s["name"] not in charts:
            charts[s["name"]] = B.Chart(int(asc // 30), {p: int(nat[P.NATAL.index(p)] // 30) for p in
                                                         ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")})
        ch = charts[s["name"]]
        ages = [int((jd - s["birth_jd"]) / 365.2425) for jd in s["jds"]]
        sc = [ch.score(active(a), tg) for a in ages]
        main = [active(a) in tg for a in ages]
        ctrl = [i for i in range(1, len(ages)) if s["mask"][i]]
        wins = sum(1.0 if sc[0] > sc[i] else 0.5 if sc[0] == sc[i] else 0.0 for i in ctrl) / len(ctrl)
        d = per.setdefault(label, {"c": [], "main_event": [], "main_ctrl": []})
        d["c"].append(wins)
        d["main_event"].append(main[0])
        d["main_ctrl"].append(np.mean([main[i] for i in ctrl]))
    report = {"run_at": datetime.now().isoformat(), "prereg": "docs/prereg_bcp_chain.md", "convention": "running year" if running else "completed age", "results": {}}
    for label, d in sorted(per.items(), key=lambda kv: -len(kv[1]["c"])):
        c = np.array(d["c"])
        r = {"events": len(c), "c": round(float(c.mean()), 4), "ci": Mo.bootstrap_ci(c),
             "main_story_event_year": round(float(np.mean(d["main_event"])), 4),
             "main_story_control_years": round(float(np.mean(d["main_ctrl"])), 4)}
        report["results"][label] = r
        print(f"{label:22s} n={r['events']:6d}  P(event year closer) {r['c']:.3f} {r['ci']} | target is MAIN story: "
              f"event year {r['main_story_event_year']:.3f} vs other years {r['main_story_control_years']:.3f}", flush=True)
    out = ROOT / "docs" / f"results_bcp_chain{'_running' if running else ''}_{datetime.now():%Y%m%d_%H%M}.json"
    out.write_text(json.dumps(report, indent=2))
    print("written", out)


if __name__ == "__main__":
    main()
