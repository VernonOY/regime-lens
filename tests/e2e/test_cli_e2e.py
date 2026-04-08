"""End-to-end test: invoke the installed `regime-lens` binary as a subprocess."""

import json
import shutil
import subprocess
from pathlib import Path

CASES_DIR = Path(__file__).parent.parent / "cases"


def test_e2e_analyze_produces_html_and_json(tmp_path: Path) -> None:
    out_html = tmp_path / "report.html"
    out_json = tmp_path / "report.json"

    ic = tmp_path / "ic.csv"
    ls = tmp_path / "ls.csv"
    price = tmp_path / "price.csv"
    shutil.copy(CASES_DIR / "sample_factor_ic.csv", ic)
    shutil.copy(CASES_DIR / "sample_long_short_returns.csv", ls)
    shutil.copy(CASES_DIR / "sample_market_prices.csv", price)

    result = subprocess.run(
        [
            "regime-lens",
            "analyze",
            "--factor-ic",
            str(ic),
            "--long-short-returns",
            str(ls),
            "--market-prices",
            str(price),
            "--output-html",
            str(out_html),
            "--output-json",
            str(out_json),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"regime-lens analyze failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert out_html.exists()
    assert out_json.exists()

    payload = json.loads(out_json.read_text())
    assert set(payload.keys()) == {"volatility", "trend"}
    for regime_name in ("volatility", "trend"):
        assert "0" in payload[regime_name]
        assert "1" in payload[regime_name]
        for metric in (
            "ic_mean",
            "ic_ir",
            "ic_win_rate",
            "annualized_return",
            "max_drawdown",
            "mean_turnover",
        ):
            assert metric in payload[regime_name]["0"]


def test_e2e_list_regimes_command() -> None:
    result = subprocess.run(
        ["regime-lens", "list-regimes"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0
    assert "volatility" in result.stdout
    assert "trend" in result.stdout
