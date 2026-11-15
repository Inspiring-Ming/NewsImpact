"""Data owned by the llm module: requests, replies, prices and spending limits."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from newsimpact.shared.events import Event, Model


class LlmRequest(Model):
    purpose: str = Field(description="what the call is for, e.g. 'semantics.classify' (ledger)")
    system: str = Field(description="stable instructions (cached by providers that support it)")
    prompt: str
    schema_: dict[str, Any] = Field(alias="schema", description="JSON schema of the answer")
    max_output_tokens: int = Field(default=2048, gt=0)


class LlmReply(Model):
    """What a provider returned, with raw token usage."""

    data: dict[str, Any] | None = Field(description="parsed JSON answer; None if unusable")
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    refused: bool = False


class LlmResult(Model):
    data: dict[str, Any]
    model: str
    cost_usd: float
    cached: bool


class ModelPrice(Model):
    """US dollars per million tokens."""

    input: float = Field(ge=0)
    output: float = Field(ge=0)
    cache_read: float = Field(ge=0)
    cache_write: float = Field(ge=0)


class LlmPreset(Model):
    """A named, reasoned choice of provider + model (data/reference/llm_models.json)."""

    provider: str = Field(description="anthropic | ollama")
    model: str
    effort: Literal["low", "medium", "high", "xhigh", "max"] = "low"
    why: str


class LlmPolicy(Model):
    monthly_budget_usd: float = Field(ge=0)
    max_calls_per_round: int = Field(ge=0)


class BudgetExceededError(RuntimeError):
    """The monthly budget or per-round call cap would be exceeded."""


PUBLISHES: tuple[type[Event], ...] = ()
