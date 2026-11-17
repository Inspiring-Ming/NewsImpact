"""Wiring: builds every service from the settings, the reference data and the plug-ins.

  plugins.py   which technology implements each port, one table per kind of
               technology; adding one = an adapter + one table entry
  (this file)  assembles the services in the order news flows

Business code never changes when a technology does. Method settings (windows,
thresholds) come from data/reference/methodology.json, each with its reason.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import httpx

from newsimpact.alerts.adapters.shared import SharedChannels
from newsimpact.alerts.service import AlertsService
from newsimpact.app.config import Settings
from newsimpact.app.views.briefs import BriefStore
from newsimpact.app.views.news_data import SnapshotNewsData
from newsimpact.app.views.snapshot import SnapshotStore
from newsimpact.app.wiring.plugins import (
    AUTH,
    EVENT_BUSES,
    FEEDS,
    LLM_PROVIDERS,
    MARKET_DATA,
    NOTIFIERS,
    SEMANTIC_STEPS,
    STORES,
    Context,
    Stores,
    pick,
)
from newsimpact.assistant.models import AssistantPolicy
from newsimpact.assistant.service import AssistantService
from newsimpact.identity.ports import Authenticator
from newsimpact.llm.adapters.json_file import load_models
from newsimpact.llm.adapters.memory import InMemoryResponseCache, InMemorySpendLedger
from newsimpact.llm.adapters.sqlite import SqliteResponseCache, SqliteSpendLedger
from newsimpact.llm.models import LlmPolicy, LlmPreset
from newsimpact.llm.service import LlmGateway
from newsimpact.market.adapters.cached import CachedMarketData
from newsimpact.market.adapters.synthetic import SyntheticMarketData
from newsimpact.market.models import MeasurementPolicy
from newsimpact.market.service import MarketService
from newsimpact.reliability.logic import MODEL_VERSION as RELIABILITY_VERSION
from newsimpact.reliability.logic import claim_reliability
from newsimpact.reliability.service import ReliabilityService
from newsimpact.semantics.adapters.json_file import JsonEntityResolver, load_taxonomy
from newsimpact.semantics.adapters.lexicon import SentenceExtractor
from newsimpact.semantics.adapters.llm_classifier import LlmClassifierStep
from newsimpact.semantics.models import Company, Taxonomy
from newsimpact.semantics.ports import ClaimStep
from newsimpact.semantics.service import SemanticsService
from newsimpact.shared.bus import EventBus
from newsimpact.sources.adapters.fixture import FixtureSearch
from newsimpact.sources.adapters.gdelt import GdeltSearch
from newsimpact.sources.adapters.json_file import JsonSourceRegistry
from newsimpact.sources.models import DuplicatePolicy, FeedConfig, Source
from newsimpact.sources.ports import ArticleStore, Feed, NewsSearch, SourceRegistry
from newsimpact.sources.service import SourcesService
from newsimpact.storylines.adapters.json_file import JsonPlaybookCatalog
from newsimpact.storylines.ports import PlaybookCatalog, StorylineStore
from newsimpact.storylines.service import MODEL_VERSION as STORYLINES_VERSION
from newsimpact.storylines.service import StorylinesService
from newsimpact.validation.logic import MODEL_VERSION as VALIDATION_VERSION
from newsimpact.validation.models import Provenance, ValidationPolicy
from newsimpact.validation.service import ValidationService

FEED_KINDS = tuple(FEEDS)  # the feed kinds sources.json may use
REFERENCE_FILES = ("taxonomy.json", "playbooks.json", "methodology.json", "llm_models.json")


@dataclass(frozen=True)
class Services:
    settings: Settings
    bus: EventBus
    sources: SourcesService
    semantics: SemanticsService
    reliability: ReliabilityService
    storylines: StorylinesService
    market: MarketService | None  # None until a price source is configured (live profile)
    validation: ValidationService
    llm: LlmGateway | None
    llm_presets: dict[str, LlmPreset]
    playbooks: PlaybookCatalog
    companies: tuple[Company, ...]  # the companies we follow (display names, countries)
    market_policy: MeasurementPolicy  # exchanges, windows (for labelling and charts)
    # read models served by the API and the views
    articles: ArticleStore
    storyline_store: StorylineStore
    alerts: AlertsService
    auth: Authenticator  # who is signed in (identity module)
    briefs: BriefStore  # three-line event briefs (app/views/briefs.py)
    snapshots: SnapshotStore  # what pages read, computed once per round (app/views/snapshot.py)
    assistant: AssistantService | None = None  # answers questions from our data (set below)


def http_client(s: Settings) -> httpx.Client:
    return httpx.Client(timeout=30, headers={"User-Agent": s.http_user_agent})


# ------------------------------------------------------------ choices
def _llm(s: Settings, stores: Stores) -> LlmGateway | None:
    if s.llm_preset == "off":
        return None
    presets, prices = load_models(s.reference_dir / "llm_models.json")
    preset = pick(presets, s.llm_preset, "LLM preset")
    provider = pick(LLM_PROVIDERS, preset.provider, "LLM provider")(s, preset)
    cache, ledger = (
        (SqliteResponseCache(stores.db), SqliteSpendLedger(stores.db))
        if stores.db
        else (InMemoryResponseCache(), InMemorySpendLedger())
    )
    policy = LlmPolicy(monthly_budget_usd=s.llm_monthly_budget_usd,
                       max_calls_per_round=s.llm_max_calls_per_round)  # fmt: skip
    return LlmGateway(provider, prices, cache, ledger, policy)


def _semantic_steps(s: Settings, taxonomy: Taxonomy, llm: LlmGateway | None) -> list[ClaimStep]:
    steps = [pick(SEMANTIC_STEPS, name, "semantic step")(taxonomy) for name in s.semantic_steps]
    if llm is not None:  # last, so it can refine what the free steps found
        steps.append(LlmClassifierStep(llm, taxonomy, scope=s.llm_scope))
    return steps


def _market(ctx: Context, policy: MeasurementPolicy, stores: Stores) -> MarketService | None:
    s = ctx.settings
    if s.profile == "demo":  # fictional prices, so the demo never needs a vendor
        demo = SyntheticMarketData.from_file(s.demo_dir / "prices.json", "MKT")
        return MarketService(demo, policy, benchmark_override="MKT")
    data = pick(MARKET_DATA, s.market_data, "market data source")(ctx, policy)
    if data is None:
        return None
    if stores.db is not None:  # daily bars change once a day: never fetch twice
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
            pick(FEEDS, feed.kind, f"feed kind (source {listing.source_id!r})")
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
    bus = pick(EVENT_BUSES, s.event_bus, "event bus")(s)
    stores = pick(STORES, s.store, "store")(s)
    method = _methodology(s)

    registry = JsonSourceRegistry.from_file(s.profile_dir / "sources.json")
    taxonomy = load_taxonomy(s.reference_dir / "taxonomy.json")
    catalog = JsonPlaybookCatalog.from_file(s.reference_dir / "playbooks.json")
    _check_reference_data(registry, taxonomy, catalog)
    duplicates = DuplicatePolicy.model_validate(method["sources"])
    resolver = JsonEntityResolver.from_file(s.profile_dir / "entities.json")
    ctx = Context(settings=s, http=http_client(s) if s.profile == "live" else None,
                  tickers=tuple(c.ticker for c in resolver.companies()))  # fmt: skip

    def feed(source: Source, config: FeedConfig) -> Feed:
        return FEEDS[config.kind](ctx, source, config)

    search: NewsSearch = (
        GdeltSearch(ctx.http) if ctx.http else FixtureSearch(s.demo_dir / "articles.json")
    )
    sources = SourcesService(bus, registry, feed, search, stores.articles,
                             stores.seen_sources, stores.watches,
                             accept_unlisted=s.accept_unlisted_sources,
                             duplicates=duplicates)  # fmt: skip

    llm = _llm(s, stores)
    extractor = SentenceExtractor(resolver.known_names(), resolver.exact_case_names())
    semantics = SemanticsService(bus, extractor,
                                 _semantic_steps(s, taxonomy, llm), resolver,
                                 copy_novelty=duplicates.copy_novelty,
                                 commentary_cues=taxonomy.words("commentary"),
                                 deal_cues={k: taxonomy.words(k) for k in taxonomy.word_lists
                                            if k.startswith("deal_")})  # fmt: skip
    reliability = ReliabilityService(bus, stores.tracked_sources, stores.evidence)
    storylines = StorylinesService(bus, stores.storylines, catalog)

    market_policy = MeasurementPolicy.model_validate(method["market"])
    market = _market(ctx, market_policy, stores)
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

    def current_reliability(source_id: str, is_rumour: bool) -> float:
        score = reliability.score_source(source_id).score
        return claim_reliability(score, is_speculative=is_rumour)

    validation = ValidationService(catalog, market, stores.assessments,
                                   ValidationPolicy.model_validate(method["validation"]),
                                   provenance, current_reliability)  # fmt: skip
    notifiers = [n for n in (make(ctx) for make in NOTIFIERS) if n is not None]

    services = Services(
        settings=s,
        bus=bus,
        sources=sources,
        semantics=semantics,
        reliability=reliability,
        storylines=storylines,
        market=market,
        validation=validation,
        llm=llm,
        llm_presets=load_models(s.reference_dir / "llm_models.json")[0],
        playbooks=catalog,
        companies=tuple(resolver.companies()),
        market_policy=market_policy,
        articles=stores.articles,
        storyline_store=stores.storylines,
        alerts=AlertsService(stores.alerts, SharedChannels(notifiers), s.site_url),
        auth=pick(AUTH, s.auth, "sign-in provider")(s),
        briefs=stores.briefs,
        snapshots=stores.snapshots,
    )
    services.sources.register_listed()  # every listed source is tracked from the start
    # The assistant reads through the finished services (latest snapshot, article store).
    tool_model = llm if llm is not None and llm.can_use_tools else None
    assistant = AssistantService(tool_model, SnapshotNewsData(services), stores.questions,
                                 AssistantPolicy.model_validate(method["assistant"]))  # fmt: skip
    return replace(services, assistant=assistant)
