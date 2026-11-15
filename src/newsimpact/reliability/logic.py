"""Reliability math - pure functions, no I/O (ADR 0007).

Source level - Beta-Binomial: prior Beta(a0, b0) by source type, plus
confirmed claims (a) and retracted/contradicted claims (b). Posterior mean =
score; interval width = how sure we are. Kept per (source, topic).

Claim level - noisy-OR over the source and *independent* corroborating
sources, times a penalty for speculative language.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from newsimpact.sources.models import SourceType

MODEL_VERSION = "reliability-beta-v0.2"

# Starting estimate per source type: the chance a report holds up before any
# track record exists. The order follows how content is checked before
# publication: filings carry legal liability; agencies and newspapers have
# editors and correction policies; press releases are accurate about the
# company's own actions but selective; aggregators mix original reporting with
# syndicated opinion; blogs and social posts are unchecked.
PRIOR_MEANS: dict[SourceType, float] = {
    SourceType.REGULATORY_FILING: 0.95,
    SourceType.WIRE: 0.80,
    SourceType.MAJOR_OUTLET: 0.75,
    SourceType.COMPANY_PRESS_RELEASE: 0.67,
    SourceType.AGGREGATOR: 0.67,
    SourceType.BLOG: 0.50,
    SourceType.SOCIAL: 0.33,
    SourceType.UNKNOWN: 0.50,
}
# Every type starts with the weight of 10 reports, so the track record moves
# all sources at the same pace: after 10 judged reports, the record and the
# starting estimate count equally.
PRIOR_STRENGTH = 10.0
PRIORS: dict[SourceType, tuple[float, float]] = {
    t: (m * PRIOR_STRENGTH, (1 - m) * PRIOR_STRENGTH) for t, m in PRIOR_MEANS.items()
}

SPECULATIVE_PENALTY = 0.7


def beta_posterior(
    prior: tuple[float, float], supported: float, refuted: float, z: float = 1.96
) -> tuple[float, float, float]:
    """(mean, ci_low, ci_high); normal approximation to the Beta interval."""
    a = prior[0] + supported
    b = prior[1] + refuted
    mean = a / (a + b)
    sd = math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)))
    return mean, max(0.0, mean - z * sd), min(1.0, mean + z * sd)


def claim_reliability(
    source_reliability: float,
    corroborating_reliabilities: Sequence[float] = (),
    *,
    is_speculative: bool = False,
) -> float:
    p_all_wrong = 1.0 - source_reliability
    for r in corroborating_reliabilities:
        p_all_wrong *= 1.0 - r
    p = 1.0 - p_all_wrong
    if is_speculative:
        p *= SPECULATIVE_PENALTY
    return round(min(max(p, 0.0), 1.0), 6)
