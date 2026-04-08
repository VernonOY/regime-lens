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
