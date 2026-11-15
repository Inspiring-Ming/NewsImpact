"""LlmProvider for Claude, through the official `anthropic` SDK (pip extra: anthropic).

Credentials: ANTHROPIC_API_KEY from the environment or the git-ignored .env
(passed in by app/wiring/plugins.py), else the SDK's own sources. Never in committed files.
Request choices and why:
  * structured outputs (output_config.format) -> the answer always parses
  * effort "low" by default: classification rarely gains from deep thinking
  * system prompt marked for prompt caching: it is identical for every claim
  * server-side refusal fallback ("default"): a declined request is retried on
    a fallback model; if the whole chain refuses we return data=None and the
    caller keeps the free baseline result
"""

from __future__ import annotations

import json
from typing import Any, Literal

import anthropic
from anthropic.types.beta import BetaTextBlock

from newsimpact.llm.models import LlmReply, LlmRequest

Effort = Literal["low", "medium", "high", "xhigh", "max"]


class AnthropicProvider:
    def __init__(
        self, model: str, effort: Effort = "low", client: Any = None, api_key: str | None = None
    ) -> None:
        self._model = model
        self._effort: Effort = effort
        # api_key=None -> the SDK's own sources (ANTHROPIC_API_KEY, `ant auth login` profile)
        self._client = client if client is not None else anthropic.Anthropic(api_key=api_key)
        self.name = f"anthropic:{model}"

    def complete(self, request: LlmRequest) -> LlmReply:
        resp = self._client.beta.messages.create(
            model=self._model,
            max_tokens=request.max_output_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={
                "effort": self._effort,
                "format": {"type": "json_schema", "schema": request.schema_},
            },
            system=[
                {"type": "text", "text": request.system, "cache_control": {"type": "ephemeral"}}
            ],
            messages=[{"role": "user", "content": request.prompt}],
        )
        usage = resp.usage
        refused = resp.stop_reason == "refusal"
        text = None if refused else _first_text(resp.content)
        data = None
        if text is not None and resp.stop_reason != "max_tokens":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = None
        return LlmReply(
            data=data,
            model=resp.model,
            input_tokens=usage.input_tokens or 0,
            output_tokens=usage.output_tokens or 0,
            cache_read_tokens=usage.cache_read_input_tokens or 0,
            cache_write_tokens=usage.cache_creation_input_tokens or 0,
            refused=refused,
        )


def _first_text(blocks: list[Any]) -> str | None:
    """With structured outputs the answer is the first text block (thinking blocks come first)."""
    return next((b.text for b in blocks if isinstance(b, BetaTextBlock)), None)
