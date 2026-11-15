"""Run the analysis chain on each new article, link entities to tickers, publish claims."""

from __future__ import annotations

from collections.abc import Sequence

from newsimpact.semantics.models import Claim, ClaimsExtracted
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
    ) -> None:
        self._bus = bus
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

    def mentioned_tickers(self, article: Article) -> set[str]:
        """Companies the article names. Free: name matching only, no analysis or LLM calls."""
        found = {e.ticker or self._resolver.resolve(e.name)
                 for c in self._extractor.extract(article) for e in c.entities}  # fmt: skip
        return {t for t in found if t}

    def claims_for(self, article: Article) -> tuple[Claim, ...]:
        """Analyse one article without publishing (also used by reports and evaluation)."""
        claims = tuple(self.analyse(c) for c in self._extractor.extract(article))
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
