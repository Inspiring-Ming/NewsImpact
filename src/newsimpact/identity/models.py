"""A signed-in person and what they may do."""

from __future__ import annotations

from pydantic import Field

from newsimpact.shared.events import Model

ADMIN = "admin"  # may run updates, load demo data, test alert channels
GUEST = "guest"  # an anonymous visitor of a public demo: may read and ask, not change anything


class User(Model):
    user_id: str = Field(description="stable id from the identity provider")
    email: str | None = None
    roles: tuple[str, ...] = ()

    @property
    def is_admin(self) -> bool:
        return ADMIN in self.roles

    @property
    def is_guest(self) -> bool:
        return GUEST in self.roles
