"""Validation rules - pure functions, no I/O. Thresholds come from ValidationPolicy
(data/reference/methodology.json), each with its reason.

Claim status (counted over independent ORIGINS, not outlets - copies and
re-reports of one scoop are one origin)
  confirmed      a filing / the company itself, or >= confirming_origins origins
  corroborated   >= corroborating_origins origins
  single_source  otherwise
Decision verdict (expected direction vs. what the market did)
  consistent       significant move in the expected direction ("uncertain" = any direction)
  inconsistent     significant move in the opposite direction
  not_significant  no move that stands out from normal days
  pending          the measurement window has not finished yet
  no_evidence      no data source for this channel
  not_measurable   a real-economy decision (board, customers) - no market metric
Confidence
  high    every stage corroborated and the market confirmed >= high_support
  medium  one of the two holds (or >= medium_support)
  low     otherwise
Calibration (across storylines)
  per stage x channel: BMP (Boehmer, Musumeci & Poulsen 1991) cross-sectional
  test of per-event statistics; per playbook: observed gaps between stages.
"""

from __future__ import annotations

import itertools
import math
import statistics
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta

from newsimpact.market.models import ChannelObservation
from newsimpact.sources.models import SourceType
from newsimpact.storylines.models import ExpectedDecision, Playbook, Report, Storyline
from newsimpact.validation.models import (
    Assessment,
    ClaimCheck,
    ClaimStatus,
    Confidence,
    DecisionCheck,
    Finding,
    StageChannelCalibration,
    StageCheck,
    ValidationPolicy,
    Verdict,
    WindowCalibration,
)

MODEL_VERSION = "validation-rules-v0.3"
AUTHORITATIVE_TYPES = frozenset({SourceType.REGULATORY_FILING, SourceType.COMPANY_PRESS_RELEASE})
AUTHORITATIVE_ATTRIBUTION = frozenset({"company_statement", "filing"})
MEASURED = frozenset({"consistent", "inconsistent", "not_significant"})


# ------------------------------------------------------------------ claims
def check_claim(reports: Sequence[Report], policy: ValidationPolicy) -> ClaimCheck:
    outlets = tuple(dict.fromkeys(r.source_id for r in reports))
    origins = tuple(dict.fromkeys(r.origin for r in reports))
    authoritative = any(
        r.source_type in AUTHORITATIVE_TYPES or r.attribution_kind in AUTHORITATIVE_ATTRIBUTION
        for r in reports
    )
    status: ClaimStatus
    if authoritative or len(origins) >= policy.confirming_origins:
        status = "confirmed"
    elif len(origins) >= policy.corroborating_origins:
        status = "corroborated"
    else:
        status = "single_source"
    return ClaimCheck(
        status=status,
        outlets=outlets,
        origins=origins,
        authoritative=authoritative,
        best_reliability=max((r.claim_reliability for r in reports), default=0.0),
    )


def trading_days_between(earlier: datetime, later: datetime) -> int:
    """Weekdays from one date to the next (holidays ignored: a conservative overlap test)."""
    start, end = earlier.date(), later.date()
    return sum((start + timedelta(days=i)).weekday() < 5 for i in range((end - start).days))


def overlapping(published: Sequence[datetime], policy: ValidationPolicy) -> list[bool]:
    """For each stage: is it within the overlap window of the stage before it?"""
    return [i > 0 and trading_days_between(published[i - 1], published[i])
            <= policy.overlap_trading_days for i in range(len(published))]  # fmt: skip


# --------------------------------------------------------------- decisions
def verdict(expected: str, obs: ChannelObservation | None) -> Verdict:
    if obs is None:
        return "no_evidence"
    if not obs.significant:
        return "not_significant"
    if expected == "uncertain" or obs.direction == expected:
        return "consistent"
    return "inconsistent"


def check_decision(
    decision: ExpectedDecision, obs: ChannelObservation | None, *, pending: bool = False
) -> DecisionCheck:
    channel = decision.market_channel.value if decision.market_channel else None
    result: Verdict
    if channel is None:
        result = "not_measurable"
    elif pending:
        result = "pending"
    else:
        result = verdict(decision.expected_direction, obs)
    return DecisionCheck(actor=decision.actor, decision=decision.decision, channel=channel,
                         expected=decision.expected_direction, verdict=result,
                         evidence=obs)  # fmt: skip


def market_support(stages: Sequence[StageCheck]) -> float | None:
    measured = [d.verdict for s in stages for d in s.decisions if d.verdict in MEASURED]
    if not measured:
        return None
    return round(measured.count("consistent") / len(measured), 4)


def confidence(
    stages: Sequence[StageCheck], support: float | None, policy: ValidationPolicy
) -> Confidence:
    claims_ok = all(s.claim.status != "single_source" for s in stages)
    market_ok = support is not None and support >= policy.high_support
    if claims_ok and market_ok:
        return "high"
    if claims_ok or market_ok or (support is not None and support >= policy.medium_support):
        return "medium"
    return "low"


# -------------------------------------------------------------- conclusion
def conclude(
    storyline: Storyline,
    playbook: Playbook,
    stages: Sequence[StageCheck],
    support: float | None,
    combined: ChannelObservation | None = None,
) -> tuple[str, tuple[str, ...]]:
    """One-paragraph conclusion + suggestions, in priority order."""
    backed = sum(s.claim.status != "single_source" for s in stages)
    measured = [d for s in stages for d in s.decisions if d.verdict in MEASURED]
    pending = [d for s in stages for d in s.decisions if d.verdict == "pending"]
    if support is None:
        market = "market reaction still being measured" if pending else "no market data connected"
    else:
        consistent = sum(d.verdict == "consistent" for d in measured)
        market = (f"the market confirmed {consistent} of {len(measured)} measured "
                  f"expectations ({support:.0%})")  # fmt: skip
    conclusion = (
        f"{storyline.theme} at {storyline.ticker} ({storyline.entity_name}): "
        f"{storyline.status.value} after {len(stages)} stage(s). "
        f"{backed} of {len(stages)} stage(s) backed by independent origins or an authoritative "
        f"source; {market}."
    )
    if combined is not None:
        conclusion += (f" Stages too close to separate, measured together: {combined.metric} = "
                       f"{combined.value:+.1%} (z={combined.statistic}).")  # fmt: skip

    tips: list[str] = []  # most important first; readers see the first few
    for s in stages:
        if s.claim.status == "single_source":
            repeats = len(s.claim.outlets) - 1
            echo = f" ({repeats} other outlet(s) only repeated it)" if repeats > 0 else ""
            tips.append(f"{_h(s.stage_name)} rests on a single source ({_h(s.claim.origins[0])})"
                        f"{echo}: wait for an independent outlet or a filing.")  # fmt: skip
        for d in s.decisions:
            if d.verdict == "inconsistent" and d.evidence is not None:
                moved = d.evidence.direction
                tips.append(f"{_h(s.stage_name)}: {_h(d.channel or '')} went {moved}, the "
                            "opposite of what usually happens - check whether the news "
                            "leaked earlier.")  # fmt: skip
        quiet = sorted({_h(d.channel or "") for d in s.decisions if d.verdict == "not_significant"})
        if quiet:
            tips.append(f"{_h(s.stage_name)}: no clear move in {', '.join(quiet).lower()} - "
                        "the market may have expected it.")  # fmt: skip
    close = [_h(s.stage_name) for s in stages if s.overlaps_previous]
    if close:
        tips.append(f"{', '.join(close)} came within days of the previous stage, so read "
                    "their market reaction together.")  # fmt: skip
    if pending:
        tips.append(f"{len(pending)} market check(s) need a few more trading days; they update "
                    "automatically.")  # fmt: skip
    if storyline.status.value != "resolved":
        upcoming = [_h(st.name) for st in playbook.stages[storyline.max_stage + 1 :]]
        if upcoming:
            tips.append(f"Next to watch for: {', '.join(upcoming).lower()} (we are searching "
                        "for it automatically).")  # fmt: skip
    missing = sorted({_h(d.channel or "") for s in stages for d in s.decisions
                      if d.verdict == "no_evidence"})  # fmt: skip
    if missing:
        tips.append(f"Not checked yet (no data source): {', '.join(missing).lower()}.")
    real_economy = [d for s in stages for d in s.decisions if d.verdict == "not_measurable"]
    if real_economy:
        tips.append(f"{len(real_economy)} expected decision(s) don't show in market data (e.g. "
                    f"{_h(real_economy[0].actor).lower()}: {real_economy[0].decision}); check "
                    "company filings and earnings calls.")  # fmt: skip
    return conclusion, tuple(tips)


# -------------------------------------------------------------- calibration
def calibrate_reactions(
    assessments: Sequence[Assessment], policy: ValidationPolicy
) -> list[StageChannelCalibration]:
    groups: dict[tuple[str, str, str, str], list[DecisionCheck]] = defaultdict(list)
    for a in assessments:
        for s in a.stages:
            for d in s.decisions:
                if d.channel is not None:
                    groups[(a.theme, s.stage_name, d.channel, d.expected)].append(d)
    out = []
    for (theme, stage, channel, expected), checks in sorted(groups.items()):
        measured = [d for d in checks if d.verdict in MEASURED and d.evidence is not None]
        stats = [d.evidence.statistic for d in measured
                 if d.evidence is not None and d.evidence.statistic is not None]  # fmt: skip
        mean, z = _bmp(stats)
        share = (sum(d.verdict == "consistent" for d in measured) / len(measured)
                 if measured else None)  # fmt: skip
        out.append(StageChannelCalibration(
            theme=theme, stage_name=stage, channel=channel, expected=expected,
            n_events=len(measured), mean_statistic=_round(mean), cross_sectional_z=_round(z),
            share_consistent=_round(share),
            finding=_finding(expected, mean, z, len(measured), policy),
        ))  # fmt: skip
    return out


def calibrate_windows(
    storylines: Sequence[Storyline], playbooks: Sequence[Playbook], policy: ValidationPolicy
) -> list[WindowCalibration]:
    gaps: dict[str, list[float]] = defaultdict(list)
    for story in storylines:
        events = sorted(story.events, key=lambda e: e.published_at)
        for earlier, later in itertools.pairwise(events):
            seconds = (later.published_at - earlier.published_at).total_seconds()
            gaps[story.theme].append(seconds / 86400)
    out = []
    for pb in playbooks:
        g = sorted(gaps.get(pb.theme, []))
        q = _quantile(g, policy.window_quantile) if g else None
        enough = len(g) >= policy.min_events_for_calibration
        out.append(WindowCalibration(
            theme=pb.theme, n_gaps=len(g),
            median_days=_round(statistics.median(g)) if g else None, quantile_days=_round(q),
            configured_days=pb.link_window_days,
            suggested_days=math.ceil(q * policy.window_margin) if enough and q else None,
        ))  # fmt: skip
    return out


def _bmp(stats: Sequence[float]) -> tuple[float | None, float | None]:
    if not stats:
        return None, None
    mean = statistics.fmean(stats)
    if len(stats) < 2:  # one event: no dispersion to test against
        return mean, None
    sd = statistics.stdev(stats)
    return mean, (mean / (sd / math.sqrt(len(stats))) if sd > 0 else None)


def _finding(
    expected: str, mean: float | None, z: float | None, n: int, policy: ValidationPolicy
) -> Finding:
    if n == 0 or mean is None:
        return "no_data"
    if n < policy.min_events_for_calibration or z is None:
        return "indicative"
    if abs(z) < policy.significance_z:
        return "not_significant"
    moved = "up" if mean > 0 else "down"
    return "supported" if expected in ("uncertain", moved) else "contradicted"


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    idx = (len(sorted_values) - 1) * q
    lo, hi = math.floor(idx), math.ceil(idx)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (idx - lo)


def _h(code: str) -> str:
    """'leader_departure' -> 'Leader departure' (readable text for people)."""
    text = code.replace("_", " ").strip()
    return text[:1].upper() + text[1:]


def _round(x: float | None) -> float | None:
    return None if x is None else round(x, 4)
