"""Sanity-check the sample data fixtures."""

import pandas as pd


def test_sample_factor_ic_loads(sample_factor_ic: "pd.Series[float]") -> None:
    assert len(sample_factor_ic) == 252
    assert sample_factor_ic.dtype.kind == "f"
    assert isinstance(sample_factor_ic.index, pd.DatetimeIndex)


def test_sample_market_prices_loads(sample_market_prices: "pd.Series[float]") -> None:
    assert len(sample_market_prices) == 252
    assert (sample_market_prices > 0).all()


def test_sample_long_short_returns_loads(
    sample_long_short_returns: "pd.Series[float]",
) -> None:
    assert len(sample_long_short_returns) == 252
    assert sample_long_short_returns.abs().mean() < 0.05  # daily returns, not percent


def test_sample_turnover_loads(sample_turnover: "pd.Series[float]") -> None:
    assert len(sample_turnover) == 252
    assert ((sample_turnover >= 0) & (sample_turnover <= 1)).all()
