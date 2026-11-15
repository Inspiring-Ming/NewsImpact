"""Feed for RSS 2.0 and Atom - the format most news sites publish.

Gives headline + summary (not full text), which is enough for claims and
storylines. Parsed with defusedxml so hostile feeds cannot attack the parser.
Licensing: reading public feeds for research is usually fine; showing their
content to paying clients needs each publisher's terms (docs/01).
"""

from __future__ import annotations

import html
import logging
import re
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree.ElementTree import Element

import httpx
from defusedxml import ElementTree

from newsimpact.shared.text import content_hash, stable_id
from newsimpact.sources.models import Article, Source

log = logging.getLogger(__name__)
_ATOM = "{http://www.w3.org/2005/Atom}"
_TAGS = re.compile(r"<[^>]+>")


def _text(node: Element | None) -> str:
    raw = node.text if node is not None and node.text else ""
    return html.unescape(_TAGS.sub(" ", raw)).strip()


def _date(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    try:
        parsed = (
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            if value[:4].isdigit()
            else parsedate_to_datetime(value)
        )
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def parse_feed(xml: bytes, source_id: str, now: datetime) -> list[Article]:
    """RSS <item> or Atom <entry> -> Article. Items without link or date are skipped."""
    root = ElementTree.fromstring(xml)
    items = root.iter("item") if root.tag != f"{_ATOM}feed" else root.iter(f"{_ATOM}entry")
    out: list[Article] = []
    for item in items:
        is_atom = item.tag.startswith(_ATOM)
        ns = _ATOM if is_atom else ""
        title = _text(item.find(f"{ns}title"))
        if is_atom:
            link_node = item.find(f"{_ATOM}link")
            link = link_node.get("href", "") if link_node is not None else ""
            body = _text(item.find(f"{_ATOM}summary")) or _text(item.find(f"{_ATOM}content"))
            when = _date(
                _text(item.find(f"{_ATOM}published")) or _text(item.find(f"{_ATOM}updated"))
            )
        else:
            link = _text(item.find("link"))
            body = _text(item.find("description"))
            when = _date(_text(item.find("pubDate")))
        if not link or not title or when is None:
            continue
        out.append(
            Article(
                article_id=stable_id(link),
                source_id=source_id,
                url=link,
                title=title,
                # Title first: the headline usually carries the main claim.
                body=f"{title}. {body}" if body else title,
                published_at=when,
                ingested_at=now,
                content_hash=content_hash(title, body),
            )
        )
    return out


class RssFeed:
    def __init__(self, source: Source, url: str, client: httpx.Client) -> None:
        self._source = source
        self.url = url
        self._client = client

    def fetch(self, since: datetime | None = None) -> Iterable[Article]:
        resp = self._client.get(self.url, follow_redirects=True)
        resp.raise_for_status()
        articles = parse_feed(resp.content, self._source.source_id, datetime.now(UTC))
        return [a for a in articles if since is None or a.published_at > since]


class PerCompanyRssFeed:
    """One RSS URL per company ("{ticker}" in the URL), read as one feed.

    A provider's per-company feeds cover every tracked company, not only those a
    general business section happens to mention. A failing company feed is
    skipped so one bad symbol does not drop the rest.
    """

    def __init__(
        self, source: Source, url_template: str, tickers: Sequence[str], client: httpx.Client
    ) -> None:
        self._feeds = [RssFeed(source, url_template.format(ticker=t), client) for t in tickers]

    def fetch(self, since: datetime | None = None) -> Iterable[Article]:
        out: list[Article] = []
        for feed in self._feeds:
            try:
                out += feed.fetch(since)
            except (httpx.HTTPError, ElementTree.ParseError, ValueError):  # ValueError: defusedxml
                log.warning("company feed failed", extra={"url": feed.url})
        return out
