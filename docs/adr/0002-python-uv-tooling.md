# 0002 – Python 3.12 with uv, ruff, mypy (strict), pytest

* Status: accepted
* Date: 2026-11-14

## Context
Core work is NLP/ML/data analysis, where Python has the deepest ecosystem.

## Decision
Python 3.12; `uv` for environments and lockfile; `ruff` lint+format; `mypy
--strict`; `pytest`; Pydantic v2 for models and settings; FastAPI for HTTP.

## Consequences
+ Fast, reproducible builds; one tool per job; typed code eases refactoring.
− Python is slower for CPU-bound hot paths → vectorise (NumPy/Polars) first;
  if still needed, write that service in Go/Rust against the same contracts (ADR 0003).
