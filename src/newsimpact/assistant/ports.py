"""What the assistant needs. The app provides NewsData (from the latest snapshot and the
article store) and the ToolModel (the llm gateway); over a network they would be API clients."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from newsimpact.llm.models import ToolRequest, ToolRunResult, ToolSpec


class NewsData(Protocol):
    """Read-only facts, as plain values (already formatted for people: '-18.5%')."""

    def companies(self) -> list[dict[str, Any]]: ...
    def events(self, ticker: str | None, days: int) -> list[dict[str, Any]]: ...
    def event(self, event_id: str) -> dict[str, Any] | None: ...
    def articles(self, text: str, ticker: str | None, days: int) -> list[dict[str, Any]]: ...


class ToolModel(Protocol):
    def run_tools(self, request: ToolRequest, tools: Sequence[ToolSpec]) -> ToolRunResult | None:
        """None if the model cannot call tools; raises BudgetExceededError over budget."""
        ...


class QuestionLog(Protocol):
    """How many questions each person asked on a day (for the daily limit)."""

    def count(self, user_id: str, day: str) -> int: ...
    def add(self, user_id: str, day: str) -> None: ...
