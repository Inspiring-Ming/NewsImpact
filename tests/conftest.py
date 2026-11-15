"""Shared test fixtures: the real reference policies, so tests use the configured numbers.

Tests never read a developer's .env (keys, alert links, live data): Settings
is told not to load it, and the variables below pin an offline, free setup even
when a shell or CI exports NI_* values. A new setting is safe by default.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest

from newsimpact.app.config import Settings
from newsimpact.market.models import MeasurementPolicy
from newsimpact.validation.models import ValidationPolicy

Settings.model_config["env_file"] = None  # never the developer's .env

os.environ.update(
    {
        "NI_PROFILE": "demo",
        "NI_STORE": "memory",
        "NI_MARKET_DATA": "none",
        "NI_LLM_PRESET": "off",
        "NI_MONITOR_EVERY_MINUTES": "0",
        "ANTHROPIC_API_KEY": "",
        "NI_EODHD_API_KEY": "",
        "NI_DISCORD_WEBHOOK_URL": "",
        "NI_AUTH": "local",
    }
)

REFERENCE = Path(__file__).resolve().parents[1] / "data" / "reference"


def _section(name: str) -> dict[str, Any]:
    raw = json.loads((REFERENCE / "methodology.json").read_text())[name]
    return {k: v for k, v in raw.items() if k != "rationale"}


@pytest.fixture
def measurement_policy() -> MeasurementPolicy:
    return MeasurementPolicy.model_validate(_section("market"))


@pytest.fixture
def validation_policy() -> ValidationPolicy:
    return ValidationPolicy.model_validate(_section("validation"))
