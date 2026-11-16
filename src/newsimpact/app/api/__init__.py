"""HTTP API and website - the single integration surface for the web app and clients.

/v1/...    versioned JSON API (OpenAPI at /openapi.json, docs at /docs)
/          the website (web/dist, built from web/), when present

One router file per area in routes/; ROUTES lists them. To add endpoints for
a new feature: write routes/<feature>.py with `router(api) -> APIRouter` and
add it to ROUTES. Every route in ROUTES requires a signed-in user (api/auth.py);
/health stays open for load balancers. Run locally: make dev.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from newsimpact import __version__
from newsimpact.app.api.auth import current_user
from newsimpact.app.api.context import ApiContext
from newsimpact.app.api.routes import (
    alerts,
    assistant,
    companies,
    monitor,
    sources,
    storylines,
    system,
)
from newsimpact.app.config import Settings
from newsimpact.app.logs import configure_logging
from newsimpact.app.monitor import BackgroundMonitor
from newsimpact.app.wiring import Services, build_services

ROUTES = (system, companies, storylines, sources, alerts, monitor, assistant)


def create_app(services: Services | None = None) -> FastAPI:
    svc = services or build_services()
    api = ApiContext(svc, BackgroundMonitor(svc, svc.settings.monitor_every_minutes))

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        api.monitor.start()
        yield
        api.monitor.stop()

    app = FastAPI(title="NewsImpact API", version=__version__, lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        s = svc.settings
        return {"status": "ok", "version": __version__, "env": s.env, "profile": s.profile}

    signed_in = Depends(current_user(api))
    for module in ROUTES:
        app.include_router(module.router(api), dependencies=[signed_in])
    if svc.settings.web_dir.is_dir():  # the website, last so /v1 routes win
        app.mount("/", WebFiles(directory=svc.settings.web_dir, html=True), name="web")
    return app


class WebFiles(StaticFiles):
    """The website. The page itself is re-checked on every visit, so a new release shows at
    once; the built files under assets/ have the content hash in their name, so browsers
    may keep them for a year."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = (
            "public, max-age=31536000, immutable" if path.startswith("assets/") else "no-cache"
        )
        return response


def _default_app() -> FastAPI:
    configure_logging(Settings().log_level)
    return create_app()


app = _default_app()
