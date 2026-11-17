"""Settings from environment variables (prefix NI_), 12-factor style.

Only *deployment* choices live here (which technology, where, how much money).
*Method* choices (windows, thresholds, what to look for, LLM presets) live in
data/reference/*.json with their reasons, so they are versioned and hashed.
Secrets (API keys) are read from the environment and never written to files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NI_", env_file=".env", extra="ignore")

    env: Literal["local", "test", "dev", "staging", "prod"] = "local"
    log_level: str = "INFO"
    # demo = fictional outlets/news/prices, no network.
    # live = the real outlets in data/reference/sources.json + GDELT search.
    profile: Literal["demo", "live"] = "demo"
    data_dir: Path = _REPO_ROOT / "data"
    web_dir: Path = _REPO_ROOT / "web" / "dist"  # built website, served at /
    # Where state lives: memory (lost on exit) or sqlite (survives restarts).
    store: str = "memory"  # memory | sqlite (wiring/plugins.py STORES)
    event_bus: str = "memory"  # memory; cloud buses join wiring/plugins.py EVENT_BUSES
    # Who may use the site: local = one built-in admin, no sign-in (a single person on their
    # own computer); demo = a public demo: everyone reads, only requests carrying
    # NI_ADMIN_TOKEN change anything (ADR 0037). Accounts for many users: cognito, next.
    auth: str = "local"
    admin_token: SecretStr | None = None  # NI_AUTH=demo: the owner's key (24+ characters)
    db_path: Path = _REPO_ROOT / "var" / "newsimpact.db"
    # Automatic monitoring inside the server: minutes between rounds, 0 = only on demand.
    monitor_every_minutes: float = 0
    accept_unlisted_sources: bool = False
    http_user_agent: str = "newsimpact/0.1"

    # Analysis chain after claim extraction (names: app/wiring/plugins.py SEMANTIC_STEPS);
    # the LLM step is added automatically when a preset is on.
    semantic_steps: tuple[str, ...] = ("taxonomy", "attribution", "sentiment", "uncertainty")

    # Market data for the live profile (demo always uses synthetic prices).
    market_data: str = "none"  # none | eodhd | csv (wiring/plugins.py MARKET_DATA)
    eodhd_api_key: SecretStr | None = None
    market_csv_dir: Path = _REPO_ROOT / "var" / "prices"

    # Language model: off | quality | economy | local (see data/reference/llm_models.json).
    llm_preset: Literal["off", "quality", "economy", "local"] = "off"
    llm_base_url: str = "http://localhost:11434"  # Ollama, for the "local" preset
    llm_scope: Literal["candidates", "all"] = (
        "all"  # measured: "all" is worth its tiny cost (docs/07)
    )
    # Read from .env or the environment under its usual name (not NI_-prefixed).
    anthropic_api_key: SecretStr | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    llm_monthly_budget_usd: float = 5.0

    # Alerts for followed companies. A Discord incoming-webhook URL is a secret (anyone with
    # it can post to the channel): set it only in the git-ignored .env. Unset = alerts off.
    discord_webhook_url: SecretStr | None = None
    site_url: str = "http://localhost:8000"  # where alert links point
    llm_max_calls_per_round: int = 200

    @property
    def reference_dir(self) -> Path:
        """Curated, real reference data (outlets, taxonomy, playbooks, entities, methodology)."""
        return self.data_dir / "reference"

    @property
    def demo_dir(self) -> Path:
        """Fictional demo data."""
        return self.data_dir / "demo"

    @property
    def profile_dir(self) -> Path:
        return self.demo_dir if self.profile == "demo" else self.reference_dir
