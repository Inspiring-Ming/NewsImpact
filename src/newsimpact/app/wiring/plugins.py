"""Plug-in tables: which technology implements each port, by name.

To add a technology: write its adapter in the owning module, then add ONE
entry to the matching table here. Settings and reference data pick entries by
name; an unknown name fails at start-up with the list of known ones.

  STORES          NI_STORE            memory | sqlite
  EVENT_BUSES     NI_EVENT_BUS        memory              (cloud: SNS/SQS, EventBridge)
  FEEDS           sources.json kind   rss | rss_per_company | fixture
  MARKET_DATA     NI_MARKET_DATA      none | eodhd | csv
  LLM_PROVIDERS   llm_models.json     anthropic | ollama
  SEMANTIC_STEPS  NI_SEMANTIC_STEPS   taxonomy | attribution | sentiment | uncertainty
  AUTH            NI_AUTH             local               (next: cognito)
  NOTIFIERS       all configured ones are used: discord (NI_DISCORD_WEBHOOK_URL)
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import httpx

from newsimpact.alerts.adapters.discord import DiscordNotifier
from newsimpact.alerts.adapters.memory import InMemoryAlertState
from newsimpact.alerts.adapters.sqlite import SqliteAlertState
from newsimpact.alerts.ports import AlertState, Notifier
from newsimpact.app.config import Settings
from newsimpact.app.views.briefs import BriefStore, InMemoryBriefs, SqliteBriefs
from newsimpact.identity.adapters.local import LocalSingleUser
from newsimpact.identity.ports import Authenticator
from newsimpact.llm.adapters.ollama import OllamaProvider
from newsimpact.llm.models import LlmPreset
from newsimpact.llm.ports import LlmProvider
from newsimpact.market.adapters.csv_file import CsvMarketData
from newsimpact.market.adapters.eodhd import EodhdMarketData
from newsimpact.market.models import MeasurementPolicy
from newsimpact.market.ports import MarketData
from newsimpact.reliability.adapters.memory import InMemoryEvidenceStore, InMemoryTrackedSources
from newsimpact.reliability.adapters.sqlite import SqliteEvidenceStore, SqliteTrackedSources
from newsimpact.reliability.ports import EvidenceStore, TrackedSources
from newsimpact.semantics.adapters.lexicon import (
    AttributionStep,
    LexiconSentiment,
    TaxonomyClassifier,
    WordListSignal,
)
from newsimpact.semantics.models import Taxonomy
from newsimpact.semantics.ports import ClaimStep
from newsimpact.shared.bus import EventBus, InMemoryEventBus
from newsimpact.shared.sqlite import Database
from newsimpact.sources.adapters.fixture import FixtureFeed
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
from newsimpact.sources.models import FeedConfig, Source
from newsimpact.sources.ports import ArticleStore, Feed, SeenSources, WatchStore
from newsimpact.storylines.adapters.memory import InMemoryStorylineStore
from newsimpact.storylines.adapters.sqlite import SqliteStorylineStore
from newsimpact.storylines.ports import StorylineStore
from newsimpact.validation.adapters.memory import InMemoryAssessmentStore
from newsimpact.validation.adapters.sqlite import SqliteAssessmentStore
from newsimpact.validation.ports import AssessmentStore


@dataclass(frozen=True)
class Stores:
    db: Database | None
    articles: ArticleStore
    seen_sources: SeenSources
    watches: WatchStore
    tracked_sources: TrackedSources
    evidence: EvidenceStore
    storylines: StorylineStore
    assessments: AssessmentStore
    alerts: AlertState
    briefs: BriefStore


@dataclass(frozen=True)
class Context:
    """What a plug-in may need to build itself."""

    settings: Settings
    http: httpx.Client | None  # None in the demo profile: nothing may touch the network
    tickers: tuple[str, ...]  # the companies we follow


def pick[T](table: Mapping[str, T], name: str, what: str) -> T:
    """The entry for `name`, or a start-up error that lists the known names."""
    if name not in table:
        raise ValueError(f"unknown {what} {name!r}; known: {sorted(table)}")
    return table[name]


def _network(ctx: Context) -> httpx.Client:
    if ctx.http is None:
        raise ValueError("this feed needs the network: use NI_PROFILE=live")
    return ctx.http


# ------------------------------------------------------------ storage
def _sqlite_stores(s: Settings) -> Stores:
    db = Database(s.db_path)
    return Stores(db, SqliteArticleStore(db), SqliteSeenSources(db), SqliteWatchStore(db),
                  SqliteTrackedSources(db), SqliteEvidenceStore(db), SqliteStorylineStore(db),
                  SqliteAssessmentStore(db), SqliteAlertState(db), SqliteBriefs(db))  # fmt: skip


def _memory_stores(s: Settings) -> Stores:
    return Stores(None, InMemoryArticleStore(), InMemorySeenSources(), InMemoryWatchStore(),
                  InMemoryTrackedSources(), InMemoryEvidenceStore(), InMemoryStorylineStore(),
                  InMemoryAssessmentStore(), InMemoryAlertState(), InMemoryBriefs())  # fmt: skip


STORES: dict[str, Callable[[Settings], Stores]] = {
    "memory": _memory_stores,
    "sqlite": _sqlite_stores,
}

EVENT_BUSES: dict[str, Callable[[Settings], EventBus]] = {
    "memory": lambda s: InMemoryEventBus(),
}


# ------------------------------------------------------------ sign-in
AUTH: dict[str, Callable[[Settings], Authenticator]] = {
    "local": lambda s: LocalSingleUser(),
}


# ------------------------------------------------------------ news feeds
def _per_company(ctx: Context, source: Source, config: FeedConfig) -> Feed:
    return PerCompanyRssFeed(source, config.url, ctx.tickers, _network(ctx))


FEEDS: dict[str, Callable[[Context, Source, FeedConfig], Feed]] = {
    "rss": lambda ctx, src, cfg: RssFeed(src, cfg.url, _network(ctx)),
    "rss_per_company": _per_company,
    "fixture": lambda ctx, src, cfg: FixtureFeed(src, ctx.settings.demo_dir / "articles.json"),
}


# ------------------------------------------------------------ market data
def _eodhd(ctx: Context, policy: MeasurementPolicy) -> MarketData:
    key = ctx.settings.eodhd_api_key
    if key is None:
        raise ValueError("NI_MARKET_DATA=eodhd needs NI_EODHD_API_KEY")
    return EodhdMarketData(httpx.Client(timeout=30), key.get_secret_value(), policy.vendor_symbol)


MARKET_DATA: dict[str, Callable[[Context, MeasurementPolicy], MarketData | None]] = {
    "none": lambda ctx, policy: None,
    "eodhd": _eodhd,
    "csv": lambda ctx, policy: CsvMarketData(ctx.settings.market_csv_dir),
}


# ------------------------------------------------------------ language models
def _anthropic(s: Settings, preset: LlmPreset) -> LlmProvider:
    # imported only when chosen: an optional dependency
    from newsimpact.llm.adapters.anthropic_api import AnthropicProvider

    key = s.anthropic_api_key.get_secret_value() if s.anthropic_api_key else None
    return AnthropicProvider(preset.model, effort=preset.effort, api_key=key)


LLM_PROVIDERS: dict[str, Callable[[Settings, LlmPreset], LlmProvider]] = {
    "anthropic": _anthropic,
    "ollama": lambda s, p: OllamaProvider(p.model, httpx.Client(timeout=120), s.llm_base_url),
}

# ------------------------------------------------------------ text analysis
SEMANTIC_STEPS: dict[str, Callable[[Taxonomy], ClaimStep]] = {
    "taxonomy": TaxonomyClassifier,
    "attribution": AttributionStep,
    "sentiment": LexiconSentiment,
    "uncertainty": lambda t: WordListSignal(t, "uncertainty"),
    # the "llm" step is added by the wiring when a preset is on (it needs the gateway)
}


# ------------------------------------------------------------ alert channels
def _discord(ctx: Context) -> Notifier | None:
    url = ctx.settings.discord_webhook_url
    if url is None or not url.get_secret_value():
        return None
    return DiscordNotifier(ctx.http or httpx.Client(timeout=15), url.get_secret_value())


# Every channel that is configured is used (None = not configured).
NOTIFIERS: tuple[Callable[[Context], Notifier | None], ...] = (_discord,)
