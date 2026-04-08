"""Top-level orchestrator that ties regime detection and metric aggregation."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from regime_lens.core.metrics import compute_metrics_by_regime
from regime_lens.core.regimes import (
    detect_trend_regime,
    detect_volatility_regime,
    validate_custom_regime,
)
from regime_lens.core.report import RegimeReport

_BUILTIN_REGIMES = {"volatility", "trend"}


@dataclass
class RegimeAnalyzer:
    """Run factor metrics sliced by market regime."""

    def analyze(
        self,
        factor_ic: pd.Series,
        long_short_returns: pd.Series,
        market_prices: pd.Series,
        regimes: list[str] | None = None,
        custom_regimes: dict[str, pd.Series] | None = None,
        turnover: pd.Series | None = None,
        vol_window: int = 20,
        trend_window: int = 60,
    ) -> RegimeReport:
        """Compute per-regime factor metrics and return a RegimeReport.

        Parameters
        ----------
        factor_ic, long_short_returns, market_prices : pd.Series
            Date-indexed input series. Required.
        regimes : list[str] | None
            Built-in regimes to compute. Subset of {"volatility", "trend"}.
            Defaults to ["volatility", "trend"] if None.
        custom_regimes : dict[str, pd.Series] | None
            User-supplied {name: 0/1 label series}. Optional.
        turnover : pd.Series | None
            Daily turnover series for mean_turnover metric. Optional.
        vol_window, trend_window : int
            Rolling window sizes for built-in detectors.

        Raises
        ------
        ValueError
            If `regimes` contains unknown names, or if both `regimes` and
            `custom_regimes` are empty.
        """
        if regimes is None:
            regimes = ["volatility", "trend"]
        unknown = set(regimes) - _BUILTIN_REGIMES
        if unknown:
            raise ValueError(
                f"unknown regime name(s): {sorted(unknown)}. "
                f"Built-in regimes are: {sorted(_BUILTIN_REGIMES)}. "
                f"Pass user-defined regimes via the `custom_regimes` argument."
            )
        if not regimes and not custom_regimes:
            raise ValueError("must specify at least one built-in regime or one custom regime")

        regime_label_series: dict[str, pd.Series] = {}
        if "volatility" in regimes:
            regime_label_series["volatility"] = detect_volatility_regime(
                market_prices, window=vol_window
            )
        if "trend" in regimes:
            regime_label_series["trend"] = detect_trend_regime(market_prices, window=trend_window)
        if custom_regimes:
            ref_idx = pd.DatetimeIndex(factor_ic.index)
            for name, series in custom_regimes.items():
                regime_label_series[name] = validate_custom_regime(series, reference_index=ref_idx)

        rows: list[dict[str, object]] = []
        for regime_name, labels in regime_label_series.items():
            per_group = compute_metrics_by_regime(
                factor_ic=factor_ic,
                long_short_returns=long_short_returns,
                regime=labels,
                turnover=turnover,
            )
            for regime_value, metrics in per_group.items():
                rows.append(
                    {
                        "regime_name": regime_name,
                        "regime_value": regime_value,
                        **metrics,
                    }
                )

        df = pd.DataFrame(rows).set_index(["regime_name", "regime_value"])
        return RegimeReport(data=df)
