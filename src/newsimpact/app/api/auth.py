"""Who is calling: every /v1 route asks for the signed-in user; some need an admin.

The token comes from the `Authorization: Bearer <token>` header and is checked
by the configured Authenticator (identity module). With NI_AUTH=local everyone
is the one built-in admin, so nothing changes for a single local user.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException, Request

from newsimpact.app.api.context import ApiContext
from newsimpact.identity.models import User


def current_user(api: ApiContext) -> Callable[[Request], User]:
    def dependency(request: Request) -> User:
        header = request.headers.get("authorization", "")
        token = header.removeprefix("Bearer ").strip() if header.startswith("Bearer ") else None
        user = api.svc.auth.user_for(token)
        if user is None:
            raise HTTPException(401, "sign in required", headers={"WWW-Authenticate": "Bearer"})
        return user

    return dependency


def member_user(api: ApiContext) -> Callable[[Request], User]:
    """A signed-in person, not an anonymous demo visitor: may change their own settings
    (followed companies are always covered, so a shared visitor must not change them)."""
    signed_in = current_user(api)

    def dependency(request: Request) -> User:
        user = signed_in(request)
        if user.is_guest:
            raise HTTPException(403, "visitors of the demo can read, not change this")
        return user

    return dependency


def admin_user(api: ApiContext) -> Callable[[Request], User]:
    signed_in = current_user(api)

    def dependency(request: Request) -> User:
        user = signed_in(request)
        if not user.is_admin:
            raise HTTPException(403, "admins only")
        return user

    return dependency
