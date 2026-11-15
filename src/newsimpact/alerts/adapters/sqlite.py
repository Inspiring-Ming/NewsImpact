"""SQLite AlertState: followed companies, last snapshot and sent alerts survive restarts."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from newsimpact.alerts.models import EventSnapshot
from newsimpact.shared.sqlite import Database


class SqliteAlertState:
    def __init__(self, db: Database) -> None:
        self._followed = db.collection("followed")
        self._snapshot = db.collection("alert_snapshot")
        self._sent = db.collection("alerts_sent")

    def followed(self) -> set[str]:
        return {json.loads(d)["ticker"] for d in self._followed.find()}

    def set_followed(self, ticker: str, follow: bool) -> None:
        if follow:
            self._followed.put(ticker, json.dumps({"ticker": ticker}))
        else:
            self._followed.delete(ticker)

    def snapshot(self) -> Mapping[str, EventSnapshot] | None:
        doc = self._snapshot.get("last")
        if doc is None:
            return None
        return {e["event_id"]: EventSnapshot.model_validate(e) for e in json.loads(doc)}

    def save_snapshot(self, events: Sequence[EventSnapshot]) -> None:
        self._snapshot.put("last", json.dumps([e.model_dump(mode="json") for e in events]))

    def was_sent(self, key: str) -> bool:
        return self._sent.get(key) is not None

    def mark_sent(self, key: str) -> None:
        self._sent.put(key, "{}")
