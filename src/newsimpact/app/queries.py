"""Read-only views for the website, composed from several modules.

Glue only: every rule and number comes from the modules; this file gathers
and shapes data for the API.
"""

from __future__ import annotations

import json

from pydantic import Field

from newsimpact.app.wiring import Services
from newsimpact.market.models import ChannelObservation
from newsimpact.semantics.logic import FieldScore, score_field
from newsimpact.semantics.models import OTHER, Claim, EntityMention
from newsimpact.shared.events import Model
from newsimpact.sources.logic import coverage
from newsimpact.sources.models import OutletCoverage


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


class BriefingItem(Model):
    """One storyline, summarised for a card: what happened, how sure, what the market did."""

    storyline_id: str
    ticker: str
    company: str
    market: str = Field(description="home exchange, e.g. US or ASX")
    theme: str
    status: str
    confidence: str
    stages: int
    stages_confirmed: int = Field(description="stages backed by independent origins or the company")
    latest_stage: str
    latest_at: str
    latest_summary: str
    reaction: ChannelObservation | None = Field(
        description="the headline market move: combined reaction, else the strongest price move"
    )
    expectations_measured: int
    expectations_met: int


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


def briefing(svc: Services) -> list[BriefingItem]:
    """Every storyline as a card, most recently updated first.

    Uses the latest stored assessment (kept current by monitoring), so the page
    never triggers market-data calls; assesses on the spot only if none is stored.
    """
    items = []
    for story in sorted(svc.storyline_store.all(), key=lambda s: s.updated_at, reverse=True):
        a = svc.validation.latest(story.storyline_id) or svc.validation.assess(story)
        latest = max(story.events, key=lambda e: e.published_at)
        prices = [d.evidence for st in a.stages for d in st.decisions
                  if d.evidence is not None and d.evidence.channel == "price"]  # fmt: skip
        strongest = max(prices, key=lambda o: abs(o.statistic or 0), default=None)
        measured = [d for st in a.stages for d in st.decisions
                    if d.verdict in ("consistent", "inconsistent", "not_significant")]  # fmt: skip
        items.append(BriefingItem(
            storyline_id=story.storyline_id, ticker=story.ticker, company=story.entity_name,
            market=svc.market_policy.exchange_of(story.ticker), theme=story.theme,
            status=story.status.value, confidence=a.confidence, stages=len(a.stages),
            stages_confirmed=sum(st.claim.status != "single_source" for st in a.stages),
            latest_stage=latest.stage_name, latest_at=latest.published_at.isoformat(),
            latest_summary=latest.summary, reaction=a.combined_reaction or strongest,
            expectations_measured=len(measured),
            expectations_met=sum(d.verdict == "consistent" for d in measured),
        ))  # fmt: skip
    return items


def outlet_coverage(svc: Services) -> list[OutletCoverage]:
    articles = list(svc.articles.recent(10**6))
    with_company: set[str] = set()
    with_trigger: set[str] = set()
    for article in articles:
        claims = svc.semantics.claims_for(article)
        if any(e.ticker for c in claims for e in c.entities):
            with_company.add(article.article_id)
        if any(c.event_type != OTHER for c in claims):
            with_trigger.add(article.article_id)
    stage_reports = [[(r.source_id, r.published_at) for r in e.reports]
                     for s in svc.storyline_store.all() for e in s.events]  # fmt: skip
    return coverage(articles, with_company, with_trigger, stage_reports)


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
