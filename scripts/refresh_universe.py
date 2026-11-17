"""Refresh data/reference/universe.json: every company in the S&P 500 and the S&P/ASX 200.

    uv run python scripts/refresh_universe.py        (quarterly, after the index reviews)

The universe is the set of companies NewsImpact can recognise in the news. Which of them it
follows at any time is decided from the live news (methodology.json "following"). Index
members are used because each has a benchmark to measure against (S&P 500 or ASX 200) and
daily prices from our market data vendor.

Source: the constituent tables on Wikipedia ("List of S&P 500 companies" and "S&P/ASX 200"),
text under CC BY-SA 4.0, credited in the file. S&P Dow Jones Indices publishes the official
lists for licensed users only.
"""

from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parents[1] / "data" / "reference" / "universe.json"
API = "https://en.wikipedia.org/w/api.php"
# Wikipedia asks automated clients to say who they are (its User-Agent policy).
USER_AGENT = "NewsImpact-universe-refresh/1.0 (https://github.com/Inspiring-Ming/NewsImpact)"
PAGES = {
    "S&P 500": ("List of S&P 500 companies", "Symbol", "Security", "GICS Sector", "US", ""),
    "S&P/ASX 200": ("S&P/ASX 200", "Code", "Company", "Sector", "AU", ".AX"),
}
# Wikipedia's sector names that differ from GICS as written in entities.json.
SECTOR = {
    "Health care": "Health Care", "Healthcare": "Health Care",
    "Communication services": "Communication Services",
    "Consumer discretionary": "Consumer Discretionary", "Consumer staples": "Consumer Staples",
    "Information technology": "Information Technology", "Real estate": "Real Estate",
}  # fmt: skip


def _cells(row: str, tag: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
            for c in re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", row, re.S)]  # fmt: skip


def _table(page: str, code: str, name: str, sector: str) -> list[tuple[str, str, str]]:
    r = httpx.get(API, params={"action": "parse", "page": page, "prop": "text", "format": "json",
                               "formatversion": "2"},
                  headers={"User-Agent": USER_AGENT}, timeout=30)  # fmt: skip
    r.raise_for_status()
    for table in re.findall(r"<table.*?</table>", r.json()["parse"]["text"], re.S):
        rows = re.findall(r"<tr.*?</tr>", table, re.S)
        head = _cells(rows[0], "th") if rows else []
        if {code, name, sector} <= set(head):
            i, j, k = head.index(code), head.index(name), head.index(sector)
            out = [(c[i], c[j], SECTOR.get(c[k], c[k])) for c in (_cells(r, "td") for r in rows[1:])
                   if len(c) > max(i, j, k)]  # fmt: skip
            if len(out) > 100:
                return out
    raise ValueError(f"no constituent table found on {page!r}")


def main() -> None:
    companies = []
    for index, (page, code, name, sector, country, suffix) in PAGES.items():
        for symbol, company, gics in _table(page, code, name, sector):
            ticker = symbol.replace(".", "-") + suffix  # BRK.B -> BRK-B (EODHD style)
            companies.append({"ticker": ticker, "name": company, "country": country,
                              "sector": gics, "index": index})  # fmt: skip
    doc = {
        "_note": "Every company NewsImpact can recognise: the S&P 500 and the S&P/ASX 200 (index "
                 "members have a benchmark and daily prices). Which are followed is decided from "
                 "the live news (methodology.json 'following'); entities.json adds how the news "
                 "writes some names. Built by scripts/refresh_universe.py from Wikipedia's "
                 "constituent lists (CC BY-SA 4.0); refresh each quarter after the index reviews.",
        "refreshed": date.today().isoformat(),
        "source": {"S&P 500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                   "S&P/ASX 200": "https://en.wikipedia.org/wiki/S%26P/ASX_200",
                   "licence": "CC BY-SA 4.0"},
        "companies": companies,
    }  # fmt: skip
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(companies)} companies to {OUT}")


if __name__ == "__main__":
    main()
