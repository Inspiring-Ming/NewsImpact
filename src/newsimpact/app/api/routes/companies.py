"""Companies and their events, as the website shows them (app/views/companies.py)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from newsimpact.app.api.context import ApiContext
from newsimpact.app.views import snapshot
from newsimpact.app.views.companies import CompanyCard
from newsimpact.app.views.snapshot import CompanyCoverage
from newsimpact.shared.events import Model


class CoverageReport(Model):
    computed_at: datetime
    analysis: str
    window_days: int
    companies: tuple[CompanyCoverage, ...]


def router(api: ApiContext) -> APIRouter:
    r = APIRouter()
    svc = api.svc

    @r.get("/v1/companies", response_model=list[CompanyCard])
    def companies() -> list[CompanyCard]:
        """Every company we follow: sector, latest news, and its events with stock moves.
        From the latest snapshot (computed once per round; see /v1/companies/coverage)."""
        return list(snapshot.latest(svc).companies)

    @r.get("/v1/companies/coverage", response_model=CoverageReport)
    def coverage() -> CoverageReport:
        """News found per company in the coverage window; a gap = none found (check the
        sources or the names we match). Also when the pages were computed, and how."""
        snap = snapshot.latest(svc)
        return CoverageReport(computed_at=snap.computed_at, analysis=snap.analysis,
                              window_days=snap.coverage_window_days,
                              companies=snap.coverage)  # fmt: skip

    @r.get("/v1/events/{event_id}/summary", response_model=CompanyCard)
    def event_summary(event_id: str) -> CompanyCard:
        card = snapshot.event_summary(svc, event_id)
        if card is None:
            raise HTTPException(404, "unknown event")
        return card

    return r
