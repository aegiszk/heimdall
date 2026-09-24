"""Offline random-entry thesis test on local MES 1-minute data.

Purpose: isolate whether the LucidFlex risk engine creates positive EV with no
entry skill. The entry decision is a seed-driven coin flip at fixed clock slots;
price, volume, and indicators are not consulted until after entry for mechanical
stop/target/flatten fills.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.base import QuantModel, Signal
from core.risk.prop_engine import PropRiskConfig, PropRiskEngine
from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many


DATA_PATH = ROOT / "data" / "MES_1m.parquet"
OUT_DIR = ROOT / "data" / "prop_futures"
EASTERN = ZoneInfo("America/New_York")
STARTING_BALANCE = 50_000.0
TICK_SIZE = 0.25
TICK_VALUE = 1.25
POINT_VALUE = 5.0
COMMISSION_RT = 1.0
SYNTHETIC_52_BUFFER_325_PASS = 0.2732
SYNTHETIC_50_BUFFER_325_PASS = 0.1785
BREAKEVEN_PASS_RATE = 99.0 / (2400.0 + 99.0)


@dataclass(frozen=True)
class NullTrade:
    entry_ts: pd.Timestamp
    exit_ts: pd.Timestamp
    session: object
    side: int
    entry_price: float
    exit_price: float
    stop_price: float
    target_price: float
    pnl: float
    reason: str
    stop_market_exit_price: float | None = None
    stop_limit_compare: str | None = None
    stop_limit_pending: bool = False


class NullRandomModel(QuantModel):
    """Genuinely random MES RTH entry model.

    Rules:
    - Candidate slots are fixed clock times every 30 minutes from 09:30 through
      13:30 ET. Slots after 13:30 are excluded so all trades can be flat by the
      14:00 ET hard flatten.
    - If flat at a slot, flip a seed-driven fair coin. Heads = long, tails =
      short. No price, volume, candle, or indicator data participates in entry.
    - Stop and target are both ``stop_ticks`` from the slipped entry price.
    - Slippage: one adverse tick on market entry, configurable adverse ticks on
      stop-market fills, one adverse tick on forced flatten, limit target fill
      at target, and gap-through stops at the worse open.
    - One open trade at a time.
    """

    strategy_params = ("stop_ticks", "slot_minutes", "flatten_time")

    def __init__(
        self,
        stop_ticks: int = 20,
        slot_minutes: int = 30,
        flatten_time: str = "14:00",
        commission_rt: float = COMMISSION_RT,
        stop_slippage_ticks: int = 1,
        flatten_slippage_ticks: int = 1,
    ):
        if stop_ticks <= 0 or slot_minutes <= 0:
            raise ValueError("stop_ticks and slot_minutes must be positive")
        if stop_slippage_ticks < 0 or flatten_slippage_ticks < 0:
            raise ValueError("slippage ticks must be non-negative")
        self.stop_ticks = int(stop_ticks)
        self.slot_minutes = int(slot_minutes)
        self.flatten_time = pd.Timestamp(flatten_time).time()
        self.commission_rt = float(commission_rt)
        self.stop_slippage_ticks = int(stop_slippage_ticks)
        self.flatten_slippage_ticks = int(flatten_slippage_ticks)

    @property
    def name(self):
        return "null_random"

    def predict(self, asset, ts, data) -> Signal:
        return self._neutral(asset, ts)

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        frame = pd.DataFrame(df).copy()
        required = {"open", "high", "low", "close", "volume"}
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise ValueError(f"missing required columns: {missing}")

        if "ts" in frame.columns:
            ts = pd.to_datetime(frame["ts"])
        elif isinstance(frame.index, pd.DatetimeIndex):
            ts = pd.Series(pd.to_datetime(frame.index), index=frame.index)
        else:
            raise ValueError("provide a ts column or DatetimeIndex")

        if getattr(ts.dt, "tz", None) is None:
            ts = ts.dt.tz_localize("UTC")
        else:
            ts = ts.dt.tz_convert("UTC")

        et = ts.dt.tz_convert(EASTERN)
        frame["_ts"] = ts
        frame["_ts_et"] = et
        frame["_session"] = et.dt.date
        frame["_time"] = et.dt.time
        for col in required:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
            if not np.isfinite(frame[col]).all():
                raise ValueError(f"{col} contains non-finite values")
        frame = frame.sort_values("_ts_et").reset_index(drop=True)
        rth = (frame["_time"] >= pd.Timestamp("09:30").time()) & (frame["_time"] <= self.flatten_time)
        weekday = frame["_ts_et"].dt.weekday < 5
        return frame.loc[rth & weekday].reset_index(drop=True)

    def simulate(self, prepared: pd.DataFrame, seed: int) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        trades: list[NullTrade] = []
        for _, session_frame in prepared.groupby("_session", sort=True):
            session_indices = list(session_frame.index)
            if not session_indices:
                continue
            open_trade: dict[str, object] | None = None
            slot_set = self._slot_times()
            last_i = session_indices[-1]
            for i in session_indices:
                row = prepared.loc[i]
                if open_trade is not None:
                    exit_price, reason = self._exit_price(open_trade, row, i == last_i)
                    if exit_price is not None:
                        trades.append(self._close_trade(open_trade, row, exit_price, reason))
                        open_trade = None

                if open_trade is None and row["_time"] in slot_set:
                    side = 1 if rng.integers(0, 2) == 1 else -1
                    entry = self._entry_price(side, float(row["close"]))
                    distance = self.stop_ticks * TICK_SIZE
                    open_trade = {
                        "entry_ts": row["_ts"],
                        "session": row["_session"],
                        "side": side,
                        "entry_price": entry,
                        "stop_price": entry - side * distance,
                        "target_price": entry + side * distance,
                    }
        return self._trades_frame(trades)

    def simulate_stop_limit(
        self,
        prepared: pd.DataFrame,
        seed: int,
        limit_offset_ticks: int,
        market_stop_slippage_ticks: int = 1,
    ) -> pd.DataFrame:
        if limit_offset_ticks < 0 or market_stop_slippage_ticks < 0:
            raise ValueError("limit and market stop slippage ticks must be non-negative")
        rng = np.random.default_rng(seed)
        trades: list[NullTrade] = []
        for _, session_frame in prepared.groupby("_session", sort=True):
            session_indices = list(session_frame.index)
            if not session_indices:
                continue
            open_trade: dict[str, object] | None = None
            slot_set = self._slot_times()
            last_i = session_indices[-1]
            for i in session_indices:
                row = prepared.loc[i]
                if open_trade is not None:
                    exit_price, reason = self._stop_limit_exit_price(
                        open_trade,
                        row,
                        i == last_i,
                        limit_offset_ticks,
                        market_stop_slippage_ticks,
                    )
                    if exit_price is not None:
                        trades.append(self._close_trade(open_trade, row, exit_price, reason))
                        open_trade = None

                if open_trade is None and row["_time"] in slot_set:
                    side = 1 if rng.integers(0, 2) == 1 else -1
                    entry = self._entry_price(side, float(row["close"]))
                    distance = self.stop_ticks * TICK_SIZE
                    open_trade = {
                        "entry_ts": row["_ts"],
                        "session": row["_session"],
                        "side": side,
                        "entry_price": entry,
                        "stop_price": entry - side * distance,
                        "target_price": entry + side * distance,
                        "pending_stop_limit": False,
                        "stop_limit_price": None,
                        "stop_market_exit_price": None,
                    }
        return self._trades_frame(trades)

    def _slot_times(self) -> set[object]:
        start = pd.Timestamp("09:30")
        end = pd.Timestamp("13:30")
        return {ts.time() for ts in pd.date_range(start, end, freq=f"{self.slot_minutes}min")}

    @staticmethod
    def _entry_price(side: int, close: float) -> float:
        return close + side * TICK_SIZE

    def _exit_price(
        self,
        open_trade: dict[str, object],
        row: pd.Series,
        is_last_session_bar: bool,
    ) -> tuple[float | None, str]:
        side = int(open_trade["side"])
        stop = float(open_trade["stop_price"])
        target = float(open_trade["target_price"])
        open_ = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])

        if side > 0:
            if open_ <= stop:
                return min(open_, stop - self.stop_slippage_ticks * TICK_SIZE), "gap_stop"
            if low <= stop:
                return stop - self.stop_slippage_ticks * TICK_SIZE, "stop"
            if high >= target:
                return target, "target"
            if row["_time"] >= self.flatten_time or is_last_session_bar:
                return float(row["close"] - self.flatten_slippage_ticks * TICK_SIZE), "session_flatten"
        else:
            if open_ >= stop:
                return max(open_, stop + self.stop_slippage_ticks * TICK_SIZE), "gap_stop"
            if high >= stop:
                return stop + self.stop_slippage_ticks * TICK_SIZE, "stop"
            if low <= target:
                return target, "target"
            if row["_time"] >= self.flatten_time or is_last_session_bar:
                return float(row["close"] + self.flatten_slippage_ticks * TICK_SIZE), "session_flatten"
        return None, ""

    def _stop_limit_exit_price(
        self,
        open_trade: dict[str, object],
        row: pd.Series,
        is_last_session_bar: bool,
        limit_offset_ticks: int,
        market_stop_slippage_ticks: int,
    ) -> tuple[float | None, str]:
        side = int(open_trade["side"])
        stop = float(open_trade["stop_price"])
        target = float(open_trade["target_price"])
        open_ = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])

        if bool(open_trade.get("pending_stop_limit")):
            limit_price = float(open_trade["stop_limit_price"])
            returned_to_limit = high >= limit_price if side > 0 else low <= limit_price
            if returned_to_limit:
                return limit_price, "stop_limit_late_fill"
            if row["_time"] >= self.flatten_time or is_last_session_bar:
                return self._flatten_price(side, float(row["close"])), "stop_limit_unfilled_flatten"
            return None, ""

        market_stop = self._market_stop_price(side, stop, open_, high, low, market_stop_slippage_ticks)
        if market_stop is not None:
            limit_price = stop - side * limit_offset_ticks * TICK_SIZE
            open_beyond_limit = open_ < limit_price if side > 0 else open_ > limit_price
            close_returned_to_limit = float(row["close"]) >= limit_price if side > 0 else float(row["close"]) <= limit_price
            open_trade["stop_market_exit_price"] = market_stop
            open_trade["stop_limit_price"] = limit_price
            if not open_beyond_limit and close_returned_to_limit:
                open_trade["pending_stop_limit"] = False
                return limit_price, "stop_limit_fill"
            open_trade["pending_stop_limit"] = True
            if close_returned_to_limit:
                return limit_price, "stop_limit_late_fill"
            if row["_time"] >= self.flatten_time or is_last_session_bar:
                return self._flatten_price(side, float(row["close"])), "stop_limit_unfilled_flatten"
            return None, ""

        if side > 0:
            if high >= target:
                return target, "target"
        else:
            if low <= target:
                return target, "target"
        if row["_time"] >= self.flatten_time or is_last_session_bar:
            return self._flatten_price(side, float(row["close"])), "session_flatten"
        return None, ""

    @staticmethod
    def _market_stop_price(
        side: int,
        stop: float,
        open_: float,
        high: float,
        low: float,
        stop_slippage_ticks: int,
    ) -> float | None:
        slip = stop_slippage_ticks * TICK_SIZE
        if side > 0:
            if open_ <= stop:
                return min(open_, stop - slip)
            if low <= stop:
                return stop - slip
        else:
            if open_ >= stop:
                return max(open_, stop + slip)
            if high >= stop:
                return stop + slip
        return None

    def _flatten_price(self, side: int, close: float) -> float:
        return close - side * self.flatten_slippage_ticks * TICK_SIZE

    def _close_trade(
        self,
        open_trade: dict[str, object],
        row: pd.Series,
        exit_price: float,
        reason: str,
    ) -> NullTrade:
        side = int(open_trade["side"])
        entry = float(open_trade["entry_price"])
        pnl = side * (float(exit_price) - entry) * POINT_VALUE - self.commission_rt
        market_exit = open_trade.get("stop_market_exit_price")
        compare = None
        if market_exit is not None:
            diff = side * (float(exit_price) - float(market_exit))
            if diff > 1e-12:
                compare = "better"
            elif diff < -1e-12:
                compare = "worse"
            else:
                compare = "neutral"
        return NullTrade(
            entry_ts=open_trade["entry_ts"],
            exit_ts=row["_ts"],
            session=open_trade["session"],
            side=side,
            entry_price=entry,
            exit_price=float(exit_price),
            stop_price=float(open_trade["stop_price"]),
            target_price=float(open_trade["target_price"]),
            pnl=float(pnl),
            reason=reason,
            stop_market_exit_price=None if market_exit is None else float(market_exit),
            stop_limit_compare=compare,
            stop_limit_pending=bool(open_trade.get("pending_stop_limit", False)),
        )

    @staticmethod
    def _trades_frame(trades: list[NullTrade]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "entry_ts": [trade.entry_ts for trade in trades],
                "exit_ts": [trade.exit_ts for trade in trades],
                "session": [trade.session for trade in trades],
                "side": [trade.side for trade in trades],
                "entry_price": [trade.entry_price for trade in trades],
                "exit_price": [trade.exit_price for trade in trades],
                "stop_price": [trade.stop_price for trade in trades],
                "target_price": [trade.target_price for trade in trades],
                "pnl": [trade.pnl for trade in trades],
                "reason": [trade.reason for trade in trades],
                "stop_market_exit_price": [trade.stop_market_exit_price for trade in trades],
                "stop_limit_compare": [trade.stop_limit_compare for trade in trades],
                "stop_limit_pending": [trade.stop_limit_pending for trade in trades],
            }
        )


def main() -> int:
    args = parse_args()
    raw = load_mes(args.data)
    model = NullRandomModel(stop_ticks=args.stop_ticks)
    prepared = model.prepare(raw)
    sessions = sorted(prepared["_session"].dropna().unique())
    cut = int(len(sessions) * 0.60)
    train_sessions = set(sessions[:cut])
    holdout_sessions = set(sessions[cut:])
    train = prepared[prepared["_session"].isin(train_sessions)].reset_index(drop=True)
    holdout = prepared[prepared["_session"].isin(holdout_sessions)].reset_index(drop=True)

    print("NULL RANDOM ENTRY TEST")
    print(f"data={args.data}")
    print("network_calls=0 databento_calls=0 offline_only=true")
    print(
        f"model=NullRandomModel contract=MES stop_ticks={args.stop_ticks} target_ticks={args.stop_ticks} "
        "slots=09:30..13:30_ET_every_30min flatten=14:00_ET entry=random_coin_flip"
    )
    print("entry_logic=timestamp_slot + rng coin only; no price/volume/indicator inputs")
    print()
    print_step0(raw, prepared, sessions, train_sessions, holdout_sessions, args.stop_ticks, args.daily_buffer)

    results, wf_by_slippage = run_stop_slippage_sweep(train, holdout, holdout_sessions, args)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result_path = OUT_DIR / "null_random_mes_slippage_sweep.csv"
    results.to_csv(result_path, index=False)

    limit_results = run_stop_limit_comparison(holdout, args)
    limit_path = OUT_DIR / "null_random_mes_stop_limit_comparison.csv"
    limit_results.to_csv(limit_path, index=False)

    print_stop_slippage_sweep(results)
    print_walk_forward_slippage_distribution(wf_by_slippage)
    print_stop_limit_comparison(limit_results)
    print_fill_assumption_answer(results)
    print(f"slippage_results_file={result_path}")
    print(f"stop_limit_results_file={limit_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline random MES entry test for risk-engine-only thesis.")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--n-seeds", type=int, default=20)
    parser.add_argument("--first-seed", type=int, default=20260702)
    parser.add_argument("--n-sims", type=int, default=10_000)
    parser.add_argument("--stop-ticks", type=int, default=20)
    parser.add_argument("--daily-buffer", type=float, default=325.0)
    parser.add_argument("--stop-slippage-sweep", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--stop-limit-offsets", nargs="+", type=int, default=[0, 1, 2])
    return parser.parse_args()


def load_mes(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    return frame[["open", "high", "low", "close", "volume"]].copy()


def observed_daily_counts(sessions: set[object], trades: pd.DataFrame) -> np.ndarray:
    ordered = sorted(sessions)
    if trades.empty:
        return np.zeros(len(ordered), dtype=int)
    counts = trades["session"].value_counts()
    return np.asarray([int(counts.get(session, 0)) for session in ordered], dtype=int)


def run_stop_slippage_sweep(
    train: pd.DataFrame,
    holdout: pd.DataFrame,
    holdout_sessions: set[object],
    args: argparse.Namespace,
) -> tuple[pd.DataFrame, dict[int, list[list[dict[str, float]]]]]:
    rows = []
    wf_by_slippage: dict[int, list[list[dict[str, float]]]] = {}
    for stop_slippage_ticks in args.stop_slippage_sweep:
        model = NullRandomModel(stop_ticks=args.stop_ticks, stop_slippage_ticks=stop_slippage_ticks)
        wf_rows_by_seed = []
        for seed in range(args.first_seed, args.first_seed + args.n_seeds):
            train_trades = model.simulate(train, seed)
            holdout_trades = model.simulate(holdout, seed)
            daily_counts = observed_daily_counts(holdout_sessions, holdout_trades)
            sized = scale_trades_for_risk_engine(holdout_trades, args.stop_ticks, args.daily_buffer)
            mc_seed = seed + stop_slippage_ticks * 100_000
            mc = monte_carlo(sized, daily_counts, mc_seed, args.n_sims, args.daily_buffer)
            summary = summarize_trades(holdout_trades)
            train_summary = summarize_trades(train_trades)
            wf = walk_forward(holdout_sessions, holdout_trades)
            wf_rows_by_seed.append(wf)
            rows.append(
                {
                    "stop_ticks": args.stop_ticks,
                    "stop_slippage_ticks": stop_slippage_ticks,
                    "seed": seed,
                    "train_mean": train_summary["mean"],
                    "holdout_trades": int(summary["n"]),
                    "holdout_win_rate": summary["win_rate"],
                    "holdout_mean": summary["mean"],
                    "holdout_rr": summary["rr"],
                    "holdout_skew": summary["skew"],
                    "wf_min": min(row["mean"] for row in wf),
                    "mc_pass_rate": mc.pass_rate,
                    "mc_ev": ev_per_eval(mc.pass_rate, 2400.0, 99.0),
                    "mc_fail_mll": mc.fail_died_mll,
                    "mc_fail_no_target": mc.fail_no_target,
                    "mc_avg_trades": mc.avg_trades,
                }
            )
        wf_by_slippage[stop_slippage_ticks] = wf_rows_by_seed
    return pd.DataFrame(rows), wf_by_slippage


def run_stop_limit_comparison(holdout: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    rows = []
    for limit_offset_ticks in args.stop_limit_offsets:
        model = NullRandomModel(stop_ticks=args.stop_ticks, stop_slippage_ticks=1)
        for seed in range(args.first_seed, args.first_seed + args.n_seeds):
            trades = model.simulate_stop_limit(
                holdout,
                seed,
                limit_offset_ticks=limit_offset_ticks,
                market_stop_slippage_ticks=1,
            )
            events = trades.loc[trades["stop_limit_compare"].notna()].copy()
            if events.empty:
                rows.append(
                    {
                        "limit_offset_ticks": limit_offset_ticks,
                        "seed": seed,
                        "stop_events": 0,
                        "better": 0,
                        "neutral": 0,
                        "worse": 0,
                        "pending": 0,
                        "unfilled_flatten": 0,
                        "avg_delta_vs_market": 0.0,
                        "median_delta_vs_market": 0.0,
                    }
                )
                continue
            delta = (
                events["side"].astype(float)
                * (events["exit_price"].astype(float) - events["stop_market_exit_price"].astype(float))
                * POINT_VALUE
            )
            rows.append(
                {
                    "limit_offset_ticks": limit_offset_ticks,
                    "seed": seed,
                    "stop_events": int(len(events)),
                    "better": int((events["stop_limit_compare"] == "better").sum()),
                    "neutral": int((events["stop_limit_compare"] == "neutral").sum()),
                    "worse": int((events["stop_limit_compare"] == "worse").sum()),
                    "pending": int(events["stop_limit_pending"].sum()),
                    "unfilled_flatten": int((events["reason"] == "stop_limit_unfilled_flatten").sum()),
                    "avg_delta_vs_market": float(delta.mean()),
                    "median_delta_vs_market": float(delta.median()),
                }
            )
    return pd.DataFrame(rows)


def scale_trades_for_risk_engine(trades: pd.DataFrame, stop_ticks: int, daily_buffer: float) -> pd.DataFrame:
    cfg = PropRiskConfig(daily_buffer=daily_buffer)
    contracts = PropRiskEngine(config=cfg).allowed_size(TICK_VALUE, stop_ticks)
    if contracts <= 0:
        raise ValueError("risk engine allowed zero contracts")
    scaled = trades.copy()
    scaled["pnl"] = scaled["pnl"].astype(float) * contracts
    scaled["contracts"] = contracts
    return scaled


def monte_carlo(trades: pd.DataFrame, daily_counts: np.ndarray, seed: int, n_sims: int, daily_buffer: float):
    params = SimParams(
        n_sims=n_sims,
        seed=seed + 7_000_000,
        daily_buffer=daily_buffer,
        commission_per_rt=COMMISSION_RT,
        min_trades_per_day=0,
        max_trades_per_day=1,
    )
    return run_empirical_many(params, trades["pnl"].to_numpy(float), daily_counts)


def summarize_trades(trades: pd.DataFrame) -> dict[str, float]:
    if trades.empty:
        return {"n": 0.0, "win_rate": 0.0, "mean": 0.0, "rr": 0.0, "skew": 0.0}
    pnl = trades["pnl"].to_numpy(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    avg_win = float(np.mean(wins)) if len(wins) else 0.0
    avg_loss = float(np.mean(losses)) if len(losses) else 0.0
    rr = avg_win / abs(avg_loss) if avg_loss < 0 else 0.0
    skew = float(stats.skew(pnl, bias=False)) if len(pnl) > 2 else 0.0
    return {
        "n": float(len(pnl)),
        "win_rate": float((pnl > 0).mean()),
        "mean": float(np.mean(pnl)),
        "rr": rr,
        "skew": skew if np.isfinite(skew) else 0.0,
    }


def walk_forward(sessions: set[object], trades: pd.DataFrame) -> list[dict[str, float]]:
    rows = []
    for idx, bucket in enumerate(np.array_split(np.asarray(sorted(sessions), dtype=object), 4), start=1):
        if trades.empty:
            bucket_trades = trades
        else:
            bucket_trades = trades.loc[trades["session"].isin(set(bucket))]
        summary = summarize_trades(bucket_trades)
        rows.append(
            {
                "bucket": float(idx),
                "start": bucket[0],
                "end": bucket[-1],
                "n": summary["n"],
                "mean": summary["mean"],
                "win_rate": summary["win_rate"],
            }
        )
    return rows


def print_step0(
    raw: pd.DataFrame,
    prepared: pd.DataFrame,
    sessions: list[object],
    train_sessions: set[object],
    holdout_sessions: set[object],
    stop_ticks: int,
    daily_buffer: float,
) -> None:
    idx = pd.DatetimeIndex(raw.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    gaps = idx.to_series().diff().dropna().gt(pd.Timedelta(minutes=1.5)).sum()
    print("STEP_0_DATA_SANITY")
    print(
        f"rows_1m={len(raw)} start_utc={idx[0].isoformat()} end_utc={idx[-1].isoformat()} "
        f"gaps_gt_1m={int(gaps)} nan_ohlcv={int(raw[['open','high','low','close','volume']].isna().sum().sum())}"
    )
    print(
        f"price_min={raw['low'].min():.2f} price_max={raw['high'].max():.2f} "
        f"prepared_rth_rows={len(prepared)} sessions={len(sessions)} "
        f"train_sessions={len(train_sessions)} holdout_sessions={len(holdout_sessions)}"
    )
    print(
        f"split train={min(train_sessions)}..{max(train_sessions)} "
        f"holdout={min(holdout_sessions)}..{max(holdout_sessions)}"
    )
    contracts = PropRiskEngine(config=PropRiskConfig(daily_buffer=daily_buffer)).allowed_size(TICK_VALUE, stop_ticks)
    print(
        f"one_contract gross_stop=${TICK_VALUE * stop_ticks:.2f}; realized target before scale=${TICK_VALUE * stop_ticks - COMMISSION_RT:.2f}; "
        f"normal stop with 1-tick stop-slip before scale=${-(TICK_VALUE * (stop_ticks + 1)) - COMMISSION_RT:.2f}; "
        f"risk_engine_allowed_contracts_at_buffer={contracts}"
    )
    print()


def print_stop_slippage_sweep(results: pd.DataFrame) -> None:
    print("STOP_SLIPPAGE_SWEEP")
    rows = [[
        "stop_slip",
        "target_1c",
        "normal_stop_1c",
        "median_pass",
        "worst_pass",
        "median_ev",
        "worst_ev",
        "median_mean",
        "median_rr",
        "worst_seed",
    ]]
    for stop_slip, group in results.groupby("stop_slippage_ticks", sort=True):
        stop_ticks = int(group["stop_ticks"].iloc[0])
        pass_rates = group["mc_pass_rate"].to_numpy(float)
        evs = group["mc_ev"].to_numpy(float)
        worst_idx = group["mc_pass_rate"].idxmin()
        target = TICK_VALUE * stop_ticks - COMMISSION_RT
        normal_stop = -(TICK_VALUE * (stop_ticks + int(stop_slip))) - COMMISSION_RT
        rows.append([
            f"{int(stop_slip)}t",
            f"${target:.2f}",
            f"${normal_stop:.2f}",
            f"{np.median(pass_rates):.4%}",
            f"{pass_rates.min():.4%}",
            f"${np.median(evs):.2f}",
            f"${evs.min():.2f}",
            f"${np.median(group['holdout_mean'].to_numpy(float)):.2f}",
            f"{np.median(group['holdout_rr'].to_numpy(float)):.3f}",
            str(int(group.loc[worst_idx, "seed"])),
        ])
    print_table(rows)
    print()


def print_walk_forward_slippage_distribution(wf_by_slippage: dict[int, list[list[dict[str, float]]]]) -> None:
    print("WALK_FORWARD_MEDIAN_MEAN_BY_STOP_SLIPPAGE")
    rows = [["stop_slip", "bucket1", "bucket2", "bucket3", "bucket4"]]
    for stop_slip, wf_rows_by_seed in sorted(wf_by_slippage.items()):
        bucket_means = []
        for bucket_idx in range(4):
            means = np.asarray([wf[bucket_idx]["mean"] for wf in wf_rows_by_seed], dtype=float)
            bucket_means.append(f"${np.median(means):.2f}")
        rows.append([f"{stop_slip}t", *bucket_means])
    print_table(rows)
    print()


def print_stop_limit_comparison(limit_results: pd.DataFrame) -> None:
    print("STOP_LIMIT_VS_STOP_MARKET_BASELINE_1T")
    print("baseline=stop-market with 1 adverse stop tick; stop-limit modeled on actual holdout paths")
    rows = [[
        "limit_offset",
        "events",
        "better",
        "neutral",
        "worse",
        "pending",
        "unfilled_flatten",
        "avg_delta",
        "median_delta",
    ]]
    for offset, group in limit_results.groupby("limit_offset_ticks", sort=True):
        events = int(group["stop_events"].sum())
        denom = max(events, 1)
        rows.append([
            f"{int(offset)}t",
            str(events),
            f"{group['better'].sum() / denom:.2%}",
            f"{group['neutral'].sum() / denom:.2%}",
            f"{group['worse'].sum() / denom:.2%}",
            f"{group['pending'].sum() / denom:.2%}",
            f"{group['unfilled_flatten'].sum() / denom:.2%}",
            f"${weighted_mean(group, 'avg_delta_vs_market', 'stop_events'):.2f}",
            f"${np.median(group['median_delta_vs_market'].to_numpy(float)):.2f}",
        ])
    print_table(rows)
    print(
        "note=pending means the stop-limit did not immediately fill when the stop-market would have; "
        "unfilled_flatten is the explicit tail where it rode to the 14:00 flatten."
    )
    print()


def print_fill_assumption_answer(results: pd.DataFrame) -> None:
    print("FILL_ASSUMPTION_ANSWER")
    rows = [["stop_slip", "median_pass", "worst_pass", "clears_breakeven"]]
    cleared = []
    for stop_slip, group in results.groupby("stop_slippage_ticks", sort=True):
        median_pass = float(np.median(group["mc_pass_rate"].to_numpy(float)))
        worst_pass = float(group["mc_pass_rate"].min())
        clears = median_pass > BREAKEVEN_PASS_RATE
        if clears:
            cleared.append(int(stop_slip))
        rows.append([
            f"{int(stop_slip)}t",
            f"{median_pass:.4%}",
            f"{worst_pass:.4%}",
            str(clears),
        ])
    print_table(rows)
    first = min(cleared) if cleared else None
    print(f"breakeven_pass_rate={BREAKEVEN_PASS_RATE:.4%}")
    if first is None:
        print("answer=no tested stop-slippage level clears breakeven on median pass_rate")
    else:
        print(f"answer=median pass_rate first clears breakeven at stop_slippage={first} ticks")
    zero_group = results.loc[results["stop_slippage_ticks"] == 0]
    if not zero_group.empty:
        zero_median = float(np.median(zero_group["mc_pass_rate"].to_numpy(float)))
        print(
            "zero_tick_stop_execution="
            + ("clears" if zero_median > BREAKEVEN_PASS_RATE else "fails")
            + f" median_pass={zero_median:.4%}"
        )
    print(
        "conclusion="
        + (
            "fill_assumption_can_rescue_coin_flip"
            if first is not None
            else "edge_required_even_with_idealized_stop_execution"
        )
    )
    print()


def weighted_mean(df: pd.DataFrame, value_col: str, weight_col: str) -> float:
    weights = df[weight_col].to_numpy(float)
    values = df[value_col].to_numpy(float)
    total = weights.sum()
    return float(np.sum(values * weights) / total) if total else 0.0


def print_seed_table(results: pd.DataFrame) -> None:
    print("SEED_RESULTS_HOLDOUT_AND_MC")
    rows = [[
        "seed",
        "n",
        "win",
        "mean",
        "rr",
        "skew",
        "wf_min",
        "pass",
        "ev",
        "mll",
        "no_target",
    ]]
    for row in results.to_dict("records"):
        rows.append([
            str(int(row["seed"])),
            str(int(row["holdout_trades"])),
            f"{row['holdout_win_rate']:.2%}",
            f"${row['holdout_mean']:.2f}",
            f"{row['holdout_rr']:.3f}",
            f"{row['holdout_skew']:.3f}",
            f"${row['wf_min']:.2f}",
            f"{row['mc_pass_rate']:.2%}",
            f"${row['mc_ev']:.2f}",
            f"{row['mc_fail_mll']:.2%}",
            f"{row['mc_fail_no_target']:.2%}",
        ])
    print_table(rows)
    print()


def print_distribution(results: pd.DataFrame) -> None:
    print("PASS_RATE_EV_DISTRIBUTION")
    pass_rates = results["mc_pass_rate"].to_numpy(float)
    evs = results["mc_ev"].to_numpy(float)
    worst_idx = int(np.argmin(pass_rates))
    best_idx = int(np.argmax(pass_rates))
    print(
        f"pass_rate min={pass_rates.min():.4%} p25={np.quantile(pass_rates, 0.25):.4%} "
        f"median={np.median(pass_rates):.4%} p75={np.quantile(pass_rates, 0.75):.4%} max={pass_rates.max():.4%}"
    )
    print(
        f"EV min=${evs.min():.2f} p25=${np.quantile(evs, 0.25):.2f} "
        f"median=${np.median(evs):.2f} p75=${np.quantile(evs, 0.75):.2f} max=${evs.max():.2f}"
    )
    print(
        f"worst_seed={int(results.iloc[worst_idx]['seed'])} pass_rate={pass_rates[worst_idx]:.4%} "
        f"EV=${evs[worst_idx]:.2f}"
    )
    print(
        f"best_seed={int(results.iloc[best_idx]['seed'])} pass_rate={pass_rates[best_idx]:.4%} "
        f"EV=${evs[best_idx]:.2f}"
    )
    print()


def print_walk_forward_distribution(wf_rows_by_seed: list[list[dict[str, float]]]) -> None:
    print("WALK_FORWARD_4_BUCKETS_HOLDOUT_ACROSS_SEEDS")
    rows = [["bucket", "median_mean", "min_mean", "max_mean", "median_win", "median_n"]]
    for bucket_idx in range(4):
        means = np.asarray([wf[bucket_idx]["mean"] for wf in wf_rows_by_seed], dtype=float)
        wins = np.asarray([wf[bucket_idx]["win_rate"] for wf in wf_rows_by_seed], dtype=float)
        ns = np.asarray([wf[bucket_idx]["n"] for wf in wf_rows_by_seed], dtype=float)
        rows.append([
            str(bucket_idx + 1),
            f"${np.median(means):.2f}",
            f"${means.min():.2f}",
            f"${means.max():.2f}",
            f"{np.median(wins):.2%}",
            f"{np.median(ns):.0f}",
        ])
    print_table(rows)
    print()


def print_direct_comparison(results: pd.DataFrame, daily_buffer: float) -> None:
    breakeven = 99.0 / (2400.0 + 99.0)
    median_pass = float(np.median(results["mc_pass_rate"]))
    worst_pass = float(results["mc_pass_rate"].min())
    print("DIRECT_COMPARISON")
    print(f"breakeven_pass_rate={breakeven:.4%}")
    print(f"synthetic_52pct_1to1_buffer325_pass={SYNTHETIC_52_BUFFER_325_PASS:.4%}")
    print(f"synthetic_50pct_1to1_buffer325_pass={SYNTHETIC_50_BUFFER_325_PASS:.4%}")
    print(f"real_random_median_pass={median_pass:.4%} gap_vs_52pct_synth={median_pass - SYNTHETIC_52_BUFFER_325_PASS:.4%}")
    print(f"real_random_worst_seed_pass={worst_pass:.4%} gap_vs_breakeven={worst_pass - breakeven:.4%}")
    print(
        "verdict="
        + (
            "risk_engine_only_survives"
            if worst_pass > breakeven
            else "risk_engine_only_fails_worst_seed_breakeven"
        )
    )
    print(
        "caveat=market-realized fair coin is not net 1:1 after commission and 1-tick stop slippage; "
        "normal MES 20-tick target is +$24.00 one-contract, normal stop is -$27.25 one-contract before risk sizing."
    )
    print(f"daily_buffer=${daily_buffer:.2f}")
    print()


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(row[i]).rjust(widths[i]) for i in range(len(row))))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


if __name__ == "__main__":
    sys.exit(main())
