"""A company's part in a deal, read from where its name stands (taxonomy.json "deal_*" cues).
The headlines are real ones from the live feed (Nov 2026)."""

from pathlib import Path

import pytest

from newsimpact.semantics.adapters.json_file import load_taxonomy
from newsimpact.semantics.logic import deal_role

TAXONOMY = load_taxonomy(Path(__file__).parents[2] / "data" / "reference" / "taxonomy.json")
CUES = {k: TAXONOMY.words(k) for k in TAXONOMY.word_lists if k.startswith("deal_")}


@pytest.mark.parametrize(("text", "names", "role"), [
    ("Johnson & Johnson to acquire Ollin Biosciences", ["Johnson & Johnson"], "buyer"),
    ("NextDC shares surged after Goodman Group and Digital Realty agreed to acquire a stake",
     ["Goodman"], "buyer"),
    ("ExxonMobil Holdings Corporation (NYSE:XOM) agreed to increase its Papua LNG interest "
     "from 28.7% to 34.1%", ["ExxonMobil"], "buyer"),
    ("JP Morgan sees limited upside in a renewed bid for Rightmove PLC by REA Group",
     ["REA Group"], "buyer"),
    ("Gold Fields has approached Northern Star Resources about a potential acquisition",
     ["Northern Star"], "target"),
    ("Australia's Suncorp shares drop after denying Tokio Marine takeover talks",
     ["Suncorp"], "target"),
    ("Blackstone REIT to Buy Amazon Data Centers in $5 Billion Deal", ["Amazon"], "seller"),
    ("Swiss Re Corporate Solutions to buy QBE credit and surety unit", ["QBE"], "seller"),
    ("Solis expands into Brazil lithium with Rio Tinto project acquisition", ["Rio Tinto"],
     "seller"),
    ("Boeing Is Handing 3 Businesses to Archer Aviation", ["Boeing"], "seller"),
    ("SpaceX's S&P 500 Bid Gets New Life as Musk Pitches Tesla Merger", ["Tesla"], None),
])  # fmt: skip
def test_the_role_comes_from_where_the_name_stands(text: str, names: list[str],
                                                   role: str | None) -> None:  # fmt: skip
    assert deal_role(text, names, CUES) == role


def test_index_members_get_safe_names() -> None:
    from newsimpact.semantics.adapters.json_file import merge
    from newsimpact.semantics.models import Company

    curated = [Company(ticker="AAPL", name="Apple", country="US", aliases=(),
                       exact_case_aliases=("Apple",))]  # fmt: skip
    listed = [{"ticker": "AAPL", "name": "Apple Inc.", "country": "US"},
              {"ticker": "GOOGL", "name": "Alphabet Inc. (Class A)", "country": "US"},
              {"ticker": "GOOG", "name": "Alphabet Inc. (Class C)", "country": "US"},
              {"ticker": "ASX.AX", "name": "ASX", "country": "AU"},
              {"ticker": "TGT", "name": "Target Corporation", "country": "US"}]  # fmt: skip
    out = {c.ticker: c for c in merge(curated, listed, ambiguous=("ASX", "Target"))}
    assert out["AAPL"] is curated[0]  # hand-written entries win
    assert out["GOOGL"].exact_case_aliases == ("Alphabet", "Alphabet Inc. (Class A)")
    assert "GOOG" not in out  # the same name stays with the first listing
    assert "ASX.AX" not in out  # only an ambiguous name: never matched
    assert out["TGT"].exact_case_aliases == ("Target Corporation",)  # not "Target" alone
