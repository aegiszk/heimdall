# Dhesi reopen adjudication — Agent 1 (lead research adjudicator)

- Work order start: 2026-09-23T15:03:02Z (`WORK_ORDER_START_UTC.txt`)
- Workspace: `workspace/dhesi_adjudication_agent1_2026-09-23/` (all outputs are here; no shared file was modified)
- Isolation: nothing Agent 2 created after the start time was read. Their workspace files (`DHESI_D4_BLIND_DERIVATION_AGENT2.*`, transcript) are dated 19:03–19:04 local (UTC+4), after the start, and were not opened. All other artifacts used here predate the start.
- Data read in this cycle: DEVELOPMENT only (`data/MNQ_1m.parquet`, 2024-07-01 → 2026-06-30). No Sierra or untouched history was read. No validation was run.
- Labels: [V] verified by direct observation, [I] inferred from verified evidence, [U] unverified.

## STATUS

**FINAL VERDICT: REOPEN_REQUIRES_NEW_HYPOTHESIS**

D4 does not explain the sign flip. The real bug fix (a side check on the stop) leaves v2 **negative**: −$446.38 becomes −$304.88. It also drops v2's holdout to −$0.62/trade. The −$446 → +$617 flip comes entirely from the **10-point minimum-stop floor**. The v3 preregistration added that floor after inspecting v2's losing trades. D4-as-applied is therefore **C. POST-HOC STRATEGY CHANGE**. The v3 model is a legitimate new hypothesis. It is not a bug-corrected v2, and its "fresh" window is a REUSED_HOLDOUT.

---

## 1. STATE CHRONOLOGY [V unless marked]

| # | Stage | Artifact | Data read | Result |
|---|---|---|---|---|
| 0 | Source | Chart Fanatics video `UIGZtoGGPH4`; Manus rule sheet `Dhesi Trades ICT Strategy_ Structured Rule Sheet.md`; transcript re-fetched independently: `UIGZtoGGPH4_agent1.en-GB.json3` | — | 4-step sequence; stop "above the current 15-minute high" |
| 1 | v1 codification | `HEIMDALL_MEMORY.md:312-327`; code has since been overwritten by v2 (no v1 source survives) [I] | MNQ/MES/ES 1m, 60/40 | Holdout 2–6 trades per instrument; "FAIL on frequency" (`:329-341`) |
| 2 | Funnel diagnostic | `tools/diag_inversion_funnel.py`, memory `:344-349` | MNQ full 2 years | ATR proxy removed; one revision authorised |
| 3 | v2 | `core/alpha/inversion_model.py` (mtime 2026-07-05); trade logs `data/prop_futures/inversion_model_{MNQ,MES,ES}_1m_trades.csv` | same | MNQ 30 trades, −$446.38 whole; holdout 13 trades, +$26.31/trade. MES/ES died from the unscaled 30-point displacement filter (`:366`) |
| 4 | Label history | memory `:365` "CONFIRMED PORTFOLIO CANDIDATE #1"; `AGENT_HANDOFF.md:63` "Live Candidate #1"; **not** in the handoff's "11 dead ends" (`AGENT_HANDOFF.md:43-54`) | — | MNQ Dhesi was **never killed**. Ledger: MNQ-v2 INCONCLUSIVE; MES/ES v1+v2 DEAD |
| 5 | Audit defect D4 | `VALIDATION_AUDIT_2026-09-22.md:44`; supersession S5 | frozen logs | 5/30 wrong-side stops; v2 reclassified INCONCLUSIVE, CI [−135, +188] |
| 6 | v3 prereg | `DHESI_V3_PREREGISTRATION.md`, SHA-256 `C9D143E5…D843` (re-verified this cycle); code `core/alpha/inversion_model_v3.py` (2026-09-22 18:44) | frozen *after* reading v2's trade log (prereg §"Why v3 exists") | Six changes, including `stop_guard` = side + 10-point floor |
| 7 | v3 run | `tools/validate_inversion_v3.py` → `data/strategy_research/dhesi_v3_*` (2026-09-23 17:46–18:15) | dev 2024-07 → 2026-06 **and** Sierra 2026-07-01 → 09-18 | Dev 49 trades +$51.03/trade; holdout 20 trades +$34.79/trade; "fresh" 4 trades +$94.59/trade; "SURVIVING RESEARCH CANDIDATE" |
| 8 | Reopen claim | `workspace/tick_discovery_2026-09-23/TICK_EDGE_DISCOVERY.md:118,134,158` | — | "D4 flipped v2 from −$446 to +$617", "FALSE KILL". **Both statements are refuted below.** |

Every evaluated window:

| Version | Window | Instrument | Status |
|---|---|---|---|
| v1, v2 | 2024-07-01 → 2025-09-10 (train) | MNQ, MES, ES | DEVELOPMENT |
| v1, v2 | 2025-09-11 → 2026-06-30 (holdout) | MNQ, MES, ES | REUSED_HOLDOUT |
| v3 | 2024-07-01 → 2026-06-30 | MNQ | DEVELOPMENT (by its own prereg) |
| v3 | 2026-07-01 → 2026-09-18 | MNQ (Sierra) | REUSED_HOLDOUT (§6); **not in the ledger** |
| this cycle | 2024-07-01 → 2026-06-30 | MNQ | DEVELOPMENT, forensic only |

GATE 0 PASSED. Every version and window is accounted for. The only gap is v1 source code, which survives only as memory text.

## 2. D4 ROOT CAUSE

### Formulas

Let `b` be the bias (+1 long, −1 short), `E = close_5m + b·0.25` the slipped entry, and `S*` the most recent confirmed 15m 3-bar fractal swing (low for long, high for short) with `swing.ts ≥ HTF inversion ts` and `confirmed_ts ≤ entry_ts`.

- **v2 code** (`inversion_model.py:835-855`, used at `:802-813`):
  `stop = S* − b·0.25`
  It has no side check. Risk is `|E − stop|` (`:807`, `:811`), so a wrong-side stop still sizes and trades. Simulation then fills `open ≤ stop` on the next bar as `gap_stop` (`:1098-1112`).
- **v3 code** (`inversion_model_v3.py:220-225`):
  same `stop`, then `if b·(E − stop) < 10.0: continue`
  `continue` moves on to the **next** LTF inversion of the same setup; it does not abandon the setup.
- **Knowable at entry?** Yes, in both versions. `S*` needs `confirmed_ts ≤ entry_ts`, and E is the entry bar close. Neither version looks ahead [V: reference reimplementation, §5].

### What the 10-point floor is

The prereg's "Stop validity" rule (`DHESI_V3_PREREGISTRATION.md:46`) bundles two rules:
1. **side:** `b·(E − stop) > 0`
2. **floor:** `b·(E − stop) ≥ 10` points

Its own §5 cites the losses that motivated the floor: "A 0.25-point and a 3-point stop sized to 40 contracts and lost $100 and $300". The floor was frozen **after** those v2 outcomes were read.

### Decomposition (DEVELOPMENT data; independent reference, cross-checked with the frozen code in §5)

| Config | Trades | Whole | Train | Holdout (13 → n) | Holdout mean |
|---|---|---|---|---|---|
| v2 frozen | 30 | −$446.38 | −$788.38 | +$342.00 (13) | +$26.31 |
| v2 + side only | 27 | **−$304.88** | −$296.88 | **−$8.00 (13)** | **−$0.62** |
| v2 + side + floor (`stop_guard`) | 26 | **+$617.12** | +$287.62 | +$329.50 (12) | +$27.46 |
| v3, no guard | 54 | +$2,337.00 | +$1,666.25 | +$670.75 (21) | +$31.94 |
| v3, side only | 50 | +$2,653.25 | +$1,957.50 | +$695.75 (20) | +$34.79 |
| v3 full (official) | 49 | +$2,500.38 | +$1,804.62 | +$695.75 (20) | +$34.79 |

Attribution of the −$446.38 → +$617.12 change (+$1,063.50):
- side check (the bug fix): **+$141.50**
- 10-point floor (post-hoc): **+$922.00**
- In v3 the guard is irrelevant to the result: the holdout is identical with or without the floor, and dropping the guard entirely changes whole-period PnL by less than 10%. v3's positive development result comes from the **other** v3 changes, which were also designed after reading the v2 log on this same data.

With the prereg's literal "skip the setup" wording instead of the code's continue rule (frozen code, Appendix A):
- v2 + side = **−$411.88**
- v2 + side + floor = **−$11.88**

So the sign flip also depends on the code departing from the prereg text.

**Root cause (one sentence):** v2 used the most recent 15m fractal as the stop without checking which side of entry it lay on. That real bug cost v2 only $141.50, and the reported sign flip was produced by a separate, post-hoc 10-point minimum-stop rule.

## 3. SOURCE vs PREREG vs OLD CODE vs FIXED CODE

| | LONG | SHORT |
|---|---|---|
| **Source** (transcript 08:09, 13:04, 35:54-36:14) | Mirror of short, stated for the long swing trade: "stop loss was placed below the recent structural swing low" (rule sheet, Trade 2) | "My stop loss … would be above the current 15-minute high"; "stop loss above that high"; "should … be at the high or near the high"; "I always try to have a wider stop … People have too tight stop losses. They get stopped off for 20 points". **No numeric minimum.** |
| **Frozen v2 spec** (`inversion_model.py:156-157`, gap `:245`) | "one tick beyond the most recent confirmed 15m fractal swing in the stop direction after HTF inversion … the swing that caused the LTF inversion" | same |
| **v2 code** | `swing_low − 0.25`; no side check. 3 wrong-side longs (2024-08-07, 2025-01-31, 2025-08-07) | `swing_high + 0.25`; no side check. 2 wrong-side shorts (2024-11-20, 2026-04-28) |
| **v3 `stop_guard`** | skip the LTF event unless `E − stop ≥ 10`; try the next event | skip unless `stop − E ≥ 10`; try the next event |
| **Only info known at entry?** | yes | yes |

Classification of each component:
- **side**: A (implementation bug). "Stop", "above the high" and "the swing that caused the inversion" are protective by definition. A stop on the wrong side is not a stop.
- **floor**: C (post-hoc). It is not in the source or the v2 spec, and it was derived from observed v2 losers. The source's "wider stop" remark supports the idea in spirit but gives no number.
- **continue vs skip after a failed guard**: B (interpretation). The prereg text says "skip the setup"; the code tries the next LTF event instead.

### D4 CLASSIFICATION: **C. POST-HOC STRATEGY CHANGE**

The "stop correction" that produced +$617 is the bundled `stop_guard`. Its sign-flipping component, the floor, was introduced after outcomes and is not implied by the frozen v2 specification. The A-class side fix inside it is real, but it does not flip the sign and does not rescue v2.

## 4. TRADE-LEVEL DIFFERENTIAL

Exactly 7 of 30 sessions change. The other 23 sessions are identical on side, entry, stop, TP1, contracts, risk, exit timestamp, exit price and PnL [V].

**No other variable changed.** Entry signal code, session, targets, sizing rule (`min(floor(325/(0.5·stop_ticks)), 40)`), commission ($1 round trip), slippage (1 adverse tick), same-bar stop-first, trade ordering and the 60/40 split are all the same code path. The only switch is the guard.

| Session | Dir | Old entry / stop (signed dist) | Old PnL, exit | New entry / stop | New PnL, exit | Cause |
|---|---|---|---|---|---|---|
| 2024-08-07 | L | 18234.00 / 18279.75 (−45.75) | −7.50 gap_stop | — no trade | 0 | side: wrong-side swing low; no later valid event |
| 2024-11-20 | S | 20678.75 / 20644.75 (−34.00) | −6.00 gap_stop | — | 0 | side |
| 2025-01-31 | L | 21743.50 / 21904.25 (−160.75) | −2.00 gap_stop | — | 0 | side |
| 2025-08-07 | L | 23363.25 / 23381.00 (−17.75) | −9.00 gap_stop | 14:55 23408.25 / 23329.75, 2 lots | **+467.00** runner_session_flatten | side, then a **later** LTF event (continue rule) |
| 2026-04-28 | S | 27128.75 / 27099.50 (−29.25) | −10.00 gap_stop | side-only: 15:20 27177.00 / 27183.75 (**6.75 pt**), 24 lots → **−360.00** stop; with floor: no trade | side-only −360.00; side+floor 0 | the replacement trade is a tiny stop that only the floor removes |
| 2025-02-24 | S | 21624.75 / 21625.00 (**0.25 pt**), 40 lots | −100.00 gap_stop | floor: 13:50 21623.75 / 21661.50, 4 lots, TP1 21567.125, runner 21558.25 | **+484.50** runner_target | floor then continue; **the single largest contributor (+$584.50)** |
| 2025-12-11 | S | 25644.50 / 25647.50 (**3 pt**), 40 lots | −300.00 stop | floor: 15:35 25670.25 / 25723.25, 3 lots | −322.50 stop | floor then continue |

Reconciliation:

| Step | Total | Δ | Source of Δ |
|---|---|---|---|
| OLD v2 | −$446.38 | | |
| + side only | −$304.88 | +$141.50 | 3 wrong-side trades removed (+$15.50); 2025-08-07 replaced (+$476.00); 2026-04-28 replaced with a worse trade (−$350.00) |
| + floor (= v2 + D4 as applied) | +$617.12 | +$922.00 | 2025-02-24 (+$584.50), 2026-04-28 (+$360.00), 2025-12-11 (−$22.50) |
| FULL v3 | +$2,500.38 | +$1,883.26 | htf_24h + early_sweeps + session_pools + attempts, interacting (singly: htf_24h −$361.50; the others ±$0) |

GATE 2: RECONCILED trade by trade. The sign flip is real arithmetic, but it is attributable to the floor, not the bug. It rests on about 2 trades, and one of them (+$584.50) is 55% of the net change.

## 5. INDEPENDENT REIMPLEMENTATION RESULT

`ref_dhesi.py` was written from the specification text: the v2 docstring and discretion-gap list, plus the v3 prereg. It uses only pandas/numpy, imports nothing from `core.alpha`, and has its own FVG, inversion, sweep, pool, fractal, sizing and simulator code. Caveat: I had read the v2 source before writing it. It is independent code, not a blind derivation.

| Target | Reference | Frozen | Agreement |
|---|---|---|---|
| v2 (all fixes off) | 30 trades, −$446.38 | 30, −$446.38 (`data/prop_futures/…MNQ…csv`) | 30/30 on entry_ts, side, entry, stop, TP1, contracts, exit, PnL |
| v3 official | 49 trades, +$2,500.38 | 49, +$2,500.38 (`dhesi_v3_development_trades.csv`) | 49/49 on the above plus exit_ts and reason |
| v2 + stop_guard | 26, +$617.12 | 26, +$617.12 (frozen-code rerun, Appendix A); +$617.13 in the stored ablation JSON (rounding) | 26/26 entries and PnL |
| v2 + side only | 27, −$304.88 | 27, −$304.88 (frozen-code rerun) | 27/27 entries and PnL |

**Disagreement rate: 0%.** The mechanical rules are reproducible, so this is not IMPLEMENTATION_NOT_CANONICAL.

Frozen-code cross-check of the decomposition (`d4_decompose.py`, subclassing the frozen code): see Appendix A.

## 6. CONTAMINATION MAP

The ledger (`data/trials_ledger.json`, 86 entries) is the source unless marked.

| Window | Instruments | Status | Prior reads | Purpose |
|---|---|---|---|---|
| 2024-07-01 → 2025-09-10 | MNQ, MES, ES (Databento 1m) | **DEVELOPMENT** | every index-futures experiment (not ledgered separately) | train / diagnosis |
| 2025-09-11 → 2026-06-30 | MNQ, MES, ES | **REUSED_HOLDOUT** | 64 ledger entries + Dhesi v3 (unledgered) + this cycle's forensic re-read | holdout for ~20 strategy families |
| 2026-02-27 → 2026-09-21 | NQ ticks / footprint (Sierra) | **REUSED_HOLDOUT** | footprint v2, tick-edge atlas (Agent 2, labelled DEVELOPMENT) | order-flow research |
| 2026-06-16/23 → 2026-09-21 | NQ, MNQ (Sierra 1m) | **REUSED_HOLDOUT** | initiative v3, absorption v1 | order-flow holdouts |
| 2026-07-01 → 2026-09-18 | MNQ, MES, ES, NQ, M2K, MYM (Sierra 1m) | **REUSED_HOLDOUT** | intraday momentum ×6 instruments, then Dhesi v3 "fresh" (unledgered) | "fresh" windows |
| 2026-09-22 → | all | **PROSPECTIVE** | 0 | — |
| < 2024-07-01 | NQ, ES, RTY, YM families | **FRESH** for the Dhesi and index families [V: no ledger entry, no artifact], **but not on disk** [V: `data/sierra/scid_snapshot_2026-09-23/` holds only 2026 contracts plus `MESU25`/`YMU25` in `tick_raw`] | 0 | — |

Findings:
- Dhesi v3's "fresh window (never seen by any Dhesi version)" is family-fresh but **dataset-group REUSED_HOLDOUT**. The CME equity-index window 2026-07 → 09 had been read by at least 6 intraday-momentum trials and 3 order-flow trials. Its +$94.59/trade (n=4) is not fresh evidence.
- Ledger gaps: `MNQ-dhesi-inversion-v3` (dev) and `MNQ-dhesi-inversion-v3-fresh` are **missing**. This cycle's forensic read should also be logged (DEVELOPMENT/REUSED_HOLDOUT, n_configs = 6). I did not write them because the ledger is read-only for this work order.
- How far back Sierra's pre-2024 NQ/ES/RTY/YM 1-minute history goes is **[U]**; it needs a metadata-only harvest check.

## 7. CANONICAL SPECIFICATION STATUS

**NOT CREATED.** Phase 5 is gated on "D4 = IMPLEMENTATION BUG and independent reproduction succeeds". Reproduction succeeded but D4 = C, so `DHESI_CANONICAL_SPEC_V1.md`, its `.sha256` and `DHESI_FRESH_VALIDATION_PROTOCOL_V1.md` were deliberately not written.

What a new-hypothesis spec must freeze, or list as discretionary, before any fresh read:
1. The stop rule: v3's side + 10-point floor + continue, or the source-closer "extreme of the retracement leg" stop. Choose **one**; no ablation selection.
2. Instrument scaling of the 30-point displacement and 10-point floor for ES/RTY/YM. These are MNQ-native points, so any scaling is a NEW INTERPRETATION. Without a frozen rule, ES/RTY/YM cannot be replication markets.
3. Still-discretionary items from the source that v2/v3 proxied: the "cleanest timeframe" choice, the volatility-expansion filter, the time-in-gap filter, stacked OB+FVG, SMT, and the runner target.
4. Roll handling for multi-day pools. The audit notes Dhesi's HTF pools straddle roll gaps (`VALIDATION_AUDIT_2026-09-22.md:77`).

## 8. POWER ANALYSIS

Inputs [V]: v3 development, 49 trades, mean $51.03, **sd $290.74**, SR 0.176/trade, median −$10, about **24.5 trades/yr** on MNQ, 1 multi-trade day in 48. The development mean is selection-inflated: v3's changes were chosen after reading this data.

One-sided α = 0.05, power 0.80, i.i.d. per trade (trades are about 1 per day, so the session-day is the natural cluster):

| True mean/trade | N needed (sd 290) | Years at 24.5/yr |
|---|---|---|
| $20 | 1,300 | **53** |
| $25 | 832 | 34 |
| $35 | 424 | 17 |
| $51 (dev point estimate) | 200 | 8 |

| Available N | Minimum detectable effect (80%) | Power if true = $20 | Power if true = $35 |
|---|---|---|---|
| 135 (NQ 2019-01 → 2024-06) | $62 | 0.20 | 0.40 |
| 355 (NQ 2010 → 2024-06, depth [U]) | $38 | 0.36 | 0.74 |

**Minimum useful expectancy:** about $20/trade, roughly 0.075R at the $269 average risk, which is what clears friction variance and Lucid pacing. On one canonical NQ series, that effect is **STRUCTURALLY_UNVALIDATABLE_AT_CURRENT_FREQUENCY**: it needs about 53 years of history. Pooling ES/RTY/YM does not rescue it without a frozen scaling rule (§7.2), and same-day index setups are correlated, so pooled N overstates effective N. A single-pass test on untouched NQ can at best confirm a **large** effect (≥ $38–62/trade) or falsify the dev estimate. It cannot establish a $20 edge.

## 9. DEFINITIVE FRESH-VALIDATION DESIGN (for the new hypothesis; frozen before any untouched read)

This design applies only after a new-hypothesis prereg (§7) is written and hashed.
- **Primary:** NQ continuous (volume-based rollover, no back-adjustment, the same Sierra convention as `MANIFEST.md`), all untouched history before 2024-07-01, one pass, unchanged frozen code. Minis and micros are not counted separately; MNQ economics are applied to the NQ price series at the $2/pt micro point value.
- **Pre-read integrity only:** hashes, row counts, missingness, contract coverage and roll dates. No outcomes.
- **Costs:** $1.00 round trip per micro, 1 adverse tick on entry, stop and flatten, gap-through stops, same-bar stop-first. Plus a 2-tick stress repricing reported alongside.
- **Primary claim, one-sided:** H1 is mean > 0 after costs. PASS requires all of the following:
  - mean > 0, and the day-clustered stationary block bootstrap (block = 20 sessions, 10,000 resamples) gives a lower 95% bound > 0;
  - positive in ≥ 60% of calendar years that have ≥ 10 trades;
  - no single trade > 25% of net PnL.
- **FAIL:** mean ≤ 0, or the bootstrap upper 95% bound < $20.
- **INCONCLUSIVE:** anything else. It is expected, given the §8 power.
- **Multiple testing:** register as a new ledger family (`dhesi_inversion`, trial count ≥ 3 already). Report DSR with the ledger's empirical trial variance.
- **Replication markets (ES/RTY/YM):** only if a scaling rule is frozen first; reported secondary, never pooled into the primary.
- **Minimum trades:** none fixed. Report achieved power at the realised N instead.

## 10. FINAL REOPEN VERDICT

**REOPEN_REQUIRES_NEW_HYPOTHESIS**

- Heimdall did **not** falsely kill Dhesi. MNQ Dhesi was never killed (it was INCONCLUSIVE), and the only real implementation defect (wrong-side stops) made v2 look slightly *better* in holdout, not worse.
- The claim "D4 flipped v2 from −$446 to +$617" (TICK_EDGE_DISCOVERY) is refuted as causal attribution. The flip comes from a post-hoc 10-point stop floor, and one trade drives most of it.
- v3 is a coherent, frozen, preregistered **new hypothesis** whose development result is positive for reasons unrelated to D4. It has no uncontaminated evidence: its "fresh" window was REUSED_HOLDOUT. At its frequency, a useful ($20) edge is structurally unvalidatable on NQ alone.

## 11. EXACT NEXT ACTION

1. **Owner decision:** whether a large-effect-only test is worth it. A single pass on untouched NQ can falsify, or confirm an effect of at least $38–62/trade; it cannot confirm $20. If no, close Dhesi as INCONCLUSIVE and structurally underpowered.
2. If yes, in this order:
   - (a) a metadata-only check of Sierra NQ history depth before 2024-07;
   - (b) write and hash `DHESI_V3_NEW_HYPOTHESIS_PREREG` from §7 and §9, choosing one stop rule;
   - (c) the ledger owner adds the missing v3 dev and "fresh" entries plus this forensic read;
   - (d) harvest, integrity-check, then one pass.
3. Correct `TICK_EDGE_DISCOVERY.md:118,158` ("FALSE KILL", "D4 flipped") through the memory owner, not by this agent.

---

## Appendix A — frozen-code cross-check (maker ≠ checker)

`d4_decompose.py` subclasses the **frozen** `InversionModelV3` with `stop_guard=False` and changes only the guard. Outputs are in `d4_decomposition_*.json` and `trades_*.csv`. [V]

| Frozen-code variant | Trades | Whole | Holdout (n) | Holdout mean | = reference? |
|---|---|---|---|---|---|
| v2 frozen class (rerun today) | 30 | −$446.375 | +$342.00 (13) | +$26.31 | = stored July log, all 30 entries and PnL |
| v2 + side, **continue** (v3 code behaviour) | 27 | −$304.88 | −$8.00 (13) | −$0.62 | yes, all entries and PnL |
| v2 + side + floor, **continue** (= `stop_guard`) | 26 | +$617.12 | +$329.50 (12) | +$27.46 | yes, all entries and PnL |
| v2 + side, **skip setup** (literal prereg text) | 25 | **−$411.88** | +$352.00 (12) | +$29.33 | — |
| v2 + side + floor, **skip setup** (literal prereg text) | 23 | **−$11.88** | +$652.00 (11) | +$59.27 | — |

Consequences:
- **No reading of the bug fix alone flips v2's sign.** Side-only gives −$304.88 with continue and −$411.88 with skip.
- The +$617 figure needs **two** non-frozen choices together:
  - the post-hoc 10-point floor (C);
  - the code's "continue to the next LTF event" rule, which departs from the prereg's own words "skip the setup" (B).
  With the prereg's literal wording, even floor + side stays negative (−$11.88).
- Holdout means move between −$0.62 and +$59.27 depending on unfrozen guard details, on 11–13 trades. That spread is itself evidence that v2's holdout sign is not robust to interpretation.

## Appendix B — artifacts (this workspace)

- `WORK_ORDER_START_UTC.txt`
- `ref_dhesi.py`, which writes `ref_{v2,v3}_{none,side,side_floor}.csv`
- `d4_decompose.py`, which writes `d4_decomposition.json`, `trades_*.csv` and `rej_*.csv`
- `UIGZtoGGPH4_agent1.en-GB.json3`, `UIGZtoGGPH4_agent1_plain.txt` (source transcript)
