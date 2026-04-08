"""Pytest fixtures for loading sample CSV data."""

from pathlib import Path

import pandas as pd
import pytest

CASES_DIR = Path(__file__).parent / "cases"


def _load_series(filename: str, value_col: str) -> "pd.Series[float]":
    df = pd.read_csv(CASES_DIR / filename, parse_dates=["date"], index_col="date")
    series: pd.Series[float] = df[value_col]
    # Explicitly clear any inferred freq so downstream tests don't rely on it
    if isinstance(series.index, pd.DatetimeIndex):
        series.index.freq = None  # type: ignore[misc]  # pandas-stubs marks freq read-only but setter exists at runtime
    return series


@pytest.fixture
def sample_factor_ic() -> "pd.Series[float]":
    return _load_series("sample_factor_ic.csv", "ic")


@pytest.fixture
def sample_long_short_returns() -> "pd.Series[float]":
    return _load_series("sample_long_short_returns.csv", "ls_return")


@pytest.fixture
def sample_market_prices() -> "pd.Series[float]":
    return _load_series("sample_market_prices.csv", "close")


@pytest.fixture
def sample_turnover() -> "pd.Series[float]":
    return _load_series("sample_turnover.csv", "turnover")
