"""Followed companies and alerts (alerts module)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from newsimpact.app.api.context import ApiContext


def router(api: ApiContext) -> APIRouter:
    r = APIRouter()
    svc = api.svc

    @r.get("/v1/watchlist", response_model=list[str])
    def watchlist() -> list[str]:
        """Companies followed for alerts (one list for now: a single user)."""
        return sorted(svc.alerts.followed())

    @r.put("/v1/watchlist/{ticker}", response_model=list[str])
    def follow(ticker: str) -> list[str]:
        if ticker not in {c.ticker for c in svc.companies}:
            raise HTTPException(404, "unknown company")
        svc.alerts.follow(ticker, True)
        return sorted(svc.alerts.followed())

    @r.delete("/v1/watchlist/{ticker}", response_model=list[str])
    def unfollow(ticker: str) -> list[str]:
        svc.alerts.follow(ticker, False)
        return sorted(svc.alerts.followed())

    @r.get("/v1/alerts")
    def alerts_status() -> dict[str, str]:
        """Is an alert channel configured? ('on' / 'off'; the channel itself stays secret)."""
        return {"channel": svc.alerts.channel}

    @r.post("/v1/alerts/test")
    def alerts_test() -> dict[str, str]:
        """Send one test message to every configured channel."""
        try:
            svc.alerts.test()
        except RuntimeError as exc:
            raise HTTPException(409, str(exc)) from None
        return {"sent": "ok"}

    return r
