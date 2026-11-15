"""What a reader should look at first, and what to check next. Rules only, no AI.

Priority (ADR 0030), for professional investors following a list of stocks:
  act         confirmed news AND (an unusual stock move OR a new update in 24 hours):
              something real is moving now
  check       confirmed news otherwise, or unconfirmed news with an unusual move:
              worth a look, nothing urgent
  background  the rest (mostly single-source items with normal moves)

Checks tell the reader what to check, never what to buy, sell or hold: factual
information, not advice (ASIC RG 244; the same line US publishers keep).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timedelta
from typing import Literal

from pydantic import Field

from newsimpact.shared.events import Model
from newsimpact.storylines.models import Playbook

Priority = Literal["act", "check", "background"]


class Check(Model):
    text: str
    url: str | None = Field(default=None, description="where to check it, if anywhere")


class TypeRecord(Model):
    """How this kind of event has moved stocks across the events we measured."""

    expected: str | None = Field(description="up | down | uncertain: the usual share price move")
    n: int
    average: float | None
    as_expected: int


def priority(*, confirmed: bool, unusual: bool, last_update: datetime, now: datetime
             ) -> tuple[Priority, str]:  # fmt: skip
    fresh = now - last_update < timedelta(hours=24)
    if confirmed and unusual:
        return "act", "Confirmed news and an unusual stock move"
    if confirmed and fresh:
        return "act", "Confirmed news with a new update in the last 24 hours"
    if confirmed:
        return "check", "Confirmed news; the stock moved within its normal range"
    if unusual:
        return "check", "Unusual stock move, but the news is not yet confirmed"
    return "background", "One source so far and no unusual stock move"


def close_after(day: date, trading_days: int) -> date:
    """The close `trading_days` after `day`, counting weekdays (exchange holidays not known)."""
    d = day
    while d.weekday() >= 5:
        d += timedelta(days=1)
    for _ in range(trading_days):
        d += timedelta(days=1)
        while d.weekday() >= 5:
            d += timedelta(days=1)
    return d


def checks(*, url: str, confirmed: bool, unusual: bool, final_on: date | None, sector: str,
           next_update: str | None, window_days: int | None) -> list[Check]:  # fmt: skip
    """The few things worth checking now, most important first."""
    out = [Check(text="Read the original article.", url=url or None)]
    if not confirmed:
        out.append(Check(text="Look for confirmation: the company's own statement or a second "
                              "independent source."))  # fmt: skip
    if unusual:
        out.append(Check(text="Review your position size in this stock: it moved more than on "
                              "19 of 20 normal days."))  # fmt: skip
    if final_on is not None:
        out.append(Check(text=f"The stock reaction is measured after the close on "
                              f"{final_on:%a %-d %b}."))  # fmt: skip
    if next_update:
        within = f" (usually within {window_days} days)" if window_days else ""
        out.append(Check(text=f"Watch for the next usual update: {next_update}{within}."))
    out.append(Check(text=f"Compare other {sector} companies: are they moving too?"))
    return out


def type_record(playbook: Playbook | None, moves: Sequence[tuple[float, bool]]) -> TypeRecord:
    """moves = (stock move, unusual) for each measured event of this type."""
    expected = None
    if playbook:
        expected = next((d.expected_direction for s in playbook.stages for d in s.decisions
                         if d.market_channel == "price"), None)  # fmt: skip
    hits = sum(
        unusual if expected == "uncertain" else (m < 0 if expected == "down" else m > 0)
        for m, unusual in moves
    ) if expected else 0  # fmt: skip
    avg = sum(m for m, _ in moves) / len(moves) if moves else None
    return TypeRecord(expected=expected, n=len(moves), average=avg, as_expected=hits)
