"""The hourly round: the steps that turn new news into events, checks, briefs and alerts.

ROUND lists the steps in order; each is one small function. To add a step,
write the function and add one line to ROUND. Each step can also run alone
(`run_step`), e.g. as its own cloud function later.

  collect        read every enabled source (oldest first)
  follow         decide which companies we follow from who the news names (app/following.py);
                 newly followed ones have their recent articles read by the AI
  follow_up      search the listed sources for each open event's next update
  track_records  reliability learns which sources' reports others confirmed
  assess         re-check every event against evidence; market checks that were
                 "pending" mature as trading days pass
  briefs         three-line AI briefs for events whose facts changed
  publish        compute what the pages show once, store it with its time and analysis
                 version, and log companies with no news in the coverage window
  alerts         tell followers what changed (Discord, ...)

Where rounds come from is a deployment choice, not business logic: the web
server runs them every NI_MONITOR_EVERY_MINUTES (and on "Update now"); on AWS,
EventBridge Scheduler -> a function calling `run_round()`. Use NI_STORE=sqlite
so state survives restarts.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from datetime import UTC, datetime

from newsimpact.alerts.models import EventSnapshot
from newsimpact.app import following
from newsimpact.app.views import snapshot
from newsimpact.app.views.briefs import ai_brief, facts_key
from newsimpact.app.views.companies import brief_facts
from newsimpact.app.wiring import Services

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RoundResult:
    at: datetime
    new_by_source: dict[str, int]
    from_follow_up: int
    open_watches: int
    assessments_updated: int

    @property
    def new_total(self) -> int:
        return sum(self.new_by_source.values()) + self.from_follow_up


def update_track_records(svc: Services) -> None:
    """Feed validation's corroboration counts into each source's reliability."""
    weight = svc.validation.policy.unconfirmed_weight
    for r in svc.validation.track_records():
        svc.reliability.set_corroboration(r.source_id, r.confirmed, r.unconfirmed * weight)


def write_briefs(svc: Services) -> int:
    """AI briefs for events whose facts changed (views/briefs.py); returns how many were written.
    Without a language model, pages use the rules brief and nothing is stored."""
    if svc.llm is None:
        return 0
    written = 0
    for c in snapshot.current_cards(svc):
        for e in c.events:
            facts = brief_facts(c, e)
            stored = svc.briefs.get(e.event_id)
            if stored and stored.facts_key == facts_key(facts):
                continue
            brief = ai_brief(svc.llm, facts)
            if brief is not None:
                svc.briefs.put(e.event_id, brief)
                written += 1
    return written


def send_alerts(svc: Services) -> None:
    """Tell followers what changed for the companies they follow (alerts module)."""
    snapshots = [
        EventSnapshot(event_id=e.event_id, ticker=c.ticker, company=c.name, event_type=e.event_type,
                      confirmed=e.verified, updates=len(e.updates),
                      latest_update=e.updates[-1].title if e.updates else "",
                      headline=e.latest_headline, article_url=e.latest_url,
                      stock_move=e.stock_move, unusual=e.stock_move_unusual,
                      index_name=c.index_name, brief=e.brief,
                      next_step=e.checks[1].text if len(e.checks) > 1 else "")
        for c in snapshot.latest(svc).companies for e in c.events
    ]  # fmt: skip
    sent = svc.alerts.check(snapshots)
    if sent:
        log.info("alerts sent", extra={"count": len(sent)})


@dataclass
class RoundState:
    """What the steps of one round report, for the round's result."""

    new_by_source: dict[str, int] = field(default_factory=dict)
    from_follow_up: int = 0
    assessments_updated: int = 0


def _collect(svc: Services, r: RoundState) -> None:
    r.new_by_source = svc.sources.collect()


def _follow(svc: Services, r: RoundState) -> None:
    current = following.refresh(svc, datetime.now(UTC))
    if current is not None:
        log.info("following", extra={"followed": len(current.followed)})


def _follow_up(svc: Services, r: RoundState) -> None:
    r.from_follow_up = svc.sources.follow_up()


def _track_records(svc: Services, r: RoundState) -> None:
    update_track_records(svc)  # from the last assessments, so this round's scores use them


def _assess(svc: Services, r: RoundState) -> None:
    r.assessments_updated = len(svc.validation.assess_and_store(svc.storyline_store.all()))


def _briefs(svc: Services, r: RoundState) -> None:
    write_briefs(svc)


def _publish(svc: Services, r: RoundState) -> None:
    snap = snapshot.publish(svc)
    gaps = [c.ticker for c in snap.coverage if c.status == "gap"]
    if gaps:
        log.warning("companies with no news", extra={"days": snap.coverage_window_days,
                                                      "tickers": ",".join(gaps)})  # fmt: skip


def _alerts(svc: Services, r: RoundState) -> None:
    send_alerts(svc)


ROUND: tuple[tuple[str, Callable[[Services, RoundState], None]], ...] = (
    ("collect", _collect),
    ("follow", _follow),
    ("follow_up", _follow_up),
    ("track_records", _track_records),
    ("assess", _assess),
    ("briefs", _briefs),
    ("publish", _publish),
    ("alerts", _alerts),
)


def run_round(svc: Services, *, skip: Collection[str] = ()) -> RoundResult:
    """Run every step of ROUND in order (minus `skip`)."""
    if svc.llm is not None:
        svc.llm.new_round()
    r = RoundState()
    for name, step in ROUND:
        if name not in skip:
            step(svc, r)
    result = RoundResult(datetime.now(UTC), r.new_by_source, r.from_follow_up,
                         len(svc.sources.active_watches), r.assessments_updated)  # fmt: skip
    log.info("monitor round", extra={"new": result.new_total, "follow_up": r.from_follow_up})
    return result


def run_step(svc: Services, name: str) -> None:
    """Run one step alone (a separate scheduled job or cloud function)."""
    dict(ROUND)[name](svc, RoundState())


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
