"""Read-only views for the website, composed from several modules.

Glue only: every rule and number comes from the modules; this file gathers
and shapes data for the API.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from pydantic import Field

from newsimpact.app.wiring import Services
from newsimpact.semantics.logic import FieldScore, score_field
from newsimpact.semantics.models import Claim, Company, EntityMention
from newsimpact.shared.events import Model
from newsimpact.sources.logic import coverage
from newsimpact.sources.models import Article, OutletCoverage
from newsimpact.storylines.models import Storyline
from newsimpact.validation.models import Assessment


class Overview(Model):
    profile: str
    outlets_enabled: int
    articles: int
    articles_24h: int = Field(description="articles published in the last 24 hours")
    storylines_open: int
    storylines_resolved: int
    market_data: str = Field(description="price source, or 'off'")
    llm: str = Field(description="LLM preset and model, or 'off'")
    llm_spent_this_month: float | None
    monitor_every_minutes: float


class EvaluationMiss(Model):
    text: str
    expected: str
    predicted: str


class Evaluation(Model):
    chain: str
    examples: int
    fields: tuple[FieldScore, ...]
    event_type_misses: tuple[EvaluationMiss, ...]


def overview(svc: Services) -> Overview:
    stories = svc.storyline_store.all()
    resolved = sum(s.status.value == "resolved" for s in stories)
    s = svc.settings
    articles = list(svc.articles.recent(10**6))
    day_ago = datetime.now(UTC) - timedelta(days=1)
    llm = "off"
    if svc.llm is not None:
        llm = f"{s.llm_preset} ({svc.llm.name})"
    return Overview(
        profile=s.profile,
        outlets_enabled=sum(x.enabled for x in svc.sources.listed()),
        articles=len(articles),
        articles_24h=sum(a.published_at >= day_ago for a in articles),
        storylines_open=len(stories) - resolved,
        storylines_resolved=resolved,
        market_data=(
            "synthetic demo prices"
            if s.profile == "demo"
            else s.market_data
            if svc.market
            else "off"
        ),
        llm=llm,
        llm_spent_this_month=svc.llm.spent_this_month() if svc.llm else None,
        monitor_every_minutes=s.monitor_every_minutes,
    )


def outlet_coverage(svc: Services) -> list[OutletCoverage]:
    """Per outlet: volume, relevance, part in stories, speed. Free: no analysis or LLM calls."""
    articles = list(svc.articles.recent(10**6))
    with_company = {a.article_id for a in articles if svc.semantics.mentioned_tickers(a)}
    stories = svc.storyline_store.all()
    in_stories = {r.article_id for s in stories for e in s.events for r in e.reports}
    stage_reports = [[(r.source_id, r.published_at) for r in e.reports]
                     for s in stories for e in s.events]  # fmt: skip
    return coverage(articles, with_company, in_stories, stage_reports)


def evaluation(svc: Services) -> Evaluation:
    """Run the configured analysis chain on the labelled set; score every field."""
    path = svc.settings.data_dir / "eval" / "semantics_gold.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    predicted: list[Claim] = []
    for i, row in enumerate(rows):
        claim = Claim(
            claim_id=f"gold-{i}",
            article_id="gold",
            text=row["text"],
            entities=(EntityMention(name=row["company"], entity_type="company"),),
        )
        predicted.append(svc.semantics.analyse(claim))  # fmt: skip
    pairs: dict[str, tuple[list[str], list[str]]] = {
        "event_type": ([r["event_type"] for r in rows], [c.event_type for c in predicted]),
        "attribution_kind": ([r["attribution_kind"] for r in rows],
                             [c.attribution.kind for c in predicted]),
        "is_speculative": ([str(r["is_speculative"]) for r in rows],
                           [str(c.is_speculative) for c in predicted]),
        "is_background": ([str(r["is_background"]) for r in rows],
                          [str(c.signals.get("background", 0) > 0) for c in predicted]),
    }  # fmt: skip
    misses = tuple(
        EvaluationMiss(text=r["text"], expected=r["event_type"], predicted=c.event_type)
        for r, c in zip(rows, predicted, strict=True)
        if r["event_type"] != c.event_type
    )
    return Evaluation(chain=svc.semantics.model_version, examples=len(rows),
                      fields=tuple(score_field(k, g, p) for k, (g, p) in pairs.items()),
                      event_type_misses=misses)  # fmt: skip


# ------------------------------------------------------------ watchlist
# Plain answers are written here once, so the website and any client read the same words.
# Vocabulary: an "event" (e.g. a leadership change) is made of dated "updates".


class NewsItem(Model):
    title: str
    url: str
    source: str
    published_at: datetime


class UpdateItem(Model):
    title: str
    published_at: datetime


class EventCard(Model):
    event_id: str
    event_type: str = Field(description="e.g. Leadership change, Earnings miss")
    ongoing: bool
    updates: tuple[UpdateItem, ...]
    latest_headline: str
    latest_source: str
    stock_move: float | None = Field(description="stock return minus its index, e.g. -0.185")
    stock_move_unusual: bool = Field(description="larger than on 19 of 20 normal trading days")
    stock_move_period: str = Field(description="e.g. '9-13 Nov'")
    stock_move_status: str = Field(
        description="measured | pending (the reaction window has not closed yet) | no_data"
    )
    sources: int = Field(description="independent news sources that reported the event")
    source_names: tuple[str, ...]
    confidence: float = Field(
        description="chance the news is true, 0-1: the weakest update's combined confidence "
        "across its independent sources"
    )
    actions: tuple[str, ...] = Field(description="what to watch or do next, most important first")
    tone: float = Field(description="sentiment of the latest update, -1 (negative) to 1")
    is_rumour: bool = Field(description="the latest update is hedged or rumoured")
    said_by: str = Field(
        description="who the latest update comes from: own_reporting | cites_outlet | "
        "company_statement | filing | anonymous"
    )
    next_update: str | None = Field(description="the update this kind of event usually brings next")


class CompanyCard(Model):
    ticker: str
    name: str
    country: str
    sector: str
    exchange: str
    index_name: str = Field(description="the index the stock is compared with, e.g. S&P 500")
    articles: int = Field(description="stored articles that name the company")
    latest_news: NewsItem | None
    events: tuple[EventCard, ...]


def companies(svc: Services) -> list[CompanyCard]:
    """Every company we follow, with its events (most recent first) and latest news."""
    names = _source_names(svc)
    mentions: dict[str, list[Article]] = defaultdict(list)
    for article in svc.articles.recent(10**6):
        for ticker in svc.semantics.mentioned_tickers(article):
            mentions[ticker].append(article)
    events: dict[str, list[EventCard]] = defaultdict(list)
    for story in svc.storyline_store.all():
        events[story.ticker].append(_event_card(svc, story, names))
    cards = [_company_card(svc, c, mentions.get(c.ticker, []), events.get(c.ticker, []), names)
             for c in svc.companies]  # fmt: skip

    def latest(c: CompanyCard) -> float:
        if c.events:
            return c.events[0].updates[-1].published_at.timestamp()
        return c.latest_news.published_at.timestamp() if c.latest_news else 0.0

    return sorted(cards, key=lambda c: (not c.events, -latest(c), c.name))


def event_summary(svc: Services, event_id: str) -> CompanyCard | None:
    """The company card for one event (the event page)."""
    story = svc.storyline_store.get(event_id)
    if story is None:
        return None
    fallback = Company(ticker=story.ticker, name=story.entity_name, country="", aliases=())
    company = next((c for c in svc.companies if c.ticker == story.ticker), fallback)
    names = _source_names(svc)
    return _company_card(svc, company, [], [_event_card(svc, story, names)], names)


def _source_names(svc: Services) -> dict[str, str]:
    return {s.source_id: s.name.split(" - ")[0] for s in svc.sources.listed()}


def _company_card(
    svc: Services,
    company: Company,
    news: list[Article],
    events: list[EventCard],
    names: dict[str, str],
) -> CompanyCard:
    latest = max(news, key=lambda a: a.published_at, default=None)
    return CompanyCard(
        ticker=company.ticker, name=company.name, country=company.country, sector=company.sector,
        exchange=svc.market_policy.exchange_of(company.ticker),
        index_name=_index_name(svc, company.ticker), articles=len(news),
        latest_news=NewsItem(title=latest.title, url=latest.url,
                             source=names.get(latest.source_id, latest.source_id),
                             published_at=latest.published_at) if latest else None,
        events=tuple(sorted(events, key=lambda e: e.updates[-1].published_at, reverse=True)),
    )  # fmt: skip


def _index_name(svc: Services, ticker: str) -> str:
    if svc.settings.profile == "demo":
        return "market index"
    return svc.market_policy.exchanges[svc.market_policy.exchange_of(ticker)].benchmark_name


def _event_card(svc: Services, story: Storyline, names: dict[str, str]) -> EventCard:
    a: Assessment = svc.validation.latest(story.storyline_id) or svc.validation.assess(story)
    playbook = next((p for p in svc.playbooks.playbooks() if p.theme == story.theme), None)
    titles = {st.name: st.title for st in playbook.stages} if playbook else {}

    def title(name: str) -> str:
        return titles.get(name) or name.replace("_", " ").capitalize()

    latest = max(story.events, key=lambda e: e.published_at)
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
    return EventCard(
        event_id=story.storyline_id,
        event_type=(playbook.title if playbook and playbook.title else story.theme),
        ongoing=story.status.value != "resolved",
        updates=tuple(UpdateItem(title=title(st.stage_name), published_at=st.published_at)
                      for st in a.stages),
        # Titles are joined to the body with ". " for sentence splitting; drop that extra stop.
        latest_headline=latest.summary.replace("?.", "?").replace("!.", "!"),
        latest_source=names.get(latest_sources[0], latest_sources[0]) if latest_sources else "",
        stock_move=move.value if move else None,
        stock_move_unusual=bool(move and move.significant),
        stock_move_period=period,
        stock_move_status="measured" if move else "pending" if any(
            d.channel == "price" and d.verdict == "pending" for st in a.stages for d in st.decisions
        ) else "no_data",
        sources=len(source_ids),
        source_names=tuple(names.get(s, s) for s in source_ids),
        confidence=min((st.claim.confidence for st in a.stages), default=0.0),
        actions=a.suggestions,
        tone=latest.tone,
        is_rumour=latest.is_rumour,
        said_by=latest.reports[0].attribution_kind if latest.reports else "own_reporting",
        next_update=(title(playbook.stages[story.max_stage + 1].name)
                     if playbook and story.status.value != "resolved"
                     and story.max_stage + 1 < len(playbook.stages) else None),
    )  # fmt: skip
