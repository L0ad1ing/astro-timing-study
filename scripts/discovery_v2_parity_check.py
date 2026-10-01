"""
scripts/discovery_v2_parity_check.py — POST-HOC (not pre-registered) check of the 17 Prize "survivors".

All 17 hinge on the Mars-Saturn angle (synodic period 2.01 years) or slow sky pairs. Controls sit at odd year offsets
(±1, ±3), so a ~2-year cycle is in the opposite phase on every control, and any even/odd-year clustering of events
becomes a huge "effect". Prize events are 64.5% in even years (Olympic medals: 1996, 2000, 2008, 2012, 2021).
This re-tests each surviving rule on the same held-out sets, adjusting for age plus the calendar-year parity and
year-mod-4 phase of every date (the Olympic calendar), instead of the pre-registered LightGBM baseline.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import harmonic_features as H                   # noqa: E402
from src import models as Mo                             # noqa: E402
from src import preprocessing as P                       # noqa: E402
from src.discovery_v2 import leak_free_splitter as S     # noqa: E402
from src.discovery_v2 import matched_controls as MC      # noqa: E402
from src.discovery_v2 import rule_evaluator as E         # noqa: E402


# Olympic Games (start, end), summer and winter 1948-2022, from memory (approximate: ±3 days slack in games()).
GAMES = [("1948-01-30", "1948-02-08"), ("1948-07-29", "1948-08-14"), ("1952-02-14", "1952-02-25"),
         ("1952-07-19", "1952-08-03"), ("1956-01-26", "1956-02-05"), ("1956-11-22", "1956-12-08"),
         ("1960-02-18", "1960-02-28"), ("1960-08-25", "1960-09-11"), ("1964-01-29", "1964-02-09"),
         ("1964-10-10", "1964-10-24"), ("1968-02-06", "1968-02-18"), ("1968-10-12", "1968-10-27"),
         ("1972-02-03", "1972-02-13"), ("1972-08-26", "1972-09-11"), ("1976-02-04", "1976-02-15"),
         ("1976-07-17", "1976-08-01"), ("1980-02-13", "1980-02-24"), ("1980-07-19", "1980-08-03"),
         ("1984-02-08", "1984-02-19"), ("1984-07-28", "1984-08-12"), ("1988-02-13", "1988-02-28"),
         ("1988-09-17", "1988-10-02"), ("1992-02-08", "1992-02-23"), ("1992-07-25", "1992-08-09"),
         ("1994-02-12", "1994-02-27"), ("1996-07-19", "1996-08-04"), ("1998-02-07", "1998-02-22"),
         ("2000-09-15", "2000-10-01"), ("2002-02-08", "2002-02-24"), ("2004-08-13", "2004-08-29"),
         ("2006-02-10", "2006-02-26"), ("2008-08-08", "2008-08-24"), ("2010-02-12", "2010-02-28"),
         ("2012-07-27", "2012-08-12"), ("2014-02-07", "2014-02-23"), ("2016-08-05", "2016-08-21"),
         ("2018-02-09", "2018-02-25"), ("2021-07-23", "2021-08-08"), ("2022-02-04", "2022-02-20")]


def games(jd: float, slack: int = 3) -> bool:
    from datetime import date
    return any(P.jd_noon(date.fromisoformat(a)) - slack <= jd <= P.jd_noon(date.fromisoformat(b)) + slack for a, b in GAMES)


def main() -> None:
    found = json.loads((ROOT / "src" / "discovery_v2" / "discovered_rules.json").read_text())
    hf = H.HarmonicFeaturizer()
    idx = {n: i for i, n in enumerate(hf.names)}
    sets = [s for s in MC.matched_sets((0, 1), ["Prize"]) if not math.isnan(s["natal"][P.NATAL.index("Ascendant")])]
    _, te_i, _ = S.split(sets)
    te = [sets[i] for i in te_i]
    X, M = Mo.matrix(te, featurizer=hf)
    years = np.array([[S.ymd(jd)[0] for jd in s["jds"]] for s in te])
    age = np.array([[(jd - s["birth_jd"]) / 365.2422 for jd in s["jds"]] for s in te])
    cal = np.stack([age, (years % 2 == 0)] + [(years % 4 == k) for k in (1, 2, 3)], axis=2).astype(float)
    # second adjustment: one indicator per calendar year with >= 10 valid dates (rarer years pooled as reference)
    vals, counts = np.unique(years[M], return_counts=True)
    fe = np.stack([age] + [(years == y) for y in vals[counts >= 10]], axis=2).astype(float)
    # third: the Olympic calendar by season — year-mod-4 phase separately for each event month (Feb winter Games,
    # Jul/Aug summer Games); the month is the same for every date in a set
    months = np.array([S.ymd(s["jds"][0])[1] for s in te])
    for m in S.TEST_MONTHS:
        sel = months == m
        ev_y = years[sel, 0]
        print(f"test events in month {m:2d}: n={sel.sum():4d}  year mod 4 = 0/1/2/3: "
              + " ".join(f"{np.mean(ev_y % 4 == k):.2f}" for k in range(4)))
    season = [((years % 4 == k) & (months[:, None] == m)) for m in S.TEST_MONTHS for k in (1, 2, 3)]
    fe = np.concatenate([fe, np.stack(season, axis=2).astype(float)], axis=2)
    # fourth: drop every set whose event falls during an Olympic Games (dates from memory, ±3 days of slack)
    on_games = np.array([games(s["jds"][0]) for s in te])
    print(f"test prize events during an Olympic Games: {on_games.sum()} of {len(te)} "
          f"(their control dates during Games: {sum(games(jd) for s in te for jd in s['jds'][1:])})")
    keep = ~on_games
    out = []
    for r in found["rules"]:
        rule = tuple((idx[n], op, t) for n, op, t in r["conditions"])
        ex = E.exposure(X, rule).astype(float)[:, :, None]
        fit = E.clogit(np.concatenate([ex, cal], axis=2), M)
        fit_fe = E.clogit(np.concatenate([ex, fe], axis=2), M)
        fit_ng = E.clogit(np.concatenate([ex[keep], cal[keep]], axis=2), M[keep])
        out.append({"text": r["text"], "pre_registered_p": r["test_p"],
                    "parity_adjusted_beta": round(float(fit["beta"][0]), 4), "parity_adjusted_p": float(fit["p"][0]),
                    "year_and_season_fe_beta": round(float(fit_fe["beta"][0]), 4),
                    "year_and_season_fe_p": float(fit_fe["p"][0]),
                    "no_games_events_beta": round(float(fit_ng["beta"][0]), 4), "no_games_events_p": float(fit_ng["p"][0])})
        print(f"p {r['test_p']:.2g} -> parity {fit['p'][0]:.3g} -> year+season FE {fit_fe['p'][0]:.3g} -> "
              f"Games events dropped {fit_ng['p'][0]:.3g} (beta {r['test_beta']:+.2f} -> {fit_ng['beta'][0]:+.2f}) | "
              f"{r['text'][:60]}", flush=True)
    n = found["n_rules_tested"]
    still = {k: sum(o[k] < 0.01 / n for o in out) for k in ("parity_adjusted_p", "year_and_season_fe_p", "no_games_events_p")}
    print(f"\nstill past the Bonferroni bar ({0.01 / n:.2g}) out of {len(out)}: parity {still['parity_adjusted_p']}, "
          f"year + season fixed effects {still['year_and_season_fe_p']}, Olympic-Games events dropped "
          f"{still['no_games_events_p']}")
    (ROOT / "docs" / "results_discovery_v2_parity_check.json").write_text(
        json.dumps({"post_hoc": True, "test_sets": len(te), "year_indicators": int((counts >= 10).sum()), "rules": out,
                    "still_surviving": still}, indent=2))


if __name__ == "__main__":
    main()
