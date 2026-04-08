"""Regime-sliced analysis report: data access, JSON export, summary text.

Plotly HTML rendering is added in Task 12.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


def _clean(value: float | None) -> float | None:
    """Convert NaN to None so json.dumps can serialize. Keep None as None."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


@dataclass
class RegimeReport:
    """Container for regime-sliced factor metrics.

    Attributes
    ----------
    data : pd.DataFrame
        Multi-index (regime_name, regime_value) with metric columns.
    """

    data: pd.DataFrame

    def to_json(self) -> dict[str, dict[str, dict[str, float | None]]]:
        """Return a nested dict: {regime_name: {regime_value: {metric: value}}}.

        NaN values are converted to None so the result is json.dumps-safe.
        """
        result: dict[str, dict[str, dict[str, float | None]]] = {}
        metric_cols = list(self.data.columns)
        records = self.data.reset_index().to_dict(orient="records")
        for record in records:
            name = str(record["regime_name"])
            value = str(int(record["regime_value"]))
            regime_bucket = result.setdefault(name, {})
            regime_bucket[value] = {metric: _clean(record[metric]) for metric in metric_cols}
        return result

    def summary(self) -> str:
        """One-sentence natural-language template per regime.

        Example:
            "volatility: factor IC is +0.074 (regime=1) vs +0.012 (regime=0); "
            "trend: factor IC is +0.056 (regime=1) vs +0.031 (regime=0)."
        """
        parts: list[str] = []
        for name in self.data.index.get_level_values("regime_name").unique():
            subset = self.data.loc[name]
            if 1 not in subset.index or 0 not in subset.index:
                continue
            ic_1 = _clean(subset.loc[1, "ic_mean"])
            ic_0 = _clean(subset.loc[0, "ic_mean"])
            ic_1_str = f"{ic_1:+.3f}" if ic_1 is not None else "N/A"
            ic_0_str = f"{ic_0:+.3f}" if ic_0 is not None else "N/A"
            parts.append(f"{name}: factor IC is {ic_1_str} (regime=1) vs {ic_0_str} (regime=0)")
        return "; ".join(parts) + "."
