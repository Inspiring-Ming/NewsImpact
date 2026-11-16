"""Run the fictional demo (data/demo) through the real pipeline. Used by the API and tests."""

from __future__ import annotations

import json
from dataclasses import dataclass

from newsimpact.app.views import snapshot
from newsimpact.app.wiring import Services


@dataclass(frozen=True)
class DemoRun:
    from_feeds: int
    from_follow_up: int


def seed_track_record(svc: Services) -> None:
    """Past claim outcomes, so each demo outlet starts with a track record."""
    raw = json.loads((svc.settings.demo_dir / "track_record.json").read_text())
    for row in raw["track_record"]:
        for _ in range(row["supported"]):
            svc.reliability.record_outcome(row["source_id"], "all", supported=True)
        for _ in range(row["refuted"]):
            svc.reliability.record_outcome(row["source_id"], "all", supported=False)


def run_demo(svc: Services) -> DemoRun:
    """Seed track records, read feeds, chase follow-ups, then check evidence (one round)."""
    if svc.settings.profile != "demo":
        raise ValueError("the demo needs NI_PROFILE=demo")
    seed_track_record(svc)
    from_feeds = sum(svc.sources.collect().values())
    run = DemoRun(from_feeds=from_feeds, from_follow_up=svc.sources.follow_up())
    svc.validation.assess_and_store(svc.storyline_store.all())  # as a monitoring round does
    snapshot.publish(svc)  # pages read this, as after a round
    return run
