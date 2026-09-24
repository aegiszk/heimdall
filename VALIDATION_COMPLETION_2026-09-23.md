# HEIMDALL — Validation Completion Review (independent checker, 2026-09-23)

Checker lane. I did not write the validator or `VALIDATION_AUDIT_2026-09-22.md`; the job was to try to refute both.
No existing file under `core/`, `tools/`, `tests/`, no `*_PREREGISTRATION.md`, `HEIMDALL_MEMORY.md` or
`AGENT_HANDOFF.md` was edited. No threshold, gate, simulator or strategy was changed. New files are only in
`workspace/validation_completion_2026-09-23/` plus this report. The external engine runs in the isolated
`workspace/validation_completion_2026-09-23/extvenv` (Python 3.12.10). Nothing was installed into the project `.venv`.

Labels: **[V]** VERIFIED (observed directly) / **[I]** INFERRED (derived from verified evidence) / **[U]** UNVERIFIED.

## 1. VERDICT

**The status stays TRUSTED WITH LIMITATIONS. A global TRUSTED rating is not justified.**

- **[V] The PnL engine is trustworthy.** Heimdall's shared RTH simulator (`FuturesRTHModel`) matched backtesting.py 0.6.6
  trade for trade on 559 trades: same count, same entry bar, same exit bar and same exit reason on every trade. Every PnL
  difference is explained. Six trades differ only because the target gapped through, and on those Heimdall is the more
  conservative engine. In production mode every difference equals the analytic slippage tax to 1e-9.
- **[V] The statistics are correct as formulas.** NW t matches statsmodels 0.15.0 HAC to 1.5e-14. PSR and DSR match a
  re-derivation from the Bailey–López de Prado papers exactly.
- **[V/I] The limitations the prior audit gave are real, and this review adds to them:**
  - The MNQ holdout was reused far more than recorded. Memory counts 3 trials; I count at least 12 on the MNQ file and
    at least 65 across the same index-futures holdout window (§7).
  - With honest deflation, SR0 is about 0.11–0.14 per trade. That makes a deployment PASS on the reused 2025-09-11 → 2026-06-30
    window practically unreachable.
  - The `max_dd` gate is sensitive to scale and to sample length. For high-variance (ES-sized) trade streams its power
    *falls* as N grows (§4, N2).
  - Four smaller defects were missed (§4).
- Nothing found here overturns a logged ALPHA verdict. Every trial with a surviving log has a per-trade SR ≤ +0.09 on the
  holdout (§7).

## 2. REVIEWER FINDINGS (prior audit §2, §5, §6, §7)

| Claim | Result | Evidence |
|---|---|---|
| Point values MES 5 / ES 50 / MNQ 2 / NQ 20 | CONFIRMED | `core/alpha/prop_futures.py:20-23`. Differential: MNQ $2/pt reproduced exactly [V] |
| Commission charged once per round turn | CONFIRMED | `prop_futures.py:227` `pnl = side*(exit-entry)*pv - commission_rt`. It is the only commission term; the backtesting.py $0.50+$0.50 per fill matched [V] |
| Entry slippage = 1 tick adverse at the signal-bar close | CONFIRMED | `prop_futures.py:183-184`. The base-mode diff is exactly +1 tick on all 559 trades [V] |
| Stop = stop − side·tick; gap stop = min/max(open, stop∓tick) | CONFIRMED | `prop_futures.py:199-211`. 22 gap stops and 362 plain stops reconcile exactly [V] |
| Target fills at the limit on touch, 0 slippage | CONFIRMED, **conservative on gaps** | `prop_futures.py:213`. When the open gaps through the target, Heimdall fills at the target and backtesting.py at the open. Six trades, −$7.0 total [V] |
| Session flatten = close − side·tick, commission charged | CONFIRMED | `prop_futures.py:214-215` + `:227`. 7 flatten exits reconcile [V] |
| Same-bar stop-first | CONFIRMED | `prop_futures.py:210` precedes `:212`. 209 exit bars had both levels touched; all resolved as stops and all matched backtesting.py, which also processes the SL order first [V] |
| No entry on the exit bar or on the last session bar; one position at a time | CONFIRMED | `prop_futures.py:155,161`. A mirrored rule in the external engine gives an identical count [V] |
| Chronological 60/40 session split | CONFIRMED | `tools/validate_research_candidates.py:63-66`, `validate_inversion_model.py:58-59`. MNQ/MES/ES all split at 2025-09-11 (515 sessions each) [V] |
| No lookahead in signal timing | CONFIRMED (for the code read) | Entry is at the close of bar *i*, and exits are checked from bar *i+1* (`:147-155`). POC/FVG signals use `shift(1)` and past-only windows (`research_candidates.py:92-105,150-205`). VWAP is cumulative through bar *i*, known at its close (`tools/target_sweep.py:141-146`) [V] |
| PSR / DSR formulas | CONFIRMED | Independent re-derivation: max abs diff 0.0 (`stat_refs.json`) [V] |
| NW t = statsmodels HAC (Bartlett, NW-1994 lag) | CONFIRMED | Max abs diff 1.5e-14 over 100 AR(1)-like series, N 30–2000. In the project `.venv` the reference test is SKIPPED (no statsmodels): `1 skipped` [V] |
| D1: convention B means SR0 = 0.52/trade | CONFIRMED | `expected_max_sharpe(1.0, 2)` = 0.51976; call site `tools/validate_research_candidates.py:80-86` [V] |
| D2: prop MC is 1-lot, iid | CONFIRMED | `tools/prop_montecarlo.py:300` `contracts=1`, `:345` iid day counts, `:360` iid trade draws from per-contract PnL [V] |
| "walk_forward: 5 sub-period Sharpes must all be > 0" | **PARTIAL** | `metrics.py:86-88` splits into n+1 folds and **drops the first**, so 1/(n+1) of trades is never scored (10 of 60 in the test). Validators using `wf_splits=4` ignore the first 20% of holdout trades [V] |
| "Not defects: … chronological split, DST" | CONFIRMED | Fixture window 2025-02-24 → 03-21 spans the 03-09 DST change. Exact match across it [V] |
| Combined FPR ≤ 4.8% | CONFIRMED at sd $20 | Null acceptance was 0–2.0% in 8 re-simulated cells (`power_extend_sd20.json`) [V] |
| Power figures (§3) | CONFIRMED, extended | See §6. SR 0.20 at N=200 gave 0.50 (prior audit 0.512) [V] |
| Test suite / purity | CONFIRMED | `2 failed, 197 passed, 1 skipped`. The 2 failures are the known OKX files. The prior audit's "198 passed" counted the statsmodels test, which is now skipped. Purity OK [V] |

## 3. DIFFERENTIAL RESULTS

**Engine: backtesting.py 0.6.6 (kernc).** It runs in extvenv on Python 3.12.10 with pandas 3.0.6, numpy 2.5.3,
bokeh 3.10.0 and pyarrow 25.0.1. The statsmodels 0.15.0 / scipy 1.18.1 references are in the same venv.

**Data.** Real `data/MNQ_1m.parquet`, RTH 09:30–16:00 ET, full 390-bar sessions only:
- Fixture window: 20 sessions, 2025-02-24 → 2025-03-21 (includes the DST change).
- Random window: 150 seeded sessions, 2024-07-05 → 2026-06-30.

**Harness.** Both engines read the same `bars.parquet` and `schedules.json`, so signals are identical by construction.

**Matched semantics.** I checked each backtesting.py behaviour in its source code:
- `trade_on_close=True`: the entry fills at the close of the signal bar.
- Bracket via `buy/sell(sl, tp)`: the SL order is queued first, which gives stop-first on the same bar. A gapped SL fills at the open.
- `position.close()` at the flatten bar fills at its close.
- Commission is `(0.5, 0)` per fill, i.e. $1 per round turn. `spread=0`.
- Prices are multiplied by 2 so that 1 unit equals $1.

**Neutralisation.**
- *zero_slip mode:* `prop_futures.TICK_SIZE` is set to 0.0 at runtime, in the test process only; no file is edited. This removes
  every Heimdall slippage tick.
- *base mode:* production code runs unchanged, and each diff must equal the predicted slippage tax.
- A strategy-level rule is mirrored in both engines: no entry on the exit bar.

| Fixture | Trades H / X | zero_slip: nonzero diffs (unexplained) | zero_slip total H vs X | base: diffs = predicted tax | base total diff |
|---|---|---|---|---|---|
| F1 long 10:00, 20×20 ticks | 20 / 20 | 0 (0) | −80.0 / −80.0 | 20/20 exact | −16.5 |
| F2 short 11:30, 40×80 | 20 / 20 | 0 (0) | 0.0 / 0.0 | 20/20 | −16.5 |
| F3 long 14:00, 400×400 (flatten-heavy) | 20 / 20 | 0 (0) | 889.5 / 889.5 | 20/20 | −15.5 |
| F4 3×3-tick, alternating side every 30 min | 200 / 200 | 5 (0), all `tp_gap_open_fill` | −463.5 / −457.0 | 200/200 | −196.0 |
| R random 300 attempts (stop/target 4–80 ticks) | 299 / 299 | 1 (0), `tp_gap_open_fill` | −1119.0 / −1118.5 | 299/299 | −234.0 |

Exit reasons exercised: 362 stops, 22 gap stops, 168 targets, 7 session flattens. 209 bars had both levels touched (stop-first).

**Every nonzero diff is explained.**
- *zero_slip:* the 6 diffs are target gap-throughs. The bar opened beyond the target; backtesting.py filled the limit at the
  better open, while Heimdall books the target. Heimdall is therefore pessimistic by $6.5 (F4) and $0.5 (R).
- *base:* every diff equals the analytic tax: entry −1 tick; stop and flatten −1 tick; gap stop = min/max(open, stop∓tick); target 0.

Files: `diff_per_trade.csv` (1,118 rows = 559 trades x 2 modes), `diff_summary.json`.

## 4. NEW DEFECTS (missed by the prior audit)

| # | Defect | Evidence | Severity / effect |
|---|---|---|---|
| N1 | **Holdout reuse is under-counted in memory.** `HEIMDALL_MEMORY.md` says "MNQ two-year holdout read by 3 experiments (Dhesi, POC, FVG)". Fabio ORB-delta (+ no-delta baseline), Okala v1/v2, Dhesi v1, intraday momentum (+ 2 diagnostics) and the contaminated "fade r_ROD" variant also read the same MNQ_1m 60/40 holdout | `tools/validate_fabio_orb_delta.py:36-44`, `validate_okala8020.py` (0.60, MNQ_1m), `validate_intraday_momentum.py:94-103`, memory lines 329 / 402 / 590 | High for deployment: this is the input to deflation (§7) [V] |
| N2 | **`max_dd` (8% compounding on $50k) makes the alpha gate depend on sample length and scale.** At sd $400/trade, true SR 0.10 is accepted 0.18 at N=300, 0.02 at N=1200 and 0.00 at N=2000; SR 0.05 is accepted 0.00 at every N up to 6,500. `max_dd` fails 40/40 at N=2000. ES trade streams are in this regime: intraday momentum ES has sd ≈ $570/trade | `power_extend_sd400.json`, reason tally in §8 | Medium. Alpha is confounded with sizing, as in D2. Belongs on the RISK/PROP axis. Historical ES verdicts are unaffected because they had negative means [V/I] |
| N3 | **VWAP-reversion targets are not rounded to the tick.** The target equals the raw VWAP, so 226 of 1,511 MES trades exit at off-tick prices | `prop_futures.py:310-311`; `data/prop_futures/vwap_reversion_hard_stop_MES_1m_trades.csv` | Low and **conservative**. Highs and lows are on-tick, so hit detection is identical to a tick-rounded limit and only the fill is understated: $143.30 in total, $0.095/trade. Verdict unchanged [V] |
| N4 | **Some validators drop zero-PnL trades from the gate series.** `validate_fabio_orb_delta.py:122` and `validate_swing_trend.py:107` use `active = returns[pnl != 0]`. An MNQ 2-tick winner nets exactly $0 after the $1 commission and would vanish from N and the Sharpe | Trade logs: 0 zero-PnL trades in Fabio (166) and swing (16) | Latent, 0 historical impact [V]. `core/funnel/funnel.py:31` uses `r[pos!=0]`, so N = bars-in-position (crypto loop lane, out of futures scope) [V] |
| N5 | **`walk_forward` silently discards the first fold** (see §2) | `metrics.py:87-88` | Low. Adds to the power cost of `wf_min` [V] |
| N6 | **Prop MC resampling is iid** for days (`rng.choice(daily_counts)`) and trades (`rng.choice(trade_pnls)`). This destroys day-level clustering, the correlation of trades within a day and regimes. Intratrade adverse excursion is not modelled, since only realized PnL goes to `on_fill` | `tools/prop_montecarlo.py:345,360` | Medium for PROP pass rates. Likely optimistic about MLL death for clustered losers [I]. Use a stationary block bootstrap over sessions |
| N7 | **Doc/code default conflict.** `CLAUDE.md` says the `daily_buffer` default is 325 ("CORRECTED"), but `core/risk/prop_engine.py:28` defaults to 400. Every validator passes 325 explicitly, so there is no numeric impact | grep of `tools/validate_*.py` | Low; SURFACED, not changed [V] |
| N8 | **16:00 bar included.** `tools/target_sweep.py:136` and `validate_prop_futures.py:64` keep the 16:00 bar (`<=`), so the last-bar flatten fills at 16:01, one minute after the RTH close | code read | Negligible [V] |

## 5. DISCOVERY vs DEPLOYMENT GATE (recommendation; no existing threshold weakened)

**Two layers with different purposes.** `run_gate` with the convention-A thresholds stays exactly as it is. It becomes the
DEPLOYMENT gate, with additions. DISCOVERY is a new, earlier layer. It only decides whether a hypothesis earns more data or
prospective paper trading. It can never authorize capital.

### DISCOVERY gate: PASS / FAIL / INCONCLUSIVE / N/A

Declare before the run, in the preregistration:
- the minimum useful edge `s_min` as a per-trade SR, plus $/trade net at the stated contract count;
- the one-sided α_d = 0.10;
- N80 = ((z₀.₉₀ + z₀.₈₀)/s_min)². With `s_min` = 0.10 this is 451.

Statistic: the per-trade net-PnL t, computed from a **stationary block bootstrap over sessions**, or NW t with Student-t
critical values when N < 100. It is a single test, not an AND of correlated t-gates. `wf_min` and `max_dd` are not used here.

| Outcome | Rule |
|---|---|
| N/A | The spec produced < 10 trades (frequency failure), or the data fidelity gate failed |
| PASS | Lower one-sided 90% bound on mean > 0 **and** the point estimate ≥ s_min/2, after Benjamini–Hochberg FDR q = 0.10 across the trials ledger family |
| FAIL | Upper one-sided 95% bound on SR < s_min (the CI excludes a useful edge) |
| INCONCLUSIVE | Otherwise. Additionally tagged UNDERPOWERED when N < N80 |

Simulated behaviour at sd $20 (`power_extend_sd20.json`; the PASS arm only, before FDR):
- Null PASS rate: 6.7–17.3%. This is above the nominal 10% at N ≤ 100 because NW over-rejects at small N, hence the
  bootstrap / t-critical requirement.
- Power: 83% at SR 0.05 / N=2000, 85% at SR 0.10 / N=500, 95% at SR 0.20 / N=200 (85% under AR(1) 0.3), 82% at SR 0.30 / N=50.
- Null FAIL rate at N=500: 73% (coin shape).

### DEPLOYMENT gate: authorizes capital

Keep every convention-A threshold (`dsr_min` 0.95, `nw_t_min` 2.0, `boot_lo` > 0, `max_dd` 8%, `min_trades` 30, `wf_min` > 0,
`pbo` < 0.05, `mc_p` < 0.05). Add:
1. **Trial-count deflation.** `nb_trials` and `sr_trials_var` come from the ledger (§7), not from 1/0 or 2/1.
   - Ledger values give SR0 ≈ 0.11–0.14 per trade.
   - A PBO from a real CSCV matrix is required.
2. **Dependence-aware bootstrap.** Use a stationary block bootstrap over sessions for `boot_lo` and for the MC null, replacing iid
   and sign-flip. The prior audit showed iid bootstrap coverage of 0.85 at AR 0.3.
3. **Prop pass rate vs contract count.** Run the MC for 1..`allowed_size` lots with a session-block bootstrap (N6). Report the
   size used and label it the PROP axis.
4. **`max_dd` on a fixed horizon.** Report `max_dd` per 100 trades at the deployed size, on the RISK axis. The existing 8% check is
   kept and not loosened, but it must not be read as alpha evidence (N2).
5. **Fresh data.** Evidence must come from data **not in the reused 2025-09-11 → 2026-06-30 window**, i.e. prospective or
   post-2026-07-01, where the trial count restarts.

## 6. REQUIRED-N TABLE (per-trade Sharpe, 80% power)

| Test | SR 0.05 | SR 0.10 | SR 0.20 | SR 0.30 |
|---|---|---|---|---|
| Analytic, discovery α=0.10 one-sided | 1,803 | 451 | 113 | 50 |
| Analytic, α=0.05 one-sided (≈ PSR/DSR nb=1 > 0.95) | 2,473 | 618 | 155 | 69 |
| Analytic, NW t > 2.0 alone | 3,230 | 807 | 202 | 90 |
| **Simulated production gate A (AND), coin, sd $20** | >6,500 (0.75 at 6,500) | ≈2,000 (0.82) | ≈500 (0.82); AR(1) 0.3: >500 (0.60) | ≈200–300 (0.79 / 0.97) |
| Simulated discovery PASS arm, coin | ≈2,000 (0.83) | ≈500 (0.85) | ≈200 (0.95; 0.71 at 100) | ≈50 (0.82) |
| Deployment DSR with ledger SR0 = 0.116 (nb 24, V 0.00345) | impossible | impossible | 882 | 183 |
| Deployment DSR with ledger SR0 = 0.139 (nb 40, V 0.004) | impossible | impossible | 1,633 | 237 |

The deployment rows use the analytic N = ((1.645 + 0.842)/(s − SR0))². At sd $400/trade the production gate never reaches
80% for SR ≤ 0.10 (N2). For comparison, the MNQ holdout supplies 13–205 trades per 1-per-day strategy.

## 7. PBO / TRIAL-COUNT RESOLUTION PLAN

### Ledger: index-futures 60/40 holdout window 2025-09-11 → 2026-06-30 (MNQ/MES/ES_1m, 515 sessions each)

**MNQ_1m file: 12 configs across 8 families.** [V from code and memory]
- Dhesi inversion v1 and v2
- Okala v1 and v2 (0 trades)
- Fabio ORB+delta, plus its no-delta baseline
- LuxAlgo POC
- Casper FVG
- Intraday momentum: primary + always-long-last-half-hour + ONFH diagnostics
- The contaminated "fade r_ROD" variant

The 2-tick stress rerun is a re-pricing, not a new signal. Dhesi v3 is preregistered but has not been run (no
`dhesi_v3_validation_*.json` exists), so it adds 0.

**Same window on MES/ES: ≥ 53 more configs.**
- Inversion v1/v2 on MES and ES: 4
- Intraday momentum MES/ES + diagnostics: 6
- Target sweep holdout grid: 30. The target was selected on train, but all 30 holdout cells were computed and printed
  (`target_sweep_grid.csv`: 30 holdout rows).
- Quality-filter holdout rows: 9
- Swing ES: 1
- VWAP / time-scalp / trend-pullback full-sample: 3

Separately, 20 random null seeds plus 60 slippage and 60 stop-limit configs were run (`tools/null_entry_test.py`). These
are true nulls: they count as looks, not as candidates.

**Totals:** ≈ 12 (MNQ file) / ≈ 65 non-null configs (window) / ≈ 12 effective families.

### Sierra footprint holdout (NQ ticks; footprint 146 RTH sessions; initiative holdout 2026-06-16 onward)

3 return trials:
- absorption v1 (Sierra 1m bar proxy, 50/50, 0 trades);
- footprint v2 (50/50, 0 trades);
- initiative v3 (28 holdout trades).

There were also 2 level-only reads with no returns: VA Stage 1 on 146 sessions, and the POC-proxy fidelity check on 4,857
five-minute bars. The prior audit's tick re-pricing of frozen trades is an outcome read, not a new trial.

A separate "fresh" window (2026-07-01 → 09-18, Sierra 1m) was read by intraday momentum on 6 contracts.

### Empirical inputs

Source: `trials_ledger_empirical.{csv,json}`: 27 trials with surviving logs, 24 with holdout N ≥ 30.

| Input | Value |
|---|---|
| var(SR̂) over all 24 trials | 0.00345 |
| Mean sampling variance 1/N | 0.00294 |
| Excess over sampling | 0.00051 |
| One-per-family variance (9 families) | 0.00525 |
| Max observed SR̂ | +0.0024 (Casper FVG) |

Every trial with N ≥ 30 had SR̂ ≤ +0.0024.

**Proposed values:**
- `nb_trials` = the effective independent count. Report both 12 (families) and 65 (configs); gate on the conservative one.
- `sr_trials_var` = max(ledger var(SR̂), 1/N_candidate) ≈ 0.0035–0.0052.
- The resulting SR0 is 0.110–0.139 per trade. With the excess-only variance, 0.00051 at nb 24, SR0 is 0.045. Report this as the
  optimistic bound only.
- Never again use 1.0.

### CSCV matrix

- Rows = the 515 RTH sessions of the full 2024-07-01 → 2026-06-30 period. CSCV creates its own IS/OOS splits, so the full
  period is used, not only the holdout.
- Columns = every non-null trial.
- Cell = per-contract net daily PnL, with 0 on no-trade days, on one common calendar.
- Trials with only holdout logs (target sweep, Fabio) must be rerun deterministically on the full period from their frozen
  code and parameters, with no tuning. Zero-trade trials are all-zero columns, so the Sharpe is 0.
- Use S = 16 blocks (≈ 32 sessions per block).
- Also compute a per-family matrix and report both PBOs.

### Minimal code change (describe only; not done)

No change to `core/validation/battery.py` or `metrics.py` is needed: `run_gate(..., candidate_matrix=...)` already feeds
`cscv_pbo`. Proposed:
1. New `tools/trials_ledger.py`, which writes an append-only `data/validation_audit/trials_ledger.csv` (trial id, family,
   dataset, window, prereg SHA, holdout N, SR̂, daily-PnL column path). It also writes a builder that returns
   `(nb_trials, sr_trials_var, candidate_matrix)`.
2. Validators read those values instead of hardcoding `nb_trials=1, sr_trials_var=0.0` or `2, 1.0`.
3. Optional core guard: `run_gate` raises if `sr_trials_var > 0.25` while the series is per-trade. That is a units sanity
   check that would have caught D1.

Regression tests:
- (a) `expected_max_sharpe(0.004, 40)` = 0.13847 ± 1e-5 and `(1.0, 2)` = 0.51976.
- (b) A static test that fails if any `tools/validate_*.py` passes `sr_trials_var >= 0.25`.
- (c) CSCV: 20 noise columns give PBO > 0.3; 19 noise columns + 1 SR 0.3 column give PBO < 0.1.
- (d) A golden test that reruns the frozen Casper FVG holdout with the ledger inputs, asserts FAIL, and documents the DSR
  before and after.
- (e) The ledger builder refuses a trial without a prereg SHA or a window.

## 8. EVIDENCE (commands + outputs)

All run from the repo root. Workspace = `workspace/validation_completion_2026-09-23/`.

- **pytest.** `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` gave
  `FAILED tests/test_connectors_live.py::test_live_public_connectors`,
  `FAILED tests/test_history_real.py::test_btc_real_history_and_funnel_verdicts` and
  `2 failed, 197 passed, 1 skipped in 177.62s` (`pytest_out.txt`).
  `-rs` shows `SKIPPED [1] tests\test_audit_stat_references.py:66: could not import 'statsmodels.api'`.
- **Purity.** `.venv/Scripts/python.exe tools/check_core_purity.py` gave `core purity OK: /core is free of /meta imports`.
- **External venv.** `py -3.12 -m venv extvenv; pip install backtesting pandas pyarrow numpy statsmodels scipy` installed
  `backtesting==0.6.6 bokeh==3.10.0 numpy==2.5.3 pandas==3.0.6 pyarrow==25.0.1 statsmodels==0.15.0 scipy==1.18.1`.
- **Differential.** `make_fixtures.py` gave `bars=64350 sessions=165 fx=2025-02-24..2025-03-21 rnd=2024-07-05..2026-06-30
  rnd_attempts=300`. `heimdall_side.py` (.venv) was followed by `ext_side.py` (extvenv) and `compare.py`. See the §3 table;
  `unexplained: 0` in all 10 fixture×mode rows.
- **Stat references.** `extvenv ... stat_refs.py` gave `nw_max_abs_diff 1.5e-14, psr 0.0, dsr 0.0,
  SR0_conventionB 0.51976, SR0_nb40_var0.004 0.13847, walk_forward_first_fold_ignored_len 10 (of 60)`.
- **Power.** `power_extend.py 20` → `power_extend_sd20.json`.
  - The first run double-scaled the per-trade sd to $400. That was my bug, caught by diagnosing a non-monotone result.
    It is kept as the scale-sensitivity result `power_extend_sd400.json`.
  - Diagnosis (40 reps, sd $400): SR 0.10 N=2000 → accept 0.0, reasons `max_dd 40, wf_min 7`, median max_dd −0.152.
- **Ledger.** `trials_ledger.py` → `trials_ledger_empirical.{csv,json}`. The `instrument` column reads "holdout" for
  target-sweep rows; this is a cosmetic parse artefact and does not affect SR̂.
- **Off-tick targets (N3).** A one-liner on the VWAP MES log gave
  `trades 1511 target exits 397 offtick 226 understatement total 143.3 per trade 0.095`.
- **Pre-existing files.** The same workspace already held files timestamped about 00:28–00:33 from an earlier session
  (`diff_*.py`, `diff_results.json`, `power_extension*.{py,json}`, `pytest_full.txt`). They are not mine and nothing here
  relies on them. They independently agree: 0 residual PnL on 2,217 trades vs backtesting.py 0.6.6, and gate-A acceptance of
  0.80 at SR 0.10 / N=2000.

**Residual limits.**
- **[U]** Slippage ticks are still uncalibrated. No live or paper fills exist.
- **[U]** Lucid rule encodings (MLL lock level, eval time limit, whether target-before-5-days is terminal) are still unverified.
- **[I]** The differential covers `FuturesRTHModel` only. The separate simulators (`inversion_model.py`, `okala8020.py`,
  `orderflow_*`, `intraday_momentum.py`, `_simulate_daily`) were not diffed against an external engine. The prior audit
  oracle-tested only the footprint v2 simulator.
