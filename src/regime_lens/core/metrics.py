"""Per-regime factor performance metrics.

All functions take a pandas Series and return a scalar float. Empty or
degenerate inputs return NaN rather than raising — callers handle the NaN
display.
"""

from __future__ import annotations

import math

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
