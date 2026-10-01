"""
scripts/blind_test.py — can the consultation engine describe a specific past period better than decoys?

The user names a period in which something major happened (without saying what). The engine writes a
reading for that period and for decoy periods (same months, other years). Readings are shuffled, labelled
A-D, and stripped of years, dates and ages; the user picks the one that fits. Chance = 1 in the number of
periods. The key is written to a file and not printed.

  python scripts/blind_test.py --birth "1879-03-14 11:30" --tz 0.6658 --lat 48.4 --lon 9.9833 \
      --period 1905-03-01:1905-06-30 --decoy-years 1903 1907 1909
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import consultation_agent as A          # noqa: E402
from src import context_builder as C             # noqa: E402
from src import preprocessing as P               # noqa: E402
from src.interactive_cli import person_from_birth  # noqa: E402

ASK = ("Describe what this person was most likely going through during the four months around this date: "
       "the main life areas, what felt pressured or opened up, and how it may have felt. Do not mention years, "
       "dates or the person's age.")


def scrub(text: str) -> str:
    text = re.sub(r"\b(1[89]\d\d|20\d\d)-\d\d-\d\d\b", "[date]", text)
    text = re.sub(r"\b(1[89]\d\d|20\d\d)s?\b", "[year]", text)
    text = re.sub(r"\b(age[sd]?\s*\d{1,2}|\d{1,2}[- ]?(years?[- ]old|yo)\b|\d{1,2}(st|nd|rd|th)? year of (life|age))",
                  "[age]", text, flags=re.IGNORECASE)
    return text


def reading(person: dict, mid: date, backend) -> dict:
    state = C.state_report(person, P.jd_noon(mid))
    s = A.Consultation(person, state, backend, log=ROOT / "data" / "consultations" / "blind_windows.jsonl")
    out = s.turn(ASK)
    text = "\n".join([out.get("summary", "")] + [f"• {t['theme']} — {t['basis']}" for t in out.get("themes", [])])
    return {"state": state, "raw": out, "shown": scrub(text)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--birth", required=True)
    ap.add_argument("--tz", type=float, required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--period", required=True, help="YYYY-MM-DD:YYYY-MM-DD")
    ap.add_argument("--decoy-years", type=int, nargs="+", required=True)
    ap.add_argument("--model", default="qwen3:8b")
    a = ap.parse_args()
    person = person_from_birth(a.birth, a.tz, a.lat, a.lon)
    start, end = (date.fromisoformat(x) for x in a.period.split(":"))
    mid = start + (end - start) / 2
    periods = [("target", mid)] + [(f"decoy {y}", mid.replace(year=y)) for y in a.decoy_years]
    random.SystemRandom().shuffle(periods)
    backend = A.OllamaBackend(a.model)
    labels = "ABCDEFGH"
    key, shown = {}, []
    for label, (kind, d) in zip(labels, periods):
        r = reading(person, d, backend)
        key[label] = {"period": kind, "mid_date": d.isoformat(), "raw": r["raw"]}
        shown.append(f"===== Reading {label} =====\n{r['shown']}\n")
    out = ROOT / "data" / "consultations" / f"blind_key_{datetime.now():%Y%m%d_%H%M%S}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(key, indent=2, default=str))
    print("\n".join(shown))
    print(f"(key saved to {out.name}; chance of picking the target at random = 1 in {len(periods)})")


if __name__ == "__main__":
    main()
