import json
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from anthropic.types.beta import BetaTextBlock

from newsimpact.llm.adapters.anthropic_api import AnthropicProvider
from newsimpact.llm.adapters.memory import InMemoryResponseCache, InMemorySpendLedger
from newsimpact.llm.adapters.ollama import OllamaProvider
from newsimpact.llm.models import (
    BudgetExceededError,
    LlmPolicy,
    LlmReply,
    LlmRequest,
    ModelPrice,
    ToolRequest,
    ToolSpec,
)
from newsimpact.llm.service import LlmGateway

REQ = LlmRequest(purpose="test", system="Classify.", prompt="Acme beat guidance.",
                 schema={"type": "object"}, max_output_tokens=1000)  # fmt: skip
PRICES = {"m": ModelPrice(input=4, output=20, cache_read=0.2, cache_write=5)}


class FakeProvider:
    def __init__(self, name: str = "anthropic:m", model: str = "m") -> None:
        self.name = name
        self.model = model
        self.calls = 0

    def complete(self, request: LlmRequest) -> LlmReply:
        self.calls += 1
        return LlmReply(data={"ok": True}, model=self.model, input_tokens=1_000,
                        output_tokens=500, cache_read_tokens=10_000)  # fmt: skip


def _gateway(provider: FakeProvider, budget: float = 1.0, calls: int = 10) -> LlmGateway:
    return LlmGateway(provider, PRICES, InMemoryResponseCache(), InMemorySpendLedger(),
                      LlmPolicy(monthly_budget_usd=budget, max_calls_per_round=calls),
                      now=lambda: datetime(2026, 11, 15, tzinfo=UTC))  # fmt: skip


def test_cost_is_recorded_and_identical_requests_are_free() -> None:
    provider = FakeProvider()
    gw = _gateway(provider)
    first = gw.complete_json(REQ)
    again = gw.complete_json(REQ)
    # 1000*4 + 500*20 + 10000*0.2 per million = 0.016
    assert first and first.cost_usd == pytest.approx(0.016) and not first.cached
    assert again and again.cached and again.cost_usd == 0
    assert provider.calls == 1 and gw.spent_this_month() == pytest.approx(0.016)


def test_limits_stop_the_call_before_any_money_is_spent() -> None:
    provider = FakeProvider()
    with pytest.raises(BudgetExceededError, match="monthly"):
        _gateway(provider, budget=0.001).complete_json(REQ)
    with pytest.raises(BudgetExceededError, match="cap"):
        _gateway(provider, calls=0).complete_json(REQ)
    assert provider.calls == 0


def test_unknown_paid_model_is_priced_at_the_most_expensive_known_price() -> None:
    provider = FakeProvider(model="some-fallback-model")
    result = _gateway(provider).complete_json(REQ)
    assert result and result.cost_usd == pytest.approx(0.016)


def test_local_models_cost_nothing() -> None:
    result = _gateway(FakeProvider(name="ollama:qwen", model="ollama:qwen")).complete_json(REQ)
    assert result and result.cost_usd == 0


def test_ollama_adapter_sends_schema_and_reads_usage() -> None:
    seen: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"content": '{"event_type": "other"}'},
                                         "prompt_eval_count": 50, "eval_count": 7})  # fmt: skip

    client = httpx.Client(transport=httpx.MockTransport(handler))
    reply = OllamaProvider("qwen", client, "http://localhost:11434").complete(REQ)
    assert seen[0]["format"] == {"type": "object"} and seen[0]["stream"] is False
    assert reply.data == {"event_type": "other"} and reply.output_tokens == 7


def _anthropic_response(stop: str, text: str) -> SimpleNamespace:
    usage = SimpleNamespace(input_tokens=100, output_tokens=40, cache_read_input_tokens=900,
                            cache_creation_input_tokens=0)  # fmt: skip
    return SimpleNamespace(stop_reason=stop, model="claude-opus-5-5", usage=usage,
                           content=[BetaTextBlock(type="text", text=text)])  # fmt: skip


class FakeAnthropic:
    def __init__(self, response: SimpleNamespace) -> None:
        self.kwargs: dict[str, Any] = {}
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))
        self._response = response

    def _create(self, **kwargs: Any) -> SimpleNamespace:
        self.kwargs = kwargs
        return self._response


def test_anthropic_adapter_uses_structured_output_caching_and_fallback() -> None:
    fake = FakeAnthropic(_anthropic_response("end_turn", '{"event_type": "other"}'))
    reply = AnthropicProvider("claude-opus-5-5", client=fake).complete(REQ)
    assert reply.data == {"event_type": "other"} and reply.cache_read_tokens == 900
    assert fake.kwargs["output_config"]["format"]["type"] == "json_schema"
    assert fake.kwargs["output_config"]["effort"] == "low"
    assert fake.kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert fake.kwargs["fallbacks"] == "default"


def test_anthropic_refusal_gives_no_data() -> None:
    fake = FakeAnthropic(_anthropic_response("refusal", ""))
    reply = AnthropicProvider("claude-opus-5-5", client=fake).complete(REQ)
    assert reply.refused and reply.data is None


# ------------------------------------------------------------ tool use
TOOL_REQ = ToolRequest(purpose="assistant.ask", system="Answer from tools.", prompt="Why?",
                       max_output_tokens=500, max_steps=3)  # fmt: skip
LOOKUP = ToolSpec(name="lookup", description="d", input_schema={"type": "object"},
                  run=lambda **kw: "x")  # fmt: skip


class FakeToolProvider(FakeProvider):
    def run_tools(self, request: ToolRequest, tools: Any) -> tuple[str, list[LlmReply], list[str]]:
        steps = [LlmReply(data=None, model="m", input_tokens=1_000, output_tokens=100)] * 2
        return "the answer", steps, ["lookup"]


def test_every_tool_step_is_priced_and_recorded() -> None:
    gw = _gateway(FakeToolProvider())
    result = gw.run_tools(TOOL_REQ, [LOOKUP])
    # each step: 1000*4 + 100*20 per million = 0.006; two steps
    assert result and result.cost_usd == pytest.approx(0.012) and result.steps == 2
    assert result.tool_calls == ("lookup",) and gw.spent_this_month() == pytest.approx(0.012)


def test_tool_runs_respect_the_budget_and_need_a_capable_provider() -> None:
    with pytest.raises(BudgetExceededError):
        _gateway(FakeToolProvider(), budget=0.001).run_tools(TOOL_REQ, [LOOKUP])
    assert _gateway(FakeProvider()).run_tools(TOOL_REQ, [LOOKUP]) is None
    assert not _gateway(FakeProvider()).can_use_tools


class FakeRunner:
    """Stands in for client.beta.messages.tool_runner: yields one message per step."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.tools = kwargs["tools"]

    def __iter__(self) -> Any:
        self.tools[0].func(query="acme")  # the model calls the tool once
        yield _anthropic_response("tool_use", "")
        yield _anthropic_response("end_turn", "Acme moved. Sources:\nhttps://x.test/a")


def test_anthropic_tool_runner_wraps_tools_and_returns_each_steps_usage() -> None:
    runners: list[FakeRunner] = []

    def tool_runner(**kwargs: Any) -> FakeRunner:
        runners.append(FakeRunner(**kwargs))
        return runners[-1]

    fake = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(tool_runner=tool_runner)))
    seen: list[dict[str, Any]] = []
    spec = ToolSpec(name="lookup", description="Look up.",
                    input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                    run=lambda **kw: seen.append(kw) or "found")  # fmt: skip
    text, steps, calls = AnthropicProvider("claude-opus-5-5", client=fake).run_tools(
        TOOL_REQ, [spec]
    )
    assert text.startswith("Acme moved.") and len(steps) == 2 and calls == ["lookup"]
    assert seen == [{"query": "acme"}] and steps[0].cache_read_tokens == 900
    kw = runners[0].kwargs
    assert kw["max_iterations"] == 3 and kw["fallbacks"] == "default"
    assert runners[0].tools[0].name == "lookup"


def test_anthropic_tool_run_that_stops_mid_tools_gives_no_answer() -> None:
    class Unfinished(FakeRunner):
        def __iter__(self) -> Any:
            yield _anthropic_response("tool_use", "")

    fake = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(
        tool_runner=lambda **kw: Unfinished(**kw))))  # fmt: skip
    text, steps, _ = AnthropicProvider("m", client=fake).run_tools(TOOL_REQ, [LOOKUP])
    assert text == "" and len(steps) == 1
