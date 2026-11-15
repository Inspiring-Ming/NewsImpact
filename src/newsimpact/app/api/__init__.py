"""HTTP API and website - the single integration surface for the web app and clients.

/v1/...    versioned JSON API (OpenAPI at /openapi.json, docs at /docs)
/          the website (web/dist, built from web/), when present

One router file per area in routes/; ROUTES lists them. To add endpoints for
a new feature: write routes/<feature>.py with `router(api) -> APIRouter` and
add it to ROUTES. Run locally: make dev.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from newsimpact import __version__
from newsimpact.app.api.context import ApiContext
from newsimpact.app.api.routes import alerts, companies, monitor, sources, storylines, system
from newsimpact.app.config import Settings
from newsimpact.app.logs import configure_logging
from newsimpact.app.monitor import BackgroundMonitor
from newsimpact.app.wiring import Services, build_services

ROUTES = (system, companies, storylines, sources, alerts, monitor)


def create_app(services: Services | None = None) -> FastAPI:
    svc = services or build_services()
    api = ApiContext(svc, BackgroundMonitor(svc, svc.settings.monitor_every_minutes))

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        api.monitor.start()
        yield
        api.monitor.stop()

    app = FastAPI(title="NewsImpact API", version=__version__, lifespan=lifespan)
    for module in ROUTES:
        app.include_router(module.router(api))
    if svc.settings.web_dir.is_dir():  # the website, last so /v1 routes win
        app.mount("/", StaticFiles(directory=svc.settings.web_dir, html=True), name="web")
    return app


def _default_app() -> FastAPI:
    configure_logging(Settings().log_level)
    return create_app()


app = _default_app()
