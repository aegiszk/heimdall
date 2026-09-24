import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.execution.fills import apply_costs, funding_accrual, slippage_bps
from core.validation.metrics import sharpe
from tools.calibrate_fills import calibrate_table, print_table, sample_btc_book


def ten_level_book():
    mid = 100.0
    bids = [[mid - 0.01 - i * 0.05, 1.0] for i in range(10)]
    asks = [[mid + 0.01 + i * 0.05, 1.0] for i in range(10)]
    return {"bids": bids, "asks": asks}


def test_book_walk_slippage_is_monotonic_with_size():
    book = ten_level_book()
    sizes = [50, 150, 300, 600, 900]
    slips = [slippage_bps(size, book) for size in sizes]

    assert all(later > earlier for earlier, later in zip(slips, slips[1:]))


def test_apply_costs_reduces_sharpe():
    rng = np.random.default_rng(7)
    returns = rng.normal(0.001, 0.01, 252)
    positions = (np.arange(252) % 2).astype(float)

    net = apply_costs(returns, positions, cost_bps_per_turn=20.0)

    assert net.mean() < returns.mean()
    assert sharpe(net) < sharpe(returns)


def test_funding_accrual_short_receives_positive_funding():
    assert funding_accrual(notional=-100_000, funding_rate=0.0001, periods=1) == 10.0
    assert funding_accrual(notional=100_000, funding_rate=0.0001, periods=1) == -10.0


def test_sample_calibration_prints_size_slippage_table(capsys):
    rows = calibrate_table(sample_btc_book())
    print_table(rows)
    output = capsys.readouterr().out
    slips = [slip for _, slip in rows]

    assert output.splitlines()[0] == "size|slippage_bps"
    assert "250,000|4.8782" in output
    assert all(later >= earlier for earlier, later in zip(slips, slips[1:]))
