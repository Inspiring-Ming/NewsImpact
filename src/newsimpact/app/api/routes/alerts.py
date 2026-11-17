"""The signed-in user's followed companies and alerts (alerts module)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from newsimpact.app.api.auth import current_user, member_user
from newsimpact.app.api.context import ApiContext
from newsimpact.identity.models import User


def router(api: ApiContext) -> APIRouter:
    r = APIRouter()
    svc = api.svc
    # Resolved when each route is defined (no postponed annotations in this file), because
    # the dependency is built per app from `api`.
    signed_in = Depends(current_user(api))
    # Following a company makes it covered for everyone, and alerts go to a real channel: not
    # for anonymous demo visitors (they keep their stars in the browser, ADR 0037).
    member = Depends(member_user(api))

    @r.get("/v1/me")
    def me(user: Annotated[User, signed_in]) -> dict[str, object]:
        """Who is asking, and whether they may change things (the website hides what not)."""
        return {"user_id": user.user_id, "admin": user.is_admin, "guest": user.is_guest}

    @r.get("/v1/watchlist", response_model=list[str])
    def watchlist(user: Annotated[User, signed_in]) -> list[str]:
        """The companies this user follows (alerts are sent for them)."""
        return sorted(svc.alerts.followed(user.user_id))

    @r.put("/v1/watchlist/{ticker}", response_model=list[str])
    def follow(ticker: str, user: Annotated[User, member]) -> list[str]:
        if ticker not in {c.ticker for c in svc.companies}:
            raise HTTPException(404, "unknown company")
        svc.alerts.follow(user.user_id, ticker, True)
        return sorted(svc.alerts.followed(user.user_id))

    @r.delete("/v1/watchlist/{ticker}", response_model=list[str])
    def unfollow(ticker: str, user: Annotated[User, member]) -> list[str]:
        svc.alerts.follow(user.user_id, ticker, False)
        return sorted(svc.alerts.followed(user.user_id))

    @r.get("/v1/alerts")
    def alerts_status(user: Annotated[User, signed_in]) -> dict[str, str]:
        """Does this user have an alert channel? ('on' / 'off'; the channel stays secret)."""
        return {"channel": svc.alerts.channel(user.user_id)}

    @r.post("/v1/alerts/test")
    def alerts_test(user: Annotated[User, member]) -> dict[str, str]:
        """Send one test message to every channel of this user."""
        try:
            svc.alerts.test(user.user_id)
        except RuntimeError as exc:
            raise HTTPException(409, str(exc)) from None
        return {"sent": "ok"}

    return r
