"""Differential test, step 2 (project .venv): run fixtures through the PRODUCTION shared RTH simulator.

Only _entry_plan/_max_trades_day are supplied (the abstract hooks). _simulate/_exit_price/_close_trade
/_market_entry_price are the unmodified production methods of core.alpha.prop_futures.FuturesRTHModel.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from core.alpha.prop_futures import TICK_SIZE, EntryPlan, FuturesRTHModel  # noqa: E402


class SpecFixture(FuturesRTHModel):
    def __init__(self, specs: list[dict], max_per_day: int):
        super().__init__("MNQ")
        self.specs = {pd.Timestamp(s["ts"]): s for s in specs}
        self.max_per_day = max_per_day

    @property
    def name(self):
        return "diff_spec_fixture"

    def _max_trades_day(self) -> int:
        return self.max_per_day

    def _entry_plan(self, frame, i):
        s = self.specs.get(frame.at[i, "_ts"])
        if s is None:
            return None
        close = float(frame.at[i, "close"])
        side = int(s["side"])
        return EntryPlan(
            side=side,
            stop_price=close - side * s["stop_ticks"] * TICK_SIZE,
            target_price=close + side * s["target_ticks"] * TICK_SIZE,
        )


def main() -> None:
    data = pd.read_parquet(HERE / "diff_data_rth.parquet")
    specs = json.loads((HERE / "diff_specs.json").read_text(encoding="utf-8"))
    for name, sp in specs.items():
        model = SpecFixture(sp, max_per_day=2 if name.startswith("F3") else 1)
        frame = model._prepare_frame(data)
        _, _, _, trades = model._simulate(frame)
        out = pd.DataFrame([t.__dict__ for t in trades])
        out.to_csv(HERE / f"heimdall_trades_{name}.csv", index=False)
        print(name, "specs", len(sp), "trades", len(out), "total_pnl", round(out["pnl"].sum(), 2))


if __name__ == "__main__":
    main()
