"""Quickstart: analyze a synthetic factor by market regime.

Run: `uv run python examples/quickstart.py`
Output: prints the summary and writes `quickstart_report.html` in the cwd.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from regime_lens import RegimeAnalyzer


def make_synthetic_data() -> tuple[pd.Series, pd.Series, pd.Series]:
    rng = np.random.default_rng(7)
    n = 252
    idx = pd.bdate_range("2024-01-02", periods=n)

    # Market prices: mid-year vol spike
    rets = np.concatenate([rng.normal(0.0004, 0.008, n // 2), rng.normal(0.0004, 0.02, n - n // 2)])
    prices = pd.Series(100 * np.exp(np.cumsum(rets)), index=idx, name="close")

    # Factor IC: stronger in high vol
    ic_values = np.concatenate([rng.normal(0.02, 0.05, n // 2), rng.normal(0.07, 0.09, n - n // 2)])
    factor_ic = pd.Series(ic_values, index=idx, name="ic")

    # Long-short returns
    ls = pd.Series(rng.normal(0.0009, 0.01, n), index=idx, name="ls_return")

    return factor_ic, ls, prices


def main() -> None:
    factor_ic, ls, prices = make_synthetic_data()
    analyzer = RegimeAnalyzer()
    report = analyzer.analyze(
        factor_ic=factor_ic,
        long_short_returns=ls,
        market_prices=prices,
        regimes=["volatility", "trend"],
    )

    print("=== regime-lens quickstart ===")
    print(report.summary())
    print()
    print(report.data)

    out = Path("quickstart_report.html")
    report.save_html(out)
    print(f"\nInteractive report: {out.resolve()}")


if __name__ == "__main__":
    main()
