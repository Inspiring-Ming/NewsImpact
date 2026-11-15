"""What the semantics module needs (implemented in adapters/).

Analysis is a chain: one ClaimExtractor finds the claims, then each
ClaimStep in turn adds what it knows (event type, sentiment, a new signal...).
To analyse something new, add one step; to change technique (word lists ->
LLM), swap the extractor or a step. Steps are chosen in app/wiring.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from newsimpact.llm.models import LlmRequest, LlmResult
from newsimpact.semantics.models import Claim
from newsimpact.sources.models import Article


class ClaimExtractor(Protocol):
    """Article -> claims with text and entity mentions (nothing classified yet)."""

    version: str

    def extract(self, article: Article) -> Sequence[Claim]: ...


class ClaimStep(Protocol):
    """Adds one kind of analysis to a claim and returns the updated claim."""

    version: str

    def apply(self, claim: Claim) -> Claim: ...


class EntityResolver(Protocol):
    """Entity linking: surface name -> ticker (later: LEI / FIGI too)."""

    def resolve(self, name: str) -> str | None: ...
    def known_names(self) -> Sequence[str]: ...


class TextModel(Protocol):
    """A language model behind cost controls (provided by the llm module's gateway)."""

    @property
    def name(self) -> str: ...

    def complete_json(self, request: LlmRequest) -> LlmResult | None:
        """Answer, or None if unusable. Raises llm.models.BudgetExceededError at a limit."""
        ...
