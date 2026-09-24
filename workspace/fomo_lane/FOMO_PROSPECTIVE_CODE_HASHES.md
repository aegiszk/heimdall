# FOMO prospective experiment — code hashes and implementation notes

**Scope.** This addendum records hashes and implementation limits only. It does **not** change the frozen rule in `FOMO_PROSPECTIVE_PREREGISTRATION.md` (SHA-256 `902263424c170fb7920c0a0880f056a8c7cc1b80e9a8dd5f2708a883c72fbc39`, frozen 2026-09-23 04:38:50 UTC).

| File | SHA-256 | Frozen |
|---|---|---|
| `fomo_recorder.py` | `867b5688ab3478258dd36f36144e94a1959a57cf7b251ddc8863886f411a8ab1` | before recording started, 2026-09-23 |
| `evaluate_prospective.py` | `9d0ae4db7793637dbef92827fe2ca84f8429276ed048e9e13034ad31f3f4c2c8` | before any exit could exist (earliest exit is 30 min after the first eligible event) |

## Implementation notes (reviewer attention)
1. **S1 window.** Implemented as blocks `[b_src − 3060, b_src)`, i.e. 300 s at 10.2 blocks/s (measured rate). Only blocks strictly before the source block count, so there is no information from after the decision.
2. **S3 state.** Uses the pool state emitted by the source's own swap: an exact point-in-time state at the source block.
3. **Detection path.** The recorder detects buys through public-RPC log polling, which lags the feed by seconds.
   - The **follower timing model** uses the feed arrival of the source block plus measured processing time plus 5 ms, as specified. That represents a production feed decoder, which this recorder is not.
   - S2 (`eth_call`) and the DexScreener price are taken at RPC detection time, a few seconds after the production decision point.
   - That lag is recorded per event (`t_detect_rpc` vs `t_arr_src_ns`). It is a small lookahead in S2 and the price; reviewer should confirm it is immaterial.
4. **Warm-up timestamps.** The 72 h universe warm-up converts block numbers to time at 10 blocks/s (approximate). Buys during the warm-up call itself are not recorded; recording starts when the poll loop starts.
5. **Tick crossings.** The fill model ignores tick crossings for v3/v4, as pre-registered.
   - The v2 fee is assumed to be 0.3%. The v3 fee comes from `fee()`.
   - Quote/USD drift over the 30 minutes is ignored; exact for USDG-quoted pools.
6. **Exit sellability.** Checked by a transfer simulation from the source wallet only while that wallet still holds the token. If it doesn't, the check is `None`, which is **not** scored as a failure: the pre-registration kills a trade only on a revert or a missing state. Reviewer should decide whether this is adequate.
7. **Outcomes.** `evaluate_prospective.py --final` refuses to run until the frozen stopping rule is met. `--integrity` and `--selftest` print no returns.

## Addendum A — 2026-09-23, before any event reached its exit (earliest exit = first event + 30 min)
- Run 1 aborted: 72 h warm-up blocked the poll loop for > 17 min; **0 events had been recorded**
  (archived `data_aborted_run1/`, feed clock only). Warm-up moved to a background thread with 8 parallel `eth_getCode`
  checks; warm-up buys written to `data/warmup/`; each event carries `warmup_complete`. Universe membership for events
  recorded before warm-up finished can be recomputed offline from warm-up buys with timestamps < T (no lookahead).
  New `fomo_recorder.py` SHA-256 `0cc05b6c8c092f84e82b23ca40cd1e465d4759773e24ba9bf8825d600701369c`. Recording (run 2)
  started 2026-09-23 ~05:38 UTC (epoch 1790139482).
- Measured recorder processing ≈ 2.5 s (sequential receipt/`eth_call`/DexScreener calls), so the PRIMARY variant
  (unchanged, as pre-registered) is slower than a production feed-decoding bot — conservative. Added SECONDARY,
  non-gating absolute-delay variants `abs{100,250,500,1000,2000,5000}ms` from source-block arrival so sub-second
  latencies are measured. Primary statistic, gate, thresholds and stopping rule unchanged.
  New `evaluate_prospective.py` SHA-256 `fec0a382346206b33e7ae6281f047afc0532f4077942489b3a809f1641813d52`.

## Addendum B — 2026-09-23, before any event reached its exit
- Run 2 detection lag grew from 15 s to 60 s: the poller handled events sequentially at ~2.5 s each. Because S2 and the
  price are taken at detection, a growing lag is a point-in-time violation.
- **Fix:** 12-worker thread pool, locked JSONL writes, 100-block poll step, and a per-event `detect_lag_s` field.
  Recorder SHA-256 `db2f0f368ee32c6564958a148d755fd3a08bc07ab242c80477e5de7f3bef7793` (run 3, same `data/` directory,
  appended).
- **Integrity rule, added before any outcome:** events decided more than 10 s after source-block arrival are LATE and are
  excluded from every outcome analysis. Their count is reported. All run-2 events with growing lag fall under this rule.
- Evaluator SHA-256 `0ce2041ea9125df1c625b580fc7a74a363d9b16325527681273840f15546e65b`.
- Primary statistic, gate, thresholds and stopping rule are unchanged.
