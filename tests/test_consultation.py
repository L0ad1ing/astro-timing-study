"""tests/test_consultation.py — state report facts and the consultation agent's guardrails."""
import json
from datetime import date

import numpy as np

from src import consultation_agent as A
from src import context_builder as C
from src import features as F
from src import preprocessing as P
from tests.test_rao import _natal

WED = P.jd_noon(date(1975, 10, 11))


def _hillary():
    swe, _ = F._swe()
    bjd = swe.julday(1947, 10, 27, 2.0)
    return {"name": "Hillary (book data)", "natal": _natal(bjd, 41.85, -87.65), "birth_jd": bjd,
            "lat": 41.85, "lon": -87.65, "gender": "F"}


def test_state_report_facts():
    s = C.state_report(_hillary(), WED)
    v = s["vimshottari"]
    assert (v["maha"]["lord"], v["antar"]["lord"], v["pratyantar"]["lord"]) == ("Mercury", "Jupiter", "Mercury")
    assert v["antar"]["from"] <= s["date"] < v["antar"]["to"]
    assert s["natal"]["lagna"] == "Gemini" and s["age"] > 27
    assert s["bhrigu_chakra"]["active_house"] == 3                  # completed age 27 -> ((27-1) % 12) + 1
    assert s["profection"]["sign"] == "Virgo"                       # Gemini + 27 signs
    assert s["profection"]["lord_of_the_year"] == "Mercury"
    assert s["sade_sati"]["phase"] in (None, "rising", "peak", "setting")
    json.dumps(s)                                                   # serializable


def test_vimshottari_periods_agree_with_features():
    rng = np.random.default_rng(0)
    for _ in range(50):
        moon, bjd = rng.uniform(0, 360), 2440000.0
        jd = bjd + rng.uniform(1, 30000)
        p = C.vimshottari_periods(moon, bjd, jd)
        assert (p["maha"]["lord"], p["antar"]["lord"], p["pratyantar"]["lord"]) == \
            tuple(F.DASHA_LORDS[i] for i in F.vimshottari_at(moon, bjd, jd))


class FakeLLM:
    def __init__(self, out):
        self.out, self.prompts = out, []

    def chat(self, system, user, schema):
        self.prompts.append((system, user))
        return json.loads(json.dumps(self.out))


def test_agent_drops_invented_dates_caps_confidence_and_logs(tmp_path):
    state = C.state_report(_hillary(), WED)
    good = state["vimshottari"]["antar"]
    fake = FakeLLM({"summary": "s", "questions": ["q?"],
                    "themes": [{"theme": "t", "basis": "b", "cites": ["vim-1", "made-up"]}],
                    "windows": [{"from": good["from"], "to": good["to"], "claim": "c", "basis": "AD", "source": "chart", "confidence": 0.9},
                                {"from": "1975-10-01", "to": "1975-10-20", "claim": "invented", "basis": "?", "source": "chart", "confidence": 0.8}]})
    s = A.Consultation(_hillary(), state, fake, log=tmp_path / "p.jsonl")
    out = s.turn()
    assert [w["claim"] for w in out["windows"]] == ["c"] and out["windows"][0]["confidence"] == 0.3
    assert len(out["dropped_windows"]) == 1
    assert out["themes"][0]["cites"] == ["vim-1"]
    logged = [json.loads(l) for l in (tmp_path / "p.jsonl").read_text().splitlines()]
    assert len(logged) == 1 and logged[0]["outcome"] is None
    system, prompt = fake.prompts[0]
    assert "EVIDENCE" in prompt and "have not shown timing power" in prompt and "STATE REPORT" in prompt


def test_user_notes_reach_the_model_and_retrieval():
    state = C.state_report(_hillary(), WED)
    fake = FakeLLM({"summary": "", "themes": [], "windows": [], "questions": []})
    s = A.Consultation(_hillary(), state, fake)
    s.turn("I am thinking about marriage")
    assert "WHAT THE USER HAS SAID" in fake.prompts[0][1]
    ids = {r["id"] for r in A.retrieve(state, A.load_kb(), "marriage")["rules"]}
    assert "vim-2" in ids and "bcp-1" in ids


def test_source_cannot_be_user_before_the_user_speaks(tmp_path):
    state = C.state_report(_hillary(), WED)
    good = state["vimshottari"]["antar"]
    fake = FakeLLM({"summary": "", "themes": [], "questions": [],
                    "windows": [{"from": good["from"], "to": good["to"], "claim": "c", "basis": "b", "source": "user", "confidence": 0.2}]})
    out = A.Consultation(_hillary(), state, fake, log=tmp_path / "p.jsonl").turn()
    assert out["windows"][0]["source"] == "chart"
