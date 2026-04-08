"""Per-regime factor performance metrics.

All functions take a pandas Series and return a scalar float. Empty or
degenerate inputs return NaN rather than raising — callers handle the NaN
display.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

_TRADING_DAYS_PER_YEAR = 252


def ic_mean(ic: pd.Series) -> float:
    """Mean of the IC series. Returns NaN on empty input."""
    if len(ic) == 0:
        return math.nan
    return float(ic.mean())


def ic_ir(ic: pd.Series, annualize_factor: int = _TRADING_DAYS_PER_YEAR) -> float:
    """Annualized IC Information Ratio = mean / std(ddof=1) * sqrt(factor).

    Returns NaN if fewer than 2 observations, if std is zero, or if std is NaN.
    """
    if len(ic) < 2:
        return math.nan
    std = float(ic.std(ddof=1))
    if std == 0 or math.isnan(std):
        return math.nan
    return float(ic.mean()) / std * math.sqrt(annualize_factor)


def ic_win_rate(ic: pd.Series) -> float:
    """Share of observations strictly greater than zero. NaN on empty input."""
    if len(ic) == 0:
        return math.nan
    return float((ic > 0).mean())


def annualized_return(returns: pd.Series, periods_per_year: int = _TRADING_DAYS_PER_YEAR) -> float:
    """Annualized compound return from a daily return series.

    Returns NaN on empty input or if the cumulative growth becomes non-positive
    (which would make the geometric mean undefined).
    """
    clean = returns.dropna()
    if len(clean) == 0:
        return math.nan
    total_growth: float = float(np.prod(1.0 + clean.to_numpy()))
    if total_growth <= 0:
        return math.nan
    ann: float = total_growth ** (periods_per_year / len(clean)) - 1.0
    return ann


def max_drawdown(returns: pd.Series) -> float:
    """Worst peak-to-trough drawdown on the cumulative equity curve (<= 0)."""
    clean = returns.dropna()
    if len(clean) == 0:
        return math.nan
    equity = np.cumprod(1.0 + clean.to_numpy())
    rolling_peak = np.maximum.accumulate(equity)
    drawdown = equity / rolling_peak - 1.0
    return float(drawdown.min())


def mean_turnover(turnover: pd.Series | None) -> float | None:
    """Mean turnover, or None if the user did not provide a turnover series."""
    if turnover is None:
        return None
    if len(turnover) == 0:
        return math.nan
    return float(turnover.mean())
