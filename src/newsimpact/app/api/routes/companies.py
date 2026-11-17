"""Companies and their events, as the website shows them (app/views/companies.py)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
from pydantic import TypeAdapter

from newsimpact.app.api.context import ApiContext
from newsimpact.app.views import snapshot
from newsimpact.app.views.companies import CompanyCard

CARDS = TypeAdapter(list[CompanyCard])


def router(api: ApiContext) -> APIRouter:
    r = APIRouter()
    svc = api.svc

    @r.get("/v1/companies", response_model=list[CompanyCard])
    def companies() -> Response:
        """Every company we follow: sector, latest news, and its events with stock moves.
        From the latest snapshot (computed once per round); its JSON is made once per
        snapshot and reused for every visitor until the next round."""
        snap = snapshot.latest(svc)
        cached = api.cache.get("companies_json")
        if cached is None or cached[0] != snap.computed_at:
            cached = (snap.computed_at, CARDS.dump_json(list(snap.companies)))
            api.cache["companies_json"] = cached
        return Response(cached[1], media_type="application/json")

    @r.get("/v1/events/{event_id}/summary", response_model=CompanyCard)
    def event_summary(event_id: str) -> CompanyCard:
        card = snapshot.event_summary(svc, event_id)
        if card is None:
            raise HTTPException(404, "unknown event")
        return card

    return r
