"""Tests for per-regime metric computation."""

import math

import numpy as np
import pandas as pd
import pytest

from regime_lens.core.metrics import (
    annualized_return,
    compute_metrics_by_regime,
    ic_ir,
    ic_mean,
    ic_win_rate,
    max_drawdown,
    mean_turnover,
)


def test_ic_mean_simple() -> None:
    ic = pd.Series([0.1, -0.05, 0.2, 0.0])
    assert ic_mean(ic) == pytest.approx(0.0625)


def test_ic_mean_empty_returns_nan() -> None:
    assert math.isnan(ic_mean(pd.Series([], dtype="float64")))


def test_ic_ir_simple() -> None:
    # mean = 0.0625, std(ddof=1) ~ 0.10969, annualized factor sqrt(252) ~ 15.8745
    ic = pd.Series([0.1, -0.05, 0.2, 0.0])
    expected = 0.0625 / ic.std(ddof=1) * math.sqrt(252)
    assert ic_ir(ic) == pytest.approx(expected)


def test_ic_ir_single_value_returns_nan() -> None:
    """ddof=1 std of a single value is NaN → ICIR is NaN."""
    assert math.isnan(ic_ir(pd.Series([0.1])))


def test_ic_ir_empty_returns_nan() -> None:
    assert math.isnan(ic_ir(pd.Series([], dtype="float64")))


def test_ic_win_rate_half() -> None:
    ic = pd.Series([0.1, -0.1, 0.2, -0.2])
    assert ic_win_rate(ic) == pytest.approx(0.5)


def test_ic_win_rate_excludes_zeros_as_losses() -> None:
    """ic > 0 → win; ic == 0 is NOT a win."""
    ic = pd.Series([0.1, 0.0, 0.2, 0.0])
    assert ic_win_rate(ic) == pytest.approx(0.5)


def test_ic_win_rate_empty_returns_nan() -> None:
    assert math.isnan(ic_win_rate(pd.Series([], dtype="float64")))


def test_annualized_return_zero_returns_zero() -> None:
    zero = pd.Series([0.0] * 252)
    assert annualized_return(zero) == pytest.approx(0.0)


def test_annualized_return_constant_positive() -> None:
    # 0.1% every day for 252 days → ~28.6% annualized
    daily = pd.Series([0.001] * 252)
    expected = (1.001**252) - 1
    assert annualized_return(daily) == pytest.approx(expected)


def test_annualized_return_empty_returns_nan() -> None:
    assert math.isnan(annualized_return(pd.Series([], dtype="float64")))


def test_max_drawdown_monotonic_up_is_zero() -> None:
    # All positive returns → equity curve never retreats → drawdown is 0
    r = pd.Series([0.01] * 100)
    assert max_drawdown(r) == pytest.approx(0.0)


def test_max_drawdown_simple_peak_to_trough() -> None:
    # +10% then -20% → peak = 1.10, trough = 0.88, drawdown = -0.20
    r = pd.Series([0.10, -0.20])
    assert max_drawdown(r) == pytest.approx(-0.20)


def test_max_drawdown_empty_returns_nan() -> None:
    assert math.isnan(max_drawdown(pd.Series([], dtype="float64")))


def test_max_drawdown_all_nan_returns_nan() -> None:
    assert math.isnan(max_drawdown(pd.Series([np.nan, np.nan])))


def test_mean_turnover_simple() -> None:
    tov = pd.Series([0.1, 0.2, 0.3])
    assert mean_turnover(tov) == pytest.approx(0.2)


def test_mean_turnover_none_returns_none() -> None:
    assert mean_turnover(None) is None


def test_mean_turnover_empty_series_returns_nan() -> None:
    result = mean_turnover(pd.Series([], dtype="float64"))
    assert result is not None
    assert math.isnan(result)


def test_compute_metrics_by_regime_shape() -> None:
    idx = pd.bdate_range("2024-01-02", periods=10)
    ic = pd.Series([0.01] * 5 + [0.05] * 5, index=idx)
    ls = pd.Series([0.001] * 5 + [0.003] * 5, index=idx)
    regime = pd.Series([0] * 5 + [1] * 5, index=idx, dtype="int8")
    result = compute_metrics_by_regime(ic, ls, regime, turnover=None)
    assert set(result.keys()) == {0, 1}
    assert set(result[0].keys()) == {
        "ic_mean",
        "ic_ir",
        "ic_win_rate",
        "annualized_return",
        "max_drawdown",
        "mean_turnover",
    }


def test_compute_metrics_by_regime_separates_groups() -> None:
    idx = pd.bdate_range("2024-01-02", periods=10)
    ic = pd.Series([0.01] * 5 + [0.05] * 5, index=idx)
    ls = pd.Series([0.001] * 10, index=idx)
    regime = pd.Series([0] * 5 + [1] * 5, index=idx, dtype="int8")
    result = compute_metrics_by_regime(ic, ls, regime, turnover=None)
    assert result[0]["ic_mean"] == pytest.approx(0.01)
    assert result[1]["ic_mean"] == pytest.approx(0.05)
    assert result[0]["mean_turnover"] is None
    assert result[1]["mean_turnover"] is None


def test_compute_metrics_by_regime_empty_group_gives_nan() -> None:
    idx = pd.bdate_range("2024-01-02", periods=5)
    ic = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05], index=idx)
    ls = pd.Series([0.001] * 5, index=idx)
    regime = pd.Series([1, 1, 1, 1, 1], index=idx, dtype="int8")
    result = compute_metrics_by_regime(ic, ls, regime, turnover=None)
    ic0 = result[0]["ic_mean"]
    assert ic0 is not None and math.isnan(ic0)
    assert result[1]["ic_mean"] == pytest.approx(0.03)


def test_compute_metrics_by_regime_with_turnover() -> None:
    idx = pd.bdate_range("2024-01-02", periods=4)
    ic = pd.Series([0.01, 0.02, 0.03, 0.04], index=idx)
    ls = pd.Series([0.001, 0.002, 0.003, 0.004], index=idx)
    tov = pd.Series([0.1, 0.2, 0.3, 0.4], index=idx)
    regime = pd.Series([0, 0, 1, 1], index=idx, dtype="int8")
    result = compute_metrics_by_regime(ic, ls, regime, turnover=tov)
    assert result[0]["mean_turnover"] == pytest.approx(0.15)
    assert result[1]["mean_turnover"] == pytest.approx(0.35)


def test_compute_metrics_by_regime_inner_joins_on_regime_index() -> None:
    """If the regime index is a subset of the ic index, only overlapping days are used."""
    ic_idx = pd.bdate_range("2024-01-02", periods=10)
    ic = pd.Series(np.arange(10, dtype=float), index=ic_idx)
    ls = pd.Series([0.001] * 10, index=ic_idx)
    # Regime only covers the second half
    regime = pd.Series([0, 0, 1, 1, 1], index=ic_idx[5:], dtype="int8")
    result = compute_metrics_by_regime(ic, ls, regime, turnover=None)
    assert result[0]["ic_mean"] == pytest.approx(5.5)  # mean of 5, 6
    assert result[1]["ic_mean"] == pytest.approx(8.0)  # mean of 7, 8, 9
