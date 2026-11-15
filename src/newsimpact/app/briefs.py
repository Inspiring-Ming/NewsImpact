"""Three-line event briefs: what happened, what the market did, why it matters.

Written by the language model from facts we already hold (our numbers, the
source headlines, a cited research finding), during the monitor round, never
while a page loads. Checked before use: no buy / sell / hold wording, and every
number must appear in the facts. Anything that fails, and every event when no
model is configured, gets a brief written by rules from the same facts.
Facts are hashed: an unchanged event is never re-written (and the LLM gateway
caches identical requests, so a repeat costs nothing).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Literal, Protocol

from pydantic import Field

from newsimpact.llm.models import BudgetExceededError, LlmRequest
from newsimpact.llm.service import LlmGateway
from newsimpact.shared.events import Model
from newsimpact.shared.sqlite import Database

log = logging.getLogger(__name__)

# Advice words: we state facts and what to check, never what to do with the stock.
FORBIDDEN = re.compile(r"\b(buy|sell|hold|recommend\w*|should|must|price target|undervalued|"
                       r"overvalued|opportunit\w*)\b", re.IGNORECASE)  # fmt: skip
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")

SYSTEM = (
    "You write a three-line brief about one company news event for professional investors. "
    "Use ONLY the facts given. Line 1 'what_happened': what the news says and whether it is "
    "confirmed (if 'confirmed' is false, say it is not yet confirmed). Line 2 'market': what the "
    "stock did against its index, using the numbers exactly as given, or that it is not measured "
    "yet. Line 3 'why_it_matters': what usually follows this kind of event, from the research "
    "finding (name its authors and year) or the past record. Plain English, at most 30 words "
    "per line, no advice: never say buy, sell, hold, should, or recommend."
)
LINES = ("what_happened", "market", "why_it_matters")
SCHEMA = {
    "type": "object",
    "properties": {k: {"type": "string"} for k in LINES},
    "required": list(LINES),
    "additionalProperties": False,
}


class Brief(Model):
    bullets: tuple[str, ...]
    by: Literal["ai", "rules"]
    facts_key: str = Field(description="hash of the facts it was written from")


def facts_key(facts: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(facts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def rules_brief(facts: dict[str, object]) -> Brief:
    status = "Confirmed." if facts["confirmed"] else "Not yet confirmed: one source so far."
    what = f"{facts['latest_update']}: {facts['headline']} {status}"
    market = str(facts["market"])
    research = facts.get("research")
    why = (f"{research} ({facts['research_source']})" if research
           else f"Next usual update: {facts['next_update']}." if facts.get("next_update")
           else "No published finding for this kind of event yet.")  # fmt: skip
    return Brief(bullets=(what, market, why), by="rules", facts_key=facts_key(facts))


def _safe(text: str, facts: dict[str, object]) -> bool:
    """No advice words, and no number that is not in the facts."""
    known = set(NUMBER.findall(json.dumps(facts, default=str)))
    return not FORBIDDEN.search(text) and all(n in known for n in NUMBER.findall(text))


def ai_brief(llm: LlmGateway, facts: dict[str, object]) -> Brief | None:
    request = LlmRequest(purpose="briefs.event", system=SYSTEM, schema=SCHEMA,
                         prompt=json.dumps(facts, default=str), max_output_tokens=400)  # fmt: skip
    try:
        result = llm.complete_json(request)
    except BudgetExceededError as exc:
        log.info("brief not written: %s", exc)
        return None
    except Exception:  # provider down: the rules brief stands in
        log.exception("brief call failed")
        return None
    if result is None:
        return None
    lines = tuple(str(result.data.get(k, "")).strip() for k in LINES)
    if not all(lines) or not all(_safe(line, facts) for line in lines):
        log.warning("AI brief rejected by the checks; using the rules brief")
        return None
    return Brief(bullets=lines, by="ai", facts_key=facts_key(facts))


class BriefStore(Protocol):
    def get(self, event_id: str) -> Brief | None: ...
    def put(self, event_id: str, brief: Brief) -> None: ...


class InMemoryBriefs:
    def __init__(self) -> None:
        self._d: dict[str, Brief] = {}

    def get(self, event_id: str) -> Brief | None:
        return self._d.get(event_id)

    def put(self, event_id: str, brief: Brief) -> None:
        self._d[event_id] = brief


class SqliteBriefs:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("briefs")

    def get(self, event_id: str) -> Brief | None:
        doc = self._c.get(event_id)
        return Brief.model_validate_json(doc) if doc else None

    def put(self, event_id: str, brief: Brief) -> None:
        self._c.put(event_id, brief.model_dump_json())
