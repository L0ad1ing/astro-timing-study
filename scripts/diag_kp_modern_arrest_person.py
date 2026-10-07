"""POST-HOC: half-1 KP-modern Arrest result with a bootstrap clustered by person (several arrests of one person are
not independent). Uses the cached phase-1 results."""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import run_bphs_engine as RB
from src import models as Mo
from src.rules import engine as E


def main():
    src = ("KP modern",)
    rules = [r for r in E.load_rules()[0] if r["kind"] == "timing" and RB._src_ok(r, src)]
    rel = RB.relevance(rules)
    dirs = np.array([1 if r["predicts"]["direction"] == "+" else -1 for r in rules], np.float32)
    S1, F1 = RB.compute(1, 4, 0, src)
    ids = RB.sets_of("Arrest", S1)
    Sa, Ma, ka = RB.scores(ids, S1, F1, "Arrest", rel, "actual", "weighted", dirs)
    Sm, Mm, km = RB.scores(ids, S1, F1, "Arrest", rel, "mismatched", "weighted", dirs)
    k = ka & km
    ca, cm = Mo.per_set_c(Sa[k], Ma[k]), Mo.per_set_c(Sm[k], Mm[k])
    names = np.array([S1[i]["name"] for i in np.array(ids)[k]])
    un = np.unique(names)
    g = {u: np.where(names == u)[0] for u in un}
    rng = np.random.default_rng(2)
    bd, bc = [], []
    for _ in range(2000):
        p = np.concatenate([g[u] for u in rng.choice(un, len(un))])
        bd.append((ca[p] - cm[p]).mean()); bc.append(ca[p].mean())
    out = {"sets": int(k.sum()), "people": int(len(un)), "max_sets_one_person": int(max(len(v) for v in g.values())),
           "c_actual": round(float(ca.mean()), 4), "c_ci_person_clustered": [round(float(np.percentile(bc, q)), 4) for q in (2.5, 97.5)],
           "dC": round(float((ca - cm).mean()), 4), "dC_ci_person_clustered": [round(float(np.percentile(bd, q)), 4) for q in (2.5, 97.5)]}
    p = ROOT / "docs" / "results_kp_modern_arrest_diagnostics.json"
    d = json.loads(p.read_text()); d["half1_person_clustered"] = out; p.write_text(json.dumps(d, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
