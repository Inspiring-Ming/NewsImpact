import json
from datetime import UTC, datetime

import httpx

from newsimpact.sources.adapters.gdelt import GdeltSearch, build_query

T0 = datetime(2026, 3, 1, tzinfo=UTC)
T1 = datetime(2026, 3, 31, tzinfo=UTC)


def test_build_query_quotes_phrases_and_limits_domains() -> None:
    assert build_query("Globex", ["steps down", "resigns"]) == '"Globex" ("steps down" OR resigns)'
    assert build_query("Globex", ["resigns"], ["bbc.com"]) == '"Globex" resigns domain:bbc.com'
    assert (
        build_query("Globex", [], ["a.com", "b.com"]) == '"Globex" (domain:a.com OR domain:b.com)'
    )


def _client(payload: bytes, seen: list[httpx.Request]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, content=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_parses_articles_and_passes_window() -> None:
    payload = json.dumps({"articles": [{
        "url": "https://news.example/x", "title": "Globex CEO steps down",
        "seendate": "20260320T130000Z", "domain": "news.example",
        "language": "English", "sourcecountry": "United States",
    }]}).encode()  # fmt: skip
    seen: list[httpx.Request] = []
    hits = list(GdeltSearch(_client(payload, seen)).search("Globex", ["steps down"], T0, T1))

    assert seen[0].url.params["startdatetime"] == "20260301000000"
    hit = hits[0]
    assert hit.domain == "news.example"
    assert hit.country == "United States"
    assert hit.article.language == "en"
    assert hit.article.published_at == datetime(2026, 3, 20, 13, tzinfo=UTC)


def test_non_json_reply_means_no_hits() -> None:
    seen: list[httpx.Request] = []
    assert (
        list(GdeltSearch(_client(b"Your query was too short", seen)).search("X", [], T0, T1)) == []
    )


def test_backs_off_and_retries_on_rate_limit() -> None:
    replies = iter([httpx.Response(429), httpx.Response(200, content=b'{"articles": []}')])
    waits: list[float] = []
    client = httpx.Client(transport=httpx.MockTransport(lambda _: next(replies)))
    search = GdeltSearch(client, sleep=waits.append, min_interval_seconds=0)
    assert list(search.search("X", ["y"], T0, T1)) == []
    assert waits == [6.0]


def test_requests_are_spaced_out_politely() -> None:
    waits: list[float] = []
    now = iter([0.0, 1.0, 5.0])  # clock readings: call 1 stamp, call 2 check, call 2 stamp
    client = httpx.Client(transport=httpx.MockTransport(
        lambda _: httpx.Response(200, content=b'{"articles": []}')))  # fmt: skip
    search = GdeltSearch(client, sleep=waits.append, clock=lambda: next(now))
    search.search("X", ["y"], T0, T1)
    search.search("X", ["y"], T0, T1)
    assert waits == [4.0]  # 5 s minimum interval, 1 s already passed
