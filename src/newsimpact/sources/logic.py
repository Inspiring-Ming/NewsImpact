"""Copy detection and outlet coverage - pure functions, no I/O.

Exact copies share a content hash. Near-copies (syndicated wire stories with
a changed headline, light rewrites) are found by comparing sets of 5-word
shingles (Broder 1997): resemblance = |A & B| / |A | B|.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import datetime

from newsimpact.shared.text import normalise
from newsimpact.sources.models import Article, OutletCoverage

SHINGLE_WORDS = 5
_WORD = re.compile(r"[a-z0-9']+")


def shingles(text: str, k: int = SHINGLE_WORDS) -> frozenset[str]:
    words = _WORD.findall(normalise(text))
    if len(words) < k:
        return frozenset({" ".join(words)}) if words else frozenset()
    return frozenset(" ".join(words[i : i + k]) for i in range(len(words) - k + 1))


def resemblance(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def coverage(
    articles: Sequence[Article],
    with_company: set[str],
    with_trigger: set[str],
    stage_reports: Iterable[Sequence[tuple[str, datetime]]],
) -> list[OutletCoverage]:
    """Per outlet: volume, relevance, originality and speed.

    `stage_reports`: for each storyline stage, the (source_id, published_at)
    of every outlet that reported it - the earliest one reported it first.
    """
    by_outlet: dict[str, list[Article]] = defaultdict(list)
    for a in articles:
        by_outlet[a.source_id].append(a)
    reported: dict[str, int] = defaultdict(int)
    first: dict[str, int] = defaultdict(int)
    for reports in stage_reports:
        for source_id in {s for s, _ in reports}:
            reported[source_id] += 1
        if reports:
            first[min(reports, key=lambda r: r[1])[0]] += 1
    rows = []
    for source_id, items in sorted(by_outlet.items()):
        n = len(items)
        times = [a.published_at for a in items]
        days = max((max(times) - min(times)).total_seconds() / 86400, 1.0)
        rows.append(OutletCoverage(
            source_id=source_id, articles=n, per_day=round(n / days, 2),
            with_company=round(sum(a.article_id in with_company for a in items) / n, 3),
            with_trigger=round(sum(a.article_id in with_trigger for a in items) / n, 3),
            copies=round(sum(a.copy_of is not None for a in items) / n, 3),
            stages_reported=reported[source_id], stages_first=first[source_id],
        ))  # fmt: skip
    return rows
