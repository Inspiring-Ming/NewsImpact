"""One built-in admin user and no sign-in: a single person running NewsImpact locally.

Safe only where the site is not reachable by others (your computer, a private
network). For anything shared, use a real identity provider (Cognito).
"""

from __future__ import annotations

from newsimpact.identity.models import ADMIN, User

LOCAL_USER = User(user_id="local", roles=(ADMIN,))


class LocalSingleUser:
    def user_for(self, token: str | None) -> User | None:
        return LOCAL_USER
