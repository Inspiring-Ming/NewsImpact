"""The assistant: tools over our data, and the checks every answer must pass."""

import json
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

from newsimpact.assistant.adapters.memory import InMemoryQuestionLog
from newsimpact.assistant.logic import Notebook, split_sources, toolbox
from newsimpact.assistant.models import AssistantPolicy
from newsimpact.assistant.service import AssistantService
from newsimpact.llm.models import BudgetExceededError, ToolRequest, ToolRunResult, ToolSpec

POLICY = AssistantPolicy(questions_per_user_per_day=2, max_steps=4, max_output_tokens=500)
ARTICLE = {"title": "Atlassian sinks 12%", "url": "https://news.test/team", "source": "Reuters",
           "date": "2026-11-14"}  # fmt: skip


class Data:
    """NewsData with one company and one event (the shape SnapshotNewsData returns)."""

    def __init__(self) -> None:
        self.asked: list[tuple[str, Any]] = []

    def companies(self) -> list[dict[str, Any]]:
        return [{"ticker": "TEAM", "name": "Atlassian", "country": "US", "sector": "IT"}]

    def events(self, ticker: str | None, days: int) -> list[dict[str, Any]]:
        self.asked.append(("events", days))
        return [{"event_id": "e1", "ticker": "TEAM", "event": "Results (mixed)",
                 "stock_vs_index": "-19.2% vs S&P 500 (13 Nov), unusual"}]  # fmt: skip

    def event(self, event_id: str) -> dict[str, Any] | None:
        return (
            {"event_id": "e1", "updates": [{"articles": [ARTICLE]}]} if event_id == "e1" else None
        )

    def articles(self, text: str, ticker: str | None, days: int) -> list[dict[str, Any]]:
        return [ARTICLE] * 15


class Model:
    """A ToolModel that calls the given tools in order, then answers with `reply`."""

    def __init__(self, reply: str, calls: Sequence[tuple[str, dict[str, Any]]] = ()) -> None:
        self.reply, self.calls = reply, calls
        self.requests: list[ToolRequest] = []

    def run_tools(self, request: ToolRequest, tools: Sequence[ToolSpec]) -> ToolRunResult | None:
        self.requests.append(request)
        by_name = {t.name: t for t in tools}
        for name, args in self.calls:
            by_name[name].run(**args)
        return ToolRunResult(text=self.reply, model="m", cost_usd=0.001, steps=2,
                             tool_calls=tuple(n for n, _ in self.calls))  # fmt: skip


def _service(model: Any, log: InMemoryQuestionLog | None = None,
             now: Callable[[], datetime] = lambda: datetime(2026, 11, 16, tzinfo=UTC)
             ) -> AssistantService:  # fmt: skip
    return AssistantService(model, Data(), log or InMemoryQuestionLog(), POLICY, now=now)


LOOKUPS = (("list_events", {"ticker": "TEAM"}), ("get_event", {"event_id": "e1"}))


def test_an_answer_keeps_only_links_that_a_tool_returned() -> None:
    reply = ("Atlassian's results were mixed; the stock did -19.2% vs the S&P 500, an unusual "
             "move.\nSources:\nhttps://news.test/team\nhttps://made-up.test/x")  # fmt: skip
    answer = _service(Model(reply, LOOKUPS)).ask("u", "Why did Atlassian fall?")
    assert answer.status == "answered" and answer.text.endswith("unusual move.")
    assert [s.url for s in answer.sources] == ["https://news.test/team"]  # invented link dropped
    assert answer.tools_used == ("list_events", "get_event")


def test_numbers_must_come_from_the_tools_and_advice_is_never_shown() -> None:
    made_up = _service(Model("The stock fell 25% this week.", LOOKUPS)).ask("u", "Why?")
    advice = _service(Model("Investors should sell Atlassian.", LOOKUPS)).ask("u", "Why?")
    assert made_up.status == advice.status == "checks_failed"
    assert "25%" not in made_up.text and "sell" not in advice.text
    # a number from the question itself is fine
    ok = _service(Model("Nothing new in the last 7 days.", LOOKUPS)).ask("u", "Last 7 days?")
    assert ok.status == "answered"


def test_nothing_in_our_data_is_said_plainly() -> None:
    answer = _service(Model("Not in our data: no events for Visa.")).ask("u", "Visa news?")
    assert answer.status == "not_in_our_data" and not answer.sources


def test_daily_limit_budget_and_missing_model() -> None:
    log = InMemoryQuestionLog()
    service = _service(Model("Nothing found in our events.", LOOKUPS), log)
    assert [service.ask("u", "q").status for _ in range(3)][-1] == "limit_reached"
    assert service.ask("someone-else", "q").status == "answered"  # the limit is per person

    class OverBudget(Model):
        def run_tools(self, request: ToolRequest, tools: Sequence[ToolSpec]) -> None:
            raise BudgetExceededError("monthly LLM budget would be exceeded")

    assert _service(OverBudget("")).ask("u", "q").status == "unavailable"
    assert _service(None).ask("u", "q").status == "unavailable"
    assert not _service(None).available


def test_the_event_being_viewed_is_given_to_the_model() -> None:
    model = Model("Nothing found in our events.")
    _service(model).ask("u", "  what   next? ", event_id="e1")
    assert model.requests[0].prompt.startswith("what next?") and "e1" in model.requests[0].prompt
    assert model.requests[0].max_steps == POLICY.max_steps


def test_tools_are_read_only_lookups_with_bounded_results() -> None:
    data, book = Data(), Notebook()
    tools = {t.name: t for t in toolbox(data, book)}
    assert set(tools) == {"find_company", "list_events", "get_event", "search_articles"}
    assert all(t.input_schema["additionalProperties"] is False for t in tools.values())
    assert json.loads(tools["find_company"].run(query="team"))[0]["name"] == "Atlassian"
    assert len(json.loads(tools["search_articles"].run(text="atlassian"))) == 10
    tools["list_events"].run(days=5000)
    assert data.asked[-1] == ("events", 365)  # at most a year back
    assert json.loads(tools["get_event"].run(event_id="nope")) == {"error": "no event with that id"}
    assert "https://news.test/team" in book.links and len(book.outputs) == 4


def test_sources_are_read_from_the_last_sources_line() -> None:
    assert split_sources("Text.\nSources:\nhttps://a.test/1 https://b.test/2") == (
        "Text.",
        ["https://a.test/1", "https://b.test/2"],
    )
    assert split_sources("No links here.") == ("No links here.", [])
