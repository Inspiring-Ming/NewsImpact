from datetime import UTC, datetime

import httpx

from newsimpact.sources.adapters.rss import RssFeed, parse_feed
from newsimpact.sources.models import Source

NOW = datetime(2026, 3, 21, tzinfo=UTC)

RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>Biz</title>
  <item>
    <title>Globex Motors CEO to step down</title>
    <link>https://news.example/globex-ceo</link>
    <description>&lt;p&gt;Chief executive Dana Reyes will step down.&lt;/p&gt;</description>
    <pubDate>Fri, 20 Mar 2026 13:00:00 GMT</pubDate>
  </item>
  <item><title>No date, skipped</title><link>https://news.example/x</link></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Filings</title>
  <entry>
    <title>8-K - Globex Motors</title>
    <link href="https://filings.example/8k"/>
    <summary>Departure of Directors or Certain Officers</summary>
    <updated>2026-03-20T16:00:00-04:00</updated>
  </entry>
</feed>"""


def test_parses_rss_items_strips_html_and_skips_undated() -> None:
    articles = parse_feed(RSS, "news", NOW)
    assert len(articles) == 1
    a = articles[0]
    assert a.body == "Globex Motors CEO to step down. Chief executive Dana Reyes will step down."
    assert a.published_at == datetime(2026, 3, 20, 13, tzinfo=UTC)
    assert a.source_id == "news"


def test_parses_atom_entries() -> None:
    (a,) = parse_feed(ATOM, "sec", NOW)
    assert a.url == "https://filings.example/8k"
    assert a.published_at == datetime(2026, 3, 20, 20, tzinfo=UTC)


def test_feed_filters_by_since() -> None:
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=RSS)))
    source = Source(source_id="news", name="News", domains=("news.example",))
    feed = RssFeed(source, "https://news.example/rss", client)
    assert len(list(feed.fetch())) == 1
    assert list(feed.fetch(since=NOW)) == []
