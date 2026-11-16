from pathlib import Path

from newsimpact.llm.models import BudgetExceededError, LlmRequest, LlmResult
from newsimpact.semantics.adapters.json_file import load_taxonomy
from newsimpact.semantics.adapters.llm_classifier import LlmClassifierStep
from newsimpact.semantics.models import Attribution, Claim, EntityMention

TAXONOMY = load_taxonomy(Path(__file__).resolve().parents[2] / "data/reference/taxonomy.json")


class FakeModel:
    name = "fake:model"

    def __init__(self, answer: dict[str, object] | None = None, fail: bool = False) -> None:
        self.answer = answer
        self.fail = fail
        self.requests: list[LlmRequest] = []

    def complete_json(self, request: LlmRequest) -> LlmResult | None:
        self.requests.append(request)
        if self.fail:
            raise BudgetExceededError("monthly LLM budget would be exceeded")
        return LlmResult(data=self.answer or {}, model="m", cost_usd=0.0, cached=False)


ANSWER = {"event_type": "leadership_departure", "is_background": False, "is_speculative": False,
          "aspect": "leadership_governance", "sentiment": -0.4,
          "attribution_kind": "cites_outlet",
          "cited_outlets": ["reuters", "not-an-outlet"]}  # fmt: skip


def _claim(event_type: str = "other", kind: str = "own_reporting") -> Claim:
    return Claim(
        claim_id="c",
        article_id="a",
        text="Acme's CEO is leaving, Reuters reported.",
        event_type=event_type,
        attribution=Attribution(kind=kind),
    )  # type: ignore[arg-type]


def test_only_candidates_go_to_the_model_and_answers_stay_inside_the_taxonomy() -> None:
    model = FakeModel(ANSWER)
    step = LlmClassifierStep(model, TAXONOMY)
    assert step.apply(_claim()) == _claim()  # baseline saw nothing: no call, no cost
    out = step.apply(_claim(kind="cites_outlet"))
    assert len(model.requests) == 1
    assert out.event_type == "leadership_departure"
    assert out.attribution.cited_outlets == ("reuters",)  # unknown outlet dropped
    assert out.signals["llm"] == 1.0
    enum = model.requests[0].schema_["properties"]["event_type"]["enum"]  # type: ignore[index]
    assert "leadership_departure" in enum and "other" in enum
    assert TAXONOMY.version in step.version


def test_budget_or_outage_keeps_the_baseline_result() -> None:
    claim = _claim(event_type="leadership_departure")
    out = LlmClassifierStep(FakeModel(fail=True), TAXONOMY).apply(claim)
    assert out.event_type == "leadership_departure" and out.signals["llm"] == 0.0


def test_background_answer_clears_the_event() -> None:
    model = FakeModel({**ANSWER, "is_background": True})
    out = LlmClassifierStep(model, TAXONOMY, scope="all").apply(_claim())
    assert out.event_type == "other" and out.signals["background"] == 1.0


def _two_companies() -> Claim:
    return Claim(
        claim_id="c",
        article_id="a",
        text="Cerebras beat estimates, helped by a new Microsoft and Nvidia deal.",
        entities=(EntityMention(name="Microsoft", entity_type="company", ticker="MSFT"),
                  EntityMention(name="Nvidia", entity_type="company", ticker="NVDA")),
        event_type="earnings_positive",
    )  # fmt: skip


def test_the_model_picks_the_subject_from_the_sentences_companies() -> None:
    model = FakeModel({**ANSWER, "event_type": "earnings_positive", "subject": "Nvidia"})
    out = LlmClassifierStep(model, TAXONOMY).apply(_two_companies())
    enum = model.requests[0].schema_["properties"]["subject"]["enum"]  # type: ignore[index]
    assert enum == ["Microsoft", "Nvidia", "none"]
    assert out.entities[0].ticker == "NVDA"  # storylines attach the event to the subject
    assert out.event_type == "earnings_positive"


def test_an_event_of_another_company_is_not_ours() -> None:
    model = FakeModel({**ANSWER, "event_type": "earnings_positive", "subject": "none"})
    out = LlmClassifierStep(model, TAXONOMY).apply(_two_companies())
    assert out.event_type == "other" and out.signals["off_subject"] == 1.0
    assert out.signals["background"] == 0.0
