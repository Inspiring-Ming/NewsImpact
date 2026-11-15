"""LLM cache and spending ledger survive restarts (SQLite)."""

from pathlib import Path

from newsimpact.llm.adapters.sqlite import SqliteResponseCache, SqliteSpendLedger
from newsimpact.llm.models import LlmResult
from newsimpact.shared.sqlite import Database


def test_cache_and_ledger_persist(tmp_path: Path) -> None:
    db = Database(tmp_path / "l.db")
    cache, ledger = SqliteResponseCache(db), SqliteSpendLedger(db)
    assert cache.get("k") is None
    cache.put("k", LlmResult(data={"a": 1}, model="m", cost_usd=0.01, cached=False))
    again = SqliteResponseCache(Database(tmp_path / "l.db")).get("k")
    assert again is not None and again.data == {"a": 1}
    ledger.record("2026-11", "briefs.event", "m", 0.25)
    ledger.record("2026-11", "semantics.classify", "m", 0.5)
    assert SqliteSpendLedger(Database(tmp_path / "l.db")).spent("2026-11") == 0.75
    assert ledger.spent("2026-12") == 0.0
