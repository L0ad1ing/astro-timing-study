"""
src/consultation_agent.py — an LLM consultation grounded in the computed state report and the knowledge base.

Design (honesty is structural, not a disclaimer):
  - The model sees only computed facts (src/context_builder.state_report), retrieved knowledge-base passages
    (each with an id it must cite) and knowledge_base/evidence.md: what this study's tests found. It is told
    to present themes as possibilities, never as predictions of events.
  - Any dated window must use dates that appear in the state report (dasha boundaries, BCP trigger dates,
    the profection year). Windows with dates that are not in the report are dropped in code.
  - Every window the user sees is logged to data/consultations/predictions.jsonl with its date range, so it
    can be scored when it closes. Windows narrowed by what the user said are marked source="user".
  - The model runs locally through Ollama by default (no cost); any backend with .chat(system, user, schema)
    works (tests use a fake).
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

KB = Path(__file__).resolve().parent / "knowledge_base"
LOG = Path(__file__).resolve().parents[1] / "data" / "consultations" / "predictions.jsonl"

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "themes": {"type": "array", "items": {"type": "object", "properties": {
            "theme": {"type": "string"}, "basis": {"type": "string"}, "cites": {"type": "array", "items": {"type": "string"}}},
            "required": ["theme", "basis", "cites"]}},
        "windows": {"type": "array", "items": {"type": "object", "properties": {
            "from": {"type": "string"}, "to": {"type": "string"}, "claim": {"type": "string"},
            "basis": {"type": "string"}, "source": {"type": "string", "enum": ["chart", "user"]},
            "confidence": {"type": "number"}},
            "required": ["from", "to", "claim", "basis", "source", "confidence"]}},
        "questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "themes", "windows", "questions"],
}

SYSTEM = """You are an astrological consultant working from COMPUTED FACTS only.
Rules:
- Use only the STATE REPORT for any sign, house, dasha, date or transit. Never state one from memory.
- Ground each theme in the state report and cite the knowledge-base passage ids you used.
- Present themes as possibilities to reflect on, not predictions of events. Read EVIDENCE: these techniques
  have not shown timing power in testing, so say so plainly whenever you give a dated window.
- Dated windows may only use dates that appear in the STATE REPORT (dasha from/to dates, Bhrigu Chakra trigger
  dates). Keep confidence at 0.3 or below unless the evidence section justifies more (it does not).
- If a window is narrowed because of something the user told you, set source to "user" and say so.
- End with one or two questions that would help the person reflect; do not fish for facts to feed back as
  if the chart revealed them."""


class OllamaBackend:
    def __init__(self, model: str = "qwen3:8b", host: str = "http://localhost:11434"):
        self.model, self.host = model, host

    def chat(self, system: str, user: str, schema: dict) -> dict:
        r = requests.post(f"{self.host}/api/chat", timeout=600, json={
            "model": self.model, "stream": False, "format": schema, "options": {"temperature": 0.4, "num_ctx": 8192},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        r.raise_for_status()
        return json.loads(r.json()["message"]["content"])


# ── Retrieval ────────────────────────────────────────────────────────────────

def load_kb() -> dict:
    return {"rules": [json.loads(line) for line in (KB / "rules.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()],
            "planets": json.loads((KB / "planets.json").read_text(encoding="utf-8")),
            "houses": json.loads((KB / "houses.json").read_text(encoding="utf-8")),
            "evidence": (KB / "evidence.md").read_text(encoding="utf-8")}


def retrieve(state: dict, kb: dict, question: str = "", k: int = 8) -> dict:
    """Passages for the techniques present in the state, ranked by overlap with its planets and the question;
    plus the significations of every planet and house the state makes active."""
    active_planets = {state["vimshottari"][lvl]["lord"] for lvl in ("maha", "antar", "pratyantar")}
    active_houses = set()
    if "bhrigu_chakra" in state:
        active_planets |= {state["bhrigu_chakra"]["lord"], *state["bhrigu_chakra"]["occupants"]}
        active_houses.add(str(state["bhrigu_chakra"]["active_house"]))
    if "profection" in state:
        active_planets.add(state["profection"]["lord_of_the_year"])
        active_houses |= {str(state["profection"]["house"]), str(state["profection"]["lord_natal_house"])}
    active_planets |= {t["planet"] for t in state.get("exact_transits", [])}
    techniques = {"vimshottari", "yogini", "transit"} | {t for t, key in (("bcp", "bhrigu_chakra"), ("profection", "profection"),
                                                                          ("tajika", "tajika"), ("chara", "chara"),
                                                                          ("ashtakavarga", "ashtakavarga")) if key in state}
    words = set(re.findall(r"[a-z]+", question.lower())) | {p.lower() for p in active_planets}
    scored = [(sum(w in r["text"].lower() for w in words), r) for r in kb["rules"] if r["technique"] in techniques]
    rules = [r for _, r in sorted(scored, key=lambda x: -x[0])][:k]
    return {"rules": rules, "planets": {p: kb["planets"][p] for p in sorted(active_planets) if p in kb["planets"]},
            "houses": {h: kb["houses"][h] for h in sorted(active_houses, key=int)}}


# ── Consultation ─────────────────────────────────────────────────────────────

def allowed_dates(state: dict) -> set[str]:
    dates = {v for lvl in state["vimshottari"].values() for v in (lvl["from"], lvl["to"])}
    dates |= set(state.get("bhrigu_chakra", {}).get("trigger_dates", {}).values())
    return dates


class Consultation:
    def __init__(self, person: dict, state: dict, backend=None, kb: dict | None = None, log: Path = LOG):
        self.person, self.state = person, state
        self.backend = backend or OllamaBackend()
        self.kb = kb or load_kb()
        self.log = Path(log)
        self.user_notes: list[str] = []
        self.id = uuid.uuid4().hex[:10]

    def turn(self, question: str = "") -> dict:
        if question:
            self.user_notes.append(question)
        ctx = retrieve(self.state, self.kb, " ".join(self.user_notes))
        prompt = (f"STATE REPORT:\n{json.dumps(self.state, indent=1)}\n\nKNOWLEDGE BASE:\n"
                  + "\n".join(f"[{r['id']}] {r['text']}" for r in ctx["rules"])
                  + f"\n\nPLANET SIGNIFICATIONS:\n{json.dumps(ctx['planets'], indent=1)}"
                  + f"\n\nHOUSES:\n{json.dumps(ctx['houses'], indent=1)}\n\nEVIDENCE:\n{self.kb['evidence']}"
                  + ("\n\nWHAT THE USER HAS SAID:\n" + "\n".join(f"- {n}" for n in self.user_notes) if self.user_notes else "")
                  + "\n\nWrite the consultation.")
        out = self.backend.chat(SYSTEM, prompt, SCHEMA)
        ok = allowed_dates(self.state)
        kept, dropped = [], []
        for w in out.get("windows", []):
            (kept if w.get("from") in ok and w.get("to") in ok and w["from"] <= w["to"] else dropped).append(w)
        for w in kept:
            w["confidence"] = min(float(w.get("confidence") or 0), 0.3)
            if not self.user_notes:
                w["source"] = "chart"            # nothing has been said yet: the model cannot credit the user
        out["windows"], out["dropped_windows"] = kept, dropped
        known = {r["id"] for r in self.kb["rules"]}
        for t in out.get("themes", []):
            t["cites"] = [c for c in t.get("cites", []) if c in known]
        self._log(kept)
        return out

    def _log(self, windows: list[dict]) -> None:
        if not windows:
            return
        self.log.parent.mkdir(parents=True, exist_ok=True)
        with self.log.open("a", encoding="utf-8") as fh:
            for w in windows:
                fh.write(json.dumps({"consultation": self.id, "person": self.person.get("name"),
                                     "made_at": datetime.now(timezone.utc).isoformat(), "state_date": self.state["date"],
                                     **w, "outcome": None}, ensure_ascii=False) + "\n")


def render(out: dict) -> str:
    lines = [out.get("summary", "").strip(), ""]
    for t in out.get("themes", []):
        lines.append(f"• {t['theme']} — {t['basis']}" + (f"  [{', '.join(t['cites'])}]" if t.get("cites") else ""))
    if out.get("windows"):
        lines += ["", "Test windows (logged and scored later; these techniques have not shown timing power):"]
        for w in out["windows"]:
            src = " (narrowed from what you said)" if w.get("source") == "user" else ""
            lines.append(f"  {w['from']} → {w['to']}: {w['claim']}{src}  — {w['basis']}")
    if out.get("dropped_windows"):
        lines.append(f"  ({len(out['dropped_windows'])} window(s) removed: dates not in the computed report)")
    if out.get("questions"):
        lines += ["", *[f"? {q}" for q in out["questions"]]]
    return "\n".join(lines)
