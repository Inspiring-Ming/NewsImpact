"""The monitor ("Update now") and loading the demo data."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from newsimpact.app.api.context import ApiContext
from newsimpact.app.demo import run_demo
from newsimpact.app.monitor import RoundResult
from newsimpact.shared.events import Model


class MonitorStatus(Model):
    every_minutes: float
    last_round_at: str | None
    last_new_articles: int | None
    last_assessments_updated: int | None


def _status(last: RoundResult | None, every: float) -> MonitorStatus:
    return MonitorStatus(
        every_minutes=every,
        last_round_at=last.at.isoformat() if last else None,
        last_new_articles=last.new_total if last else None,
        last_assessments_updated=last.assessments_updated if last else None,
    )


def router(api: ApiContext) -> APIRouter:
    r = APIRouter()
    svc = api.svc

    @r.get("/v1/monitor", response_model=MonitorStatus)
    def monitor_status() -> MonitorStatus:
        return _status(api.monitor.last, svc.settings.monitor_every_minutes)

    @r.post("/v1/monitor/run", response_model=MonitorStatus)
    def run_monitor_round() -> MonitorStatus:
        """Run one full round now (every step in app/monitor.py ROUND)."""
        if svc.settings.profile == "demo" and not api.demo_loaded:
            raise HTTPException(409, "demo profile: load the demo data first")
        return _status(api.monitor.run_now(), svc.settings.monitor_every_minutes)

    @r.post("/v1/demo/load")
    def load_demo() -> dict[str, int]:
        if svc.settings.env == "prod" or svc.settings.profile != "demo":
            raise HTTPException(404)
        if api.demo_loaded:
            raise HTTPException(409, "demo data already loaded")
        api.demo_loaded = True
        run = run_demo(svc)
        return {"from_feeds": run.from_feeds, "from_follow_up": run.from_follow_up}

    return r
