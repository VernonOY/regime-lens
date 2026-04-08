"""Regime-sliced analysis report: data access, JSON export, summary, Plotly HTML."""

from __future__ import annotations

import math
import tempfile
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Metric display configuration: column name -> (display label, value format, "higher is better")
_METRIC_CONFIG: dict[str, tuple[str, str, bool | None]] = {
    "ic_mean": ("IC Mean", "+.3f", True),
    "ic_ir": ("IC IR (annualized)", "+.2f", True),
    "ic_win_rate": ("IC Win Rate", ".1%", True),
    "annualized_return": ("Annualized Return", "+.2%", True),
    "max_drawdown": ("Max Drawdown", "+.2%", False),
    "mean_turnover": ("Mean Turnover", ".1%", None),
}

# Semantic labels for each built-in regime: (label for value=0, label for value=1)
_REGIME_LABELS: dict[str, tuple[str, str]] = {
    "volatility": ("low vol", "high vol"),
    "trend": ("down-trend", "up-trend"),
}

# Consistent color palette for label values across all subplots
_COLOR_LABEL_0 = "#E15759"  # soft red
_COLOR_LABEL_1 = "#4E79A7"  # soft blue


def _clean(value: float | None) -> float | None:
    """Convert NaN to None so json.dumps can serialize. Keep None as None."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _format_value(value: float | None, fmt: str) -> str:
    """Format a cleaned metric value for display, or 'N/A' if missing."""
    cleaned = _clean(value)
    if cleaned is None:
        return "N/A"
    return format(cleaned, fmt)


def _semantic_label(regime_name: str, label_value: int) -> str:
    """Return a human-readable name for a regime label (e.g. 'high vol' for volatility=1)."""
    if regime_name in _REGIME_LABELS:
        return _REGIME_LABELS[regime_name][label_value]
    return f"label {label_value}"


@dataclass
class RegimeReport:
    """Container for regime-sliced factor metrics.

    Attributes
    ----------
    data : pd.DataFrame
        Multi-index (regime_name, regime_value) with metric columns.
    regime_counts : dict[str, dict[int, int]]
        Number of days in each label (0 / 1) per regime type. Used by the
        HTML report to show the regime distribution.
    """

    data: pd.DataFrame
    regime_counts: dict[str, dict[int, int]] = field(default_factory=dict)

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
            "volatility: factor IC is +0.074 (high vol) vs +0.012 (low vol); "
            "trend: factor IC is +0.056 (up-trend) vs +0.031 (down-trend)."
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
            label_1 = _semantic_label(str(name), 1)
            label_0 = _semantic_label(str(name), 0)
            parts.append(f"{name}: factor IC is {ic_1_str} ({label_1}) vs {ic_0_str} ({label_0})")
        return "; ".join(parts) + "."

    def to_html(self) -> str:
        """Render the report as a self-contained HTML page with header, plot, and table."""
        fig = _build_figure(self)
        plot_div: str = fig.to_html(
            include_plotlyjs="inline",
            full_html=False,
            div_id="regime-lens-plot",
        )
        return _wrap_html(self, plot_div)

    def save_html(self, path: Path | str) -> None:
        """Write the HTML report to disk."""
        Path(path).write_text(self.to_html(), encoding="utf-8")

    def show(self) -> None:
        """Open the HTML report in the default web browser."""
        tmp = Path(tempfile.gettempdir()) / "regime_lens_report.html"
        self.save_html(tmp)
        webbrowser.open(tmp.as_uri())


def _build_figure(report: RegimeReport) -> Any:
    """Build a Plotly Figure: one subplot per metric, grouped bars by regime type."""
    regime_names = list(report.data.index.get_level_values("regime_name").unique())
    metric_cols = list(report.data.columns)

    # 2 columns, enough rows to hold all metrics
    n_metrics = len(metric_cols)
    n_cols = 2
    n_rows = (n_metrics + n_cols - 1) // n_cols

    subplot_titles = [_METRIC_CONFIG.get(m, (m, "", None))[0] for m in metric_cols]
    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=subplot_titles,
        vertical_spacing=0.12,
        horizontal_spacing=0.15,
    )

    for i, metric in enumerate(metric_cols):
        row = i // n_cols + 1
        col = i % n_cols + 1
        display_name, fmt, _direction = _METRIC_CONFIG.get(metric, (metric, "+.4f", None))

        values_0: list[float | None] = []
        values_1: list[float | None] = []
        text_0: list[str] = []
        text_1: list[str] = []
        for name in regime_names:
            subset = report.data.loc[name]
            v0 = _clean(subset.loc[0, metric]) if 0 in subset.index else None
            v1 = _clean(subset.loc[1, metric]) if 1 in subset.index else None
            values_0.append(v0 if v0 is not None else 0.0)
            values_1.append(v1 if v1 is not None else 0.0)
            text_0.append(_format_value(v0, fmt))
            text_1.append(_format_value(v1, fmt))

        # Label-value traces: one per label, consistent color across all metrics.
        # Legend shows once (only on the first subplot).
        show_legend = i == 0
        fig.add_trace(
            go.Bar(
                name="regime = 0",
                x=regime_names,
                y=values_0,
                text=text_0,
                textposition="outside",
                marker_color=_COLOR_LABEL_0,
                showlegend=show_legend,
                legendgroup="label_0",
                hovertemplate="%{x} · regime=0<br>" + display_name + ": %{text}<extra></extra>",
            ),
            row=row,
            col=col,
        )
        fig.add_trace(
            go.Bar(
                name="regime = 1",
                x=regime_names,
                y=values_1,
                text=text_1,
                textposition="outside",
                marker_color=_COLOR_LABEL_1,
                showlegend=show_legend,
                legendgroup="label_1",
                hovertemplate="%{x} · regime=1<br>" + display_name + ": %{text}<extra></extra>",
            ),
            row=row,
            col=col,
        )

    fig.update_layout(
        title={
            "text": "regime-lens · factor metrics by market regime",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18},
        },
        barmode="group",
        height=280 * n_rows + 120,
        margin={"t": 100, "b": 60, "l": 60, "r": 40},
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="white",
        font={"family": "-apple-system, BlinkMacSystemFont, Helvetica, Arial", "size": 12},
        legend={
            "orientation": "h",
            "y": 1.06,
            "x": 0.5,
            "xanchor": "center",
            "bgcolor": "rgba(0,0,0,0)",
        },
        bargap=0.25,
        bargroupgap=0.1,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EEEEEE", zeroline=True, zerolinecolor="#CCCCCC")
    return fig


def _render_distribution(report: RegimeReport) -> str:
    """Return an HTML snippet summarizing sample counts per regime."""
    if not report.regime_counts:
        return ""
    items: list[str] = []
    for name, counts in report.regime_counts.items():
        total = counts.get(0, 0) + counts.get(1, 0)
        if total == 0:
            continue
        label_0_name = _semantic_label(name, 0)
        label_1_name = _semantic_label(name, 1)
        pct_0 = counts.get(0, 0) / total * 100
        pct_1 = counts.get(1, 0) / total * 100
        items.append(
            f"<li><strong>{name}</strong> — "
            f"{counts.get(1, 0)} days {label_1_name} ({pct_1:.1f}%) · "
            f"{counts.get(0, 0)} days {label_0_name} ({pct_0:.1f}%)</li>"
        )
    if not items:
        return ""
    return (
        '<section class="distribution"><h2>Regime distribution</h2>'
        f"<ul>{''.join(items)}</ul></section>"
    )


def _render_data_table(report: RegimeReport) -> str:
    """Return an HTML table with all metrics in their display form."""
    display = report.data.copy()
    # Rename rows to include semantic labels
    new_rows: list[tuple[str, str]] = []
    for name, value in display.index:
        semantic = _semantic_label(str(name), int(value))
        new_rows.append((str(name), f"{int(value)} · {semantic}"))
    display.index = pd.MultiIndex.from_tuples(new_rows, names=["regime", "label"])

    # Format each column with its configured spec
    formatted_cols: dict[str, list[str]] = {}
    for col in display.columns:
        _label, fmt, _dir = _METRIC_CONFIG.get(col, (col, "+.4f", None))
        formatted_cols[col] = [_format_value(v, fmt) for v in display[col]]
    formatted = pd.DataFrame(formatted_cols, index=display.index)
    # Rename columns to display labels
    formatted.columns = pd.Index(
        [_METRIC_CONFIG.get(c, (c, "", None))[0] for c in formatted.columns]
    )
    table_html: str = formatted.to_html(
        classes="data-table", border=0, escape=False, justify="left"
    )
    return f'<section class="table-section"><h2>Data</h2>{table_html}</section>'


def _wrap_html(report: RegimeReport, plot_div: str) -> str:
    """Wrap a plotly div in a full HTML page with header, summary, table, footer."""
    summary_text = report.summary()
    distribution_html = _render_distribution(report)
    table_html = _render_data_table(report)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>regime-lens report</title>
<style>
  :root {{
    --text: #222;
    --muted: #666;
    --border: #e5e5e5;
    --accent: #4E79A7;
    --bg: #fcfcfc;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif;
    max-width: 1200px;
    margin: 2em auto;
    padding: 0 2em 4em 2em;
    color: var(--text);
    background: var(--bg);
    line-height: 1.5;
  }}
  header {{
    border-bottom: 3px solid var(--accent);
    padding-bottom: 1em;
    margin-bottom: 1.5em;
  }}
  header h1 {{
    margin: 0;
    font-size: 1.7em;
    font-weight: 600;
  }}
  header .tagline {{
    color: var(--muted);
    font-size: 0.95em;
    margin-top: 0.3em;
  }}
  .summary-box {{
    background: #fff;
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    padding: 1em 1.2em;
    margin: 1.5em 0;
    font-size: 1.05em;
    line-height: 1.6;
  }}
  .summary-box strong {{ color: var(--accent); }}
  section.distribution {{
    margin: 1.5em 0;
  }}
  section.distribution h2,
  section.table-section h2 {{
    font-size: 1.1em;
    margin-bottom: 0.5em;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  section.distribution ul {{
    list-style: none;
    padding: 0;
    margin: 0;
  }}
  section.distribution li {{
    padding: 0.4em 0;
    border-bottom: 1px solid var(--border);
    color: var(--text);
  }}
  section.distribution li:last-child {{ border-bottom: none; }}
  .plot-wrap {{
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1em;
    margin: 1.5em 0;
  }}
  section.table-section {{
    margin-top: 2em;
  }}
  table.data-table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 0.9em;
    background: #fff;
  }}
  table.data-table th,
  table.data-table td {{
    padding: 0.6em 0.8em;
    border: 1px solid var(--border);
    text-align: right;
    font-variant-numeric: tabular-nums;
  }}
  table.data-table th {{
    background: #f5f5f5;
    text-align: left;
    font-weight: 600;
  }}
  table.data-table td:first-child,
  table.data-table th:first-child,
  table.data-table td:nth-child(2),
  table.data-table th:nth-child(2) {{
    text-align: left;
  }}
  footer {{
    margin-top: 3em;
    padding-top: 1em;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: 0.85em;
  }}
  footer code {{
    background: #f0f0f0;
    padding: 0.1em 0.4em;
    border-radius: 3px;
  }}
</style>
</head>
<body>
<header>
  <h1>regime-lens — factor performance by market regime</h1>
  <div class="tagline">
    One line of code to see how your quant factor really performs across market regimes.
  </div>
</header>

<div class="summary-box">
  <strong>Summary:</strong> {summary_text}
</div>

{distribution_html}

<div class="plot-wrap">
{plot_div}
</div>

{table_html}

<footer>
  Generated by <code>regime-lens v0.1.0</code> · part of the
  <a href="https://github.com/VernonOY/alpha-kit">alpha-kit</a> ecosystem.
  Volatility regime threshold is computed in-sample — see README for caveats.
</footer>
</body>
</html>
"""
