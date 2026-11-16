"""QuestionLog in memory: for tests and the demo (counts reset on restart)."""

from __future__ import annotations

from collections import Counter


class InMemoryQuestionLog:
    def __init__(self) -> None:
        self._n: Counter[str] = Counter()

    def count(self, user_id: str, day: str) -> int:
        return self._n[f"{user_id}|{day}"]

    def add(self, user_id: str, day: str) -> None:
        self._n[f"{user_id}|{day}"] += 1
