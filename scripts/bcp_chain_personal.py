"""
scripts/bcp_chain_personal.py — blind personal test of the BCP chain method (docs/prereg_bcp_chain.md, Test 1).
For each age, show either the real chain story or a decoy (an active house whose lord differs); the person scores
each 0-3 for fit with what happened that year. The key is saved, not printed.

  python scripts/bcp_chain_personal.py --birth "1879-03-14 11:30" --tz 0.6658 --lat 48.4 --lon 9.9833
"""
import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import bcp_chain as B                      # noqa: E402
from src import preprocessing as P                  # noqa: E402
from src.interactive_cli import person_from_birth   # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--birth", required=True, help="YYYY-MM-DD HH:MM local time")
ap.add_argument("--tz", type=float, required=True, help="hours east of UT at birth")
ap.add_argument("--lat", type=float, required=True)
ap.add_argument("--lon", type=float, required=True)
ap.add_argument("--ages", default="18-44", help="first-last age, inclusive")
a = ap.parse_args()

person = person_from_birth(a.birth, a.tz, a.lat, a.lon)
nat = person["natal"]
birth_year = int(a.birth[:4])
chart = B.Chart(int(nat[-1] // 30), {p: int(nat[P.NATAL.index(p)] // 30) for p in
                                     ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")})
rng = random.SystemRandom()
lo, hi = (int(x) for x in a.ages.split("-"))
ages = list(range(lo, hi + 1))
real = set(rng.sample(ages, len(ages) // 2 + 1))
key, out = {}, []
for age in ages:
    act = B.active_house(age)
    if age in real:
        shown = act
    else:
        choices = [h for h in range(1, 13) if chart.lord_of(h) != chart.lord_of(act)]
        shown = rng.choice(choices)
    key[age] = {"real": age in real, "real_active": act, "shown_active": shown}
    y = birth_year + age
    out.append(f"{y}-{str(y + 1)[2:]} (age {age}): {chart.story(shown, age)}")
path = ROOT / "data" / "consultations" / f"bcp_chain_key_{datetime.now():%Y%m%d_%H%M%S}.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(key, indent=1))
print("\n\n".join(out))
print(f"\n(key: {path.name})")
