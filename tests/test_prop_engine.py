import os
import sys
from dataclasses import replace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.risk.prop_engine import Action, PropRiskConfig, PropRiskEngine


MICRO_TICKS = {
    "MES": 1.25,
    "MNQ": 0.50,
}


def obey_engine_for_random_days(days=10_000, seed=20260702):
    rng = np.random.default_rng(seed)
    engine = PropRiskEngine()
    min_margin = engine.live_equity - engine.mll_floor
    fills = 0
    stop_days = 0
    flatten_days = 0

    for _ in range(days):
        action = engine.check()
        if action == Action.DEAD:
            raise AssertionError("engine was dead before trading")

        for _ in range(int(rng.integers(1, 16))):
            action = engine.check()
            if action == Action.FLATTEN_NOW:
                flatten_days += 1
                break
            if action == Action.STOP_DAY:
                stop_days += 1
                break

            gross = float(rng.uniform(25.0, engine.config.daily_buffer))
            pnl = gross if rng.random() < 0.52 else -gross
            engine.on_fill(pnl)
            fills += 1

            min_margin = min(min_margin, engine.live_equity - engine.mll_floor)
            assert engine.live_equity > engine.mll_floor
            assert engine.check() != Action.DEAD

        engine.on_eod_close()
        min_margin = min(min_margin, engine.live_equity - engine.mll_floor)
        assert engine.peak_eod_balance >= engine.starting_balance
        assert engine.live_equity > engine.mll_floor
        assert engine.check() != Action.DEAD

    return {
        "days": days,
        "fills": fills,
        "final_balance": engine.live_equity,
        "mll_floor": engine.mll_floor,
        "min_margin_to_mll": min_margin,
        "stop_days": stop_days,
        "flatten_days": flatten_days,
    }


def test_random_days_cannot_touch_real_mll_when_engine_is_obeyed():
    result = obey_engine_for_random_days()
    print(
        "\n10k safety proof:",
        f"days={result['days']}",
        f"fills={result['fills']}",
        f"final_balance={result['final_balance']:.2f}",
        f"mll_floor={result['mll_floor']:.2f}",
        f"min_margin_to_mll={result['min_margin_to_mll']:.2f}",
        f"stop_days={result['stop_days']}",
        f"flatten_days={result['flatten_days']}",
    )
    assert result["min_margin_to_mll"] > 0.0


def test_green_day_protection_stops_before_giving_back_more_than_half():
    engine = PropRiskEngine()
    engine.on_fill(600.0)
    assert engine.check() == Action.OK

    engine.on_fill(-299.0)
    assert engine.check() == Action.OK

    engine.on_fill(-1.0)
    assert engine.daily_realized_pnl == 300.0
    assert engine.check() == Action.STOP_DAY


def test_eod_trailing_peak_and_mll_only_rise_until_lock():
    engine = PropRiskEngine()
    floors = [engine.mll_floor]
    peaks = [engine.peak_eod_balance]

    engine.on_fill(1_000.0)
    engine.on_eod_close()
    floors.append(engine.mll_floor)
    peaks.append(engine.peak_eod_balance)

    engine.on_fill(-500.0)
    engine.on_eod_close()
    floors.append(engine.mll_floor)
    peaks.append(engine.peak_eod_balance)

    engine.on_fill(1_500.0)
    engine.on_eod_close()
    floors.append(engine.mll_floor)
    peaks.append(engine.peak_eod_balance)

    engine.on_fill(2_000.0)
    engine.on_eod_close()
    floors.append(engine.mll_floor)
    peaks.append(engine.peak_eod_balance)

    assert peaks == sorted(peaks)
    assert floors == sorted(floors)
    assert floors == [48_000.0, 49_000.0, 49_000.0, 50_000.0, 50_000.0]
    assert engine.peak_eod_balance == 54_000.0


def test_allowed_size_caps_mes_mnq_full_stop_at_daily_buffer():
    engine = PropRiskEngine()
    stop_ticks = {
        "MES": 80,
        "MNQ": 200,
    }
    for symbol, tick_value in MICRO_TICKS.items():
        size = engine.allowed_size(tick_value=tick_value, stop_ticks=stop_ticks[symbol])
        full_stop_loss = size * tick_value * stop_ticks[symbol]
        next_contract_loss = (size + 1) * tick_value * stop_ticks[symbol]
        assert full_stop_loss <= engine.config.daily_buffer
        assert next_contract_loss > engine.config.daily_buffer


def simulate_pass_rate(
    daily_buffer: float,
    outcomes: np.ndarray,
    *,
    max_days: int = 80,
    trades_per_day: int = 8,
) -> float:
    passes = 0
    paths = outcomes.shape[0]
    cfg = replace(PropRiskConfig(), daily_buffer=float(daily_buffer))
    trade_risk = float(daily_buffer) / 4.0

    for path in range(paths):
        engine = PropRiskEngine(config=cfg)
        passed = False
        failed = False
        for day in range(max_days):
            if engine.live_equity >= engine.starting_balance + 3_000.0:
                passed = True
                break
            if engine.check() in {Action.DEAD, Action.FLATTEN_NOW}:
                failed = True
                break

            for trade in range(trades_per_day):
                action = engine.check()
                if action == Action.DEAD:
                    failed = True
                    break
                if action in {Action.FLATTEN_NOW, Action.STOP_DAY}:
                    break

                pnl = trade_risk if outcomes[path, day, trade] else -trade_risk
                engine.on_fill(pnl)

                if engine.live_equity >= engine.starting_balance + 3_000.0:
                    passed = True
                    break
                if engine.check() == Action.DEAD:
                    failed = True
                    break

            engine.on_eod_close()
            if passed or failed:
                break

        if passed:
            passes += 1

    return passes / paths


def test_daily_buffer_sweep_pass_rate(capsys):
    rng = np.random.default_rng(314159)
    outcomes = rng.random((10_000, 80, 8)) < 0.52
    buffers = [250, 325, 400, 600]
    rows = [(buffer, simulate_pass_rate(buffer, outcomes)) for buffer in buffers]
    best_buffer, best_rate = max(rows, key=lambda row: row[1])

    print("\nP(pass +3000 before -2000), fixed 52% 1:1 strategy")
    print("daily_buffer  pass_rate")
    for buffer, rate in rows:
        print(f"{buffer:12.0f}  {rate:.4%}")
    print(f"best_buffer={best_buffer:.0f} best_pass_rate={best_rate:.4%}")

    captured = capsys.readouterr()
    print(captured.out, end="")
    assert all(0.0 <= rate <= 1.0 for _, rate in rows)
    assert best_buffer in buffers
