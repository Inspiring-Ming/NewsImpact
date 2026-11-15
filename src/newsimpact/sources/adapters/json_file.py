"""SourceRegistry read from a JSON file: {"sources": [<SourceListing>, ...]}."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from newsimpact.sources.models import SourceListing


class JsonSourceRegistry:
    def __init__(self, listings: Sequence[SourceListing]) -> None:
        ids = [s.source_id for s in listings]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate source_id in source list")
        self._listings = tuple(listings)

    @classmethod
    def from_file(cls, path: Path) -> JsonSourceRegistry:
        rows = json.loads(path.read_text())["sources"]
        return cls([SourceListing.model_validate(r) for r in rows])

    def listings(self) -> Sequence[SourceListing]:
        return self._listings
