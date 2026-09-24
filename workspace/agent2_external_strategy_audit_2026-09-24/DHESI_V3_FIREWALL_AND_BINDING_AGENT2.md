# DHESI V3 — FIREWALL & BINDING CHECK (Agent 2, checker)

- Prepared 2026-09-24 (UTC start in `WORK_ORDER_START_UTC.txt`). Agent 2 did **not** edit any Agent-1 artifact, did **not** run `primary`/`secondary`, and did **not** read any pre-2024-07-01 price.
- Verdict: **CANONICAL ARTIFACTS VERIFY. NO ECONOMICALLY MATERIAL SPEC/CODE DISAGREEMENT. RUN NOT AUTHORIZED — 3 preconditions open + 2 pre-run defects recommended for Agent 1 to fix (non-strategy).**

## 1. Hash binding (recomputed by Agent 2, `sha256sum`)

| Artifact | Claimed | Recomputed | Match |
|---|---|---|---|
| `DHESI_V3_CANONICAL_SPEC_V1.md` | 8f330ae2…9c6059 | 8f330ae21a7537586cf769b20b4727fddc4f4eee7aea9d94e36bd29aeb9c6059 | YES |
| `DHESI_V3_VALIDATION_PROTOCOL_V1.md` | 49d8d8b9…148793 | 49d8d8b98e139e4d7d88809e36bd8cb9376f7b0b40f5419bb41edd5c3d148793 | YES |
| `dhesi_v3_validator.py` | e52ba647…512710 | e52ba64722a70ac4d80df550809b8c37d7816c63872027d6c72d829cbd512710 | YES |
| `dhesi_v3_harvest_integrity.py` | 6be444f4…30cec6 | 6be444f49dd2efd89d8357e48cebb50120daa03fec41c351a51fa1c3bb30cec6 | YES |
| `AUTHORIZATION_REQUEST_DHESI_V3.md` | fcbc85d1…4cc5bb | fcbc85d1f11dbd0b4ac7d2d263d5250ad0dde1e3641ee5ff1117790f234cc5bb | YES |
| `core/alpha/inversion_model.py` | e32e88f1…0037 | same | YES |
| `core/alpha/inversion_model_v3.py` | 0ab7a515…bf85 | same | YES |
| `core/risk/prop_engine.py` | 5750672e…a265 | same | YES |
| `core/alpha/base.py` | 2d8c40e5…8737 | same | YES |
| `tools/prop_montecarlo.py` | c5aaee33…8e23 | same | YES |
| `tools/validate_inversion_model.py` | 5dffdb7c…9165 | same | YES |
| `selftest_dev_result.json` (49/49 identical) | b837f37e…9e66 | same | YES |
| `data/MNQ_1m.parquet` (dev) | 91670f3f…5774 | same | YES |
| `data/strategy_research/dhesi_v3_development_trades.csv` | 1e92a189…868c | same | YES |
| `data/trials_ledger.json` | a4a797fc…9064 | same (ledger NOT yet updated — see §4) | YES |
| Dhesi rule sheet | 98b931bc…6090 | same | YES |

## 2. Spec ↔ frozen code ↔ reference engine (rule-by-rule, read by Agent 2)

Agent 2 read spec §1–§12, frozen `InversionModelV3._run_backtest/_first_entry_trade_v3`, every inherited v2 method on the path (`_prepare_frame`, `_build_session_pools`, `_equal_pools`, `_cluster_equal_levels`, `_dedupe_pools`, `_resample_bars`, `_detect_fvgs`, `_build_inversion_events`, `_build_ltf_events`, `_build_swings`, `_detect_sweeps`, `_has_4h_fvg`, `_first_inversion`, `_first_retracement`, `_stop_from_recent_swing`, `_targets`, `_simulate_trade`, `_closed_trade`, `_allowed_contracts`→`PropRiskEngine.allowed_size`, `_entry_price`, `_stop_exit_price`, `_target_hit`), and the validator's `reference_run`.

| Rule group | Spec | Frozen code | Reference | Status |
|---|---|---|---|---|
| M1–M6 data/time | §1 | UTC→ET IANA, no fill | same | AGREE |
| T1–T7 sessions, burn-in | §2 | RTH [09:30,16:00] incl.; burn-in applied by validator | same | AGREE |
| B1 15m/5m right-closed right-labelled | §3 | `resample(label=right, closed=right)` | same | AGREE |
| B2 24h HTF bins, 18:00 anchor, session = date(end−1m+6h) | §3 | `_htf_bars_24h` | `_bins24` | AGREE |
| P1–P8 pools, order, dedupe (kind, round(level/0.25)) | §4 | as spec | as spec | AGREE |
| S0 sweep (3-bar reclaim, duplicate pendings) | §5 | `_detect_sweeps` | same | AGREE |
| S1 fractal / S2 FVG / S3 inversion (latest-formed, first on tie, formation after inversion) | §5 | as spec (`max` returns first on tie) | as spec | AGREE |
| S4–S8 HTF choice, displacement ≥30, retracement, attempt gating | §5 | as spec | as spec | AGREE |
| E1–E11, R1 | §6 | as spec | as spec | AGREE |
| E9 size = min(floor(325/(0.50×ticks)),40) | §6 | `floor(daily_buffer/(tick_value×stop_ticks))` | same | AGREE |
| X1–X5 stop-first, TP1 half+BE, runner, flatten, PnL | §7 | as spec | as spec | AGREE |
| L1–L4 | §8 | 3 attempts / 2 losses | same | AGREE |
| Stress = contracts × $1.50 | protocol §3 | validator `evaluate` | — | AGREE |
| Bootstrap (stationary, block 5, B 20,000, seed 20260923, 5th/95th pct) | protocol §6 | validator | — | AGREE |
| P1–P7, FAIL-first | protocol §6 | validator | — | AGREE |

**No economically material disagreement found → no ABORT.** Evidence class: VERIFIED by reading; runtime agreement on dev data VERIFIED by Agent 1 (49/49) and re-verified on synthetic data by Agent 2 (§6).

### Non-material discrepancies (reported, not blocking economics)

| # | Finding | Severity |
|---|---|---|
| D1 | Validator comment cites "spec §2.20, §7"; actual sections are spec §12 / protocol §8. | cosmetic |
| D2 | Protocol §9 requires top-5 trades + share, DSR, achieved power, PROP label word (`PROP_STANDALONE_PASSABLE` / `PROP_PORTFOLIO_COMPONENT_ONLY`). Validator emits none of these. All are derivable post-hoc from the saved trades CSV **without** re-running, so not blocking. | reporting gap |
| **D3** | Protocol §4.5: "Any frozen/reference disagreement must be itemised trade by trade in the report." The validator **does not persist the reference trades**, only a boolean. If the run disagrees, itemisation would require a second pass over the untouched window, which §4.6 forbids. | **PRE-RUN FIX RECOMMENDED** (plumbing only; Agent 1 edits → new validator hash → new authorization request) |
| **D4** | Integrity gate 1 checks NaN only in OHLC. Frozen `_prepare_frame` raises on non-finite **volume**. A NaN volume would crash the one-shot run after the file was opened. Allowed-fix path exists (§4.6) but it is avoidable. | **PRE-RUN FIX RECOMMENDED** (add volume to gate 1) |
| D5 | Sierra-export → parquet conversion is **not frozen** (column names, timezone, Date/Time parsing). M4 requires bar-start UTC stamps; Sierra's export convention is UNVERIFIED. **Mitigated by gate 3:** on the dev window 2024-07-01..09-30, only **45.7%** of minutes have \|1-min close change\| ≤ 2 pt (90,374 minutes, Agent 2, VERIFIED), so a bar-end/±1-minute stamp shift would score ≈46% against the ≥95% threshold and gate 3 would BLOCK. An hour-scale tz error would also fail. | LOW — recommend freezing the converter script by hash before harvest |
| D6 | Protocol says the series is Sierra's own continuous chart (spec M3). The earlier Agent-2 `SIERRA_HARVEST_PLAN.md` / `blind_build.py` (2026-09-23) describe an **offline** volume-leader stitch with a hard end 2024-06-30. That plan is **superseded** by the frozen protocol and cannot satisfy gate 3 (needs data to 2024-09-30). Use the protocol route. | conflict resolved in favour of the frozen protocol |

## 3. Reserved-data firewall

### 3.1 Inventory (metadata only: first/last timestamps; no prices parsed)

- `data/` — all CME equity-index parquet/scid start ≥ 2024-07-01 (dev) or 2026.
- `C:/SierraChart/Data/*.scid` — all index contracts 2026 records only; `MESU25`, `YMU25` empty (0 records).
- **HAZARD — `C:/SierraChart/Data/*.dly` daily files contain pre-2024-07-01 bars:**

| File | First bar | Last bar | SHA-256 |
|---|---|---|---|
| `NQZ26-CME.dly` | 2022-05-23 | 2026-09-21 | 3ffac094…670f |
| `ESZ26-CME.dly` | 2021-09-16 | 2026-09-21 | c36d1137…7c7 |
| `ESM26-CME.dly` | 2023-08-17 | 2026-06-18 | 962da7ca…93ca |
| `ESU26-CME.dly` | 2023-08-17 | 2026-09-18 | a127e4dc…64ef3 |
| `NQM26-CME.dly` | 2024-12-19 | 2026-06-18 | 5f104ba3…64e9 (clean) |

These are **single deferred-contract daily bars**, not the NQ continuous 1-minute series. Hashes are frozen in `SIERRA_PRE2024_DLY_HAZARD.sha256`. No repo script references `.dly` (grep: 0 hits).

### 3.2 CONTAMINATION_EVENT disclosure (self-reported)

**CONTAMINATION_EVENT CE-2026-09-24-A2-01 — severity: TECHNICAL / ZERO-INFORMATION (owner to adjudicate).**
- What: Agent 2's firewall probe (`scratchpad/ts_only.py`) opened the `.dly` files above and loaded their text into memory to extract the **first column (date)**. The OHLC columns were in the loaded bytes but were never parsed into numbers, computed on, printed or displayed. The output contains dates and row counts only.
- Series affected: deferred-contract (NQZ26, ESZ26, ESM26, ESU26) **daily** bars 2021-09 → 2024-06. Not NQ continuous, not 1-minute, not front-month.
- Outcomes derived: none (no return, range, signal, PnL, chart).
- Agent 2's assessment: **no bearing on the Dhesi primary run** and no knowledge transfer. It is declared because the rule says "declare immediately; do not hide it", not because information leaked. The owner may overrule.
- Mitigation recommended (owner decision, not done by Agent 2): quarantine the four `.dly` files out of `C:/SierraChart/Data` until the Dhesi run completes, **or** add a hard exclusion of `*.dly` to every research script's data loader.

### 3.3 New-script audit (Agent 1 eight-strategy program)

At audit time (Agent 1 folder `workspace/external_strategies/`, created 08:21 local): **only `_source_transcripts/` (8 × .json/.txt) exists. No script, no data load, no result.** Therefore no reserved-period read by the eight-strategy program has occurred.

Re-audit 08:33 local: Agent 1 added `_source_reports/` (the 8 report .md files, same as the zip) and `_data_tools/`:
- `dukascopy_pull.py`: free Dukascopy spot FX + XAUUSD 1m bid/ask, 2022-01-01 → 2026-09-18, written to `data/fx_dukascopy/`.
- `histdata_pull.py`: HistData spot FX + XAUUSD 1m bid, 2022 → 2026-08, written to `data/fx_histdata/`.

Neither touches CME equity-index data or any pre-2024-07 index row. **Firewall: PASS.** The execution-axis caveat is recorded in the audit (spot FX ≠ Lucid-tradable CME FX futures). The status must be re-audited each time Agent 1 adds code; the rule to enforce is **any loader of NQ/ES/YM/RTY/MNQ/MES/MYM/M2K rows must hard-fail on timestamps < 2024-07-01 before the Dhesi run**.

## 4. Preconditions to Dhesi run (protocol §4 / Part Q)

| # | Precondition | State (Agent 2 verified) |
|---|---|---|
| 1 | Canonical artifacts verify | **PASS** (§1–§2) |
| 2 | Dataset harvest integrity passes | **OPEN** — no NQ untouched harvest exists; `DHESI_V3_HARVEST_INTEGRITY.json` absent |
| 3 | Freshness manifest confirms no contamination | **CONDITIONAL** — manifest valid for the NQ continuous 1m window; add CE-A2-01 and the `.dly` hazard |
| 4 | Validation binding exists | **PARTIAL** — hashes bound in the authorization request; ledger trials `MNQ-dhesi-inversion-v3` (dev), `-v3-fresh`, and `NQ-dhesi-inversion-v3-untouched` **not registered** (ledger hash unchanged a4a797fc…) |
| 5 | Owner authorization token exists | **ABSENT** (`DHESI_V3_RUN_AUTHORIZATION.txt` not present) |

**Dhesi run status: NOT RUN. Agent 2 will not run it until all five hold.**

## 5. Execution-axis note (for the final report, not the verdict)

MNQ was listed 2019-05-06. For 2011-09 → 2019-05 the MNQ economics applied to NQ prices are **hypothetical** (no MNQ book existed). Spec M2 declares this. The EXECUTION axis must report pre-2019 and post-2019 sub-samples descriptively and must not describe pre-2019 fills as achievable.

## 6. Synthetic pipeline dry run (no market data)

See `dhesi_synthetic_dryrun/dryrun_result.json`. The purpose, method and result are summarised in `AGENT2_EXTERNAL_STRATEGY_AUDIT.md` §1.
