# HEIMDALL — Lane B: independent checker + orthogonal alpha (2026-09-23)

**Written by:** Lane B (independent checker).
**Scope rules:**
- No edits to Lane A files, `HEIMDALL_MEMORY.md`, shared strategy code, thresholds, or verdicts.
- Every Lane B artifact is in this folder.

**Labels:**
- [V] verified by command this session.
- [I] inferred.
- [U] unverified.

**STATUS:**
- Lane-A audit complete for the W1 / mirror / cluster replay.
- H2 is **BLOCKED** at the wallet level: the historical xyz fills are paid, and the final data must be prospective.
- **WINNER: NONE.**

## 1. Lane-A audit (FOMO / Robinhood Chain replay, `workspace/profit_discovery_2026-09-23/`)

| Component | Verdict | Evidence |
|---|---|---|
| Future leakage | **PASS for W1's point-in-time rule; FAIL for F10 / F12 / F13** (Lane A self-flagged) | The point-in-time ≥5-prior-sells filter re-implemented from raw logs gives n=525 vs Lane A's 530 (sell-direction heuristic differs slightly). The hook tax, `dex`, `priced` and `usd` filters are all known at entry. Mirror exits use the source's sell, observable at exit. Universe = FomoPulse list frozen ~09-05, and the development window is 09-05→09-22, i.e. after selection. |
| Delay model | **PASS on data fidelity; CORRECTION on interpretation** | See "Delay model detail" below. |
| AMM / route fidelity | **UNKNOWN (optimistic in places)** | See "AMM / route detail" below. |
| Survivorship | **PASS for the development window; FAIL for any backfill** (Lane A flagged) | The pre-09-05 backfill of the frozen universe is in-sample to selection. `FOMO_PROSPECTIVE_PREREGISTRATION.md` is referenced in `fomo_trials_dev.json` but **does not exist** → UNKNOWN. |
| Dependence | **PASS with caveat** | See "Dependence detail" below. |
| Tail dependence | **FAIL** | See the tail table below. |

**Delay model detail:**
- An independent public-RPC `eth_getLogs` recount on a stratified sample (36 buys, 12 per size tercile × d ∈ {3, 50, 600}) matched Lane A's cached logs **36/36** on swap count and **36/36** on sqrtPrice [V `chain_recount.csv`].
- "Median entry drift 0.0000" is a *signed* median inside a mass of exact zeros. |drift| is real:

  | Delay (blocks) | Exact-zero share | Median \|drift\| | p90 \|drift\| |
  |---|---|---|---|
  | d=1 | 87% | — | — |
  | d=50 | 27% | 0.7% | 11.7% |
  | d=600 (≈60 s) | 3% | 4.3% | 25.8% |

- Other swaps in the same pool within 60 s: median 25; only 3.2% of buys see none.
- Insensitivity holds **in expectation only**: signed mean drift is +0.25% to +2.1%, and return means are flat across d. It is **not** "no price movement".

**AMM / route detail:**
- Tick crossings are ignored (constant-L).
- Input-side hook fees are not modelled.
- 153 of 866 (17.7%) sampled buys routed through non-v4 pools were skipped (selection).
- Fixed-horizon exits convert quote→USD at the *entry* rate.
- Our own buy is not persisted in exit state. Selling into a state without our footprint double-charges impact → **conservative**.
- The "60m" horizon is 35,000 blocks ≈ 58.7 min at 9.93 blocks/s (minor).
- Lane A's `win` columns divide by rows including NaN: mirror win is reported 29.5% but is actually **36.9%** on non-missing rows (minor, understates).
- **Decisive:** 59 of 699 raw W1 trades exit into pools with **zero swaps within ±5 min of the modelled exit**. They average +95.6% and carry **62% of raw W1 PnL**. Six of the top 10 raw winners are such exits; 7 of the top 15 modelled exits exceed every real sell in the window. See [V `top_winner_realizability.csv`, `w1_pool_activity.csv`].

**Dependence detail:**
- The token-cluster bootstrap barely widens the raw W1 30 m CI: iid [+6.2%, +20.6%] vs token [+5.5%, +21.9%].
- Kish effective N by token = 167 of 699. Wallet clusters: 188.
- Only **18 day-clusters, one memecoin regime**. The real dependence is regime-level and cannot be estimated from 18 days.

**Tail table** (S=$500, d=3, 30 m exit; "real exit" = at least one swap within ±5 min of the exit, a condition observable at exit time):

| Metric | Raw W1 | W1 point-in-time filter | W1 + real exit | PIT + real exit | Mirror |
|---|---|---|---|---|---|
| n | 699 | 525 | 640 | 512 | 564 |
| mean | +13.1% | +11.6% | +5.4% | +7.6% | +19.5% |
| median | −2.0% | −3.1% | −2.7% | −3.5% | −23.0% |
| trimmed 5% mean | +0.6% | −0.4% | — | — | −11.4% |
| top-1 / 5 / 10 share of total | 10% / 43% / 71% | 15% / 59% / 87% | — / — / **130%** | — / — / **116%** | 58% / 106% / 130% |
| mean excluding top 10 | +3.8% | +1.5% | **−1.6%** | **−1.25%** | −5.9% |
| worst | −100% | −98.6% | — | — | −99.9% |
| ES5 | −90.1% | −88.9% | — | — | −99.5% |
| P(total loss ≤ −90%) | 2.9% | 2.7% | — | — | 19.5% |
| max drawdown, sequential $500 | −$4,256 | −$4,053 | — | — | −$11,983 |

**Audit verdict:**
- Lane A's own headline ("ALPHA INCONCLUSIVE, sign not robust") is **confirmed and strengthened**.
- Once exits into zero-activity pools are excluded, the mean without the top 10 trades is negative in every variant.
- W1 must not be promoted on this development window.
- Its prospective test needs (a) an exit-realizability rule fixed in advance, and (b) a pre-registration file that currently does not exist.

## 2. H2 causal threats (assume H2 false)

1. **HL follows CME by construction.** The trade.xyz oracle takes CME futures quotes 23/5; the relayer publishes about every 3 s with a ±1% per-update cap [V docs]. HL market makers hedge on CME.
2. **Fast followers look informed.** A wallet that reacts to CME within 0.2–0.8 s will show a positive HL markout, and a *zero* CME markout. Scoring must use **CME** forward returns measured *after* the Lucid entry opportunity, never HL markouts.
3. **Clock alignment:**
   - HL block time vs receipt p50 315 ms (this host).
   - Sierra timestamp semantics are [U].
   - This host's clock is ~15 s fast and drifting.
   - Mitigation: a full 1-minute delay between the feature minute and the target window, plus timestamp-free lead-lag checks.
4. **Closed-market periods:** outside CME hours the oracle is an internal EMA. Excluded.
5. **Index mismatch:** XYZ100 is not NDX. The basis is controlled; convergence trades are not identity information.
6. **Selection leakage:** any wallet universe drawn from later activity (including the recorder) is forbidden in scoring.
7. **Multiple testing / cohort mining:** 12-test Holm family; one pre-declared survivor.
8. **Development-day contamination:** the Tardis free days 2026-04-01, 05-01, 06-01, 07-01, 09-01 were inspected here. They are **excluded from validation**.
9. **Lucid feasibility:** entries only inside the Lucid session. Overnight-hold permission is UNRESOLVED (memory).

**Revised periods** (supersede my earlier draft):
- Development: all historical data with the five inspected days excluded from validation.
- **FINAL = prospective recorder data from 2026-09-23 onward only.**

## 3. H2 zero-cost results (aggregate only — no wallet identity; development days only)

**Tick-level lead-lag** (HL `xyz:*` trades from Tardis free files, NQ one-tick trades from Sierra; `h2_zero_cost_leadlag.json`):
- HY best lag: **NQ leads HL** on 10/10 day×symbol cells.
  - XYZ100: 200 / 700 / 700 / 600 / 600 ms.
  - SP500: 200 / 700 / 800 / 700 / 700 ms.
  - HL receive time adds another 300–500 ms.
- 1 s Granger, out-of-sample (fit on the first half-day, test on the second):

  | Direction | XYZ100 | SP500 |
  |---|---|---|
  | R²(HL next \| lagged NQ) | 9.5–21.9% | 5.5–12.3% |
  | R²(NQ next \| lagged HL) | −0.21 to +0.15% | −0.21 to +0.15% |

**Minute-level flow test** (`h2_power_check.json`):
- Lean baseline: NQ 1 m and 15 m returns, HL–NQ basis change, 30 m volatility.
- Pooled over 5 days (≈6,485 minutes), leave-one-day-out.

| Flow input | XYZ100 h = 1 / 5 / 15 | SP500 h = 1 / 5 / 15 |
|---|---|---|
| **Lagged (causal) aggregate flow, ΔR²** | −0.09 / −0.23 / −0.65 pp | −0.02 / −0.17 / −0.14 pp |
| **Positive control: leaked flow over the target window, ΔR²** | +3.6 / +4.3 / +4.7 pp | +1.8 / +2.9 / +4.9 pp |

- Contemporaneous correlation of flow with NQ return: 0.14–0.38 per day.
- **Reading:** the pipeline detects 2–5 pp when information is present. Causal aggregate HL flow carries **none** at 1–15 minutes.
- An informed wallet subset diluted in the aggregate is **not ruled out**.
- An earlier heavy-baseline version (24 hour dummies) overfit (baseline R² to −5.4%). A misaligned first positive control (off by one minute) was deleted and superseded.

## 4. Falsification tests

| Test | Status |
|---|---|
| Aggregate-flow-only model | **Done:** OOS R² ≤ 0 at all horizons (0.03 pp at best) |
| Time-shifted flow (±60 min) | **Done (aggregate):** indistinguishable from actual (both ≈0) |
| Future-flow leakage test | **Done:** leaked flow → +1.8 to +4.9 pp (the pipeline can detect); a −60 min "lead" placebo gives no signal |
| Sign-flipped cohorts | Aggregate: **uninformative by construction** (a fitted linear coefficient absorbs the sign). Deferred to the fixed-direction cohort rule. |
| Randomized wallet identities | **BLOCKED** (no historical wallet-attributed xyz fills at $0) |
| Matched random cohorts | **BLOCKED** (same) |

## 5. Fast-server economics (separate latency from economics)

| Hypothesis | Information latency | Network | Decision / signing | Submission + venue | Edge remaining | Bottleneck |
|---|---|---|---|---|---|---|
| Binance → HL lead-lag | HL catches up over 0.5–0.7 s (HY, event time) | This host: Binance +79 ms, HL prints +315 ms; colocation ~ms [I] | <1 ms / ~0.2 ms [I] | HL block ~0.1–0.2 s [I] | **Total** catch-up from t: 2.26–2.70 bps mean; from +300 ms: 1.95–2.37 bps; taker round trip 9 bps | **ECONOMICS.** Even zero latency cannot pay 9 bps. |
| HL maker quote protection | same | same | same | same | Gatto: touch net −0.458 bp pre-fee; our maker fee ≥0.9 bp | **ECONOMICS** (fee tier) |
| H2 (HL flow → MNQ) | HL lags NQ 0.2–0.8 s; HL feed +0.3 s | Lucid / Rithmic path [U] | trivial | CME fill | Aggregate: none detected | **INFORMATION**, not latency (minute horizon) |
| W1 RH-chain copy | Post-sequencing; N+1 at best | Dubai RTT 231–272 ms (Lane A) | ms | ~10 blocks/s | Mean flat across d = 0…600 blocks | **ECONOMICS / tails / realizability** |
| H3 / H4 HL events | minutes | — | — | — | Unmeasured | Data, then economics |

**Conclusion:** no current hypothesis has latency as its binding constraint. Fast servers are not justified by any evidence in hand.

## 6. Data gap

**$0 sources exhausted for wallet-level H2:**
- HL `recentTrades`: last 10 only.
- `userFillsByTime`: per known user, ≤10,000 fills, and wallets can't be enumerated without future data.
- Tardis: no wallet IDs.
- Dune: enterprise-gated.
- Allium: free tier of 20k credits, but coverage of HIP-3 / xyz with addresses is undocumented [U], and it needs an owner signup.
- Hydromancer Reservoir, Artemis and HL official S3 are all **requester-pays** [V anonymous AccessDenied].
- The prospective recorder is **reserved as FINAL**, so it cannot be used for development.

## 7. Exact minimum paid-data request (NOT requested for download; for owner decision after ~$0.01 cost discovery)

- **Files:** `s3://hydromancer-reservoir/by_dex/xyz/fills/perp/all/date=YYYY-MM-DD/fills.parquet`, for **2025-10-13 → 2026-03-31 (170 daily files)**.
  - Discovery: 2025-10-13 → 2025-12-31.
  - Validation: 2026-01-01 → 2026-03-31.
- **Rows:** `coin == 'xyz:XYZ100'` only. SP500 listed ~2026-03-18 and is out of this minimum.
- **Fields (13 of 27):** `timestamp, coin, side, price, size, address, crossed, direction, start_position, twap_id, is_liquidation, builder, trade_id`.
- **CME side:** owned Databento MNQ 1 m to 2026-06-30 [A]. No purchase needed.
- **Estimated bytes [I]:** whole files 27–66 GB → **$3.1–7.6** at $0.114/GB (upper bound; the earlier xyz dex was smaller).
  - If Parquet row groups and column chunks are selectable (the discovery footer tells): ~0.3–1.6 GB → **$0.04–0.19**.
  - Plus GET requests of order $0.01.
- **What it decides:** H2 for XYZ100 → MNQ at the validation gate. A validation fail kills H2 without SP500 data or the prospective final.
- **Precondition:** run `workspace/external_intel_2026-09-23/reservoir_cost_discovery.py` scoped to these 170 partitions (≈$0.01), then quote exact bytes to the owner.

## 8. H2 verdict: **BLOCKED**

- It is not killed: identity-level information is untested.
- It is strongly disfavoured:
  - HL follows NQ at the tick level on 10/10 development days.
  - Aggregate causal flow adds ≤0 while a leaked-flow control is detectable.
- The only remaining path is the paid minimum subset (§7), then the prospective final.

## 9. Top new contradictory evidence

1. HL xyz index perps **follow** CME NQ by 200–800 ms (10/10 days). HL→NQ OOS R² ≈ 0. Aggregate causal flow ΔR² ≤ 0 while a leaked control shows +1.8–4.9 pp.
2. Lane A W1: **62% of raw PnL comes from exits into pools with no swaps within ±5 min**. Under a realizable-exit condition, the mean excluding the top 10 is negative (−1.25% to −1.6%).
3. Lane A's "median entry drift 0" hides |drift| of 4.3% median / 25.8% p90 at 60 s. "Latency-insensitive" holds in expectation only.
4. `FOMO_PROSPECTIVE_PREREGISTRATION.md`, cited as W1's forward test, does not exist.

## 10. Next single action

With owner approval only: run the ≈$0.01 Reservoir LIST + Parquet-footer discovery, restricted to the 170 `by_dex/xyz/fills/perp/all` partitions (2025-10-13 → 2026-03-31). Then report exact bytes and whether XYZ100 rows are range-selectable. **No historical pull.**

## Artifacts (this folder)

- `audit_fomo_lane.py/.json`
- `chain_recount.py/.csv`
- `top_winner_realizability.py/.csv`
- `w1_pool_activity.csv`
- `h2_zero_cost_leadlag.py/.json`
- `h2_aggregate_flow_control.py/.json` (heavy baseline, superseded by the power check for inference)
- `h2_power_check.py/.json`

## CORRECTION (2026-09-23, Lane B / Agent 2)
The claim above that `FOMO_PROSPECTIVE_PREREGISTRATION.md` "does not exist" is **WRONG as of report time**. It was a
timing error, not a path/worktree issue: Lane B's `ls` ran ~04:35 UTC; the file was frozen 04:38:50 UTC
(mtime 08:38:48 +04:00, `.sha256` 08:38:50); this report was written 04:50 UTC without re-checking.
Verified now: SHA-256 `902263424c170fb7920c0a0880f056a8c7cc1b80e9a8dd5f2708a883c72fbc39` matches the `.sha256` file.
§1 Survivorship row and §9 item 4 are superseded by this note.
