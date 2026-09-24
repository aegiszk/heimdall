"""Differential test, step 3 (run with extvenv, Python 3.12, backtesting.py 0.6.6).

Matched semantics:
  * market entry at the signal bar's CLOSE      -> trade_on_close=True
  * stop/target checked from the NEXT bar        -> bt reprocesses SL/TP on the fill bar (bar i+1)
  * SL before TP when both inside one bar        -> bt inserts SL orders at queue head
  * gap through stop fills at the open           -> bt stop-market: min/max(open, stop)
  * one RT commission $1 (MNQ, $2/pt)            -> commission callable 0.25 pt per side
  * no re-entry on the bar a trade exited        -> enforced in Strategy.next
  * session flatten at first bar >= 16:45 ET or last session bar, at that bar's close
    -> position.close() in next(); bt fills non-contingent market order at prev close
Unmatchable (neutralised post-hoc in diff_compare.py, see report):
  * Heimdall fixed 1-tick slippage on entry, stop and flatten fills (bt has only relative spread)
  * Heimdall fills a gapped-through TARGET at the target; bt fills a limit at the better open
"""
from __future__ import annotations

import json
import warnings
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd
from backtesting import Backtest, Strategy

HERE = Path(__file__).resolve().parent
TICK = 0.25
FLATTEN = time(16, 45)
ENTRY_START, ENTRY_END = time(9, 45), time(15, 30)


def make_strategy(specs: list[dict], max_per_day: int, last_bar_flags: np.ndarray):
    spec_map = {pd.Timestamp(s["ts"]): (k, s) for k, s in enumerate(specs)}

    class SpecStrategy(Strategy):
        def init(self):
            self.day = None
            self.taken = 0

        def next(self):
            i = len(self.data) - 1
            ts = self.data.index[-1]
            if ts.normalize() != self.day:
                self.day, self.taken = ts.normalize(), 0
            t = ts.time()
            if self.position:
                if t >= FLATTEN or last_bar_flags[i]:
                    self.position.close()
                return
            # production rule: no new entry on the bar where a trade exited
            if self.closed_trades and self.closed_trades[-1].exit_bar == i:
                return
            if self.taken >= max_per_day or not (ENTRY_START <= t <= ENTRY_END) or last_bar_flags[i]:
                return
            hit = spec_map.get(ts)
            if hit is None:
                return
            k, s = hit
            c = float(self.data.Close[-1])
            side = s["side"]
            sl = c - side * s["stop_ticks"] * TICK
            tp = c + side * s["target_ticks"] * TICK
            if side > 0:
                self.buy(size=1, sl=sl, tp=tp, tag=k)
            else:
                self.sell(size=1, sl=sl, tp=tp, tag=k)
            self.taken += 1

    return SpecStrategy


def main() -> None:
    import backtesting

    data = pd.read_parquet(HERE / "diff_data_rth.parquet")
    df = pd.DataFrame(
        {"Open": data["open"], "High": data["high"], "Low": data["low"], "Close": data["close"], "Volume": data["volume"]}
    )
    df.index = pd.DatetimeIndex(data["ts"])
    day = df.index.normalize()
    last_bar = np.r_[day[1:] != day[:-1], True]
    specs = json.loads((HERE / "diff_specs.json").read_text(encoding="utf-8"))
    for name, sp in specs.items():
        strat = make_strategy(sp, 2 if name.startswith("F3") else 1, last_bar)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bt = Backtest(df, strat, cash=10_000_000, commission=lambda size, price: 0.25 * abs(size),
                          trade_on_close=True, hedging=False, exclusive_orders=False, finalize_trades=True)
            st = bt.run()
        tr = st["_trades"].copy()
        tr.to_csv(HERE / f"bt_trades_{name}.csv", index=False)
        print(name, "backtesting.py", backtesting.__version__, "trades", len(tr), "PnL_pts", round(tr["PnL"].sum(), 4))


if __name__ == "__main__":
    main()
