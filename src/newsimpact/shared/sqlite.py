"""A tiny JSON document table on SQLite - shared by the modules' `adapters/sqlite.py`.

Only adapters may use this (enforced by `make arch`). SQLite needs no server
and costs nothing, which suits a single machine monitoring a few outlets.
For the cloud, each module gets a Postgres adapter behind the same ports.

Layout: one table, rows keyed by (collection, key), with one optional
indexed column (`tag`) for lookups and a sortable time column (`at`).
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    collection TEXT NOT NULL,
    key        TEXT NOT NULL,
    tag        TEXT NOT NULL DEFAULT '',
    at         TEXT NOT NULL DEFAULT '',
    doc        TEXT NOT NULL,
    PRIMARY KEY (collection, key)
);
CREATE INDEX IF NOT EXISTS documents_tag ON documents (collection, tag);
"""


class Database:
    """One SQLite file shared by all stores (thread-safe for the API's worker threads)."""

    def __init__(self, path: Path | str) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock, self._conn:
            self._conn.executescript(_SCHEMA)

    def collection(self, name: str) -> Collection:
        return Collection(self, name)

    def execute(self, sql: str, params: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
        with self._lock, self._conn:
            return list(self._conn.execute(sql, params).fetchall())


class Collection:
    def __init__(self, db: Database, name: str) -> None:
        self._db = db
        self._name = name

    def put(self, key: str, doc: str, *, tag: str = "", at: str = "") -> None:
        self._db.execute(
            "INSERT INTO documents (collection, key, tag, at, doc) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT (collection, key) DO UPDATE SET tag=excluded.tag, at=excluded.at, "
            "doc=excluded.doc",
            (self._name, key, tag, at, doc),
        )

    def get(self, key: str) -> str | None:
        rows = self._db.execute(
            "SELECT doc FROM documents WHERE collection=? AND key=?", (self._name, key)
        )
        return rows[0][0] if rows else None

    def delete(self, key: str) -> None:
        self._db.execute("DELETE FROM documents WHERE collection=? AND key=?", (self._name, key))

    def has_tag(self, tag: str) -> bool:
        rows = self._db.execute(
            "SELECT 1 FROM documents WHERE collection=? AND tag=? LIMIT 1", (self._name, tag)
        )
        return bool(rows)

    def find(
        self, tag: str | None = None, *, newest_first: bool = False, limit: int = -1
    ) -> list[str]:
        where: str = "collection=?"
        params: tuple[str, ...] = (self._name,)
        if tag is not None:
            where, params = ("collection=? AND tag=?", (self._name, tag))
        order = "DESC" if newest_first else "ASC"
        sql = f"SELECT doc FROM documents WHERE {where} ORDER BY at {order}, key LIMIT {int(limit)}"  # noqa: S608 - no user input in the SQL text
        return [r[0] for r in self._db.execute(sql, params)]
