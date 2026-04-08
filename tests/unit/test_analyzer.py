"""Tests for the RegimeAnalyzer orchestrator."""

import pandas as pd
import pytest

from regime_lens.core.analyzer import RegimeAnalyzer


def test_analyzer_runs_with_two_builtin_regimes(
    sample_factor_ic: "pd.Series[float]",
    sample_long_short_returns: "pd.Series[float]",
    sample_market_prices: "pd.Series[float]",
) -> None:
    analyzer = RegimeAnalyzer()
    report = analyzer.analyze(
        factor_ic=sample_factor_ic,
        long_short_returns=sample_long_short_returns,
        market_prices=sample_market_prices,
        regimes=["volatility", "trend"],
    )
    df = report.data
    # Two regime types x two labels = 4 rows
    assert len(df) == 4
    assert set(df.index.get_level_values("regime_name")) == {"volatility", "trend"}
    assert set(df.index.get_level_values("regime_value")) == {0, 1}
    assert set(df.columns) == {
        "ic_mean",
        "ic_ir",
        "ic_win_rate",
        "annualized_return",
        "max_drawdown",
        "mean_turnover",
    }


def test_analyzer_includes_custom_regime(
    sample_factor_ic: "pd.Series[float]",
    sample_long_short_returns: "pd.Series[float]",
    sample_market_prices: "pd.Series[float]",
) -> None:
    n = len(sample_factor_ic)
    custom = pd.Series(
        [0] * (n // 2) + [1] * (n - n // 2),
        index=sample_factor_ic.index,
        dtype="int8",
    )
    analyzer = RegimeAnalyzer()
    report = analyzer.analyze(
        factor_ic=sample_factor_ic,
        long_short_returns=sample_long_short_returns,
        market_prices=sample_market_prices,
        regimes=[],
        custom_regimes={"halves": custom},
    )
    assert set(report.data.index.get_level_values("regime_name")) == {"halves"}


def test_analyzer_turnover_propagates(
    sample_factor_ic: "pd.Series[float]",
    sample_long_short_returns: "pd.Series[float]",
    sample_market_prices: "pd.Series[float]",
    sample_turnover: "pd.Series[float]",
) -> None:
    analyzer = RegimeAnalyzer()
    report = analyzer.analyze(
        factor_ic=sample_factor_ic,
        long_short_returns=sample_long_short_returns,
        market_prices=sample_market_prices,
        regimes=["volatility"],
        turnover=sample_turnover,
    )
    tov_column = report.data["mean_turnover"]
    assert not tov_column.isna().all()


def test_analyzer_rejects_unknown_regime_name(
    sample_factor_ic: "pd.Series[float]",
    sample_long_short_returns: "pd.Series[float]",
    sample_market_prices: "pd.Series[float]",
) -> None:
    analyzer = RegimeAnalyzer()
    with pytest.raises(ValueError, match="unknown regime"):
        analyzer.analyze(
            factor_ic=sample_factor_ic,
            long_short_returns=sample_long_short_returns,
            market_prices=sample_market_prices,
            regimes=["hmm_states"],
        )


def test_analyzer_requires_at_least_one_regime(
    sample_factor_ic: "pd.Series[float]",
    sample_long_short_returns: "pd.Series[float]",
    sample_market_prices: "pd.Series[float]",
) -> None:
    analyzer = RegimeAnalyzer()
    with pytest.raises(ValueError, match="at least one"):
        analyzer.analyze(
            factor_ic=sample_factor_ic,
            long_short_returns=sample_long_short_returns,
            market_prices=sample_market_prices,
            regimes=[],
            custom_regimes=None,
        )
