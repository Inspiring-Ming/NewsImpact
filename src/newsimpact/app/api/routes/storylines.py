"""Raw events (storylines), their evidence check and price path, for integrations."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, HTTPException

from newsimpact.app.api.context import ApiContext
from newsimpact.market.models import PricePath
from newsimpact.storylines.models import Storyline
from newsimpact.validation.models import Assessment


def router(api: ApiContext) -> APIRouter:
    r = APIRouter()
    svc = api.svc

    @r.get("/v1/storylines", response_model=list[Storyline])
    def list_storylines(ticker: str | None = None) -> list[Storyline]:
        items = svc.storyline_store.all()
        return [s for s in items if ticker is None or s.ticker == ticker.upper()]

    @r.get("/v1/storylines/{storyline_id}", response_model=Storyline)
    def get_storyline(storyline_id: str) -> Storyline:
        storyline = svc.storyline_store.get(storyline_id)
        if storyline is None:
            raise HTTPException(404, "unknown storyline")
        return storyline

    @r.get("/v1/storylines/{storyline_id}/assessment", response_model=Assessment)
    def assess_storyline(storyline_id: str) -> Assessment:
        """Evidence check of every update, conclusion and notes (with provenance).

        The latest stored assessment from monitoring, else assessed now.
        """
        story = get_storyline(storyline_id)
        return svc.validation.latest(storyline_id) or svc.validation.assess(story)

    @r.get("/v1/storylines/{storyline_id}/prices", response_model=PricePath | None)
    def storyline_prices(storyline_id: str) -> PricePath | None:
        """Stock vs. its index around the event (rebased to 100); null without price data."""
        story = get_storyline(storyline_id)
        if svc.market is None:
            return None
        first = min(e.published_at for e in story.events).date()
        last = max(e.published_at for e in story.events).date()
        try:
            return svc.market.price_path(story.ticker, first - timedelta(days=30),
                                         last + timedelta(days=20))  # fmt: skip
        except ValueError:
            return None

    return r
