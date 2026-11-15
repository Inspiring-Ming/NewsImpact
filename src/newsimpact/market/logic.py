"""Market reaction measures - pure functions, no I/O.

Price (MacKinlay, 1997 market model):
  R_stock = alpha + beta * R_market + e            (estimation window)
  AR_t    = R_stock_t - (alpha + beta * R_market_t) (event window)
  CAR     = sum(AR_t);   t = CAR / (sigma_e * sqrt(L))
Volume:      mean log volume in the event window vs. the estimation window (z).
Volatility:  sum(AR_t^2) / sigma_e^2 ~ chi2(L) under "nothing happened";
             reported as the ratio of event to normal volatility, with a
             normal approximation z = (chi2 - L) / sqrt(2L).
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from datetime import datetime

from newsimpact.market.models import EventStudyResult

MODEL_VERSION = "market-measures-v0.3"
MIN_ESTIMATION_POINTS = 30


def market_model_event_study(
    ticker: str,
    event_time: datetime,
    est_stock: Sequence[float],
    est_market: Sequence[float],
    evt_stock: Sequence[float],
    evt_market: Sequence[float],
) -> EventStudyResult:
    if len(est_stock) != len(est_market) or len(evt_stock) != len(evt_market):
        raise ValueError("stock and market series must be aligned")
    if len(est_stock) < MIN_ESTIMATION_POINTS:
        raise ValueError(f"need >= {MIN_ESTIMATION_POINTS} estimation observations")
    if not evt_stock:
        raise ValueError("event window is empty")

    beta, alpha = statistics.linear_regression(est_market, est_stock)
    residuals = [s - (alpha + beta * m) for s, m in zip(est_stock, est_market, strict=True)]
    sigma = statistics.stdev(residuals)
    ars = tuple(s - (alpha + beta * m) for s, m in zip(evt_stock, evt_market, strict=True))
    car = sum(ars)

    return EventStudyResult(
        ticker=ticker,
        event_time=event_time,
        estimation_alpha=alpha,
        estimation_beta=beta,
        residual_sd=sigma,
        abnormal_returns=ars,
        cumulative_abnormal_return=car,
        t_stat=car / (sigma * math.sqrt(len(ars))) if sigma > 0 else None,
        model_version=MODEL_VERSION,
    )


def abnormal_volume(
    est_volumes: Sequence[float], evt_volumes: Sequence[float]
) -> tuple[float, float]:
    """(log volume ratio, z). Positive = more trading than normal."""
    if len(est_volumes) < MIN_ESTIMATION_POINTS or not evt_volumes:
        raise ValueError("not enough volume history")
    est = [math.log(v) for v in est_volumes if v > 0]
    evt = [math.log(v) for v in evt_volumes if v > 0]
    mean_est = statistics.fmean(est)
    diff = statistics.fmean(evt) - mean_est
    sd = statistics.stdev(est)
    return diff, (diff / (sd / math.sqrt(len(evt))) if sd > 0 else 0.0)


def volatility_ratio(abnormal_returns: Sequence[float], residual_sd: float) -> tuple[float, float]:
    """(event volatility / normal volatility, z). Above 1 = more volatile than normal."""
    n = len(abnormal_returns)
    if n == 0 or residual_sd <= 0:
        raise ValueError("need abnormal returns and a positive residual sd")
    chi2 = sum(a * a for a in abnormal_returns) / residual_sd**2
    return math.sqrt(chi2 / n), (chi2 - n) / math.sqrt(2 * n)
