"""Presets and price table from data/reference/llm_models.json."""

from __future__ import annotations

import json
from pathlib import Path

from newsimpact.llm.models import LlmPreset, ModelPrice


def load_models(path: Path) -> tuple[dict[str, LlmPreset], dict[str, ModelPrice]]:
    raw = json.loads(path.read_text())
    presets = {name: LlmPreset.model_validate(p) for name, p in raw["presets"].items()}
    prices = {model: ModelPrice.model_validate(p) for model, p in raw["models"].items()}
    return presets, prices
