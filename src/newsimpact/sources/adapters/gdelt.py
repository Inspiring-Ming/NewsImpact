"""NewsSearch over the GDELT DOC 2.0 API (free, global, multilingual).

Limits to know: returns headline-level metadata (no article body), covers
roughly the last 3 months, and is rate-limited - be polite. For production,
pair with a licensed full-text provider behind the same port.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime

import httpx

from newsimpact.shared.text import content_hash, stable_id
from newsimpact.sources.models import Article, SearchHit

API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
_LANG = {
    "english": "en",
    "chinese": "zh",
    "japanese": "ja",
    "german": "de",
    "french": "fr",
    "spanish": "es",
    "korean": "ko",
    "italian": "it",
    "portuguese": "pt",
    "russian": "ru",
}


def _any_of(parts: Sequence[str]) -> str:
    return parts[0] if len(parts) == 1 else f"({' OR '.join(parts)})"


def build_query(entity_name: str, terms: Sequence[str], domains: Sequence[str] = ()) -> str:
    query = f'"{entity_name}"'
    if terms:
        query += " " + _any_of([f'"{t}"' if " " in t else t for t in terms])
    if domains:
        query += " " + _any_of([f"domain:{d}" for d in domains])
    return query


class GdeltSearch:
    """GDELT asks for at most ~1 request / 5 s: we space requests out, and on
    HTTP 429 we back off and retry."""

    def __init__(
        self,
        client: httpx.Client,
        max_records: int = 75,
        retries: int = 3,
        backoff_seconds: float = 6.0,
        sleep: Callable[[float], None] = time.sleep,
        min_interval_seconds: float = 5.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._client = client
        self._max = max_records
        self._retries = retries
        self._backoff = backoff_seconds
        self._sleep = sleep
        self._min_interval = min_interval_seconds
        self._clock = clock
        self._last_call: float | None = None

    def _get(self, params: dict[str, str]) -> httpx.Response:
        for attempt in range(self._retries + 1):
            self._wait_turn()
            resp = self._client.get(API_URL, params=params)
            if resp.status_code != httpx.codes.TOO_MANY_REQUESTS or attempt == self._retries:
                break
            self._sleep(self._backoff * (attempt + 1))
        resp.raise_for_status()
        return resp

    def _wait_turn(self) -> None:
        if self._last_call is not None:
            wait = self._min_interval - (self._clock() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._clock()

    def search(
        self,
        entity_name: str,
        terms: Sequence[str],
        since: datetime,
        until: datetime,
        domains: Sequence[str] = (),
    ) -> Iterable[SearchHit]:
        params = {
            "query": build_query(entity_name, terms, domains),
            "mode": "artlist",
            "format": "json",
            "sort": "dateasc",
            "maxrecords": str(self._max),
            "startdatetime": since.astimezone(UTC).strftime("%Y%m%d%H%M%S"),
            "enddatetime": until.astimezone(UTC).strftime("%Y%m%d%H%M%S"),
        }
        resp = self._get(params)
        if not resp.content.strip().startswith(b"{"):
            return []  # GDELT answers plain text for empty/invalid queries
        now = datetime.now(UTC)
        hits: list[SearchHit] = []
        for row in resp.json().get("articles", []):
            domain = str(row.get("domain", "unknown"))
            title = str(row.get("title", "")).strip()
            url = str(row.get("url", ""))
            article = Article(
                article_id=stable_id(url),
                source_id=domain,  # resolved to a listed outlet by the service
                url=url,
                title=title,
                body=title,  # GDELT provides headlines only
                language=_LANG.get(str(row.get("language", "")).lower(), "und"),
                published_at=datetime.strptime(row["seendate"], "%Y%m%dT%H%M%SZ").replace(
                    tzinfo=UTC
                ),
                ingested_at=now,
                content_hash=content_hash(title, ""),
            )
            hits.append(
                SearchHit(domain=domain, country=row.get("sourcecountry") or None, article=article)
            )
        return hits
