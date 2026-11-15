"""Shared test fixtures: the real reference policies, so tests use the configured numbers.

Tests never use a developer's local .env deployment choices (LLM presets, keys,
live data): environment variables override .env, so these pin an offline,
free configuration for every test.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest

from newsimpact.market.models import MeasurementPolicy
from newsimpact.validation.models import ValidationPolicy

os.environ.update(
    {
        "NI_PROFILE": "demo",
        "NI_STORE": "memory",
        "NI_MARKET_DATA": "none",
        "NI_LLM_PRESET": "off",
        "NI_MONITOR_EVERY_MINUTES": "0",
        "ANTHROPIC_API_KEY": "",
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
