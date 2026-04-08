"""Regime-sliced analysis report: data access, JSON export, summary, Plotly HTML."""

from __future__ import annotations

import math
import tempfile
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


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

    def to_html(self) -> str:
        """Render the report as a self-contained Plotly HTML string."""
        fig = _build_figure(self)
        html: str = fig.to_html(include_plotlyjs="inline", full_html=True)
        return html

    def save_html(self, path: Path | str) -> None:
        """Write the HTML report to disk."""
        Path(path).write_text(self.to_html(), encoding="utf-8")

    def show(self) -> None:
        """Open the HTML report in the default web browser."""
        tmp = Path(tempfile.gettempdir()) / "regime_lens_report.html"
        self.save_html(tmp)
        webbrowser.open(tmp.as_uri())


def _build_figure(report: RegimeReport) -> Any:
    """Build a Plotly Figure with one subplot per regime type."""
    regime_names = list(report.data.index.get_level_values("regime_name").unique())
    # mean_turnover is often None - skip it in the bar chart
    metric_cols = [c for c in report.data.columns if c != "mean_turnover"]
    fig = make_subplots(
        rows=len(regime_names),
        cols=1,
        subplot_titles=[f"Regime: {name}" for name in regime_names],
    )
    for i, name in enumerate(regime_names, start=1):
        subset = report.data.loc[name]
        for regime_value in subset.index:
            values = [_clean(subset.loc[regime_value, m]) or 0.0 for m in metric_cols]
            fig.add_trace(
                go.Bar(
                    name=f"{name}={int(regime_value)}",
                    x=metric_cols,
                    y=values,
                ),
                row=i,
                col=1,
            )
    fig.update_layout(
        title_text="regime-lens: factor metrics by market regime",
        height=320 * len(regime_names),
        barmode="group",
    )
    return fig
