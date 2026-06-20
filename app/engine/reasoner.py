"""Rule-based reasoning engine.

Loads the declarative rule base, evaluates each rule's `when` condition against
a flat fact dictionary, and returns the FIRED rules with full provenance. This
is deterministic and explainable: every conclusion the report makes can be
traced back to a rule id, its source citation, and the facts that triggered it.

`when` is evaluated in a restricted namespace (no builtins) so the YAML cannot
execute arbitrary code — only read the facts we pass in.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import yaml

_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "rules", "rules.yaml")


@dataclass
class FiredRule:
    id: str
    system: str
    area: str
    weight: float
    source: str
    text: str


def load_rules(path: str = _RULES_PATH) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _safe_eval(expr: str, facts: dict) -> bool:
    try:
        return bool(eval(expr, {"__builtins__": {}}, facts))
    except Exception:
        # A rule that references a fact we don't have simply doesn't fire.
        return False


def fire(facts: dict, rules: list[dict] | None = None) -> list[FiredRule]:
    rules = rules if rules is not None else load_rules()
    fired = []
    for r in rules:
        if _safe_eval(r["when"], facts):
            fired.append(FiredRule(
                id=r["id"], system=r["system"], area=r["area"],
                weight=float(r.get("weight", 0.5)),
                source=r["source"], text=r["text"],
            ))
    # Strongest signal first within the report.
    fired.sort(key=lambda x: x.weight, reverse=True)
    return fired
