"""Agent 2 Dhesi v3 pipeline dry run on SYNTHETIC random-walk data (no market data read).

Purposes: (1) runtime at full untouched-window scale, (2) frozen-code vs reference-engine agreement on
13 years of never-seen structure, (3) null control: a zero-drift walk must not produce PASS.
Imports the frozen validator read-only; never calls primary()/secondary(); writes only to this folder.
"""
import sys, time, json, importlib.util
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[3]; HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("v", ROOT/"workspace/dhesi_adjudication_agent1_2026-09-23/dhesi_v3_validator.py")
V = importlib.util.module_from_spec(spec); spec.loader.exec_module(V)
from core.alpha.inversion_model_v3 import InversionModelV3

def synth(seed, start="2011-09-18", end="2024-10-01", p0=2300.0, drift_ann=0.0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, end, freq="1min", tz="America/New_York", inclusive="left")
    wd, h = idx.weekday, idx.hour
    live = ~((wd == 5) | ((wd == 4) & (h >= 17)) | ((wd == 6) & (h < 18)) | (h == 17))
    idx = idx[live]
    n = len(idx); sig = 0.013 / np.sqrt(1380)            # ~1.3% daily vol
    rth = (idx.time >= pd.Timestamp("09:30").time()) & (idx.time <= pd.Timestamp("16:00").time())
    s = np.where(rth, sig * 1.6, sig * 0.6)               # more RTH activity
    r = rng.standard_normal((n, 4)) * (s[:, None] / 2) + drift_ann / (252 * 1380) / 4
    path = p0 * np.exp(np.cumsum(r.reshape(-1)))
    q = lambda x: np.round(x / 0.25) * 0.25
    paths = path.reshape(n, 4)
    o = q(np.r_[p0, paths[:-1, 3]]); c = q(paths[:, 3])
    hi = q(np.maximum(paths.max(1), np.maximum(o, c))); lo = q(np.minimum(paths.min(1), np.minimum(o, c)))
    vol = rng.integers(50, 2000, n).astype(float)
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": c, "volume": vol}, index=idx.tz_convert("UTC"))

def run(seed):
    out = {"seed": seed}; t0 = time.time()
    raw = V.truncate_untouched(synth(seed)); out["rows"] = len(raw); out["last_utc"] = str(raw.index.max())
    keep = set(V.sessions_after_burn_in(raw)); out["eval_sessions"] = len(keep)
    t1 = time.time(); m = InversionModelV3(contract="MNQ")
    fr = m.trades_frame(m._run_backtest(raw).trades); fr = fr[fr["session"].isin(keep)].reset_index(drop=True)
    out["frozen_sec"] = round(time.time() - t1, 1)
    t2 = time.time(); ref = V.reference_run(raw, V.INSTR["MNQ"], V.floor_points(V.INSTR["MNQ"]), V.NQ_DISP_POINTS)
    ref = ref[ref["session"].isin(keep)].reset_index(drop=True) if len(ref) else ref
    out["ref_sec"] = round(time.time() - t2, 1)
    cols = ["entry_ts", "exit_ts", "side", "entry_price", "stop_price", "tp1_price", "exit_price", "contracts", "pnl"]
    same_n = len(fr) == len(ref); out["n_frozen"], out["n_ref"] = len(fr), len(ref)
    mism = {}
    if same_n and len(fr):
        for c in cols:
            a, b = fr[c], ref[c]
            mism[c] = int((a.astype(str) != b.astype(str)).sum()) if c.endswith("ts") else int((~np.isclose(a.astype(float), b.astype(float))).sum())
    out["field_mismatches"] = mism
    out["result"] = V.evaluate(fr, V.INSTR["MNQ"]) if len(fr) else {"n": 0}
    out["total_sec"] = round(time.time() - t0, 1)
    fr.to_csv(HERE / f"synthetic_seed{seed}_frozen_trades.csv", index=False)
    if len(ref): ref.to_csv(HERE / f"synthetic_seed{seed}_ref_trades.csv", index=False)
    return out

if __name__ == "__main__":
    res = [run(int(s)) for s in sys.argv[1:]]
    (HERE / "dryrun_result.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1, default=str))
