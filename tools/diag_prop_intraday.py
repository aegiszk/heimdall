"""Measure a simple intraday futures setup and prop-account survival on real data.

Source: Yahoo Finance chart data via yfinance for CME micro futures proxies:
MES=F and MNQ=F. Yahoo currently limits 5-minute futures history to the last
60 days; the tool prints a coverage failure when the requested 18-month minimum
is not met.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.risk.prop_engine import Action, PropRiskConfig, PropRiskEngine


EASTERN = ZoneInfo("America/New_York")
DATA_DIR = ROOT / "data"
COMMISSION_RT = 1.00
TARGET_PROFIT = 3_000.0
STARTING_BALANCE = 50_000.0
EVAL_COST = 99.0
PAYOUT_SPLIT = 0.80
MIN_PROFIT_DAY = 150.0
MIN_PROFIT_DAYS_REQUIRED = 5


@dataclass(frozen=True)
class Contract:
    name: str
    yahoo: str
    tick_size: float
    tick_value: float

    @property
    def point_value(self) -> float:
        return self.tick_value / self.tick_size


CONTRACTS = (
    Contract("MES", "MES=F", 0.25, 1.25),
    Contract("MNQ", "MNQ=F", 0.25, 0.50),
)


@dataclass
class Trade:
    symbol: str
    session: pd.Timestamp
    entry_ts: pd.Timestamp
    exit_ts: pd.Timestamp
    side: str
    entry: float
    exit: float
    stop: float
    target: float
    pnl: float
    r_mult: float
    exit_reason: str


@dataclass
class PropResult:
    outcome: str
    days: int
    profit_days: int
    final_balance: float
    trades: int
    stop_days: int
    flatten_days: int


def main() -> int:
    args = parse_args()
    frames = {contract.name: load_yahoo_5m(contract, args.period) for contract in CONTRACTS}
    print_step0(frames, args.period)

    coverage_ok = all(coverage_months(df) >= args.min_months for df in frames.values())
    gaps_ok = all(sanity_stats(df)["missing_pct"] <= 1.0 for df in frames.values())
    if not coverage_ok:
        print(f"COVERAGE_STATUS: FAIL (<{args.min_months:.0f} months; Yahoo 5m futures data is capped near 60 days)")
    if not gaps_ok:
        print("GAP_STATUS: FAIL (>1% expected ETH 5-minute bars missing)")
    if (not coverage_ok or not gaps_ok) and not args.continue_on_coverage_fail:
        print("STOP: mandatory data sanity failed; rerun with --continue-on-coverage-fail for exploratory stats only.")
        return 1

    trades = []
    skipped = {}
    for contract in CONTRACTS:
        contract_trades, symbol_skipped = simulate_orb(frames[contract.name], contract)
        trades.extend(contract_trades)
        skipped[contract.name] = symbol_skipped

    trades_df = trades_to_frame(trades)
    out_path = DATA_DIR / "prop_orb_trade_pnls_yahoo_5m.csv"
    trades_df.to_csv(out_path, index=False)

    print_step1_rules()
    print_step2_costs()
    print_step3_distribution(trades_df, skipped, out_path)
    print_prop_mc(trades_df, frames, args)
    return 0 if coverage_ok and gaps_ok else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure MES/MNQ ORB tails and prop survival.")
    parser.add_argument("--period", default="60d", help="Yahoo period. 5m futures data is limited to about 60d.")
    parser.add_argument("--min-months", type=float, default=18.0)
    parser.add_argument("--continue-on-coverage-fail", action="store_true")
    parser.add_argument("--n-sims", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260702)
    parser.add_argument("--max-days", type=int, default=80)
    parser.add_argument("--daily-buffer", type=float, default=325.0)
    return parser.parse_args()


def load_yahoo_5m(contract: Contract, period: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("yfinance is required for Yahoo futures data. Install it in .venv.") from exc

    df = yf.download(
        contract.yahoo,
        period=period,
        interval="5m",
        progress=False,
        auto_adjust=False,
        prepost=True,
        threads=False,
    )
    if df.empty:
        raise RuntimeError(f"Yahoo returned no rows for {contract.yahoo} period={period} interval=5m")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [column[0] for column in df.columns]
    out = df.rename(columns=str.lower).loc[:, ["open", "high", "low", "close", "volume"]].copy()
    out.index = pd.DatetimeIndex(out.index)
    if out.index.tz is None:
        out.index = out.index.tz_localize("UTC")
    out.index = out.index.tz_convert(EASTERN)
    out = out[~out.index.duplicated(keep="last")].sort_index()
    for column in out.columns:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(DATA_DIR / f"yahoo_{contract.name}_5m.parquet")
    return out


def print_step0(frames: dict[str, pd.DataFrame], period: str) -> None:
    print("STEP 0 DATA SANITY")
    print("source=Yahoo Finance via yfinance")
    for contract in CONTRACTS:
        print(
            "endpoint="
            f"https://query2.finance.yahoo.com/v8/finance/chart/{contract.yahoo}"
            f"?range={period}&interval=5m&includePrePost=true&events=history"
        )
    print("ETH session assumption: CME equity index futures trade Sun 18:00-Fri 17:00 ET with daily 17:00-18:00 ET break.")
    print("RTH strategy session: Mon-Fri 09:30-16:00 ET; opening range is 09:30-10:00 ET.")
    rows = [[
        "symbol",
        "rows",
        "start_et",
        "end_et",
        "months",
        "missing_eth_bars",
        "missing_pct",
        "nan_open",
        "nan_high",
        "nan_low",
        "nan_close",
        "nan_volume",
    ]]
    for symbol, df in frames.items():
        s = sanity_stats(df)
        rows.append([
            symbol,
            str(len(df)),
            df.index[0].isoformat(),
            df.index[-1].isoformat(),
            f"{coverage_months(df):.2f}",
            str(s["missing_bars"]),
            f"{s['missing_pct']:.2f}%",
            str(int(df["open"].isna().sum())),
            str(int(df["high"].isna().sum())),
            str(int(df["low"].isna().sum())),
            str(int(df["close"].isna().sum())),
            str(int(df["volume"].isna().sum())),
        ])
    print_table(rows)
    for symbol, df in frames.items():
        print(f"{symbol} min/max:")
        for column in ["open", "high", "low", "close", "volume"]:
            print(f"  {column}: min={df[column].min():.4f} max={df[column].max():.4f}")
    print()


def sanity_stats(df: pd.DataFrame) -> dict[str, float]:
    expected = expected_eth_index(df.index[0], df.index[-1])
    missing = expected.difference(df.index)
    missing_bars = int(len(missing))
    missing_pct = 100.0 * missing_bars / max(len(df), 1)
    return {"missing_bars": missing_bars, "missing_pct": missing_pct}


def expected_eth_index(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    grid = pd.date_range(start.floor("5min"), end.ceil("5min"), freq="5min", tz=EASTERN)
    return pd.DatetimeIndex([ts for ts in grid if is_eth_open_bar(ts)])


def is_eth_open_bar(ts: pd.Timestamp) -> bool:
    weekday = ts.weekday()
    clock = ts.time()
    if weekday == 5:
        return False
    if weekday == 6:
        return clock >= time(18, 0)
    if weekday == 4 and clock > time(17, 0):
        return False
    if time(17, 5) <= clock < time(18, 0):
        return False
    return True


def coverage_months(df: pd.DataFrame) -> float:
    return (df.index[-1] - df.index[0]).total_seconds() / (86400.0 * 30.4375)


def print_step1_rules() -> None:
    print("STEP 1 STRATEGY RULES")
    print("entry=30-minute RTH opening-range breakout; one trade max per symbol per day")
    print("long if post-10:00 bar breaks OR high; short if it breaks OR low; ambiguous same-bar dual break is skipped")
    print("stop=opposite side of opening range; target=1.0R fixed; exit any open trade at RTH close")
    print()


def print_step2_costs() -> None:
    print("STEP 2 COST MODEL")
    print("commission=$1.00 round-trip per micro contract")
    print("market entry=1 tick adverse; stop=1 tick adverse minimum; gap-through stop fills at gap open if worse")
    print("target exits are limit fills at target; RTH close exits are market exits with 1 tick adverse")
    print()


def simulate_orb(df: pd.DataFrame, contract: Contract) -> tuple[list[Trade], dict[str, int]]:
    trades: list[Trade] = []
    skipped = {"no_rth": 0, "no_opening_range": 0, "ambiguous_break": 0, "no_break": 0}
    for session, day in df.groupby(df.index.date):
        rth = day.between_time("09:30", "16:00", inclusive="both")
        if rth.empty:
            skipped["no_rth"] += 1
            continue
        opening = rth.between_time("09:30", "10:00", inclusive="right")
        after = rth.between_time("10:05", "16:00", inclusive="both")
        if opening.empty or after.empty:
            skipped["no_opening_range"] += 1
            continue
        or_high = float(opening["high"].max())
        or_low = float(opening["low"].min())
        trade = first_orb_trade(contract, pd.Timestamp(session, tz=EASTERN), after, or_high, or_low)
        if trade is None:
            skipped["no_break"] += 1
        elif trade == "ambiguous":
            skipped["ambiguous_break"] += 1
        else:
            trades.append(trade)
    return trades, skipped


def first_orb_trade(
    contract: Contract,
    session: pd.Timestamp,
    bars: pd.DataFrame,
    or_high: float,
    or_low: float,
) -> Trade | str | None:
    for i, (ts, row) in enumerate(bars.iterrows()):
        breaks_high = float(row["high"]) >= or_high
        breaks_low = float(row["low"]) <= or_low
        if breaks_high and breaks_low:
            return "ambiguous"
        if breaks_high:
            entry = max(float(row["open"]), or_high) + contract.tick_size
            stop = or_low
            risk_points = entry - stop
            if risk_points <= 0:
                return None
            target = entry + risk_points
            return manage_trade(contract, session, ts, "long", entry, stop, target, bars.iloc[i:])
        if breaks_low:
            entry = min(float(row["open"]), or_low) - contract.tick_size
            stop = or_high
            risk_points = stop - entry
            if risk_points <= 0:
                return None
            target = entry - risk_points
            return manage_trade(contract, session, ts, "short", entry, stop, target, bars.iloc[i:])
    return None


def manage_trade(
    contract: Contract,
    session: pd.Timestamp,
    entry_ts: pd.Timestamp,
    side: str,
    entry: float,
    stop: float,
    target: float,
    bars: pd.DataFrame,
) -> Trade:
    exit_price = float(bars.iloc[-1]["close"])
    exit_ts = bars.index[-1]
    reason = "rth_close"
    for ts, row in bars.iterrows():
        open_ = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        if side == "long":
            if open_ <= stop:
                exit_price = min(open_, stop - contract.tick_size)
                exit_ts = ts
                reason = "gap_stop"
                break
            if low <= stop:
                exit_price = stop - contract.tick_size
                exit_ts = ts
                reason = "stop"
                break
            if high >= target:
                exit_price = target
                exit_ts = ts
                reason = "target"
                break
        else:
            if open_ >= stop:
                exit_price = max(open_, stop + contract.tick_size)
                exit_ts = ts
                reason = "gap_stop"
                break
            if high >= stop:
                exit_price = stop + contract.tick_size
                exit_ts = ts
                reason = "stop"
                break
            if low <= target:
                exit_price = target
                exit_ts = ts
                reason = "target"
                break

    if reason == "rth_close":
        close = float(bars.iloc[-1]["close"])
        exit_price = close - contract.tick_size if side == "long" else close + contract.tick_size

    gross = (
        (exit_price - entry) * contract.point_value
        if side == "long"
        else (entry - exit_price) * contract.point_value
    )
    pnl = gross - COMMISSION_RT
    initial_risk = abs(entry - stop) * contract.point_value
    r_mult = pnl / initial_risk if initial_risk else 0.0
    return Trade(
        symbol=contract.name,
        session=session,
        entry_ts=entry_ts,
        exit_ts=exit_ts,
        side=side,
        entry=entry,
        exit=exit_price,
        stop=stop,
        target=target,
        pnl=float(pnl),
        r_mult=float(r_mult),
        exit_reason=reason,
    )


def trades_to_frame(trades: Iterable[Trade]) -> pd.DataFrame:
    return pd.DataFrame([trade.__dict__ for trade in trades])


def print_step3_distribution(trades: pd.DataFrame, skipped: dict[str, dict[str, int]], out_path: Path) -> None:
    print("STEP 3 TRADE DISTRIBUTION")
    print(f"saved_trade_distribution={out_path}")
    print(f"skipped_days={skipped}")
    if trades.empty:
        print("No trades generated.")
        return
    pnl = trades["pnl"].to_numpy(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    avg_win = safe_mean(wins)
    avg_loss = safe_mean(losses)
    rr = avg_win / abs(avg_loss) if avg_loss < 0 else 0.0
    rows = [[
        "scope",
        "trades",
        "win_rate",
        "avg_win",
        "avg_loss",
        "realized_rr",
        "mean_pnl",
        "median_pnl",
        "skew",
        "kurtosis",
        "max_consec_losses",
    ]]
    rows.append([
        "ALL",
        str(len(trades)),
        f"{(pnl > 0).mean() * 100:.2f}%",
        money(avg_win),
        money(avg_loss),
        f"{rr:.3f}",
        money(float(np.mean(pnl))),
        money(float(np.median(pnl))),
        f"{finite(stats.skew(pnl, bias=False)):.3f}",
        f"{finite(stats.kurtosis(pnl, fisher=True, bias=False)):.3f}",
        str(max_consecutive_losses(trades.sort_values("exit_ts")["pnl"].to_numpy(float))),
    ])
    for symbol, group in trades.groupby("symbol"):
        gpnl = group["pnl"].to_numpy(float)
        gwins = gpnl[gpnl > 0]
        glosses = gpnl[gpnl < 0]
        g_avg_win = safe_mean(gwins)
        g_avg_loss = safe_mean(glosses)
        g_rr = g_avg_win / abs(g_avg_loss) if g_avg_loss < 0 else 0.0
        rows.append([
            symbol,
            str(len(group)),
            f"{(gpnl > 0).mean() * 100:.2f}%",
            money(g_avg_win),
            money(g_avg_loss),
            f"{g_rr:.3f}",
            money(float(np.mean(gpnl))),
            money(float(np.median(gpnl))),
            f"{finite(stats.skew(gpnl, bias=False)):.3f}",
            f"{finite(stats.kurtosis(gpnl, fisher=True, bias=False)):.3f}",
            str(max_consecutive_losses(group.sort_values("exit_ts")["pnl"].to_numpy(float))),
        ])
    print_table(rows)
    print("Worst 5 trades")
    worst = trades.sort_values("pnl").head(5)
    print_table([
        ["symbol", "session", "side", "entry_ts", "exit_ts", "entry", "exit", "pnl", "r_mult", "exit_reason"],
        *[
            [
                row.symbol,
                pd.Timestamp(row.session).date().isoformat(),
                row.side,
                pd.Timestamp(row.entry_ts).isoformat(),
                pd.Timestamp(row.exit_ts).isoformat(),
                f"{row.entry:.2f}",
                f"{row.exit:.2f}",
                money(row.pnl),
                f"{row.r_mult:.3f}",
                row.exit_reason,
            ]
            for row in worst.itertuples(index=False)
        ],
    ])
    print()


def print_prop_mc(trades: pd.DataFrame, frames: dict[str, pd.DataFrame], args: argparse.Namespace) -> None:
    print("PROP MONTE CARLO WITH REAL TRADE DISTRIBUTION")
    if trades.empty:
        print("No trades; pass_rate=0.0000% EV=-$99.00")
        return
    daily_counts = observed_daily_trade_counts(trades, frames)
    results = run_empirical_prop_mc(
        trades["pnl"].to_numpy(float),
        daily_counts,
        n_sims=args.n_sims,
        seed=args.seed,
        max_days=args.max_days,
        daily_buffer=args.daily_buffer,
    )
    outcomes = [result.outcome for result in results]
    pass_rate = outcomes.count("pass") / len(outcomes)
    payout = TARGET_PROFIT * PAYOUT_SPLIT
    ev = pass_rate * payout - (1.0 - pass_rate) * EVAL_COST
    final = np.array([result.final_balance for result in results], dtype=float)
    print(f"lucid=50K FLEX buffer=${args.daily_buffer:.2f} sims={args.n_sims} max_days={args.max_days}")
    print(f"trade_sampling=empirical one-contract ORB pnl with observed daily trade-count distribution {daily_count_summary(daily_counts)}")
    print(f"pass_rate={pass_rate:.4%}")
    print(f"EV_per_eval=${ev:.2f} using eval_cost=${EVAL_COST:.2f}, payout_after_split=${payout:.2f}")
    print(f"fail_died_mll={outcomes.count('died_mll') / len(outcomes):.4%}")
    print(f"fail_never_reached_target={outcomes.count('never_reached_target') / len(outcomes):.4%}")
    print(f"fail_target_failed_5_day_rule={outcomes.count('hit_target_failed_5_day_rule') / len(outcomes):.4%}")
    print(f"avg_final_balance=${np.mean(final):.2f}")
    print()


def observed_daily_trade_counts(trades: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> np.ndarray:
    days = sorted({idx.date() for df in frames.values() for idx in df.between_time("09:30", "16:00").index})
    counts = trades.groupby(pd.to_datetime(trades["session"]).dt.date).size()
    return np.array([int(counts.get(day, 0)) for day in days], dtype=int)


def run_empirical_prop_mc(
    trade_pnls: np.ndarray,
    daily_counts: np.ndarray,
    *,
    n_sims: int,
    seed: int,
    max_days: int,
    daily_buffer: float,
) -> list[PropResult]:
    rng = np.random.default_rng(seed)
    return [
        simulate_empirical_challenge(rng, trade_pnls, daily_counts, max_days=max_days, daily_buffer=daily_buffer)
        for _ in range(n_sims)
    ]


def simulate_empirical_challenge(
    rng: np.random.Generator,
    trade_pnls: np.ndarray,
    daily_counts: np.ndarray,
    *,
    max_days: int,
    daily_buffer: float,
) -> PropResult:
    cfg = PropRiskConfig(daily_buffer=daily_buffer, min_profit_day=MIN_PROFIT_DAY)
    engine = PropRiskEngine(starting_balance=STARTING_BALANCE, config=cfg)
    target_balance = STARTING_BALANCE + TARGET_PROFIT
    profit_days = 0
    trades = 0
    stop_days = 0
    flatten_days = 0

    for day in range(1, max_days + 1):
        if engine.check() == Action.DEAD:
            return PropResult("died_mll", day, profit_days, engine.live_equity, trades, stop_days, flatten_days)
        n_trades = int(rng.choice(daily_counts)) if len(daily_counts) else 0
        died = False
        for _ in range(n_trades):
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
            pnl = float(rng.choice(trade_pnls))
            engine.on_fill(pnl)
            trades += 1
            post = engine.check()
            if post == Action.DEAD:
                died = True
                break
            if post == Action.FLATTEN_NOW:
                flatten_days += 1
                break
            if post == Action.STOP_DAY:
                stop_days += 1
                break

        if engine.daily_realized_pnl >= MIN_PROFIT_DAY:
            profit_days += 1
        if died:
            return PropResult("died_mll", day, profit_days, engine.live_equity, trades, stop_days, flatten_days)
        if engine.live_equity >= target_balance:
            outcome = "pass" if profit_days >= MIN_PROFIT_DAYS_REQUIRED else "hit_target_failed_5_day_rule"
            return PropResult(outcome, day, profit_days, engine.live_equity, trades, stop_days, flatten_days)
        engine.on_eod_close()
        if engine.check() == Action.DEAD:
            return PropResult("died_mll", day, profit_days, engine.live_equity, trades, stop_days, flatten_days)

    return PropResult("never_reached_target", max_days, profit_days, engine.live_equity, trades, stop_days, flatten_days)


def max_consecutive_losses(pnl: np.ndarray) -> int:
    max_run = 0
    run = 0
    for value in pnl:
        if value < 0:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
    return max_run


def safe_mean(values: np.ndarray) -> float:
    return float(np.mean(values)) if len(values) else 0.0


def finite(value: float) -> float:
    value = float(value)
    return value if np.isfinite(value) else 0.0


def money(value: float) -> str:
    return f"${value:.2f}"


def daily_count_summary(counts: np.ndarray) -> str:
    if len(counts) == 0:
        return "empty"
    unique, freq = np.unique(counts, return_counts=True)
    return "{" + ", ".join(f"{int(k)}:{int(v)}" for k, v in zip(unique, freq)) + "}"


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(row[i]).rjust(widths[i]) for i in range(len(row))))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


if __name__ == "__main__":
    sys.exit(main())
