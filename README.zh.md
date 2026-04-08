# regime-lens

**[English](README.md) | 简体中文**

> **一行代码,看清你的量化因子在不同市场环境下到底表现如何。**

[alpha-kit](https://github.com/VernonOY/alpha-kit) 生态系统的一部分。

## 为什么要这个工具

一个因子在整个样本期上报"IC = 0.04"看起来平平无奇,但可能掩盖了两段完全不同的故事:

- 高波动市场下 IC **+0.055**,平静市场下 IC **+0.037**
- 上涨趋势 IC **+0.061**,下跌趋势 IC **+0.039**

`regime-lens` 用**内置市场 regime**(波动率、趋势)或**用户提供的 0/1 标签序列**对你的因子 IC、多空 PnL、换手率进行切片,产出一份开箱即用的 Plotly 交互式 HTML 报告 + JSON 数据导出 + 一句话自然语言总结。

## 安装

v0.1 仅通过 GitHub 发布 — **暂未上 PyPI**。

```bash
# uv (推荐)
uv add "git+https://github.com/VernonOY/regime-lens@v0.1.0"

# pip
pip install "git+https://github.com/VernonOY/regime-lens@v0.1.0"
```

PyPI 发布计划在 v0.2。

## 快速上手 (Python)

```python
from regime_lens import RegimeAnalyzer

analyzer = RegimeAnalyzer()
report = analyzer.analyze(
    factor_ic=my_factor_ic_series,            # pd.Series[float],日频 IC
    long_short_returns=my_ls_returns,         # pd.Series[float],日频多空组合收益
    market_prices=index_close,                # pd.Series[float],指数收盘价
    regimes=["volatility", "trend"],
)

print(report.summary())
# "volatility: factor IC is +0.055 (high vol) vs +0.037 (low vol); trend: factor IC is +0.061 (up-trend) vs +0.039 (down-trend)."

report.save_html("report.html")   # 生成交互式 Plotly 报告
print(report.to_json())           # json.dumps 安全的字典
```

完整的端到端示例见 [`examples/quickstart.py`](examples/quickstart.py)。

## 快速上手 (CLI)

```bash
regime-lens analyze \
    --factor-ic factor_ic.csv \
    --long-short-returns ls_returns.csv \
    --market-prices index_close.csv \
    --output-html report.html \
    --output-json report.json
```

每个输入 CSV 都有一个 `date` 列和一个数值列(`ic`、`ls_return` 或 `close`)。

终端样例输出:

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

Summary: volatility: factor IC is +0.055 (high vol) vs +0.037 (low vol); trend:
factor IC is +0.061 (up-trend) vs +0.039 (down-trend).
HTML: report.html
JSON: report.json
```

也可用 `regime-lens list-regimes` 查看内置 regime 的定义。

## 内置 regime

| 名称         | 定义                                                                                |
|--------------|-------------------------------------------------------------------------------------|
| `volatility` | 20 日 realized vol 与样本内中位数比较(label 1=高波,0=低波)                          |
| `trend`      | market_prices 与 60 日简单移动平均比较(label 1=上涨趋势,0=下跌趋势)                |
| custom       | 通过 `custom_regimes` 参数传入任意用户定义的 `pd.Series[int]` 0/1 标签              |

**关于波动率阈值的说明**:中位数是在**全样本期**(in-sample)计算的。这适合做事后因子诊断,但如果作为实盘 regime 切换信号会有数据穿越。自动 regime 检测(HMM、Chow test、CUSUM)规划在 v0.3。

## 每个 regime 报告的指标

- `ic_mean` — 日频 IC 的均值
- `ic_ir` — 年化 IC Information Ratio
- `ic_win_rate` — IC > 0 的天数占比
- `annualized_return` — 多空组合的年化复合收益
- `max_drawdown` — 最大峰谷回撤
- `mean_turnover` — 平均日频换手率(如未提供则显示 `N/A`)

## Alpha-kit 生态系统

- [qtype](https://github.com/VernonOY/qtype) — 静态分析工具,捕捉 look-ahead 偏差等致命量化 bug
- **regime-lens** (本仓库)
- backtest-debugger (即将推出)
- context-distiller, paper2alpha, agent-risk-harness, replicalpha (规划中)

## 开发

```bash
uv sync --all-extras --dev
uv run ruff check .
uv run mypy --strict src/
uv run pytest --cov=regime_lens
```

覆盖率门禁:≥80%。共享开发约定见 [alpha-kit CLAUDE.md](https://github.com/VernonOY/alpha-kit)。

## License

MIT. 见 [LICENSE](LICENSE)。
