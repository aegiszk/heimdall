"""Dhesi v3 one-shot untouched-history validator (DHESI_V3_VALIDATION_PROTOCOL_V1.md).

Modes
  selftest-dev   DEVELOPMENT data only. Proves the parameterized reference engine below
                 reproduces the frozen v3 development trades (49/49) on MNQ. No new data.
  primary        NQ canonical series, untouched window. REQUIRES owner authorization file.
  secondary      ES / RTY / YM replication. REQUIRES authorization AND a primary verdict != FAIL.
  selftest-engines-dev        DEVELOPMENT data only: runs BOTH engines, persists both ledgers + comparison.
  selftest-engines-synthetic  internally generated synthetic walk only (no file input): same as above.

Revision 2 (2026-09-24, pre-validation hardening; strategy logic unchanged):
  D3  primary persists FROZEN_ENGINE_TRADES / REFERENCE_ENGINE_TRADES (.csv + .parquet) and ENGINE_COMPARISON.json
      BEFORE any statistic is computed. If the engines disagree on any strategy-defining field the result is
      INVALID and no strategy statistic or verdict is computed (PROTOCOL_AMENDMENT_1.md, supersedes protocol §4.5).
  D4  primary/secondary refuse to start the engines when the consumed rows fail row integrity (non-finite
      OHLCV, negative volume, OHLC geometry, duplicate / non-monotonic / invalid stamps), via the same checks as
      dhesi_v3_harvest_integrity.py (hash-bound below). Nothing is imputed.
  AUTH the authorization file must also name the spec, protocol, amendment and integrity-tool hashes.

Never tunes anything. All numbers used below are frozen in DHESI_V3_CANONICAL_SPEC_V1.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

ET = "America/New_York"
OHLCV = ["open", "high", "low", "close", "volume"]

# ---------------------------------------------------------------- frozen hashes (spec §0)
FROZEN_CODE = {
    "core/alpha/inversion_model.py": "e32e88f1a309c8e259274fd181929c3aa19935e667bcf568ff31eb9fbbdd0037",
    "core/alpha/inversion_model_v3.py": "0ab7a5156e506c629110efe5253a6b93315072cd3f544490d80c2a746922bf85",
    "core/risk/prop_engine.py": "5750672eea42047ae294415a14c795c783aef4348cd4af7bfc9eead0cae7a265",
    "core/alpha/base.py": "2d8c40e53bfdd0ab5f26ca90165b1cf7a38475e0429edd5f304c83eef1d78737",
    "tools/prop_montecarlo.py": "c5aaee3311289e11f92d0abc42ab5738861f477a81e40d0fcaf7dfbdd7b88e23",
    "tools/validate_inversion_model.py": "5dffdb7c4a7f7166d8e28c0d8df13bcc2ab2314f7e5fd720a828e27f79c59165",
}
AUTH_FILE = ROOT / "DHESI_V3_RUN_AUTHORIZATION.txt"
SPEC_FILE = HERE / "DHESI_V3_CANONICAL_SPEC_V1.md"
PROTOCOL_FILE = HERE / "DHESI_V3_VALIDATION_PROTOCOL_V1.md"
AMENDMENT_FILE = HERE / "PROTOCOL_AMENDMENT_1.md"
INTEGRITY_TOOL = HERE / "dhesi_v3_harvest_integrity.py"

# ---------------------------------------------------------------- frozen protocol constants
UNTOUCHED_END_ET = pd.Timestamp("2024-06-29 00:00", tz=ET)   # rows at/after this are dropped before any computation
LAST_SESSION = pd.Timestamp("2024-06-28").date()
BURN_IN_SESSIONS = 20
MU_MIN = 30.0                    # $/trade, spec §5
N_MIN_PASS = 80
BOOT_B, BOOT_BLOCK, BOOT_SEED = 20_000, 5.0, 20260923
MIN_TRADES_YEAR = 5
YEAR_POS_SHARE = 2.0 / 3.0
MIN_QUALIFYING_YEARS = 6
MAX_SINGLE_TRADE_SHARE = 0.25
WORST_YEAR_FLOOR = -2000.0
STRESS_EXTRA_TICKS = 2           # one extra adverse tick on entry and on final exit
STRESS_EXTRA_COMM = 0.50         # $/contract round trip

# instrument economics (spec §12, protocol §3/§8). tick_value = tick * point_value
INSTR = {
    "MNQ": dict(tick=0.25, pv=2.0, comm=1.0, maxc=40),
    "MES": dict(tick=0.25, pv=5.0, comm=1.0, maxc=40),
    "M2K": dict(tick=0.10, pv=5.0, comm=1.0, maxc=40),
    "MYM": dict(tick=1.00, pv=0.5, comm=1.0, maxc=40),
}
SECONDARY = {"ES": "MES", "RTY": "M2K", "YM": "MYM"}
NQ_DISP_POINTS = 30.0
FRICTION_RATIO = 10.0            # floor: per-contract risk >= 10 x per-contract friction


def floor_points(spec: dict) -> float:
    """Spec §7.3. Friction per contract = 2 ticks slippage + round-trip commission."""
    friction = 2 * spec["tick"] * spec["pv"] + spec["comm"]
    return FRICTION_RATIO * friction / spec["pv"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_frozen_code() -> dict:
    got = {k: sha(ROOT / k) for k in FROZEN_CODE}
    bad = {k: v for k, v in got.items() if v != FROZEN_CODE[k]}
    if bad:
        raise SystemExit(f"FROZEN CODE CHANGED, refusing to run: {bad}")
    return got


def check_authorization() -> str:
    me = sha(Path(__file__))
    if not AUTH_FILE.exists():
        raise SystemExit(f"NOT AUTHORIZED: {AUTH_FILE.name} missing (owner must create it)")
    text = AUTH_FILE.read_text(encoding="utf-8")
    need = {"validator": me, "spec": sha(SPEC_FILE), "protocol": sha(PROTOCOL_FILE),
            "amendment": sha(AMENDMENT_FILE), "integrity_tool": sha(INTEGRITY_TOOL)}
    missing = [k for k, v in need.items() if v not in text]
    if "AUTHORIZED_BY_OWNER" not in text or missing:
        raise SystemExit(f"NOT AUTHORIZED: file must contain AUTHORIZED_BY_OWNER and the current SHA-256 of {missing}: "
                         + json.dumps(need))
    return me


def _integrity_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("dhesi_v3_harvest_integrity", INTEGRITY_TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ================================================================ reference engine (parameterized copy of ref_dhesi.py)
T0930, T1000, T1600 = time(9, 30), time(10, 0), time(16, 0)
LOOKBACK, EQ_TOL, TP1_R, BUFFER = 20, 0.0005, 1.5, 325.0


def _rth(raw):
    et = raw.index.tz_convert(ET)
    f = raw.copy(); f["et"] = et; f["date"] = et.date; f["t"] = et.time
    m = (et.weekday < 5) & (f["t"] >= T0930) & (f["t"] <= T1600)
    return f.loc[m].reset_index(drop=True)


def _resample(f, rule):
    g = f.set_index("et").resample(rule, label="right", closed="right")
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "session": g["date"].last()}).dropna()
    b["ts"] = b.index
    return b.reset_index(drop=True)


def _bins24(raw, hours):
    wall = raw.index.tz_convert(ET).tz_localize(None)
    sh = wall - pd.Timedelta(hours=18)
    start = sh.normalize() + pd.to_timedelta((sh.hour // hours) * hours, unit="h") + pd.Timedelta(hours=18)
    df = raw[["open", "high", "low", "close"]].copy(); df["bin"] = start
    g = df.groupby("bin", sort=True)
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last()})
    end = b.index + pd.Timedelta(hours=hours)
    b = b.reset_index(drop=True)
    b["ts"] = pd.DatetimeIndex(end).tz_localize(ET, ambiguous=True, nonexistent="shift_forward")
    b["session"] = [(e - pd.Timedelta(minutes=1) + pd.Timedelta(hours=6)).date() for e in end]
    return b


def _inversions(b, sord):
    H, L, O, C = (b[k].to_numpy(float) for k in ("high", "low", "open", "close"))
    TS, SS = list(b["ts"]), list(b["session"])
    active, allf, dead, out, uid = [], [], set(), [], 0
    for i in range(len(b)):
        cur = sord.get(SS[i])
        if cur is not None:
            active = [g for g in active if g[0] not in dead and g[2] in sord and 0 <= cur - sord[g[2]] <= LOOKBACK]
            hit = [g for g in active if (g[3] == 1 and C[i] < g[4]) or (g[3] == -1 and C[i] > g[5])]
            for g in hit:
                dead.add(g[0])
            for bias in (-1, 1):
                same = [g for g in hit if -g[3] == bias]
                if same:
                    best = same[0]
                    for g in same[1:]:
                        if g[1] > best[1]:
                            best = g
                    out.append(dict(ts=TS[i], session=SS[i], bias=bias, lo=best[4], hi=best[5], formed=best[1],
                                    close=C[i], disp=abs(C[i] - O[i]), c3lo=best[6], c3hi=best[7]))
        if i >= 2:
            if H[i - 2] < L[i]:
                g = (uid, TS[i], SS[i], 1, H[i - 2], L[i], L[i], H[i]); uid += 1; active.append(g); allf.append(g)
            if L[i - 2] > H[i]:
                g = (uid, TS[i], SS[i], -1, H[i], L[i - 2], L[i], H[i]); uid += 1; active.append(g); allf.append(g)
    return allf, out


def _fractals(ts, sess, H, L):
    out = []
    for i in range(1, len(H) - 1):
        if H[i] > H[i - 1] and H[i] >= H[i + 1]:
            out.append(("high", ts[i], ts[i + 1], sess[i], H[i]))
        if L[i] < L[i - 1] and L[i] <= L[i + 1]:
            out.append(("low", ts[i], ts[i + 1], sess[i], L[i]))
    return out


def _clusters(vals):
    vals = sorted(v for v in vals if np.isfinite(v) and v > 0)
    res, cur = [], []
    for v in vals:
        if not cur:
            cur = [v]; continue
        a = sum(cur) / len(cur)
        if abs(v - a) / a <= EQ_TOL:
            cur.append(v)
        else:
            if len(cur) >= 2:
                res.append(cur)
            cur = [v]
    if len(cur) >= 2:
        res.append(cur)
    return res


def _dedupe(pools, tick):
    seen, out = set(), []
    for lvl, kind in pools:
        if not np.isfinite(lvl):
            continue
        k = (kind, int(round(lvl / tick)))
        if k not in seen:
            seen.add(k); out.append((lvl, kind))
    return out


def reference_run(raw: pd.DataFrame, spec: dict, floor_pts: float, disp_min) -> pd.DataFrame:
    """v3 with all switches on. disp_min: float, or dict session->float (secondary scaling)."""
    TICK, PV, COMM, MAXC = spec["tick"], spec["pv"], spec["comm"], spec["maxc"]
    TICKV = TICK * PV
    raw = raw[OHLCV].astype(float).sort_index()
    f = _rth(raw)
    sessions = list(dict.fromkeys(f["date"]))
    sord = {s: i for i, s in enumerate(sessions)}
    alld = raw.copy(); alld["d"] = raw.index.tz_convert(ET).date
    dayhl = alld.groupby("d").agg(h=("high", "max"), l=("low", "min"))
    pdh, pdl = dayhl["h"].shift(1), dayhl["l"].shift(1)
    rth = f.groupby("date").agg(h=("high", "max"), l=("low", "min"))
    prh, prl = rth["h"].shift(1), rth["l"].shift(1)
    r20h = rth["h"].shift(1).rolling(LOOKBACK, min_periods=LOOKBACK).max()
    r20l = rth["l"].shift(1).rolling(LOOKBACK, min_periods=LOOKBACK).min()
    swk: dict = {}
    for kind, _, _, s, p in _fractals(list(f["et"]), list(f["date"]), f["high"].to_numpy(float), f["low"].to_numpy(float)):
        swk.setdefault((s, kind), []).append(p)
    tt = alld.index.tz_convert(ET); tm = tt.time
    ai = (tm >= time(20, 0)) & (tm <= time(23, 59)); li = (tm >= time(2, 0)) & (tm <= time(4, 59))
    asia = alld.loc[ai].assign(k=(tt[ai].tz_localize(None).normalize() + pd.Timedelta(days=1)).date).groupby("k").agg(h=("high", "max"), l=("low", "min"))
    london = alld.loc[li].assign(k=tt[li].tz_localize(None).normalize().date).groupby("k").agg(h=("high", "max"), l=("low", "min"))
    pools = {}
    for s in sessions:
        cur = sord[s]
        hi = [(float(a), b) for a, b in ((prh.get(s, np.nan), "prior_rth_high"), (pdh.get(s, np.nan), "prior_day_high"), (r20h.get(s, np.nan), "rolling20_high")) if np.isfinite(a)]
        lo = [(float(a), b) for a, b in ((prl.get(s, np.nan), "prior_rth_low"), (pdl.get(s, np.nan), "prior_day_low"), (r20l.get(s, np.nan), "rolling20_low")) if np.isfinite(a)]
        prev = [sessions[j] for j in range(max(0, cur - LOOKBACK), cur)]
        mh, ml = [], []
        for kind, lst, mj in (("high", hi, mh), ("low", lo, ml)):
            for c in _clusters([p for ps in prev for p in swk.get((ps, kind), [])]):
                lvl = max(c) if kind == "high" else min(c)
                lst.append((lvl, f"equal_{kind}"))
                if len(c) >= 3:
                    mj.append((lvl, f"stacked_equal_{kind}"))
        if np.isfinite(r20h.get(s, np.nan)):
            mh.append((float(r20h[s]), "rolling20_high"))
        if np.isfinite(r20l.get(s, np.nan)):
            ml.append((float(r20l[s]), "rolling20_low"))
        hi, lo = _dedupe(hi, TICK), _dedupe(lo, TICK)
        for tab, nm in ((asia, "asia"), (london, "london")):
            if s in tab.index:
                hi = _dedupe(hi + [(float(tab.loc[s, "h"]), f"{nm}_high")], TICK)
                lo = _dedupe(lo + [(float(tab.loc[s, "l"]), f"{nm}_low")], TICK)
        pools[s] = {"high": hi, "low": lo, "mhigh": _dedupe(mh, TICK), "mlow": _dedupe(ml, TICK)}

    f4, inv4 = _inversions(_bins24(raw, 4), sord)
    _, inv1 = _inversions(_bins24(raw, 1), sord)
    b15, b5 = _resample(f, "15min"), _resample(f, "5min")
    s5 = {s: i for i, s in enumerate(dict.fromkeys(b5["session"]))}
    _, ltf = _inversions(b5, s5)
    ltf.sort(key=lambda e: e["ts"])

    def group(evs):
        d = {}
        for e in evs:
            d.setdefault((e["session"], e["bias"]), []).append(e)
        for v in d.values():
            v.sort(key=lambda e: e["ts"])
        return d

    g4, g1, gl = group(inv4), group(inv1), group(ltf)
    f4_meta = [(g[1], g[2]) for g in f4]
    b15_by = {s: d.reset_index(drop=True) for s, d in b15.groupby("session", sort=True)}
    sw15_by: dict = {}
    for kind, ts, conf, s, p in _fractals(list(b15["ts"]), list(b15["session"]), b15["high"].to_numpy(float), b15["low"].to_numpy(float)):
        sw15_by.setdefault(s, []).append((kind, ts, conf, p))
    pos = {t: i for i, t in enumerate(f["et"])}
    O, Hh, Ll, Cc = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    TT, DD, TM = list(f["et"]), list(f["date"]), list(f["t"])

    def simulate(i0, side, entry, stop, tp1, runner, n):
        s = DD[i0]; j = i0 + 1
        rstop, hit, frac, gtp1, last = stop, False, 1.0, 0.0, None
        while j < len(TT) and DD[j] == s:
            last = j
            if side > 0:
                ex = (min(O[j], rstop - TICK), "gap_stop") if O[j] <= rstop else ((rstop - TICK, "stop") if Ll[j] <= rstop else None)
            else:
                ex = (max(O[j], rstop + TICK), "gap_stop") if O[j] >= rstop else ((rstop + TICK, "stop") if Hh[j] >= rstop else None)
            if ex:
                g = frac * n * side * (ex[0] - entry) * PV
                return j, ex[0], (gtp1 + g) if hit else g, ("runner_" + ex[1]) if hit else ex[1], hit
            if not hit and ((Hh[j] >= tp1) if side > 0 else (Ll[j] <= tp1)):
                hit, frac, rstop = True, 0.5, entry
                gtp1 = 0.5 * n * side * (tp1 - entry) * PV
                j += 1
                continue
            if hit and runner is not None and ((Hh[j] >= runner) if side > 0 else (Ll[j] <= runner)):
                return j, runner, gtp1 + frac * n * side * (runner - entry) * PV, "runner_target", hit
            if TM[j] >= T1600:
                break
            j += 1
        if last is None:
            px = Cc[i0] - side * TICK
            return i0, px, n * side * (px - entry) * PV, "session_flatten", False
        k = i0 + 1
        while k + 1 < len(TT) and DD[k + 1] == s:
            k += 1
        px = Cc[k] - side * TICK
        g = frac * n * side * (px - entry) * PV
        return k, px, (gtp1 + g) if hit else g, "runner_session_flatten" if hit else "session_flatten", hit

    def try_entry(s, bias, inv, rts, not_before):
        for e in gl.get((s, bias), []):
            if e["formed"] < rts or e["ts"] <= rts:
                continue
            if not_before is not None and e["ts"] <= not_before:
                continue
            if e["ts"].time() < T1000 or e["ts"].time() > T1600:
                continue
            if max(e["c3lo"], inv["lo"]) > min(e["c3hi"], inv["hi"]):
                continue
            if e["ts"] not in pos:
                continue
            want = "low" if bias > 0 else "high"
            cands = [(ts, p) for kind, ts, conf, p in sw15_by.get(s, []) if kind == want and conf <= e["ts"] and ts >= inv["ts"]]
            if not cands:
                continue
            tsb = max(c[0] for c in cands)
            p = [c[1] for c in cands if c[0] == tsb][0]
            stop = p - TICK if bias > 0 else p + TICK
            entry = e["close"] + bias * TICK
            if bias * (entry - stop) < floor_pts:
                continue
            rp = abs(entry - stop)
            n = min(int(np.floor(BUFFER / (TICKV * rp / TICK))), MAXC)
            if n <= 0:
                continue
            risk = n * rp * PV
            if risk <= 0 or risk > BUFFER + 1e-9:
                continue
            P = pools[s]
            if bias > 0:
                opp = sorted([x for x in P["high"] if x[0] > entry], key=lambda x: x[0])
                maj = sorted([x for x in P["mhigh"] if x[0] > entry], key=lambda x: x[0])
            else:
                opp = sorted([x for x in P["low"] if x[0] < entry], key=lambda x: -x[0])
                maj = sorted([x for x in P["mlow"] if x[0] < entry], key=lambda x: -x[0])
            if not opp:
                continue
            near = opp[0][0]
            tp1 = near if bias * (near - entry) >= TP1_R * rp else entry + bias * TP1_R * rp
            rc = [x for x in maj if bias * (x[0] - tp1) > 0]
            runner = rc[0][0] if rc else None
            j, px, gross, why, hit = simulate(pos[e["ts"]], bias, entry, stop, tp1, runner, n)
            return dict(entry_ts=e["ts"], exit_ts=TT[j], session=s, side=bias, entry_price=entry, exit_price=px,
                        stop_price=stop, tp1_price=tp1, runner_target_price=runner, contracts=n, risk_dollars=risk,
                        pnl=gross - n * COMM, gross_pnl=gross, tp1_hit=hit, reason=why)
        return None

    trades = []
    for s, day in f.groupby("date", sort=True):
        H, L, C, TS = day["high"].to_numpy(float), day["low"].to_numpy(float), day["close"].to_numpy(float), list(day["et"])
        ev, pend = [], []
        for i in range(len(day)):
            for lvl, kind in pools[s]["high"]:
                if H[i] > lvl:
                    pend.append((i + 3, lvl, kind, -1))
            for lvl, kind in pools[s]["low"]:
                if L[i] < lvl:
                    pend.append((i + 3, lvl, kind, 1))
            keep = []
            for exp, lvl, kind, b in pend:
                if i > exp:
                    continue
                if (C[i] < lvl) if b < 0 else (C[i] > lvl):
                    ev.append((TS[i], b, lvl, kind))
                else:
                    keep.append((exp, lvl, kind, b))
            pend = keep
        ev.sort(key=lambda x: x[0])
        dmin = disp_min.get(s, np.inf) if isinstance(disp_min, dict) else disp_min
        taken = losses = 0
        last_exit = None
        for ts, bias, lvl, kind in ev:
            if taken >= 3 or losses >= 2:
                break
            if last_exit is not None and ts < last_exit:
                continue
            cur = sord[s]
            has4 = any(fm < ts and fs in sord and 0 <= cur - sord[fs] <= LOOKBACK for fm, fs in f4_meta)
            cand = [e for e in (g4 if has4 else g1).get((s, bias), []) if e["ts"] > ts and e["ts"].time() <= T1600]
            if not cand:
                continue
            inv = min(cand, key=lambda e: e["ts"])
            if inv["disp"] < dmin:
                continue
            b15s = b15_by.get(s)
            if b15s is None:
                continue
            rts = None
            for _, r in b15s[(b15s["ts"] > inv["ts"]) & (b15s["ts"].dt.time <= T1600)].iterrows():
                if max(float(r["low"]), inv["lo"]) <= min(float(r["high"]), inv["hi"]):
                    rts = r["ts"]; break
            if rts is None:
                continue
            t = try_entry(s, bias, inv, rts, last_exit)
            if t is None:
                continue
            t["sweep_pool"] = kind
            trades.append(t)
            taken += 1
            losses += t["pnl"] < 0
            last_exit = t["exit_ts"]
    return pd.DataFrame(trades)


# ================================================================ D3: dual-ledger persistence + comparison
# Strategy-defining fields common to both engines (verified identical on 231/231 synthetic and 49/49 dev trades).
COMPARE_FIELDS = ["entry_ts", "exit_ts", "session", "side", "entry_price", "exit_price", "stop_price", "tp1_price",
                  "runner_target_price", "contracts", "risk_dollars", "gross_pnl", "pnl", "tp1_hit", "reason", "sweep_pool"]
TEXT_FIELDS = {"entry_ts", "exit_ts", "session", "tp1_hit", "reason", "sweep_pool"}
NUM_TOL = 1e-9   # numbers are tick-grid prices, integer contracts and cent PnL: agreement must be exact to float noise


def ledger(trades: pd.DataFrame, engine: str) -> pd.DataFrame:
    """Deterministic, reconcilable ledger. Both engines decide and enter on the close of the 5m LTF inversion bar
    (spec §6), so signal_ts == entry_ts. trade_id = session|side|entry_ts (unique: one open position at a time)."""
    cols = COMPARE_FIELDS
    t = trades.copy() if len(trades) else pd.DataFrame(columns=cols)
    for c in cols:
        if c not in t.columns:
            t[c] = np.nan
    t = t.sort_values(["entry_ts", "side"], kind="mergesort").reset_index(drop=True)
    t.insert(0, "trade_id", [f"{s}|{int(d)}|{e}" for s, d, e in zip(t["session"].astype(str), t["side"], t["entry_ts"].astype(str))])
    t.insert(1, "engine", engine)
    t.insert(2, "signal_ts", t["entry_ts"])
    t["position_size_contracts"] = t["contracts"]
    t["costs"] = t["gross_pnl"].astype(float) - t["pnl"].astype(float)
    return t


def compare_ledgers(fz: pd.DataFrame, rf: pd.DataFrame) -> dict:
    fi, ri = fz.set_index("trade_id"), rf.set_index("trade_id")
    miss_f = sorted(set(ri.index) - set(fi.index))
    miss_r = sorted(set(fi.index) - set(ri.index))
    both = [i for i in fi.index if i in ri.index]
    mism, maxdiff = [], {}
    for c in COMPARE_FIELDS:
        a, b = fi.loc[both, c], ri.loc[both, c]
        if c in TEXT_FIELDS:
            bad = [i for i in both if str(a[i]) != str(b[i])]
        else:
            av, bv = a.astype(float).to_numpy(), b.astype(float).to_numpy()
            both_nan = np.isnan(av) & np.isnan(bv)
            diff = np.where(both_nan, 0.0, np.abs(av - bv))
            diff = np.where(np.isnan(diff), np.inf, diff)
            maxdiff[c] = float(diff.max()) if len(diff) else 0.0
            bad = [both[k] for k in np.flatnonzero(diff > NUM_TOL)]
        mism.extend({"trade_id": i, "field": c, "frozen": str(fi.loc[i, c]), "reference": str(ri.loc[i, c])} for i in bad)
    ok = not miss_f and not miss_r and not mism and len(fz) == len(rf)
    return {"frozen_trades": int(len(fz)), "reference_trades": int(len(rf)), "matched_trades": int(len(both)),
            "missing_on_frozen": miss_f, "missing_on_reference": miss_r, "field_mismatches": mism,
            "field_mismatch_count": len(mism), "max_abs_numeric_diff": maxdiff, "numeric_tolerance": NUM_TOL,
            "compared_fields": COMPARE_FIELDS, "result": "PASS" if ok else "FAIL"}


def run_both_engines_and_persist(raw: pd.DataFrame, keep: set, outdir: Path) -> tuple[pd.DataFrame, dict]:
    """Runs frozen (normative) and reference engines on the SAME rows, writes both ledgers and the comparison to
    disk BEFORE anything else is computed, and returns (frozen ledger, comparison)."""
    from core.alpha.inversion_model_v3 import InversionModelV3
    outdir.mkdir(parents=True, exist_ok=True)
    model = InversionModelV3(contract="MNQ")
    frozen = model.trades_frame(model._run_backtest(raw).trades)
    frozen = frozen[frozen["session"].isin(keep)].reset_index(drop=True) if len(frozen) else frozen
    fz = ledger(frozen, "frozen")
    fz.to_csv(outdir / "FROZEN_ENGINE_TRADES.csv", index=False)
    fz.astype({c: str for c in ("entry_ts", "exit_ts", "signal_ts", "session")}).to_parquet(outdir / "FROZEN_ENGINE_TRADES.parquet")
    ref = reference_run(raw, INSTR["MNQ"], floor_points(INSTR["MNQ"]), NQ_DISP_POINTS)
    ref = ref[ref["session"].isin(keep)].reset_index(drop=True) if len(ref) else ref
    rf = ledger(ref, "reference")
    rf.to_csv(outdir / "REFERENCE_ENGINE_TRADES.csv", index=False)
    rf.astype({c: str for c in ("entry_ts", "exit_ts", "signal_ts", "session")}).to_parquet(outdir / "REFERENCE_ENGINE_TRADES.parquet")
    cmp_ = compare_ledgers(fz, rf)
    cmp_["files"] = {p.name: sha(p) for p in sorted(outdir.glob("*_ENGINE_TRADES.*"))}
    (outdir / "ENGINE_COMPARISON.json").write_text(json.dumps(cmp_, indent=1, default=str) + "\n", encoding="utf-8")
    return frozen, cmp_


def require_row_integrity(raw: pd.DataFrame) -> dict:
    """D4: refuse before any engine runs if a consumed row is not valid. Counts only; nothing imputed."""
    res = _integrity_module().row_integrity(raw)
    return res


# ================================================================ statistics / verdict
def stationary_bootstrap(trades: pd.DataFrame) -> tuple[float, float]:
    by = trades.groupby("session", sort=True)["pnl"].agg(["sum", "count"])
    s, c = by["sum"].to_numpy(float), by["count"].to_numpy(float)
    n = len(s)
    rng = np.random.default_rng(BOOT_SEED)
    p = 1.0 / BOOT_BLOCK
    means = np.empty(BOOT_B)
    for b in range(BOOT_B):
        idx = np.empty(n, dtype=int)
        idx[0] = rng.integers(n)
        new = rng.random(n) < p
        jumps = rng.integers(n, size=n)
        for i in range(1, n):
            idx[i] = jumps[i] if new[i] else (idx[i - 1] + 1) % n
        means[b] = s[idx].sum() / c[idx].sum()
    return float(np.percentile(means, 5)), float(np.percentile(means, 95))


def evaluate(trades: pd.DataFrame, spec: dict) -> dict:
    if trades.empty:
        return {"n": 0, "verdict": "INCONCLUSIVE", "reasons": ["zero trades"]}
    t = trades.copy()
    t["stress_pnl"] = t["pnl"] - t["contracts"] * (STRESS_EXTRA_TICKS * spec["tick"] * spec["pv"] + STRESS_EXTRA_COMM)
    n, mean, total = len(t), float(t.pnl.mean()), float(t.pnl.sum())
    lo, hi = stationary_bootstrap(t)
    slo, _ = stationary_bootstrap(t.assign(pnl=t["stress_pnl"]))
    t["year"] = pd.to_datetime(t["session"].astype(str)).dt.year
    yr = t.groupby("year")["pnl"].agg(["count", "sum", "mean"])
    q = yr[yr["count"] >= MIN_TRADES_YEAR]
    share_pos = float((q["sum"] > 0).mean()) if len(q) else 0.0
    top_share = float(t.pnl.max() / total) if total > 0 else float("inf")
    checks = {
        "P1_n_ge_80": n >= N_MIN_PASS,
        "P2_mean_ge_mu_min": mean >= MU_MIN,
        "P3_boot_lo_gt_0": lo > 0,
        "P4_years": len(q) >= MIN_QUALIFYING_YEARS and share_pos >= YEAR_POS_SHARE,
        "P5_top_trade_share_le_25pct": top_share <= MAX_SINGLE_TRADE_SHARE,
        "P6_worst_year_ge_-2000": float(yr["sum"].min()) >= WORST_YEAR_FLOOR,
        "P7_stress_mean_gt_0_and_lo_gt_0": float(t.stress_pnl.mean()) > 0 and slo > 0,
    }
    if hi < MU_MIN:
        verdict = "FAIL"
    elif all(checks.values()):
        verdict = "PASS"
    else:
        verdict = "INCONCLUSIVE"
    return {"n": n, "mean": mean, "total": total, "sd": float(t.pnl.std(ddof=1)) if n > 1 else None,
            "win_rate": float((t.pnl > 0).mean()), "boot_lo95": lo, "boot_hi95": hi, "stress_mean": float(t.stress_pnl.mean()),
            "stress_boot_lo95": slo, "years": yr.reset_index().to_dict("records"), "qualifying_years": int(len(q)),
            "qualifying_years_positive_share": share_pos, "top_trade_share": top_share, "checks": checks, "verdict": verdict}


def prop_report(trades: pd.DataFrame, sessions: list) -> dict:
    """REPORT-ONLY prop axis (protocol §6). Same Lucid MC settings as tools/validate_inversion_v3.py."""
    if trades.empty:
        return {"pass_rate": 0.0, "note": "zero trades"}
    from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many
    from tools.validate_inversion_model import observed_daily_counts
    counts = observed_daily_counts(np.asarray(sorted(sessions), dtype=object), trades)
    params = SimParams(n_sims=10_000, seed=20260922, daily_buffer=325.0, min_trades_per_day=0,
                       max_trades_per_day=3, commission_per_rt=0.0)
    mc = run_empirical_many(params, trades["pnl"].to_numpy(float), counts)
    return {"pass_rate": mc.pass_rate, "breakeven_pass_rate": 0.0396, "ev_per_eval": ev_per_eval(mc.pass_rate, 2400.0, 99.0),
            "fail_died_mll": mc.fail_died_mll, "fail_never_target": mc.fail_no_target, "fail_5day": mc.fail_target_min_days,
            "trades_per_year": float(len(trades) / max(1e-9, len(sessions) / 252.0))}


def truncate_untouched(raw: pd.DataFrame) -> pd.DataFrame:
    idx = pd.DatetimeIndex(raw.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    raw = raw.set_axis(idx)
    return raw.loc[raw.index < UNTOUCHED_END_ET.tz_convert("UTC")]


def sessions_after_burn_in(raw: pd.DataFrame) -> list:
    et = raw.index.tz_convert(ET)
    rth = (et.weekday < 5) & (et.time >= T0930) & (et.time <= T1600)
    s = sorted(set(et[rth].date))
    return [x for x in s[BURN_IN_SESSIONS:] if x <= LAST_SESSION]


def integrity(raw: pd.DataFrame, path: Path) -> dict:
    return {"path": str(path), "sha256": sha(path), "rows": int(len(raw)), "start": str(raw.index.min()), "end": str(raw.index.max()),
            "duplicates": int(raw.index.duplicated().sum()), "nan_cells": int(raw[OHLCV].isna().sum().sum())}


# ================================================================ modes
def selftest_dev() -> int:
    raw = pd.read_parquet(ROOT / "data" / "MNQ_1m.parquet")[OHLCV]
    ref = reference_run(raw, INSTR["MNQ"], floor_points(INSTR["MNQ"]), NQ_DISP_POINTS)
    off = pd.read_csv(ROOT / "data" / "strategy_research" / "dhesi_v3_development_trades.csv")
    ok = len(ref) == len(off) and (ref["entry_ts"].astype(str).values == off["entry_ts"].astype(str).values).all() \
        and np.allclose(ref["pnl"].to_numpy(float), off["pnl"].to_numpy(float))
    out = {"mode": "selftest-dev", "data": "DEVELOPMENT data/MNQ_1m.parquet", "floor_pts_MNQ": floor_points(INSTR["MNQ"]),
           "ref_trades": len(ref), "official_trades": len(off), "identical": bool(ok)}
    print(json.dumps(out, indent=1))
    (HERE / "selftest_dev_result.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0 if ok else 1


def primary(nq_path: Path) -> int:
    code = check_frozen_code()
    me = check_authorization()
    raw = truncate_untouched(pd.read_parquet(nq_path)[OHLCV])
    report = {"mode": "primary", "validator_sha256": me, "frozen_code": code, "integrity": integrity(raw, nq_path)}
    rows = require_row_integrity(raw)
    report["row_integrity"] = rows
    out_json = HERE / "dhesi_v3_untouched_primary.json"
    if not rows.get("gate1_rows_valid"):
        report["result"] = {"verdict": "INVALID", "reason": "D4 row integrity failed on consumed rows; engines not run"}
        out_json.write_text(json.dumps(report, indent=1, default=str) + "\n", encoding="utf-8")
        print(json.dumps(report["result"]))
        return 2
    keep = set(sessions_after_burn_in(raw))
    frozen, cmp_ = run_both_engines_and_persist(raw, keep, HERE / "primary_run")
    report["engine_comparison"] = {k: cmp_[k] for k in ("result", "frozen_trades", "reference_trades", "matched_trades",
                                                        "field_mismatch_count", "files")}
    if cmp_["result"] != "PASS":
        report["result"] = {"verdict": "INVALID", "reason": "frozen/reference engines disagree (PROTOCOL_AMENDMENT_1): "
                            "no strategy conclusion; see primary_run/ENGINE_COMPARISON.json"}
    else:
        report["result"] = evaluate(frozen, INSTR["MNQ"])
        report["prop_report_only"] = prop_report(frozen, sorted(keep))
    frozen.to_csv(HERE / "dhesi_v3_untouched_primary_trades.csv", index=False)
    out_json.write_text(json.dumps(report, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: report["result"][k] for k in ("n", "mean", "boot_lo95", "boot_hi95", "verdict") if k in report["result"]}, default=str))
    return 0


def secondary(market: str, path: Path, nq_path: Path) -> int:
    check_frozen_code()
    me = check_authorization()
    prim = json.loads((HERE / "dhesi_v3_untouched_primary.json").read_text(encoding="utf-8"))
    if prim["result"]["verdict"] == "FAIL":
        raise SystemExit("primary verdict FAIL: secondary replication is not run (protocol §7)")
    spec = INSTR[SECONDARY[market]]
    raw = truncate_untouched(pd.read_parquet(path)[OHLCV])
    nq = truncate_untouched(pd.read_parquet(nq_path)[OHLCV])
    rows = require_row_integrity(raw)
    if not rows.get("gate1_rows_valid"):
        (HERE / f"dhesi_v3_untouched_secondary_{market}.json").write_text(json.dumps(
            {"mode": "secondary", "market": market, "row_integrity": rows,
             "result": {"verdict": "INVALID", "reason": "D4 row integrity failed; engine not run"}}, indent=1, default=str) + "\n",
            encoding="utf-8")
        return 2

    def prev_rth_close(r):
        f = _rth(r)
        return f.groupby("date")["close"].last().shift(1)

    ratio = (prev_rth_close(raw) / prev_rth_close(nq)).dropna()
    disp = {s: NQ_DISP_POINTS * float(v) for s, v in ratio.items()}
    keep = set(sessions_after_burn_in(raw))
    tr = reference_run(raw, spec, floor_points(spec), disp)
    tr = tr[tr["session"].isin(keep)].reset_index(drop=True) if len(tr) else tr
    res = evaluate(tr, spec)
    report = {"mode": "secondary", "market": market, "execution": SECONDARY[market], "validator_sha256": me,
              "floor_points": floor_points(spec), "integrity": integrity(raw, path), "result": res}
    tr.to_csv(HERE / f"dhesi_v3_untouched_secondary_{market}_trades.csv", index=False)
    (HERE / f"dhesi_v3_untouched_secondary_{market}.json").write_text(json.dumps(report, indent=1, default=str) + "\n", encoding="utf-8")
    print(market, res.get("n"), res.get("mean"), res["verdict"])
    return 0


def synthetic_walk(seed: int = 7, start: str = "2022-01-03", end: str = "2024-01-01") -> pd.DataFrame:
    """Seeded synthetic random walk (Agent 2 dry-run generator, shortened). NOT market data."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, end, freq="1min", tz=ET, inclusive="left")
    wd, h = idx.weekday, idx.hour
    idx = idx[~((wd == 5) | ((wd == 4) & (h >= 17)) | ((wd == 6) & (h < 18)) | (h == 17))]
    n, sig, p0 = len(idx), 0.013 / np.sqrt(1380), 2300.0
    rth = (idx.time >= T0930) & (idx.time <= T1600)
    s = np.where(rth, sig * 1.6, sig * 0.6)
    path = p0 * np.exp(np.cumsum((rng.standard_normal((n, 4)) * (s[:, None] / 2)).reshape(-1))).reshape(n, 4)
    q = lambda x: np.round(x / 0.25) * 0.25  # noqa: E731
    o, c = q(np.r_[p0, path[:-1, 3]]), q(path[:, 3])
    hi, lo = q(np.maximum(path.max(1), np.maximum(o, c))), q(np.minimum(path.min(1), np.minimum(o, c)))
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": c,
                         "volume": rng.integers(50, 2000, n).astype(float)}, index=idx.tz_convert("UTC"))


def selftest_engines(mode: str) -> int:
    """D3 self-test WITHOUT reserved data: dev MNQ (consumed) or an internal synthetic walk. Never authorization."""
    if mode == "dev":
        raw = pd.read_parquet(ROOT / "data" / "MNQ_1m.parquet")[OHLCV]
        idx = pd.DatetimeIndex(raw.index)
        raw = raw.set_axis(idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC"))
        if raw.index.min() < pd.Timestamp("2024-07-01", tz="UTC"):
            raise SystemExit("firewall: dev file contains pre-2024-07-01 rows")
    else:
        raw = synthetic_walk()
    rows = require_row_integrity(raw)
    if not rows.get("gate1_rows_valid"):
        raise SystemExit(f"row integrity failed: {rows}")
    keep = set(sessions_after_burn_in(raw)) if mode == "synthetic" else set(pd.DatetimeIndex(raw.index).tz_convert(ET).date)
    _, cmp_ = run_both_engines_and_persist(raw, keep, HERE / f"selftest_engines_{mode}")
    print(json.dumps({k: cmp_[k] for k in ("result", "frozen_trades", "reference_trades", "matched_trades", "field_mismatch_count", "max_abs_numeric_diff")}, indent=1))
    return 0 if cmp_["result"] == "PASS" else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["selftest-dev", "primary", "secondary", "selftest-engines-dev", "selftest-engines-synthetic"])
    ap.add_argument("--nq", type=Path)
    ap.add_argument("--market", choices=sorted(SECONDARY))
    ap.add_argument("--data", type=Path)
    a = ap.parse_args()
    if a.mode == "selftest-dev":
        raise SystemExit(selftest_dev())
    if a.mode.startswith("selftest-engines-"):
        raise SystemExit(selftest_engines(a.mode.split("-")[-1]))
    if a.mode == "primary":
        raise SystemExit(primary(a.nq))
    raise SystemExit(secondary(a.market, a.data, a.nq))
