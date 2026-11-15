"""Companies and their events, as the website and API show them.

Glue only: every rule and number comes from the modules (and the guidance rules
beside this file); this file gathers and shapes them per company and event.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from pydantic import Field

from newsimpact.app.views.briefs import facts_key, rules_brief
from newsimpact.app.views.guidance import (
    Check,
    Priority,
    TypeRecord,
    checks,
    close_after,
    priority,
    type_record,
)
from newsimpact.app.wiring import Services
from newsimpact.market.models import ChannelObservation
from newsimpact.semantics.models import Company
from newsimpact.shared.events import Model
from newsimpact.sources.models import Article, SourceType
from newsimpact.storylines.models import ResearchFinding, Storyline
from newsimpact.validation.models import Assessment


class NewsItem(Model):
    title: str
    url: str
    source: str
    published_at: datetime


class UpdateItem(Model):
    title: str
    published_at: datetime
    articles: tuple[NewsItem, ...] = Field(description="the original articles, one per source")


class EventCard(Model):
    event_id: str
    event_type: str = Field(description="e.g. Leadership change, Earnings miss")
    updates: tuple[UpdateItem, ...]
    latest_headline: str
    latest_source: str
    latest_url: str = Field(description="link to the original article")
    verified: bool = Field(
        description="an update has 2+ independent sources, or came from the company or a filing"
    )
    stock_move: float | None = Field(description="stock return minus its index, e.g. -0.185")
    stock_move_unusual: bool = Field(description="larger than on 19 of 20 normal trading days")
    stock_move_period: str = Field(description="e.g. '9-13 Nov'")
    move_so_far: float | None = Field(
        description="provisional stock move vs its index to the latest close, while pending"
    )
    so_far_through: date | None = Field(description="the latest close in move_so_far")
    stock_move_status: str = Field(
        description="measured | pending (the reaction window has not closed yet) | no_data"
    )
    sources: int = Field(description="independent news sources that reported the event")
    source_names: tuple[str, ...]
    notes: tuple[str, ...] = Field(description="status of the checks, e.g. what is still pending")
    research: tuple[ResearchFinding, ...] = Field(description="how markets usually react, cited")
    watch: tuple[str, ...] = Field(description="what investors typically check next")
    stages_total: int = Field(description="updates this kind of event usually has")
    volume_ratio: float | None = Field(description="highest trading volume vs normal, e.g. 3.7")
    tone: float = Field(description="sentiment of the latest update, -1 (negative) to 1")
    is_rumour: bool = Field(description="the latest update is hedged or rumoured")
    next_update: str | None = Field(description="the update this kind of event usually brings next")
    link_window_days: int | None = Field(description="how long new reports join this event")
    final_measure_on: date | None = Field(description="close after which the move is final")
    # Guidance (views/guidance.py) and the brief (views/briefs.py), filled in by companies()
    priority: Priority = "background"
    priority_reason: str = ""
    checks: tuple[Check, ...] = ()
    record: TypeRecord | None = Field(default=None, description="this event type's track record")
    brief: tuple[str, ...] = ()
    brief_by: Literal["ai", "rules"] = "rules"


class CompanyCard(Model):
    ticker: str
    name: str
    country: str
    sector: str
    exchange: str
    index_name: str = Field(description="the index the stock is compared with, e.g. S&P 500")
    articles: int = Field(description="stored articles that name the company")
    articles_24h: int = Field(description="of those, published in the last 24 hours")
    articles_24h_by_source: dict[str, int] = Field(description="source name -> those articles")
    latest_news: NewsItem | None
    events: tuple[EventCard, ...]


def companies(svc: Services) -> list[CompanyCard]:
    """Every company we follow, with its events (most recent first) and latest news."""
    names = source_names(svc)
    mentions: dict[str, list[Article]] = defaultdict(list)
    articles = {a.article_id: a for a in svc.articles.recent(10**6)}
    for article in articles.values():
        for ticker in svc.semantics.mentioned_tickers(article):
            mentions[ticker].append(article)
    events: dict[str, list[EventCard]] = defaultdict(list)
    for story in svc.storyline_store.all():
        events[story.ticker].append(_event_card(svc, story, names, articles))
    cards = [_company_card(svc, c, mentions.get(c.ticker, []), events.get(c.ticker, []), names)
             for c in svc.companies]  # fmt: skip
    cards = _with_guidance(svc, cards)

    def latest(c: CompanyCard) -> float:  # newest update of any event
        if c.events:
            return max(e.updates[-1].published_at for e in c.events).timestamp()
        return c.latest_news.published_at.timestamp() if c.latest_news else 0.0

    return sorted(cards, key=lambda c: (not c.events, -latest(c), c.name))


def event_summary(svc: Services, event_id: str) -> CompanyCard | None:
    """The company card for one event (the event page). Built from the full list, because
    the event's priority and track record compare it with every other event."""
    for card in companies(svc):
        for e in card.events:
            if e.event_id == event_id:
                return card.model_copy(update={"events": (e,)})
    return None


def brief_facts(c: CompanyCard, e: EventCard) -> dict[str, object]:
    """Everything a brief may say, as plain values (the AI may use nothing else)."""
    if e.stock_move is not None:
        side = "worse" if e.stock_move < 0 else "better"
        market = (
            f"The stock did {abs(e.stock_move) * 100:.1f}% {side} than the {c.index_name} "
            f"({e.stock_move_period}), "
            f"{'an unusual move' if e.stock_move_unusual else 'within its normal range'}."
        )
    elif e.move_so_far is not None:
        side = "worse" if e.move_so_far < 0 else "better"
        market = (
            f"So far {abs(e.move_so_far) * 100:.1f}% {side} than the {c.index_name} to the "
            f"close of {e.so_far_through}; provisional until the window closes."
        )
    else:
        market = "The stock reaction is not measured yet."
    finding = e.research[0] if e.research else None
    r = e.record
    return {
        "company": c.name, "ticker": c.ticker, "sector": c.sector, "event_type": e.event_type,
        "updates": [f"{u.published_at:%-d %b}: {u.title}" for u in e.updates],
        "latest_update": e.updates[-1].title if e.updates else e.event_type,
        "headline": e.latest_headline, "confirmed": e.verified,
        "sources": list(e.source_names), "rumour": e.is_rumour, "market": market,
        "volume": f"{e.volume_ratio:.1f}x a normal day" if e.volume_ratio else None,
        "research": finding.finding if finding else None,
        "research_source": finding.source if finding else None,
        "past_record": (f"{r.n} past {e.event_type} events measured: average move "
                        f"{r.average * 100:+.1f}%, {r.as_expected} of {r.n} as expected"
                        if r and r.n and r.average is not None else None),
        "next_update": e.next_update,
    }  # fmt: skip


def _with_guidance(svc: Services, cards: list[CompanyCard]) -> list[CompanyCard]:
    """Add each event's priority, checks, its type's track record and its brief."""
    playbooks = {p.title or p.theme: p for p in svc.playbooks.playbooks()}
    moves: dict[str, list[tuple[float, bool]]] = defaultdict(list)
    for c in cards:
        for e in c.events:
            if e.stock_move is not None:
                moves[e.event_type].append((e.stock_move, e.stock_move_unusual))
    now = datetime.now(UTC)
    out = []
    for c in cards:
        events = []
        for e in c.events:
            level, reason = priority(confirmed=e.verified, unusual=e.stock_move_unusual,
                                     last_update=e.updates[-1].published_at, now=now)  # fmt: skip
            e = e.model_copy(update={
                "priority": level, "priority_reason": reason,
                "record": type_record(playbooks.get(e.event_type), moves[e.event_type]),
                "checks": tuple(checks(url=e.latest_url, confirmed=e.verified,
                                       unusual=e.stock_move_unusual, final_on=e.final_measure_on,
                                       sector=c.sector, next_update=e.next_update,
                                       window_days=e.link_window_days)),
            })  # fmt: skip
            facts = brief_facts(c, e)
            stored = svc.briefs.get(e.event_id)
            brief = (
                stored if stored and stored.facts_key == facts_key(facts) else rules_brief(facts)
            )
            events.append(e.model_copy(update={"brief": brief.bullets, "brief_by": brief.by}))
        out.append(c.model_copy(update={"events": tuple(events)}))
    return out


def source_names(svc: Services) -> dict[str, str]:
    return {s.source_id: s.name.split(" - ")[0] for s in svc.sources.listed()}


def _company_card(
    svc: Services,
    company: Company,
    news: list[Article],
    events: list[EventCard],
    names: dict[str, str],
) -> CompanyCard:
    latest = max(news, key=lambda a: a.published_at, default=None)
    day_ago = datetime.now(UTC) - timedelta(days=1)
    return CompanyCard(
        ticker=company.ticker, name=company.name, country=company.country, sector=company.sector,
        exchange=svc.market_policy.exchange_of(company.ticker),
        index_name=_index_name(svc, company.ticker), articles=len(news),
        articles_24h=sum(day_ago <= a.published_at for a in news),
        articles_24h_by_source=dict(Counter(names.get(a.source_id, a.source_id)
                                            for a in news if day_ago <= a.published_at)),
        latest_news=NewsItem(title=latest.title, url=latest.url,
                             source=names.get(latest.source_id, latest.source_id),
                             published_at=latest.published_at) if latest else None,
        # Lead with verified news, then the most recent: a single-source misreading
        # must not hide a confirmed event.
        events=tuple(sorted(events, key=lambda e: (e.verified, e.updates[-1].published_at),
                            reverse=True)),
    )  # fmt: skip


def _index_name(svc: Services, ticker: str) -> str:
    if svc.settings.profile == "demo":
        return "market index"
    return svc.market_policy.exchanges[svc.market_policy.exchange_of(ticker)].benchmark_name


AUTHORITATIVE = (SourceType.REGULATORY_FILING, SourceType.COMPANY_PRESS_RELEASE)


def _news(article: Article, names: dict[str, str]) -> NewsItem:
    return NewsItem(title=article.title, url=article.url, published_at=article.published_at,
                    source=names.get(article.source_id, article.source_id))  # fmt: skip


def _observe(
    svc: Services, story: Storyline, channel: str, at: datetime
) -> ChannelObservation | None:
    """A market measure for the first update even when the playbook expects no reaction in
    that channel, so every event shows its stock move and trading volume. None = not yet."""
    if svc.market is None:
        return None
    try:
        return svc.market.observe(story.ticker, channel, at)
    except ValueError:  # too early (WindowNotComplete) or no data from the vendor
        return None


def _measure(svc: Services, story: Storyline, channel: str, at: datetime) -> float | None:
    o = _observe(svc, story, channel, at)
    return o.value if o else None


def _so_far(svc: Services, story: Storyline) -> tuple[float, date] | None:
    """Stock return minus its index from the close before the first update to the latest
    close: what the market has done so far while the measured window is still open."""
    if svc.market is None:
        return None
    first = min(e.published_at for e in story.events)
    day = svc.market.event_day(story.ticker, first)
    try:
        path = svc.market.price_path(story.ticker, day - timedelta(days=10), date.today())
    except ValueError:
        return None
    before = [p for p in path.points if p.day < day]
    if not before or path.points[-1].day < day:
        return None
    base, last = before[-1], path.points[-1]
    return (last.stock / base.stock) - (last.benchmark / base.benchmark), last.day


def _event_card(
    svc: Services, story: Storyline, names: dict[str, str], articles: dict[str, Article]
) -> EventCard:
    a: Assessment = svc.validation.latest(story.storyline_id) or svc.validation.assess(story)
    playbook = next((p for p in svc.playbooks.playbooks() if p.theme == story.theme), None)
    titles = {st.name: st.title for st in playbook.stages} if playbook else {}

    def title(name: str) -> str:
        return titles.get(name) or name.replace("_", " ").capitalize()

    latest = max(story.events, key=lambda e: e.published_at)
    latest_article = articles.get(latest.article_id)
    reports = {(e.stage, e.published_at): e.reports for e in story.events}
    prices = [d.evidence for st in a.stages for d in st.decisions
              if d.evidence is not None and d.evidence.channel == "price"]  # fmt: skip
    move = a.combined_reaction or max(prices, key=lambda o: abs(o.statistic or 0), default=None)
    first, last = a.stages[0].published_at, a.stages[-1].published_at
    period = (f"{first:%-d %b}" if first.date() == last.date()
              else f"{first:%-d %b}-{last:%-d %b}")  # fmt: skip
    source_ids = sorted({o for st in a.stages for o in st.claim.outlets})
    latest_sources = next(
        (st.claim.outlets for st in a.stages if st.published_at == latest.published_at), ()
    )
    first_at = min(e.published_at for e in story.events)
    if move is None:  # this event type expects no price reaction: measure it anyway
        move = _observe(svc, story, "price", first_at)
    pending = any(d.channel == "price" and d.verdict == "pending"
                  for st in a.stages for d in st.decisions)  # fmt: skip
    status = "measured" if move else "pending" if pending else "no_data"
    so_far = _so_far(svc, story) if status == "pending" else None
    return EventCard(
        event_id=story.storyline_id,
        event_type=(playbook.title if playbook and playbook.title else story.theme),
        updates=tuple(
            UpdateItem(title=title(st.stage_name), published_at=st.published_at,
                       articles=tuple(_news(articles[r.article_id], names)
                                      for r in reports.get((st.stage, st.published_at), ())
                                      if r.article_id in articles))
            for st in a.stages
        ),
        latest_url=latest_article.url if latest_article else "",
        # Verified = facts that cannot be misread: 2+ independent origins, or published by
        # the company itself or a regulator. Wording that merely quotes the company does not
        # count (the attribution reading can be wrong, and one outlet is still one source).
        verified=any(len(st.claim.origins) >= svc.validation.policy.corroborating_origins
                     for st in a.stages)
        or any(r.source_type in AUTHORITATIVE for e in story.events for r in e.reports),
        # Titles are joined to the body with ". " for sentence splitting; drop that extra stop.
        latest_headline=latest.summary.replace("?.", "?").replace("!.", "!"),
        latest_source=names.get(latest_sources[0], latest_sources[0]) if latest_sources else "",
        stock_move=move.value if move else None,
        stock_move_unusual=bool(move and move.significant),
        stock_move_period=period,
        stock_move_status=status,
        link_window_days=playbook.link_window_days if playbook else None,
        final_measure_on=(close_after(svc.market.event_day(story.ticker, first_at),
                                      svc.market_policy.windows["price"][1])
                          if status == "pending" and svc.market else None),
        move_so_far=so_far[0] if so_far else None,
        so_far_through=so_far[1] if so_far else None,
        sources=len(source_ids),
        source_names=tuple(names.get(s, s) for s in source_ids),
        notes=a.suggestions,
        research=playbook.research if playbook else (),
        watch=playbook.watch if playbook else (),
        stages_total=len(playbook.stages) if playbook else len(a.stages),
        volume_ratio=max((d.evidence.value for st in a.stages for d in st.decisions
                          if d.evidence is not None and d.evidence.channel == "volume"),
                         default=None) or _measure(svc, story, "volume", first_at),
        tone=latest.tone,
        is_rumour=latest.is_rumour,
        next_update=(title(playbook.stages[story.max_stage + 1].name)
                     if playbook and story.status.value != "resolved"
                     and story.max_stage + 1 < len(playbook.stages) else None),
    )  # fmt: skip
