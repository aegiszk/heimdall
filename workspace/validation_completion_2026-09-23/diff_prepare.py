"""Differential test, step 1 (run with project .venv): build shared data + fixture specs.

Writes:
  diff_data_rth.parquet  -- MNQ 1m, ET-naive 'ts', 09:30-16:59 ET, weekdays only
  diff_specs.json        -- fixture entry specs (ET bar-open timestamp, side, stop/target ticks)
No core/ file is modified. Deterministic (seeded).
"""
from __future__ import annotations

import json
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main() -> None:
    raw = pd.read_parquet(ROOT / "data" / "MNQ_1m.parquet")
    et = raw.index.tz_convert("America/New_York").tz_localize(None)
    df = pd.DataFrame(
        {
            "ts": et,
            "open": raw["open"].to_numpy(float),
            "high": raw["high"].to_numpy(float),
            "low": raw["low"].to_numpy(float),
            "close": raw["close"].to_numpy(float),
            "volume": raw["volume"].to_numpy(float),
        }
    )
    t = df["ts"].dt.time
    df = df[(t >= time(9, 30)) & (t <= time(16, 59)) & (df["ts"].dt.weekday < 5)].reset_index(drop=True)
    df["vwap"] = df["close"]  # required column for FuturesRTHModel._prepare_frame; unused by fixtures
    df.to_parquet(HERE / "diff_data_rth.parquet")

    ts_set = set(df["ts"])
    sessions = sorted(df["ts"].dt.normalize().unique())
    specs: dict[str, list[dict]] = {"F1_long_1000_20x20": [], "F2_short_1530_80x240": [], "F3_two_per_day_6x6": [], "F4_random_200": []}

    def add(name, ts, side, stop, target):
        if ts in ts_set:
            specs[name].append({"ts": str(ts), "side": int(side), "stop_ticks": int(stop), "target_ticks": int(target)})

    for s in sessions:
        s = pd.Timestamp(s)
        add("F1_long_1000_20x20", s + pd.Timedelta(hours=10), 1, 20, 20)
        add("F2_short_1530_80x240", s + pd.Timedelta(hours=15, minutes=30), -1, 80, 240)
        add("F3_two_per_day_6x6", s + pd.Timedelta(hours=9, minutes=45), 1, 6, 6)
        add("F3_two_per_day_6x6", s + pd.Timedelta(hours=13, minutes=30), -1, 6, 6)

    rng = np.random.default_rng(20260923)
    chosen = rng.choice(len(sessions), size=200, replace=False)
    for k in sorted(chosen):
        s = pd.Timestamp(sessions[k])
        minute = int(rng.integers(9 * 60 + 45, 15 * 60 + 30 + 1))
        ts = s + pd.Timedelta(minutes=minute)
        side = int(rng.choice([-1, 1]))
        add("F4_random_200", ts, side, int(rng.integers(4, 121)), int(rng.integers(4, 161)))

    (HERE / "diff_specs.json").write_text(json.dumps(specs, indent=1), encoding="utf-8")
    print("rows", len(df), "sessions", len(sessions), {k: len(v) for k, v in specs.items()})


if __name__ == "__main__":
    main()
