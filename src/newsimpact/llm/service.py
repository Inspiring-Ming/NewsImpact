"""The LLM gateway: cache -> limits -> call -> record. Callers get a result or None."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import cast

from newsimpact.llm.logic import cache_key, cost_usd, worst_case_usd
from newsimpact.llm.models import (
    BudgetExceededError,
    LlmPolicy,
    LlmRequest,
    LlmResult,
    ModelPrice,
    ToolRequest,
    ToolRunResult,
    ToolSpec,
)
from newsimpact.llm.ports import LlmProvider, ResponseCache, SpendLedger, ToolUsingProvider

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

    @property
    def can_use_tools(self) -> bool:
        return callable(getattr(self._provider, "run_tools", None))

    def run_tools(self, request: ToolRequest, tools: Sequence[ToolSpec]) -> ToolRunResult | None:
        """Let the model answer by calling `tools`; every step is priced and recorded.
        None if the provider cannot call tools. Not cached: the data behind the tools changes.

        Raises BudgetExceededError before starting if the worst case (every step using its
        full output allowance) would cross the monthly budget."""
        if not self.can_use_tools:
            return None
        provider = cast(ToolUsingProvider, self._provider)
        price = self._price(self._provider.name.split(":", 1)[-1])
        one_step = LlmRequest(purpose=request.purpose, system=request.system,
                              prompt=request.prompt, schema={},
                              max_output_tokens=request.max_output_tokens)  # fmt: skip
        worst = worst_case_usd(one_step, price) * request.max_steps
        if self.spent_this_month() + worst > self._policy.monthly_budget_usd:
            raise BudgetExceededError("monthly LLM budget would be exceeded")
        text, steps, calls = provider.run_tools(request, tools)
        cost = 0.0
        for reply in steps:
            step_cost = cost_usd(reply, self._price(reply.model))
            self._ledger.record(self._month(), request.purpose, reply.model, step_cost)
            cost += step_cost
        model = steps[-1].model if steps else self._provider.name
        return ToolRunResult(text=text, model=model, cost_usd=round(cost, 6), steps=len(steps),
                             tool_calls=tuple(calls))  # fmt: skip

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
