"""Which companies we follow, decided from the live news (methodology.json "following").

We can recognise every S&P 500 and S&P/ASX 200 company (universe.json, ~700). A company is
FOLLOWED once enough separate articles name it within a window, stays followed while it is
in the news (plus `keep_days`), and is always followed if a user follows it. Followed
companies get their own news feed each round, have their sentences read by the AI, and are
shown on the website. Each round also reads the feeds of a rotating slice of the others
("discovery"), so every index member can qualify from its own news.

decide() is the rule (pure); FollowingStore keeps the result between rounds; refresh() is
the round step. Without a universe (the demo profile) every known company is followed.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Protocol

from pydantic import Field, ValidationError

from newsimpact.shared.events import Model
from newsimpact.shared.sqlite import Database
from newsimpact.sources.models import ArticleIngested

if TYPE_CHECKING:
    from newsimpact.app.wiring import Services
    from newsimpact.semantics.models import Company


class FollowingPolicy(Model):
    min_articles: int = Field(gt=0)
    window_days: int = Field(gt=0)
    keep_days: int = Field(gt=0)
    max_followed: int = Field(gt=0)
    discover_per_round: int = Field(ge=0)


class Following(Model):
    computed_at: datetime
    followed: tuple[str, ...] = Field(description="tickers, users' choices first, then most named")
    mentions: dict[str, int] = Field(description="ticker -> articles naming it in the window")
    last_seen: dict[str, datetime] = Field(description="ticker -> latest article naming it")
    discover_from: int = Field(default=0, description="where the next discovery slice starts")


def decide(policy: FollowingPolicy, seen: Mapping[str, Sequence[datetime]], pinned: Collection[str],
           previous: Following | None, now: datetime,
           with_events: Collection[str] = ()) -> Following:  # fmt: skip
    """seen = ticker -> publication times of articles naming it (any age); with_events =
    companies with an event updated within keep_days (kept, so the event can be followed)."""
    since = now - timedelta(days=policy.window_days)
    mentions = {t: sum(d >= since for d in days) for t, days in seen.items()}
    last = {t: max(days) for t, days in seen.items() if days}
    keep_since = now - timedelta(days=policy.keep_days)
    qualifies = {t for t, n in mentions.items() if n >= policy.min_articles}
    kept = {t for t in (previous.followed if previous else ()) if last.get(t, now) >= keep_since}
    kept |= set(with_events)
    ranked = sorted(qualifies | kept, key=lambda t: (-mentions.get(t, 0), t))
    pins = sorted(set(pinned))
    followed = (
        pins + [t for t in ranked if t not in pinned][: max(0, policy.max_followed - len(pins))]
    )
    return Following(
        computed_at=now, followed=tuple(followed), last_seen=last,
        mentions={t: n for t, n in mentions.items() if n},
        discover_from=previous.discover_from if previous else 0,
    )  # fmt: skip


def feed_tickers(following: Following | None, universe: Sequence[str],
                 per_round: int) -> list[str]:  # fmt: skip
    """Followed companies, then this round's discovery slice of the others (in turn)."""
    followed = list(following.followed) if following else []
    others = [t for t in universe if t not in set(followed)]
    if not others or per_round == 0:
        return followed
    start = (following.discover_from if following else 0) % len(others)
    return followed + (others + others)[start : start + min(per_round, len(others))]


def followed_companies(svc: Services) -> list[Company]:
    """The companies the website shows: followed ones (all known ones without a universe)."""
    if svc.following_policy is None:
        return list(svc.companies)
    current = svc.following.get()
    order = {t: i for i, t in enumerate(current.followed if current else ())}
    return sorted((c for c in svc.companies if c.ticker in order), key=lambda c: order[c.ticker])


def refresh(svc: Services, now: datetime) -> Following | None:
    """Round step: recount who the news names, decide who is followed, move the discovery
    slice on, and read the recent articles of newly followed companies with the AI."""
    policy = svc.following_policy
    if policy is None:
        return None
    previous = svc.following.get()
    if previous is None:  # first decision: what the website showed until now was followed
        shown = svc.snapshots.get()
        followed = tuple(c.ticker for c in shown.companies) if shown else ()
        previous = Following(computed_at=now, followed=followed, mentions={}, last_seen={})
    horizon = now - timedelta(days=max(policy.keep_days, policy.window_days))
    recent = svc.articles.since(horizon)
    seen: dict[str, list[datetime]] = {}
    for article in recent:
        for ticker in svc.semantics.mentioned_tickers(article):
            seen.setdefault(ticker, []).append(article.published_at)
    pinned = {t for tickers in svc.alerts.followers().values() for t in tickers}
    keep_since = now - timedelta(days=policy.keep_days)
    with_events = {s.ticker for s in svc.storyline_store.all()
                   if max(e.published_at for e in s.events) >= keep_since}  # fmt: skip
    current = decide(policy, seen, pinned, previous, now, with_events)
    current = current.model_copy(
        update={"discover_from": current.discover_from + policy.discover_per_round}
    )
    svc.following.put(current)
    new = set(current.followed) - set(previous.followed if previous else ())
    if new:  # read their recent news with the AI now, not only from the next round
        window = now - timedelta(days=policy.window_days)
        for article in sorted(recent, key=lambda a: a.published_at):
            if article.published_at >= window and new & svc.semantics.mentioned_tickers(article):
                svc.bus.publish(ArticleIngested(article=article).to_envelope(
                    "/following", correlation_id=article.article_id))  # fmt: skip
    return current


# ------------------------------------------------------------------ store
class FollowingStore(Protocol):
    def get(self) -> Following | None: ...
    def put(self, following: Following) -> None: ...


class InMemoryFollowing:
    def __init__(self) -> None:
        self._f: Following | None = None

    def get(self) -> Following | None:
        return self._f

    def put(self, following: Following) -> None:
        self._f = following


class SqliteFollowing:
    """One row: the latest decision (each round replaces it)."""

    def __init__(self, db: Database) -> None:
        self._c = db.collection("following")

    def get(self) -> Following | None:
        doc = self._c.get("latest")
        try:
            return Following.model_validate_json(doc) if doc else None
        except ValidationError:  # stored by an older release: decided again next round
            return None

    def put(self, following: Following) -> None:
        self._c.put("latest", following.model_dump_json())
