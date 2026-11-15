from datetime import UTC, datetime
from pathlib import Path

import pytest

from newsimpact.semantics.adapters.json_file import load_taxonomy
from newsimpact.semantics.adapters.lexicon import (
    AttributionStep,
    LexiconSentiment,
    SentenceExtractor,
    TaxonomyClassifier,
    WordListSignal,
)
from newsimpact.semantics.models import Attribution, Claim
from newsimpact.sources.models import Article

NOW = datetime(2026, 3, 10, tzinfo=UTC)
TAXONOMY = load_taxonomy(Path(__file__).resolve().parents[2] / "data/reference/taxonomy.json")
CLASSIFY = TaxonomyClassifier(TAXONOMY)


def _article(body: str) -> Article:
    return Article(article_id="a1", source_id="s1", url="u", title="t", body=body,
                   published_at=NOW, ingested_at=NOW, content_hash="h")  # fmt: skip


def test_extractor_keeps_sentences_naming_known_entities_in_text_order() -> None:
    extractor = SentenceExtractor(["Acme Semiconductors", "Acme", "Helix Cloud"])
    claims = extractor.extract(_article("Helix Cloud may buy Acme Semiconductors. Rain today."))
    assert len(claims) == 1
    assert [e.name for e in claims[0].entities] == ["Helix Cloud", "Acme Semiconductors"]


def test_classifier_sets_speculation_event_type_and_aspect() -> None:
    claim = CLASSIFY.apply(Claim(claim_id="c", article_id="a",
                                 text="Acme beat revenue guidance on record demand."))  # fmt: skip
    assert claim.event_type == "earnings_positive"
    assert claim.aspect == "revenue_demand"
    assert not claim.is_speculative


@pytest.mark.parametrize(
    ("sentence", "expected"),
    [
        ("the ceo published an open letter apologising to customers.", "leadership_apology"),
        ("the chief executive will step down at month end.", "leadership_departure"),
        ("the company named a new chief executive.", "leadership_appointment"),
        ("a recall after a safety investigation.", "product_recall"),
        ("a regulator opened an investigation.", "regulatory_action"),
        ("it is reportedly considering an acquisition.", "m_and_a_rumor"),
        ("it agreed an acquisition of the rival.", "m_and_a_announced"),
        ("the weather was fine.", "other"),
    ],
)
def test_event_types_come_from_the_taxonomy(sentence: str, expected: str) -> None:
    assert CLASSIFY.event_type(sentence, speculative=CLASSIFY.is_speculative(sentence)) == expected


def test_sentiment_and_word_list_signal() -> None:
    claim = Claim(claim_id="c", article_id="a", text="Shares plunged amid uncertainty and fear.")
    claim = WordListSignal(TAXONOMY, "uncertainty").apply(LexiconSentiment(TAXONOMY).apply(claim))
    assert claim.sentiment < 0
    assert claim.signals["uncertainty"] == pytest.approx(2 / 3, abs=1e-3)


def test_versions_name_the_taxonomy_for_reproducibility() -> None:
    assert TAXONOMY.version in CLASSIFY.version


@pytest.mark.parametrize(
    ("sentence", "kind", "cited"),
    [
        ("Globex will cut jobs, Reuters reported.", "cites_outlet", ("reuters",)),
        (
            "According to The Wall Street Journal, Initech may sell a unit.",
            "cites_outlet",
            ("wsj",),
        ),
        ("Globex said in a statement that the CEO resigned.", "company_statement", ()),
        ("Initech disclosed the change in a filing with the SEC.", "filing", ()),
        ("Helix is in talks, people familiar with the matter said.", "anonymous", ()),
        ("Globex Motors recalled 40,000 cars.", "own_reporting", ()),
    ],
)
def test_attribution(sentence: str, kind: str, cited: tuple[str, ...]) -> None:
    a = AttributionStep(TAXONOMY).attribute(sentence)
    assert (a.kind, a.cited_outlets) == (kind, cited)


def test_background_history_is_not_a_new_event() -> None:
    text = "Orbit Auto has issued several recalls in the past."
    claim = CLASSIFY.apply(Claim(claim_id="c", article_id="a", text=text))
    assert claim.event_type == "other" and claim.signals["background"] == 1.0


def test_copy_origin_wins_over_own_reporting() -> None:
    assert Attribution(copy_of_source="wire").origin("paper") == "wire"
    cited = Attribution(kind="cites_outlet", cited_outlets=("ft",))
    assert cited.origin("paper") == "outlet:ft"
    assert Attribution().origin("paper") == "paper"
