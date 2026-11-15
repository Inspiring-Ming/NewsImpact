"""What the llm module needs (implemented in adapters/)."""

from __future__ import annotations

from typing import Protocol

from newsimpact.llm.models import LlmReply, LlmRequest, LlmResult


class LlmProvider(Protocol):
    """One model behind one API (local or hosted)."""

    name: str  # e.g. "anthropic:claude-opus-5-5", "ollama:qwen2.5:7b"

    def complete(self, request: LlmRequest) -> LlmReply: ...


class ResponseCache(Protocol):
    """Identical request -> stored answer: never pay twice for the same text."""

    def get(self, key: str) -> LlmResult | None: ...
    def put(self, key: str, result: LlmResult) -> None: ...


class SpendLedger(Protocol):
    def spent(self, month: str) -> float: ...
    def record(self, month: str, purpose: str, model: str, cost_usd: float) -> None: ...
