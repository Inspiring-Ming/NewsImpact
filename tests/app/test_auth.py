"""Sign-in on the API: every /v1 route needs a user, admin routes need an admin,
and each user has their own followed companies."""

from dataclasses import replace

from fastapi.testclient import TestClient

from newsimpact.app.api import create_app
from newsimpact.app.config import Settings
from newsimpact.app.wiring import build_services
from newsimpact.identity.models import ADMIN, User

USERS = {"ana-token": User(user_id="ana"), "boss-token": User(user_id="boss", roles=(ADMIN,))}


class TokenAuth:
    """Stands in for a real provider (Cognito): a known token -> its user."""

    def user_for(self, token: str | None) -> User | None:
        return USERS.get(token or "")


def _client() -> TestClient:
    svc = build_services(Settings(env="test", profile="demo"))
    return TestClient(create_app(replace(svc, auth=TokenAuth())))


def _as(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_routes_need_sign_in_but_health_stays_open() -> None:
    client = _client()
    assert client.get("/health").status_code == 200
    assert client.get("/v1/companies").status_code == 401
    assert client.get("/v1/companies", headers=_as("wrong")).status_code == 401
    assert client.get("/v1/companies", headers=_as("ana-token")).status_code == 200


def test_admin_routes_need_an_admin() -> None:
    client = _client()
    assert client.post("/v1/demo/load", headers=_as("ana-token")).status_code == 403
    assert client.post("/v1/demo/load", headers=_as("boss-token")).status_code == 200


def test_each_user_has_their_own_watchlist() -> None:
    client = _client()
    client.put("/v1/watchlist/GLBX", headers=_as("ana-token"))
    assert client.get("/v1/watchlist", headers=_as("ana-token")).json() == ["GLBX"]
    assert client.get("/v1/watchlist", headers=_as("boss-token")).json() == []


def test_alert_routes_answer_per_user() -> None:
    client = _client()
    assert client.get("/v1/alerts", headers=_as("ana-token")).json() == {"channel": "off"}
    assert client.post("/v1/alerts/test", headers=_as("ana-token")).status_code == 409  # no channel
    client.put("/v1/watchlist/GLBX", headers=_as("ana-token"))
    assert client.delete("/v1/watchlist/GLBX", headers=_as("ana-token")).json() == []
    assert client.put("/v1/watchlist/NOPE", headers=_as("ana-token")).status_code == 404


def test_a_public_demo_lets_everyone_read_and_only_the_owner_change_things() -> None:
    import pytest
    from pydantic import SecretStr

    key = "k" * 32
    settings = Settings(env="test", profile="demo", auth="demo", admin_token=SecretStr(key))
    client = TestClient(create_app(build_services(settings)))
    owner = {"Authorization": f"Bearer {key}"}
    assert client.get("/v1/me").json() == {"user_id": "visitor", "admin": False, "guest": True}
    assert client.get("/v1/companies").status_code == 200  # reading needs no sign-in
    assert client.put("/v1/watchlist/GLBX").status_code == 403  # the followed list is shared
    assert client.post("/v1/monitor/run").status_code == 403  # rounds cost money
    assert client.post("/v1/alerts/test").status_code == 403
    assert client.get("/v1/me", headers=owner).json()["admin"] is True
    assert client.put("/v1/watchlist/GLBX", headers=owner).json() == ["GLBX"]
    big = client.get("/v1/companies", headers={"Accept-Encoding": "gzip"})
    assert big.headers.get("content-encoding") == "gzip" or len(big.content) < 1000
    with pytest.raises(ValueError, match="at least 24"):
        build_services(
            Settings(env="test", profile="demo", auth="demo", admin_token=SecretStr("short"))
        )
