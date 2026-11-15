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
