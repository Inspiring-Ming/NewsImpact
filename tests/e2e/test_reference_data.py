"""The real reference data loads, and the live profile wires up without touching the network."""

import json
from pathlib import Path

from newsimpact.app.config import Settings
from newsimpact.app.wiring import FEED_KINDS, build_services

REFERENCE = Path(__file__).resolve().parents[2] / "data" / "reference"


def test_live_profile_tracks_the_curated_outlets() -> None:
    svc = build_services(Settings(env="test", profile="live"))
    listed = svc.sources.listed()
    assert len(listed) >= 5
    assert all(feed.kind in FEED_KINDS for s in listed for feed in s.feeds)
    assert {s.source_id for s in svc.reliability.sources()} == {s.source_id for s in listed}
    assert svc.market is None  # no fake prices in the live profile


def test_every_entity_alias_maps_to_a_ticker() -> None:
    aliases = json.loads((REFERENCE / "entities.json").read_text())["aliases"]
    assert all(isinstance(t, str) and t.isupper() for t in aliases.values())
