"""Half-1 check of the KP-modern Arrest near-miss (docs/prereg_kp_modern_arrest_confirm.md). Usage:
python scripts/confirm_kp_modern_arrest.py [--workers N]"""
import argparse, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import run_bphs_engine as RB
from src.rules import engine as E

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=4); a = ap.parse_args()
    src = ("KP modern",)
    rules = [r for r in E.load_rules()[0] if r["kind"] == "timing" and RB._src_ok(r, src)]
    t0 = time.time()
    sets, fired = RB.compute(1, a.workers, 0, src)
    r = RB.analyse(sets, fired, rules, ["Arrest"], 1)["Arrest"]
    w = r["weighted"]
    ok = w["delta"]["ci95"][0] > 0 and w["c_actual_ci"][0] > 0.5 and w["placebo_delta"]["ci95"][0] <= 0
    out = {"run_at": datetime.now(timezone.utc).isoformat(), "prereg": "docs/prereg_kp_modern_arrest_confirm.md",
           "timing_rules": len(rules), "half": 1, "Arrest": r, "confirmed": bool(ok), "seconds": round(time.time() - t0)}
    p = ROOT / "docs" / f"results_kp_modern_arrest_confirm_{datetime.now():%Y%m%d_%H%M}.json"
    p.write_text(json.dumps(out, indent=2))
    print(f"Arrest half 1: n={w['n']} C {w['c_actual']} {w['c_actual_ci']} mismatched {w['c_mismatched']} dC {w['delta']} "
          f"placebo {w['placebo_delta']['ci95']} -> {'CONFIRMED' if ok else 'not confirmed'}; written {p}")
