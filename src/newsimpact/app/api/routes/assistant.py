"""Ask NewsImpact: a question answered from our own data, with its sources (assistant module)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field

from newsimpact.app.api.auth import current_user
from newsimpact.app.api.context import ApiContext
from newsimpact.assistant.models import Answer
from newsimpact.identity.models import User
from newsimpact.shared.events import Model


class Question(Model):
    question: str = Field(min_length=3, max_length=500)
    event_id: str | None = Field(default=None, description="the event the person is looking at")


class AssistantStatus(Model):
    available: bool = Field(description="False without a language model that can call tools")


def router(api: ApiContext) -> APIRouter:
    r = APIRouter()
    svc = api.svc
    signed_in = Depends(current_user(api))  # resolved per app (no postponed annotations here)

    @r.get("/v1/assistant", response_model=AssistantStatus)
    def status(user: Annotated[User, signed_in]) -> AssistantStatus:
        return AssistantStatus(available=bool(svc.assistant and svc.assistant.available))

    @r.post("/v1/assistant/ask", response_model=Answer)
    def ask(body: Question, user: Annotated[User, signed_in]) -> Answer:
        """Answered only from our events, sources and stock moves; checked before it is
        returned (no advice, no number that is not in our data); links a tool returned."""
        if svc.assistant is None:  # always built by the wiring; kept for type safety
            raise HTTPException(503, "assistant not configured")
        return svc.assistant.ask(user.user_id, body.question, body.event_id)

    return r
