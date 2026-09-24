# HEIMDALL — AGENT HANDOFF & OPERATIONAL BRIEF
_Canonical onboarding document for new agent sessions. Read this alongside `HEIMDALL_MEMORY.md` and `AGENTS.md` before executing any commands or writing code._

---

## 0. MANDATORY FIRST ACTIONS
1. **Read Memory First:** `HEIMDALL_MEMORY.md` is the single source of truth for all settled numbers, test logs, and architectural verdicts. Never re-derive a settled fact or pick a previously killed direction.
2. **Run Integrity Check:**
   ```bash
   python tools/check_core_purity.py
   pytest tests/test_prop_engine.py tests/test_inversion_model.py tests/test_null_entry.py -q
   ```
   *Rule:* `/core` may NEVER import `/meta`. If `check_core_purity.py` fails, stop immediately.

---

## 1. PROJECT ESSENCE & CURRENT PHASE
* **Nature:** Autonomous **prop-account survival machine** targeting **LucidTrading 50K FLEX** (CME index futures: MES/ES, MNQ/NQ).
* **Core Philosophy:** We do NOT hunt alpha. Three alpha edges (crypto funding carry, cross-venue spread, liquidation cascade) died when tested. The edge is **risk discipline and trailing MLL survival** (`core/risk/prop_engine.py`).
* **Confirmed Target Numbers (Lucid 50K FLEX, July 2026):**
  * Starting Capital: $50,000
  * Profit Target: $3,000
  * Max Loss Limit (MLL): $2,000 EOD-trailing ("Below Initial Trail")
  * Daily Loss Limit: **NONE** (earlier $1,000 DLL was a corrected hallucination)
  * Sizing Cap: 4 mini / 40 micro contracts
  * Minimum Profitable Days: 5 days of >= $150 profit each
  * Mandatory Flatten: 16:45 EST (session close)
  * Commissions: MES/MNQ $1.00 round-turn; ES/NQ $3.50 round-turn

---

## 2. HARD RISK ENGINE INVARIANTS (`core/risk/prop_engine.py`)
* `daily_buffer = 325` — Optimal daily loss stop (Monte Carlo proof: 325 > 400 > 500 pass rate).
* `kill_cushion = 400` — Account flattens $400 ABOVE the real MLL floor; we never touch the hard line.
* `protect_green_at = 500` — Once up $500 intraday, stop loss is tightened; never round-trip a green day.
* `session_flatten = 16:45 EST` — No overnight holds.
* **Stop-Slippage Tax (Milestone 5 Falsification):**
  * A true random 50/50 coin loses -$1.625 EV/trade mechanically because target fills are clean while stop fills suffer adverse slippage and gap risk.
  * "Risk engine only + coin flip" is FALSE. Every strategy MUST have real directional edge to clear this execution tax.

---

## 3. THE 11 DEAD ENDS — DO NOT REVISIT
1. **Single-Venue Funding Carry (Binance BTC):** Dead. Fees kill always-on carry; right-tail events too rare to pass OOS gate.
2. **Cross-Venue Funding Spread (Hyperliquid vs Binance):** Dead. Spread decayed ~7x over 2 years (1430 -> 200 bps ann).
3. **Liquidation Cascade Reversion:** Dead. Sub-minute latency wall (our 4-12s stack cannot capture it).
4. **Generic Retail TA (ES/MES):** Dead. VWAP reversion, trend pullback, time-structured scalp, daily breakout cluster at 42-50% win rate; friction consumes gross profit.
5. **Indicator Filters on Retail TA:** Dead. Vol/time/trend filters only trim trade count, cannot turn negative EV positive.
6. **ES Swing Trend (20d breakout):** Dead. Only 16 holdout trades in 2 years (statistically unvalidatable).
7. **Null-Entry 50/50 Scalping:** Falsified. Proven negative EV after stop-slippage drag.
8. **Fabio Valentini IVB Model (ORB + Delta):** Dead. Marketing theater; failed independent replication.
9. **ATAS Platform:** Dead. dxFeed does not support delta/order-flow footprint export in trial, no bulk export.
10. **Okala 80/20 (NQ) v1 & v2:** Dead. Mechanical 2-candle sequence at 80/20 levels on 200s bars produces 0 trades over 2 years; edge lives only in discretionary human eyes.
11. **Small-Cap Shorting (Kris Verma / Dux):** Rejected. Equities market, cannot trade on CME futures Lucid account.

---

## 4. CURRENT REPOSITORY ASSETS & STATE
* **Engine & Funnel:**
  * `core/risk/prop_engine.py` — The core product.
  * `core/validation/battery.py` — Statistical battery (DSR > 0.95, PBO < 5%, MC-perm < 0.05, NWt > 2).
  * `tools/prop_montecarlo.py` — Monte Carlo pass rate simulator under Lucid rules.
* **Live Candidate #1 (Portfolio Ready):**
  * `core/alpha/inversion_model.py` — Dhesi Trades ICT Inversion Model.
  * Setup: Pure price action on MNQ 1m (liquidity sweep -> HTF FVG inversion -> 15m retrace -> LTF FVG entry).
  * Metrics: MNQ holdout 13 trades, 38.5% win, RR 2.05, positive skew (+0.79), +$26.31/trade mean. Walk-forward 3/4 green.
  * Limitation: Sparse (~7 trades/year). Cannot pass a 5-day profit rule alone.
* **Strategic Direction:** An **OR-PORTFOLIO** of 4–5 independent, sparse, positive-expectancy strategies managed by the prop risk engine (5 strategies x 20 trades/yr = 100 trades/yr = passable).
* **Data in Hand:**
  * `data/MNQ_1m.parquet` — 2-year Databento GLBX.MDP3 continuous 1m CME data (clean, 0 NaNs).
  * `data/MES_1m.parquet` & `data/ES_1m.parquet` — Matching 2-year 1m data.

---

## 5. SIERRA ROADBLOCK REMOVED
* **Next Strategy Thread:** Order Flow Absorption & Aggression (Rule Sheet 2 in `Trading Philosophy and Order Flow Analysis_ Structured Rule Sheets.md`).
* **POC:** PASSED. NQ continuous one-minute bars contain real BidVolume/AskVolume and reconcile to total volume with 0.00% material mismatch.
* **Archive:** 90-day validated continuous parquets exist for NQ/MNQ/ES/MES/GC/MGC/CL/MCL/RTY/M2K/YM/MYM. See `data/sierra/MANIFEST.md` for exact rows, ranges, hashes, and caveats.
* **Limit:** These are bar-level trade-volume fields, not MBO/order-book queue history.
* **Loader:** `tools/sierra_csv_loader.py` matches the observed Sierra header (`Last`, not `Close`) and emits the eight-column standard schema.

---

## 6. NEXT WORK ORDER FOR THE AGENT
1. Order-flow absorption v1, price-level footprint v2, and initiative-continuation v3 are complete and DEAD.
   V3 looked profitable in development (+$9.50/trade) but failed untouched holdout (-$12.68/trade, 39.29%
   wins, 1/4 positive buckets). Do not tune, loosen, or rerun any of them. Read the exact funnels in memory.
2. The paid Sierra acquisition is complete: 67,772,289 one-tick NQ records plus the multi-market 90-day
   bar archive are preserved and checksummed. No further data purchase is currently justified.
3. DONE 2026-09-22 (see `STRATEGY_RESEARCH_2026-09-22.md`): LuxAlgo POC sweep reclaim and Casper opening-FVG
   scalp both REJECTED by measured holdout results; four other YouTube videos are not faithfully testable.
   Value-area re-acceptance (`VA_REACCEPTANCE_PREREGISTRATION.md`) FAILED its Stage 1 proxy-fidelity gate, so
   its Stage 2 must not run on proxy data. It is blocked by missing data, not rejected. Next decision is the
   owner's: authorize a cost QUOTE ONLY for multi-year NQ/MNQ trade-level data, or pause strategy tests until
   Lucid API access is confirmed. The Dhesi inversion remains the only positive but sparse candidate.
4. Futures execution remains blocked on written confirmation of API access for the exact Lucid account
   (Rithmic R|Protocol or CQG) and the owner's production host choice. Do not build an adapter before that.
5. Keep wallet-copy read-only/offline. Do not add RPC, signing, approvals, or order submission without a
   provider cost quote plus exact chain/router/wallet inputs.

## 7. PENDING (not settled; do not copy into memory) — 2026-09-23
- Profit discovery checkpoint 2: `PROFIT_DISCOVERY_CHECKPOINT_2026-09-23.md` (WINNER NONE, STATUS CHECKPOINT).
  Wallet copy-entry/fixed-exit = INCONCLUSIVE (honeypot-sensitive, tail-driven); mirror and cluster copy <= 0 realizable;
  T13 HL alt carry = REVISE-SPEC/leaning reject (same family as the killed spread) — NOT pre-registered.
- Superseded memory statements: `MEMORY_SUPERSESSION_2026-09-23.md` (S1–S13). Dhesi v2 is INCONCLUSIVE, not "Live Candidate #1".
- Validator: `VALIDATION_AUDIT_2026-09-22.md` + `VALIDATION_COMPLETION_2026-09-23.md` are a blocking dependency for any new test;
  every verdict must be split ALPHA / EXECUTION / DEPLOYMENT with PASS/FAIL/INCONCLUSIVE/N/A and a pre-declared power check.
- The External Alpha (Phase 2) memory block is provisional too; treat its SURVIVING list as pending.
- 2026-09-23 LANE A (FOMO prospective): frozen prereg `FOMO_PROSPECTIVE_PREREGISTRATION.md` (SHA 902263…fbc39); recorder
  RUNNING read-only (`workspace/fomo_lane/fomo_recorder.py`, run 3 from epoch 1790139605). Do NOT compute outcomes before
  the stopping rule (>=3,500 eligible AND >=14 days, cap 45 days); `evaluate_prospective.py --integrity` only.
  Review packet: `FOMO_LANE_A_REVIEW_PACKET_2026-09-23.md`. Validator split awaiting Agent 2 audit:
  `VALIDATOR_SPLIT_REVIEW_PACKET_2026-09-23.md`. Trials ledger flags the Jul–Sep futures window as NOT fresh (DISPUTED
  vs memory's "untouched" initiative-v3 holdout) — owner decision.
