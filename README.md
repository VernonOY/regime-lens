# regime-lens

> **One line of code to see how your quant factor really performs across different market regimes.**

Part of the [alpha-kit](https://github.com/VernonOY/alpha-kit) ecosystem.

## Why

A factor that reports "IC = 0.04" across the full sample period can hide two very
different stories:

- IC **+0.055** when the market is volatile, IC **+0.037** when it's calm
- IC **+0.061** in up-trends, IC **+0.039** in down-trends

`regime-lens` slices your factor's IC, long-short PnL, and turnover by **built-in
market regimes** (volatility, trend) or by a **user-supplied 0/1 label series**,
and produces a one-shot Plotly HTML report plus a JSON data export plus a
one-sentence summary.

## Install

```bash
uv add regime-lens
# or
pip install regime-lens
```

## Quickstart (Python)

```python
from regime_lens import RegimeAnalyzer

analyzer = RegimeAnalyzer()
report = analyzer.analyze(
    factor_ic=my_factor_ic_series,            # pd.Series[float], daily IC
    long_short_returns=my_ls_returns,         # pd.Series[float], daily LS portfolio return
    market_prices=index_close,                # pd.Series[float], index close price
    regimes=["volatility", "trend"],
)

print(report.summary())
# "volatility: factor IC is +0.055 (regime=1) vs +0.037 (regime=0); trend: factor IC is +0.061 (regime=1) vs +0.039 (regime=0)."

report.save_html("report.html")   # interactive Plotly
print(report.to_json())           # json.dumps-safe dict
```

A runnable end-to-end example lives at [`examples/quickstart.py`](examples/quickstart.py).

## Quickstart (CLI)

```bash
regime-lens analyze \
    --factor-ic factor_ic.csv \
    --long-short-returns ls_returns.csv \
    --market-prices index_close.csv \
    --output-html report.html \
    --output-json report.json
```

Each input CSV has a `date` column and one value column (`ic`, `ls_return`, or `close`).

Sample terminal output:

```
                                 Regime metrics
┏━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ regime  ┃ value ┃ ic_mean ┃   ic_ir ┃ ic_win_ ┃ annual_ ┃ max_draw ┃ mean_to ┃
┡━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ volati… │ 0     │ +0.0373 │ +10.343 │ +0.7586 │ -0.1279 │  -0.1059 │     N/A │
│ volati… │ 1     │ +0.0548 │ +9.7905 │ +0.7414 │ -0.0106 │  -0.1276 │     N/A │
│ trend   │ 0     │ +0.0391 │ +7.6941 │ +0.6903 │ +0.0513 │  -0.0940 │     N/A │
│ trend   │ 1     │ +0.0615 │ +13.143 │ +0.8125 │ -0.2359 │  -0.1094 │     N/A │
└─────────┴───────┴─────────┴─────────┴─────────┴─────────┴──────────┴─────────┘

Summary: volatility: factor IC is +0.055 (regime=1) vs +0.037 (regime=0); trend:
factor IC is +0.061 (regime=1) vs +0.039 (regime=0).
HTML: report.html
JSON: report.json
```

Also available: `regime-lens list-regimes` to see the built-in regime definitions.

## Built-in regimes

| name         | definition                                                                      |
|--------------|---------------------------------------------------------------------------------|
| `volatility` | 20-day realized vol of market_prices compared to the in-sample median           |
| `trend`      | market_prices compared to its 60-day simple moving average                      |
| custom       | any user-supplied `pd.Series[int]` of 0/1 labels via the `custom_regimes` kwarg |

**Note on the volatility threshold:** the median is computed over the **full
sample period** (in-sample). This is appropriate for ex-post factor diagnosis,
but would leak if used as a live regime-switching signal. Automatic regime
detection (HMM, Chow test, CUSUM) is planned for v0.3.

## Metrics reported per regime

- `ic_mean` — mean of daily IC
- `ic_ir` — annualized Information Ratio of IC
- `ic_win_rate` — share of days with IC > 0
- `annualized_return` — compound annual return of the long-short PnL
- `max_drawdown` — worst peak-to-trough drawdown
- `mean_turnover` — average daily turnover (if provided; otherwise `N/A`)

## Alpha-kit ecosystem

- [qtype](https://github.com/VernonOY/qtype) — static analyzer for look-ahead bias and other fatal quant bugs
- **regime-lens** (this repo)
- backtest-debugger (coming soon)
- context-distiller, paper2alpha, agent-risk-harness, replicalpha (future)

## Development

```bash
uv sync --all-extras --dev
uv run ruff check .
uv run mypy --strict src/
uv run pytest --cov=regime_lens
```

Coverage gate: ≥80%. See [alpha-kit CLAUDE.md](https://github.com/VernonOY/alpha-kit)
for the shared development conventions.

## License

MIT. See [LICENSE](LICENSE).
