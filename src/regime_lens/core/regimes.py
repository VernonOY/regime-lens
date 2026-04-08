"""Regime detection functions.

Each detector takes a market price series and returns an int8 Series of 0/1
labels, aligned to the valid (non-warmup) portion of the input.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_TRADING_DAYS_PER_YEAR = 252


def detect_volatility_regime(market_prices: pd.Series, window: int = 20) -> pd.Series:
    """Label days as high-vol (1) or low-vol (0) relative to the sample median.

    High-vol = rolling realized volatility is strictly greater than the median
    of the entire rolling-vol series over the sample period. The median is
    computed in-sample over the full input, not rolling — see the project
    README for why this is intentional for ex-post factor diagnosis.

    Parameters
    ----------
    market_prices : pd.Series
        DatetimeIndex, float values, length > window.
    window : int
        Rolling window in trading days for realized volatility.

    Returns
    -------
    pd.Series
        int8 0/1 series, length = len(market_prices) - window, index aligned
        to the non-NaN portion of the rolling vol.

    Raises
    ------
    ValueError
        If market_prices has length <= window.
    """
    if len(market_prices) <= window:
        raise ValueError(
            f"market_prices must have at least {window + 1} rows, got {len(market_prices)}"
        )

    returns = market_prices.pct_change()
    rolling_vol = returns.rolling(window).std(ddof=1) * np.sqrt(_TRADING_DAYS_PER_YEAR)
    rolling_vol = rolling_vol.dropna()
    threshold = rolling_vol.median()
    labels: pd.Series = (rolling_vol > threshold).astype(np.int8)
    labels.name = "volatility_regime"
    return labels


def detect_trend_regime(market_prices: pd.Series, window: int = 60) -> pd.Series:
    """Label days as up-trend (1) or down-trend (0) relative to a moving average.

    Up-trend = close price strictly above the N-day simple moving average.

    Parameters
    ----------
    market_prices : pd.Series
        DatetimeIndex, float values, length >= window.
    window : int
        Moving average window in trading days.

    Returns
    -------
    pd.Series
        int8 0/1 series, length = len(market_prices) - (window - 1).

    Raises
    ------
    ValueError
        If market_prices has length < window.
    """
    if len(market_prices) < window:
        raise ValueError(
            f"market_prices must have at least {window} rows, got {len(market_prices)}"
        )

    ma = market_prices.rolling(window).mean()
    valid = ma.notna()
    labels: pd.Series = (market_prices[valid] > ma[valid]).astype(np.int8)
    labels.name = "trend_regime"
    return labels


def validate_custom_regime(regime: pd.Series, reference_index: pd.DatetimeIndex) -> pd.Series:
    """Validate and normalize a user-supplied regime label series.

    Rules:
    - Every value must be in {0, 1} (bool is accepted and coerced to int8).
    - Every entry in `reference_index` must appear in `regime.index` — the
      custom regime must cover the full factor date range.
    - The returned series has dtype int8 and is reindexed to `reference_index`.

    Parameters
    ----------
    regime : pd.Series
        User-supplied 0/1 or bool Series.
    reference_index : pd.DatetimeIndex
        Reference index the regime must cover.

    Returns
    -------
    pd.Series
        int8 Series reindexed to `reference_index`, name "custom_regime".

    Raises
    ------
    ValueError
        On dtype, value, or alignment problems.
    """
    if regime.dtype == bool:
        regime = regime.astype(np.int8)

    values = set(pd.Series(regime.unique()).dropna().tolist())
    if not values.issubset({0, 1}):
        raise ValueError(f"custom regime values must be 0 or 1, found: {sorted(values)}")

    missing = reference_index.difference(regime.index.tolist())
    if len(missing) > 0:
        raise ValueError(
            f"custom regime missing {len(missing)} entries from reference index "
            f"(first missing: {missing[0]})"
        )

    result: pd.Series = regime.reindex(reference_index).astype(np.int8)
    result.name = "custom_regime"
    return result
