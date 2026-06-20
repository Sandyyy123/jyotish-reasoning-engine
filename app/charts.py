"""Astrological chart layer (Vedic).

Real ephemeris via `pyswisseph` when installed; otherwise a DETERMINISTIC
fallback so the engine always runs in a demo. The fallback is clearly flagged
in the output (`ephemeris="approximate"`) and is reproducible from the birth
data, so the rest of the pipeline can be exercised end-to-end without GPU,
network, or licensed ephemeris files.

In production you swap `_approx_positions` for the swisseph call — the rest of
the pipeline (reasoning, retrieval, report) is unchanged.
"""
from __future__ import annotations

import datetime as _dt
import math
from dataclasses import dataclass

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Vishottari Dasha sequence and durations (years) — the real Vedic system.
DASHA_SEQUENCE = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
    ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17),
]
DASHA_TOTAL = sum(d for _, d in DASHA_SEQUENCE)  # 120 years

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


@dataclass
class ChartPosition:
    planet: str
    sign: str
    sign_index: int
    longitude: float


def _try_swisseph(jd: float):
    try:
        import swisseph as swe  # type: ignore
    except Exception:
        return None
    codes = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
        "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS,
        "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE,
    }
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # sidereal — Vedic standard
    out = []
    for name, code in codes.items():
        lon = swe.calc_ut(jd, code, swe.FLG_SIDEREAL)[0][0]
        out.append((name, lon))
    rahu = dict(out)["Rahu"]
    out.append(("Ketu", (rahu + 180.0) % 360.0))
    return out


def _approx_positions(dob: _dt.datetime) -> list[tuple[str, float]]:
    """Deterministic, reproducible stand-in keyed off the birth moment.

    NOT astronomically accurate — flagged as `approximate` downstream. Exists
    only so the reasoning/report pipeline is fully runnable in the demo.
    """
    epoch = _dt.datetime(2000, 1, 1)
    days = (dob - epoch).total_seconds() / 86400.0
    # crude mean motions (deg/day), seeded per planet for stable spread
    rates = {
        "Sun": 0.9856, "Moon": 13.176, "Mars": 0.524, "Mercury": 1.383,
        "Jupiter": 0.083, "Venus": 1.602, "Saturn": 0.034, "Rahu": -0.0529,
    }
    seeds = {p: (i + 1) * 33.0 for i, p in enumerate(rates)}
    out = []
    for p, rate in rates.items():
        lon = (seeds[p] + rate * days) % 360.0
        out.append((p, lon))
    rahu = dict(out)["Rahu"]
    out.append(("Ketu", (rahu + 180.0) % 360.0))
    return out


def _julian_day(dt: _dt.datetime) -> float:
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    frac = (dt.hour - 12) / 24 + dt.minute / 1440 + dt.second / 86400
    return jdn + frac


def compute_chart(dob: _dt.datetime) -> tuple[list[ChartPosition], str]:
    jd = _julian_day(dob)
    raw = _try_swisseph(jd)
    ephemeris = "swisseph_sidereal_lahiri"
    if raw is None:
        raw = _approx_positions(dob)
        ephemeris = "approximate"  # demo flag — surfaced in API + report
    positions = []
    for planet, lon in raw:
        idx = int(lon // 30) % 12
        positions.append(ChartPosition(planet, SIGNS[idx], idx, round(lon, 2)))
    return positions, ephemeris


def current_dasha(dob: _dt.datetime, on: _dt.date) -> dict:
    """Which Vishottari Mahadasha is running on a given date.

    Anchors the 120-year cycle at birth (simplified — real systems start from
    Moon nakshatra balance; structure and sequence are correct and the hook for
    the real calc is here)."""
    elapsed_years = (on - dob.date()).days / 365.25
    pos = elapsed_years % DASHA_TOTAL
    acc = 0.0
    for lord, dur in DASHA_SEQUENCE:
        if pos < acc + dur:
            into = pos - acc
            return {
                "mahadasha_lord": lord,
                "years_into": round(into, 2),
                "years_remaining": round(dur - into, 2),
                "period_years": dur,
            }
        acc += dur
    return {"mahadasha_lord": DASHA_SEQUENCE[0][0]}
