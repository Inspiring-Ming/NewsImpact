"""Health, overview counts, and the method: settings with reasons, calibration, accuracy."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter

from newsimpact import __version__
from newsimpact.app.api.context import ApiContext
from newsimpact.app.views import system as views
from newsimpact.app.views.system import Evaluation, Overview
from newsimpact.llm.models import LlmPreset
from newsimpact.shared.events import Model
from newsimpact.storylines.models import Playbook
from newsimpact.validation.models import StageChannelCalibration, WindowCalibration


class Calibration(Model):
    reactions: tuple[StageChannelCalibration, ...]
    windows: tuple[WindowCalibration, ...]


class Method(Model):
    """Every setting with its reason - what the website's "How it works" page shows."""

    methodology: dict[str, Any]
    playbooks: tuple[Playbook, ...]
    late_report_days: int
    llm_presets: dict[str, LlmPreset]
    llm_preset_in_use: str


def router(api: ApiContext) -> APIRouter:
    r = APIRouter()
    svc = api.svc

    @r.get("/health")
    def health() -> dict[str, str]:
        s = svc.settings
        return {"status": "ok", "version": __version__, "env": s.env, "profile": s.profile}

    @r.get("/v1/overview", response_model=Overview)
    def overview() -> Overview:
        return views.overview(svc)

    @r.get("/v1/calibration", response_model=Calibration)
    def calibration() -> Calibration:
        """Across events: does each update move each measure as expected? Do windows fit?"""
        reactions, windows = svc.validation.calibrate(svc.storyline_store.all())
        return Calibration(reactions=tuple(reactions), windows=tuple(windows))

    @r.get("/v1/evaluation", response_model=Evaluation)
    def evaluation() -> Evaluation:
        """Analysis quality on the hand-labelled set. Computed once per server start: the
        labelled set and the reading chain only change with a deploy, and the website shows
        it on every visit (with an LLM preset each run would cost money)."""
        if "evaluation" not in api.cache:
            api.cache["evaluation"] = views.evaluation(svc)
        result: Evaluation = api.cache["evaluation"]
        return result

    @r.get("/v1/method", response_model=Method)
    def method() -> Method:
        raw = json.loads((svc.settings.reference_dir / "methodology.json").read_text())
        return Method(methodology=raw, playbooks=tuple(svc.playbooks.playbooks()),
                      late_report_days=svc.playbooks.late_report_days,
                      llm_presets=svc.llm_presets,
                      llm_preset_in_use=svc.settings.llm_preset)  # fmt: skip

    return r
