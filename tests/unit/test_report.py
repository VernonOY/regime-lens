"""Tests for RegimeReport data access, JSON export, and summary string."""

import json
import math

import pandas as pd
import pytest

from regime_lens.core.analyzer import RegimeAnalyzer
from regime_lens.core.report import RegimeReport


@pytest.fixture
def report(
    sample_factor_ic: "pd.Series[float]",
    sample_long_short_returns: "pd.Series[float]",
    sample_market_prices: "pd.Series[float]",
) -> RegimeReport:
    analyzer = RegimeAnalyzer()
    return analyzer.analyze(
        factor_ic=sample_factor_ic,
        long_short_returns=sample_long_short_returns,
        market_prices=sample_market_prices,
        regimes=["volatility", "trend"],
    )


def test_report_data_is_dataframe(report: RegimeReport) -> None:
    assert isinstance(report.data, pd.DataFrame)
    assert report.data.index.names == ["regime_name", "regime_value"]


def test_report_to_json_is_serializable(report: RegimeReport) -> None:
    payload = report.to_json()
    encoded = json.dumps(payload)  # must round-trip
    decoded = json.loads(encoded)
    assert "volatility" in decoded
    assert "trend" in decoded
    # regime_value keys are stringified ints
    assert "0" in decoded["volatility"]
    assert "1" in decoded["volatility"]


def test_report_to_json_nan_becomes_none(report: RegimeReport) -> None:
    """json.dumps can't serialize NaN — to_json() must convert NaN to None."""
    report.data.loc[("volatility", 0), "ic_mean"] = math.nan
    payload = report.to_json()
    encoded = json.dumps(payload)  # would raise ValueError if NaN survived
    assert "NaN" not in encoded
    assert payload["volatility"]["0"]["ic_mean"] is None


def test_report_summary_mentions_each_regime(report: RegimeReport) -> None:
    text = report.summary()
    assert "volatility" in text
    assert "trend" in text
    assert "IC" in text


def test_report_summary_handles_nan_gracefully(report: RegimeReport) -> None:
    report.data.loc[("volatility", 0), "ic_mean"] = math.nan
    text = report.summary()
    # No literal "nan" in the rendered sentence
    assert "nan" not in text.lower()
    assert "N/A" in text


def test_report_to_html_is_plotly_standalone(report: RegimeReport) -> None:
    html = report.to_html()
    assert "plotly" in html.lower()
    assert "<div" in html


def test_report_to_html_mentions_each_regime(report: RegimeReport) -> None:
    html = report.to_html()
    assert "volatility" in html
    assert "trend" in html


def test_report_save_html_writes_file(
    report: RegimeReport, tmp_path: "pytest.TempPathFactory"
) -> None:
    from pathlib import Path

    out = Path(str(tmp_path)) / "report.html"
    report.save_html(out)
    assert out.exists()
    content = out.read_text()
    assert "plotly" in content.lower()


def test_report_show_opens_browser(report: RegimeReport, monkeypatch: pytest.MonkeyPatch) -> None:
    """show() writes to a tempfile and calls webbrowser.open — mock the browser."""
    called: list[str] = []

    def fake_open(url: str, *args: object, **kwargs: object) -> bool:
        called.append(url)
        return True

    monkeypatch.setattr("webbrowser.open", fake_open)
    report.show()
    assert len(called) == 1
    assert called[0].startswith("file://")


def test_report_html_contains_summary_box(report: RegimeReport) -> None:
    """The HTML page wraps the plot with a summary box containing the summary text."""
    html = report.to_html()
    assert "summary-box" in html
    assert report.summary() in html


def test_report_html_contains_regime_distribution(report: RegimeReport) -> None:
    """The HTML page shows a regime distribution section with semantic labels."""
    html = report.to_html()
    assert "Regime distribution" in html
    assert "high vol" in html
    assert "low vol" in html
    assert "up-trend" in html
    assert "down-trend" in html


def test_report_html_contains_data_table(report: RegimeReport) -> None:
    """The HTML page includes a data-table with formatted display metric names."""
    html = report.to_html()
    assert "data-table" in html
    assert "IC Mean" in html
    assert "IC IR (annualized)" in html
    assert "Max Drawdown" in html


def test_report_summary_uses_semantic_labels(report: RegimeReport) -> None:
    """Summary prose uses 'high vol' / 'up-trend' instead of 'regime=1'."""
    text = report.summary()
    assert "high vol" in text
    assert "low vol" in text
    assert "up-trend" in text
    assert "down-trend" in text
    assert "regime=1" not in text
    assert "regime=0" not in text


def test_report_regime_counts_populated_by_analyzer(
    sample_factor_ic: "pd.Series[float]",
    sample_long_short_returns: "pd.Series[float]",
    sample_market_prices: "pd.Series[float]",
) -> None:
    """The analyzer populates regime_counts with per-regime sample sizes."""
    analyzer = RegimeAnalyzer()
    rep = analyzer.analyze(
        factor_ic=sample_factor_ic,
        long_short_returns=sample_long_short_returns,
        market_prices=sample_market_prices,
        regimes=["volatility", "trend"],
    )
    assert "volatility" in rep.regime_counts
    assert "trend" in rep.regime_counts
    for name in ("volatility", "trend"):
        assert set(rep.regime_counts[name].keys()) == {0, 1}
        for v in rep.regime_counts[name].values():
            assert isinstance(v, int) and v >= 0
    vol_total = sum(rep.regime_counts["volatility"].values())
    assert 0 < vol_total <= len(sample_market_prices)
