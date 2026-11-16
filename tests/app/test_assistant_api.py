"""The assistant through the real wiring: its data from the snapshot, the API route, and MCP."""

import json

import anyio
from fastapi.testclient import TestClient
from mcp import Client

from newsimpact.app.api import create_app
from newsimpact.app.config import Settings
from newsimpact.app.demo import run_demo
from newsimpact.app.mcp import build_server
from newsimpact.app.views.news_data import SnapshotNewsData
from newsimpact.app.wiring import build_services


def _demo():  # type: ignore[no-untyped-def]
    svc = build_services(Settings(env="test", profile="demo"))
    run_demo(svc)
    return svc


def test_the_tools_read_live_events_and_articles_from_the_snapshot() -> None:
    svc = _demo()
    data = SnapshotNewsData(svc)
    events = data.events(None, 3650)  # the demo news is dated in the past
    assert events and {"event_id", "company", "stock_vs_index", "confirmed"} <= set(events[0])
    detail = data.event(events[0]["event_id"])
    assert detail and detail["updates"] and detail["updates"][0]["articles"][0]["url"]
    word = detail["updates"][0]["articles"][0]["title"].split()[0]
    assert data.articles(word, None, 3650)
    assert data.event("missing") is None


def test_without_a_language_model_the_route_says_so() -> None:
    client = TestClient(create_app(build_services(Settings(env="test", profile="demo"))))
    assert client.get("/v1/assistant").json() == {"available": False}
    answer = client.post("/v1/assistant/ask", json={"question": "Why did Globex fall?"}).json()
    assert answer["status"] == "unavailable"
    assert client.post("/v1/assistant/ask", json={"question": ""}).status_code == 422


def test_mcp_clients_get_the_same_tools_over_the_same_data() -> None:
    svc = _demo()

    async def session() -> tuple[set[str], dict[str, object], bool]:
        async with Client(build_server(svc)) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            listed = await client.call_tool("list_events", {"days": 3650})
            first = json.loads(listed.content[0].text)[0]  # type: ignore[union-attr]
            bad = await client.call_tool("no_such_tool", {})
            return names, first, bool(bad.is_error)

    names, first, bad_is_error = anyio.run(session)
    assert names == {"find_company", "list_events", "get_event", "search_articles"}
    assert first["event_id"] and bad_is_error
