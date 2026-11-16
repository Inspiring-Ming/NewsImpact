"""QuestionLog in SQLite: one row per person and day, so the daily limit survives restarts."""

from __future__ import annotations

from newsimpact.shared.sqlite import Database


class SqliteQuestionLog:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("assistant_questions")

    def count(self, user_id: str, day: str) -> int:
        doc = self._c.get(f"{user_id}|{day}")
        return int(doc) if doc else 0

    def add(self, user_id: str, day: str) -> None:
        self._c.put(f"{user_id}|{day}", str(self.count(user_id, day) + 1), tag=user_id, at=day)
