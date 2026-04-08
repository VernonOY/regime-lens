"""Tests for per-regime metric computation."""

import math

import pandas as pd
import pytest

from regime_lens.core.metrics import ic_ir, ic_mean, ic_win_rate


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
