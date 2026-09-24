# HEIMDALL — External Alpha Intelligence, Checkpoint 2 (2026-09-23)

**STATUS: CHECKPOINT — ALL ZERO-COST WORK DONE; AWS COST DISCOVERY PREPARED, NOT EXECUTED.**
No paid object has been downloaded and no AWS call has been made.

This document continues `EXTERNAL_ALPHA_INTELLIGENCE_2026-09-23.md`.

**Labels:**
- [V] verified this session by command or fetch.
- [I] inferred from [V].
- [U] unverified.
- [A] from an existing repo artifact.

**Where things live:**
- Scripts and results: `workspace/external_intel_2026-09-23/`.
- New tools: `tools/hl_trade_recorder.py`, `tools/feed_latency_probe.py`, `tools/hl_tape_audit.py`.
- Tests: `tests/test_hl_trade_recorder.py`.

## 1. Free Tardis replication (E3)

**Scope:**
- 23 free first-of-month days, 2024-11-01 → 2026-09-01. This is every day with Hyperliquid (HL) coverage; HL files return 400 before 2024-11.
- Coins: BTC, ETH, SOL.
- Sources: trades and quotes on both venues. 138 of 138 cells were available [V].
- Estimators:
  - A 100 ms-grid cross-correlation.
  - A **Hayashi–Yoshida (HY)** asynchronous tick estimator, added because HL prints ~10× fewer trades. Forward-filled grids bias the sparser series toward looking late.

**Best lag, in ms. Positive = Binance leads. EVENT time (exchange timestamps):**

| Estimator | Coin | Median | IQR | Min–max | Days Binance leads | Median best ρ/corr |
|---|---|---|---|---|---|---|
| HY trades | BTC | 600 | 500–650 | 400–1100 | 23/23 | 0.134 |
| HY trades | ETH | 550 | 500–600 | 400–900 | 23/23 | 0.273 |
| HY trades | SOL | 700 | 650–750 | 400–1050 | 23/23 | 0.395 |
| grid trades | BTC / ETH / SOL | 900 / 900 / 900 | 700–1000 | 300–1100 | 23/23 each | 0.13 / 0.13 / 0.09 |
| grid quotes | BTC / ETH / SOL | 1200 / 1100 / 900 | 700–1300 | 600–3000 | 23/23 each | ~0.11 |

**HY event lag by period (median):**

| Period | BTC | ETH | SOL |
|---|---|---|---|
| 2024-11 → 2025-06 | 625 | 550 | 700 |
| 2025-07 → 2026-02 | 675 | 600 | 700 |
| 2026-03 → 2026-09 | 500 | 500 | 700 |

**Readings:**
- There is **no sign failure in any regime.** HL-leads correlation mass never exceeded Binance-leads mass (0 of 69 days).
- The grid overstates the lag by about 300 ms (sparsity bias).
- Grid-quotes overstates it further. Tardis builds HL quotes from throttled book snapshots, and uses `fastBook` from 2026-06-17 (Tardis changelog) [I].
- **HY is the estimate of record.**
- HY ρ exceeds 1 on some 2024–25 days (thin HL). HY is unnormalized-bounded, so only lag *locations* are interpreted.
- Per-day table: `leadlag_per_day.csv`. Raw: `tardis_leadlag_results.json`, `tardis_hy_results.json`.

**Economics** (7 days, 2026-03 → 2026-09, event time):
- Trigger: the top 0.5% of Binance 200 ms moves (about 30,000 events per coin).
- HL's signed catch-up still available **between +300 ms and +1,500 ms** (the earliest window this host could plausibly act in):

  | Coin | Mean | Median | p90 |
  |---|---|---|---|
  | BTC | 1.95 bps | 1.44 | 4.67 |
  | ETH | 2.37 bps | 1.62 | 6.11 |
  | SOL | 2.37 bps | 1.57 | 6.42 |

- An HL taker round trip costs **9.0 bps** plus spread.
- **Verdict: Binance→HL lead-lag trading is KILLED for Heimdall.** It survives only as an execution filter (H5).

## 2. Event time vs receive time

- **Receive-time** best lag (HY) is **250–300 ms longer** than event-time at the median:

  | Coin | Receive-time median | Range |
  |---|---|---|
  | BTC | 850 ms | 500–1500 |
  | ETH | 850 ms | 450–1150 |
  | SOL | 950 ms | 450–1300 |

- That excess equals the HL public-feed delivery delay. The Tardis collector's HL p50 is 168 / 287 / 238 ms by period; Binance p50 is ≈3 ms.
- The extra receive-time lag is therefore **transport**.
- **The event-time lead is not transport.** It exists in exchange timestamps, is 400–1,100 ms, and survives the asynchronous estimator. It is **venue-level price discovery latency**: HL prices incorporate Binance information about 0.5–0.7 s later.
- **Unresolved:** how much of that 0.5–0.7 s is HL order-submission → block-timestamp mechanics versus slower market makers. HL's block-timestamp semantics were not verified [U].
- Either way, it cannot be captured net of taker fees (§1).

## 3. Live host latency (this machine, 65 minutes, 2026-09-23)

**Clock methodology:**
- SNTP (RFC 4330 client) to time.google.com, time.cloudflare.com and pool.ntp.org every 5 minutes, 3 queries each: **87 good samples**.
- Offset = median of the lowest-RTT third.
- **This host's clock is 14.97 s FAST** (all samples −14.955 to −14.986 s; RTT median 77 ms).
- Later recorder samples show **−15.95 s**, a drift of ≈140 ms/hour. Windows time sync is not disciplining this clock.
- Every raw-clock latency previously measured on this host is wrong by ~15 s. RTT-based measurements (e.g., PD §2) are unaffected.
- Latencies below are **offset-corrected**. Residual uncertainty ≈ ±RTT/2 of the best samples (~15–25 ms).

| Feed | n | p50 | p90 | p99 |
|---|---|---|---|---|
| Binance USD-M aggTrade, event E → receipt (BTC) | 22,295 | 78.7 ms | 84.6 | 221.6 |
| Binance aggTrade, match T → receipt (BTC) | — | 83.2 | 229.2 | 234.8 |
| Binance (ETH / SOL, E → receipt) | 19,603 / 9,560 | 78.7 / 78.4 | 84.4 / 81.4 | 213.2 / 115.4 |
| Hyperliquid trades, block time → receipt (BTC) | 6,217 | 315.1 ms | 484.7 | 750.6 |
| Hyperliquid (ETH / SOL) | 3,237 / 2,145 | 321.3 / 314.0 | 609.8 / 520.0 | 725.6 / 678.7 |

- Zero disconnects.
- **Endpoint correction [V]:** Binance futures `aggTrade` now streams only from `wss://fstream.binance.com/market/...`. The legacy `/ws` and `/stream` paths connect but deliver nothing.
- Binance SOL aggTrade `E` trails `T` by about 150 ms at the median (T→receipt p50 222.7 ms vs E→receipt 78.4).
- Raw: `data/latency_probe/run_2026-09-23/` (`msgs.csv`, `ntp.csv`, `summary.json`).
- **Not measured:** order round trip to HL (no order path exists; none built).

## 4. Prospective recorder

- `tools/hl_trade_recorder.py`, **read-only**. It uses only the public WS `trades` channel. No keys, no signing, no `/exchange` path; a test asserts this.
- **Recorded fields:** `ex_ms`, `recv_ns`, `coin`, `side`, `px`, `sz` (exact strings), `tid`, `hash`, `buyer`, `seller`, and `snap` (subscribe snapshot, excluded from latency).
- **Storage:** append-only hourly JSONL `data/hl_tape/trades/YYYY-MM-DD/HH.jsonl`, deduplicated on (coin, tid), fsync every 1 s.
- **Event log:** `data/hl_tape/events/YYYY-MM-DD.jsonl` records connect, subscribe, disconnect, reject, and an **SNTP clock offset every 10 minutes**, so `recv_ns` can be corrected offline.
- **Markets:** BTC, ETH, SOL (H1 subset); xyz:SP500, xyz:XYZ100 (H2); xyz:CL, xyz:GOLD (Lucid CL/GC analogs).
- **Running** as detached PID in `data/hl_tape_recorder.pid`, since 2026-09-23.
- **Completeness audit** (`tools/hl_tape_audit.py`, against HL 1-minute candle `n` over the same minutes) [V]:

  | Market | Recorded / candle_n |
  |---|---|
  | BTC | 5020 / 5022 |
  | ETH | 3180 / 3180 |
  | SOL | 1322 / 1323 |
  | xyz:SP500 | 805 / 805 |
  | xyz:XYZ100 | 799 / 799 |
  | xyz:CL | 1096 / 1096 |
  | xyz:GOLD | 110 / 110 |

  Ratio 0.9992–1.0000.
- **Caveats:**
  - The process is a user process. It **does not survive a reboot or logoff**; there is no service or scheduled task (owner decision).
  - Candle `n` only covers ~3.5 days, so run the audit at least every 3 days.
  - Disk use is ≈4 MB/hour at quiet hours [V]. Expect roughly 0.2–0.5 GB/day [I].

## 5. H2 causal test design (pre-registration draft; not run — no historical xyz fills yet)

**Question:** do identified HL wallets' signed flows in `xyz:SP500` / `xyz:XYZ100` add **out-of-sample** predictive information for **future MES / MNQ returns**, beyond current and recent CME prices and HL prices?

The oracle follows CME (trade.xyz docs), so the null is "HL follows CME".

**Data:**
- Reservoir `by_dex/xyz/fills/perp/all` (SP500, XYZ100 rows only).
- CME: Databento 1m MES/MNQ/ES to 2026-06-30 [A], plus Sierra 1m archive (~2026-06-23 → 2026-09-21) [A], spliced with a pre-declared overlap check.
- Prospective recorder data from 2026-09-23 as a **second final set**.

**Sample:** CME-open minutes only. Excluded:
- 17:00–18:00 ET and weekends (the xyz oracle is internal EMA then);
- ±2 minutes around 08:30 and 14:00 ET scheduled releases.

**Timing:**
- Features at the close of minute *t*.
- Entry at the **open of *t*+1**.
- Target r(*t*+1 open → *t*+1+*h*), *h* ∈ {1, 5, 15} minutes.

**Periods:**

| Instrument pair | Discovery (score wallets, fit M0/M1) | Validation (select) | Final untouched |
|---|---|---|---|
| xyz:XYZ100 → MNQ | 2025-10-13 → 2026-01-31 | 2026-02-01 → 2026-04-30 | 2026-05-01 → 2026-09-22, then prospective |
| xyz:SP500 → MES | 2026-03-18 [I listing date from first funding record] → 2026-05-15 | 2026-05-16 → 2026-06-30 | 2026-07-01 → 2026-09-22, then prospective |

**Baseline M0** (current CME price information):
- CME returns over the last 1, 2–5, 15 and 60 minutes.
- HL perp returns over the same windows.
- HL–CME basis (perp mid minus CME last, minus its trailing 1-day median).
- Aggregate HL signed taker flow from **all** wallets.
- Trailing 30-minute realized volatility.
- 30-minute time-of-day dummies.
- Rolling 60-minute beta of the HL perp on CME.

The key control is aggregate flow: identity must add beyond *total* flow.

**Treatment M1** = M0 plus signed taker flow, normalized by 20-day ADV, over the last 1 / 5 / 15 minutes, from:
- the **informed cohort**;
- the **anti-informed cohort**.

**Wallet scoring (discovery only):**
1. Fit M0 on discovery.
2. For each taker fill, take the M0 residual of the forward CME return (*h* = 5).
3. Wallet score = notional-weighted mean residual × trade sign, reported as an empirical-Bayes-shrunk t-stat.
- **Minimum sample:** ≥200 taker fills, ≥20 active days, ≥$250k notional in discovery.
- **Cohorts:** top decile = informed, bottom decile = anti-informed. Each must have ≥30 wallets, otherwise the test is **unpowered → STOP**, not loosen.
- **Clustering:** entity = wallets with ≥90% same-second co-trading overlap, merged before scoring. Inference uses day-clustered errors and a day-block bootstrap (1,000 draws).
- **Placebo:** 200 cohorts matched on discovery notional × fill-count deciles. The informed cohort must beat the placebo 95th percentile.

**Tests:**
- Primary: out-of-sample ΔR²(M1 − M0) > 0 on validation, with a day-block-bootstrap p-value.
- Family: 2 instruments × 3 horizons × 2 cohorts = **12 tests**, corrected with **Holm–Bonferroni α = 0.05**.
- Exactly one pre-declared survivor (default: *h* = 5, informed) goes to the final untouched set as a single one-sided test at α = 0.05.
- The DSR uses nb_trials = 12, only after the D1 units fix.

**Economic rule** (fixed in discovery):
- Trade when |cohort flow z| exceeds its discovery 99th percentile.
- One contract, in the flow direction, entry at the *t*+1 open, exit at *h*.
- Costs per repo conventions:

  | Contract | Commission (RT) | Slippage | Total per trade |
  |---|---|---|---|
  | MNQ | $1.00 | 1 adverse tick in + 1 out ($0.50 each) | **$2.00 = 4 ticks** |
  | MES | $1.00 | 2 ticks × $1.25 | **$3.50** |

**PASS (final set) requires all of:**
- mean net ≥ **+1 tick** per trade ($0.50 MNQ / $1.25 MES);
- 95% CI lower bound > 0;
- n ≥ 100 trades;
- positive in ≥3 of 4 time buckets.

**KILL on any of:** ΔR² ≤ 0; cohort ≤ placebo p95; net < 1 tick. No tuning after results.

## 6. H1 maker economics design

**Per-quote expected PnL:**

E[PnL] = P(fill) × [ half-spread capture + rebate − maker fee − adverse selection(*h*) − hedge cost ] − inventory carry/risk − queue / missed-fill opportunity cost

**Verified inputs:**
- Gatto 2026 (`DaruFinance/crypto-adverse-selection`, MIT, pushed 2026-09-21): last-in-queue touch quoter on HL, 10 s, pre-fee.
  - Capture **+0.560 bp**, adverse **−1.017 bp**, net **−0.458 bp** (95% CI [−0.729, −0.186]).
  - Re-quote at 2 s removes 32.7% of the adverse leg. At the widest rung the net is still −0.040 bp.
- Albers, Cucuringu, Howison & Shestopaloff (arXiv 2502.18625v2):
  - Fill probability is inversely related to post-fill return (~90% fills when the next 5 s return is negative vs ~30% when positive).
  - Back-of-queue 1 s markout −0.78 bp vs front −0.06 bp.
  - Naive touch MM annualized Sharpe −109.
- HL fees [V]: base maker **+1.5 bp**; staking discount ≤40% → 0.9 bp; 0 bp only above $500M per 14 days (Tier 4).

**Analytic bound:** even a *perfect* identity filter (adverse = 0) nets 0.560 − 0.9 = **−0.34 bp per fill** at our best reachable fee. That is before inventory, hedging and queue costs.

**Use-case verdicts:**

| Use | Verdict |
|---|---|
| **Quote skew** | NONE for Heimdall |
| **Do-not-quote filter** | NONE for Heimdall (only relevant to a Tier 4+ maker, not our scale) |
| **Directional** | The only remaining use. Needs a minute-horizon top-cohort markout > ~10 bp (9 bp taker round trip + spread) in a period later than discovery. Zhai's 3.11 bp at 10 s must *grow* ≥3× with horizon. Low prior; one cheap test on the bounded H1 subset (markouts at 1/5/15/60 minutes; same persistence/placebo machinery as H2). |
| **Overall** | Maker = NONE; directional = test once, expect kill. |

## 7. New institutional / academic findings

**Maker adverse selection:**
- **Gatto 2026** (above). A practitioner-grade replication kit; the numbers were verified in the repo README.
- **Albers et al. 2026 (Oxford)** (above). The same group built the L4 HL dataset (SSRN 6465720).
- **Ochędzan & Antulov-Fantulin, 2606.05882:** a trade-off between adverse selection and price discovery for MM profitability. Only the abstract was extracted; no numbers.

**Metaorder completion (H3 prior):**
- Fair-pricing theory and evidence (Farmer, Gerig, Lillo & Waelbroeck; Bucci et al.): permanent impact ≈ **2/3 of peak**, so post-completion reversion ≈ **1/3 of peak impact**.
- **Naviglio et al. (arXiv 2501.17096):** metaorders reconstructed from public data show near-linear impact and "very limited" reversion.
- Barone & Lillo's HL gap between visible and hidden permanent impact is only 3–5 bps.
- **H3 prior downgraded:** reversion is likely < the 9–12 bp taker cost except for the largest TWAPs.

**Liquidation recovery:**
- No peer-reviewed post-liquidation reversal magnitudes were found for 2024–26.
- Evidence is event anatomy only: Oct-10-2025 spreads averaged 5.92 bps during the cascade (≈30× normal); mark undershoot fed the loop.
- Garcia Seuma: subcritical, no early warning.
- H4 stays a measurement study.

**Cross-venue lead-lag:** no new academic source beyond Zhai and the Arrakis thread. Our own 69-cell HY replication (§1) is now the strongest evidence in hand.

**HL market-maker economics:** HLP ~22% net APR TTM (secondary sources, [U]); 55–65% of it from spread capture, 15–20% from liquidations. That is consistent with the protocol-level maker capturing the retail loss.

**Access notes:**
- SSRN / X / some PDFs still returned 402/403.
- Dwellir's historical-data page timed out (not verified).
- No Man / AQR / Citadel publication added a testable mechanism. That lane is exhausted at reasonable effort.

## 8. AWS cost-discovery plan (prepared; NOT executed)

**Verified prices** (AWS price list API, ap-northeast-1, published 2026-09-16/18):

| Item | Price |
|---|---|
| Transfer out to internet, first 10 TB/month | **$0.114/GB** |
| LIST | **$0.0047 per 1,000** |
| GET | **$0.0037 per 10,000** |

**Access facts:**
- `hydromancer-reservoir` and `artemis-hyperliquid-data` are both requester-pays; anonymous LIST returns `AccessDenied` [V].
- The AWS CLI `list-objects-v2` supports `--request-payer requester` and returns `Size` [V docs].
- DuckDB httpfs has **no documented requester-pays header support** (duckdb discussion #17770), and issue #172 reports request explosions. This conflicts with Hydromancer's DuckDB quick-start → **UNRESOLVED; do not use DuckDB against these buckets.**

**Script:** `workspace/external_intel_2026-09-23/reservoir_cost_discovery.py` (boto3). It does:
- (1) `ListObjectsV2` on exactly the date partitions each experiment needs;
- (2) for ≤3 files per dataset, **two ranged GETs** reading only the Parquet footer (≤1 MiB), to learn row-group coin statistics, i.e., whether BTC/ETH/SOL or SP500/XYZ100 rows can be fetched without whole files.

Footer parsing was verified offline on a local Parquet file. It never downloads a whole object.

Equivalent CLI for manual inspection:
```
aws s3api list-objects-v2 --bucket hydromancer-reservoir --request-payer requester \
  --prefix by_dex/xyz/fills/perp/all/date=2026-03-18/ --query "Contents[].{K:Key,S:Size}"
aws s3api get-object --bucket hydromancer-reservoir --request-payer requester \
  --key <key> --range bytes=-8 tail.bin        # footer length + magic only
```

**Requests needed:** about 978 LIST calls (28 + 345 + 183 + 422 partitions) ≈ **$0.005**, plus ≤24 footer GETs ≈ $0.00001, plus ≤24 MiB egress ≈ $0.003. **Total discovery ≈ $0.01.**

## 9. Data volume by experiment (INFERRED; to be replaced by the LIST output)

**Basis [V]:**
- HL 1-day candle trade counts, last 30 days (median): main dex **3.43M** trades/day, xyz **1.63M**.
- BTC 343k, ETH 163k, SOL 91k; SP500 43.6k; XYZ100 39.0k.
- Candle `n` = trade count (matches Tardis within 0.02%).

**Assumptions:**
- Reservoir rows = 2 per trade (one per side) [I from the per-address schema].
- Compressed bytes/row **50–120 [U]**.
- Recent activity is used for all dates, so figures are **upper-bound-ish**.

| Exp | Scope (narrowest) | Full daily files | If coin row-groups are selectable |
|---|---|---|---|
| H1 | main dex `fills/perp/all`, 4 windows × 7 days (2025-08, 2025-11, 2026-03, 2026-08); BTC/ETH/SOL only | 9.6–23 GB → $1.10–2.63 | 17.4% → 1.7–4.0 GB → $0.19–0.46 |
| H2 | `by_dex/xyz/fills/perp/all`, 2025-10-13 → 2026-09-22 (345 days); SP500 + XYZ100 only | 56–135 GB → $6.4–15.4 | 5.1% → 2.9–6.9 GB → $0.33–0.79 |
| H3 | `fills/perp/twap_fills`, 2026-03-24 → 2026-09-22 (subset file) + price path capped at 30 days of 1 s candles [U size] | 0.6–7.5 GB + 6–24 GB → $0.8–3.6 | — |
| H4 | `fills/perp/liquidations`, full history (subset file) + price path capped at 30 cascade days | 0.1–2.5 GB + 6–24 GB → $0.7–3.0 | — |
| **All** | | **≈ 72–216 GB → ≈ $9–25** | **≈ 11–60 GB → ≈ $1.3–7** |

AWS's 100 GB/month free outbound tier might apply to requester-pays egress on the requester's account [U]. H2 alone is enough to decide the only Lucid-reachable hypothesis.

## 10. Updated top 5

1. **H2:** HL CME-analog wallet flow → MES/MNQ, 1–15 minutes. Unchanged. Only Lucid-reachable; causal design ready (§5). The strongest evidence against it: oracle anchored to CME, plus the relayer's ~3 s / ±1% cadence. HL follows CME by construction during CME hours [V docs, HIP-3].
2. **H4:** HL liquidation-cluster recovery path. Measurement only; small data.
3. **H3:** post-visible-TWAP decay. **Downgraded** by fair-pricing theory (1/3 reversion) and Naviglio (limited reversion). Better event definitions now exist: Artemis `Node TWAP Statuses` gives start/size/side [V docs].
4. **H1:** directional wallet identity at minute horizons. **Maker/skew/filter uses KILLED** at our fee tier (§6).
5. **H5:** Binance-lead execution filter. **Verified** lead (69/69 cells; HY median 500–700 ms in 2026) but only ≈2 bps capturable, so it is execution hygiene, not alpha.

**Killed this checkpoint:**
- **X8** Binance→HL latency arbitrage (≈2 bps available vs 9 bps cost).
- **X9** identity-based quoting at base or staking fee tiers (analytic bound −0.34 bp/fill with a perfect filter).

## 11. Search saturation (pass 3 of the protocol, repeated)

1. **New data sources:**
   - **Artemis** open S3 (`artemis-hyperliquid-data/raw/`, requester-pays, from 2025-08-17): fills, **all order statuses (~54 GB/day)**, **TWAP statuses**, daily balances [V docs + anonymous probe].
   - **Dune:** HL tables are enterprise/trial-gated [V docs].
   - **Allium:** free tier of 20,000 credits; claims full order history [U coverage/cost].
   - None displaces the top 5. Artemis TWAP statuses improve H3. Allium could be a no-AWS path for H2 if its free tier covers xyz fills [U, cheap to check].
2. **Unconsidered mechanisms:**
   - HIP-3 relayer cadence ~3 s with ±1% cap per update, and stale-mark fallback after 10 s. This can create stale **mark** prices (liquidation/funding timing), not stale trade prices.
   - Hourly funding settlement: no evidence of a price pattern found.
   - Neither is a credible top-5 challenger.
3. **Market-maker view:** the maker-markout literature (Gatto, Albers) closes quoting for us. An MM would next look at queue position and re-quote latency. That needs a colocated node, outside Heimdall's constraints.

**No credible new top-5 challenger appeared.** STATUS remains CHECKPOINT only because H1–H4 need data that is not free.

## 12. Recommended next action

1. **Owner approval for AWS cost discovery only** (≈$0.01 of requests; §8): create an AWS IAM user with read-only S3 on requester-pays and run `reservoir_cost_discovery.py`. Then decide H2's pull with real byte counts. H2 selectable ≈ $0.3–0.8; full-file ≈ $6–15.
2. **Keep the recorder running.** Make it survive reboot (a scheduled task) if you want it permanent.
3. **Fix this host's clock**: enable Windows Time sync (`w32tm /resync` after configuring NTP peers; needs admin). The clock is 15.95 s fast and drifting ~140 ms/hour.
4. **Optional $0 check:** does Allium's free tier include xyz fills history (H2 without AWS)?

## 13. Evidence receipts

**Scripts:**
- `workspace/external_intel_2026-09-23/tardis_leadlag_all.py`
- `tardis_hy_leadlag.py`
- `reservoir_cost_discovery.py`
- `reconcile_indexers.py`
- `leadlag_tardis.py`
- `tools/feed_latency_probe.py`, `tools/hl_trade_recorder.py`, `tools/hl_tape_audit.py`

**Results:**
- `tardis_leadlag_results.json` (138 cells), `tardis_hy_results.json` (69 cells), `leadlag_per_day.csv`, `raw/hl_daily_trade_counts_1d.json`
- `data/latency_probe/run_2026-09-23/summary.json`
- `data/hl_tape/audit_latest.json`

**Commands observed:**
- Anonymous LIST on `artemis-hyperliquid-data` and `hydromancer-reservoir`: "Anonymous users cannot invoke requests against Requester Pays buckets."
- Binance `wss://fstream.binance.com/ws/btcusdt@aggTrade`: recv timeout. `/market/ws/...`: data.
- Tests: `pytest tests/test_hl_trade_recorder.py` 12 passed; full suite 209 passed / 2 failed (known OKX live tests) / 1 skipped.
- `tools/check_core_purity.py`: OK.

**URLs:**
- https://datasets.tardis.dev/v1/{hyperliquid,binance-futures}/{trades,quotes}/YYYY/MM/01/…
- https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/{AmazonS3,AWSDataTransfer}/current/ap-northeast-1/index.json
- https://docs.aws.amazon.com/cli/latest/reference/s3api/list-objects-v2.html
- https://github.com/duckdb/duckdb/discussions/17770
- https://github.com/duckdb/duckdb-httpfs/issues/172
- https://www.artemis.ai/docs/snowflake-share/tables/hyperliquid
- https://docs.dune.com/data-catalog/community/hyperliquid/overview
- https://www.allium.so/ecosystems/hyperliquid
- https://github.com/DaruFinance/crypto-adverse-selection
- https://arxiv.org/html/2502.18625v2
- https://arxiv.org/pdf/2606.05882
- https://ideas.repec.org/p/arx/papers/2501.17096.html
- https://ar5iv.labs.arxiv.org/html/1901.05332
- https://arxiv.org/pdf/1802.08502
- https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-3-builder-deployed-perpetuals
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/hip-3-deployer-actions
- https://www.coingecko.com/learn/hyperliquid-hlp-vault-analysis
- https://blog.amberdata.io/how-3.21b-vanished-in-60-seconds-october-2025-crypto-crash-explained-through-7-charts
