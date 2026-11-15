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
    assert change["stock_move_status"] == "measured"
    assert change["said_by"] and -1 <= change["tone"] <= 1 and change["next_update"] is None
    assert change["sources"] >= 3 and change["actions"]
    # more independent sources -> more confidence than any one of them alone
    assert 0.9 < change["confidence"] <= 1
    orbit = next(c for c in companies if c["ticker"] == "ORBT")
    assert orbit["events"] == [] and orbit["name"] == "Orbit Auto"
    summary = client.get(f"/v1/events/{change['event_id']}/summary").json()
    assert summary["name"] == "Globex Motors" and summary["events"][0]["updates"]

    stories = client.get("/v1/storylines?ticker=GLBX").json()
    assert {s["theme"] for s in stories} == {"leadership_crisis", "product_safety"}
    crisis = next(s for s in stories if s["theme"] == "leadership_crisis")
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
