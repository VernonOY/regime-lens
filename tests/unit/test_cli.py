"""CLI unit tests using click.testing.CliRunner (no subprocess)."""

import json
from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from regime_lens.cli.main import cli


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_cli_analyze_writes_html_and_json(
    cli_runner: CliRunner,
    sample_factor_ic: "pd.Series[float]",
    sample_long_short_returns: "pd.Series[float]",
    sample_market_prices: "pd.Series[float]",
    tmp_path: Path,
) -> None:
    ic_path = tmp_path / "ic.csv"
    ls_path = tmp_path / "ls.csv"
    price_path = tmp_path / "price.csv"
    out_html = tmp_path / "report.html"
    out_json = tmp_path / "report.json"

    sample_factor_ic.to_csv(ic_path, header=["ic"])
    sample_long_short_returns.to_csv(ls_path, header=["ls_return"])
    sample_market_prices.to_csv(price_path, header=["close"])

    result = cli_runner.invoke(
        cli,
        [
            "analyze",
            "--factor-ic",
            str(ic_path),
            "--long-short-returns",
            str(ls_path),
            "--market-prices",
            str(price_path),
            "--output-html",
            str(out_html),
            "--output-json",
            str(out_json),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out_html.exists()
    assert out_json.exists()
    payload = json.loads(out_json.read_text())
    assert "volatility" in payload
    assert "trend" in payload


def test_cli_analyze_prints_summary(
    cli_runner: CliRunner,
    sample_factor_ic: "pd.Series[float]",
    sample_long_short_returns: "pd.Series[float]",
    sample_market_prices: "pd.Series[float]",
    tmp_path: Path,
) -> None:
    ic_path = tmp_path / "ic.csv"
    ls_path = tmp_path / "ls.csv"
    price_path = tmp_path / "price.csv"
    sample_factor_ic.to_csv(ic_path, header=["ic"])
    sample_long_short_returns.to_csv(ls_path, header=["ls_return"])
    sample_market_prices.to_csv(price_path, header=["close"])

    result = cli_runner.invoke(
        cli,
        [
            "analyze",
            "--factor-ic",
            str(ic_path),
            "--long-short-returns",
            str(ls_path),
            "--market-prices",
            str(price_path),
            "--output-html",
            str(tmp_path / "r.html"),
            "--output-json",
            str(tmp_path / "r.json"),
        ],
    )
    assert result.exit_code == 0
    assert "volatility" in result.output
    assert "IC" in result.output


def test_cli_analyze_errors_on_missing_input(cli_runner: CliRunner, tmp_path: Path) -> None:
    result = cli_runner.invoke(
        cli,
        [
            "analyze",
            "--factor-ic",
            str(tmp_path / "nonexistent.csv"),
            "--long-short-returns",
            str(tmp_path / "ls.csv"),
            "--market-prices",
            str(tmp_path / "p.csv"),
            "--output-html",
            str(tmp_path / "r.html"),
            "--output-json",
            str(tmp_path / "r.json"),
        ],
    )
    assert result.exit_code != 0
