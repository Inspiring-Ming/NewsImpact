"""JSON reference files for semantics: the companies we can recognise, and the taxonomy."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from pathlib import Path

from newsimpact.semantics.models import Company, Taxonomy


class JsonEntityResolver:
    """{"companies": [{"ticker", "name", "country", "aliases": [...]}]}"""

    def __init__(self, companies: Sequence[Company]) -> None:
        self._companies = tuple(companies)
        self._aliases = {a.lower(): c.ticker for c in companies
                         for a in (*c.aliases, *c.exact_case_aliases)}  # fmt: skip
        self._names = [a for c in companies for a in c.aliases]
        self._exact = [a for c in companies for a in c.exact_case_aliases]

    @classmethod
    def from_file(cls, path: Path) -> JsonEntityResolver:
        rows = json.loads(path.read_text())["companies"]
        return cls([Company.model_validate(r) for r in rows])

    @classmethod
    def from_files(cls, entities: Path, universe: Path) -> JsonEntityResolver:
        """The index members in `universe` (names as listed), with the hand-written entries in
        `entities` taking precedence; an entry outside the indexes counts only with a `why`."""
        raw = json.loads(entities.read_text())
        curated = [Company.model_validate(r) for r in raw["companies"]]
        listed = json.loads(universe.read_text())["companies"]
        members = {r["ticker"] for r in listed}
        companies = [c for c in curated if c.ticker in members or c.why]
        return cls(merge(companies, listed, raw.get("ambiguous_names", ())))

    def resolve(self, name: str) -> str | None:
        return self._aliases.get(name.lower())

    def known_names(self) -> Sequence[str]:
        return list(self._names)

    def exact_case_names(self) -> Sequence[str]:
        return list(self._exact)

    def companies(self) -> Sequence[Company]:
        return self._companies


# Legal forms and share classes that the news leaves out ("Alphabet Inc. (Class A)" -> "Alphabet").
_FORM = re.compile(
    r"(\s*\(.*?\)|,?\s+(Inc\.?|Incorporated|Corporation|Corp\.?|Company|Co\.?|Limited|"
    r"Ltd\.?|plc|PLC|Group|Holdings?|N\.V\.|S\.A\.|SE|& Co\.?))+$"
)


def merge(curated: Sequence[Company], listed: Iterable[dict[str, str]],
          ambiguous: Iterable[str]) -> list[Company]:  # fmt: skip
    """Curated companies first, then each index member not already there, with its names as
    listed and without the legal form. Generated names match only as written (they are proper
    nouns) and skip `ambiguous` ones (also ordinary words or other things: "ASX", "Seek").
    A name two companies share stays with the first (e.g. one listed in both markets)."""
    skip = {a.lower() for a in ambiguous}
    out = list(curated)
    taken = {a.lower() for c in curated for a in (*c.aliases, *c.exact_case_aliases)}
    tickers = {c.ticker for c in curated}
    for row in listed:
        if row["ticker"] in tickers:
            continue
        full = re.sub(r"^The\s+", "", row["name"]).strip()
        if _FORM.sub("", full).strip().lower() in taken:
            continue  # the same company already (another share class, or both markets)
        names = [n for n in dict.fromkeys((_FORM.sub("", full).strip(), full))
                 if len(n) >= 3 and n.lower() not in skip and n.lower() not in taken]  # fmt: skip
        if not names:
            continue  # no name we can match safely
        taken |= {n.lower() for n in names}
        tickers.add(row["ticker"])
        out.append(Company(ticker=row["ticker"], name=_FORM.sub("", full).strip() or full,
                           country=row["country"], sector=row.get("sector", ""), aliases=(),
                           exact_case_aliases=tuple(names)))  # fmt: skip
    return out


def load_taxonomy(path: Path) -> Taxonomy:
    raw = {k: v for k, v in json.loads(path.read_text()).items() if not k.startswith("_")}
    return Taxonomy.model_validate(raw)
