"""Tests for regime detection functions."""

import numpy as np
import pandas as pd
import pytest

from regime_lens.core.regimes import detect_trend_regime, detect_volatility_regime


def test_volatility_regime_returns_int8_series(
    sample_market_prices: "pd.Series[float]",
) -> None:
    regime = detect_volatility_regime(sample_market_prices, window=20)
    assert isinstance(regime, pd.Series)
    assert regime.dtype == np.int8
    assert set(regime.unique()).issubset({0, 1})


def test_volatility_regime_drops_warmup_nans(
    sample_market_prices: "pd.Series[float]",
) -> None:
    regime = detect_volatility_regime(sample_market_prices, window=20)
    # 20-day rolling std means first 20 entries are NaN
    assert len(regime) == len(sample_market_prices) - 20
    assert regime.index[0] == sample_market_prices.index[20]


def test_volatility_regime_splits_near_median(
    sample_market_prices: "pd.Series[float]",
) -> None:
    regime = detect_volatility_regime(sample_market_prices, window=20)
    # By construction (fixture has mid-year vol shift), roughly half should be high-vol
    high_vol_share = regime.mean()
    assert 0.3 < high_vol_share < 0.7


def test_volatility_regime_high_vol_half_dominated_by_label_1() -> None:
    """Synthetic: second half of the series is clearly more volatile → label 1."""
    rng = np.random.default_rng(0)
    n = 200
    idx = pd.bdate_range("2024-01-02", periods=n)
    low = rng.normal(0.0, 0.005, n // 2)
    high = rng.normal(0.0, 0.03, n // 2)
    prices = 100 * np.exp(np.cumsum(np.concatenate([low, high])))
    regime = detect_volatility_regime(pd.Series(prices, index=idx), window=20)
    # After warmup, second half should be mostly label 1
    second_half = regime.iloc[len(regime) // 2 :]
    assert second_half.mean() > 0.8


def test_volatility_regime_rejects_empty_series() -> None:
    with pytest.raises(ValueError, match="at least"):
        detect_volatility_regime(pd.Series([], dtype="float64"), window=20)


def test_trend_regime_returns_int8_series(
    sample_market_prices: "pd.Series[float]",
) -> None:
    regime = detect_trend_regime(sample_market_prices, window=60)
    assert regime.dtype == np.int8
    assert set(regime.unique()).issubset({0, 1})


def test_trend_regime_drops_warmup_nans(
    sample_market_prices: "pd.Series[float]",
) -> None:
    regime = detect_trend_regime(sample_market_prices, window=60)
    # 60-day MA means first 59 entries are NaN (pandas rolling default)
    assert len(regime) == len(sample_market_prices) - 59
    assert regime.index[0] == sample_market_prices.index[59]


def test_trend_regime_detects_uptrend() -> None:
    """Monotonically increasing prices → regime is 1 (above MA) almost everywhere."""
    idx = pd.bdate_range("2024-01-02", periods=200)
    prices = pd.Series(np.linspace(100, 200, 200), index=idx)
    regime = detect_trend_regime(prices, window=60)
    assert regime.mean() > 0.95


def test_trend_regime_detects_downtrend() -> None:
    idx = pd.bdate_range("2024-01-02", periods=200)
    prices = pd.Series(np.linspace(200, 100, 200), index=idx)
    regime = detect_trend_regime(prices, window=60)
    assert regime.mean() < 0.05


def test_trend_regime_rejects_short_series() -> None:
    with pytest.raises(ValueError, match="at least"):
        detect_trend_regime(pd.Series([1.0, 2.0, 3.0]), window=60)
