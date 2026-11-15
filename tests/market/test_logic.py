import random
from datetime import UTC, datetime

import pytest

from newsimpact.market.logic import abnormal_volume, market_model_event_study, volatility_ratio

T0 = datetime(2026, 3, 10, tzinfo=UTC)


def _series(n: int, seed: int) -> tuple[list[float], list[float]]:
    rng = random.Random(seed)
    market = [rng.gauss(0, 0.01) for _ in range(n)]
    stock = [0.0005 + 1.3 * m + rng.gauss(0, 0.005) for m in market]
    return stock, market


def test_recovers_beta_and_detects_shock() -> None:
    est_s, est_m = _series(120, 1)
    evt_s, evt_m = _series(3, 2)
    evt_s[1] += 0.05
    res = market_model_event_study("X", T0, est_s, est_m, evt_s, evt_m)
    assert res.estimation_beta == pytest.approx(1.3, abs=0.15)
    assert res.cumulative_abnormal_return == pytest.approx(0.05, abs=0.02)
    assert res.t_stat is not None and res.t_stat > 3


@pytest.mark.parametrize(
    ("est_len", "market_trim", "message"),
    [(10, 0, "estimation"), (60, 1, "aligned")],
)
def test_rejects_bad_input(est_len: int, market_trim: int, message: str) -> None:
    est_s, est_m = _series(est_len, 1)
    with pytest.raises(ValueError, match=message):
        market_model_event_study("X", T0, est_s, est_m[: est_len - market_trim], [0.0], [0.0])


def test_abnormal_volume_detects_heavy_trading() -> None:
    rng = random.Random(3)
    normal = [1e6 * (1 + rng.gauss(0, 0.1)) for _ in range(60)]
    ratio, z = abnormal_volume(normal, [3e6, 2.5e6])
    assert ratio > 0.8 and z > 3


def test_volatility_ratio_is_about_one_on_normal_days_and_high_after_shocks() -> None:
    calm, z_calm = volatility_ratio([0.01, -0.01, 0.01, -0.01], residual_sd=0.01)
    wild, z_wild = volatility_ratio([0.05, -0.04, 0.03, 0.0], residual_sd=0.01)
    assert calm == pytest.approx(1.0) and abs(z_calm) < 1
    assert wild > 2 and z_wild > 3
