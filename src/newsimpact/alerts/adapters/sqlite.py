"""SQLite AlertState: followed companies, last snapshot and sent alerts survive restarts.

Per-person rows are keyed "<user_id>|<ticker or alert key>" and tagged with the
user, so one person's list is one indexed lookup.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence

from newsimpact.alerts.models import EventSnapshot
from newsimpact.shared.sqlite import Database


class SqliteAlertState:
    def __init__(self, db: Database) -> None:
        self._followed = db.collection("followed")
        self._snapshot = db.collection("alert_snapshot")
        self._sent = db.collection("alerts_sent")

    def followed(self, user_id: str) -> set[str]:
        return {json.loads(d)["ticker"] for d in self._followed.find(user_id)}

    def set_followed(self, user_id: str, ticker: str, follow: bool) -> None:
        key = f"{user_id}|{ticker}"
        if follow:
            self._followed.put(key, json.dumps({"user_id": user_id, "ticker": ticker}),
                               tag=user_id)  # fmt: skip
        else:
            self._followed.delete(key)

    def followers(self) -> Mapping[str, set[str]]:
        out: dict[str, set[str]] = defaultdict(set)
        for doc in self._followed.find():
            row = json.loads(doc)
            out[row["user_id"]].add(row["ticker"])
        return out

    def snapshot(self) -> Mapping[str, EventSnapshot] | None:
        doc = self._snapshot.get("last")
        if doc is None:
            return None
        return {e["event_id"]: EventSnapshot.model_validate(e) for e in json.loads(doc)}

    def save_snapshot(self, events: Sequence[EventSnapshot]) -> None:
        self._snapshot.put("last", json.dumps([e.model_dump(mode="json") for e in events]))

    def was_sent(self, user_id: str, key: str) -> bool:
        return self._sent.get(f"{user_id}|{key}") is not None

    def mark_sent(self, user_id: str, key: str) -> None:
        self._sent.put(f"{user_id}|{key}", "{}", tag=user_id)
