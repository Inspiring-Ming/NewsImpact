"""Wiring: the ONE place that picks which technology implements each port.

Every choice is a small, named function below, driven by Settings:
  _stores           memory | sqlite                 (NI_STORE)
  _feed_factory     feed kind -> adapter             (sources.json "kind")
  _llm              off | quality | economy | local  (NI_LLM_PRESET, llm_models.json)
  _semantic_steps   analysis chain                   (NI_SEMANTIC_STEPS, + llm if on)
  _market           synthetic | eodhd | csv | none   (profile, NI_MARKET_DATA)
Method settings (windows, thresholds) are loaded from methodology.json.
To swap a technology: add an adapter in the owning module and select it in
the matching function. Business code never changes.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from newsimpact.app.config import Settings
from newsimpact.impact.adapters.json_file import JsonRelationshipGraph
from newsimpact.impact.adapters.memory import InMemoryImpactStore
from newsimpact.impact.adapters.sqlite import SqliteImpactStore
from newsimpact.impact.ports import ImpactStore
from newsimpact.impact.service import ImpactService
from newsimpact.llm.adapters.json_file import load_models
from newsimpact.llm.adapters.memory import InMemoryResponseCache, InMemorySpendLedger
from newsimpact.llm.adapters.ollama import OllamaProvider
from newsimpact.llm.adapters.sqlite import SqliteResponseCache, SqliteSpendLedger
from newsimpact.llm.models import LlmPolicy, LlmPreset
from newsimpact.llm.ports import LlmProvider
from newsimpact.llm.service import LlmGateway
from newsimpact.market.adapters.cached import CachedMarketData
from newsimpact.market.adapters.csv_file import CsvMarketData
from newsimpact.market.adapters.eodhd import EodhdMarketData
from newsimpact.market.adapters.synthetic import SyntheticMarketData
from newsimpact.market.models import MeasurementPolicy
from newsimpact.market.ports import MarketData
from newsimpact.market.service import MarketService
from newsimpact.reliability.adapters.memory import InMemoryEvidenceStore, InMemoryTrackedSources
from newsimpact.reliability.adapters.sqlite import SqliteEvidenceStore, SqliteTrackedSources
from newsimpact.reliability.logic import MODEL_VERSION as RELIABILITY_VERSION
from newsimpact.reliability.logic import claim_reliability
from newsimpact.reliability.ports import EvidenceStore, TrackedSources
from newsimpact.reliability.service import ReliabilityService
from newsimpact.semantics.adapters.json_file import JsonEntityResolver, load_taxonomy
from newsimpact.semantics.adapters.lexicon import (
    AttributionStep,
    LexiconSentiment,
    SentenceExtractor,
    TaxonomyClassifier,
    WordListSignal,
)
from newsimpact.semantics.adapters.llm_classifier import LlmClassifierStep
from newsimpact.semantics.models import Company, Taxonomy
from newsimpact.semantics.ports import ClaimStep
from newsimpact.semantics.service import SemanticsService
from newsimpact.shared.bus import InMemoryEventBus
from newsimpact.shared.sqlite import Database
from newsimpact.sources.adapters.fixture import FixtureFeed, FixtureSearch
from newsimpact.sources.adapters.gdelt import GdeltSearch
from newsimpact.sources.adapters.json_file import JsonSourceRegistry
from newsimpact.sources.adapters.memory import (
    InMemoryArticleStore,
    InMemorySeenSources,
    InMemoryWatchStore,
)
from newsimpact.sources.adapters.rss import PerCompanyRssFeed, RssFeed
from newsimpact.sources.adapters.sqlite import (
    SqliteArticleStore,
    SqliteSeenSources,
    SqliteWatchStore,
)
from newsimpact.sources.models import DuplicatePolicy, FeedConfig, Source
from newsimpact.sources.ports import (
    ArticleStore,
    Feed,
    FeedFactory,
    NewsSearch,
    SeenSources,
    SourceRegistry,
    WatchStore,
)
from newsimpact.sources.service import SourcesService
from newsimpact.storylines.adapters.json_file import JsonPlaybookCatalog
from newsimpact.storylines.adapters.memory import InMemoryStorylineStore
from newsimpact.storylines.adapters.sqlite import SqliteStorylineStore
from newsimpact.storylines.ports import PlaybookCatalog, StorylineStore
from newsimpact.storylines.service import MODEL_VERSION as STORYLINES_VERSION
from newsimpact.storylines.service import StorylinesService
from newsimpact.validation.adapters.memory import InMemoryAssessmentStore
from newsimpact.validation.adapters.sqlite import SqliteAssessmentStore
from newsimpact.validation.logic import MODEL_VERSION as VALIDATION_VERSION
from newsimpact.validation.models import Provenance, ValidationPolicy
from newsimpact.validation.ports import AssessmentStore
from newsimpact.validation.service import ValidationService

FEED_KINDS = ("rss", "rss_per_company", "fixture")
SEMANTIC_STEPS: dict[str, Callable[[Taxonomy], ClaimStep]] = {
    "taxonomy": TaxonomyClassifier,
    "attribution": AttributionStep,
    "sentiment": LexiconSentiment,
    "uncertainty": lambda t: WordListSignal(t, "uncertainty"),
    # "llm" is added in _semantic_steps because it needs the gateway
}
REFERENCE_FILES = ("taxonomy.json", "playbooks.json", "methodology.json", "llm_models.json")


@dataclass(frozen=True)
class Services:
    settings: Settings
    bus: InMemoryEventBus
    sources: SourcesService
    semantics: SemanticsService
    reliability: ReliabilityService
    storylines: StorylinesService
    impact: ImpactService
    market: MarketService | None  # None until a price source is configured (live profile)
    validation: ValidationService
    llm: LlmGateway | None
    llm_presets: dict[str, LlmPreset]
    playbooks: PlaybookCatalog
    companies: tuple[Company, ...]  # the companies we follow (display names, countries)
    market_policy: MeasurementPolicy  # exchanges, windows (for labelling and charts)
    # read models served by the API and reports
    articles: ArticleStore
    impacts: ImpactStore
    storyline_store: StorylineStore


@dataclass(frozen=True)
class Stores:
    db: Database | None
    articles: ArticleStore
    seen_sources: SeenSources
    watches: WatchStore
    tracked_sources: TrackedSources
    evidence: EvidenceStore
    storylines: StorylineStore
    impacts: ImpactStore
    assessments: AssessmentStore


# ------------------------------------------------------------ choices
def _stores(s: Settings) -> Stores:
    if s.store == "sqlite":
        db = Database(s.db_path)
        return Stores(db, SqliteArticleStore(db), SqliteSeenSources(db), SqliteWatchStore(db),
                      SqliteTrackedSources(db), SqliteEvidenceStore(db),
                      SqliteStorylineStore(db), SqliteImpactStore(db),
                      SqliteAssessmentStore(db))  # fmt: skip
    return Stores(None, InMemoryArticleStore(), InMemorySeenSources(), InMemoryWatchStore(),
                  InMemoryTrackedSources(), InMemoryEvidenceStore(),
                  InMemoryStorylineStore(), InMemoryImpactStore(),
                  InMemoryAssessmentStore())  # fmt: skip


def http_client(s: Settings) -> httpx.Client:
    return httpx.Client(timeout=30, headers={"User-Agent": s.http_user_agent})


def _feed_factory(s: Settings, client: httpx.Client | None, tickers: Sequence[str]) -> FeedFactory:
    def build(source: Source, config: FeedConfig) -> Feed:
        if config.kind == "rss" and client is not None:
            return RssFeed(source, config.url, client)
        if config.kind == "rss_per_company" and client is not None:
            return PerCompanyRssFeed(source, config.url, tickers, client)
        if config.kind == "fixture":
            return FixtureFeed(source, s.demo_dir / "articles.json")
        raise ValueError(f"feed kind {config.kind!r} is not available in profile {s.profile!r}")

    return build


def _llm(s: Settings, stores: Stores) -> LlmGateway | None:
    if s.llm_preset == "off":
        return None
    presets, prices = load_models(s.reference_dir / "llm_models.json")
    preset = presets[s.llm_preset]
    provider: LlmProvider
    if preset.provider == "ollama":
        provider = OllamaProvider(preset.model, httpx.Client(timeout=120), s.llm_base_url)
    elif preset.provider == "anthropic":  # imported only when chosen: optional dependency
        from newsimpact.llm.adapters.anthropic_api import AnthropicProvider

        key = s.anthropic_api_key.get_secret_value() if s.anthropic_api_key else None
        provider = AnthropicProvider(preset.model, effort=preset.effort, api_key=key)
    else:
        raise ValueError(f"unknown LLM provider {preset.provider!r} in llm_models.json")
    cache, ledger = (
        (SqliteResponseCache(stores.db), SqliteSpendLedger(stores.db))
        if stores.db
        else (InMemoryResponseCache(), InMemorySpendLedger())
    )
    policy = LlmPolicy(monthly_budget_usd=s.llm_monthly_budget_usd,
                       max_calls_per_round=s.llm_max_calls_per_round)  # fmt: skip
    return LlmGateway(provider, prices, cache, ledger, policy)


def _semantic_steps(s: Settings, taxonomy: Taxonomy, llm: LlmGateway | None) -> list[ClaimStep]:
    steps: list[ClaimStep] = []
    for name in s.semantic_steps:
        if name not in SEMANTIC_STEPS:
            raise ValueError(f"unknown semantic step {name!r}; known: {list(SEMANTIC_STEPS)}")
        steps.append(SEMANTIC_STEPS[name](taxonomy))
    if llm is not None:  # last, so it can refine what the free steps found
        steps.append(LlmClassifierStep(llm, taxonomy, scope=s.llm_scope))
    return steps


def _market(s: Settings, policy: MeasurementPolicy, stores: Stores) -> MarketService | None:
    data: MarketData
    if s.profile == "demo":
        data = SyntheticMarketData.from_file(s.demo_dir / "prices.json", "MKT")
        return MarketService(data, policy, benchmark_override="MKT")
    if s.market_data == "eodhd":
        if s.eodhd_api_key is None:
            raise ValueError("NI_MARKET_DATA=eodhd needs NI_EODHD_API_KEY")
        data = EodhdMarketData(httpx.Client(timeout=30), s.eodhd_api_key.get_secret_value(),
                               policy.vendor_symbol)  # fmt: skip
    elif s.market_data == "csv":
        data = CsvMarketData(s.market_csv_dir)
    else:
        return None
    if stores.db is not None:
        data = CachedMarketData(data, stores.db)
    return MarketService(data, policy)


# ------------------------------------------------- reference data
def _methodology(s: Settings) -> dict[str, Any]:
    raw: dict[str, Any] = json.loads((s.reference_dir / "methodology.json").read_text())
    return {k: {f: v for f, v in sec.items() if f != "rationale"}
            for k, sec in raw.items() if isinstance(sec, dict)}  # fmt: skip


def _check_reference_data(
    registry: SourceRegistry, taxonomy: Taxonomy, catalog: PlaybookCatalog
) -> None:
    """Fail at start-up, not at 3 a.m., if the reference files disagree."""
    for listing in registry.listings():
        for feed in listing.feeds:
            if feed.kind not in FEED_KINDS:
                raise ValueError(f"{listing.source_id}: unknown feed kind {feed.kind!r}")
    known = taxonomy.event_type_names()
    for playbook in catalog.playbooks():
        missing = playbook.event_types() - known
        if missing:
            raise ValueError(f"playbook {playbook.theme!r} uses event types not in "
                             f"taxonomy.json: {sorted(missing)}")  # fmt: skip


def _fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


# ------------------------------------------------------------ build
def build_services(settings: Settings | None = None) -> Services:
    s = settings or Settings()
    client = http_client(s) if s.profile == "live" else None
    bus = InMemoryEventBus()
    stores = _stores(s)
    method = _methodology(s)

    registry = JsonSourceRegistry.from_file(s.profile_dir / "sources.json")
    taxonomy = load_taxonomy(s.reference_dir / "taxonomy.json")
    catalog = JsonPlaybookCatalog.from_file(s.reference_dir / "playbooks.json")
    _check_reference_data(registry, taxonomy, catalog)
    duplicates = DuplicatePolicy.model_validate(method["sources"])

    search: NewsSearch = (
        GdeltSearch(client) if client else FixtureSearch(s.demo_dir / "articles.json")
    )
    resolver = JsonEntityResolver.from_file(s.profile_dir / "entities.json")
    tickers = [c.ticker for c in resolver.companies()]
    sources = SourcesService(bus, registry, _feed_factory(s, client, tickers), search,
                             stores.articles,
                             stores.seen_sources, stores.watches,
                             accept_unlisted=s.accept_unlisted_sources,
                             duplicates=duplicates)  # fmt: skip

    llm = _llm(s, stores)
    semantics = SemanticsService(bus, SentenceExtractor(resolver.known_names()),
                                 _semantic_steps(s, taxonomy, llm), resolver,
                                 copy_novelty=duplicates.copy_novelty,
                                 commentary_cues=taxonomy.words("commentary"))  # fmt: skip
    graph = (
        JsonRelationshipGraph({})  # Phase 1: real supplier/customer data
        if s.profile == "live"
        else JsonRelationshipGraph.from_file(s.demo_dir / "relationships.json")
    )
    market_policy = MeasurementPolicy.model_validate(method["market"])
    market = _market(s, market_policy, stores)
    reference = [s.profile_dir / "sources.json", s.profile_dir / "entities.json"]
    reference += [s.reference_dir / f for f in REFERENCE_FILES]
    provenance = Provenance(
        components={
            "semantics": semantics.model_version,
            "reliability": RELIABILITY_VERSION,
            "storylines": STORYLINES_VERSION,
            "market": market.version if market else "none",
            "validation": VALIDATION_VERSION,
            "llm": llm.name if llm else "none",
        },
        reference_data={f"{p.parent.name}/{p.name}": _fingerprint(p) for p in reference},
    )

    reliability = ReliabilityService(bus, stores.tracked_sources, stores.evidence)

    def current_reliability(source_id: str, is_rumour: bool) -> float:
        score = reliability.score_source(source_id).score
        return claim_reliability(score, is_speculative=is_rumour)

    validation = ValidationService(catalog, market, stores.assessments,
                                   ValidationPolicy.model_validate(method["validation"]),
                                   provenance, current_reliability)  # fmt: skip

    services = Services(
        settings=s,
        bus=bus,
        sources=sources,
        semantics=semantics,
        reliability=reliability,
        storylines=StorylinesService(bus, stores.storylines, catalog),
        impact=ImpactService(bus, graph, stores.impacts),
        market=market,
        validation=validation,
        llm=llm,
        llm_presets=load_models(s.reference_dir / "llm_models.json")[0],
        playbooks=catalog,
        companies=tuple(resolver.companies()),
        market_policy=market_policy,
        articles=stores.articles,
        impacts=stores.impacts,
        storyline_store=stores.storylines,
    )
    services.sources.register_listed()  # every listed outlet is tracked from the start
    return services
