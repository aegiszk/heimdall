"""Build shared bar data + deterministic entry schedules for the differential test.

Runs in the project .venv. Writes bars.parquet (RTH-only MNQ 1m, ts tz-aware UTC + ts_et naive)
and schedules.json. Both engines read ONLY these files, so signals are identical by construction.
"""
from __future__ import annotations

import json
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TICK = 0.25

raw = pd.read_parquet(ROOT / "data" / "MNQ_1m.parquet")[["open", "high", "low", "close", "volume"]]
et = raw.index.tz_convert("America/New_York")
mask = (et.weekday < 5) & (et.time >= time(9, 30)) & (et.time < time(16, 0))
rth = raw.loc[mask].copy()
rth["ts_et"] = rth.index.tz_convert("America/New_York").tz_localize(None)
rth["session"] = rth["ts_et"].dt.date
full = rth.groupby("session").size()
full_sessions = [s for s, n in full.items() if n == 390]

# Fixture window: 20 consecutive full sessions spanning the 2025-03-09 US DST change.
fx_sessions = [s for s in full_sessions if s >= pd.Timestamp("2025-02-24").date()][:20]
# Random window: 150 full sessions drawn (seeded) from the whole file, sorted.
rng = np.random.default_rng(20260923)
rnd_sessions = sorted(rng.choice(np.array(full_sessions, dtype=object), size=150, replace=False).tolist())

def sched_fixed(sessions, hhmm, side, stop_t, tgt_t):
    return [{"ts": f"{s} {hhmm}:00", "side": side, "stop_ticks": stop_t, "target_ticks": tgt_t} for s in sessions]

schedules = {
    # F1 symmetric 1R bracket, long at 10:00 bar
    "F1_long_1000_20x20": {"flatten": "15:50", "sessions": [str(s) for s in fx_sessions],
                           "entries": sched_fixed(fx_sessions, "10:00", 1, 20, 20)},
    # F2 short 2R bracket at 11:30 bar
    "F2_short_1130_40x80": {"flatten": "15:50", "sessions": [str(s) for s in fx_sessions],
                            "entries": sched_fixed(fx_sessions, "11:30", -1, 40, 80)},
    # F3 very wide bracket -> mostly forced session flatten
    "F3_long_1400_400x400_flatten": {"flatten": "15:50", "sessions": [str(s) for s in fx_sessions],
                                     "entries": sched_fixed(fx_sessions, "14:00", 1, 400, 400)},
    # F4 tight 3x3 tick brackets, alternating side every 30 min -> same-bar ambiguity + re-entry rules
    "F4_tight_3x3_every30m": {"flatten": "15:50", "sessions": [str(s) for s in fx_sessions],
                              "entries": [
                                  {"ts": f"{s} {h:02d}:{m:02d}:00", "side": 1 if (h * 60 + m) // 30 % 2 == 0 else -1,
                                   "stop_ticks": 3, "target_ticks": 3}
                                  for s in fx_sessions for h in range(10, 15) for m in (0, 30)]},
}

rnd_entries = []
for s in rnd_sessions:
    minutes = sorted(rng.choice(np.arange(9 * 60 + 31, 15 * 60 + 40), size=2, replace=False).tolist())
    for mm in minutes:
        rnd_entries.append({"ts": f"{s} {mm // 60:02d}:{mm % 60:02d}:00",
                            "side": int(rng.choice([-1, 1])),
                            "stop_ticks": int(rng.integers(4, 81)),
                            "target_ticks": int(rng.integers(4, 81))})
schedules["R_random_300_attempts"] = {"flatten": "15:50", "sessions": [str(s) for s in rnd_sessions],
                                      "entries": rnd_entries}

need = set(fx_sessions) | set(rnd_sessions)
bars = rth[rth["session"].isin(need)].copy()
bars["ts"] = bars.index
bars = bars.reset_index(drop=True)
bars["session"] = bars["session"].astype(str)
bars.to_parquet(HERE / "bars.parquet", index=False)
(HERE / "schedules.json").write_text(json.dumps(schedules, indent=1), encoding="utf-8")
print(f"bars={len(bars)} sessions={bars['session'].nunique()} fx={fx_sessions[0]}..{fx_sessions[-1]} "
      f"rnd={rnd_sessions[0]}..{rnd_sessions[-1]} rnd_attempts={len(rnd_entries)}")
print({k: len(v["entries"]) for k, v in schedules.items()})
