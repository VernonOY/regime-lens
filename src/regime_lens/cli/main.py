"""regime-lens command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import click
import pandas as pd
from rich.console import Console
from rich.table import Table

from regime_lens.core.analyzer import RegimeAnalyzer

_console = Console()


def _load_series(path: Path, value_col: str) -> pd.Series:
    df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    series: pd.Series = df[value_col]
    return series


@click.group()
@click.version_option(package_name="regime-lens")
def cli() -> None:
    """regime-lens: factor performance analysis by market regime."""


@cli.command("analyze")
@click.option(
    "--factor-ic",
    "factor_ic_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="CSV with columns: date, ic",
)
@click.option(
    "--long-short-returns",
    "ls_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="CSV with columns: date, ls_return",
)
@click.option(
    "--market-prices",
    "prices_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="CSV with columns: date, close",
)
@click.option(
    "--output-html",
    "out_html",
    type=click.Path(path_type=Path),
    required=True,
    help="Where to write the interactive HTML report",
)
@click.option(
    "--output-json",
    "out_json",
    type=click.Path(path_type=Path),
    required=True,
    help="Where to write the JSON data",
)
@click.option(
    "--vol-window",
    type=int,
    default=20,
    show_default=True,
    help="Rolling window for the volatility regime detector",
)
@click.option(
    "--trend-window",
    type=int,
    default=60,
    show_default=True,
    help="SMA window for the trend regime detector",
)
def analyze(
    factor_ic_path: Path,
    ls_path: Path,
    prices_path: Path,
    out_html: Path,
    out_json: Path,
    vol_window: int,
    trend_window: int,
) -> None:
    """Analyze a factor sliced by market regime."""
    factor_ic = _load_series(factor_ic_path, "ic")
    long_short_returns = _load_series(ls_path, "ls_return")
    market_prices = _load_series(prices_path, "close")

    analyzer = RegimeAnalyzer()
    report = analyzer.analyze(
        factor_ic=factor_ic,
        long_short_returns=long_short_returns,
        market_prices=market_prices,
        regimes=["volatility", "trend"],
        vol_window=vol_window,
        trend_window=trend_window,
    )

    report.save_html(out_html)
    out_json.write_text(json.dumps(report.to_json(), indent=2), encoding="utf-8")

    _render_summary_table(report.data)
    _console.print()
    _console.print(f"[bold]Summary:[/bold] {report.summary()}")
    _console.print(f"HTML: {out_html}")
    _console.print(f"JSON: {out_json}")


def _render_summary_table(df: pd.DataFrame) -> None:
    table = Table(title="Regime metrics")
    table.add_column("regime")
    table.add_column("value")
    for col in df.columns:
        table.add_column(col, justify="right")
    records = df.reset_index().to_dict(orient="records")
    for record in records:
        cells = [str(record["regime_name"]), str(int(record["regime_value"]))]
        for col in df.columns:
            raw = record[col]
            cells.append("N/A" if raw is None or pd.isna(raw) else f"{raw:+.4f}")
        table.add_row(*cells)
    _console.print(table)
