"""Frozen before outcomes (2026-09-23). K>=3 distinct tracked wallets buy the same token (>= $100 each)
within 600 s; signal time T = the 3rd wallet's buy. USD minute candles from GeckoTerminal.
Entry A: close of the candle containing T (<= ~60 s after T). Entry B: close of the first candle
starting >= next minute (~60-120 s). Exit: close of last candle starting <= entry candle + H.
Cost model (S = $500): lp fee 1% per side (FOMO doc: v4 fee field 0-6%), impact 2*S/liquidity per side
(constant-product approximation, liquidity = tape DexScreener USD liquidity, fetched later than the
event -> flagged), gas $0.66 per side (measured median). Baseline: random candle times on the SAME pool
windows (seed 1), same exits and costs. No parameter is tuned on outcomes."""
import os, json, numpy as np, pandas as pd
SP = os.path.dirname(os.path.abspath(__file__))
S, FEE, GAS = 500.0, 0.01, 0.66
H = {"5m": 300, "30m": 1800, "2h": 7200, "6h": 21600}
ev = pd.read_parquet(os.path.join(SP, "cluster_events.parquet")); ev = ev[ev.K == 3]
tape = pd.read_parquet(os.path.join(SP, "fomopulse_tape.parquet"))
tape["liquidity"] = pd.to_numeric(tape.liquidity, errors="coerce"); tape["id"] = tape.id.astype(float)
liq = tape.sort_values("id").groupby("token").liquidity.last()
rng = np.random.default_rng(1)

def path_for(r):
    p = os.path.join(SP, "ohlcv", f"{r.pool}_{r.ts}.json")
    if not os.path.exists(p): return None
    c = json.load(open(p))["ohlcv"]
    if not c: return None
    df = pd.DataFrame(c, columns=["t", "o", "h", "l", "c", "v"]).sort_values("t").reset_index(drop=True)
    return df

def trade(df, t_entry_min, entry_mode):
    if entry_mode == "A":
        cand = df[(df.t >= t_entry_min) & (df.t <= t_entry_min + 300)]
    else:
        cand = df[(df.t >= t_entry_min + 60) & (df.t <= t_entry_min + 360)]
    if cand.empty: return None
    e = cand.iloc[0]; out = {}
    for k, h in H.items():
        if df.t.max() < e.t + h: continue          # window does not reach the horizon
        x = df[df.t <= e.t + h].iloc[-1]
        out[k] = x.c / e.c - 1
    return out

rows, base = [], []
for r in ev.itertuples(index=False):
    df = path_for(r)
    if df is None: continue
    L = liq.get(r.token, np.nan)
    cost = 2 * FEE + (2 * (2 * S / L) if np.isfinite(L) and L > 0 else np.nan) + 2 * GAS / S
    tmin = (r.ts // 60) * 60
    for mode in ("A", "B"):
        g = trade(df, tmin, mode)
        if g: rows.append(dict(token=r.token, mode=mode, cost=cost, liq=L, **g))
    # baseline: 3 random candle starts from this pool's window, excluding +-30 min around the event
    pool_t = df.t[(df.t < df.t.max() - 21600) & ((df.t < tmin - 1800) | (df.t > tmin + 1800))]
    for t0 in rng.choice(pool_t.values, size=min(3, len(pool_t)), replace=False) if len(pool_t) else []:
        g = trade(df, int(t0), "A")
        if g: base.append(dict(token=r.token, cost=cost, **g))

res, bas = pd.DataFrame(rows), pd.DataFrame(base)
res.to_parquet(os.path.join(SP, "cluster_results.parquet"))
def boot_ci(x, n=5000):
    x = x.dropna().values
    if len(x) < 5: return (np.nan, np.nan)
    m = [rng.choice(x, len(x)).mean() for _ in range(n)]
    return (np.percentile(m, 2.5), np.percentile(m, 97.5))
print(f"events with candles: {res[res['mode']=='A'].shape[0]} / {len(ev)} ; baseline draws: {len(bas)}")
print("median modelled round-trip cost:", round(res.cost.median(), 4), " liquidity median $", round(res.liq.median()))
for mode in ("A", "B"):
    x = res[res["mode"] == mode]
    print(f"\nENTRY {mode}")
    for k in H:
        g = x[k].dropna(); net = (x[k] - x.cost).dropna()
        lo, hi = boot_ci(net)
        print(f"  {k:>3}: n={len(g):4d} gross mean {g.mean():+.3f} median {g.median():+.3f} win {(g>0).mean():.2f} | "
              f"NET mean {net.mean():+.3f} median {net.median():+.3f} win {(net>0).mean():.2f} 95%CI [{lo:+.3f},{hi:+.3f}]")
print("\nBASELINE random entry (same pools)")
for k in H:
    g = bas[k].dropna(); net = (bas[k] - bas.cost).dropna()
    print(f"  {k:>3}: n={len(g):4d} gross mean {g.mean():+.3f} median {g.median():+.3f} | NET mean {net.mean():+.3f} median {net.median():+.3f}")
