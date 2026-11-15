"""SQLite AssessmentStore: full history, so you can see how evidence matured."""

from __future__ import annotations

from collections.abc import Sequence

from newsimpact.shared.sqlite import Database
from newsimpact.validation.models import Assessment


class SqliteAssessmentStore:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("assessments")

    def add(self, assessment: Assessment) -> None:
        key = f"{assessment.storyline_id}|{assessment.as_of.isoformat()}"
        self._c.put(key, assessment.model_dump_json(), tag=assessment.storyline_id,
                    at=assessment.as_of.isoformat())  # fmt: skip

    def latest(self, storyline_id: str) -> Assessment | None:
        docs = self._c.find(storyline_id, newest_first=True, limit=1)
        return Assessment.model_validate_json(docs[0]) if docs else None

    def latest_all(self) -> Sequence[Assessment]:
        latest: dict[str, Assessment] = {}
        for doc in self._c.find(newest_first=True):
            a = Assessment.model_validate_json(doc)
            latest.setdefault(a.storyline_id, a)
        return list(latest.values())
