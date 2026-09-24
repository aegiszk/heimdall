# HEIMDALL — Tick-level edge discovery + graveyard integrity (2026-09-23)

**Written by:** Agent 2.

**Data status:** all NQ ticks used here are **DEVELOPMENT data**: 140 trading days, 2026-03 → 2026-09, 67.8M records. Nothing here may be reported as untouched validation.

**Scope:**
- No orders, no paid data, no strategy optimization.
- `HEIMDALL_MEMORY.md` not edited.

**Labels:**
- [V] verified.
- [I] inferred.
- [U] unverified.

## 0. Blockers — fixed / remaining

| Blocker | State |
|---|---|
| Host clock 15.95 s fast (Windows Time service **stopped**) | **FIXED.** Service set to Automatic, NTP peers configured, forced resync (UAC approved). SNTP now measures **+4 to +12 ms**. HL tape `recv_ns` jumps ~16 s at the fix time; correctable from the logged offsets. |
| HL recorder not reboot-persistent | **FIXED.** Per-user Startup entry `Heimdall_HL_Tape_Recorder.cmd`. |
| HL recorder had died | **Found and restarted.** It stopped 2026-09-23 06:25 UTC (a reboot at 16:39 local); restarted 13:24 UTC. **Gap 06:25–13:24 UTC is declared and unrecoverable.** |
| Dhesi v2 "labelled rerun needed" (D4 wrong-side stops) | **FIXED:** frozen `validate_inversion_v3.py` run once (prereg SHA verified). Result: §5b. |
| CL tick history (needed for B) | **NOT FIXED — owner GUI step.** No computer-use tools in this session. CL `.scid` are still 1-minute (unchanged since 2026-09-22). |
| Sierra live recorder proof | **NOT FIXED — owner GUI step** (add the study to charts). |
| AWS cost discovery, Databento key, Lucid API / Sunday confirmations | Owner accounts / external parties. |

## 1. NQ event-time atlas

**Setup** (script `nq_event_atlas.py`, registry `nq_event_atlas_registry.json`, per-event file `nq_event_atlas_events.parquet`):
- 5.1M events, 22 family/threshold configurations (all logged; none dropped).
- Percentile thresholds calibrated on the first 20 days only, then frozen.
- Direction: aggressor side, or sign of signed volume.

**Timestamp precision [V/I]:**
- Sierra stamps are unique at 1 µs, but the true resolution is **1 ms** (the p10 inter-trade gap is exactly 1 µs, i.e. uniqueness increments).
- So **50 ms and 100 ms horizons are TESTABLE at ms resolution.**
- Whether the stamp is exchange time or Sierra server time is **UNVERIFIED**, and no reaction latency is included in the "from-event" markouts.

**Price reference — two corrections, both disclosed:**
1. The first run used a last-buy / last-sell mid proxy. It is **INVALID**: it lags up to 5 s and manufactured +1.05 tick (50 ms) to +2.42 tick (1 s) markouts for *random* trades. Kept as `*_STALE_MIDPROXY_INVALID.*`.
2. The second run uses an aggressor-adjusted mid (px − side·½ tick), which is exact only when the spread is 1 tick.
   - Quote-free data shows the gap between a trade and the latest opposite-side trade within 1 s is spread over 0–7+ ticks. So **the spread cannot be pinned from trades**, and this reference is approximate.
   - The **baseline** (every 1000th trade) passes on *tradable* markouts: 10 s −0.03 ticks (t −0.1), 60 s +0.05 (t 0.1).
   - From-event markouts at ≤1 s are positive for random trades (+0.55 tick at 50 ms): the same aggressive order sweeping further levels within the same millisecond. Real but **not tradable**.

**Tradable markout** = mid(t+250 ms+h) − mid(t+250 ms), in ticks. Day-clustered t; full table in `nq_event_atlas_summary.csv`.

| Family (threshold) | Events/day | x10 s | t | x60 s | t | Months same sign | Reading |
|---|---|---|---|---|---|---|---|
| E1 same-side run k8 / k16 / k32 | 14,206 / 2,971 / 460 | −0.47 / −0.64 / −0.69 | −7.1 / −7.2 / −2.3 | −0.81 / −1.25 / −1.37 | −6.4 / −6.4 / −2.1 | 7/7 | fade (see artifact test) |
| E2 arrival acceleration p99 / p99.9 | 14.1 / 0.7 | +2.03 / −9.0 | 1.2 / −1.4 | +1.98 / −16.6 | 0.6 / −1.5 | 3/7 / 5/7 | noise |
| E3 signed volume 1 s p99 / p99.9 | 34.8 / 2.4 | −1.66 / +0.24 | −1.4 / 0.1 | −2.01 / −0.54 | −1.1 / −0.1 | 5/7 | nothing tradable after 250 ms |
| E4 large print ≥20 / ≥50 / ≥100 lots | 141 / 20.4 / 4.3 | +0.23 / +0.43 / **+4.64** | 0.8 / 0.5 / **2.5** | +0.40 / +1.60 / +5.77 | 0.5 / 1.0 / 1.8 | 3/7 / 3/7 / 5/7 | size dose-response; tail-driven (below) |
| E5 two ≥20-lot prints in 1 s | 17.4 | −0.67 | −0.4 | −3.27 | −1.1 | 5/7 | noise |
| E6 1-lot same-side sequences k20 / k40 | 1,106 / 128 | −0.39 / −0.54 | −1.8 / −0.6 | −1.04 / −1.57 | −3.4 / −0.8 | 7/7 / 5/7 | fade |
| E7 same-ms sweep k5 / k10 (unbundled PROXY; true flag unavailable in .scid) | 13,630 / 3,292 | −0.81 / −0.87 | −5.8 / −8.8 | −1.26 / −1.56 | −7.1 / −6.7 | 7/7 | fade (see artifact test) |
| E8 high flow + high displacement 5 s | 13.7 | −2.78 | −1.6 | −4.12 | −1.3 | 6/7 | no continuation |
| E9 high flow + low displacement 5 s (overlaps DEAD absorption) | 2.2 | +0.09 | 0.0 | −3.03 | −0.7 | 4/7 | nothing |
| E10 failed continuation → reverse | 17.6 | +2.03 | 1.6 | +3.17 | 1.5 | 4/7 | weak; flips by contract/session |
| E11 flow exhaustion | 0.7 | −1.28 | −0.4 | −3.69 | −0.8 | 3/7 | n=100, noise |
| E12 immediate reversal | 0.1 | — | — | — | — | — | n=8, untestable |

**Other measured quantities:**
- MAE/MFE medians over 10 s are 10–30 ticks for rare-event families: noise dominates.
- Impact per 100 lots is in the summary.
- Every family has P(reversal at 60 s) of 0.46–0.60.

## 2. Economically meaningful NQ phenomena — **NONE established**

**Sweep / run fade (E1, E6, E7):**
- Very consistent: every month, every contract, every session has the same sign; median −1 tick; no tail dependence; −0.6 to −1.6 ticks at 60 s.
- But on the ~3% of events where a 1-tick spread is verified at both entry and exit, it shrinks to −0.4 to +0.2 ticks (|t| ≤ 2.7) (`spread_artifact_test.json`).
- It **cannot be separated from post-sweep spread widening in the reference price** without real quotes.
- Even at face value it is 0.2–0.6× the 2.7-tick taker friction. That friction assumes a 1-tick spread and is **optimistic**.
- Class: **INFORMATION-OR-ARTIFACT, NOT ECONOMIC as taker. Maker version: INSUFFICIENT DATA** (needs queue/fill data).

**Large print ≥100 lots (E4):**
- 10 s: +2.0 ticks pooled, median +1, positive in all 3 contracts and all 4 sessions.
- 60 s: flips by contract (NQU26 −0.33), by session (RTH open −4.1 vs ETH +7.8) and by month. Top-10 events = 98–119% of the sum.
- 10 s effect / friction = 0.74. Day t 2.5 among ~105 tests (Bonferroni ~3.5).
- Class: **INFORMATION BUT NOT ECONOMIC; not multiple-testing robust.** Size dose-response (≥20 → ≥50 → ≥100) is the only structural hint → WATCH.

## 3. CL EIA tick results — **BLOCKED (no CL ticks yet)**
- The 1-minute result stands (earlier lab): ~2× displacement and volume in minute 0; no continuation or reversal after minute 1.
- The windows 0–1 s … 1–2 min and the five mechanistic questions await the harvest (§8, step 1).

## 4. Effect size vs friction

| Phenomenon | Tradable move | Friction (NQ taker, 1-tick-spread assumption) | Ratio | Class |
|---|---|---|---|---|
| Sweep / run fade (60 s) | 0.6–1.6 ticks (face value) | 2.7 ticks | 0.2–0.6 | Information-or-artifact; not economic |
| Large print ≥100 (10 s) | 2.0 ticks mean, 1 median | 2.7 | 0.74 | Information, not economic |
| Everything else | \|x\| < 2 ticks with \|t\| < 2, or n too small | 2.7 | < 1 | No information |

## 5. Graveyard integrity table

Defects considered:
- **D1** DSR units. **D2** 1-lot MC. **D3** 5 m stop-first. **D4** wrong-side stops.
- **N1** holdout reuse. **N2** max-dd scale. **N3** off-tick targets. **N4** zero-PnL drop. **N6** iid MC.
- **NEW-C:** carry fee charged every bar.
- **NEW-S:** same-bar stop-first depresses random win rate to 45.8–49.9% at 0 slippage.

| # | Family | Actual kill reason (evidence) | Defects touching it | Could the defect flip sign / deployment? | Class |
|---|---|---|---|---|---|
| 1 | Single-venue funding carry (Binance BTC) | "Always-on negative" came from `carry.py:14` charging the fee **every hourly bar** (≈17.5%/yr phantom). Fat-tail thresholds too rare in holdout. | **NEW-C** | **Yes for the always-on verdict.** Recomputed correctly on HL: +0.8 to +5.0 pp/yr over USDC lend. Low, not Lucid. | **DEAD BUT VALIDATOR-BUG AFFECTED → FALSE KILL of mechanism; economically a low-yield treasury carry, not alpha** |
| 2 | Cross-venue funding spread | Measured decay 1430 → 200 bps/yr by half-year; ETH regime-switching. | none (data refetch discrepancy noted) | No | ROBUSTLY DEAD |
| 3 | Liquidation-cascade reversion | 25–35 events (underpowered) + a latency wall that was **assumed, never measured**. | clock 15 s fast (fixed today) | Unknown | **INCONCLUSIVE / BLOCKED DATA** (HL liquidation fills are paid; Reservoir) |
| 4 | Cross-sectional crypto momentum | Work order issued, **never run** (prop pivot). | — | — | **NEVER TESTED** (not dead) |
| 5 | VWAP-rev / trend-pullback / time-scalp (MES) | Holdout gross ≈ 0 (VWAP +$0.22, t 0.12; scalp +$0.14, t 0.43); net negative. | D2, N3 (conservative, $0.095/trade), NEW-S | No: gross ≈ 0 | ROBUSTLY DEAD |
| 6 | Filters on TA | All 4 walk-forward buckets negative. | D2 | No | ROBUSTLY DEAD |
| 7 | ES swing 20-day breakout | Sizing bug (1 ES = 2–3× risk budget); 16 holdout trades. | sizing (execution) | Unknown (n=16) | **INCONCLUSIVE + EXECUTION-BUG AFFECTED; BLOCKED** (overnight permission, years of data) |
| 8 | Null entry 50/50 | Random entry negative even at 0 stop slippage (−$1.0 to −$2.9 per trade; commission). | NEW-S (win 45.8–49.9% at 0 slippage → same-bar stop-first) | Direction no; **magnitude yes.** The "stop-slippage tax is the unifying mechanism" claim is overstated. | ROBUSTLY DEAD (direction) / EXECUTION-MODEL-AFFECTED (magnitude) |
| 9 | Fabio ORB+delta | Holdout n=166, −$24.71/trade, t −1.88 [V trade log]. | N1, N4 (0 impact), D1 | No | ROBUSTLY DEAD |
| 10 | ATAS | Platform capability, not a strategy. | — | — | N/A |
| 11 | Okala v1/v2 | 0 trades as coded. | — | — | **INCONCLUSIVE** (untestable as spec'd; alpha N/A) |
| 12 | Small-cap shorting | Wrong venue. | — | — | BLOCKED (venue) |
| 13 | Dhesi inversion v2 | 13 holdout trades, CI [−135, +188]; D4 wrong-side stops. | **D4**, D2, N1 | **Yes: D4 flipped v2 from −$446 to +$617** | **FALSE KILL (as "dead end"); now INCONCLUSIVE, positive but underpowered** (v3: holdout +$34.8/tr, n=20; fresh +$94.6/tr, n=4) |
| 14 | Absorption v1/v2 | 0 trades (frequency). Tick atlas E9 (related) shows nothing. | — | No | INCONCLUSIVE as spec'd; related tick phenomenon = no information |
| 15 | Initiative v3 | 28 holdout trades, −$12.68, CI [−37, +12] contains dev +9.50. | N1 | Unknown | INCONCLUSIVE (underpowered) |
| 16 | LuxAlgo POC reclaim | Worst −5.20 / resolved −2.24 / best-ordering +2.08. | **D1, D3** | Only under best-case intrabar ordering | DEAD BUT VALIDATOR/EXECUTION-BUG AFFECTED (lean dead; resolvable with ticks for 2026 only) |
| 17 | Casper opening FVG | Holdout gross t 0.10. | D1 | No (gross ≈ 0) | ROBUSTLY DEAD |
| 18 | Intraday momentum | Holdout −$11.65, 0/4 buckets ≥ 0; literature shows decay. | N1 | No | ROBUSTLY DEAD |
| 19 | Value-area re-acceptance | Proxy fidelity 0.68%. | — | — | **BLOCKED DATA → unblockable at $0** (Sierra tick history from 2011, included) |
| 20 | All "Lucid MC 0%" lines | 1-lot sizing. | D2, N6 | Yes for the PROP verdict | PROP-ONLY verdicts, not alpha kills |

### 5b. Dhesi v3 frozen rerun
**Run facts:**
- Frozen `validate_inversion_v3.py`, run once. Prereg SHA-256 `C9D143E5…D843` verified.
- Output: `data/strategy_research/dhesi_v3_validation_2026-09-22.json`, `dhesi_v3_development_trades.csv`, `dhesi_v3_fresh_trades.csv`.

**Results:**
- **v2 reproduction** (all v3 fixes off): 30 trades, −$446.38 total. Reproduction is exact.
- **Single-fix ablation `stop_guard` only (the D4 fix):** 26 trades, **+$617.13, +$23.74/trade**. **D4 flips the sign** of v2's result. The other single fixes (htf_24h, early_sweeps, session_pools, attempts) stay negative.
- **v3 development** (MNQ 1m, REUSED 60/40 holdout, N1):

  | Split | Trades | Win | Mean per trade | Realized RR | Skew |
  |---|---|---|---|---|---|
  | Train | 29 | 44.8% | +$62.2 | — | — |
  | Holdout | 20 | 50% | +$34.8 | 1.36 | +0.44 |

  Holdout buckets: +$36.3 / −$12.7 / +$53.2 / +$74.0 (3/4 positive).
- **Fresh window** (Sierra 2026-07-01 → 09-18, first read): **4 trades**, 2W / 2L, +$94.6/trade, RR 2.0.
- Gate: FAIL `min_trades` (20 < 30). Lucid MC (1-lot, D2): 0.13–0.21% pass.
- Script verdict: **"SURVIVING RESEARCH CANDIDATE (not validated)"**.

**Reading:**
- The D4 execution bug materially depressed v2.
- With stops fixed, the sign is positive in every split, but n = 20 + 4 trades is far below power (~1,000 trades needed per the audit).
- The only honest route to validation is more *fresh* history: Sierra NQ/MNQ ticks and 1-minute data from 2011–2024 were never used.
- Class moves from INCONCLUSIVE to **INCONCLUSIVE, EXECUTION-BUG-CORRECTED, POSITIVE-BUT-UNDERPOWERED**.

## 6. False kills discovered
1. **Funding carry "fee-killed"** (family #1): a false kill caused by charging the fee every bar. Mechanism reopened; economics are low-yield and not Lucid. **Not resurrected as a strategy.**
2. **Null-entry "stop-slippage tax" as the unifying mechanism:** overstated. Same-bar stop-first depresses random win rates to 46–50% at zero slippage. Direction still correct.
3. **Cross-sectional momentum** is listed as dead in the handoff narrative but was **never tested**.
4. **Value-area re-acceptance** is "blocked by data" that Sierra already includes at no cost.
5. **Dhesi inversion:** the handoff lists it as a "dead end" family. Its v2 result was **sign-flipped by the D4 wrong-side-stop bug** (−$446 → +$617 with only the stop guard). The frozen v3 rerun is positive on the reused holdout (+$34.8/trade, n=20) and on fresh data (+$94.6/trade, n=4). **Not resurrected:** it is underpowered. Its reopen is justified, and the validation path is pre-2025 Sierra history (§8).

## 7. One best new hypothesis: **NONE**
No phenomenon met all five gates (many events, ≫ friction, causal, not graveyard, robust to stratification).

## 8. Exact fresh-data validation plan
1. **Resolve the fade-vs-artifact question with real quotes** (cheapest, decisive):
   - Owner adds the Sierra recorder to NQZ26 (Type 6 quote records give the true mid).
   - After ≥10 RTH sessions, recompute E1/E6/E7 tradable markouts against the recorded **quote mid**. Frozen definitions from this atlas; no threshold changes.
   - PASS for "real": ≥ −0.5 tick at 60 s with day-t ≤ −3 on quote mid.
   - Even if real, it is only economic as a maker. The live quotes also give fill-proxy evidence.
2. **E4 ≥100-lot continuation:**
   - Frozen definition, 10 s horizon.
   - Fresh data = Sierra NQ ticks harvested from **2024–2025** (never used), plus the prospective recorder.
   - PASS: mean ≥ +2.7 ticks tradable at 10 s, day-t ≥ 3, positive in ≥4 of 6 half-years.
3. **CL EIA:** harvest 24 months of CL ticks; run the pre-declared windows. Single pass, no re-cutting.
4. **Dhesi v3** (a graveyard reopen, not a new hypothesis):
   - Harvest Sierra MNQ/NQ 1-minute data for **2019-01 → 2024-06**. It predates the Databento window and was never read.
   - Run the *unchanged* frozen v3 code once.
   - Expect roughly 7–25 trades/yr, so ~40–140 trades.
   - PASS: mean > +$20/trade after costs, day-bootstrap lower bound > 0, and ≥4/6 years positive.

## Artifacts
In `workspace/tick_discovery_2026-09-23/`:
- `nq_event_atlas.py`
- `nq_event_atlas_registry.json`, `nq_event_atlas_events.parquet`
- `nq_event_atlas_summary.csv/.json`
- `robustness.py/.json`
- `spread_artifact_test.py/.json`
- `*_STALE_MIDPROXY_INVALID.*`

## CORRECTION (2026-09-23 15:12Z, Agent 2): Dhesi D4 attribution
The statements above that "D4 flipped v2 from −$446 to +$617" are **wrong in attribution**. An independent trade-level decomposition
(`workspace/dhesi_replication_agent2_2026-09-23/DHESI_D4_INDEPENDENT_VERDICT_AGENT2.md`) shows the change splits into three parts:
- The wrong-side-stop BUG fix: +$34.50 (5 trades).
- A post-hoc 10-point stop floor: +$400 (2 trades).
- **Three skip-enabled replacement trades: +$629.** The sign rests on n=3.
The Dhesi "FALSE KILL" label in §5/§6 is withdrawn. Status: INCONCLUSIVE; any reopen must be a fresh-data test of a frozen spec.
