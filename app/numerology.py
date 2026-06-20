"""Deterministic numerology layer.

This module is fully real and runnable with zero external dependencies.
Numerology is a closed, deterministic system, so it is the right place to
demonstrate the rule-based core of the engine without needing an ephemeris.

Two systems are implemented:
  - Pythagorean (Western)  -> Life Path, Expression, Soul Urge
  - Chaldean               -> name vibration (used in many Vedic numerology texts)
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

PYTHAGOREAN = {
    "a": 1, "j": 1, "s": 1,
    "b": 2, "k": 2, "t": 2,
    "c": 3, "l": 3, "u": 3,
    "d": 4, "m": 4, "v": 4,
    "e": 5, "n": 5, "w": 5,
    "f": 6, "o": 6, "x": 6,
    "g": 7, "p": 7, "y": 7,
    "h": 8, "q": 8, "z": 8,
    "i": 9, "r": 9,
}

# Chaldean has no 9 assignment to letters (9 is considered sacred).
CHALDEAN = {
    "a": 1, "i": 1, "j": 1, "q": 1, "y": 1,
    "b": 2, "k": 2, "r": 2,
    "c": 3, "g": 3, "l": 3, "s": 3,
    "d": 4, "m": 4, "t": 4,
    "e": 5, "h": 5, "n": 5, "x": 5,
    "u": 6, "v": 6, "w": 6,
    "o": 7, "z": 7,
    "f": 8, "p": 8,
}

VOWELS = set("aeiou")
MASTER_NUMBERS = {11, 22, 33}


def _reduce(n: int, keep_master: bool = True) -> int:
    """Reduce to a single digit, preserving master numbers 11/22/33."""
    while n > 9:
        if keep_master and n in MASTER_NUMBERS:
            return n
        n = sum(int(d) for d in str(n))
    return n


def _name_sum(name: str, table: dict[str, int], filter_fn=None) -> int:
    total = 0
    for ch in name.lower():
        if ch in table and (filter_fn is None or filter_fn(ch)):
            total += table[ch]
    return total


@dataclass
class NumerologyProfile:
    life_path: int
    expression: int
    soul_urge: int
    personality: int
    chaldean_name: int
    birth_day: int
    details: dict = field(default_factory=dict)


def compute(name: str, dob: _dt.date) -> NumerologyProfile:
    """Compute the full numerology profile. Pure function, fully testable."""
    digits = [int(c) for c in dob.strftime("%Y%m%d")]
    life_path = _reduce(sum(digits))

    expression = _reduce(_name_sum(name, PYTHAGOREAN))
    soul_urge = _reduce(_name_sum(name, PYTHAGOREAN, lambda c: c in VOWELS))
    personality = _reduce(_name_sum(name, PYTHAGOREAN, lambda c: c not in VOWELS))
    chaldean = _reduce(_name_sum(name, CHALDEAN))
    birth_day = _reduce(dob.day)

    return NumerologyProfile(
        life_path=life_path,
        expression=expression,
        soul_urge=soul_urge,
        personality=personality,
        chaldean_name=chaldean,
        birth_day=birth_day,
        details={
            "name_used": name,
            "dob": dob.isoformat(),
            "is_master_life_path": life_path in MASTER_NUMBERS,
        },
    )
