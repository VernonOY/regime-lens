# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-04-08

### Added

- `RegimeAnalyzer.analyze()` orchestrator that slices factor metrics by market regime.
- Built-in regime detectors: `volatility` (20-day realized vol vs. in-sample median) and `trend` (60-day SMA).
- User-supplied custom 0/1 regime label series via `custom_regimes`.
- Per-regime metrics: `ic_mean`, `ic_ir`, `ic_win_rate`, `annualized_return`, `max_drawdown`, `mean_turnover`.
- `RegimeReport` with `.data`, `.to_json()`, `.summary()`, `.to_html()`, `.save_html()`, `.show()`.
- `regime-lens analyze` CLI command producing an HTML report + JSON export.
- `regime-lens list-regimes` CLI command.
- `examples/quickstart.py` showing end-to-end usage on synthetic data.
- Three-layer architecture (`core/`, `cli/`) per alpha-kit conventions.
- CI: pytest (unit + e2e) + ruff + mypy --strict on Python 3.11 and 3.12, coverage gate ≥ 80%.

### Known limitations

- The `volatility` regime uses an in-sample median threshold. This is fine for ex-post
  factor diagnosis but would leak if applied as a live regime-switching signal.
  Automatic regime detection (HMM / Chow test / CUSUM) is scheduled for v0.3.
- `scipy` is intentionally not a dependency; all metrics are computed with pandas + numpy only.
