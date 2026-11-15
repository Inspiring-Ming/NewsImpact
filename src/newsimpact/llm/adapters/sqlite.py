"""SQLite ResponseCache and SpendLedger: answers and spend survive restarts."""

from __future__ import annotations

import json
import uuid

from newsimpact.llm.models import LlmResult
from newsimpact.shared.sqlite import Database


class SqliteResponseCache:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("llm_cache")

    def get(self, key: str) -> LlmResult | None:
        doc = self._c.get(key)
        return LlmResult.model_validate_json(doc) if doc else None

    def put(self, key: str, result: LlmResult) -> None:
        self._c.put(key, result.model_dump_json())


class SqliteSpendLedger:
    """One row per paid call (month, purpose, model, cost) - auditable spend."""

    def __init__(self, db: Database) -> None:
        self._c = db.collection("llm_spend")

    def spent(self, month: str) -> float:
        return float(sum(json.loads(d)["cost_usd"] for d in self._c.find(month)))

    def record(self, month: str, purpose: str, model: str, cost_usd: float) -> None:
        row = {"purpose": purpose, "model": model, "cost_usd": cost_usd}
        self._c.put(uuid.uuid4().hex, json.dumps(row), tag=month)
