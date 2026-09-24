# AGENT 2 — POST-COMMIT INDEPENDENT CERTIFICATION (2026-09-24)

**STATUS: CERTIFIED_WITH_LIMITATIONS.**
- The zero-survivor conclusion is certified.
- Limitations:
  - The Dhesi hardening PR does not exist yet, so Part K is pending.
  - F's (and partly E's) sparsity diagnosis is disputed.
  - One ledger-semantics defect.

Branch `agent2/certification-2026-09-24` (worktree `../heimdall_agent2_cert`). No Agent-1 file was modified. No Dhesi run, no purchase, no new hypothesis. Evidence scripts and outputs are in this folder.

## 1. Pinned commits

| Item | SHA |
|---|---|
| origin/main at audit | `8f70789801a2fc02b94f3159ebf3bf1b583d347c` |
| External-program commit audited | `8f70789801a2fc02b94f3159ebf3bf1b583d347c` |
| Agent 1 hardening branch `agent1/prevalidation-hardening-2026-09-24` | local only; head = `8f70789` (no hardening commits); **no PR** |

## 2. Source-recovery verdict (Part B)

Method: I read the verbatim transcripts in full (B; G by targeted extraction). **Jev** (`jev-latest`, TypeSafe citation-check pattern) was the second judge: code pulls the verbatim block at each cited timestamp and string-checks the key phrase, then one Choice asks how the section relates to the claim. Confidence below 0.8 goes to my manual reading. Files: `jev_source_check.py`, `jev_source_check_result.json`, `jev_review_resolutions.json`.

| Claim | Final | Evidence |
|---|---|---|
| B Trader Mayne is specified (3-candle swings, close-MSB, range, OB, LTF breaker, min 2:1) | **VERIFIED** | Jev supports 0.99 / 1.00 / 0.85 at 0:07:20, 0:34:52, 0:29:35 |
| G = Jay Ortani US-stock order flow; rule-sheet passes A/B/C not in video | **VERIFIED** | 0:00:00 "his entire orderflow strategy"; Bookmap 1:17:26 (Jev 0.98); TSLA/NVDA; no IPP/Silver-Bullet/FX content |
| G "Camarilla" levels | **PARTIALLY_VERIFIED** | S3/S4/R3 spoken; the word "Camarilla" is not (Jev partial 0.44) |
| PO3 10:00 hour manipulates above the 09:00-hour high | **VERIFIED** | 0:11:03 verbatim (Jev 0.81) |
| PO3 SMT NQ-vs-ES "at 0:48:12" | **PARTIALLY_VERIFIED** | cited block does not mention SMT (Jev says_nothing); SMT is stated at 0:28:59 and 1:01:03; the tie to the 10:00 sweep is INTERPRETED |
| PO3 BE when the 15m low is taken; "don't trade Mondays and Fridays" | **VERIFIED** | 1:01:56; 1:13:22 block |
| Small-cap GS gap "has to be above 100%" | **VERIFIED** | 0:18:32 verbatim (Jev 1.00); overrides 0:04:xx "typically 100%, 70%, … 1,000%" |
| Trident single 30m timeframe | **VERIFIED** | 0:02:47 (Jev partial 0.47 → manual: word split across block) |
| Trident FVG outside kill zone ignored; 2:30 counterexample; "13 or 15" | **VERIFIED** | 0:33:54, 0:33:04 (Jev 0.99 / 0.93) |

Transcript JSON hash prefixes match the recovery table. **No affected trial becomes uninterpretable.** The two partials concern a label (Camarilla, G is untested) and a citation timestamp (C's SMT rule exists elsewhere).

## 3. Family A bugfix verdict (Part C): **IMPLEMENTATION_REPAIR — not CONTAMINATED_RULE_CHANGE**

- **Rule (prereg):** sell when price trades above internal high H while the anchor is intact; the stop order sits 1 tick beyond.
- **Bug:** a harness `stop` order for a short triggers when `low <= P` (sell-stop semantics), which was already true at placement. Independently recomputed: **1,436 / 1,454 (98.8%)** first-run A1 fills were > 2 ticks on the wrong side; after the fix **0 / 1,119**.
- **Fix diff** (git `a3367a3` → `8f70789`): one token, `"stop"` → `"limit"`, plus a comment. Harness, params and prereg are unchanged. `PREREG_AMENDMENT_1.json` hashes match the current files.
- **Post-result choice test:** the prereg says "stop order", while the fix chose a limit, a different execution model. I re-ran A1 with the **literal prereg semantics** (trigger at H+1 tick, then market 1 tick adverse): n = 1,120, **−0.0028R**, CI [−0.055, +0.055]. The limit version gives −0.0009R. **Immaterial.**
- **Pre-freeze code:** git `e93c93b` (04:54 UTC, before the 04:58 freeze, when no result files existed) holds all six strategy files, and each hashes **exactly** to the PREREG_MANIFEST values. No post-result code tuning in B–F.

## 4. Independent trade replication (Part D)

Own engine (`a2_engine.py`, imports nothing from `external_strategies`), unit-safe comparator (`compare_trades.py`):

| Trial | Built | n A2 / A1 | Matched | Field mismatches (entry, stop, exit time, reason, R) | Mismatch rate |
|---|---|---|---|---|---|
| A1 fix1 MNQ | blind from prereg | 1,119 / 1,119 | 1,119 | 0 | **0.0%** |
| A2 fix1 MNQ | blind | 857 / 857 | 857 | 0 | **0.0%** |
| A3 fix1 MNQ | blind | 1,039 / 1,039 | 1,039 | 0 | **0.0%** |
| A4 MNQ | blind | 987 / 987 | 987 | 0 | **0.0%** |
| D4 MNQ / ES / XAU | blind (chain rule from prereg'd docstring) | 295 / 290 / 458 | all | 0 | **0.0%** |
| B4 MNQ | blind | 54 / 70 | 4 | — | **disagree** |
| B4 MNQ | diagnostic (Agent 1's disclosed definitions, own code) | 70 / 70 | 70 | 0 | 0.0% |
| F1 EURUSD | blind | 102 / 24 | 9 | 8 entry | **disagree (4× frequency)** |

Every trade was compared, which covers the 10-winner / 10-loser / 10-random sample for all trials. Published metrics reproduce: A1 −0.001 [−0.053, +0.057]; A2 −0.051 [−0.107, +0.008]; A3 −0.010; A4 +0.013; D4 MNQ +0.151 [−0.036, +0.347].

**Fidelity findings:**
- **(i) B4:** the prereg row says expiry = "30 HTF bars / HTF close beyond range low / target first". Agent 1's `ob_limit` path applies only the 30-bar expiry. With the prereg-faithful expiry, B4 = n 43, **−0.741R**, CI [−0.92, −0.49], still ROBUSTLY_REJECTED.
- **(ii) B4 placebo:** random entries with identical side, stop, target and +2R BE average **−0.021R** (5–95% of rep means [−0.32, +0.39]). B4's −0.64R is **worse than random**: its limit fills are adversely selected. This is not a management artifact.
- **(iii) Undefined rules:** D's "chain count ≤ 2" and B's OB construction are implementation-defining but defined only in code, not in the prereg text.

## 5. D4 MNQ fragility (Part E): **FRAGILE + REGIME_DEPENDENT + TAIL_DEPENDENT — supported**

| Test | Agent 2 |
|---|---|
| Full mean R | +0.151 (CI [−0.036, +0.347]; median −0.383) |
| Drop top 5 | +0.014 |
| Drop top 1% | +0.065 |
| Top-5 share of ΣR | 91% |
| Bull regime (prior close > 50-session SMA) | +0.257 (n 192) |
| Bear regime | −0.047 (n 103) |
| One-bar delay | +0.110 (n 274); drop-top-5 −0.036 |
| Cost ×1.5 | +0.141 |
| Stop-slip ×3 | +0.131; drop-top-5 −0.003 |
| Frictionless | +0.172 |
| ES replication | −0.054 |
| XAU replication | −0.073 |

**Not promotable.**

## 6. Multiple testing / ledger (Part F)

- **Counts.** 66 EXT8 ledger entries. The true composition is:
  - **58 valid trials**;
  - **4 executed-but-invalid looks** (A1/A2/A3 MNQ, A1 YM first runs);
  - **4 correction markers**.
  "62 valid trials" is **wrong wording**: 62 = looks at data (58 + 4 invalid). Agent 1's K = 62 for DSR is correct as a look count.
- **Ledger defect.** The 4 original entries still carry live verdicts (3× ROBUSTLY_REJECTED, 1× INCONCLUSIVE). Only a separate `-INVALIDATED` marker voids them, so any consumer filtering on `verdict` will count the invalid runs as rejections. **Required:** ledger readers must honour `-INVALIDATED` markers. Documented here; the ledger was not edited (append-only, Agent-1-owned).
- **Completeness.** Prereg'd configs = 5 (A) + 4 + 4 + 12 + 24 + 9 = 58 = the valid trials. No trial is omitted and none was renamed. Chain linkage is verified.
- **Undercounting.** B/C/F/A (sweep → reversal / FVG families) overlap mechanically with `dhesi_inversion` and `casper_fvg` but are registered as new `ext8_*` families. Deflation should also use the global count.

| Statistic | Agent 1 | Agent 2 recomputed (own code) |
|---|---|---|
| Holm min adj p (valid) | 1.0 | **1.0**; raw min p 0.029 (D4 MNQ); 53 of 58 in the family (n ≥ 3) |
| BH min q | 1.0 | **1.0** |
| White RC, CME | 0.43 | **0.43** on the full session calendar (0.45 on union-of-trade-days) |
| White RC, FX/XAU | 0.97 | **0.97** (K = 4 only; E/F rows n < 30 excluded) |
| DSR, best n ≥ 30 | ≤ 0.08 | **0.082** at K = 62; **0.019** at the global ledger K = 433 |

- **Defect (non-material).** `white_reality_check` is documented as using "session days (0 on no-trade days)" but builds on the union of trade days. The recompute shows p moves by < 0.03.

## 7. Execution audit (Part G)

**No family was falsely rejected for costs.** Every ROBUSTLY_REJECTED trial is negative *gross*: A2 −0.039, B1 −0.415, B4 −0.758, D1 XAU −0.072, D3 XAU −0.059. Pooled gross vs net by family:

| Family | Gross | Net | Cost |
|---|---|---|---|
| A | −0.002 | −0.009 | — |
| B | −0.249 | −0.254 | — |
| C | +0.095 | +0.081 | — |
| D | +0.012 | −0.048 | — |
| F | −0.105 | −0.140 | 0.035R (up to 0.25R per row, 5–10 pip stops) |
| E | +0.731 | +0.281 | **0.45R per trade** |

- **F:** EXECUTION_SENSITIVE, gross ≤ 0, no hidden edge.
- **E:** gross is carried by two or three 20R hits (E1 gross drop-top-1 +0.85, median −1.0). It should be labelled **EXECUTION_SENSITIVE + TOO_SPARSE** (Agent 1 labels only TOO_SPARSE).
- **Cost model** (futures +1 tick market/stop, 1-tick limit trade-through, gap fills at open; FX raw-ECN spreads + 0.2 pip + $7/lot): reasonable, not harsh.
- **Deployability:** Lucid is CME-only, so an E/F result would need repricing on CME FX/gold futures.

## 8. Frequency fidelity (Part H) — counts only, no PnL, nothing loosened

- **C PO3:** NQ sweeps its 09:00-hour extreme during 10:00–11:00 on **477/515 days (93%)**. The creator's "most days" is true of the sweep. The **stated SMT** condition holds on 50 days, a **24.5/yr ceiling**; Agent 1 gets 22/yr. → **CREATOR_CLAIM_UNSUPPORTED** for the SMT-gated setup. Mechanization is not at fault.
- **E Trident (EURUSD dev)** funnel per year:

  | Stage | Per year |
  |---|---|
  | FVG in window | 200 |
  | Doji | 55 |
  | Wick through CE | 19 |
  | Body above FVG top | 9 |
  | **Confirmation** | **6.0** |
  | EMA stack | 3.7 |
  | EMA200 | 2.0 |

  The core pattern runs at **~6/yr = the creator's 6–8**. The ~3× cut comes from applying the EMA context as **hard filters**, although the source calls it "preferred" / a "tell". → **mostly WRONG_MECHANIZATION (over-strict)**, with the doji threshold as SOURCE_DISCRETION.
- **F MMXM:** a blind build of the same prereg sentence yields **102 vs 24** EURUSD setups. Agent 1's code adds a rule that is **not in the prereg**: a first PDH/PDL run *outside* a kill zone voids the day, and with the FX day starting 17:00 NY, Asia runs kill most days. Also zero = lowest low, and a 60-bar swing lookback. → **WRONG_MECHANIZATION / undisclosed assumption** for the sparsity claim. The PnL sign is unaffected: my build is negative too.

## 9. G / H data decision (Part I)

- **G — DO_NOT_BUY.**
  - The source gives no quantitative tape/absorption thresholds (BLOCKED_SOURCE for the detector), so one month of `XNAS.ITCH` MBO ($26.72) cannot define the hypothesis.
  - ITCH is a single venue, not the consolidated tape of TSLA/NVDA.
  - Equities are not tradable on Lucid.
- **H — DO_NOT_BUY.**
  - The $28 `XNAS.ITCH ohlcv-1d` has no point-in-time float, cap, shortability/borrow, halts or premarket volume.
  - It is Nasdaq-listed only, missing NYSE American/OTC runners.
  - So it cannot apply the universe filter (float 1–50M, cap < $100M) or model shortability: **not decisive**.
  - Not tradable on Lucid.

## 10. 8-family certification

| Fam | AGENT1_VERDICT | AGENT2_VERDICT | Agree? | Evidence |
|---|---|---|---|---|
| A Liquidity trap | INCONCLUSIVE (A2 ROBUSTLY_REJECTED) | INCONCLUSIVE (A2 ROBUSTLY_REJECTED) | **YES** | 4 trials 100% replicated; ≈0 gross over ~1,000 trades; prereg-literal order type same result |
| B Trader Mayne | REJECTED_IMPLEMENTATION_NOT_FAMILY | REJECTED_IMPLEMENTATION_NOT_FAMILY | **YES** | B4 reproduced; prereg-faithful expiry worse (−0.74R); entries worse than random placebo; mechanization-sensitive definitions |
| C PO3 / 50% | INCONCLUSIVE (TOO_SPARSE) | INCONCLUSIVE (TOO_SPARSE) | **YES** | frequency ceiling set by the source's SMT rule |
| D Little Rizzy | INCONCLUSIVE (XAU F-short ROBUSTLY_REJECTED; H BLOCKED_DATA) | INCONCLUSIVE (same; H = BLOCKED_DATA and structurally < 10 events) | **YES** | D4 295/295 replicated; fragility battery reproduced |
| E Trident | INCONCLUSIVE (TOO_SPARSE) | INCONCLUSIVE (TOO_SPARSE + EXECUTION_SENSITIVE) | **YES on state; diagnosis DISPUTED** | sparsity mostly from hard EMA filters, not only source discretion |
| F MMXM / OTE | INCONCLUSIVE (TOO_SPARSE, EXECUTION_SENSITIVE) | INCONCLUSIVE | **YES on state; sparsity DISPUTED** | blind build 4× more setups; undisclosed "run outside KZ voids day" rule |
| G SQEtBHOJW6I | BLOCKED_DATA (+ BLOCKED_SOURCE thresholds) | BLOCKED_DATA + BLOCKED_SOURCE | **YES** | verbatim identity verified; DO_NOT_BUY |
| H Small-cap shorts | BLOCKED_DATA | BLOCKED_DATA | **YES** | PIT float/cap/borrow absent; DO_NOT_BUY |

- **Survivors confirmed:** 0.
- **Survivors rejected:** n/a (none claimed).
- **SURVIVING_RESEARCH_CANDIDATE:** none.

## 11. Dhesi hardening PR review (Part K): **PENDING — no PR exists**

Review checklist fixed now:
- D3 saves *both* engine ledgers in the same one-shot run;
- D4 rejects non-finite **and negative** volume (in the integrity gate as well as the validator);
- a diff shows no strategy code or constant changed;
- the spec hash is preserved unless its bytes change;
- the new infrastructure hashes are recomputed;
- the ledger test pins a frozen historical snapshot while the live ledger stays dynamic;
- no reserved read;
- synthetic dry run re-executed (`../agent2_external_strategy_audit_2026-09-24/dhesi_synthetic_dryrun/dryrun.py`).

Any failure → REQUEST_CHANGES.

## 12. Contamination event ruling (Part L)

- **CE-2026-09-24-A2-01 = METADATA_ONLY_NON_OUTCOME_EXPOSURE** (final).
- Only the date column was extracted and no price was parsed. The files are deferred-contract daily bars, not the reserved 1-minute continuous dataset, which is **not** declared contaminated.
- **Isolation done:** `ESM26/ESU26/ESZ26/NQZ26-CME.dly` were **moved** (not deleted) from `C:/SierraChart/Data` to `C:/SierraChart/QUARANTINE_pre2024_dly_2026-09-24/`. Sierra was not running. SHA-256 is unchanged (962da7ca… / a127e4dc… / c36d1137… / 3ffac094…).
- Note: Sierra re-downloads a `.dly` if one of those symbols is charted. Re-check the directory before the harvest.

## 13. Test results (pinned `8f70789`)

- `tools/check_core_purity.py`: OK.
- EXT8 tests: **18 passed**.
- Full `pytest tests`: **232 passed, 1 skipped, 3 failed**:
  - `test_connectors_live` and `test_history_real`: known OKX network;
  - `test_gates_split::test_ledger_integrity_and_reference_numbers`: disclosed by Agent 1; owner decision; belongs in the hardening PR with snapshot semantics.

## 14. Remaining disputes

1. F sparsity attributed to source discretion vs an undisclosed mechanization rule (Agent 2: mechanization).
2. E sparsity: hard EMA filters vs source discretion (Agent 2: mostly mechanization).
3. B4 expiry deviates from the prereg (verdict unaffected).
4. Ledger `-INVALIDATED` semantics; "62 valid" wording.
5. White RC calendar implementation (immaterial).

None changes a terminal state. All are fidelity and accounting issues.

## 15. READY_FOR_DHESI_HARVEST: **YES**

The Sierra download may proceed: owner GUI, metadata-only handling, charts not scrolled; re-check `C:/SierraChart/Data` for new pre-2024 `.dly` first.

**Run `dhesi_v3_harvest_integrity.py` only after the hardening PR is merged**, so gate 1 includes the volume check. The Dhesi run itself is still NOT authorized.

## 16. Exact next action

Agent 1 opens the pre-validation-hardening PR (D3 + D4 + ledger-test snapshot semantics) against `main`. Agent 2 then reviews it under §11.
