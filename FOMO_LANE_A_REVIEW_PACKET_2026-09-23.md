# FOMO Lane A — review packet for Agent 2 (NOT SELF-CERTIFIED)

Maker: primary experimentalist (this session). Checker: Agent 2. Nothing here authorizes capital, signing or orders.

## Artifacts
| Artifact | Path | SHA-256 |
|---|---|---|
| Frozen pre-registration | `FOMO_PROSPECTIVE_PREREGISTRATION.md` | `902263424c170fb7920c0a0880f056a8c7cc1b80e9a8dd5f2708a883c72fbc39` (frozen 2026-09-23 04:38:50 UTC) |
| Code hashes + Addenda A/B (pre-outcome changes) | `workspace/fomo_lane/FOMO_PROSPECTIVE_CODE_HASHES.md` | — |
| Recorder (run 3) | `workspace/fomo_lane/fomo_recorder.py` | `db2f0f368ee32c6564958a148d755fd3a08bc07ab242c80477e5de7f3bef7793` |
| Evaluator | `workspace/fomo_lane/evaluate_prospective.py` | `0ce2041ea9125df1c625b580fc7a74a363d9b16325527681273840f15546e65b` |
| Prospective data (append-only JSONL) | `workspace/fomo_lane/data/{blocks,rtt,logs,events,exits,warmup}/` | — |
| Aborted run 1 (feed clock only, 0 events) | `workspace/fomo_lane/data_aborted_run1/` | — |
| Dev-trial ledger (FOMO, 153 configs / 6 families) | `workspace/fomo_lane/fomo_trials_dev.json`, merged into `data/trials_ledger.json` | — |
| Validator split (separate maker) | `core/validation/gates.py`, `tools/trials_ledger.py`, `tests/test_gates_split.py`, `VALIDATOR_SPLIT_REVIEW_PACKET_2026-09-23.md` | — |
| Development analyses | `workspace/profit_discovery_2026-09-23/` (`copy_sim.py`, `copy_sim_results.parquet`, `logs/`) | — |

## Questions for the auditor
1. **Point-in-time leaks.**
   - S2 and the DexScreener price are taken at RPC detection time. Run-3 lag from source-block feed arrival is p50 3.4 s, p90 8.0 s, max 10.5 s.
   - Is that residual lookahead immaterial? Should the LATE threshold (10 s) be tighter for S2-sensitive analyses?
2. **Universe.** The 72 h activity universe is warmed up in a background thread. Events recorded before the warm-up finished have `warmup_complete=false` and `universe=false`.
   - Proposed: recompute universe membership offline from `data/warmup/` plus in-run buys with timestamp < T.
   - Confirm that is lookahead-free and should replace the live flag (the pre-registration says universe = trailing 72 h of recorded buys).
3. **Replay correctness.**
   - `state_end_of_block` uses bisect on `(block, logIndex)`.
   - The follower state excludes the follower's own footprint on later swaps.
   - Constant-L fills ignore tick crossings.
   - The `usd_per_q` conversion uses the detection-time price divided by the source post-state price.
   - Please verify against an independent computation for a sample of events, e.g. an archive `eth_call` quoter where available.
4. **Exit sellability `None` case.** The source wallet has already sold, so no transfer simulation from it is possible. Is scoring this as sellable adequate, or should the pre-registration's "missing state" clause apply?
5. **Latency mapping.**
   - Target block = first block with `t_arr ≥ t_sub + 2·ow`, where ow = median sequencer RTT / 2 (measured ~117–142 ms from this host).
   - Check the formula and the `abs*` secondary variants.
6. **Dependence.**
   - The pre-registration uses a token-cluster bootstrap and a design effect of 1.39 (dev pool clustering).
   - Wallet clusters (1.22) and day/cohort clusters (unreliable with 18/43 clusters) are secondary.
   - Is N = 3,500 plus ≥14 days adequate, given the far higher live event rate (~50 FOMO buys/min before filters)?
7. **Evaluator refusal.** `--final` refuses until the stopping rule is met. Confirm it cannot be bypassed without a code change, which would change the hash.

## Known limitations (maker-declared)
- **No v4 Quoter / full sell-route simulation.** S2 is a token-transfer `eth_call` only. Hook-level sell blocks can pass S2.
- **Input-side hook fees** are not observable; handled only by the +1% per side sensitivity.
- **Detection path is RPC polling, not a production feed decoder.** The PRIMARY latency (≈ processing time 1–2.5 s) is conservative; `abs*` variants measure sub-second latencies.
- **Mint/blacklist/pause authority** is not screened.
- **Recorder downtime** between runs 1→2→3 (minutes) is visible as gaps in `events/`; the feed clock is gap-free within each run.
