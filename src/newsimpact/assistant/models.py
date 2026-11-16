"""Data owned by the assistant module: answers, their sources, and the limits."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from newsimpact.shared.events import Event, Model

Status = Literal["answered", "not_in_our_data", "checks_failed", "limit_reached", "unavailable"]


class SourceLink(Model):
    title: str
    url: str
    source: str = Field(description="the outlet, e.g. Reuters")


class Answer(Model):
    question: str
    text: str = Field(description="the answer shown to the person (or why there is none)")
    status: Status
    sources: tuple[SourceLink, ...] = Field(default=(), description="links a tool returned")
    tools_used: tuple[str, ...] = ()
    model: str = ""
    cost_usd: float = 0.0


class AssistantPolicy(Model):
    """Limits, with their reasons in data/reference/methodology.json "assistant"."""

    questions_per_user_per_day: int = Field(gt=0)
    max_steps: int = Field(gt=0, description="model replies per question (tool rounds + 1)")
    max_output_tokens: int = Field(gt=0, description="per model reply")


PUBLISHES: tuple[type[Event], ...] = ()
