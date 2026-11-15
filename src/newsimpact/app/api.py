"""HTTP API and website - the single integration surface for the web app and clients.

/v1/...    versioned JSON API (OpenAPI at /openapi.json, docs at /docs)
/          the website (web/dist, built from web/), when present
Run locally: make dev  (API with reload + website dev server)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from newsimpact import __version__
from newsimpact.app import queries
from newsimpact.app.config import Settings
from newsimpact.app.demo import run_demo
from newsimpact.app.logs import configure_logging
from newsimpact.app.monitor import BackgroundMonitor, RoundResult
from newsimpact.app.wiring import Services, build_services
from newsimpact.impact.models import ImpactAssessment
from newsimpact.llm.models import LlmPreset
from newsimpact.market.models import PricePath
from newsimpact.reliability.models import ReliabilityScore
from newsimpact.shared.events import Model
from newsimpact.sources.models import Article, OutletCoverage, Source
from newsimpact.storylines.models import Playbook, Storyline
from newsimpact.validation.models import (
    Assessment,
    StageChannelCalibration,
    WindowCalibration,
)


class SourceWithReliability(Model):
    source: Source
    reliability: ReliabilityScore
    enabled: bool


class MonitorStatus(Model):
    every_minutes: float
    last_round_at: str | None
    last_new_articles: int | None
    last_assessments_updated: int | None


class Calibration(Model):
    reactions: tuple[StageChannelCalibration, ...]
    windows: tuple[WindowCalibration, ...]


class Method(Model):
    """Every setting with its reason - what the website's "Method" page shows."""

    methodology: dict[str, Any]
    playbooks: tuple[Playbook, ...]
    late_report_days: int
    llm_presets: dict[str, LlmPreset]
    llm_preset_in_use: str


def create_app(services: Services | None = None) -> FastAPI:
    svc = services or build_services()
    monitor = BackgroundMonitor(svc, svc.settings.monitor_every_minutes)
    state = {"demo_loaded": False}
    evaluated: dict[str, queries.Evaluation] = {}

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        monitor.start()
        yield
        monitor.stop()

    app = FastAPI(title="NewsImpact API", version=__version__, lifespan=lifespan)

    # ------------------------------------------------------------ status
    @app.get("/health")
    def health() -> dict[str, str]:
        s = svc.settings
        return {"status": "ok", "version": __version__, "env": s.env, "profile": s.profile}

    @app.get("/v1/overview", response_model=queries.Overview)
    def overview() -> queries.Overview:
        return queries.overview(svc)

    @app.get("/v1/companies", response_model=list[queries.CompanyCard])
    def companies() -> list[queries.CompanyCard]:
        """Every company we follow: sector, latest news, and its events with stock moves."""
        return queries.companies(svc)

    @app.get("/v1/events/{event_id}/summary", response_model=queries.CompanyCard)
    def event_summary(event_id: str) -> queries.CompanyCard:
        card = queries.event_summary(svc, event_id)
        if card is None:
            raise HTTPException(404, "unknown event")
        return card

    @app.get("/v1/monitor", response_model=MonitorStatus)
    def monitor_status() -> MonitorStatus:
        return _status(monitor.last, svc.settings.monitor_every_minutes)

    @app.post("/v1/monitor/run", response_model=MonitorStatus)
    def run_monitor_round() -> MonitorStatus:
        """Collect from every outlet, chase follow-ups, re-check evidence - now."""
        if svc.settings.profile == "demo" and not state["demo_loaded"]:
            raise HTTPException(409, "demo profile: load the demo data first")
        return _status(monitor.run_now(), svc.settings.monitor_every_minutes)

    @app.post("/v1/demo/load")
    def load_demo() -> dict[str, int]:
        if svc.settings.env == "prod" or svc.settings.profile != "demo":
            raise HTTPException(404)
        if state["demo_loaded"]:
            raise HTTPException(409, "demo data already loaded")
        state["demo_loaded"] = True
        run = run_demo(svc)
        return {"from_feeds": run.from_feeds, "from_follow_up": run.from_follow_up}

    # ------------------------------------------------------------ sources
    @app.get("/v1/sources", response_model=list[SourceWithReliability])
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

    @app.get("/v1/sources/{source_id}/reliability", response_model=ReliabilityScore)
    def source_reliability(source_id: str, topic: str = "all") -> ReliabilityScore:
        if source_id not in {s.source_id for s in svc.reliability.sources()}:
            raise HTTPException(404, "unknown source")
        return svc.reliability.score_source(source_id, topic)

    @app.get("/v1/coverage", response_model=list[OutletCoverage])
    def coverage() -> list[OutletCoverage]:
        """Evidence for which outlets to keep, add or drop (docs/07)."""
        return queries.outlet_coverage(svc)

    @app.get("/v1/articles", response_model=list[Article])
    def recent_articles(limit: int = 50) -> list[Article]:
        return list(svc.articles.recent(min(limit, 200)))

    # --------------------------------------------------------- storylines
    @app.get("/v1/storylines", response_model=list[Storyline])
    def list_storylines(ticker: str | None = None) -> list[Storyline]:
        items = svc.storyline_store.all()
        return [s for s in items if ticker is None or s.ticker == ticker.upper()]

    @app.get("/v1/storylines/{storyline_id}", response_model=Storyline)
    def get_storyline(storyline_id: str) -> Storyline:
        storyline = svc.storyline_store.get(storyline_id)
        if storyline is None:
            raise HTTPException(404, "unknown storyline")
        return storyline

    @app.get("/v1/storylines/{storyline_id}/assessment", response_model=Assessment)
    def assess_storyline(storyline_id: str) -> Assessment:
        """Evidence check of every stage, conclusion and suggestions (with provenance).

        The latest stored assessment from monitoring, else assessed now.
        """
        story = get_storyline(storyline_id)
        return svc.validation.latest(storyline_id) or svc.validation.assess(story)

    @app.get("/v1/storylines/{storyline_id}/prices", response_model=PricePath | None)
    def storyline_prices(storyline_id: str) -> PricePath | None:
        """Stock vs. benchmark around the story (rebased to 100); null without price data."""
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

    @app.get("/v1/impact/{ticker}", response_model=list[ImpactAssessment])
    def impact_for_ticker(ticker: str) -> list[ImpactAssessment]:
        return list(svc.impacts.by_ticker(ticker.upper()))

    # ------------------------------------------------------ quality & method
    @app.get("/v1/calibration", response_model=Calibration)
    def calibration() -> Calibration:
        """Across storylines: does each stage move each channel as expected? Do windows fit?"""
        reactions, windows = svc.validation.calibrate(svc.storyline_store.all())
        return Calibration(reactions=tuple(reactions), windows=tuple(windows))

    @app.get("/v1/evaluation", response_model=queries.Evaluation)
    def evaluation() -> queries.Evaluation:
        """Analysis quality on the hand-labelled set. Computed once per server start: the
        labelled set and the reading chain only change with a deploy, and the website shows
        it on every visit (with an LLM preset each run would cost money)."""
        if "result" not in evaluated:
            evaluated["result"] = queries.evaluation(svc)
        return evaluated["result"]

    @app.get("/v1/method", response_model=Method)
    def method() -> Method:
        raw = json.loads((svc.settings.reference_dir / "methodology.json").read_text())
        return Method(methodology=raw, playbooks=tuple(svc.playbooks.playbooks()),
                      late_report_days=svc.playbooks.late_report_days,
                      llm_presets=svc.llm_presets,
                      llm_preset_in_use=svc.settings.llm_preset)  # fmt: skip

    # ------------------------------------------------------------ website
    if svc.settings.web_dir.is_dir():
        app.mount("/", StaticFiles(directory=svc.settings.web_dir, html=True), name="web")
    return app


def _status(last: RoundResult | None, every: float) -> MonitorStatus:
    return MonitorStatus(
        every_minutes=every,
        last_round_at=last.at.isoformat() if last else None,
        last_new_articles=last.new_total if last else None,
        last_assessments_updated=last.assessments_updated if last else None,
    )


def _default_app() -> FastAPI:
    configure_logging(Settings().log_level)
    return create_app()


app = _default_app()
