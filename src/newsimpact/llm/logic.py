"""Cost arithmetic - pure functions, no I/O."""

from __future__ import annotations

import hashlib
import json

from newsimpact.llm.models import LlmReply, LlmRequest, ModelPrice

CHARS_PER_TOKEN = 3.5  # conservative for English text (real tokenizers average ~4)


def cost_usd(reply: LlmReply, price: ModelPrice) -> float:
    per = 1_000_000
    return round(
        reply.input_tokens * price.input / per
        + reply.output_tokens * price.output / per
        + reply.cache_read_tokens * price.cache_read / per
        + reply.cache_write_tokens * price.cache_write / per,
        6,
    )


def worst_case_usd(request: LlmRequest, price: ModelPrice) -> float:
    """Upper bound before the call: all input uncached, all output tokens used."""
    tokens_in = (len(request.system) + len(request.prompt)) / CHARS_PER_TOKEN
    return round((tokens_in * max(price.input, price.cache_write)
                  + request.max_output_tokens * price.output) / 1_000_000, 6)  # fmt: skip


def cache_key(provider: str, request: LlmRequest) -> str:
    payload = json.dumps([provider, request.system, request.prompt, request.schema_],
                         sort_keys=True)  # fmt: skip
    return hashlib.sha256(payload.encode()).hexdigest()
