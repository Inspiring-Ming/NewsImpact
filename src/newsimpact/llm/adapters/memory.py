"""In-memory ResponseCache and SpendLedger (tests)."""

from __future__ import annotations

from collections import defaultdict

from newsimpact.llm.models import LlmResult


class InMemoryResponseCache:
    def __init__(self) -> None:
        self._items: dict[str, LlmResult] = {}

    def get(self, key: str) -> LlmResult | None:
        return self._items.get(key)

    def put(self, key: str, result: LlmResult) -> None:
        self._items[key] = result


class InMemorySpendLedger:
    def __init__(self) -> None:
        self._by_month: dict[str, float] = defaultdict(float)

    def spent(self, month: str) -> float:
        return self._by_month[month]

    def record(self, month: str, purpose: str, model: str, cost_usd: float) -> None:
        self._by_month[month] += cost_usd
