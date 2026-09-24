# HEIMDALL — Validation / Backtest Trust Audit (2026-09-22)

Separate lane from Profit Discovery. No threshold, gate, simulator or strategy file was modified.
New files only: `tests/test_audit_pnl_oracle.py`, `tests/test_audit_stat_references.py`,
`tests/test_audit_invariants_prop.py`, `tools/audit_power_map.py`, `tools/audit_stat_behavior.py`,
`tools/audit_execution_intrabar.py`, `tools/audit_historical_review.py`, outputs in `data/validation_audit/`.

## STATUS: TRUSTED WITH LIMITATIONS

The validator reliably **rejects** no-edge and negative strategies (combined false-positive rate <= 4.8%
in every null cell). It **cannot confirm** realistic edges at Heimdall's sample sizes, and several
past "DEAD" labels are really "INCONCLUSIVE / UNDERPOWERED". One call convention (LuxAlgo/FVG validator)
cannot accept anything. The prop Monte Carlo verdict is a 1-contract sizing verdict, not an alpha verdict.

---

## 1. Validation architecture (raw -> verdict)

| Stage | Source |
|---|---|
| Raw data | Databento GLBX.MDP3 `data/{MNQ,MES,ES}_1m.parquet` (ts_event UTC, bar-open label, `*.v.0` volume roll, NOT back-adjusted); Sierra `.scid` -> `tools/sierra_scid_loader.py` -> `data/sierra/tick/*.parquet`; Sierra CSV -> `tools/sierra_csv_loader.py` |
| Normalization / sessions | `FuturesRTHModel._prepare_frame` (`core/alpha/prop_futures.py:95`): UTC -> America/New_York, `_session` = ET calendar date |
| Features / signal | per model: `core/alpha/research_candidates.py`, `inversion_model.py`, `okala8020.py`, `orderflow_*.py`, `intraday_momentum.py` |
| Entry / fill / exit / costs | shared: `FuturesRTHModel._simulate/_exit_price/_close_trade` (`prop_futures.py:130-238`); own sims in `inversion_model.py:889`, `orderflow_absorption.py:312`, `orderflow_footprint.py:165`, `okala8020.py`, `intraday_momentum.py:35` |
| Trade PnL | `pnl = side*(exit-entry)*point_value - commission_rt` (once per round turn) |
| Split | `tools/validate_*.py` chronological session split (60/40), 4 holdout buckets |
| Statistical gate | `core/validation/battery.py:run_gate` + `metrics.py`, thresholds `core/config.py:DEFAULT_GATE_CFG` |
| Prop simulator | `tools/prop_montecarlo.py:run_empirical_many` + `core/risk/prop_engine.py` |
| Verdict | human-written in `HEIMDALL_MEMORY.md` from validator JSON/stdout |

Gate call conventions in use: **A** `nb_trials=1, sr_trials_var=0.0` (inversion, okala, fabio, absorption,
swing, intraday_momentum); **B** `nb_trials=2, sr_trials_var=1.0` (`tools/validate_research_candidates.py:83`).
PBO: `candidate_matrix` is never passed by any validator -> PBO gate is always skipped (N/A).
`mc`: only computed when `positions`+`market_returns` are passed, and it is a sign-flip test on trade
returns (`battery.py:30`), not the timing permutation in `metrics.monte_carlo_permutation`.

## 2. Critical defects (proven)

| # | Defect | Evidence | Effect |
|---|---|---|---|
| D1 | Convention B deflates against SR0 = 0.52 **per trade** (`sr_trials_var=1.0` in per-trade Sharpe units; realistic cross-trial variance ~1/N_trades) | `test_convention_B_benchmark_is_implausibly_high`; power map: accept <= 5.2% in every cell, 0.0% for every shape at true SR 0.30 and N=500 | Structural auto-reject for LuxAlgo POC + Casper FVG gates. Verdicts unchanged (both had ~0 gross edge anyway). |
| D2 | Prop Monte Carlo is 1 contract, 80 days, iid resampled. "0% Lucid pass / 100% never_target" is a SIZING statement | `test_mc_one_lot_sizing_confounds_alpha_with_prop_verdict`: +$10/trade edge -> 0.0% at 1 lot, >50% at 5 lots | Every "Lucid MC 0%" line in memory is a prop-compatibility verdict at 1 lot, not evidence of no alpha. |
| D3 | LuxAlgo POC simulated on 5-minute parent bars with stop-first ordering although 1-minute data was owned | `execution_intrabar_2026-09-22.json`: 65/205 holdout stop exits had target inside the same 5m bar | Holdout mean -$5.20 is the worst-case bound; 1m/tick-resolved -$2.24; best bound +$2.08. Still no evidence of edge. |
| D4 | Dhesi InversionModel v2 takes the stop from the latest 15m swing without checking side | 5/30 MNQ trades have long-stop >= entry or short-stop <= entry, exit instantly as `gap_stop` (`inversion_model.py:836`); 1 of 13 holdout trades | Phantom small losses + they consume the one-entry-per-session slot. v3 (`inversion_model_v3.py:224`, `stop_guard`) already guards this. v2 numbers need a labelled rerun, not an overwrite. |

Not defects (verified correct): contract point values/commissions, stop/gap/flatten fills, commission-once,
no MC double-charge, PSR/DSR formulas, NW t (matches statsmodels HAC to 1e-9), chronological split, DST.

## 3. Positive / negative control results (V2)

`tools/audit_power_map.py`, 400 reps/cell, 8 shapes x 6 true edges x 7 sample sizes, production `run_gate`.
True edge = per-trade Sharpe (0.10 ~ 55% win at 1:1; 0.20 ~ 60% win at 1:1).

Convention A accept rate, coin 1:1 shape (other shapes similar; see JSON):

| true SR \ N | 10 | 20 | 30 | 50 | 100 | 200 | 500 |
|---|---|---|---|---|---|---|---|
| -0.10 | 0 | 0 | .007 | .005 | .003 | 0 | 0 |
| 0.00 (null) | 0 | 0 | .003 | .005 | .010 | .015 | .005 |
| +0.05 | 0 | 0 | .037 | .033 | .035 | .062 | .070 |
| +0.10 | 0 | 0 | .058 | .070 | .090 | .142 | .315 |
| +0.20 | 0 | 0 | .065 | .155 | .270 | .512 | .855 |
| +0.30 | 0 | 0 | .072 | .350 | .537 | .820 | .993 |

- False-positive rate: max 4.75% across all null cells (neg_skew, N=50). Negative controls <= 1.5%.
- Power is the binding problem: 50% power at SR 0.20 needs ~200 trades; at SR 0.10 it needs > 500.
- N < 30 -> accept 0 by construction (`min_trades`). Those are UNDERPOWERED, not DEAD.
- Failure attribution (SR 0.30, N=30): `wf_min` fails 90%, t-type gates ~55%. `wf_min` (every one of 5
  sub-period Sharpes > 0) is the most binding gate from N=30 to N=200.
- Convention B: ~0 at every edge and N (D1).

## 4. Data fidelity (V4)

- `MNQ_1m`: 707,185 rows, 0 duplicates, monotonic, 0 OHLC inconsistencies, 0 off-tick prices; 515 RTH
  sessions, 495 full 390-bar, 20 short = holidays/early closes; DST correct (July sessions 390 bars).
- Rolls: 8 unadjusted rolls, all at 00:00 UTC (19:00/20:00 ET, outside RTH), jumps +207.75 to +316.0 pts.
  Intraday-only strategies are unaffected; multi-day lookbacks (Dhesi HTF pools, swing) straddle roll gaps
  on ~8 sessions / 2 years. Low severity, unquantified.
- `_session` = ET calendar date, so 18:00-23:59 Globex bars sit in the prior date; `prior_close` in
  `FuturesRTHModel` is the 23:59 ET print, not the RTH close or settlement.
- Cross-source: Databento MNQ vs Sierra NQM26 ticks on 4 same-contract RTH days: median |close diff| 0.25 pt,
  max 1.0-3.5 pt, all 390 minutes present -> scale and timestamps align (MNQ and NQ are separate books; 1-tick
  divergence expected). 2026-03-10 differs ~218 pts = MNQ still on H26 vs NQM26.
- Resample `label="right", closed="right"` on bar-open labels (inversion, okala) shifts 5m/15m/1h/4h candles by
  one minute vs exchange-aligned candles. No lookahead (entry at the close of the last 1m bar in the bin), but
  candles differ from what the source trader sees. Fidelity issue, P2.
- Sierra tick/footprint reconciliation: already recorded in `data/sierra/MANIFEST.md` (not re-derived).

## 5. Execution model (V5)

Re-pricing frozen exits (paths unchanged, only fills):

| Strategy (holdout) | gross/trade | optimistic | base (Heimdall) | stress | tax/trade (base) |
|---|---|---|---|---|---|
| LuxAlgo POC (205) | -3.39 | -4.39 | -5.20 | -6.32 | 1.81 |
| Casper FVG (67) | +2.38 | +1.38 | +0.46 | -0.79 | 1.92 |
| VWAP reversion MES (610) | +0.22 | — | -2.94 | — | 3.16 |
| Time scalp MES (933) | +0.14 | — | -2.73 | — | 2.87 |
| Dhesi inversion MNQ (13) | +32.46 | — | +26.31 | — | 6.15 |

Optimistic = 0 tick slip + $1 RT; base = 1 tick entry/stop/flatten + $1 RT; stress = 2/3/2 ticks + $1 RT.
Conclusion: every rejected strategy failed on **gross** edge (~0), class A ("signal has no edge"), not class B/C.
Calibration: commissions are sourced (Lucid fee table, memory). Slippage ticks are UNCALIBRATED assumptions -
no live or paper fills exist. Targets fill on touch at limit price (optimistic: no queue); stops fill 1 tick
through (assumption). Base case kept.

## 6. Statistical battery audit (V3)

| Gate | Verdict | Notes |
|---|---|---|
| Sharpe | CORRECT | mean/sd(ddof=1), per trade |
| DSR (A: nb=1) | CORRECT formula / MISAPPLIED | = undeflated PSR. ~20+ strategies share the MNQ holdout (reused 3x) -> no multiple-testing correction. Under-deflated -> false-positive side. Standalone FPR 6-14% under AR(1) 0.3 / neg skew |
| DSR (B: nb=2, var=1) | BUGGED (units) | D1 |
| PSR | CORRECT | matches Bailey-LdP 2012 to 1e-12 |
| Newey-West t | CORRECT | matches statsmodels HAC; NW-1994 lag rule. Small-N over-rejects (9.7-22% FPR at N=10) |
| Bootstrap Sharpe CI | UNDERPOWERED/MISAPPLIED for dependence | iid; coverage 0.85 at AR 0.3, 0.65 at AR 0.6. Spec says lo > 1.0, code uses lo > 0.0 (spec/code conflict, SURFACED not changed) |
| MC (sign-flip) | MISAPPLIED under skew | assumes symmetric null: FPR 10-19% on negatively skewed zero-mean trades |
| PBO / CSCV | N/A | implementation sane (noise PBO > 0.3, real edge < 0.1) but never fed a candidate matrix |
| Walk-forward | MISNAMED + UNDERPOWERED | no refit; 5 sub-period Sharpes must all be > 0. Dominant false-negative source N=30-200 |
| Max DD 8% | CORRECT, rarely binding at 1 lot | compounding on pnl/50k |
| Min trades 30 | CORRECT but should emit INCONCLUSIVE, not FAIL |
| Param cap | CORRECT | |
| Independence unit | Mostly OK for 1-trade/day futures | event/wallet/token clustering not implemented (wallet-copy lane is replay-only) |

Combined AND: redundant t-type gates (DSR~PSR~NW~boot) are highly correlated; `wf_min` supplies most of the
extra strictness. The combination is conservative (FPR <= 4.8%) even though individual gates are not.

## 7. Differential test results (V1/V8)

- Shared RTH simulator vs hand oracle: 14 hand fixtures (MNQ/MES/ES long/short, target, stop, same-bar, gap
  stop, gap target, flatten, commission-once, MC no-recharge) + 40 randomized paths: **exact match**.
- Footprint v2 simulator: matches oracle except a gapped stop fills at stop-1 tick instead of the open
  (optimistic; v2 had 0 trades so no effect).
- Frozen logs re-priced from nominal prices reproduce every logged base PnL exactly (`base_matches_log: true`).
- External engines (vectorbt/LEAN/Backtrader/Nautilus): NOT run. Not installed; oracle covers the semantics.

## 8. False-negative risk register (V12)

| Component | Mechanism | Sev | Evidence | Affected | Result |
|---|---|---|---|---|---|
| DSR conv. B | SR0 0.52/trade | High | power map | LuxAlgo, FVG | Confirmed, verdicts unchanged |
| Prop MC | 1 lot / 80 days / terminal 5-day fail | High | invariants test | all "Lucid 0%" | Confirmed; prop != alpha |
| wf_min | all folds > 0 | High | attribution | every gate result | Confirmed power cost |
| Sample size | N 0-205 | High | power map | Dhesi, initiative, absorption, okala | UNDERPOWERED |
| Same-bar pessimism | 5m bars | Med | intrabar audit | LuxAlgo | Confirmed, still rejected |
| Same-bar pessimism | 1m bars | Low | 58/460 stop exits time scalp; 0 FVG | time scalp | Bound < $1.3/trade, still negative |
| Wrong-side stop | strategy bug | Med | trade log | Dhesi v2 | Confirmed |
| Excess slippage | 1-tick stop | Low-Med | sensitivity | all | Uncalibrated; not decisive (gross ~0) |
| Commission / double charge / point value / sign | — | — | oracle | — | Clean |
| Timezone / DST / session | — | — | V4 | — | Clean |
| Roll artifacts | unadjusted jumps | Low | 8 rolls | multi-day models | Unquantified |
| Data loss in aggregation | — | Low | row counts / reconciliation | — | Clean |
| Signal/fill timestamp | right-label resample | Low | code read | inversion, okala | No leakage; 1-min candle offset |
| Bad bootstrap / wrong independence | iid | — | coverage | — | False-POSITIVE side, not negative |
| Lucid rules in sim | MLL lock at start balance, max_days=80, target-before-5-days = fail | ? | UNVERIFIED vs Lucid source | prop MC | UNRESOLVED |

## 9. Historical impact (V11, frozen rules, no rerun)

| Experiment | Holdout evidence | Classification |
|---|---|---|
| VWAP reversion MES (terrible) | gross +$0.22 (t 0.12), net -$2.94 | UNCHANGED |
| Time scalp MES (execution-sensitive) | gross +$0.14 (t 0.43), net -$2.73 (t -7.8); ordering bound < $1.3 | UNCHANGED |
| Casper FVG (borderline) | 67 tr, gross t 0.10, 0 ambiguous | UNCHANGED |
| LuxAlgo POC | worst -5.20, resolved -2.24, best +2.08 | LESS NEGATIVE BUT STILL REJECTED |
| Dhesi inversion v2 (sparse promising) | 13 tr, mean +26.31, 95% CI [-135, +188], needs ~1,000 trades; 1 phantom trade | INCONCLUSIVE (both "DEAD" and "positive candidate" are unsupported) + labelled rerun needed (D4) |
| Initiative v3 (order flow) | 28 tr, -12.68, 95% CI [-37, +12] contains dev +9.50 | INCONCLUSIVE (holdout does not statistically refute dev) |
| Absorption v1/v2, Okala v1/v2 | 0 trades | UNCHANGED as spec'd-frequency failures; alpha N/A |
| All "Lucid MC 0%" lines | 1-lot sizing | PROP verdict only |

## 10. Required fixes

- **P0** Label every verdict on three axes: ALPHA / EXECUTION / PROP-COMPATIBILITY, and emit
  INCONCLUSIVE when N is below the trades needed for 80% power at a pre-declared minimum useful edge.
- **P0** Retire convention B: stop passing `sr_trials_var=1.0`. Replace both A and B with a trials ledger
  (count every strategy that touched the MNQ holdout) and `sr_trials_var` = empirical variance of those
  trials' per-trade Sharpe. Per V13 this needs a regression test + documented effect before merging;
  expect it to deflate MORE than A.
- **P0** Prop MC: report pass rate vs contract count (1..risk-engine `allowed_size`) and state which size.
- **P1** Dhesi v2: labelled rerun with a side check (as v3 does); keep the original result.
- **P1** Simulate on the finest owned bars (1m) and, when 1m is ambiguous, resolve with tick data or report
  worst/best bounds (`BLOCKED BY DATA RESOLUTION` if the sign flips).
- **P1** Verify from Lucid source: MLL lock level, eval time limit, whether hitting target before 5
  qualifying days ends the eval. Until then mark those MC outcomes UNRESOLVED.
- **P1** Rename `walk_forward` -> sub-period consistency; report it with its power cost. Changing the gate
  itself requires V13 evidence.
- **P2** Block bootstrap / dependence-aware MC; fix bootstrap spec/code conflict (1.0 vs 0.0) by owner decision.
- **P2** Footprint sim gap rule; right-label resample alignment; roll-aware multi-day levels; CME session dates.

## 11. Recommended validation standard (no threshold weakened)

Keep convention A thresholds. Add, before any run: minimum useful edge (per-trade SR and $/trade for the
chosen size) and the N needed for 80% power. Verdicts: PASS / FAIL (CI excludes the useful edge) /
INCONCLUSIVE (CI contains both 0 and the useful edge) / N/A. Report gross, tax, net separately; report
worst/resolved/best intrabar bounds; report prop pass-rate curve over contract size.

**Answer to the final question.** Convention A, coin-shaped edge: a real edge of per-trade SR 0.10
(~55% win at 1:1) is accepted 6-9% of the time at 30-100 holdout trades and 14% at 200; SR 0.20 (~60% at 1:1)
is accepted 7-27% at 30-100 trades and 51% at 200. Below 30 trades: 0%. Under convention B: ~0% at every
size. A strong edge (SR 0.30) with 200 trades is accepted 59-85% depending on shape. Meanwhile null strategies are accepted <= 4.8%. The system is a reliable rejector and a
weak detector; the dominant cause is sample size plus the all-folds-positive rule, not a PnL bug.

## 12. Evidence receipts

- Tests: `tests/test_audit_pnl_oracle.py` (54), `tests/test_audit_stat_references.py` (11; NW check needs
  `HEIMDALL_AUDIT_REFS` -> out-of-venv statsmodels 0.15.0), `tests/test_audit_invariants_prop.py` (39). All pass.
- Full suite: `198 passed, 2 failed` (only known OKX-timeout files `test_connectors_live.py`,
  `test_history_real.py`). `tools/check_core_purity.py`: OK.
- Outputs: `data/validation_audit/power_map_2026-09-22.json`, `stat_behavior_2026-09-22.json`,
  `execution_intrabar_2026-09-22.json`, `historical_review_2026-09-22.json`.
- References: Bailey & Lopez de Prado (2012) PSR; Bailey & Lopez de Prado (2014) DSR; Bailey et al. (2016)
  CSCV/PBO; Newey & West (1987, 1994); statsmodels OLS HAC as numeric reference.
- Tick-resolved ordering uses Sierra NQ prints as a proxy for MNQ (median 1-tick divergence), so tick
  resolutions can be off by one tick at the exact level.
