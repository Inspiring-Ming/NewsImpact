"""Run the analysis chain on each new article, link entities to tickers, publish claims."""

from __future__ import annotations

from collections.abc import Sequence

from newsimpact.semantics.models import OTHER, Claim, ClaimsExtracted
from newsimpact.semantics.ports import ClaimExtractor, ClaimStep, EntityResolver
from newsimpact.shared.bus import EventBus
from newsimpact.shared.events import EventEnvelope
from newsimpact.sources.models import Article, ArticleIngested

EVENT_SOURCE = "/semantics"


class SemanticsService:
    def __init__(
        self,
        bus: EventBus,
        extractor: ClaimExtractor,
        steps: Sequence[ClaimStep],
        resolver: EntityResolver,
        *,
        copy_novelty: float = 0.2,
        commentary_cues: Sequence[str] = (),
    ) -> None:
        self._bus = bus
        self._commentary = tuple(c.lower() for c in commentary_cues)
        self._copy_novelty = copy_novelty
        self._extractor = extractor
        self._steps = tuple(steps)
        self._resolver = resolver
        bus.subscribe(ArticleIngested.EVENT_TYPE, self.on_article_ingested)

    @property
    def model_version(self) -> str:
        """Every step, in order - enough to reproduce a claim's analysis."""
        return "+".join([self._extractor.version, *(s.version for s in self._steps)])

    def analyse(self, claim: Claim) -> Claim:
        for step in self._steps:
            claim = step.apply(claim)
        return self._link(claim).model_copy(update={"model_version": self.model_version})

    def is_commentary(self, article: Article) -> bool:
        """Headline or opening sentence reads as opinion, explainer, interview or feature
        (taxonomy.json "commentary"). The body starts with the headline, so its first
        300 characters cover both."""
        lead = f" {article.body[:300].lower()} "
        return any(cue in lead for cue in self._commentary)

    def mentioned_tickers(self, article: Article) -> set[str]:
        """Companies the article names. Free: name matching only, no analysis or LLM calls."""
        found = {e.ticker or self._resolver.resolve(e.name)
                 for c in self._extractor.extract(article) for e in c.entities}  # fmt: skip
        return {t for t in found if t}

    def claims_for(self, article: Article) -> tuple[Claim, ...]:
        """Analyse one article without publishing (also used by reports and evaluation)."""
        claims = tuple(self.analyse(c) for c in self._extractor.extract(article))
        if self.is_commentary(article):
            # Opinion or feature piece: talk about the news, not a new event.
            claims = tuple(c.model_copy(update={"event_type": OTHER,
                                                "signals": {**c.signals, "commentary": 1.0}})
                           for c in claims)  # fmt: skip
        if article.copy_of_source is None:
            return claims
        # A copy of another outlet's article: same origin, and stale news (Tetlock 2011).
        return tuple(
            c.model_copy(update={
                "attribution": c.attribution.model_copy(
                    update={"copy_of_source": article.copy_of_source}),
                "novelty": min(c.novelty, self._copy_novelty),
            })
            for c in claims
        )  # fmt: skip

    def on_article_ingested(self, envelope: EventEnvelope) -> None:
        article = ArticleIngested.model_validate(envelope.data).article
        claims = self.claims_for(article)
        if not claims:
            return
        self._bus.publish(
            ClaimsExtracted(
                article_id=article.article_id,
                source_id=article.source_id,
                published_at=article.published_at,
                claims=claims,
            ).follow(EVENT_SOURCE, envelope)
        )

    def _link(self, claim: Claim) -> Claim:
        entities = tuple(
            e if e.ticker else e.model_copy(update={"ticker": self._resolver.resolve(e.name)})
            for e in claim.entities
        )
        return claim.model_copy(update={"entities": entities})
