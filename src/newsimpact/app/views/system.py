"""System status for the website: overview counts, source coverage, each event type's
steps and record (How it works), reading accuracy."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from pydantic import Field

from newsimpact.app.views.companies import CompanyCard, source_names, type_records
from newsimpact.app.views.guidance import CHANCE, GroupRecord
from newsimpact.semantics.logic import FieldScore, score_field
from newsimpact.semantics.models import Claim, EntityMention
from newsimpact.shared.events import Model
from newsimpact.sources.logic import coverage
from newsimpact.sources.models import Article, OutletCoverage

if TYPE_CHECKING:  # type hints only: the wiring imports the views' stores
    from newsimpact.app.wiring import Services


class Overview(Model):
    profile: str
    outlets_enabled: int
    articles: int
    articles_24h: int = Field(description="articles published in the last 24 hours")
    articles_24h_by_source: dict[str, int] = Field(description="source name -> articles, 24 hours")
    storylines_open: int
    storylines_resolved: int
    market_data: str = Field(description="price source, or 'off'")
    llm: str = Field(description="LLM preset and model, or 'off'")
    llm_spent_this_month: float | None
    monitor_every_minutes: float


class StepCount(Model):
    title: str
    reached: int = Field(description="events of this type that reached this step")


class TypeStats(Model):
    """One event type on the How it works page: how we follow it, how often its steps really
    happened, and how its events moved the stock against the research, case by case."""

    theme: str
    title: str
    events: int
    confirmed: int = Field(description="events confirmed (2+ independent sources or official)")
    window_days: int = Field(description="how long new reports still join an event")
    window_why: str
    steps: tuple[StepCount, ...] = Field(description="possible steps, in order (from research)")
    cases: tuple[GroupRecord, ...] = Field(description="share price expectation per case")
    no_expectation: int = Field(description="events with no expectation (e.g. role unclear)")


def event_types(svc: Services, cards: Sequence[CompanyCard]) -> list[TypeStats]:
    shown = {c.ticker for c in cards}  # the same companies as the events counted below
    storylines = [s for s in svc.storyline_store.all() if s.ticker in shown]
    records = type_records(svc, cards)
    events = [e for c in cards for e in c.events]
    out = []
    for p in svc.playbooks.playbooks():
        title = p.title or p.theme
        mine = [s for s in storylines if s.theme == p.theme]
        reached = Counter(e.stage for s in mine for e in {x.stage: x for x in s.events}.values())
        cases = [r for (t, _), r in records.items() if t == title]
        seen = {r.label for r in cases}
        for x in p.expectations:  # cases research describes but no event has shown yet
            if x.label not in seen:
                cases.append(GroupRecord(label=x.label, expected=x.expected, finding=x.finding,
                                         source=x.source, n=0, average=None, met=0, unusual=0,
                                         chance=CHANCE[x.expected], verdict="too_few"))  # fmt: skip
        order = [x.label for x in p.expectations]
        cases.sort(key=lambda r: (order.index(r.label) if r.label in order else -1, -r.n))
        typed = [e for e in events if e.event_type == title]
        out.append(
            TypeStats(
                theme=p.theme,
                title=title,
                events=len(typed),
                confirmed=sum(e.verified for e in typed),
                window_days=p.link_window_days,
                window_why=p.window_why,
                steps=tuple(
                    StepCount(title=st.title or st.name, reached=reached.get(i, 0))
                    for i, st in enumerate(p.stages)
                ),
                cases=tuple(cases),
                no_expectation=sum(e.expectation is None for e in typed),
            )
        )
    return out


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
    storylines = svc.storyline_store.all()
    resolved = sum(s.status.value == "resolved" for s in storylines)
    s = svc.settings
    day_ago = datetime.now(UTC) - timedelta(days=1)
    last_day = svc.articles.since(day_ago)
    names = source_names(svc)
    llm = "off"
    if svc.llm is not None:
        llm = f"{s.llm_preset} ({svc.llm.name})"
    return Overview(
        profile=s.profile,
        outlets_enabled=sum(x.enabled for x in svc.sources.listed()),
        articles=svc.articles.count(),
        articles_24h=len(last_day),
        articles_24h_by_source=dict(Counter(names.get(a.source_id, a.source_id) for a in last_day)),
        storylines_open=len(storylines) - resolved,
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


def outlet_coverage(
    svc: Services, articles: Sequence[Article], with_company: set[str]
) -> list[OutletCoverage]:
    """Per outlet: volume, relevance, part in storylines, speed. Free: no analysis or LLM calls.
    `with_company`: ids of the articles that name a company we recognise (S&P 500, ASX 200)."""
    storylines = svc.storyline_store.all()
    in_stories = {r.article_id for s in storylines for e in s.events for r in e.reports}
    stage_reports = [[(r.source_id, r.published_at) for r in e.reports]
                     for s in storylines for e in s.events]  # fmt: skip
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
