"""Stage 1 of VA_REACCEPTANCE_PREREGISTRATION.md: value-area proxy fidelity.

Reads price levels only. Computes no trade, no return, and no outcome. Uses the
footprint file alone, so proxy and truth come from the same trades.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.value_area import value_area


FOOTPRINT = ROOT / "data" / "sierra" / "tick" / "NQ_continuous_1m_footprint.parquet"
OUT = ROOT / "data" / "strategy_research" / "va_proxy_fidelity_2026-09-22.json"
TICK = 0.25
TOLERANCE_TICKS = 4
PASS_RATE = 0.80
FRACTION = 0.70


def main() -> int:
    cells = pd.read_parquet(FOOTPRINT, columns=["minute", "price", "volume", "bar_close", "session"])
    local = cells["minute"].dt.tz_convert("America/New_York").dt.time
    cells = cells.loc[(local >= pd.Timestamp("09:30").time()) & (local < pd.Timestamp("16:00").time())]
    print("STEP 0 DATA SANITY")
    print(f"path={FOOTPRINT.relative_to(ROOT)} rth_cells={len(cells)} sessions={cells['session'].nunique()}")
    print(f"minute_min={cells['minute'].min()} minute_max={cells['minute'].max()}")
    print(f"nonfinite_price={int((~np.isfinite(cells['price'].to_numpy(float))).sum())} zero_volume_cells={int((cells['volume'] == 0).sum())}")

    rows = []
    for session, group in cells.groupby("session", sort=True):
        true_profile = group.groupby("price")["volume"].sum().astype(float).to_dict()
        minutes = group.groupby("minute").agg(close=("bar_close", "last"), volume=("volume", "sum"))
        proxy_profile = minutes.groupby("close")["volume"].sum().astype(float).to_dict()
        t_poc, t_val, t_vah = value_area(true_profile, FRACTION)
        p_poc, p_val, p_vah = value_area(proxy_profile, FRACTION)
        rows.append(
            {
                "session": str(session),
                "vah_err_ticks": abs(p_vah - t_vah) / TICK,
                "val_err_ticks": abs(p_val - t_val) / TICK,
                "poc_err_ticks": abs(p_poc - t_poc) / TICK,
                "va_width_ticks": (t_vah - t_val) / TICK,
            }
        )

    frame = pd.DataFrame(rows)
    both_ok = (frame["vah_err_ticks"] <= TOLERANCE_TICKS) & (frame["val_err_ticks"] <= TOLERANCE_TICKS)
    pass_rate = float(both_ok.mean())
    result = {
        "preregistration": "VA_REACCEPTANCE_PREREGISTRATION.md",
        "stage": 1,
        "outcomes_computed": False,
        "sessions": int(len(frame)),
        "tolerance_ticks": TOLERANCE_TICKS,
        "required_pass_rate": PASS_RATE,
        "both_edges_within_tolerance_rate": pass_rate,
        "verdict": "PASS" if pass_rate >= PASS_RATE else "FAIL",
        "vah_err_ticks_median": float(frame["vah_err_ticks"].median()),
        "vah_err_ticks_p95": float(frame["vah_err_ticks"].quantile(0.95)),
        "val_err_ticks_median": float(frame["val_err_ticks"].median()),
        "val_err_ticks_p95": float(frame["val_err_ticks"].quantile(0.95)),
        "poc_err_ticks_median_diagnostic": float(frame["poc_err_ticks"].median()),
        "true_va_width_ticks_median": float(frame["va_width_ticks"].median()),
    }
    print()
    print(json.dumps(result, indent=2))
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"saved={OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
