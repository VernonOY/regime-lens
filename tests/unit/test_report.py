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
