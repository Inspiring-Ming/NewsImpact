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

    steps = {s["step"]: s for s in client.get("/v1/pipeline").json()["steps"]}
    assert list(steps) == ["monitor", "connect", "anticipate", "verify"]
    assert steps["monitor"]["headline"] == 10 and steps["connect"]["headline"] == 3
    assert 0 < steps["verify"]["headline"] <= steps["anticipate"]["headline"]
    coverage = {c["source_id"]: c for c in client.get("/v1/coverage").json()}
    assert coverage["wire-alpha"]["in_stories"] > 0

    cards = client.get("/v1/briefing").json()
    crisis_card = next(c for c in cards if c["theme"] == "leadership_crisis")
    assert crisis_card["market"] == "US" and crisis_card["stages"] == 3
    assert crisis_card["reaction"]["channel"] == "price"
    assert crisis_card["expectations_met"] <= crisis_card["expectations_measured"]

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
