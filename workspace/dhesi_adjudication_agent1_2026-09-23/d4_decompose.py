"""Agent 1 forensic D4 decomposition. DEVELOPMENT data only (data/MNQ_1m.parquet).

Separates v3 `stop_guard` into its two components:
  side  : stop must be on the protective side of the slipped entry (bias*(entry-stop) > 0)
  floor : stop distance must be >= 10.0 points (MIN_STOP_POINTS)
and the two possible failure actions:
  continue : try the next LTF inversion in the same setup (what v3 code does)
  skip     : abandon the setup (literal reading of prereg "skip the setup")

Everything else is the frozen v2/v3 code path. No parameter is tuned.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.alpha.inversion_model import InversionModel, ranges_overlap  # noqa: E402
from core.alpha.inversion_model_v3 import InversionModelV3, MIN_STOP_POINTS  # noqa: E402

OUT = Path(__file__).resolve().parent
OHLCV = ["open", "high", "low", "close", "volume"]


class Variant(InversionModelV3):
    def __init__(self, *, mode: str, action: str = "continue", **flags):
        super().__init__(contract="MNQ", stop_guard=False, **flags)
        self.mode, self.action = mode, action
        self.rejections: list[dict] = []

    def _first_entry_trade_v3(self, frame, idx_by_ts, ltf_events, swings_15m, pools, sweep, inversion, retrace, not_before):
        for event in ltf_events:
            if event.formed_ts < retrace["ts"] or event.inverted_ts <= retrace["ts"]:
                continue
            if not_before is not None and event.inverted_ts <= not_before:
                continue
            if event.inverted_ts.time() < pd.Timestamp("10:00").time() or event.inverted_ts.time() > pd.Timestamp("16:00").time():
                continue
            if not ranges_overlap(event.formation_low, event.formation_high, inversion.zone_low, inversion.zone_high):
                continue
            if event.inverted_ts not in idx_by_ts:
                continue
            entry_i = idx_by_ts[event.inverted_ts]
            stop = self._stop_from_recent_swing(swings_15m, event.bias, inversion.ts, event.inverted_ts, sweep.session)
            if stop is None:
                continue
            entry = self._entry_price(event.bias, float(event.close))
            dist = event.bias * (entry - stop)
            bad = (self.mode == "side" and dist <= 0) or (self.mode == "side_floor" and dist < MIN_STOP_POINTS) \
                or (self.mode == "floor_abs" and abs(entry - stop) < MIN_STOP_POINTS)
            if bad:
                self.rejections.append({"session": str(sweep.session), "ts": str(event.inverted_ts), "bias": event.bias,
                                        "entry": entry, "stop": stop, "signed_dist": dist})
                if self.action == "skip":
                    return None
                continue
            stop_ticks = abs(entry - stop) / 0.25
            contracts = self._allowed_contracts(stop_ticks)
            if contracts <= 0:
                continue
            risk_dollars = contracts * abs(entry - stop) * self.point_value
            if risk_dollars <= 0 or risk_dollars > 325.0 + 1e-9:
                continue
            targets = self._targets(entry, stop, event.bias, pools)
            if targets is None:
                continue
            tp1, tp1_pool, runner_target, runner_pool = targets
            return self._simulate_trade(frame, entry_i, event.bias, entry, stop, tp1, runner_target, contracts,
                                        risk_dollars, inversion.timeframe, sweep.pool_kind, tp1_pool, runner_pool)
        return None


V2_FLAGS = dict(htf_24h=False, early_sweeps=False, session_pools=False, attempts=False)
ALL_ON = dict(htf_24h=True, early_sweeps=True, session_pools=True, attempts=True)


def summarize(tr: pd.DataFrame) -> dict:
    if tr.empty:
        return {"n": 0}
    return {"n": int(len(tr)), "total": round(float(tr.pnl.sum()), 2), "mean": round(float(tr.pnl.mean()), 2),
            "win": round(float((tr.pnl > 0).mean()), 4), "long_n": int((tr.side > 0).sum()),
            "long_total": round(float(tr.loc[tr.side > 0, "pnl"].sum()), 2), "short_n": int((tr.side < 0).sum()),
            "short_total": round(float(tr.loc[tr.side < 0, "pnl"].sum()), 2)}


def main() -> int:
    dev = pd.read_parquet(ROOT / "data" / "MNQ_1m.parquet")[OHLCV]
    runs = {
        "v2_frozen_class": (InversionModel(contract="MNQ"), None),
        "v2_flags_none": (Variant(mode="none", **V2_FLAGS), None),
        "v2+side_continue": (Variant(mode="side", **V2_FLAGS), None),
        "v2+side_skip": (Variant(mode="side", action="skip", **V2_FLAGS), None),
        "v2+side_floor_continue(=stop_guard)": (Variant(mode="side_floor", **V2_FLAGS), None),
        "v2+side_floor_skip": (Variant(mode="side_floor", action="skip", **V2_FLAGS), None),
        "v3_all_but_guard": (Variant(mode="none", **ALL_ON), None),
        "v3_side_only": (Variant(mode="side", **ALL_ON), None),
        "v3_full(=side_floor_continue)": (Variant(mode="side_floor", **ALL_ON), None),
        "v3_official_class": (InversionModelV3(contract="MNQ"), None),
    }
    only = sys.argv[1:]
    report, frames = {}, {}
    for name, (model, _) in runs.items():
        if only and name not in only:
            continue
        tr = model.trades_frame(model._run_backtest(dev).trades)
        frames[name] = tr
        report[name] = summarize(tr)
        if hasattr(model, "rejections"):
            report[name]["rejections"] = len(model.rejections)
            pd.DataFrame(model.rejections).to_csv(OUT / f"rej_{name.replace('(', '_').replace(')', '').replace('=', '').replace('+', '_')}.csv", index=False)
        tr.to_csv(OUT / f"trades_{name.replace('(', '_').replace(')', '').replace('=', '').replace('+', '_')}.csv", index=False)
        print(name, report[name], flush=True)
    tag = "_".join(only).replace("+", "_").replace("(", "").replace(")", "").replace("=", "") if only else "all"
    (OUT / f"d4_decomposition_{tag}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
