"""Automatic monitoring: collect from every listed outlet, chase follow-ups, repeat.

One round:
  1. sources.collect()                read every enabled outlet (oldest first)
  2. sources.follow_up()              search listed outlets for next stages
  3. update_track_records()           reliability learns which sources' reports
                                      other sources later confirmed
  4. validation.assess_and_store()    re-check every storyline against evidence
                                      (claims re-scored with current reliability);
                                      market checks that were "pending" mature
                                      as trading days pass
Where rounds come from is a deployment choice, not business logic:
  * the web server:  NI_MONITOR_EVERY_MINUTES=15 runs BackgroundMonitor; the
                     website's "Run a round now" button triggers one on demand
  * AWS:             EventBridge Scheduler -> Lambda calling `run_round()`
Use NI_STORE=sqlite so state survives restarts.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import UTC, datetime

from newsimpact.app.wiring import Services

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RoundResult:
    at: datetime
    new_by_outlet: dict[str, int]
    from_follow_up: int
    open_watches: int
    assessments_updated: int

    @property
    def new_total(self) -> int:
        return sum(self.new_by_outlet.values()) + self.from_follow_up


def update_track_records(svc: Services) -> None:
    """Feed validation's corroboration counts into each source's reliability."""
    weight = svc.validation.policy.unconfirmed_weight
    for r in svc.validation.track_records():
        svc.reliability.set_corroboration(r.source_id, r.confirmed, r.unconfirmed * weight)


def run_round(svc: Services, *, follow_up: bool = True) -> RoundResult:
    if svc.llm is not None:
        svc.llm.new_round()
    counts = svc.sources.collect()
    found = svc.sources.follow_up() if follow_up else 0
    update_track_records(svc)  # from the last assessments, so this round's scores use them
    updated = svc.validation.assess_and_store(svc.storyline_store.all())
    result = RoundResult(datetime.now(UTC), counts, found, len(svc.sources.active_watches),
                         len(updated))  # fmt: skip
    log.info("monitor round", extra={"new": result.new_total, "follow_up": found})
    return result


class BackgroundMonitor:
    """Runs rounds on a timer inside the web server; one round at a time."""

    def __init__(self, svc: Services, every_minutes: float) -> None:
        self._svc = svc
        self._every = every_minutes
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.last: RoundResult | None = None

    def start(self) -> None:
        if self._every > 0 and self._thread is None:
            self._thread = threading.Thread(target=self._loop, name="monitor", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def run_now(self) -> RoundResult:
        with self._lock:
            self.last = run_round(self._svc)
            return self.last

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_now()
            except Exception:
                log.exception("monitor round failed")
            self._stop.wait(self._every * 60)
