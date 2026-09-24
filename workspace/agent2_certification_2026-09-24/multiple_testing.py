"""Agent 2 independent multiple-testing recomputation (own code; reads only committed trade logs / matrix).
- Holm / BH on one-sided NW p over the 58 VALID trials (and with the 4 invalid first runs, as Agent 1's family).
- White Reality Check (stationary bootstrap) on daily R over the FULL session calendar (Agent 1 used the union
  of trade days only) for the CME and FX/XAU groups.
- DSR (Bailey & Lopez de Prado) per-trade, with the program count K=62 and the GLOBAL ledger count.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EXT = REPO / "workspace" / "external_strategies"
ET = "America/New_York"


def nw_t(x, lags=None):
    x = np.asarray(x, float); n = len(x)
    if n < 3: return np.nan
    lags = lags if lags is not None else int(np.floor(4 * (n / 100) ** (2 / 9)))
    e = x - x.mean()
    s = e @ e / n
    for L in range(1, lags + 1):
        s += 2 * (1 - L / (lags + 1)) * (e[L:] @ e[:-L]) / n
    return x.mean() / np.sqrt(s / n)


def holm(p):
    m = len(p); o = np.argsort(p); a = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, min(1, (m - r) * p[i])); a[i] = run
    return a


def bh(p):
    m = len(p); o = np.argsort(p); q = np.empty(m); prev = 1
    for r in range(m - 1, -1, -1):
        i = o[r]; prev = min(prev, p[i] * m / (r + 1)); q[i] = prev
    return q


def dsr(R, sr_var, K):
    R = np.asarray(R, float); n = len(R)
    sr = R.mean() / R.std(ddof=1)
    g3, g4 = st.skew(R), st.kurtosis(R, fisher=False)
    emc = 0.5772156649
    sr0 = np.sqrt(sr_var) * ((1 - emc) * st.norm.ppf(1 - 1 / K) + emc * st.norm.ppf(1 - 1 / (K * np.e)))
    z = (sr - sr0) * np.sqrt(n - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return float(st.norm.cdf(z))


def white_rc(X, B=2000, block=5.0, seed=11):
    T, K = X.shape; mu = X.mean(0); stat = np.sqrt(T) * mu.max()
    rng = np.random.default_rng(seed); p = 1 / block; c = 0
    for _ in range(B):
        idx = np.empty(T, int); idx[0] = rng.integers(T)
        new = rng.random(T) < p; jump = rng.integers(T, size=T)
        for t in range(1, T):
            idx[t] = jump[t] if new[t] else (idx[t - 1] + 1) % T
        if np.sqrt(T) * (X[idx].mean(0) - mu).max() >= stat: c += 1
    return c / B


def sess_day(ts):
    e = pd.to_datetime(ts, utc=True).dt.tz_convert(ET).dt.tz_localize(None) + pd.Timedelta(hours=6)
    return e.dt.normalize()


if __name__ == "__main__":
    m = pd.read_csv(REPO / "EXTERNAL_8_STRATEGIES_TEST_MATRIX.csv")
    invalid = m.index[:5].tolist()  # rows 0,1,2,4 are first-run A1/A2/A3/YM (row 3 = A4 valid)
    inv_mask = m.cfg.isin(["A1_k1_spike_nearest", "A2_k2_spike_nearest", "A3_k1_spike_split"])
    rows = []
    for _, r in m.iterrows():
        f = EXT / r.family / "results" / f"trades_{r.cfg}_{r.inst}.csv"
        if not f.exists():
            continue
        d = pd.read_csv(f)
        rows.append(dict(key=f"{r.cfg}|{r.inst}", family=r.family, inst=r.inst, invalid=bool(inv_mask[_]), n=len(d),
                         R=d.R.to_numpy(float), day=sess_day(d.t_entry)))
    valid = [x for x in rows if not x["invalid"]]
    res = {"n_trial_rows_with_logs": len(rows), "n_valid": len(valid), "n_invalid_first_runs": len(rows) - len(valid)}
    fam = [x for x in valid if x["n"] >= 3]
    p = np.array([1 - st.norm.cdf(nw_t(x["R"])) for x in fam])
    res["holm_min_adj_p_valid"] = float(holm(p).min()); res["bh_min_q_valid"] = float(bh(p).min())
    res["raw_min_p"] = float(p.min()); res["raw_min_p_trial"] = fam[int(p.argmin())]["key"]
    res["family_size_used_valid_n_ge_3"] = len(fam)
    # DSR
    srs = np.array([x["R"].mean() / x["R"].std(ddof=1) for x in valid if x["n"] >= 30])
    srv = float(np.var(srs, ddof=1))
    ledger = json.load(open(REPO / "data" / "trials_ledger.json"))["entries"]
    K_global = int(sum(int(e.get("n_configs") or 1) for e in ledger))
    best = max((x for x in valid if x["n"] >= 30), key=lambda x: x["R"].mean())
    res["dsr_best_n30"] = {"trial": best["key"], "sr_var": round(srv, 4), "K_program_62": round(dsr(best["R"], srv, 62), 4),
                           "K_global_ledger_configs": K_global, "K_global": round(dsr(best["R"], srv, K_global), 4)}
    # White RC on the FULL session calendar per group (trials n>=30)
    for grp, pred in (("CME", lambda x: x["inst"] in ("MNQ", "ES")), ("FX_XAU", lambda x: x["inst"] not in ("MNQ", "ES", "YM_S"))):
        cols = {x["key"]: pd.Series(x["R"]).groupby(x["day"].values).sum() for x in valid if pred(x) and x["n"] >= 30}
        M = pd.DataFrame(cols)
        cal = pd.bdate_range(M.index.min(), M.index.max())
        full = M.reindex(cal).fillna(0.0)
        union = M.fillna(0.0)
        res[f"white_rc_{grp}"] = {"K": M.shape[1], "T_union_trade_days": len(union), "T_full_calendar": len(full),
                                  "best": str(M.mean().idxmax()),
                                  "p_union": white_rc(union.to_numpy()), "p_full_calendar": white_rc(full.to_numpy())}
    print(json.dumps(res, indent=1, default=str))
    (HERE / "multiple_testing_result.json").write_text(json.dumps(res, indent=1, default=str))
