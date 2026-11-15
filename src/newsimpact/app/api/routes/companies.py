"""Companies and their events, as the website shows them (app/views/companies.py)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from newsimpact.app.api.context import ApiContext
from newsimpact.app.views import companies as views
from newsimpact.app.views.companies import CompanyCard


def router(api: ApiContext) -> APIRouter:
    r = APIRouter()
    svc = api.svc

    @r.get("/v1/companies", response_model=list[CompanyCard])
    def companies() -> list[CompanyCard]:
        """Every company we follow: sector, latest news, and its events with stock moves."""
        return views.companies(svc)

    @r.get("/v1/events/{event_id}/summary", response_model=CompanyCard)
    def event_summary(event_id: str) -> CompanyCard:
        card = views.event_summary(svc, event_id)
        if card is None:
            raise HTTPException(404, "unknown event")
        return card

    return r
