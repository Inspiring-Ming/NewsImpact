"""Companies and their events, as the website and API show them.

Glue only: every rule and number comes from the modules (and the guidance rules
beside this file); this file gathers and shapes them per company and event.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Literal

from pydantic import Field

from newsimpact.app.following import followed_companies
from newsimpact.app.views.briefs import facts_key, rules_brief
from newsimpact.app.views.guidance import (
    Check,
    GroupRecord,
    Priority,
    checks,
    close_after,
    group_record,
    priority,
)
from newsimpact.market.models import ChannelObservation
from newsimpact.semantics.models import Company
from newsimpact.shared.events import Model
from newsimpact.sources.models import Article, SourceType
from newsimpact.storylines.models import Expectation, Playbook, ResearchFinding, Storyline
from newsimpact.validation.logic import overlapping
from newsimpact.validation.models import Assessment

if TYPE_CHECKING:  # type hints only: the wiring builds the stores these views use
    from newsimpact.app.wiring import Services


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
    event_type: str = Field(description="e.g. Leadership change, Results")
    reading: str | None = Field(
        default=None,
        description="for events that can read either way (results): 'better than expected', "
        "'worse than expected', or 'mixed' when the reports disagree",
    )
    updates: tuple[UpdateItem, ...]
    latest_headline: str
    latest_source: str
    latest_url: str = Field(description="link to the original article")
    verified: bool = Field(
        description="an update has 2+ independent sources, or came from the company or a filing"
    )
    stock_move: float | None = Field(description="stock return minus its index, e.g. -0.185")
    stock_move_unusual: bool = Field(description="larger than on 19 of 20 normal trading days")
    stock_move_period: str = Field(description="the trading days the move covers, e.g. '9-11 Nov'")
    move_from: date | None = Field(default=None, description="first trading day of the move")
    move_to: date | None = Field(default=None, description="last close of the move")
    shares_move_with: tuple[str, ...] = Field(
        default=(),
        description="other events of this company measured over overlapping days: "
        "the move cannot be split between them",
    )
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
    volume_ratio: float | None = Field(description="highest trading volume vs normal, e.g. 3.7")
    tone: float = Field(description="sentiment of the latest update, -1 (negative) to 1")
    is_rumour: bool = Field(description="the latest update is hedged or rumoured")
    next_update: str | None = Field(description="the possible next step (research), if any")
    role: Literal["buyer", "target", "seller"] | None = Field(
        default=None, description="the company's part in a deal, read from the reports"
    )
    spark: tuple[float, ...] = Field(
        default=(),
        description="stock minus its index at each close, 0 = the close before the "
        "event; starts a few days before it (for a small line chart)",
    )
    spark_event_at: int | None = Field(default=None, description="index in spark of the event day")
    expectation: Expectation | None = Field(
        default=None, description="the usual share price move for this case, with its source"
    )
    link_window_days: int | None = Field(description="how long new reports join this event")
    final_measure_on: date | None = Field(description="close after which the move is final")
    # Guidance (views/guidance.py) and the brief (views/briefs.py), filled in by companies()
    priority: Priority = "background"
    priority_reason: str = ""
    checks: tuple[Check, ...] = ()
    record: GroupRecord | None = Field(
        default=None, description="how past events of this type and case moved the stock"
    )
    brief: tuple[str, ...] = ()
    brief_by: Literal["ai", "rules"] = "rules"


class CompanyCard(Model):
    ticker: str
    name: str
    country: str
    sector: str
    exchange: str
    index_name: str = Field(description="the index the stock is compared with, e.g. S&P 500")
    articles: int = Field(description="articles naming the company in the pages window")
    articles_24h: int = Field(description="of those, published in the last 24 hours")
    articles_24h_by_source: dict[str, int] = Field(description="source name -> those articles")
    latest_news: NewsItem | None
    events: tuple[EventCard, ...]


def mentions(svc: Services, articles: Sequence[Article]) -> dict[str, list[Article]]:
    """Ticker -> the given articles that name the company (name matching only, no AI)."""
    by_ticker: dict[str, list[Article]] = defaultdict(list)
    for article in articles:
        for ticker in svc.semantics.mentioned_tickers(article):
            by_ticker[ticker].append(article)
    return by_ticker


def companies(svc: Services, by_ticker: dict[str, list[Article]]) -> list[CompanyCard]:
    """Every company we follow, with its events (most recent first) and its news in the
    pages window (`by_ticker`). Pages read these from the snapshot, computed once per round."""
    names = source_names(svc)
    followed = followed_companies(svc)
    tickers = {c.ticker for c in followed}
    storylines = [s for s in svc.storyline_store.all() if s.ticker in tickers]
    articles = {a.article_id: a for news in by_ticker.values() for a in news}
    for article_id in {r.article_id for s in storylines for e in s.events for r in e.reports}:
        if article_id not in articles and (article := svc.articles.get(article_id)):
            articles[article_id] = article  # an older event keeps its own articles
    events: dict[str, list[EventCard]] = defaultdict(list)
    for storyline in storylines:
        events[storyline.ticker].append(_event_card(svc, storyline, names, articles))
    cards = [_company_card(svc, c, by_ticker.get(c.ticker, []), events.get(c.ticker, []), names)
             for c in followed]  # fmt: skip
    cards = _with_guidance(svc, cards)

    def latest(c: CompanyCard) -> float:  # newest update of any event
        if c.events:
            return max(e.updates[-1].published_at for e in c.events).timestamp()
        return c.latest_news.published_at.timestamp() if c.latest_news else 0.0

    return sorted(cards, key=lambda c: (not c.events, -latest(c), c.name))


EXPECTED_WORDS = {
    "up": "a rise",
    "down": "a fall",
    "flat": "no unusual move",
    "uncertain": "a larger move than usual, either way",
}


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
    # The research for this event's own case (e.g. 'company is the buyer'), else the lead one.
    finding = e.expectation or (e.research[0] if e.research else None)
    r = e.record
    return {
        "company": c.name, "ticker": c.ticker, "sector": c.sector, "event_type": e.event_type,
        "reading": e.reading,
        "updates": [f"{u.published_at:%-d %b}: {u.title}" for u in e.updates],
        "latest_update": e.updates[-1].title if e.updates else e.event_type,
        "headline": e.latest_headline, "confirmed": e.verified,
        "sources": list(e.source_names), "rumour": e.is_rumour, "market": market,
        "volume": f"{e.volume_ratio:.1f}x a normal day" if e.volume_ratio else None,
        "research": finding.finding if finding else None,
        "research_source": finding.source if finding else None,
        "expected": (f"{e.expectation.label}: research expects "
                     f"{EXPECTED_WORDS[e.expectation.expected]} ({e.expectation.source})"
                     if e.expectation else None),
        "past_record": (f"{r.n} past {e.event_type} events ({r.label}) measured: average move "
                        f"{r.average * 100:+.1f}%, {r.met} of {r.n} as research expects"
                        if r and r.n and r.average is not None else None),
        "next_update": e.next_update,
    }  # fmt: skip


def _with_guidance(svc: Services, cards: list[CompanyCard]) -> list[CompanyCard]:
    """Add each event's priority, checks, its type's track record and its brief."""
    cards = [_with_shared_moves(c) for c in cards]
    records = type_records(svc, cards)
    now = datetime.now(UTC)
    out = []
    for c in cards:
        events = []
        for e in c.events:
            level, reason = priority(confirmed=e.verified, unusual=e.stock_move_unusual,
                                     last_update=e.updates[-1].published_at, now=now)  # fmt: skip
            e = e.model_copy(update={
                "priority": level, "priority_reason": reason,
                "record": _without(records.get((e.event_type, e.expectation.label)), e, svc, cards)
                if e.expectation else None,
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


def _with_shared_moves(card: CompanyCard) -> CompanyCard:
    """Mark events of one company whose measured days overlap: the stock had one move on
    those days, and it cannot be split between the events."""
    spans = [(e, e.move_from, e.move_to) for e in card.events if e.move_from and e.move_to]
    shared = {e.event_id: tuple(o.event_type for o, f2, t2 in spans
                                if o is not e and f1 <= t2 and f2 <= t1)
              for e, f1, t1 in spans}  # fmt: skip
    return card.model_copy(
        update={
            "events": tuple(
                e.model_copy(update={"shares_move_with": shared.get(e.event_id, ())})
                for e in card.events
            )
        }
    )


def _without(record: GroupRecord | None, e: EventCard, svc: Services,
             cards: Sequence[CompanyCard]) -> GroupRecord | None:  # fmt: skip
    """This event's case record from the OTHER events (an event is not its own evidence)."""
    if record is None or e.stock_move is None or e.shares_move_with:
        return record
    return type_records(svc, cards, skip=e.event_id).get((e.event_type, record.label), record)


def type_records(svc: Services, cards: Sequence[CompanyCard], skip: str = ""
                 ) -> dict[tuple[str, str], GroupRecord]:  # fmt: skip
    """(event type, case) -> how its measured events moved, against the research. A move
    shared with another event of the same company is left out: it cannot be attributed."""
    moves: dict[tuple[str, str], list[tuple[float, bool]]] = defaultdict(list)
    cases: dict[tuple[str, str], Expectation] = {}
    for c in cards:
        for e in c.events:
            if e.expectation is None:
                continue
            key = (e.event_type, e.expectation.label)
            cases[key] = e.expectation
            if e.stock_move is not None and not e.shares_move_with and e.event_id != skip:
                moves[key].append((e.stock_move, e.stock_move_unusual))
    policy = svc.validation.policy
    return {key: group_record(exp, moves[key], min_events=policy.min_events_for_calibration,
                              z_needed=policy.significance_z)
            for key, exp in cases.items()}  # fmt: skip


def expectation(svc: Services, storyline: Storyline, playbook: Playbook | None,
                reading: str | None) -> tuple[Literal["buyer", "target", "seller"] | None,
                                              Expectation | None]:  # fmt: skip
    """The company's part in a deal (if this type depends on it) and the expected move."""
    if playbook is None:
        return None, None
    events = sorted(storyline.events, key=lambda e: e.published_at)
    opening = (
        playbook.stages[events[0].stage].name if events[0].stage < len(playbook.stages) else ""
    )
    role = None
    if any(x.when in ROLES for x in playbook.expectations):
        role = svc.semantics.deal_role(storyline.ticker, [e.summary for e in events])
        return role, playbook.expectation((role or "role unclear", opening))
    return None, playbook.expectation((reading, opening))


ROLES = ("buyer", "target", "seller")


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
    svc: Services, storyline: Storyline, channel: str, at: datetime
) -> ChannelObservation | None:
    """A market measure for the first update even when the playbook expects no reaction in
    that channel, so every event shows its stock move and trading volume. None = not yet."""
    if svc.market is None:
        return None
    try:
        return svc.market.observe(storyline.ticker, channel, at)
    except ValueError:  # too early (WindowNotComplete) or no data from the vendor
        return None


def _measure(svc: Services, storyline: Storyline, channel: str, at: datetime) -> float | None:
    o = _observe(svc, storyline, channel, at)
    return o.value if o else None


SPARK_DAYS_BEFORE = 5  # trading days shown before the event, so the line shows its reaction


def _measured_days(
    svc: Services,
    storyline: Storyline,
    a: Assessment,
    move: ChannelObservation | None,
    first_at: datetime,
) -> tuple[date, date] | None:
    """The trading days a reported move covers: the event day of the update it was measured
    for (or of the first and last of a run of close updates, measured as one) to the last
    close of the price window."""
    if move is None or svc.market is None:
        return None
    stamps = [st.published_at for st in a.stages]
    if move is a.combined_reaction and any(overlapping(stamps, svc.validation.policy)):
        close = overlapping(stamps, svc.validation.policy)
        i = close.index(True) - 1
        j = i + 1
        while j + 1 < len(close) and close[j + 1]:
            j += 1
        start, end = stamps[i], stamps[j]
    else:
        start = end = next((st.published_at for st in a.stages for d in st.decisions
                            if d.evidence is move), first_at)  # fmt: skip
    ticker = storyline.ticker
    return (
        svc.market.event_day(ticker, start),
        close_after(svc.market.event_day(ticker, end), svc.market_policy.windows["price"][1]),
    )


def _vs_index(svc: Services, storyline: Storyline) -> list[tuple[date, float]]:
    """Stock return minus its index, each close from a few days before the first update to the
    latest close, relative to the close before the first update (0 = no difference)."""
    if svc.market is None:
        return []
    first = min(e.published_at for e in storyline.events)
    day = svc.market.event_day(storyline.ticker, first)
    try:
        path = svc.market.price_path(
            storyline.ticker, day - timedelta(days=14), datetime.now(UTC).date()
        )
    except ValueError:
        return []
    before = [p for p in path.points if p.day < day]
    if not before or path.points[-1].day < day:
        return []
    base = before[-1]
    shown = path.points[max(0, len(before) - SPARK_DAYS_BEFORE) :]
    return [(p.day, round((p.stock / base.stock) - (p.benchmark / base.benchmark), 5))
            for p in shown]  # fmt: skip


def _reading(storyline: Storyline, playbook: Playbook | None) -> str | None:
    """What the reports say, for stages that can read either way (playbook "readings"):
    one reading, or "mixed" when the sources disagree."""
    if playbook is None:
        return None
    found = set()
    for e in storyline.events:
        readings = playbook.stages[e.stage].readings if e.stage < len(playbook.stages) else {}
        found |= {readings[t] for t in (e.event_type, *(r.event_type for r in e.reports))
                  if t in readings}  # fmt: skip
    if not found:
        return None
    return found.pop() if len(found) == 1 else "mixed"


def _event_card(
    svc: Services, storyline: Storyline, names: dict[str, str], articles: dict[str, Article]
) -> EventCard:
    a: Assessment = svc.validation.latest(storyline.storyline_id) or svc.validation.assess(
        storyline
    )
    playbook = next((p for p in svc.playbooks.playbooks() if p.theme == storyline.theme), None)
    titles = {st.name: st.title for st in playbook.stages} if playbook else {}

    def title(name: str) -> str:
        return titles.get(name) or name.replace("_", " ").capitalize()

    latest = max(storyline.events, key=lambda e: e.published_at)
    latest_article = articles.get(latest.article_id)
    reports = {(e.stage, e.published_at): e.reports for e in storyline.events}
    prices = [d.evidence for st in a.stages for d in st.decisions
              if d.evidence is not None and d.evidence.channel == "price"]  # fmt: skip
    pending = a.combined_pending or any(d.channel == "price" and d.verdict == "pending"
                                        for st in a.stages for d in st.decisions)  # fmt: skip
    # While any update's window is still open, one update's move is not the event's move:
    # show the provisional move so far over the whole event instead (status "pending").
    move = a.combined_reaction or (
        None if pending else max(prices, key=lambda o: abs(o.statistic or 0), default=None)
    )
    source_ids = sorted({o for st in a.stages for o in st.claim.outlets})
    latest_sources = next(
        (st.claim.outlets for st in a.stages if st.published_at == latest.published_at), ()
    )
    first_at = min(e.published_at for e in storyline.events)
    if move is None and not pending:  # this type expects no price reaction: measure anyway
        move = _observe(svc, storyline, "price", first_at)
    if move is None and not pending and svc.market is not None:  # too recent to have closes yet
        end = close_after(
            svc.market.event_day(storyline.ticker, first_at), svc.market_policy.windows["price"][1]
        )
        pending = end >= datetime.now(UTC).date()
    status = "measured" if move else "pending" if pending else "no_data"
    days = _measured_days(svc, storyline, a, move, first_at)
    reading = _reading(storyline, playbook)
    role, expected = expectation(svc, storyline, playbook, reading)
    vs_index = _vs_index(svc, storyline)
    so_far = (vs_index[-1][1], vs_index[-1][0]) if status == "pending" and vs_index else None
    return EventCard(
        event_id=storyline.storyline_id,
        reading=reading,
        role=role,
        expectation=expected,
        spark=tuple(v for _, v in vs_index),
        spark_event_at=next((i for i, (d, _) in enumerate(vs_index)
                             if d >= svc.market.event_day(storyline.ticker, first_at)), None)
        if vs_index and svc.market else None,
        event_type=(playbook.title if playbook and playbook.title else storyline.theme),
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
        or any(r.source_type in AUTHORITATIVE for e in storyline.events for r in e.reports),
        # Titles are joined to the body with ". " for sentence splitting; drop that extra stop.
        latest_headline=latest.summary.replace("?.", "?").replace("!.", "!"),
        latest_source=names.get(latest_sources[0], latest_sources[0]) if latest_sources else "",
        stock_move=move.value if move else None,
        stock_move_unusual=bool(move and move.significant),
        stock_move_period=(f"{days[0]:%-d %b}" if days and days[0] == days[1] else
                           f"{days[0]:%-d %b}-{days[1]:%-d %b}" if days else ""),
        move_from=days[0] if days else None,
        move_to=days[1] if days else None,
        stock_move_status=status,
        link_window_days=playbook.link_window_days if playbook else None,
        final_measure_on=(close_after(svc.market.event_day(storyline.ticker, first_at),
                                      svc.market_policy.windows["price"][1])
                          if status == "pending" and svc.market else None),
        move_so_far=so_far[0] if so_far else None,
        so_far_through=so_far[1] if so_far else None,
        sources=len(source_ids),
        source_names=tuple(names.get(s, s) for s in source_ids),
        notes=a.suggestions,
        research=playbook.research if playbook else (),
        watch=playbook.watch if playbook else (),
        volume_ratio=max((d.evidence.value for st in a.stages for d in st.decisions
                          if d.evidence is not None and d.evidence.channel == "volume"),
                         default=None) or _measure(svc, storyline, "volume", first_at),
        tone=latest.tone,
        is_rumour=latest.is_rumour,
        next_update=(title(playbook.stages[storyline.max_stage + 1].name)
                     if playbook and storyline.status.value != "resolved"
                     and storyline.max_stage + 1 < len(playbook.stages) else None),
    )  # fmt: skip
