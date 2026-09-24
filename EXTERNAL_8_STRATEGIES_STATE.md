# External 8-Strategy Research Program — State (2026-09-24)

**STATUS: COMPLETE (development phase).** 8/8 families have a terminal state. **Surviving research candidates: 0.**
No live trading, no paid data, no fresh-validation data consumed. Code/artefacts: `workspace/external_strategies/`.

## 1. State reconciliation
- Read: HEIMDALL_MEMORY.md, AGENT_HANDOFF.md, AGENTS.md, CLAUDE.md, TOOLING.md, MEMORY_SUPERSESSION, DHESI_V3
  prereg + record reconciliation, trials ledger, Sierra MANIFEST, rule sheet, owner-supplied report zip.
- Dhesi firewall: pre-2024-07-01 NQ/MNQ/ES/MES is **not on disk** and was not fetched; `load_futures` asserts it.
- Every CME window on disk (Databento 2024-07..2026-06, Sierra 90d) is already REUSED → all futures results are
  DEVELOPMENT/diagnostic only. FX/XAU (HistData, first Heimdall use): DEV 2022–2024 used; **2025-01..2026-08 SEALED**.
- `Heimdall.md` does not exist in the repo (only `HEIMDALL_MEMORY.md`); noted, not a blocker.

## 2. Source recovery (details: `EXTERNAL_8_STRATEGIES_SOURCE_RECOVERY.md`)
All 8 primary transcripts retrieved (5 creator-uploaded, 3 auto). Two rule-sheet conclusions overturned:
**coBMd1vk2Lo** is fully specified (was "all MISSING"); **SQEtBHOJW6I** is Jay Ortani's stock order-flow strategy —
the rule sheet's three reconstructions (IPP / 2 PM Silver Bullet / ICT-FX) and their five "examples" are not in the video.

## 3. Eight-family coverage matrix
| Fam | Video | Setups | Implemented trials | Terminal family state |
|---|---|---|---|---|
| A | DAnXM7C16h0 | sweep short, sweep long | 4 (+YM replication) | TESTED_MECHANIZED_INTERPRETATION — no signal |
| B | coBMd1vk2Lo | HTF-range long/short, breaker, OB-limit | 4 | TESTED_MECHANIZED_INTERPRETATION — H4 variants robustly rejected |
| C | HNuRp9Z1bMs | PO3 short, bullish mirror | 4 | TESTED_MECHANIZED_INTERPRETATION — too sparse |
| D | AVVM-FyewLg | F short, G long, H crash-bottom | 12 (4 × MNQ/ES/XAU) | TESTED_MECHANIZED_INTERPRETATION (H: BLOCKED_DATA) |
| E | ADnslyKOwFE | long, gold exception, short mirror | 24 (4 × 6 instruments) | TESTED_MECHANIZED_INTERPRETATION — too sparse |
| F | IB-fyWI5j8w | sell, buy mirror, OTE (2nd-leg Silver Bullet not built) | 9 (3 × 3 pairs) | TESTED_MECHANIZED_INTERPRETATION — too sparse |
| G | SQEtBHOJW6I | Market-DNA order flow; retired passes A/B/C | 0 | BLOCKED_DATA (+ BLOCKED_SOURCE for thresholds) |
| H | 52ZsDmFHqyY | Gap-Up Short, Bounce Short, First Red Day | 0 | BLOCKED_DATA |

## 4. Exact interpretations tested
Frozen per family in `*/PREREGISTRATION.md`; hash manifest `_program/PREREG_MANIFEST.json`
(aggregate SHA-256 `067f073c3857420414139efa599b0efda53eff57b783a3d70829cec5d43c2bcc`), frozen before any PnL.
Post-freeze change: one BUGFIX only (`_program/BUGFIX_A_ENTRY.md`, `PREREG_AMENDMENT_1.json`), no rule change.

## 5. Data used
| Data | Window | Status | Sanity |
|---|---|---|---|
| Databento MNQ/ES 1m (Panama back-adjusted at 8 quarterly rolls) | 2024-07-01..2026-06-30 | REUSED | 707k rows, 0 NaN (memory Milestone 3) |
| Sierra YM 1m (roll 2026-09-14 00:00 UTC adjusted) | 2026-06-24..2026-09-21 | REUSED | 85,742 rows (MANIFEST) |
| HistData 1m BID: EURUSD GBPUSD USDJPY USDCAD NZDUSD XAUUSD | 2022-01..2026-08 (dev 2022–24) | NEW, free | 1.61–1.69M rows each, 0 NaN, 0 low>high; weekday gaps>1h 553–586 (XAU 1,414: daily break) |
HistData timestamps = EST without DST (vendor documentation), converted to UTC. Dukascopy was tried first
(verified working, but throttled to ~1 of 3 requests) and abandoned.

## 6. Implementation / fidelity
- Shared harness (`common/harness.py`): ET-anchored bars (DST-tested), fill engine with conservative same-bar
  rules, cost models; 18 tests pass (`common/test_harness.py`, `common/test_families.py`).
- Fidelity gate (signals only, before PnL): 0 geometry violations after fixing a sign error in the checker
  itself; 0 truncation-lookahead mismatches across all primary configs.
- **Frequency-fidelity gaps** (pre-PnL): Trident ~1 setup/yr/pair vs creator's 6–8; PO3 ~20/yr vs "most days".
  Not loosened (thresholds were frozen); recorded as a mechanization-vs-discretion gap.
- **Bug found post-PnL, fixed**: Family A entry used sell-stop semantics — 98.8% of A1 fills were on the wrong side
  of the trigger. First-run A1/A2/A3/YM = INVALID_IMPLEMENTATION; corrected `_fix1` trials registered as new looks.

## 7. Development results (net of modelled costs; R = net / initial risk)
| Trial (best-evidence rows) | n | mean R | 95% cluster CI | frictionless R | verdict |
|---|---|---|---|---|---|
| A1 fix1 MNQ (k=1) | 1,119 | −0.001 | [−0.054, +0.057] | +0.015 | INCONCLUSIVE (≈0; edge > +0.06R excluded) |
| A2 fix1 MNQ (k=2) | 857 | −0.051 | [−0.108, +0.007] | −0.036 | ROBUSTLY_REJECTED |
| A3 fix1 MNQ (split) | 1,039 | −0.010 | [−0.064, +0.050] | +0.004 | INCONCLUSIVE |
| A4 MNQ (close-confirm) | 987 | +0.013 | [−0.038, +0.073] | +0.023 | INCONCLUSIVE |
| A1 fix1 YM | 125 | +0.024 | [−0.159, +0.227] | +0.047 | INCONCLUSIVE |
| B1 H4→M15 | 52 | −0.435 | [−0.703, −0.111] | −0.419 | ROBUSTLY_REJECTED |
| B4 H4 OB-limit | 70 | −0.638 | [−0.830, −0.413] | −0.628 | ROBUSTLY_REJECTED |
| B2 H1→M5 / B3 D→H1 | 140 / 17 | −0.123 / +0.799 | wide | — | INCONCLUSIVE |
| C1..C4 PO3 | 25–42 | −0.05..+0.17 | all straddle 0 | similar | INCONCLUSIVE (TOO_SPARSE) |
| D1 F-short 1h XAU / D3 XAU | 498 / 330 | −0.170 / −0.124 | upper < +0.04 | −0.067 / −0.030 | ROBUSTLY_REJECTED |
| D4 G-long 1h MNQ (best of program) | 295 | +0.151 | [−0.036, +0.351] | +0.172 | INCONCLUSIVE — FRAGILE (below) |
| D4 G-long 1h ES / XAU | 290 / 458 | −0.054 / −0.073 | straddle | ≈0 | INCONCLUSIVE |
| E1 Trident long, pooled 6 instr. | 22 | +1.305 (median −1.23; top trade = 69%) | [−1.46, +4.46] | — | INCONCLUSIVE (TOO_SPARSE) |
| E4 Trident short mirror, pooled | 16 | −1.316 (0 wins) | [−1.47, −1.20] | — | INCONCLUSIVE (n<30) |
| F1/F2/F3 MMXM pooled 3 pairs | 67 / 58 / 66 | −0.015 / −0.249 / −0.170 | straddle | — | INCONCLUSIVE |
Full table: `EXTERNAL_8_STRATEGIES_TEST_MATRIX.csv`; per-family `*/RESULTS.md`; trade logs `*/results/`.
Claim check: Trident's stated ~90% win rate vs 3 wins in 22 mechanized longs (14%).

## 8. Execution realism
Futures: +1 tick on market/stop entries and stop exits, 1-tick trade-through for limits, gap-through fills,
commissions MNQ $1 / ES $3.50 (confirmed), YM $3.50 (assumed). FX: modelled spread + 0.2 pip slip + $7/lot (all
ASSUMPTIONS). Frictionless re-simulation (all costs = 0) flips the sign of 5 of 62 rows: D3 ES (−0.037→+0.003)
and D4 XAU (−0.073→+0.025), both ≈0 either way, and three small FX MMXM/Trident rows (F2 GBPUSD n=26
−0.158→+0.197, F3 GBPUSD n=28 −0.027→+0.148, E2 USDJPY n=7 −0.103→+0.192) whose CIs are far too wide to call
an edge. FX costs (modelled, not measured) are 0.1–0.4R per trade on 10–20-pip stops, so for F the cost model
matters; that is recorded as EXECUTION-SENSITIVE + TOO_SPARSE, not as a hidden edge. Everywhere else the failure
class is NO_SIGNAL or TOO_SPARSE. Deployability: B holds multi-day (conflicts with Lucid
16:45 flat); E/F are FX (not tradable on Lucid); G/H are equities (not tradable on Lucid).

## 9. Multiple-testing ledger
62 valid trials + 4 invalid looks, all in `data/trials_ledger.json` (append-only, chain verified; ids `EXT8-*`).
Holm and BH: every adjusted p = 1.0. DSR (n_trials 62, empirical SR variance 0.0305): max 0.46 (F3 USDJPY, n=11);
every n ≥ 30 trial ≤ 0.08. White Reality Check (stationary bootstrap, daily R): CME group p = 0.43 (best D4 MNQ),
FX/XAU group p = 0.97. PBO/CSCV not computed: no candidate set to select from (method would be ceremonial).
**Side effect:** the new CME trials overlap the shared 60/40 MNQ holdout (now 93 configs), raising its empirical SR-trial
variance from 0.00345 to 0.0172. `tests/test_gates_split.py::test_ledger_integrity_and_reference_numbers` pins the
old value and now fails — the ledger doing its job. Test NOT edited; owner decision (re-pin, or exclude
post-2026-09-23 ids from the snapshot assertion).

## 10. Robustness / red team (D4 MNQ, the only near-candidate; descriptive, it failed the candidate bar)
drop top 5: +0.151 → +0.014R · drop top 1%: +0.065R · bull days +0.257R vs bear days −0.047R · one-bar delay
+0.083R · cost ×1.5 +0.141R · stop slip ×3 +0.131R · same rule on ES −0.054R, XAU −0.073R → **FRAGILE,
regime- and tail-dependent**: a long-only trend proxy harvesting the 2024–26 NQ bull run.

## 11. Terminal verdict for every setup
| Setup | Verdict | Diagnosis |
|---|---|---|
| A sweep-short / sweep-long | INCONCLUSIVE (A2 variant ROBUSTLY_REJECTED) | NO_SIGNAL: ≈0R before costs over ~1,000 trades; source discretion (level choice, news, HTF logic) untested |
| B long / short (breaker) | REJECTED_IMPLEMENTATION_NOT_FAMILY | H4 mechanizations robustly negative (~10% win vs 2R+ targets); D/H1 too sparse |
| B OB-limit (direct entry) | REJECTED_IMPLEMENTATION_NOT_FAMILY | robustly negative |
| C bearish PO3 / bullish mirror | INCONCLUSIVE | TOO_SPARSE (25–42 trades/2y) + frequency-fidelity gap |
| D-F downtrend short | INCONCLUSIVE (XAU variants ROBUSTLY_REJECTED) | NO_SIGNAL / WRONG_MARKET for gold |
| D-G uptrend long | INCONCLUSIVE | FRAGILE, REGIME_DEPENDENT, TAIL_DEPENDENT |
| D-H crash-bottom | BLOCKED_DATA | needs multi-decade monthly index history; < 10 events (TOO_SPARSE by nature) |
| E Trident long (+gold exception) | INCONCLUSIVE | TOO_SPARSE (22 trades/3y across 6 instruments); lottery-shaped |
| E Trident short mirror | INCONCLUSIVE | 16 trades, 0 wins; source barely supports shorts |
| F MMXM sell / buy, OTE | INCONCLUSIVE | TOO_SPARSE (58–67 pooled/3y), centred ≈0 to negative |
| F Silver-Bullet second leg | INCONCLUSIVE | not implemented (declared scope cut) |
| G Market-DNA order flow | BLOCKED_DATA | needs historical full-depth US equity book + tape |
| G Pass A / B / C | BLOCKED_SOURCE | not present in the video — retired |
| H Gap-Up Short / Bounce Short / FRD | BLOCKED_DATA | needs PIT float/cap, pre-market, halts, borrow |

## 12. Surviving research candidates
**None (0).** No interpretation met the preregistered CANDIDATE bar; nothing survives multiple-testing correction.

## 13. Cross-source mechanisms (reporting only; no new hypotheses created)
- *Liquidity sweep → reversal* (A, B-breaker, C, F): four independent mechanizations, none positive with
  evidence; A (largest sample) is ≈0 before costs. The phenomenon is **not supported** as mechanically capturable here.
- *Retrace into imbalance / FVG CE / OTE* (C inversion, E, F): all sparse; none positive with evidence.
- *Session-timed manipulation* (C 10:00 ET, E London KZ, F kill zones): no support.
- *Trend continuation* (D-G on MNQ): the only positive tilt, and it is just bull-market beta.
Consistent with Heimdall's prior record: the publicly narrated structure reproduces mechanically at ≈0 edge,
while the frequency the creators claim lives in discretion the transcripts do not specify.

## 14. Data / source blockers (quotes 2026-09-24, Databento `metadata.get_cost`, nothing purchased)
| Need | Provider / dataset | Window | Quote | Decides |
|---|---|---|---|---|
| G full-depth book | XNAS.ITCH MBO, NVDA/TSLA/AMD | 1 month | $26.72 | whether an absorption/refill detector is even definable |
| G depth (10 levels) | XNAS.ITCH MBP-10, same | 1 month | $18.65 | same, cheaper |
| G tape | XNAS.ITCH trades, same | 2023-01..2026-09 | $174.50 | trade-side aggression only |
| H daily bars | XNAS.ITCH ohlcv-1d, all symbols | 2019..2026-09 | $28.00 | FRD price-pattern frequency/fade (no float/borrow; Nasdaq-listed only) |
| H intraday | XNAS.ITCH ohlcv-1m, all | 2019..2026-09 | $1,428.29 | GS intraday (Nasdaq only) |
| H intraday consolidated | EQUS.MINI ohlcv-1m, all | 2023-06..2026-09 | $522.25 | GS intraday, all venues |
| H float / cap / borrow | not offered by Databento | — | UNVERIFIED (no quote) | universe + short feasibility |
Cheapest decisive subset: $28 (H-FRD price-only prototype). Neither G nor H can trade on Lucid (CME only).

## 15. Fresh validation plans
No survivor, so no validation data is authorized for consumption. Reserved and untouched:
- FX/XAU 2025-01-01..2026-08-31 (HistData, sealed) — would serve E/F only if a future, newly preregistered
  hypothesis earned it; running E/F on it now would add ~15 trades per config (still underpowered).
- If the owner nonetheless wants D4 (MNQ uptrend long) followed: PROSPECTIVE forward paper from 2026-09-24,
  ≥ 150 trades (~6 months at ~145/yr), PASS = mean ≥ +0.10R net with 95% CI lower > 0 AND positive in a
  bear-regime subset (≥ 40 trades with MNQ < 50-day SMA); FAIL = mean ≤ 0 or bear subset ≤ 0; else INCONCLUSIVE.
  Execution gate: live-fill slippage ≤ 2 ticks median; risk gate: multi-day holds are incompatible with
  Lucid's 16:45 flat, so it would need an intraday-flat variant = a NEW hypothesis. **Not recommended.**

## 16. Artefacts + hashes
See `EXTERNAL_8_STRATEGIES_MASTER_LEDGER.json` (all trial rows, RC, DSR), `EXTERNAL_8_STRATEGIES_TEST_MATRIX.csv`,
`EXTERNAL_8_STRATEGIES_SOURCE_RECOVERY.md`, `workspace/external_strategies/_program/ARTEFACT_HASHES.json`.

## 17. Next single action
Owner decision on the pinned-reference test (`test_gates_split::test_ledger_integrity_and_reference_numbers`),
then close this program. No strategy from these eight sources warrants further data spend; the $28 Nasdaq daily-bar
quote for H-FRD is the only cheap follow-up, and it cannot be traded on Lucid.
