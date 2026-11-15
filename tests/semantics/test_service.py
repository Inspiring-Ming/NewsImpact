from collections.abc import Sequence
from datetime import UTC, datetime

from newsimpact.semantics.adapters.json_file import JsonEntityResolver
from newsimpact.semantics.models import Claim, ClaimsExtracted, Company, EntityMention
from newsimpact.semantics.service import SemanticsService
from newsimpact.shared.bus import InMemoryEventBus
from newsimpact.sources.models import Article, ArticleIngested

NOW = datetime(2026, 3, 10, tzinfo=UTC)


class OneClaim:
    version = "fake-extractor-v1"

    def extract(self, article: Article) -> Sequence[Claim]:
        mention = EntityMention(name="Acme", entity_type="company")
        return [Claim(claim_id="c", article_id=article.article_id, text=article.body,
                      entities=(mention,))]  # fmt: skip


class Tag:
    def __init__(self, name: str) -> None:
        self.version = f"tag-{name}-v1"
        self._name = name

    def apply(self, claim: Claim) -> Claim:
        order = claim.signals.get("order", 0.0)
        return claim.model_copy(update={"signals": {**claim.signals, self._name: order,
                                                    "order": order + 1}})  # fmt: skip


def test_steps_run_in_order_tickers_are_linked_and_versions_recorded() -> None:
    bus = InMemoryEventBus()
    SemanticsService(bus, OneClaim(), [Tag("first"), Tag("second")],
                     JsonEntityResolver([Company(ticker="ACMX", name="Acme", country="US",
                                                 aliases=("Acme",))]))  # fmt: skip
    article = Article(article_id="a", source_id="s", url="u", title="t", body="Acme grew.",
                      published_at=NOW, ingested_at=NOW, content_hash="h")  # fmt: skip
    bus.publish(ArticleIngested(article=article).to_envelope("/test"))

    (claim,) = ClaimsExtracted.model_validate(bus.published[-1].data).claims
    assert claim.signals == {"first": 0.0, "second": 1.0, "order": 2.0}
    assert claim.entities[0].ticker == "ACMX"
    assert claim.model_version == "fake-extractor-v1+tag-first-v1+tag-second-v1"
