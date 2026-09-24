# FOMO prospective — Pre-registration Amendment 1 (infrastructure only)

Frozen 2026-09-24 by Agent 1, **before the amended recorder started and before any prospective outcome was computed or
inspected**. Checker authorization: Agent 2 ruling of 2026-09-24 (infrastructure-only amendment permitted). The owner is
informed through the PR that carries this file; the amended recorder is not started until that PR is reviewed.

Base pre-registration: `FOMO_PROSPECTIVE_PREREGISTRATION.md`, SHA-256
`902263424c170fb7920c0a0880f056a8c7cc1b80e9a8dd5f2708a883c72fbc39`. **That file is unchanged, byte for byte.**

## 1. Why (integrity metrics only; no returns were computed)
Frozen evaluator `--integrity` on the pre-amendment sample (`data/`, runs 2–4), 2026-09-24:
- fomo_buy_events 3,256; in_universe 21; eligible 2.
- 0 events with `warmup_complete=true`. The 72 h universe warm-up has never completed in any run.
- loop_errors 138. Since about 10:50 local on 2026-09-24 the public RPC answers HTTP 429 on `eth_getLogs`, and the poll loop has fallen about 59k blocks behind head.
- **feed_missing_frac 0.865.** This is mostly the 24.1 h outage on 2026-09-23/24.

Cause (from the code):
- `rpc()` counted a rate-limited reply as a failure. `get_logs()` then bisected the block range, so every 429 multiplied the request load.
- The warm-up swept 2.6 M blocks in 200k-block chunks through that path, and never finished.

Consequence as frozen:
- The ≥3,500 stopping rule is unreachable before the 45-day cap.
- Events are decided long after their source block, so they fall under Addendum B's LATE rule.

**Pre-amendment sample VOID.** The base pre-registration's integrity clause says: "> 5% of blocks missing timing … VOID; a new pre-registration is required". The pre-amendment sample (0.865 missing) is VOID under that clause, independently of the warm-up defect. This amendment therefore also serves as the re-registration of the **identical** hypothesis on a fresh sample. No outcome of the VOID sample was ever computed.
- Ledger treatment is for the checker to decide. Agent 2's ruling is "same trial, register nothing new".
- Agent 1's view: no look has been taken at any outcome, so the multiple-testing cost is nil either way.

## 2. What changes (data plumbing only)
`workspace/fomo_lane/fomo_recorder.py`:
1. **Rate gate.** A token bucket per RPC method class:
   - `eth_getLogs`: starts at 2/s; floor 0.5/s, ceiling 5/s.
   - Other methods: starts at 10/s.
   - On HTTP 429 the rate halves and a shared cooldown starts at 5 s, doubling up to a cap of 300 s. Every 50 successes the rate rises by 0.25/s.
   - Each 429 is logged to `rtt`.
2. **No bisection on 429.** `get_logs()` raises `RateLimited` instead. Bisection on genuine range errors is kept, as before.
3. **Warm-up.**
   - Low priority: it waits while the live poll loop is more than 300 blocks behind, and uses at most half the gate rate.
   - Adaptive chunks: start 20,000 blocks, halve on non-rate errors down to 100, grow ×1.5 up to 200,000. No recursive bisection.
   - A range that still fails at 100 blocks is logged as `warmup_gap` and retried until it succeeds.
   - `warmup_complete=true` only after a gap-free pass over the whole 72 h window.
   - Progress rows go to `rtt`.
   - The wallet-code check (`eth_getCode`) is retried 3× before a failure counts as "not a FOMO wallet".
4. **Output directory.** Output goes to `data_amend1/`. The pre-amendment `data/` is kept untouched for the record. The start row carries `"amendment": "FOMO_PROSPECTIVE_PREREGISTRATION_AMENDMENT_1.md"`.

`workspace/fomo_lane/evaluate_prospective.py` (sample selection and clock only):
- Reads `data_amend1/`.
- New `eligible_counted` = eligible **and** `warmup_complete`. The stopping rule and the final sample use it. `events_pre_warmup` is reported.

## 3. What is byte-identical (unchanged)
- **Hypothesis and source-event definitions:** FOMO wallet test, executor Transfer, single identifiable swap, UNROUTABLE exclusion.
- **Universe:** U(T) = ≥10 buys in 72 h, including the warm-up block-to-time conversion at 10 blocks/s.
- **Filters:** the $100 notional filter; S1/S2/S3; the $500 size.
- **Execution model:** timing model, entry and exit states, fill math, the 1800 s exit, exit-sellability, gas $0.66.
- **Decision code:** `handle_buy`, `ingest_pool_log`, `universe_ok`, `run_exit_checks`, `v4_key`, the feed clock and RTT probe are all unchanged.
- **Evaluation:**
  - primary statistic, MUE +5.0%, token-cluster bootstrap (10,000 resamples, seed 20260923);
  - PASS/FAIL/INCONCLUSIVE/-TAIL/UNDERPOWERED rules;
  - Addendum B LATE rule (>10 s);
  - all secondary reports.
- **Stopping thresholds:** N = 3,500; ≥14 days; 45-day cap.

## 4. Sample clock (declared before any outcome)
- **Counted events:** only those recorded by the amended recorder (`data_amend1/`) with `warmup_complete=true`. Events before warm-up completes are recorded and reported, not counted.
- **Pre-amendment events** (`data/`, including the 2 eligible) are excluded from evaluation and kept for the record.
- **Day clock:** the 14-day minimum and the **45-day cap run from the amended restart** (the first `start_head` row in `data_amend1/rtt`), not from the original 2026-09-23 start.
- **VOID rule:** the >5% missing-timing rule applies to the amended sample's own block span. Recorder restarts create gaps, so the amended run must stay up continuously.
  - The earlier 24.1 h outage happened because the recorder did not survive a reboot.
  - Making it reboot-persistent is an OS-level change and is left to the owner.

## 5. Verification (offline, no network)
`workspace/fomo_lane/amend1_plumbing_check.py` runs against a mock RPC that sends periodic 429s and rejects ranges over 50k blocks. Results:
- Warm-up completes with every expected log (37/37), no gaps, and 2 throttling cool-downs.
- An always-429 `get_logs` makes exactly 40 calls, with no bisection.
- A low-priority call blocks while the poll loop lags and is released when it catches up.

Result: `ALL OK`.

## 6. Hashes (frozen with this file)
| File | SHA-256 |
|---|---|
| `FOMO_PROSPECTIVE_PREREGISTRATION.md` (unchanged) | `902263424c170fb7920c0a0880f056a8c7cc1b80e9a8dd5f2708a883c72fbc39` |
| `workspace/fomo_lane/fomo_recorder.py` (amended; replaces `db2f0f36…`) | see `FOMO_PROSPECTIVE_PREREGISTRATION_AMENDMENT_1.sha256` |
| `workspace/fomo_lane/evaluate_prospective.py` (amended; replaces `0ce2041e…`) | see `FOMO_PROSPECTIVE_PREREGISTRATION_AMENDMENT_1.sha256` |
| `workspace/fomo_lane/amend1_plumbing_check.py` | see `FOMO_PROSPECTIVE_PREREGISTRATION_AMENDMENT_1.sha256` |

## 7. Restart procedure (after PR review only)
1. Agent 2 reviews the PR and the owner has been informed.
2. Stop run 4 (pid 30560, old code `db2f0f36…`).
3. Verify the three code hashes against the `.sha256` file.
4. Start `fomo_recorder.py` from `workspace/fomo_lane/`.
5. Report only integrity metrics until the stopping rule is met: events, `eligible_counted`, `events_pre_warmup`, feed_missing_frac, 429 cool-downs, warm-up progress.
