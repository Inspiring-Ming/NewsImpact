"""What the identity module needs from the outside world: something that checks sign-ins."""

from __future__ import annotations

from typing import Protocol

from newsimpact.identity.models import User


class Authenticator(Protocol):
    def user_for(self, token: str | None) -> User | None:
        """The signed-in user for a request's bearer token; None = not signed in."""
        ...
