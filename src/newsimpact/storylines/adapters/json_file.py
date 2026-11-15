"""PlaybookCatalog from a JSON file (data/reference/playbooks.json)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from newsimpact.storylines.models import Playbook


class JsonPlaybookCatalog:
    def __init__(self, playbooks: Sequence[Playbook], late_report_days: int = 3) -> None:
        self._playbooks = tuple(playbooks)
        self.late_report_days = late_report_days

    @classmethod
    def from_file(cls, path: Path) -> JsonPlaybookCatalog:
        raw = json.loads(path.read_text())
        return cls([Playbook.model_validate(p) for p in raw["playbooks"]], raw["late_report_days"])

    def playbooks(self) -> Sequence[Playbook]:
        return self._playbooks
