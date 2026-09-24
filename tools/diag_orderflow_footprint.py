"""Diagnostic funnel for dead, frozen order-flow footprint v2; no tuning."""
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.orderflow_footprint import TICK, _bars, volume_area


def main() -> None:
    data = pd.read_parquet(ROOT / "data/sierra/tick/NQ_continuous_1m_footprint.parquet")
    sessions = sorted(data.session.unique())
    grouped = {session: frame for session, frame in data.groupby("session", sort=True)}
    stages = {
        "touch": 0,
        "reject_inside_1tick": 0,
        "extreme_aggressor_ge20": 0,
        "imbalance_ge3x": 0,
        "concentration_ge20pct": 0,
        "full_candidate": 0,
    }
    for index in range(20, len(sessions)):
        val, vah = volume_area(grouped[sessions[index - 1]])
        bars = _bars(grouped[sessions[index]])
        local_minutes = bars.index.tz_convert("America/New_York").hour * 60 + bars.index.tz_convert("America/New_York").minute
        bars = bars[local_minutes <= 15 * 60 + 30]
        for _, bar in bars.iterrows():
            for side in (-1, 1):
                touch = bar.high >= vah if side < 0 else bar.low <= val
                if not touch:
                    continue
                stages["touch"] += 1
                reject = bar.close <= vah - TICK if side < 0 else bar.close >= val + TICK
                if not reject:
                    continue
                stages["reject_inside_1tick"] += 1
                aggressive = bar.short_ask if side < 0 else bar.long_bid
                opposing = bar.short_bid if side < 0 else bar.long_ask
                total = bar.ask_volume if side < 0 else bar.bid_volume
                if aggressive < 20:
                    continue
                stages["extreme_aggressor_ge20"] += 1
                if aggressive < 3 * max(1.0, opposing):
                    continue
                stages["imbalance_ge3x"] += 1
                if aggressive < 0.20 * max(1.0, total):
                    continue
                stages["concentration_ge20pct"] += 1
                stages["full_candidate"] += 1
    print("ORDERFLOW FOOTPRINT V2 DIAGNOSTIC (NO PARAMETER SWEEP)")
    for key, value in stages.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
