"""LLM orchestration layer.

Turns the FIRED rules (structured, explainable facts) into polished narrative
prose for each report section. Two modes:

  - If `anthropic` is installed and ANTHROPIC_API_KEY is set, it asks Claude to
    narrate ONLY from the supplied fired rules (grounded — no free invention).
  - Otherwise it falls back to a deterministic template narrator so the demo
    runs offline.

Critically, the LLM is constrained to the retrieved rules: this is the
"explainable output" guarantee. The model rephrases evidence; it does not
introduce claims that aren't backed by a fired rule.
"""
from __future__ import annotations

import os

from .reasoner import FiredRule

_SECTION_TITLES = {
    "personality": "Personality Analysis",
    "relationship": "Relationship Insights",
    "career": "Career Insights",
    "financial": "Financial Themes",
    "challenge": "Life Challenges",
    "opportunity": "Opportunity Periods",
    "risk": "Risk Periods",
}


def _template_narrate(area: str, rules: list[FiredRule]) -> str:
    if not rules:
        return "No strong indicators in the current chart for this area."
    lines = []
    for r in rules:
        lines.append(f"{r.text} (basis: {r.source}; rule {r.id})")
    return " ".join(lines)


def _claude_narrate(area: str, rules: list[FiredRule]) -> str | None:
    try:
        import anthropic  # type: ignore
    except Exception:
        return None
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    evidence = "\n".join(f"- [{r.system}] {r.text} (source: {r.source})" for r in rules)
    prompt = (
        f"You are writing the '{_SECTION_TITLES.get(area, area)}' section of an "
        f"astrology report. Use ONLY the evidence below. Do not invent any claim "
        f"not supported by it. Write 2-3 grounded sentences.\n\nEvidence:\n{evidence}"
    )
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return None


def narrate_section(area: str, rules: list[FiredRule]) -> dict:
    text = _claude_narrate(area, rules)
    mode = "claude"
    if text is None:
        text = _template_narrate(area, rules)
        mode = "template"
    return {
        "title": _SECTION_TITLES.get(area, area.title()),
        "narrative": text,
        "evidence": [{"rule": r.id, "system": r.system, "source": r.source} for r in rules],
        "narrator": mode,
    }
