"""Frozen evaluator for FOMO_PROSPECTIVE_PREREGISTRATION.md (SHA-256 902263424c17...).
  python evaluate_prospective.py --integrity   -> counts/integrity only (allowed any time; NO returns)
  python evaluate_prospective.py --final       -> outcome evaluation; REFUSES unless the frozen stopping rule is met
                                                  (>=3500 eligible trades AND >=14 days) or >=45 days elapsed.
"""
import json, os, sys, glob, bisect, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data_amend1")   # Amendment 1 sample
PREREG_SHA = "902263424c170fb7920c0a0880f056a8c7cc1b80e9a8dd5f2708a883c72fbc39"
SIZE, GAS, EXIT_S, MUE, N_TARGET, MIN_DAYS, MAX_DAYS = 500.0, 0.66, 1800, 0.05, 3500, 14, 45
EXTRA_MS = [0, 100, 250, 500, 1000, 2000, 5000]
Q96 = 2 ** 96
T_SWAP4 = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
T_SWAP3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
T_SYNC2 = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"

def load(kind):
    out = []
    for f in sorted(glob.glob(os.path.join(D, kind, "*.jsonl"))):
        with open(f) as fh:
            for line in fh:
                try: out.append(json.loads(line))
                except json.JSONDecodeError: pass
    return out

def integrity():
    ev = [e for e in load("events") if "id" in e]; err = [e for e in load("events") if "error" in e]
    blocks = load("blocks"); rtt = load("rtt"); ex = load("exits")
    bnums = sorted(x["b"] for x in blocks)
    span = (bnums[-1] - bnums[0] + 1) if bnums else 0
    starts = [r for r in rtt if "start_head" in r]
    t0 = starts[0]["t"] if starts else None
    tl = max((e.get("t_decision", 0) for e in ev), default=None)
    rep = {
        "prereg_sha256": PREREG_SHA,
        "recording_start_utc": t0, "last_event_utc": tl,
        "days_elapsed": ((tl - t0) / 86400) if (t0 and tl) else 0,
        "fomo_buy_events": len(ev), "event_errors": len(err),
        "in_universe": sum(bool(e.get("universe")) for e in ev),
        "unroutable": sum(e.get("route") == "UNROUTABLE" for e in ev),
        "no_price": sum(e.get("src_usd") is None for e in ev),
        "s1_pass": sum((e.get("s1_sells") or 0) >= 5 for e in ev),
        "s2_pass": sum(bool(e.get("s2_transfer_ok")) for e in ev),
        "s3_pass": sum(e.get("s3_impact") is not None and e["s3_impact"] <= 0.05 for e in ev),
        "eligible": sum(bool(e.get("eligible")) for e in ev),
        # Amendment 1 sample clock: only events decided after the amended recorder reported warmup_complete=true count
        "eligible_counted": sum(bool(e.get("eligible")) and bool(e.get("warmup_complete")) for e in ev),
        "events_pre_warmup": sum(not e.get("warmup_complete") for e in ev),
        "eligible_missing_src_block_time": sum(bool(e.get("eligible")) and not e.get("t_arr_src_ns") for e in ev),
        "exit_checks_done": len(ex), "exit_transfer_failed": sum(x.get("exit_transfer_ok") is False for x in ex),
        "feed_blocks_recorded": len(bnums), "feed_block_span": span,
        "feed_missing_frac": (1 - len(set(bnums)) / span) if span else None,
        "feed_errors": sum("feed_error" in r for r in rtt), "loop_errors": sum("loop_error" in r for r in rtt),
        "warmup": next((r for r in rtt if "warmup_fomo_buys" in r), None),
        "seq_rtt_ms_medians": [r.get("seq_rtt_ms_median") for r in rtt if "seq_rtt_ms_median" in r][-5:],
        "unique_tokens_eligible": len({e["token"] for e in ev if e.get("eligible")}),
        "unique_wallets_eligible": len({e["wallet"] for e in ev if e.get("eligible")}),
    }
    return rep

# ---------------- outcome machinery (used only by --final) ----------------
def buy_out(st, x, tok_c1, fee):
    x = x * (1 - fee)
    if st["kind"] == "v2":
        rin, rout = (st["r0"], st["r1"]) if tok_c1 else (st["r1"], st["r0"])
        return rout * x / (rin + x)
    L, sp = st["L"], st["sp"]
    if L <= 0: return 0.0
    if tok_c1: sp2 = 1 / (1 / sp + x / L); return L * (sp - sp2)
    sp2 = sp + x / L; return L * (1 / sp - 1 / sp2)

def sell_out(st, t, tok_c1, fee):
    t = t * (1 - fee)
    if st["kind"] == "v2":
        rin, rout = (st["r1"], st["r0"]) if tok_c1 else (st["r0"], st["r1"])
        return rout * t / (rin + t)
    L, sp = st["L"], st["sp"]
    if L <= 0: return 0.0
    if tok_c1: sp2 = sp + t / L; return L * (1 / sp - 1 / sp2)
    sp2 = 1 / (1 / sp + t / L); return L * (sp - sp2)

def build_states():
    """pool key -> (sorted keys [(b,i)], states, txs)"""
    pools = collections.defaultdict(list)
    for l in load("logs"):
        t0 = l["t"][0]; d = l["d"][2:]
        if t0 == T_SWAP4:
            key = l["t"][1].lower(); w = [d[64 * k:64 * (k + 1)] for k in range(6)]
            st = {"kind": "v4", "sp": int(w[2], 16) / Q96, "L": int(w[3], 16), "fee": int(w[5], 16) / 1e6}
        elif t0 == T_SWAP3:
            key = l["a"]; st = {"kind": "v3", "sp": int(d[128:192], 16) / Q96, "L": int(d[192:256], 16), "fee": None}
        elif t0 == T_SYNC2:
            key = l["a"]; st = {"kind": "v2", "r0": int(d[:64], 16), "r1": int(d[64:128], 16), "fee": 0.003}
        else:
            continue
        pools[key].append(((l["b"], l["i"]), st, l["tx"]))
    out = {}
    for k, v in pools.items():
        v.sort(key=lambda z: z[0]); out[k] = ([z[0] for z in v], [z[1] for z in v], [z[2] for z in v])
    return out

def state_end_of_block(P, X):
    keys = P[0]; j = bisect.bisect_right(keys, (X, 1 << 60)) - 1
    return P[1][j] if j >= 0 else None

def tok_price_q(st, tok_c1):
    if st["kind"] == "v2":
        return (st["r0"] / st["r1"]) if tok_c1 else (st["r1"] / st["r0"])   # quote raw per token raw
    p = st["sp"] ** 2
    return (1 / p) if tok_c1 else p

def cluster_boot(vals, clusters, B=10000, seed=20260923):
    rng = np.random.default_rng(seed); vals = np.asarray(vals); cl = np.asarray(clusters)
    u, inv = np.unique(cl, return_inverse=True)
    sums = np.bincount(inv, weights=vals); cnt = np.bincount(inv)
    m = np.empty(B)
    for i in range(B):
        idx = rng.integers(0, len(u), len(u)); m[i] = sums[idx].sum() / cnt[idx].sum()
    return float(np.percentile(m, 10)), float(np.percentile(m, 90))

def compute(events, rtt, dec_fn, fee3_fn, exits_by_id, selftest=False):
    blocks = load("blocks"); B = sorted((x["b"], x["t_ns"]) for x in blocks)
    bnum = [b for b, _ in B]; tarr = {b: t for b, t in B}
    T_sorted = sorted(tarr.items(), key=lambda z: z[1]); T_times = [t for _, t in T_sorted]; T_blocks = [b for b, _ in T_sorted]
    seq = [r["seq_rtt_ms_median"] for r in rtt if "seq_rtt_ms_median" in r]
    ow_ns = (float(np.median(seq)) / 2 if seq else 135.0) * 1e6
    P_all = build_states(); rows = []; coverage = collections.Counter()
    def first_block_at(t_ns):
        j = bisect.bisect_left(T_times, t_ns)
        return T_blocks[j] if j < len(T_blocks) else None
    for e in events:
        P = P_all.get(e.get("pool"))
        if P is None: coverage["no_pool_logs"] += 1; continue
        src_idx = [k for k, tx in enumerate(P[2]) if tx == e["tx"]]
        if not src_idx: coverage["source_swap_not_logged"] += 1; continue
        st_src = P[1][src_idx[-1]]; tok_c1 = e["token_is_c1"]
        dec = dec_fn(e["token"]); px = e.get("price_usd_detect")
        if dec is None or not px: coverage["no_price_or_decimals"] += 1; continue
        usd_per_q = (px / 10 ** dec) / tok_price_q(st_src, tok_c1)
        t_src = e.get("t_arr_src_ns") or tarr.get(e["block"])
        if not t_src: coverage["no_src_block_time"] += 1; continue
        tax = e.get("output_tax") or 0.0
        variants = {f"+{x}ms": t_src + (e.get("processing_ms", 0) + 5 + x) * 1e6 for x in EXTRA_MS}
        # secondary, non-gating (addendum 2026-09-23, before any exit existed): absolute delays from source-block arrival
        variants.update({f"abs{x}ms": t_src + x * 1e6 for x in (100, 250, 500, 1000, 2000, 5000)})
        for vname, t_sub in list(variants.items()) + [("next_block", None)]:
            if t_sub is None: b_tgt = e["block"] + 1
            else:
                b_tgt = first_block_at(t_sub + 2 * ow_ns)
                if b_tgt is None: coverage["target_beyond_recording"] += 1; continue
                b_tgt = max(b_tgt, e["block"] + 1)
            t_tgt = tarr.get(b_tgt)
            if t_tgt is None: coverage["target_block_time_missing"] += 1; continue
            b_exit = first_block_at(t_tgt + EXIT_S * 1e9)
            if b_exit is None: coverage["exit_beyond_recording"] += 1; continue
            for side, off in (("pess", 0), ("opt", 1)):
                st_in = state_end_of_block(P, b_tgt - off); st_out = state_end_of_block(P, b_exit - off)
                if st_in is None or st_out is None: coverage["state_missing"] += 1; continue
                fee = st_in.get("fee") if st_in.get("fee") is not None else fee3_fn(e["pool"])
                xq = SIZE / usd_per_q
                toks = buy_out(st_in, xq, tok_c1, fee) * (1 - tax)
                xq_s = xq * 0.99; toks_s = buy_out(st_in, xq_s, tok_c1, fee) * (1 - tax)
                exr = exits_by_id.get(e["id"], {})
                dead = exr.get("exit_transfer_ok") is False
                proceeds = 0.0 if dead else sell_out(st_out, toks, tok_c1, fee) * (1 - tax) * usd_per_q
                proceeds_s = 0.0 if dead else sell_out(st_out, toks_s, tok_c1, fee) * (1 - tax) * usd_per_q * 0.99
                rows.append({"id": e["id"], "token": e["token"], "wallet": e["wallet"], "variant": vname, "state": side,
                             "day": int(t_src // 86_400_000_000_000), "eligible": bool(e.get("eligible")),
                             "ret": (proceeds - SIZE - 2 * GAS) / SIZE, "ret_infee": (proceeds_s - SIZE - 2 * GAS) / SIZE,
                             "b_src": e["block"], "b_tgt": b_tgt, "b_exit": b_exit})
                coverage["resolved"] += 1
    return rows, coverage

def final(selftest=False):
    rep = integrity()
    ok = (rep["eligible_counted"] >= N_TARGET and rep["days_elapsed"] >= MIN_DAYS) or rep["days_elapsed"] >= MAX_DAYS
    if not ok and not selftest:
        print(json.dumps({"REFUSED": "frozen stopping rule not met", **{k: rep[k] for k in ("eligible_counted", "days_elapsed")}}, indent=1))
        sys.exit(2)
    import requests
    RPC = "https://rpc.mainnet.chain.robinhood.com"; dc, fc = {}, {}
    def call(to, data):
        return requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, "latest"]}, timeout=20).json()["result"]
    def dec_fn(t):
        if t not in dc:
            try: dc[t] = int(call(t, "0x313ce567"), 16)
            except Exception: dc[t] = None
        return dc[t]
    def fee3_fn(p):
        if p not in fc:
            try: fc[p] = int(call(p, "0xddca3f43"), 16) / 1e6
            except Exception: fc[p] = 0.003
        return fc[p]
    # Addendum B (pre-outcome integrity rule): decisions taken > 10 s after source-block arrival are LATE (point-in-time
    # violation for S2/price) and excluded from all outcome analyses; their count is reported.
    def late(e):
        return (not e.get("t_arr_src_ns")) or (e["t_detect_rpc"] - e["t_arr_src_ns"] / 1e9 > 10.0)
    allev = [e for e in load("events") if "id" in e]
    n_late = sum(late(e) for e in allev)
    evs = [e for e in allev if not late(e) and e.get("route") not in (None, "UNROUTABLE") and e.get("universe")
           and e.get("warmup_complete")]                          # Amendment 1 sample clock
    exits = {x["id"]: x for x in load("exits")}
    rows, cov = compute(evs, load("rtt"), dec_fn, fee3_fn, exits, selftest)
    if selftest:   # NO RETURNS PRINTED
        print(json.dumps({"selftest_coverage": dict(cov), "rows": len(rows),
                          "eligible_rows_primary": sum(r["eligible"] and r["variant"] == "+0ms" and r["state"] == "pess" for r in rows)}, indent=1))
        return
    import pandas as pd
    df = pd.DataFrame(rows); prim = df[df.eligible & (df.variant == "+0ms") & (df.state == "pess")]
    v = prim.ret.values; lo, hi = cluster_boot(v, prim.token.values)
    cut = np.quantile(v, 0.99); ex_top = v[v < cut].mean()
    verdict = "PASS" if (lo > 0 and ex_top > 0) else ("FAIL" if hi < MUE else "INCONCLUSIVE")
    if verdict == "INCONCLUSIVE" and lo > 0 and ex_top <= 0: verdict = "INCONCLUSIVE-TAIL"
    if len(prim) < N_TARGET: verdict += "/UNDERPOWERED"
    out = {"prereg": PREREG_SHA, "late_excluded": n_late, "coverage": dict(cov), "n": len(prim), "tokens": prim.token.nunique(),
           "wallets": prim.wallet.nunique(), "days": prim.day.nunique(), "mean": float(v.mean()), "median": float(np.median(v)),
           "lb90": lo, "ub90": hi, "mean_ex_top1pct": float(ex_top), "verdict_discovery": verdict,
           "secondary": df[df.eligible].groupby(["variant", "state"]).ret.agg(["count", "mean", "median"]).reset_index().to_dict("records"),
           "infee_sensitivity_mean": float(prim.ret_infee.mean()),
           "unfiltered_mean": float(df[(df.variant == "+0ms") & (df.state == "pess")].ret.mean())}
    print(json.dumps(out, indent=1, default=str))

if __name__ == "__main__":
    if "--final" in sys.argv: final()
    elif "--selftest" in sys.argv: final(selftest=True)
    else: print(json.dumps(integrity(), indent=1, default=str))
