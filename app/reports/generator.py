"""Report generation pipeline.

Assembles the full structured report from:
  1. numerology profile
  2. chart positions + current dasha
  3. fired rules (reasoning)
  4. narrated sections (orchestration)

Returns a single JSON-serialisable dict. Every section carries its evidence,
so the report is auditable end-to-end.
"""
from __future__ import annotations

import datetime as _dt

from .. import charts, numerology
from ..engine import orchestrator, reasoner

# Areas reported in fixed order (matches the client's Output Requirements).
REPORT_AREAS = [
    "personality", "relationship", "career", "financial",
    "challenge", "opportunity", "risk",
]


def build_facts(name: str, dob_dt: _dt.datetime, on: _dt.date) -> dict:
    num = numerology.compute(name, dob_dt.date())
    positions, ephemeris = charts.compute_chart(dob_dt)
    dasha = charts.current_dasha(dob_dt, on)

    facts = {
        "life_path": num.life_path,
        "expression": num.expression,
        "soul_urge": num.soul_urge,
        "personality": num.personality,
        "chaldean_name": num.chaldean_name,
        "birth_day": num.birth_day,
        "mahadasha_lord": dasha.get("mahadasha_lord"),
    }
    for p in positions:
        facts[f"{p.planet}_sign"] = p.sign
        facts[f"{p.planet}_sign_index"] = p.sign_index

    meta = {
        "numerology": num.__dict__,
        "positions": [p.__dict__ for p in positions],
        "dasha": dasha,
        "ephemeris": ephemeris,
    }
    return facts, meta


def generate(name: str, dob_dt: _dt.datetime, on: _dt.date | None = None) -> dict:
    on = on or _dt.date.today()
    facts, meta = build_facts(name, dob_dt, on)
    fired = reasoner.fire(facts)

    by_area: dict[str, list] = {a: [] for a in REPORT_AREAS}
    for r in fired:
        by_area.setdefault(r.area, []).append(r)

    sections = [orchestrator.narrate_section(a, by_area.get(a, [])) for a in REPORT_AREAS]

    return {
        "subject": {"name": name, "dob": dob_dt.isoformat(), "as_of": on.isoformat()},
        "chart_meta": meta,
        "rules_fired": [r.id for r in fired],
        "rule_count": len(fired),
        "sections": sections,
        "explainability": "Every narrative sentence is grounded in a fired rule; see section.evidence.",
    }
