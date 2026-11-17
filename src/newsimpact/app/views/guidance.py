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

import math
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from typing import Literal

from pydantic import Field

from newsimpact.shared.events import Model
from newsimpact.storylines.models import Expectation

Priority = Literal["act", "check", "background"]


class Check(Model):
    text: str
    url: str | None = Field(default=None, description="where to check it, if anywhere")


# How often each expectation would be met by chance alone. "Unusual" = larger than on 19 of
# 20 normal trading days, so a random day is unusual 5% of the time; a direction is a coin flip.
CHANCE = {"up": 0.5, "down": 0.5, "uncertain": 0.05, "flat": 0.95}


class GroupRecord(Model):
    """How events of one kind and case moved the stock, against what research expects."""

    label: str = Field(description="the case, e.g. 'company is the buyer'")
    expected: str = Field(description="up | down | flat | uncertain")
    finding: str
    source: str
    n: int = Field(description="events with a measured stock move")
    average: float | None
    met: int = Field(description="events that moved as research expects")
    unusual: int = Field(description="moves larger than on 19 of 20 normal days")
    chance: float = Field(description="share that would match by chance alone")
    verdict: Literal["too_few", "supports", "no_pattern", "against"]


def met(expected: str, move: float, unusual: bool) -> bool:
    """up / down: the stock moved that way (any size); uncertain: an unusual move either way;
    flat: no unusual move."""
    if expected == "up":
        return move > 0
    if expected == "down":
        return move < 0
    return unusual if expected == "uncertain" else not unusual


def group_record(exp: Expectation, moves: Sequence[tuple[float, bool]], *, min_events: int,
                 z_needed: float) -> GroupRecord:  # fmt: skip
    """moves = (stock move, unusual) per measured event. The verdict compares the share that
    met the expectation with chance (binomial z-test), and waits for enough events."""
    n, chance = len(moves), CHANCE[exp.expected]
    hits = sum(met(exp.expected, m, u) for m, u in moves)
    verdict: Literal["too_few", "supports", "no_pattern", "against"] = "too_few"
    if n >= min_events:
        z = (hits - n * chance) / math.sqrt(n * chance * (1 - chance))
        verdict = "supports" if z >= z_needed else "against" if z <= -z_needed else "no_pattern"
    return GroupRecord(
        label=exp.label, expected=exp.expected, finding=exp.finding, source=exp.source, n=n,
        average=sum(m for m, _ in moves) / n if n else None, met=hits,
        unusual=sum(u for _, u in moves), chance=chance, verdict=verdict,
    )  # fmt: skip


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
        within = f"; reports within {window_days} days join this event" if window_days else ""
        out.append(Check(text=f"Watch for a possible next step: {next_update}{within}."))
    out.append(Check(text=f"Compare other {sector} companies: are they moving too?"))
    return out
