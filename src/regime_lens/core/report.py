"""Regime-sliced analysis report — stub (fleshed out in Task 11)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class RegimeReport:
    """Container for regime-sliced factor metrics.

    Attributes
    ----------
    data : pd.DataFrame
        Multi-index (regime_name, regime_value) with metric columns.
    """

    data: pd.DataFrame
