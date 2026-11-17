"""ClaimStep that asks a language model to classify a claim - within the taxonomy.

Design for reliability and cost:
  * the model may only answer with labels from taxonomy.json (JSON schema enums),
    so its output plugs into playbooks exactly like the word-list baseline
  * scope "candidates" (default): only claims where the baseline saw something
    (an event, attribution, speculation or background) go to the model; the
    rest stay free. Scope "all" sends every claim.
  * if the model is unavailable, over budget or answers nothing usable, the
    claim keeps its baseline labels and signals["llm"] = 0
  * the model names the company the event happens to (the subject). A sentence
    about another company that only mentions ours ("Cerebras beat estimates,
    helped by a Microsoft deal") is not our company's event: event "other"
  * the step's version names provider, model and taxonomy (reproducibility)
"""

from __future__ import annotations

import logging
from typing import Any, Literal, get_args

from newsimpact.llm.models import BudgetExceededError, LlmRequest
from newsimpact.semantics.models import (
    OTHER,
    Attribution,
    AttributionKind,
    Claim,
    EntityMention,
    Taxonomy,
)
from newsimpact.semantics.ports import TextModel

log = logging.getLogger(__name__)

KINDS: dict[str, AttributionKind] = {k: k for k in get_args(AttributionKind)}
NO_SUBJECT = "none"  # the event happens to a company we do not follow, or there is no event


class LlmClassifierStep:
    def __init__(
        self,
        model: TextModel,
        taxonomy: Taxonomy,
        scope: Literal["candidates", "all"] = "candidates",
    ) -> None:
        self._model = model
        self._t = taxonomy
        self._scope = scope
        self.version = f"llm-classifier-v2/{model.name}/{taxonomy.version}/{scope}"
        self._system = self._build_system()
        self._schema = self._build_schema()

    def apply(self, claim: Claim) -> Claim:
        if self._scope == "candidates" and not _is_candidate(claim):
            return claim
        names = [e.name for e in claim.entities]
        prompt = f"Companies mentioned: {', '.join(names)}\nSentence: {claim.text}"
        request = LlmRequest(purpose="semantics.classify", system=self._system, prompt=prompt,
                             schema=self._with_subject(names))  # fmt: skip
        try:
            result = self._model.complete_json(request)
        except BudgetExceededError as exc:
            log.info("LLM skipped: %s", exc)
            result = None
        except Exception:  # provider down: never block the pipeline
            log.exception("LLM call failed")
            result = None
        if result is None:
            return claim.model_copy(update={"signals": {**claim.signals, "llm": 0.0}})
        return self._merge(claim, result.data)

    # ------------------------------------------------------------ helpers
    def _merge(self, claim: Claim, d: dict[str, object]) -> Claim:
        subject = d.get("subject")
        off_subject = subject == NO_SUBJECT and bool(claim.entities)
        background = bool(d.get("is_background"))
        kind = KINDS.get(str(d.get("attribution_kind")), "own_reporting")
        raw_cited = d.get("cited_outlets")
        cited = tuple(
            str(o)
            for o in (raw_cited if isinstance(raw_cited, list) else [])
            if str(o) in self._t.attribution.outlets
        )
        sentiment = d.get("sentiment")
        return claim.model_copy(update={
            "event_type": (OTHER if background or off_subject
                           else str(d.get("event_type", claim.event_type))),
            "aspect": str(d.get("aspect", claim.aspect)),
            "is_speculative": bool(d.get("is_speculative", claim.is_speculative)),
            "sentiment": (max(-1.0, min(1.0, float(sentiment)))
                          if isinstance(sentiment, int | float) else claim.sentiment),
            "attribution": Attribution(kind=kind,
                                       cited_outlets=cited if kind == "cites_outlet" else ()),
            "entities": _subject_first(claim, subject),
            "signals": {**claim.signals, "llm": 1.0, "background": 1.0 if background else 0.0,
                        "off_subject": 1.0 if off_subject else 0.0},
        })  # fmt: skip

    def _build_system(self) -> str:
        events = "\n".join(f"- {e.name}: {e.description}" for e in self._t.event_types)
        aspects = ", ".join(self._t.aspects)
        outlets = ", ".join(self._t.attribution.outlets)
        return (
            "You classify single sentences from financial news about listed companies.\n"
            "Answer only with the JSON schema provided.\n\n"
            f"event_type - the real-world event the sentence REPORTS AS NEW:\n{events}\n"
            "- other: none of the above, or not about the named company. Also 'other' for: "
            "share-price moves or comparisons ('beat Nvidia', 'down 13% this year'), previews "
            "of results not yet out, forecasts, outlooks and recommendations, partnerships, "
            "customer contracts, product news and law-firm adverts inviting investors to join "
            "a class action. A deal means ownership changes hands: buying "
            "or selling a company, a business unit or a stake (or raising one) IS one; licensing, "
            "film, supply and customer deals are not. Reported deal talks are a rumour even "
            "when the company denies them.\n\n"
            "subject - the mentioned company the event happens to; in a deal the buyer, the "
            "seller and the target all count. 'none' if it happens to another company (ours "
            "is only a customer, partner or comparison) or there is no event.\n"
            "is_background - true if the sentence only recalls history or context "
            "(e.g. 'has issued several recalls in the past'); then use event_type 'other'.\n"
            "is_speculative - true for rumours, hedged or unconfirmed claims.\n"
            f"aspect - one of: {aspects}, other.\n"
            "sentiment - from -1 (very negative for the company) to 1 (very positive).\n"
            "attribution_kind - where the claim comes from: own_reporting, cites_outlet "
            "(another outlet is named as the source), company_statement, filing, anonymous "
            "(unnamed people familiar with the matter).\n"
            f"cited_outlets - ids of outlets named as the source, from: {outlets}."
        )

    def _with_subject(self, names: list[str]) -> dict[str, Any]:
        """The answer schema, plus the subject chosen from this sentence's companies."""
        if not names:
            return self._schema
        props = {
            **self._schema["properties"],
            "subject": {"type": "string", "enum": [*dict.fromkeys(names), NO_SUBJECT]},
        }
        return {
            **self._schema,
            "properties": props,
            "required": [*self._schema["required"], "subject"],
        }

    def _build_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "event_type": {"type": "string",
                               "enum": [e.name for e in self._t.event_types] + [OTHER]},
                "is_background": {"type": "boolean"},
                "is_speculative": {"type": "boolean"},
                "aspect": {"type": "string", "enum": [*self._t.aspects, OTHER]},
                "sentiment": {"type": "number"},
                "attribution_kind": {"type": "string", "enum": list(KINDS)},
                "cited_outlets": {"type": "array", "items": {
                    "type": "string", "enum": sorted(self._t.attribution.outlets)}},
            },
            "required": ["event_type", "is_background", "is_speculative", "aspect", "sentiment",
                         "attribution_kind", "cited_outlets"],
            "additionalProperties": False,
        }  # fmt: skip


def _subject_first(claim: Claim, subject: object) -> tuple[EntityMention, ...]:
    """Put the subject first: storylines attach the event to the first company."""
    return tuple(sorted(claim.entities, key=lambda e: e.name != subject))


def _is_candidate(claim: Claim) -> bool:
    return (
        claim.event_type != OTHER
        or claim.attribution.kind != "own_reporting"
        or claim.is_speculative
        or claim.signals.get("background", 0.0) > 0
    )
