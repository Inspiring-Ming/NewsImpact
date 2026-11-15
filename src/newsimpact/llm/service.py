"""The LLM gateway: cache -> limits -> call -> record. Callers get a result or None."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime

from newsimpact.llm.logic import cache_key, cost_usd, worst_case_usd
from newsimpact.llm.models import BudgetExceededError, LlmPolicy, LlmRequest, LlmResult, ModelPrice
from newsimpact.llm.ports import LlmProvider, ResponseCache, SpendLedger

log = logging.getLogger(__name__)


class LlmGateway:
    def __init__(
        self,
        provider: LlmProvider,
        prices: dict[str, ModelPrice],
        cache: ResponseCache,
        ledger: SpendLedger,
        policy: LlmPolicy,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._provider = provider
        self._prices = prices
        self._cache = cache
        self._ledger = ledger
        self._policy = policy
        self._now = now
        self._calls_this_round = 0

    @property
    def name(self) -> str:
        return self._provider.name

    def new_round(self) -> None:
        self._calls_this_round = 0

    def spent_this_month(self) -> float:
        return self._ledger.spent(self._month())

    def complete_json(self, request: LlmRequest) -> LlmResult | None:
        """Cached or fresh answer; None if the provider gave nothing usable.

        Raises BudgetExceededError *before* calling when a limit would be crossed.
        """
        key = cache_key(self._provider.name, request)
        hit = self._cache.get(key)
        if hit is not None:
            return hit.model_copy(update={"cached": True, "cost_usd": 0.0})
        price = self._price(self._provider.name.split(":", 1)[-1])
        if self._calls_this_round >= self._policy.max_calls_per_round:
            raise BudgetExceededError("per-round LLM call cap reached")
        if (
            self.spent_this_month() + worst_case_usd(request, price)
            > self._policy.monthly_budget_usd
        ):
            raise BudgetExceededError("monthly LLM budget would be exceeded")

        self._calls_this_round += 1
        reply = self._provider.complete(request)
        cost = cost_usd(reply, self._price(reply.model))
        self._ledger.record(self._month(), request.purpose, reply.model, cost)
        if reply.data is None:
            log.warning(
                "unusable LLM reply", extra={"model": reply.model, "refused": reply.refused}
            )
            return None
        result = LlmResult(data=reply.data, model=reply.model, cost_usd=cost, cached=False)
        self._cache.put(key, result)
        return result

    def _price(self, model: str) -> ModelPrice:
        if self._provider.name.startswith("ollama:"):
            return ModelPrice(input=0, output=0, cache_read=0, cache_write=0)  # runs locally
        if model in self._prices:
            return self._prices[model]
        if not self._prices:
            raise BudgetExceededError("no price table: refusing to call a paid API blind")
        # Unknown model (e.g. a server-side fallback): assume the most expensive known price.
        return max(self._prices.values(), key=lambda p: p.output)

    def _month(self) -> str:
        return self._now().strftime("%Y-%m")
