"""Run the same fixture schedules through backtesting.py (kernc) in the isolated extvenv.

Matched semantics (verified from backtesting/backtesting.py source, v0.6.6):
- trade_on_close=True: market entry placed in next() at bar i fills at Close[i] (time_index i-1 path).
- SL/TP bracket via buy/sell(sl=, tp=); SL order inserted at queue head -> SL processed before TP
  on the same bar (stop-first). SL gapped through -> fills at Open (min/max(open, stop)).
- TP limit gapped through -> fills at Open (better than limit)  [Heimdall fills at target: expected diff].
- Forced flatten: position.close() at the flatten bar -> fills at that bar's Close.
- Commission: fixed $0.50 per fill => $1.00 round turn (MNQ). spread=0.
- Prices are multiplied by the MNQ point value (2.0) so 1 unit PnL == USD.
Strategy-level rules mirrored from Heimdall's loop: no entry on the bar a trade exited, no entry
on the last bar of a session, one position at a time.
"""
from __future__ import annotations

import json
import warnings
from datetime import time
from pathlib import Path

import pandas as pd
from backtesting import Backtest, Strategy

HERE = Path(__file__).resolve().parent
PV = 2.0
TICK = 0.25
warnings.filterwarnings("ignore")


def run_one(bars: pd.DataFrame, entries: list, flatten: str) -> list:
    sched = {pd.Timestamp(e["ts"]): e for e in entries}
    flat_t = time.fromisoformat(flatten)
    last_bar = set(bars.groupby("session")["ts_et"].max())
    data = pd.DataFrame({"Open": bars["open"] * PV, "High": bars["high"] * PV, "Low": bars["low"] * PV,
                         "Close": bars["close"] * PV, "Volume": bars["volume"]})
    data.index = pd.DatetimeIndex(bars["ts_et"])

    class Sched(Strategy):
        def init(self):
            pass

        def next(self):
            i = len(self.data) - 1
            t = self.data.index[-1]
            if self.position and (t.time() >= flat_t or t in last_bar):
                self.position.close()
                return
            if self.position:
                return
            if self.closed_trades and self.closed_trades[-1].exit_bar == i:
                return  # Heimdall: no entry on the exit bar
            e = sched.get(t)
            if e is None or t in last_bar:
                return
            side = int(e["side"])
            c = float(self.data.Close[-1])
            sl = c - side * e["stop_ticks"] * TICK * PV
            tp = c + side * e["target_ticks"] * TICK * PV
            if side > 0:
                self.buy(size=1, sl=sl, tp=tp)
            else:
                self.sell(size=1, sl=sl, tp=tp)

    bt = Backtest(data, Sched, cash=10_000_000, commission=(0.5, 0.0), spread=0.0, margin=1.0,
                  trade_on_close=True, hedging=False, exclusive_orders=False, finalize_trades=True)
    st = bt.run()
    tr = st._trades
    return [{"entry_ts": str(r.EntryTime), "exit_ts": str(r.ExitTime), "side": 1 if r.Size > 0 else -1,
             "entry": r.EntryPrice / PV, "exit": r.ExitPrice / PV,
             "sl": (r.SL / PV) if pd.notna(r.SL) else None, "tp": (r.TP / PV) if pd.notna(r.TP) else None,
             "pnl": float(r.PnL), "commission": float(r.Commission)} for r in tr.itertuples()]


if __name__ == "__main__":
    import backtesting
    bars = pd.read_parquet(HERE / "bars.parquet")
    scheds = json.loads((HERE / "schedules.json").read_text(encoding="utf-8"))
    out = {"engine": f"backtesting.py {backtesting.__version__}", "results": {}}
    for name, spec in scheds.items():
        b = bars[bars["session"].isin(set(spec["sessions"]))].reset_index(drop=True)
        out["results"][name] = run_one(b, spec["entries"], spec["flatten"])
    (HERE / "ext_trades.json").write_text(json.dumps(out, indent=0), encoding="utf-8")
    print(out["engine"], {k: len(v) for k, v in out["results"].items()})
