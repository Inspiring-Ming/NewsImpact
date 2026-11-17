"""A public demo: everyone may read, only the owner may change anything.

Visitors are one shared, non-admin user ("visitor"): they see every page and may ask the
assistant (its daily limit is then shared by all visitors, which caps the AI cost). The
owner sends `Authorization: Bearer <NI_ADMIN_TOKEN>` to run updates, load data, change the
followed companies or test alerts. No accounts, so nothing personal is stored.
"""

from __future__ import annotations

import hmac

from newsimpact.identity.models import ADMIN, GUEST, User

VISITOR = User(user_id="visitor", roles=(GUEST,))
OWNER = User(user_id="owner", roles=(ADMIN,))


class PublicDemo:
    def __init__(self, admin_token: str) -> None:
        if len(admin_token) < 24:
            raise ValueError("NI_ADMIN_TOKEN must be at least 24 characters for NI_AUTH=demo")
        self._token = admin_token.encode()

    def user_for(self, token: str | None) -> User | None:
        if token and hmac.compare_digest(token.encode(), self._token):
            return OWNER
        return VISITOR
