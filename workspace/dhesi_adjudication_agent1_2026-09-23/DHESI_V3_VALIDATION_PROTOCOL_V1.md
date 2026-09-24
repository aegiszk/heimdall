# DHESI V3 — ONE-SHOT UNTOUCHED-HISTORY VALIDATION PROTOCOL V1

- Frozen: 2026-09-23 by Agent 1. No untouched market data was read before or while writing this document.
- Hypothesis: `DHESI_V3_CANONICAL_SPEC_V1.md` (hash in `DHESI_V3_CANONICAL_SPEC_V1.sha256`), run **unchanged**.
- Executor: `dhesi_v3_validator.py`. Its hash is recorded in `AUTHORIZATION_REQUEST_DHESI_V3.md`, and it refuses to run without owner authorization (§4).
- This protocol does **not** authorize the run. Only the owner can, by creating `DHESI_V3_RUN_AUTHORIZATION.txt`.

## 1. Question and axes

**Primary question (ALPHA axis):** does the unchanged canonical Dhesi v3 have positive after-cost expectancy at or above the frozen minimum useful edge (§5) on untouched NQ history?

**PROP axis (separate, report-only):** Lucid 50K FLEX Monte Carlo pass rate of the realised trade stream. It never changes the ALPHA verdict, and the ALPHA verdict never changes it.

## 2. Data: range, series, contamination boundary

### 2.1 What exists, from Sierra documentation only (no prices read) [V, fetched 2026-09-23]

- `SierraChartHistoricalData.php`: CME futures data "in 1 minute units … begins at June 2008"; tick data "begins at 2011".
- `ContinuousFuturesContractCharts.html`: intraday charts load at most **15 years** back. Volume-based rollover is supported, and back-adjust can be set to None. Historical data for the expired contracts is required and is supplied by Sierra's own service.

### 2.2 Contamination boundary [V, `data/trials_ledger.json` and file inventory]

Heimdall's first CME equity-index data starts **2024-07-01** (Databento `data/{MNQ,MES,ES}_1m.parquet`). The FirstRate vendor samples are 2026-06/07, and all Sierra files are 2026. Nothing before 2024-07-01 has been read by any Heimdall experiment.

### 2.3 Frozen primary window

| Item | Value |
|---|---|
| Series | **NQ continuous**: Sierra "Continuous Futures Contract – Volume Based Rollover", back-adjust None, 1-minute, UTC chart time zone, bar-start stamps |
| First row | whatever the earliest 1-minute row Sierra delivers on the continuous chart is. Expected ≈ **2011-09** (15-year intraday limit counted from the harvest date). Harvest promptly: every day of delay loses a day at the start. |
| Evaluated sessions | from the 21st RTH session of the delivered series (spec T7 burn-in) through **2024-06-28** inclusive |
| Hard cut | every row with ET time ≥ **2024-06-29 00:00** is dropped by the validator **before any computation** |
| Expected untouched span | ≈ **12.75 years** (≈ 2011-09-23 → 2024-06-28) [U until harvest metadata] |
| Excluded | 2008-06 → 2011-09 (outside Sierra's continuous-chart range). Adding it would need a Heimdall-built roll stitch of expired contracts, a new, untested degree of freedom. Decided now, before any outcome. |
| MNQ price data | not used as evidence (one family). MNQ economics are applied to NQ prices (spec M2). |

### 2.4 Harvest and integrity (allowed before authorization; NO outcomes)

**Allowed:**
- set up and export the chart;
- file SHA-256, row count, first/last timestamp, duplicate count, NaN count;
- per-session RTH row counts and missing-minute share;
- the list of contract months / roll dates reported by Sierra;
- the file size.

**Forbidden until authorization and the run:**
- any price, return, range, volatility or volume summary, and any chart of the window;
- any FVG, sweep or strategy computation;
- any look at the 2011–2024 bars.

Integrity gates (all must pass, or the run is **BLOCKED**, not amended):
1. 0 duplicate timestamps and 0 NaN OHLC cells.
2. At least 95% of evaluated sessions have ≥ 370 of their RTH minute rows (09:30–16:00 has 391).
3. **Series-equivalence check** on already-contaminated data: harvest the same chart through 2024-09-30. For 2024-07-01 → 2024-09-30, compare NQ close vs `data/MNQ_1m.parquet` close. \|diff\| ≤ 2.0 points on ≥ 95% of shared minutes. Roll-day minutes (±1 session of any Sierra roll date) are excluded. This window is DEVELOPMENT/REUSED already, so reading it adds no contamination. The validator's hard cut then removes it from the run.
4. Record gate outputs in `DHESI_V3_HARVEST_INTEGRITY.json` (hashes, counts, roll dates) **before** authorization.

## 3. Costs and execution (frozen; identical to development)

- $1.00 round trip per MNQ contract, charged once on the full count.
- 1 adverse tick (0.25 pt) on entry, stop fills and session flatten; gap-through stops fill at the open.
- TP1 and runner fill at the level exactly.
- Same-bar stop and target: stop first.

**Stress repricing** (for P7): per trade, subtract contracts × (2 × 0.25 pt × $2 + $0.50) = contracts × $1.50. That is one extra adverse tick on entry, one on exit, and +50% commission.

## 4. Execution procedure (one shot)

1. Owner reviews `AUTHORIZATION_REQUEST_DHESI_V3.md` and `DHESI_V3_HARVEST_INTEGRITY.json`.
2. Owner creates `DHESI_V3_RUN_AUTHORIZATION.txt` in the repo root containing `AUTHORIZED_BY_OWNER`, the validator SHA-256, the spec SHA-256 and this protocol's SHA-256.
3. Register the ledger trial `NQ-dhesi-inversion-v3-untouched` (window 2011-09 → 2024-06-28, `window_status: FRESH`, n_configs 1) **before** running.
4. Run, from the repo root:
   `python workspace/dhesi_adjudication_agent1_2026-09-23/dhesi_v3_validator.py primary --nq <harvested NQ parquet>`
   The validator refuses if any frozen code hash differs, or if the authorization is missing or names a different validator.
5. The validator runs the **frozen code** (normative) and the independent reference engine. The verdict stands on the frozen code. Any frozen/reference disagreement must be itemised trade by trade in the report; it cannot change the verdict.
6. **Exactly one run.** A crash before a verdict is printed may be fixed only in non-strategy plumbing (I/O, paths). The diff is logged and the owner approves it. Once any result is printed, no rerun is allowed for any reason.
7. After the run, the window's ledger status becomes REUSED_HOLDOUT for all future work.

## 5. Minimum economically useful edge (frozen: **μ_min = $30 net per trade**, ≈ 0.11R)

Inputs (development, v3; used only for design) [V]:
- about 24.5 trades/yr;
- mean risk $269/trade (sized to the $325 cap);
- sd $290/trade (≈ 1.08R);
- mean 2.61 contracts;
- commission ≈ $2.61/trade; stress adds ≈ $3.92/trade.

| Criterion | Requirement | Implied μ |
|---|---|---|
| Standalone risk-adjusted value | annual information ratio ≥ 0.5 → μ ≥ 0.5 × σ / √f = 0.5 × 290 / √24.5 | **$29.3** |
| Covers fixed running costs | Sierra data $26/mo ($312/yr) + ~3 Lucid eval fees/yr at $99 ≈ $600/yr → 600 / 24.5 | $24.5 |
| Friction robustness | μ > 2 × stress cost | $7.8 |
| Drawdown tolerance (PROP, not ALPHA) | At μ = $30: annual EV ≈ $735 vs annual sd ≈ $1,435, so P(losing year) ≈ 30%. The $2,000 MLL is reachable in a bad year, so standalone prop use is marginal. | reported only |

μ_min = max(29.3, 24.5, 7.8), rounded up = **$30.00/trade**. The earlier $20 figure is not reused.

**PROP axis (report-only):** Lucid MC as in `tools/validate_inversion_v3.py`: 10,000 sims, seed 20260922, daily_buffer 325, ≤ 3 trades/day, empirical daily counts. Label:
- `PROP_STANDALONE_PASSABLE` if pass rate ≥ 3.96% (breakeven, CLAUDE.md);
- otherwise `PROP_PORTFOLIO_COMPONENT_ONLY`.

On the development stream this gives 0.22% (mechanics test), so standalone prop use is expected to fail regardless of alpha.

## 6. Statistics and decision rules (ALPHA axis)

- **Unit:** trade (net $). **Cluster:** ET session; same-session trades are summed together with their count.
- **Bootstrap:** stationary bootstrap over the chronological sequence of trade-sessions. Mean block length 5 trade-sessions, B = 20,000, seed 20260923. Statistic = Σ resampled session PnL / Σ resampled trade counts. `lo95` = 5th percentile, `hi95` = 95th percentile (one-sided 95% bounds).
- **Year:** calendar year of the session. "Qualifying year" = ≥ 5 trades.

**PASS** only if ALL of:

| # | Criterion |
|---|---|
| P1 | N ≥ 80 trades |
| P2 | net mean ≥ μ_min ($30) |
| P3 | lo95 > 0 |
| P4 | ≥ 6 qualifying years **and** net PnL > 0 in ≥ 2/3 of them |
| P5 | largest single trade ≤ 25% of total net PnL |
| P6 | worst calendar year net ≥ −$2,000 (one Lucid MLL) |
| P7 | stressed mean > 0 **and** stressed lo95 > 0 |

**FAIL**: hi95 < μ_min. The data contradict a useful edge at the one-sided 95% level. This is checked first and overrides everything else.

**INCONCLUSIVE**: everything else, including N < 80 without FAIL. A valid, expected outcome.

No other verdict word is used. Secondary markets, sub-periods, long/short splits and ablations are **descriptive only** and cannot change the primary verdict.

## 7. Power (normal approximation, σ = $290; PASS ≈ P(x̄ ≥ max(μ_min, 1.645·SE)); FAIL ≈ P(x̄ < μ_min − 1.645·SE))

The untouched span is ≈ 12.76 years. Trade frequency is uncertain because the 30-pt raw displacement is stricter at the lower NQ prices of 2011–2019 (spec §11), so three frequency scenarios are shown:

| Scenario | N | SE | true +$0 | +$20 | +$40 | +$60 | +$80 |
|---|---|---|---|---|---|---|---|
| 24.5/yr (dev rate) | 313 | $16.4 | PASS 0.03 / FAIL 0.57 | 0.27 / 0.15 | 0.73 / 0.01 | 0.97 / 0.00 | 1.00 / 0.00 |
| 12/yr | 153 | $23.4 | 0.05 / 0.36 | 0.21 / 0.11 | 0.52 / 0.02 | 0.82 / 0.00 | 0.96 / 0.00 |
| 6/yr | 77 | $33.0 | 0.05 / 0.23 | 0.15 / 0.09 | 0.33 / 0.03 | 0.57 / 0.01 | 0.78 / 0.00 |

Reading:
- Untouched history can reliably confirm only a **large** edge (≥ $60/trade at the central frequency).
- A true edge at μ_min passes about half the time at best.
- A true zero edge passes ≤ 5% of the time and is caught as FAIL only 23–57% of the time; otherwise it is INCONCLUSIVE.
- PASS figures are upper bounds, because P4–P7 are not modelled.
- If N < 80, the result is INCONCLUSIVE by design, i.e. structurally underpowered at this frequency.

## 8. Secondary replication (only if primary ≠ FAIL; never rescues or selects)

- **Markets:** ES (execution MES), RTY (M2K), YM (MYM). Series: same Sierra method and same untouched window, run with `secondary --market {ES,RTY,YM}`.
- **Scaling:** spec §12, frozen now.
  - Floor: friction ratio (MES 7.0 / M2K 4.0 / MYM 40.0 pts).
  - Displacement: 30 × prior-session close ratio to NQ.
  - Everything else unchanged.
  - The M2K/MYM commission must be verified live first (spec §12 [U]).
- Each market receives the §6 verdict independently. Reported jointly:
  - `REPLICATED` if ≥ 2 of 3 markets have net mean > 0 **and** none is FAIL;
  - otherwise `NOT_REPLICATED`.
- Secondary results are never pooled into the primary statistic. They cannot upgrade an INCONCLUSIVE primary to PASS and cannot turn a FAIL into anything else. No market is "selected".
- If the primary is FAIL, the secondary runs are **not performed**.
- Minis and micros are never counted twice.

## 9. Multiple testing and reporting

- Ledger family `dhesi_inversion`: prior trials v1 ×3, v2 ×3, v3 dev, v3 "fresh" (the last two are missing from the ledger and must be added by the ledger owner), and this forensic cycle. The untouched run is the family's first FRESH trial.
- Report, **descriptively only**: DSR with the ledger's empirical trial variance and trial count, the realised N, and achieved power at μ_min.
- The report must include:
  - the verdict word;
  - every P-check value;
  - the per-year table;
  - the top-5 trades and their share of PnL;
  - the frozen/reference agreement;
  - the stress results;
  - the PROP label;
  - the realised trades/yr versus the §7 scenarios.

## 10. Forbidden

- Changing any spec value, adding or removing filters, or re-running with another window, roll method, cost model or series.
- Reading untouched prices before authorization.
- Choosing among secondary markets.
- Reporting a sub-period as the result.
- Using this window again as "fresh".
- Creating `REOPEN_APPROVED` or the authorization file (owner only).
