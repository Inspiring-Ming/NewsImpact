"""Read-only views for the website, composed from several modules.

Glue only: every rule and number comes from the modules; this file gathers
and shapes data for the API.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime

from pydantic import Field

from newsimpact.app.wiring import Services
from newsimpact.market.models import ChannelObservation
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
    llm = "off"
    if svc.llm is not None:
        llm = f"{s.llm_preset} ({svc.llm.name})"
    return Overview(
        profile=s.profile,
        outlets_enabled=sum(x.enabled for x in svc.sources.listed()),
        articles=len(svc.articles.recent(10**6)),
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


class NewsItem(Model):
    title: str
    url: str
    outlet: str
    published_at: datetime


class EventItem(Model):
    title: str
    published_at: datetime


class StoryCard(Model):
    storyline_id: str
    story_type: str = Field(description="e.g. Leadership crisis")
    status: str = Field(description="unfolding | escalating | settled")
    status_text: str = Field(description="e.g. 'Settled - new leader named'")
    events: tuple[EventItem, ...]
    latest_headline: str
    reaction: ChannelObservation | None
    reaction_text: str = Field(
        description="e.g. '18.5% below the S&P 500 - an unusually large move'"
    )
    confirmed: str = Field(description="yes | partly | no")
    confirmed_text: str
    evidence: str = Field(description="strong | partial | weak")
    evidence_text: str


class CompanyCard(Model):
    ticker: str
    name: str
    country: str
    exchange: str
    benchmark_name: str
    articles: int = Field(description="stored articles that name the company")
    latest_news: NewsItem | None
    stories: tuple[StoryCard, ...]


STATUS = {"developing": "unfolding", "escalating": "escalating", "resolved": "settled"}
EVIDENCE = {"high": "strong", "medium": "partial", "low": "weak"}


def companies(svc: Services) -> list[CompanyCard]:
    """Every company we follow: stories first, then companies in the news, then the rest."""
    outlet_names = {s.source_id: s.name.split(" - ")[0] for s in svc.sources.listed()}
    mentions: dict[str, list[Article]] = defaultdict(list)
    for article in svc.articles.recent(10**6):
        for ticker in svc.semantics.mentioned_tickers(article):
            mentions[ticker].append(article)
    stories: dict[str, list[StoryCard]] = defaultdict(list)
    for story in svc.storyline_store.all():
        stories[story.ticker].append(_story_card(svc, story, outlet_names))
    cards = []
    for company in svc.companies:
        news = sorted(mentions.get(company.ticker, []), key=lambda a: a.published_at)
        latest = news[-1] if news else None
        exchange = svc.market_policy.exchange_of(company.ticker)
        cards.append(CompanyCard(
            ticker=company.ticker, name=company.name, country=company.country, exchange=exchange,
            benchmark_name=_benchmark_name(svc, company.ticker), articles=len(news),
            latest_news=NewsItem(title=latest.title, url=latest.url,
                                 outlet=outlet_names.get(latest.source_id, latest.source_id),
                                 published_at=latest.published_at) if latest else None,
            stories=tuple(sorted(stories.get(company.ticker, []),
                                 key=lambda c: c.events[-1].published_at, reverse=True)),
        ))  # fmt: skip
    return sorted(cards, key=lambda c: (
        not c.stories, not c.articles,
        -(c.stories[0].events[-1].published_at.timestamp() if c.stories else
          c.latest_news.published_at.timestamp() if c.latest_news else 0),
        c.name,
    ))  # fmt: skip


def story_summary(svc: Services, storyline_id: str) -> CompanyCard | None:
    """The company card for one story (the story page header)."""
    story = svc.storyline_store.get(storyline_id)
    if story is None:
        return None
    fallback = Company(ticker=story.ticker, name=story.entity_name, country="", aliases=())
    company = next((c for c in svc.companies if c.ticker == story.ticker), fallback)
    outlet_names = {s.source_id: s.name.split(" - ")[0] for s in svc.sources.listed()}
    card = _story_card(svc, story, outlet_names)
    return CompanyCard(
        ticker=company.ticker,
        name=company.name,
        country=company.country,
        exchange=svc.market_policy.exchange_of(company.ticker),
        benchmark_name=_benchmark_name(svc, company.ticker),
        articles=0,
        latest_news=None,
        stories=(card,),
    )


def _benchmark_name(svc: Services, ticker: str) -> str:
    if svc.settings.profile == "demo":
        return "market index"
    return svc.market_policy.exchanges[svc.market_policy.exchange_of(ticker)].benchmark_name


def _story_card(svc: Services, story: Storyline, outlet_names: dict[str, str]) -> StoryCard:
    a: Assessment = svc.validation.latest(story.storyline_id) or svc.validation.assess(story)
    playbook = next((p for p in svc.playbooks.playbooks() if p.theme == story.theme), None)
    titles = {st.name: st.title for st in playbook.stages} if playbook else {}

    def title(name: str) -> str:
        return titles.get(name) or name.replace("_", " ").capitalize()

    events = tuple(EventItem(title=title(st.stage_name), published_at=st.published_at)
                   for st in a.stages)  # fmt: skip
    latest = max(story.events, key=lambda e: e.published_at)
    status = STATUS.get(story.status.value, story.status.value)
    if status == "settled":
        status_text = f"Settled - {events[-1].title.lower()}"
    elif status == "escalating":
        status_text = f"Escalating - {events[-1].title.lower()}"
    else:
        later = playbook.stages[story.max_stage + 1 :] if playbook else ()
        upcoming = later[0].title if later else ""
        status_text = (
            f"Still unfolding - watching for: {upcoming.lower()}" if upcoming else "Still unfolding"
        )

    prices = [d.evidence for st in a.stages for d in st.decisions
              if d.evidence is not None and d.evidence.channel == "price"]  # fmt: skip
    reaction = a.combined_reaction or max(prices, key=lambda o: abs(o.statistic or 0), default=None)
    bench = _benchmark_name(svc, story.ticker)
    if reaction is None:
        reaction_text = ("No price data connected yet" if svc.market is None
                         else "Not measured yet - needs a few trading days")  # fmt: skip
    else:
        side = "below" if reaction.value < 0 else "above"
        size = "an unusually large move" if reaction.significant else "within normal daily swings"
        reaction_text = f"{abs(reaction.value):.1%} {side} the {bench} - {size}"

    outlets = {o for st in a.stages for o in st.claim.outlets}
    backed = sum(st.claim.status != "single_source" for st in a.stages)
    if backed == len(a.stages):
        confirmed, confirmed_text = "yes", f"Yes - reported by {len(outlets)} outlets"
    elif backed:
        confirmed = "partly"
        confirmed_text = (
            f"Partly - {backed} of {len(a.stages)} events reported by more than one outlet"
        )
    else:
        names = ", ".join(sorted(outlet_names.get(o, o) for o in outlets))
        confirmed, confirmed_text = "no", f"Not yet - only {names} so far"

    evidence = EVIDENCE.get(a.confidence, a.confidence)
    market_clear = reaction is not None and reaction.significant
    evidence_text = {
        "strong": "Confirmed by several outlets, and the stock clearly reacted",
        "partial": (
            "Confirmed news, but no clear stock reaction yet"
            if confirmed == "yes"
            else "The stock reacted, but the news is not fully confirmed yet"
            if market_clear
            else "Partly confirmed news; stock reaction still unclear"
        ),
        "weak": "Not yet confirmed, and no clear stock reaction",
    }.get(evidence, "")
    return StoryCard(
        storyline_id=story.storyline_id,
        story_type=(playbook.title if playbook and playbook.title else story.theme),
        status=status,
        status_text=status_text,
        events=events,
        latest_headline=latest.summary,
        reaction=reaction,
        reaction_text=reaction_text,
        confirmed=confirmed,
        confirmed_text=confirmed_text,
        evidence=evidence,
        evidence_text=evidence_text,
    )
