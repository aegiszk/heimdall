"""Offline quality-filter diagnostic for ES prop futures candidates.

Uses only data/ES_1m.parquet. No network calls, no Databento imports.

Pre-registered filters:
- volatility: ATR-14 must be above its shifted trailing 20-RTH-session median.
- time_of_day: entries only 09:45-11:30 and 13:30-15:30 ET.
- trend_alignment: VWAP reversion only; fade only against the current
  open-to-now daily trend, so the entry side must match that daily trend.

The target/stop stays fixed at the prior winning ES config: 25/20 ticks.
Pair selection is train-only by win rate, then RR, then mean PnL.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from datetime import time

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.target_sweep import (
    Config,
    EASTERN,
    TICK_SIZE,
    close_trade,
    entry_plan,
    entry_window,
    ev_per_eval,
    exit_price_for,
    load_features,
    max_trades_day,
    metrics,
    money,
    monte_carlo,
    observed_daily_counts,
    pct,
    print_table,
    split_session,
    walk_forward_rows,
)


DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "quality_filter_sweep"
INSTRUMENT = "ES"
TARGET_TICKS = 25
STOP_TICKS = 20
STRATEGIES = ("vwap_reversion", "trend_pullback")
BASE_FILTERS = ("volatility", "time_of_day")
VWAP_ONLY_FILTERS = ("trend_alignment",)
MIN_HOLDOUT_TRADES = 300
ATR_PERIOD = 14
RTH_BARS_PER_SESSION = 390
ATR_MEDIAN_SESSIONS = 20


@dataclass(frozen=True)
class FilterSpec:
    name: str
    filters: tuple[str, ...]
    kind: str


def main() -> int:
    ensure_data_present()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    frame = add_filter_features(load_features(INSTRUMENT))
    split_day = split_session(frame)
    config_by_strategy = {
        strategy: Config(strategy, INSTRUMENT, TARGET_TICKS, STOP_TICKS)
        for strategy in STRATEGIES
    }

    print_filter_contract(split_day)

    rows: list[dict[str, object]] = []
    wf_rows: list[dict[str, object]] = []
    selected_pairs: list[dict[str, object]] = []

    for strategy in STRATEGIES:
        config = config_by_strategy[strategy]
        specs = filter_specs_for(strategy, frame, split_day, config)
        selected_pairs.extend(pair_selection_rows(strategy, specs))

        for spec in specs:
            trades = simulate_filtered(frame, config, spec)
            trades.to_csv(OUT_DIR / f"{strategy}_{spec.name}_trades.csv", index=False)
            train = trades[trades["session"] <= split_day].copy()
            holdout = trades[trades["session"] > split_day].copy()

            rows.append(metric_row(config, spec, "train", train, None))
            daily_counts = observed_daily_counts(frame, holdout, after_day=split_day)
            mc = monte_carlo(holdout, daily_counts) if len(holdout) >= MIN_HOLDOUT_TRADES else None
            rows.append(metric_row(config, spec, "holdout", holdout, mc))

            for row in walk_forward_rows(trades, config):
                row["filter"] = spec.name
                row["filter_kind"] = spec.kind
                wf_rows.append(row)

    results = pd.DataFrame(rows)
    wf = pd.DataFrame(wf_rows)
    pair_df = pd.DataFrame(selected_pairs)
    results.to_csv(OUT_DIR / "quality_filter_results.csv", index=False)
    wf.to_csv(OUT_DIR / "quality_filter_walk_forward.csv", index=False)
    pair_df.to_csv(OUT_DIR / "pair_selection_train_only.csv", index=False)

    print_pair_selection(pair_df)
    print_holdout_results(results, wf)
    print_walk_forward(wf)
    print_verdict(results, wf)
    return 0


def ensure_data_present() -> None:
    path = DATA_DIR / f"{INSTRUMENT}_1m.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Required local parquet missing; refusing to pull data: {path}")


def add_filter_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    prev_close = out["close"].shift(1)
    true_range = pd.concat(
        [
            out["high"] - out["low"],
            (out["high"] - prev_close).abs(),
            (out["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr14"] = true_range.rolling(ATR_PERIOD, min_periods=ATR_PERIOD).mean()
    median_window = ATR_MEDIAN_SESSIONS * RTH_BARS_PER_SESSION
    out["atr14_median"] = (
        out["atr14"]
        .shift(1)
        .rolling(median_window, min_periods=RTH_BARS_PER_SESSION)
        .median()
    )
    out["session_open"] = out.groupby("session")["open"].transform("first")
    return out


def filter_specs_for(
    strategy: str,
    frame: pd.DataFrame,
    split_day,
    config: Config,
) -> list[FilterSpec]:
    singles = list(BASE_FILTERS)
    if strategy == "vwap_reversion":
        singles.extend(VWAP_ONLY_FILTERS)
    specs = [FilterSpec("baseline", tuple(), "baseline")]
    specs.extend(FilterSpec(name, (name,), "single") for name in singles)

    pair = select_pair_on_train(strategy, frame, split_day, config, singles)
    if pair is not None:
        specs.append(pair)
    return specs


def select_pair_on_train(
    strategy: str,
    frame: pd.DataFrame,
    split_day,
    config: Config,
    singles: list[str],
) -> FilterSpec | None:
    candidates: list[tuple[tuple[float, float, float, int], FilterSpec]] = []
    for pair in combinations(singles, 2):
        spec = FilterSpec("+".join(pair), tuple(pair), "pair")
        trades = simulate_filtered(frame, config, spec)
        train = trades[trades["session"] <= split_day]
        values = metrics(train, config)
        score = (
            float(values["win_rate"]),
            float(values["realized_rr"]),
            float(values["mean_pnl"]),
            int(values["n_trades"]),
        )
        candidates.append((score, spec))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def pair_selection_rows(strategy: str, specs: list[FilterSpec]) -> list[dict[str, object]]:
    return [
        {
            "strategy": strategy,
            "selected_pair": spec.name,
            "filters": ",".join(spec.filters),
        }
        for spec in specs
        if spec.kind == "pair"
    ]


def simulate_filtered(frame: pd.DataFrame, config: Config, spec: FilterSpec) -> pd.DataFrame:
    rows = []
    contract = {"point_value": 50.0, "tick_value": 12.50, "commission": 3.50}
    for session, day in frame.groupby("session", sort=True):
        open_trade = None
        trades_today = 0
        last_i = day.index[-1]
        for ts, bar in day.iterrows():
            clock = ts.tz_convert(EASTERN).time()
            if open_trade is not None:
                exit_price, reason = exit_price_for(open_trade, bar, ts == last_i)
                if exit_price is not None:
                    rows.append(close_trade(open_trade, bar, exit_price, reason, contract))
                    open_trade = None
                    continue

            if open_trade is not None:
                continue
            if trades_today >= max_trades_day(config.strategy):
                continue
            if not entry_window(config.strategy, clock):
                continue

            plan = entry_plan(config, day, ts)
            if plan is None:
                continue
            side, signal_price = plan
            if not passes_filters(spec, config.strategy, bar, clock, side):
                continue

            entry_price = signal_price + side * TICK_SIZE
            open_trade = {
                "strategy": config.strategy,
                "instrument": config.instrument,
                "filter": spec.name,
                "session": session,
                "entry_ts": ts,
                "side": side,
                "signal_price": signal_price,
                "entry_price": entry_price,
                "target_price": signal_price + side * config.target_ticks * TICK_SIZE,
                "stop_price": signal_price - side * config.stop_ticks * TICK_SIZE,
                "target_ticks": config.target_ticks,
                "stop_ticks": config.stop_ticks,
            }
            trades_today += 1
    return pd.DataFrame(rows)


def passes_filters(spec: FilterSpec, strategy: str, bar: pd.Series, clock: time, side: int) -> bool:
    for name in spec.filters:
        if name == "volatility":
            atr = float(bar["atr14"])
            median = float(bar["atr14_median"])
            if not (np.isfinite(atr) and np.isfinite(median) and atr > median):
                return False
        elif name == "time_of_day":
            if not ((time(9, 45) <= clock <= time(11, 30)) or (time(13, 30) <= clock <= time(15, 30))):
                return False
        elif name == "trend_alignment":
            if strategy != "vwap_reversion":
                return False
            trend = float(bar["close"]) - float(bar["session_open"])
            if trend == 0:
                return False
            trend_side = 1 if trend > 0 else -1
            if side != trend_side:
                return False
        else:
            raise ValueError(f"unknown filter {name}")
    return True


def metric_row(config: Config, spec: FilterSpec, split: str, trades: pd.DataFrame, mc) -> dict[str, object]:
    values = metrics(trades, config)
    pass_rate = 0.0 if mc is None else mc.pass_rate
    return {
        "strategy": config.strategy,
        "instrument": config.instrument,
        "filter": spec.name,
        "filter_kind": spec.kind,
        "split": split,
        "target_ticks": config.target_ticks,
        "stop_ticks": config.stop_ticks,
        **values,
        "meaningful_holdout": split != "holdout" or int(values["n_trades"]) >= MIN_HOLDOUT_TRADES,
        "pass_rate": pass_rate,
        "ev_per_eval": ev_per_eval(pass_rate, 2400.0, 99.0) if mc is not None else -99.0,
        "fail_died_mll": 0.0 if mc is None else mc.fail_died_mll,
        "fail_never_target": 1.0 if mc is None else mc.fail_no_target,
        "fail_failed_5day": 0.0 if mc is None else mc.fail_target_min_days,
    }


def print_filter_contract(split_day) -> None:
    print("OFFLINE QUALITY FILTER SWEEP")
    print(f"data_source=data/{INSTRUMENT}_1m.parquet only")
    print(f"target_ticks={TARGET_TICKS} stop_ticks={STOP_TICKS} train_holdout_split_day={split_day}")
    print("volatility=ATR14 > shifted trailing 20-RTH-session median")
    print("time_of_day=09:45-11:30 and 13:30-15:30 ET")
    print("trend_alignment=vwap only, entry side must match session-open-to-now trend")
    print("pair_selection=train only: max win_rate, then RR, then mean PnL")
    print()


def print_pair_selection(pair_df: pd.DataFrame) -> None:
    print("TRAIN-ONLY SELECTED PAIRS")
    rows = [["strategy", "selected_pair"]]
    for row in pair_df.itertuples(index=False):
        rows.append([row.strategy, row.selected_pair])
    print_table(rows)
    print()


def print_holdout_results(results: pd.DataFrame, wf: pd.DataFrame) -> None:
    print("HOLDOUT FILTER RESULTS")
    rows = [
        [
            "strategy",
            "filter",
            "kind",
            "trades",
            "win",
            "RR",
            "mean",
            "fric%",
            "pass",
            "EV",
            ">=300",
            "beats_wf_base",
            "all_pos",
            "improving",
        ]
    ]
    holdout = results[results["split"] == "holdout"].copy()
    holdout = holdout.sort_values(["strategy", "filter_kind", "filter"])
    for row in holdout.itertuples(index=False):
        flags = stability_flags(wf, row.strategy, row.filter)
        rows.append(
            [
                row.strategy,
                row.filter,
                row.filter_kind,
                str(int(row.n_trades)),
                pct(row.win_rate),
                f"{row.realized_rr:.3f}",
                money(row.mean_pnl),
                pct(row.friction_pct_avg_gross_win),
                pct(row.pass_rate),
                money(row.ev_per_eval),
                "YES" if row.meaningful_holdout else "NO",
                "YES" if beats_baseline_each_bucket(wf, row.strategy, row.filter) else "NO",
                "YES" if flags["all_positive"] else "NO",
                "YES" if flags["improving"] else "NO",
            ]
        )
    print_table(rows)
    print()


def print_walk_forward(wf: pd.DataFrame) -> None:
    print("WALK-FORWARD 6M STABILITY")
    rows = [["strategy", "filter", "bucket", "start", "end", "trades", "win", "RR", "mean"]]
    ordered = wf.sort_values(["strategy", "filter_kind", "filter", "bucket"])
    for row in ordered.itertuples(index=False):
        rows.append(
            [
                row.strategy,
                row.filter,
                str(int(row.bucket)),
                row.start,
                row.end,
                str(int(row.n_trades)),
                pct(row.win_rate),
                f"{row.realized_rr:.3f}",
                money(row.mean_pnl),
            ]
        )
    print_table(rows)
    print()


def print_verdict(results: pd.DataFrame, wf: pd.DataFrame) -> None:
    holdout = results[results["split"] == "holdout"].copy()
    verdict_rows = []
    for row in holdout[holdout["filter"] != "baseline"].itertuples(index=False):
        baseline = holdout[(holdout["strategy"] == row.strategy) & (holdout["filter"] == "baseline")].iloc[0]
        flags = stability_flags(wf, row.strategy, row.filter)
        beats_baseline = (
            row.n_trades >= MIN_HOLDOUT_TRADES
            and row.win_rate > baseline.win_rate
            and row.realized_rr >= baseline.realized_rr
            and beats_baseline_each_bucket(wf, row.strategy, row.filter)
        )
        stable = flags["all_positive"] or flags["improving"]
        if beats_baseline and stable:
            verdict_rows.append(row)

    if verdict_rows:
        best = max(verdict_rows, key=lambda row: row.ev_per_eval)
        print(
            "VERDICT: FILTER CANDIDATE SURVIVED stability gate: "
            f"{best.strategy} {best.filter} trades={int(best.n_trades)} "
            f"win={best.win_rate:.2%} RR={best.realized_rr:.3f} "
            f"EV=${best.ev_per_eval:.2f}"
        )
        return

    print(
        "VERDICT: NO filter beat the unfiltered baseline while also passing the "
        "walk-forward stability test across all 4 buckets. Any aggregate improvement is not stable enough to trust."
    )


def stability_flags(wf: pd.DataFrame, strategy: str, filter_name: str) -> dict[str, bool]:
    subset = wf[(wf["strategy"] == strategy) & (wf["filter"] == filter_name)].sort_values("bucket")
    means = [float(value) for value in subset["mean_pnl"].tolist()]
    if len(means) < 4:
        return {"all_positive": False, "improving": False}
    all_positive = all(value > 0.0 for value in means[:4])
    improving = all(next_value > value for value, next_value in zip(means[:4], means[1:4]))
    return {"all_positive": all_positive, "improving": improving}


def beats_baseline_each_bucket(wf: pd.DataFrame, strategy: str, filter_name: str) -> bool:
    if filter_name == "baseline":
        return False
    candidate = bucket_means(wf, strategy, filter_name)
    baseline = bucket_means(wf, strategy, "baseline")
    if len(candidate) < 4 or len(baseline) < 4:
        return False
    return all(candidate_mean > baseline_mean for candidate_mean, baseline_mean in zip(candidate[:4], baseline[:4]))


def bucket_means(wf: pd.DataFrame, strategy: str, filter_name: str) -> list[float]:
    subset = wf[(wf["strategy"] == strategy) & (wf["filter"] == filter_name)].sort_values("bucket")
    return [float(value) for value in subset["mean_pnl"].tolist()]


if __name__ == "__main__":
    sys.exit(main())
