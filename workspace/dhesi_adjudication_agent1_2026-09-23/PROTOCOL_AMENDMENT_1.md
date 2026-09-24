# DHESI V3 — VALIDATION PROTOCOL AMENDMENT 1 (infrastructure only)

Prepared 2026-09-24 by Agent 1 on owner work order "PRE-VALIDATION HARDENING RELEASE" (base commit
8f70789801a2fc02b94f3159ebf3bf1b583d347c). Addresses Agent 2 findings D3 and D4
(`workspace/agent2_external_strategy_audit_2026-09-24/DHESI_V3_FIREWALL_AND_BINDING_AGENT2.md` §2).

**Unchanged:** the hypothesis (`DHESI_V3_CANONICAL_SPEC_V1.md`, SHA-256 8f330ae2…9c6059, bytes unchanged), the frozen
code, the reference engine's rules, costs, the untouched window, μ_min, every statistic and every decision rule of
`DHESI_V3_VALIDATION_PROTOCOL_V1.md` (SHA-256 49d8d8b9…148793, bytes unchanged). This amendment is read together with
Protocol V1 and overrides it only where stated below. STRATEGY_LOGIC_CHANGE = NO.

## A1. Replaces Protocol V1 §4.5 (frozen/reference disagreement)

Old text: "The verdict stands on the frozen code. Any frozen/reference disagreement must be itemised trade by trade in
the report; it cannot change the verdict."

New rule:
1. In the one authorized run the validator executes the frozen engine and the independent reference engine on the same
   rows and writes, **before any statistic is computed**, `primary_run/FROZEN_ENGINE_TRADES.{csv,parquet}`,
   `primary_run/REFERENCE_ENGINE_TRADES.{csv,parquet}` and `primary_run/ENGINE_COMPARISON.json`.
2. Each ledger row carries: trade_id (session|side|entry_ts), signal_ts (= entry_ts: both engines decide and enter on
   the close of the 5-minute LTF inversion bar, spec §6), side, session, sweep_pool (setup identifier), entry_ts,
   entry_price, stop_price, tp1_price, runner_target_price, contracts (position size), exit_ts, exit_price, reason,
   tp1_hit, risk_dollars, gross_pnl, costs (= gross_pnl − pnl), pnl.
3. ENGINE_COMPARISON.json lists trade counts, matched count, ids missing on either engine, every field-level mismatch
   and the exact maximum absolute numeric difference per field. Gate: **100% agreement** on the 16 strategy-defining
   fields (entry_ts, exit_ts, session, side, entry/exit/stop/tp1/runner prices, contracts, risk_dollars, gross_pnl,
   pnl, tp1_hit, reason, sweep_pool); numeric tolerance 1e-9 (float noise on tick-grid prices).
4. If the gate FAILS the validation result is **INVALID**: no statistic, verdict or strategy conclusion is computed or
   issued. The persisted ledgers allow the disagreement to be itemised **without** re-reading the reserved window.
   §4.6 (no rerun after a printed result) still applies; an INVALID result is a printed result.

## A2. Extends Protocol V1 §2.4 integrity gate 1 (row validity)

Gate 1 now requires, on every row of the harvested file: valid, unique, strictly increasing timestamps; finite
open/high/low/close **and volume**; volume ≥ 0; OHLC geometry (high ≥ low, high ≥ max(open, close), low ≤ min(open,
close)). Zero volume is valid and counted. Nothing is imputed. Any failure BLOCKS the harvest.
Also reported: index timezone, per-session RTH row counts, sessions below 370 rows, intra-RTH gaps > 1 minute, roll
dates inside the file range (gate 4), and the gate-3 equivalence share at minute lags −1/0/+1 (gate 3 now also fails
if a neighbouring lag is strictly better than lag 0, i.e. a stamp shift).
Scope clarification: these outputs are **counts of invalid cells/rows**, not summaries of prices, returns, ranges,
volatility or volume; they are integrity metadata under §2.4 "Allowed". The validator repeats gate 1 on the consumed
rows and refuses to start the engines (result INVALID, nothing computed) if it fails.

## A3. Authorization binding (Protocol V1 §4.2)

`DHESI_V3_RUN_AUTHORIZATION.txt` must contain `AUTHORIZED_BY_OWNER` and the current SHA-256 of: the validator, the
canonical spec, Protocol V1, this amendment, and `dhesi_v3_harvest_integrity.py`. The validator enforces all five.

## A4. Non-material fixes carried in the same infrastructure revision
- D1: validator comment now cites spec §12 / protocol §3, §8 (cosmetic).
- D2 (reporting gap: top-5 share, DSR, achieved power, PROP label word) remains **open**; all are derivable post-hoc
  from the persisted frozen ledger without re-reading data.
