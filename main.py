"""FastAPI entry point for the Jyotish reasoning + report engine.

Run:
    uvicorn main:app --reload
Then POST birth data to /report, or run `python main.py` for a CLI demo.
"""
from __future__ import annotations

import datetime as _dt

from app.reports import generator

try:
    from fastapi import FastAPI
    from pydantic import BaseModel

    app = FastAPI(title="Jyotish Reasoning Engine", version="0.1.0")

    class BirthData(BaseModel):
        name: str
        date_of_birth: str          # YYYY-MM-DD
        time_of_birth: str = "12:00"  # HH:MM
        place_of_birth: str = ""      # used by the geo->lat/lon step in prod
        as_of: str | None = None      # forecast anchor date

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/report")
    def report(b: BirthData):
        dob_dt = _dt.datetime.fromisoformat(f"{b.date_of_birth}T{b.time_of_birth}")
        on = _dt.date.fromisoformat(b.as_of) if b.as_of else None
        return generator.generate(b.name, dob_dt, on)

except ImportError:
    app = None  # FastAPI not installed — CLI demo still works.


def _demo():
    dob = _dt.datetime(1974, 4, 3, 8, 30)
    rep = generator.generate("Arjun Mehta", dob)
    print(f"Subject: {rep['subject']['name']}  ({rep['subject']['dob']})")
    print(f"Ephemeris mode: {rep['chart_meta']['ephemeris']}")
    print(f"Current Mahadasha: {rep['chart_meta']['dasha']['mahadasha_lord']}")
    print(f"Rules fired ({rep['rule_count']}): {', '.join(rep['rules_fired'])}\n")
    for s in rep["sections"]:
        print(f"## {s['title']}  [{s['narrator']}]")
        print(f"   {s['narrative']}")
        if s["evidence"]:
            print(f"   evidence: {[e['rule'] for e in s['evidence']]}")
        print()


if __name__ == "__main__":
    _demo()
