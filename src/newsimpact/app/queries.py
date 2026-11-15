"""Read-only views for the website, composed from several modules.

Glue only: every rule and number comes from the modules; this file gathers
and shapes data for the API.
"""

from __future__ import annotations

import json

from pydantic import Field

from newsimpact.app.wiring import Services
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
