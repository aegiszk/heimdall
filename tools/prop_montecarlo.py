"""Monte Carlo Lucid 50K FLEX prop challenge survival.

Measurement tool only. Strategy is intentionally trivial: independent trades
with configurable win rate and 1:R payoff. Risk state and sizing are delegated
to core.risk.prop_engine.
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.risk.prop_engine import Action, PropRiskConfig, PropRiskEngine


PLACEHOLDER_COMMISSION = 1.34
FAIL_DIED_MLL = "died_mll"
FAIL_NO_TARGET = "never_reached_target"
FAIL_TARGET_MIN_DAYS = "hit_target_failed_5_day_rule"
PASS = "pass"


@dataclass(frozen=True)
class SimParams:
    n_sims: int = 10_000
    seed: int = 20260702
    starting_balance: float = 50_000.0
    target_profit: float = 3_000.0
    max_days: int = 80
    min_trades_per_day: int = 3
    max_trades_per_day: int = 8
    win_rate: float = 0.52
    payoff: float = 1.0
    daily_buffer: float = 400.0
    kill_cushion: float = 400.0
    protect_green_at: float = 500.0
    min_profit_day: float = 150.0
    min_profit_days_required: int = 5
    tick_value: float = 1.25
    stop_ticks: float = 80.0
    commission_per_rt: float = PLACEHOLDER_COMMISSION
    eval_cost: float = 99.0
    payout_split: float = 0.80


@dataclass
class RunResult:
    outcome: str
    days: int
    profit_days: int
    final_balance: float
    trades: int
    stop_days: int
    flatten_days: int
    day_pnls: list[float]


@dataclass
class Aggregate:
    params: SimParams
    contracts: int
    gross_stop_loss: float
    net_win: float
    net_loss: float
    pass_rate: float
    fail_died_mll: float
    fail_no_target: float
    fail_target_min_days: float
    avg_final_balance: float
    avg_pass_balance: float
    avg_days: float
    avg_trades: float
    stop_day_rate: float
    flatten_day_rate: float
    flattened_runs: int
    daily_pnls: np.ndarray


def main() -> int:
    args = parse_args()
    params = SimParams(
        n_sims=args.n_sims,
        seed=args.seed,
        max_days=args.max_days,
        min_trades_per_day=args.min_trades_per_day,
        max_trades_per_day=args.max_trades_per_day,
        win_rate=args.win_rate,
        payoff=args.payoff,
        daily_buffer=args.daily_buffer,
        kill_cushion=args.kill_cushion,
        protect_green_at=args.protect_green_at,
        min_profit_day=args.min_profit_day,
        min_profit_days_required=args.min_profit_days_required,
        tick_value=args.tick_value,
        stop_ticks=args.stop_ticks,
        commission_per_rt=args.commission_per_rt,
        eval_cost=args.eval_cost,
        payout_split=args.payout_split,
    )

    if args.trade_pnls_file:
        trade_pnls = load_trade_pnls(Path(args.trade_pnls_file), args.trade_pnl_column)
        daily_counts = parse_daily_counts(args.daily_counts)
        empirical = run_empirical_many(params, trade_pnls, daily_counts)
        print_empirical_assumptions(params, args.trade_pnls_file, args.trade_pnl_column, daily_counts)
        print_empirical_result(empirical, params)
        return 0

    if args.commission_per_rt == PLACEHOLDER_COMMISSION:
        print("COMMISSION WARNING: commission_per_rt=$1.34 is a MES placeholder until the real Lucid RT fee is supplied.")
    print_assumptions(params)
    print()

    base = run_many(params)
    print_contract_sizing(base)
    print_daily_stats(base)
    print_fail_breakdown(base)
    print()

    grid = []
    for win_rate in args.win_rate_sweep:
        row = []
        for daily_buffer in args.daily_buffer_sweep:
            cell_params = replace_params(
                params,
                win_rate=win_rate,
                daily_buffer=daily_buffer,
                seed=params.seed + int(round(win_rate * 10_000)) + int(daily_buffer) * 31,
            )
            row.append(run_many(cell_params))
        grid.append((win_rate, row))

    print_pass_grid(args.daily_buffer_sweep, grid)
    print()
    print_ev_table(args.daily_buffer_sweep, grid, params)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate true net Lucid 50K FLEX pass rate.")
    parser.add_argument("--n-sims", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260702)
    parser.add_argument("--max-days", type=int, default=80, help="Challenge horizon assumption in trading days.")
    parser.add_argument("--min-trades-per-day", type=int, default=3)
    parser.add_argument("--max-trades-per-day", type=int, default=8)
    parser.add_argument("--win-rate", type=float, default=0.52)
    parser.add_argument("--payoff", type=float, default=1.0)
    parser.add_argument("--daily-buffer", type=float, default=400.0)
    parser.add_argument("--kill-cushion", type=float, default=400.0)
    parser.add_argument("--protect-green-at", type=float, default=500.0)
    parser.add_argument("--min-profit-day", type=float, default=150.0)
    parser.add_argument("--min-profit-days-required", type=int, default=5)
    parser.add_argument("--tick-value", type=float, default=1.25, help="MES tick value placeholder.")
    parser.add_argument("--stop-ticks", type=float, default=80.0)
    parser.add_argument("--commission-per-rt", type=float, default=PLACEHOLDER_COMMISSION)
    parser.add_argument("--eval-cost", type=float, default=99.0)
    parser.add_argument("--payout-split", type=float, default=0.80)
    parser.add_argument("--win-rate-sweep", nargs="+", type=float, default=[0.50, 0.52, 0.55, 0.58])
    parser.add_argument("--daily-buffer-sweep", nargs="+", type=float, default=[325.0, 400.0, 500.0])
    parser.add_argument("--trade-pnls-file", default=None, help="CSV of empirical net trade PnLs; enables empirical mode.")
    parser.add_argument("--trade-pnl-column", default="pnl")
    parser.add_argument(
        "--daily-counts",
        default=None,
        help="Observed daily trade-count distribution as count:frequency pairs, e.g. '0:1,2:48'.",
    )
    return parser.parse_args()


def run_many(params: SimParams) -> Aggregate:
    rng = np.random.default_rng(params.seed)
    results = [simulate_challenge(rng, params) for _ in range(params.n_sims)]
    contracts, gross_stop, net_win, net_loss = trade_shape(params)
    outcomes = [result.outcome for result in results]
    passes = [result for result in results if result.outcome == PASS]
    final_balances = np.array([result.final_balance for result in results], dtype=float)
    daily_pnls = np.array([pnl for result in results for pnl in result.day_pnls], dtype=float)
    total_days = sum(result.days for result in results)
    stop_days = sum(result.stop_days for result in results)
    flatten_days = sum(result.flatten_days for result in results)
    flattened_runs = sum(1 for result in results if result.flatten_days > 0 and result.outcome != PASS)

    return Aggregate(
        params=params,
        contracts=contracts,
        gross_stop_loss=gross_stop,
        net_win=net_win,
        net_loss=net_loss,
        pass_rate=outcomes.count(PASS) / params.n_sims,
        fail_died_mll=outcomes.count(FAIL_DIED_MLL) / params.n_sims,
        fail_no_target=outcomes.count(FAIL_NO_TARGET) / params.n_sims,
        fail_target_min_days=outcomes.count(FAIL_TARGET_MIN_DAYS) / params.n_sims,
        avg_final_balance=float(np.mean(final_balances)),
        avg_pass_balance=safe_mean([result.final_balance for result in passes]),
        avg_days=safe_mean([result.days for result in results]),
        avg_trades=safe_mean([result.trades for result in results]),
        stop_day_rate=stop_days / total_days if total_days else 0.0,
        flatten_day_rate=flatten_days / total_days if total_days else 0.0,
        flattened_runs=flattened_runs,
        daily_pnls=daily_pnls,
    )


def simulate_challenge(rng: np.random.Generator, params: SimParams) -> RunResult:
    cfg = PropRiskConfig(
        daily_buffer=params.daily_buffer,
        kill_cushion=params.kill_cushion,
        protect_green_at=params.protect_green_at,
        min_profit_day=params.min_profit_day,
    )
    engine = PropRiskEngine(starting_balance=params.starting_balance, config=cfg)
    _, _, net_win, net_loss = trade_shape(params)
    target_balance = params.starting_balance + params.target_profit

    profit_days = 0
    trades = 0
    stop_days = 0
    flatten_days = 0
    day_pnls: list[float] = []

    for day in range(1, params.max_days + 1):
        pre_action = engine.check()
        if pre_action == Action.DEAD:
            return RunResult(FAIL_DIED_MLL, day, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)
        if pre_action == Action.FLATTEN_NOW:
            flatten_days += 1
            return RunResult(FAIL_NO_TARGET, day, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)

        requested_trades = int(rng.integers(params.min_trades_per_day, params.max_trades_per_day + 1))
        died = False
        for _ in range(requested_trades):
            action = engine.check()
            if action == Action.DEAD:
                died = True
                break
            if action == Action.FLATTEN_NOW:
                flatten_days += 1
                break
            if action == Action.STOP_DAY:
                stop_days += 1
                break

            pnl = net_win if rng.random() < params.win_rate else net_loss
            engine.on_fill(pnl)
            trades += 1

            post_action = engine.check()
            if post_action == Action.DEAD:
                died = True
                break
            if post_action == Action.FLATTEN_NOW:
                flatten_days += 1
                break
            if post_action == Action.STOP_DAY:
                stop_days += 1
                break

        day_pnl = engine.daily_realized_pnl
        day_pnls.append(day_pnl)
        if day_pnl >= params.min_profit_day:
            profit_days += 1

        if died:
            return RunResult(FAIL_DIED_MLL, day, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)

        if engine.live_equity >= target_balance:
            outcome = PASS if profit_days >= params.min_profit_days_required else FAIL_TARGET_MIN_DAYS
            return RunResult(outcome, day, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)

        engine.on_eod_close()
        if engine.check() == Action.DEAD:
            return RunResult(FAIL_DIED_MLL, day, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)

    return RunResult(FAIL_NO_TARGET, params.max_days, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)


def run_empirical_many(params: SimParams, trade_pnls: np.ndarray, daily_counts: np.ndarray | None) -> Aggregate:
    rng = np.random.default_rng(params.seed)
    results = [simulate_empirical_challenge(rng, params, trade_pnls, daily_counts) for _ in range(params.n_sims)]
    outcomes = [result.outcome for result in results]
    passes = [result for result in results if result.outcome == PASS]
    final_balances = np.array([result.final_balance for result in results], dtype=float)
    daily_pnls = np.array([pnl for result in results for pnl in result.day_pnls], dtype=float)
    total_days = sum(result.days for result in results)
    stop_days = sum(result.stop_days for result in results)
    flatten_days = sum(result.flatten_days for result in results)
    flattened_runs = sum(1 for result in results if result.flatten_days > 0 and result.outcome != PASS)

    return Aggregate(
        params=params,
        contracts=1,
        gross_stop_loss=0.0,
        net_win=safe_mean(trade_pnls[trade_pnls > 0]),
        net_loss=safe_mean(trade_pnls[trade_pnls < 0]),
        pass_rate=outcomes.count(PASS) / params.n_sims,
        fail_died_mll=outcomes.count(FAIL_DIED_MLL) / params.n_sims,
        fail_no_target=outcomes.count(FAIL_NO_TARGET) / params.n_sims,
        fail_target_min_days=outcomes.count(FAIL_TARGET_MIN_DAYS) / params.n_sims,
        avg_final_balance=float(np.mean(final_balances)),
        avg_pass_balance=safe_mean([result.final_balance for result in passes]),
        avg_days=safe_mean([result.days for result in results]),
        avg_trades=safe_mean([result.trades for result in results]),
        stop_day_rate=stop_days / total_days if total_days else 0.0,
        flatten_day_rate=flatten_days / total_days if total_days else 0.0,
        flattened_runs=flattened_runs,
        daily_pnls=daily_pnls,
    )


def simulate_empirical_challenge(
    rng: np.random.Generator,
    params: SimParams,
    trade_pnls: np.ndarray,
    daily_counts: np.ndarray | None,
) -> RunResult:
    cfg = PropRiskConfig(
        daily_buffer=params.daily_buffer,
        kill_cushion=params.kill_cushion,
        protect_green_at=params.protect_green_at,
        min_profit_day=params.min_profit_day,
    )
    engine = PropRiskEngine(starting_balance=params.starting_balance, config=cfg)
    target_balance = params.starting_balance + params.target_profit
    profit_days = 0
    trades = 0
    stop_days = 0
    flatten_days = 0
    day_pnls: list[float] = []

    for day in range(1, params.max_days + 1):
        if engine.check() == Action.DEAD:
            return RunResult(FAIL_DIED_MLL, day, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)
        if daily_counts is None:
            requested_trades = int(rng.integers(params.min_trades_per_day, params.max_trades_per_day + 1))
        else:
            requested_trades = int(rng.choice(daily_counts))

        died = False
        for _ in range(requested_trades):
            action = engine.check()
            if action == Action.DEAD:
                died = True
                break
            if action == Action.FLATTEN_NOW:
                flatten_days += 1
                break
            if action == Action.STOP_DAY:
                stop_days += 1
                break

            engine.on_fill(float(rng.choice(trade_pnls)))
            trades += 1

            post_action = engine.check()
            if post_action == Action.DEAD:
                died = True
                break
            if post_action == Action.FLATTEN_NOW:
                flatten_days += 1
                break
            if post_action == Action.STOP_DAY:
                stop_days += 1
                break

        day_pnl = engine.daily_realized_pnl
        day_pnls.append(day_pnl)
        if day_pnl >= params.min_profit_day:
            profit_days += 1
        if died:
            return RunResult(FAIL_DIED_MLL, day, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)
        if engine.live_equity >= target_balance:
            outcome = PASS if profit_days >= params.min_profit_days_required else FAIL_TARGET_MIN_DAYS
            return RunResult(outcome, day, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)

        engine.on_eod_close()
        if engine.check() == Action.DEAD:
            return RunResult(FAIL_DIED_MLL, day, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)

    return RunResult(FAIL_NO_TARGET, params.max_days, profit_days, engine.live_equity, trades, stop_days, flatten_days, day_pnls)


def trade_shape(params: SimParams) -> tuple[int, float, float, float]:
    cfg = PropRiskConfig(
        daily_buffer=params.daily_buffer,
        kill_cushion=params.kill_cushion,
        protect_green_at=params.protect_green_at,
        min_profit_day=params.min_profit_day,
    )
    engine = PropRiskEngine(starting_balance=params.starting_balance, config=cfg)
    contracts = engine.allowed_size(params.tick_value, params.stop_ticks)
    if contracts <= 0:
        raise ValueError("allowed_size returned 0 contracts; lower stop_ticks or raise daily_buffer")
    gross_stop = contracts * params.tick_value * params.stop_ticks
    commission = contracts * params.commission_per_rt
    net_win = gross_stop * params.payoff - commission
    net_loss = -gross_stop - commission
    return contracts, gross_stop, net_win, net_loss


def print_assumptions(params: SimParams) -> None:
    print("Lucid 50K FLEX Monte Carlo assumptions")
    print(f"sims={params.n_sims} seed={params.seed} horizon_days={params.max_days}")
    print(f"target_profit=${params.target_profit:.2f} max_loss_limit=$2000 EOD-trailing min_profit_days={params.min_profit_days_required}x >=${params.min_profit_day:.2f}")
    print(f"trades_per_day={params.min_trades_per_day}-{params.max_trades_per_day} win_rate={params.win_rate:.2%} payoff={params.payoff:.2f}:1")
    print(f"daily_buffer=${params.daily_buffer:.2f} kill_cushion=${params.kill_cushion:.2f} protect_green_at=${params.protect_green_at:.2f}")
    print(f"tick_value=${params.tick_value:.2f} stop_ticks={params.stop_ticks:.1f} commission_per_rt=${params.commission_per_rt:.2f} per contract")
    print(f"EV assumes eval_cost=${params.eval_cost:.2f}, payout_split={params.payout_split:.0%}, payout_on_pass=${params.target_profit * params.payout_split:.2f}")


def print_empirical_assumptions(
    params: SimParams,
    trade_pnls_file: str,
    trade_pnl_column: str,
    daily_counts: np.ndarray | None,
) -> None:
    print("Lucid 50K FLEX Monte Carlo assumptions")
    print(f"mode=empirical_trade_distribution file={trade_pnls_file} pnl_column={trade_pnl_column}")
    print(f"sims={params.n_sims} seed={params.seed} horizon_days={params.max_days}")
    print(f"target_profit=${params.target_profit:.2f} max_loss_limit=$2000 EOD-trailing min_profit_days={params.min_profit_days_required}x >=${params.min_profit_day:.2f}")
    print(f"daily_buffer=${params.daily_buffer:.2f} kill_cushion=${params.kill_cushion:.2f} protect_green_at=${params.protect_green_at:.2f}")
    print(f"daily_trade_counts={daily_count_summary(daily_counts) if daily_counts is not None else 'synthetic min/max args'}")
    print(f"EV assumes eval_cost=${params.eval_cost:.2f}, payout_split={params.payout_split:.0%}, payout_on_pass=${params.target_profit * params.payout_split:.2f}")


def print_empirical_result(agg: Aggregate, params: SimParams) -> None:
    print("Empirical trade distribution")
    print(f"avg_win=${agg.net_win:.2f} avg_loss=${agg.net_loss:.2f}")
    print_daily_stats(agg)
    print_fail_breakdown(agg)
    payout = params.target_profit * params.payout_split
    print(f"EV_per_eval=${ev_per_eval(agg.pass_rate, payout, params.eval_cost):.2f}")


def print_contract_sizing(agg: Aggregate) -> None:
    print("Sizing")
    print(f"contracts={agg.contracts} gross_full_stop=${agg.gross_stop_loss:.2f} net_win=${agg.net_win:.2f} net_loss=${agg.net_loss:.2f}")


def print_daily_stats(agg: Aggregate) -> None:
    pnls = agg.daily_pnls
    print("Daily PnL stats, net of commissions")
    print(
        f"days_sampled={len(pnls)} mean=${np.mean(pnls):.2f} std=${np.std(pnls, ddof=1):.2f} "
        f"p05=${np.quantile(pnls, 0.05):.2f} median=${np.median(pnls):.2f} p95=${np.quantile(pnls, 0.95):.2f}"
    )
    print(
        f"green_days={(pnls > 0).mean():.2%} min_profit_days={(pnls >= agg.params.min_profit_day).mean():.2%} "
        f"stop_day_rate={agg.stop_day_rate:.2%} flatten_day_rate={agg.flatten_day_rate:.2%} flattened_runs={agg.flattened_runs}"
    )


def print_fail_breakdown(agg: Aggregate) -> None:
    print("True challenge result")
    print(f"pass_rate={agg.pass_rate:.4%}")
    print(f"fail_died_mll={agg.fail_died_mll:.4%}")
    print(f"fail_never_reached_target={agg.fail_no_target:.4%}")
    print(f"fail_hit_target_but_failed_5_day_rule={agg.fail_target_min_days:.4%}")
    print(f"avg_days={agg.avg_days:.2f} avg_trades={agg.avg_trades:.2f} avg_final_balance=${agg.avg_final_balance:.2f} avg_pass_balance=${agg.avg_pass_balance:.2f}")


def print_pass_grid(buffers: list[float], grid: list[tuple[float, list[Aggregate]]]) -> None:
    rows = [["win_rate"] + [f"buf_{fmt_buffer(buffer)}" for buffer in buffers]]
    for win_rate, aggs in grid:
        rows.append([f"{win_rate:.2%}"] + [f"{agg.pass_rate:.4%}" for agg in aggs])
    print("True PASS-rate grid, all rules enforced")
    print_table(rows)


def print_ev_table(buffers: list[float], grid: list[tuple[float, list[Aggregate]]], params: SimParams) -> None:
    payout = params.target_profit * params.payout_split
    threshold = params.eval_cost / (payout + params.eval_cost)
    rows = [["win_rate", "best_buffer", "best_pass_rate", "best_ev_per_eval"]]
    positive_rates: list[float] = []
    for win_rate, aggs in grid:
        evs = [ev_per_eval(agg.pass_rate, payout, params.eval_cost) for agg in aggs]
        best_idx = int(np.argmax(evs))
        if evs[best_idx] > 0:
            positive_rates.append(win_rate)
        rows.append(
            [
                f"{win_rate:.2%}",
                fmt_buffer(buffers[best_idx]),
                f"{aggs[best_idx].pass_rate:.4%}",
                f"${evs[best_idx]:.2f}",
            ]
        )

    print("EV table")
    print(f"assumption: avg payout after split = target_profit * payout_split = ${payout:.2f}; eval_cost=${params.eval_cost:.2f}")
    print(f"breakeven_pass_rate={threshold:.4%}")
    print_table(rows)
    if positive_rates:
        print(f"min_win_rate_positive_ev_in_sweep={min(positive_rates):.2%}")
    else:
        print("min_win_rate_positive_ev_in_sweep=none")


def ev_per_eval(pass_rate: float, payout: float, eval_cost: float) -> float:
    return pass_rate * payout - (1.0 - pass_rate) * eval_cost


def replace_params(params: SimParams, **updates) -> SimParams:
    values = params.__dict__.copy()
    values.update(updates)
    return SimParams(**values)


def safe_mean(values) -> float:
    arr = np.asarray(list(values), dtype=float)
    return float(np.mean(arr)) if len(arr) else 0.0


def fmt_buffer(buffer: float) -> str:
    return str(int(buffer)) if float(buffer).is_integer() else f"{buffer:.2f}"


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(cell).rjust(widths[i]) for i, cell in enumerate(row)))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


def load_trade_pnls(path: Path, column: str) -> np.ndarray:
    values: list[float] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or column not in reader.fieldnames:
            raise ValueError(f"{path} must contain column {column!r}")
        for row in reader:
            values.append(float(row[column]))
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        raise ValueError(f"{path} contains no finite trade PnLs in column {column!r}")
    return arr


def parse_daily_counts(value: str | None) -> np.ndarray | None:
    if not value:
        return None
    counts: list[int] = []
    for part in value.split(","):
        count_s, freq_s = part.split(":", 1)
        count = int(count_s)
        freq = int(freq_s)
        if count < 0 or freq < 0:
            raise ValueError("daily-count pairs must be non-negative")
        counts.extend([count] * freq)
    if not counts:
        raise ValueError("daily-counts produced an empty distribution")
    return np.asarray(counts, dtype=int)


def daily_count_summary(counts: np.ndarray | None) -> str:
    if counts is None:
        return "none"
    unique, freq = np.unique(counts, return_counts=True)
    return "{" + ", ".join(f"{int(k)}:{int(v)}" for k, v in zip(unique, freq)) + "}"


if __name__ == "__main__":
    sys.exit(main())
