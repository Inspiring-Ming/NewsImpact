"""What the validation module needs. The market and storylines modules provide
MarketEvidence and Playbooks in-process (wired in app/wiring.py); over a network
they would be API clients."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from newsimpact.market.models import ChannelObservation
from newsimpact.storylines.models import Playbook
from newsimpact.validation.models import Assessment


class MarketEvidence(Protocol):
    def observe(self, ticker: str, channel: str, at: datetime) -> ChannelObservation | None:
        """None = no data for this channel; raises WindowNotComplete when it is too early."""
        ...

    def observe_span(self, ticker: str, first: datetime, last: datetime) -> ChannelObservation:
        """One price reaction from the first to the last of several close stages."""
        ...


class Playbooks(Protocol):
    def playbooks(self) -> Sequence[Playbook]: ...


class AssessmentStore(Protocol):
    """Every assessment ever made (history shows how evidence matured)."""

    def add(self, assessment: Assessment) -> None: ...
    def latest(self, storyline_id: str) -> Assessment | None: ...
    def latest_all(self) -> Sequence[Assessment]: ...
