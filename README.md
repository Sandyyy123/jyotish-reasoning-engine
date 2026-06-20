# Jyotish Reasoning Engine (demo)

A small, **runnable** reference architecture for an AI-powered astrology/numerology
interpretation engine: rule-based reasoning + knowledge retrieval + LLM orchestration
+ explainable, structured report generation. Built as a working sketch of the layered
design — not a finished product.

> Demo subject fires 5 rules across Numerology, Vedic, and Dasha systems with a full
> evidence trace for every sentence. Runs offline with zero paid APIs.

## Why this design

The client requirement was explicit: *"not a simple chatbot"* — they want
**rule-based reasoning, a structured interpretation framework, LLM orchestration, a
knowledge retrieval layer, and explainable outputs.** A raw LLM prompt fails all five:
it hallucinates, can't cite a source, and isn't auditable.

This repo separates the layers so the probabilistic part (LLM) only ever **rephrases
evidence the deterministic engine already proved**:

```
 Birth data ─▶ Computation layer        (numerology = exact; chart = ephemeris)
            ─▶ Fact dictionary
            ─▶ Reasoning engine          (declarative rules fire → provenance)
            ─▶ Knowledge retrieval       (rule base; vector store in prod)
            ─▶ LLM orchestration         (Claude narrates ONLY fired rules)
            ─▶ Report generator          (structured sections + evidence)
```

## Layers

| Layer | File | Status in demo |
|-------|------|----------------|
| Numerology (deterministic) | `app/numerology.py` | **Fully real** — Pythagorean + Chaldean |
| Vedic chart + Dasha | `app/charts.py` | Real via `pyswisseph`; deterministic fallback otherwise (flagged `approximate`) |
| Rule base (knowledge) | `app/rules/rules.yaml` | Declarative, multi-system, cited; add a system = add rules |
| Reasoning engine | `app/engine/reasoner.py` | Fires rules, returns provenance, sandboxed eval |
| LLM orchestration | `app/engine/orchestrator.py` | Claude when keyed; grounded template fallback |
| Report pipeline | `app/reports/generator.py` | Structured JSON, every sentence carries evidence |
| API | `main.py` (FastAPI) | `POST /report`, `GET /health` |

## Explainability

Every narrative sentence is grounded in a fired rule. The report returns
`section.evidence` listing the `rule id`, `system`, and `source` citation behind each
claim, plus the top-level `rules_fired` list. Nothing reaches the report that a rule
didn't license.

## Run it

```bash
pip install -r requirements.txt
python main.py                 # CLI demo (offline)
uvicorn main:app --reload      # API, then POST /report
```

```json
POST /report
{ "name": "Arjun Mehta", "date_of_birth": "1974-04-03",
  "time_of_birth": "08:30", "place_of_birth": "Pune, India" }
```

## Production path (not in this demo)

- Swap the `approximate` ephemeris for `pyswisseph` sidereal (Lahiri) + a geocoding step for place → lat/lon/timezone.
- Move the rule base into a vector store (Chroma/Pinecone) for semantic retrieval over a large classical-text corpus, keeping the deterministic rules as the spine.
- Add KP, Nadi, and Lal Kitab rule packs (same YAML schema, no code change).
- LangGraph orchestration for multi-step reasoning (chart → dasha → transit → synthesis) with per-step validators.
- Month-by-month forecast = dasha/antardasha + transit windows over a date range.

Built by Dr. Sandeep Grover.
