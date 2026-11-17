from fastapi.testclient import TestClient

from newsimpact.app.api import create_app
from newsimpact.app.config import Settings
from newsimpact.app.wiring import build_services


def test_api_contract_for_the_website() -> None:
    client = TestClient(create_app(build_services(Settings(env="test", profile="demo"))))
    assert client.get("/health").json()["status"] == "ok"

    # Listed outlets are visible (with prior-based reliability) before any news arrives.
    sources = client.get("/v1/sources").json()
    assert {s["source"]["source_id"] for s in sources} == {"wire-alpha", "daily-markets",
                                                          "rumor-blog", "globex-ir"}  # fmt: skip
    assert client.post("/v1/monitor/run").status_code == 409  # demo needs its data first

    assert client.post("/v1/demo/load").json() == {"from_feeds": 5, "from_follow_up": 5}
    assert client.post("/v1/demo/load").status_code == 409
    assert client.post("/v1/monitor/run").json()["last_new_articles"] == 0

    overview = client.get("/v1/overview").json()
    assert overview["articles"] == 10 and overview["llm"] == "off"
    assert len(client.get("/v1/articles?limit=3").json()) == 3
    assert client.get("/v1/sources/nope/reliability").status_code == 404
    assert client.get("/v1/coverage").json()

    coverage = {c["source_id"]: c for c in client.get("/v1/coverage").json()}
    assert coverage["wire-alpha"]["in_stories"] > 0

    companies = client.get("/v1/companies").json()
    assert companies[0]["events"], "companies with events come first"
    globex = next(c for c in companies if c["ticker"] == "GLBX")
    assert globex["sector"] == "Consumer Discretionary" and globex["index_name"] == "market index"
    change = next(e for e in globex["events"] if e["event_type"] == "Leadership change")
    assert [u["title"] for u in change["updates"]] == [
        "Leader under pressure",
        "Leader steps down",
        "New leader named",
    ]
    assert change["stock_move"] < 0 and change["stock_move_unusual"] is True
    assert change["stock_move_status"] == "measured" and change["move_so_far"] is None
    assert change["verified"] and change["latest_url"].startswith("http")
    assert change["priority"] in {"act", "check"} and change["checks"][0]["url"]
    assert len(change["brief"]) == 3 and change["brief_by"] == "rules"
    assert change["record"]["n"] == 0  # the only such event: it is not its own evidence
    assert all(u["articles"] for u in change["updates"])
    assert -1 <= change["tone"] <= 1 and change["next_update"] is None
    assert change["sources"] >= 3 and change["notes"] and change["watch"]
    assert change["research"][0]["source"] and change["expectation"]["source"]
    orbit = next(c for c in companies if c["ticker"] == "ORBT")
    assert orbit["events"] == [] and orbit["name"] == "Orbit Auto"
    summary = client.get(f"/v1/events/{change['event_id']}/summary").json()
    assert summary["name"] == "Globex Motors" and summary["events"][0]["updates"]

    storylines = client.get("/v1/storylines?ticker=GLBX").json()
    assert {s["theme"] for s in storylines} == {"leadership_crisis", "product_safety"}
    crisis = next(s for s in storylines if s["theme"] == "leadership_crisis")
    assessment = client.get(f"/v1/storylines/{crisis['storyline_id']}/assessment").json()
    assert assessment["conclusion"] and assessment["provenance"]["components"]
    prices = client.get(f"/v1/storylines/{crisis['storyline_id']}/prices").json()
    assert prices["points"] and prices["benchmark"] == "MKT"
    assert client.get("/v1/storylines/missing").status_code == 404

    assert client.get("/v1/calibration").json()["reactions"]
    assert client.get("/v1/evaluation").json()["examples"] >= 50
    method = client.get("/v1/method").json()
    assert method["llm_presets"]["quality"]["model"] == "claude-opus-5-5"
    assert "rationale" in method["methodology"]["market"]


def test_a_new_release_shows_at_once(tmp_path) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html></html>")
    (tmp_path / "assets" / "index-abc123.js").write_text("")
    settings = Settings(env="test", profile="demo", web_dir=tmp_path)
    client = TestClient(create_app(build_services(settings)))
    assert client.get("/").headers["cache-control"] == "no-cache"  # the page is re-checked
    assert "immutable" in client.get("/assets/index-abc123.js").headers["cache-control"]


def test_how_it_works_explains_its_numbers() -> None:
    client = TestClient(create_app(build_services(Settings(env="test", profile="demo"))))
    client.post("/v1/demo/load")
    method = client.get("/v1/method").json()
    assert method["source_priors"]["wire"]["why"] and method["prior_strength"] == 10
    types = {t["theme"]: t for t in client.get("/v1/event-types").json()}
    assert set(types) == {p["theme"] for p in method["playbooks"]}
    for t in types.values():
        assert t["window_why"] and t["steps"] and t["confirmed"] <= t["events"]
        assert all(c["finding"] and c["source"] and 0 < c["chance"] < 1 for c in t["cases"])
    takeover = types["m_and_a"]
    assert [c["label"] for c in takeover["cases"][:2]] == ["company is the target",
                                                           "company is the buyer"]  # fmt: skip


def test_events_carry_a_small_price_line_from_before_the_event() -> None:
    client = TestClient(create_app(build_services(Settings(env="test", profile="demo"))))
    client.post("/v1/demo/load")
    events = [e for c in client.get("/v1/companies").json() for e in c["events"]]
    lines = [e for e in events if len(e["spark"]) > 1]
    assert lines, "the demo has prices, so measured events get a line"
    e = lines[0]
    assert 0 < e["spark_event_at"] < len(e["spark"])  # a few closes before the event day
    assert e["spark"][e["spark_event_at"] - 1] == 0  # the close before the event is the zero line
