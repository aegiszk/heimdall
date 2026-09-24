"""Run the fixture schedules through Heimdall's UNMODIFIED shared simulator
(core.alpha.prop_futures.FuturesRTHModel._simulate/_exit_price/_close_trade).

Two modes:
  base      : production code as-is (1-tick entry/stop/flatten slippage via TICK_SIZE).
  zero_slip : prop_futures.TICK_SIZE monkeypatched to 0.0 IN THIS PROCESS ONLY (no file edit),
              which removes every slippage tick; used for the matched-semantics comparison.
Only a fixture subclass (entry schedule, window, flatten time) is defined here.
"""
from __future__ import annotations

import json
import sys
from datetime import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

import core.alpha.prop_futures as pf  # noqa: E402

FIXTURE_TICK = 0.25  # bracket geometry constant, independent of pf.TICK_SIZE


class ScheduleModel(pf.FuturesRTHModel):
    entry_start = time(9, 30)
    entry_end = time(15, 59)

    def __init__(self, schedule: dict, flatten: str):
        super().__init__("MNQ")
        self.flatten_time = time.fromisoformat(flatten)
        self._sched = {pd.Timestamp(e["ts"]): e for e in schedule}

    @property
    def name(self) -> str:
        return "diff_fixture"

    def _max_trades_day(self) -> int:
        return 10_000

    def _entry_plan(self, frame, i):
        e = self._sched.get(frame.loc[i, "_ts"])
        if e is None:
            return None
        side = int(e["side"])
        close = float(frame.loc[i, "close"])
        return pf.EntryPlan(side=side,
                            stop_price=close - side * e["stop_ticks"] * FIXTURE_TICK,
                            target_price=close + side * e["target_ticks"] * FIXTURE_TICK)


def run(mode: str) -> dict:
    if mode == "zero_slip":
        pf.TICK_SIZE = 0.0
    else:
        pf.TICK_SIZE = 0.25
    bars = pd.read_parquet(HERE / "bars.parquet")
    scheds = json.loads((HERE / "schedules.json").read_text(encoding="utf-8"))
    out = {}
    for name, spec in scheds.items():
        df = bars[bars["session"].isin(set(spec["sessions"]))][["ts", "open", "high", "low", "close", "volume"]].copy()
        df["vwap"] = df["close"]
        model = ScheduleModel(spec["entries"], spec["flatten"])
        frame = model._prepare_frame(df)
        _, _, _, trades = model._simulate(frame)
        out[name] = [{"entry_ts": str(t.entry_ts), "exit_ts": str(t.exit_ts), "side": t.side,
                      "entry": t.entry_price, "exit": t.exit_price, "stop": t.stop_price,
                      "target": t.target_price, "pnl": t.pnl, "reason": t.reason} for t in trades]
    return out


if __name__ == "__main__":
    res = {"zero_slip": run("zero_slip"), "base": run("base")}
    (HERE / "heimdall_trades.json").write_text(json.dumps(res, indent=0), encoding="utf-8")
    for mode, d in res.items():
        print(mode, {k: len(v) for k, v in d.items()})
