"""News sources: the list with reliability, coverage, and recent articles."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from newsimpact.app.api.context import ApiContext
from newsimpact.app.views import system as views
from newsimpact.reliability.models import ReliabilityScore
from newsimpact.shared.events import Model
from newsimpact.sources.models import Article, OutletCoverage, Source


class SourceWithReliability(Model):
    source: Source
    reliability: ReliabilityScore
    enabled: bool


def router(api: ApiContext) -> APIRouter:
    r = APIRouter()
    svc = api.svc

    @r.get("/v1/sources", response_model=list[SourceWithReliability])
    def list_sources() -> list[SourceWithReliability]:
        enabled = {s.source_id: s.enabled for s in svc.sources.listed()}
        return [
            SourceWithReliability(
                source=s,
                reliability=svc.reliability.score_source(s.source_id),
                enabled=enabled.get(s.source_id, True),
            )
            for s in svc.reliability.sources()
        ]

    @r.get("/v1/sources/{source_id}/reliability", response_model=ReliabilityScore)
    def source_reliability(source_id: str, topic: str = "all") -> ReliabilityScore:
        if source_id not in {s.source_id for s in svc.reliability.sources()}:
            raise HTTPException(404, "unknown source")
        return svc.reliability.score_source(source_id, topic)

    @r.get("/v1/coverage", response_model=list[OutletCoverage])
    def coverage() -> list[OutletCoverage]:
        """Evidence for which sources to keep, add or drop (docs/07)."""
        return views.outlet_coverage(svc)

    @r.get("/v1/articles", response_model=list[Article])
    def recent_articles(limit: int = 50) -> list[Article]:
        return list(svc.articles.recent(min(limit, 200)))

    return r
