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

MODEL_VERSION = "reliability-beta-v0.1"

# (alpha, beta) prior pseudo-counts. Expert judgement until calibrated on
# resolved claims.
PRIORS: dict[SourceType, tuple[float, float]] = {
    SourceType.REGULATORY_FILING: (19.0, 1.0),
    SourceType.WIRE: (8.0, 2.0),
    SourceType.MAJOR_OUTLET: (6.0, 2.0),
    SourceType.COMPANY_PRESS_RELEASE: (6.0, 3.0),
    # Mixes original reporting with syndicated analysis and opinion pieces.
    SourceType.AGGREGATOR: (4.0, 2.0),
    SourceType.BLOG: (2.0, 2.0),
    SourceType.SOCIAL: (1.0, 2.0),
    SourceType.UNKNOWN: (1.0, 1.0),
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
