# AGENT 2 — EXTERNAL STRATEGY AUDIT (checker / falsifier / data governance)

- Date: 2026-09-24 (UTC start: `WORK_ORDER_START_UTC.txt`).
- Role: independent checker. **No Agent-1 file was edited. No pre-2024-07-01 price was read. No live trade. No paid data.**
- Status: **CHECKPOINT.**
  - The Dhesi side is audited and not runnable yet.
  - The eight-strategy side has no candidates to check, since Agent 1 has produced sources and data tools only.
- **WINNER: NONE.**

Companion artifacts in this folder:
- `DHESI_V3_FIREWALL_AND_BINDING_AGENT2.md`: hash binding, spec↔code check, firewall, contamination disclosure.
- `AGENT2_EXTERNAL_STRATEGY_LEDGER.json`: checker-side trial count.
- `AGENT2_DATA_GAPS.md`.
- `AGENT2_SURVIVOR_REPLICATIONS/`: empty, with the replication protocol fixed in advance.
- `SOURCE_EVIDENCE_HASHES.sha256`, `SIERRA_PRE2024_DLY_HAZARD.sha256`.
- `dhesi_synthetic_dryrun/`.

---

## 1. Dhesi readiness

- All 5 canonical artifacts and the 6 frozen code files re-hash exactly. Spec ↔ frozen code ↔ reference engine agree rule by rule; **no ABORT condition**.
- Three pre-run defects are recommended to Agent 1. They are plumbing only; none changes the strategy.
  - **D3:** the reference trades are not persisted, so a disagreement could not be itemised without a forbidden rerun.
  - **D4:** integrity gate 1 skips volume NaN, while the frozen code raises on it.
  - **D5 (low):** freeze the Sierra→parquet converter. Gate 3 already catches a ±1-minute stamp shift: a shifted series scores 45.7% vs the required 95%.
- Synthetic dry run: see §1a.

### 1a. Synthetic pipeline dry run (Agent 2, no market data)

`dhesi_synthetic_dryrun/dryrun.py` generates a zero-drift random walk on the untouched-window calendar (2011-09-18 → 2024-10-01, CME hours, NQ-like start 2300, ≈1.3% daily vol, 0.25 tick). It then applies the validator's own `truncate_untouched` and burn-in, runs the **frozen** `InversionModelV3` and the validator's `reference_run`, and scores the result with the validator's `evaluate`.

Result (seed 1, `dryrun_result.json`; VERIFIED):

| Check | Result |
|---|---|
| Scale | 4,602,300 1-minute rows, 3,315 evaluated sessions, last row 2024-06-28 20:59 UTC (hard cut works) |
| Runtime | frozen code 1,912 s + reference 1,275 s = **53 min total**. The one-shot run is feasible on this machine. |
| Frozen vs reference | 231 vs 231 trades; **0 mismatches** on entry_ts, exit_ts, side, entry, stop, TP1, exit price, contracts, PnL (13 synthetic years of never-seen structure, incl. DST transitions, low price levels, gap stops) |
| Null control (zero-drift walk) | mean −$11.36/trade, win 41.6%, one-sided bounds lo95 −$43.67 / hi95 +$20.46 → **FAIL** (hi95 < μ_min $30). The pipeline does not manufacture a PASS from noise. |

A single seed is one null draw. It shows the machinery works; it is not a false-positive-rate estimate (that would need many seeds at about 53 min each).

## 2. Reserved-data integrity

- No eight-strategy code read reserved data. Agent 1's `_data_tools` pull spot FX/XAU from Dukascopy/HistData, 2022→2026: **PASS**.
- **Hazard:** Sierra `C:/SierraChart/Data/{NQZ26,ESZ26,ESM26,ESU26}-*.dly` hold deferred-contract daily bars back to 2021-09. They are hashed and quarantine is recommended.
- **CONTAMINATION_EVENT CE-2026-09-24-A2-01 (self-reported):**
  - Agent 2's timestamp probe loaded those `.dly` bytes to read the date column.
  - No price was parsed, computed or displayed.
  - Deferred-contract daily series, not the Dhesi NQ continuous 1-minute series.
  - Assessed zero-information; the **owner adjudicates**.

## 3. Source-fidelity audit (Part D)

Evidence base, hashed in `SOURCE_EVIDENCE_HASHES.sha256`:
- the rule sheet (5e307c80…3584);
- the 8 research reports (zip ecd90a4d…6735);
- the **8 verbatim auto-caption transcripts** Agent 1 fetched at 08:21. These are primary and **outrank** the rule sheet where they conflict. The rule sheet itself says several reports were "non-verbatim audiovisual" reconstructions.

**Two major rule-sheet errors found by reading the verbatim transcripts:**
1. **B (`coBMd1vk2Lo`) is not "[MISSING]"**. The full transcript exists and is the most mechanical of the eight; see B below.
2. **G (`SQEtBHOJW6I`) is misidentified.** The rule sheet offers three conflicting guesses: IPP, T-Rex/2 PM Silver Bullet, and generic ICT FX. The verbatim transcript is **Jay Ortani's large-cap US stock tape-reading / order-flow playbook** (TSLA, NVDA, AMD, ARM; Bookmap; same-day options). All three rule-sheet alternatives are **invalidated**, and none may be mechanized as "G".

Heading key for every family: SOURCE FACTS = [STATED] with timestamp. MISSING. AGENT-1 ASSUMPTIONS: none exist yet, since no mechanization has been submitted. ASSUMPTIONS NOT SUPPORTED: pre-registered now, so Agent 1 can be held to them. AMBIGUITIES: implementation-defining; the choices marked [k] multiply the interpretation count in the ledger.

### A — Liquidity Trap (`DAnXM7C16h0`, timestamped 3rd-party transcript + verbatim captions)
- **SOURCE FACTS:**
  - "Buy below lows, sell above highs" (10:06).
  - No buy until the selected low is taken (24:43); no sell until the high is taken (25:23).
  - Entry market "as soon as the high is spiked out" (46:33–47:09).
  - Stop beyond the swept extreme, "a tick or two" (09:07, 16:54, 31:19).
  - Target opposing liquidity; internal first, external larger (28:20, 31:34).
  - No fixed R (33:20). Partials 50%, or 70% when confident (32:08).
  - 5m normal execution, 1m optional (42:32, 47:04). NY time, entries after the 09:30 open (42:16–43:20).
  - No entry before news; wait 2–4 min after (07:24).
- **MISSING:**
  - which swing is "respected" and the lookback;
  - minimum penetration and whether a reclaim is needed;
  - HTF bias rule;
  - session end, news tiers, sizing, expiry/re-entry.
- **ASSUMPTIONS NOT SUPPORTED:**
  - requiring a close back inside as the **base** trigger (the source's base trigger is the intrabar spike; the 5m close is an *add* condition, 26:32);
  - any fixed-R target;
  - FVG/OB entry refinement (explicitly rejected, 08:14).
- **AMBIGUITIES (9):**
  1. swing algorithm;
  2. internal vs external low selection;
  3. HTF bias/target definition;
  4. trigger: intrabar breach vs 5m close [2];
  5. stop buffer 1 vs 2 ticks [2];
  6. partial: none vs 50% [2] (70% "when confident" is discretionary and excluded);
  7. session bounds;
  8. news blackout source;
  9. 5m vs 1m execution (5m fixed as "normal").
- Interpretations ≥ **8**.
- **Overlap:** mechanically close to the Dhesi `S0` sweep. Disclose in the trial count.

### B — Trader Mayne ICT blueprint (`coBMd1vk2Lo`, verbatim transcript read in full by Agent 2)
- **SOURCE FACTS:**
  - At least two timeframes; stated pairs W→D/H12, D/H12→H1, H4→M15, H1→M5 for scalpers (05:29–06:26).
  - Swing = 3-candle fractal. Market-structure break = a candle **close** through the swing (07:20).
  - Range = most immediate swing low → the swing high after the MSB ("for simplicity… the most immediate", 53:36–54:30).
  - OB = the down candle(s) before the up move that broke structure, either the last one or all of them (19:49–20:42).
  - Premium/discount at 50%; buy in discount (16:15–17:16).
  - LTF entry inside the HTF OB (33:08–36:40):
    - a swing low forms;
    - it is **taken out**;
    - the high that generated it **breaks**;
    - this gives a breaker entry.
  - Stop below the swept low; the alternative "right below the breaker" is stated.
  - **Minimum 2:1 R or no trade** (35:47).
  - Target HTF external (the swing high). At 2R, "take half off **or** move stop to break even" (33:08).
  - Stated alternative: enter directly at the HTF OB, stop at its far side, target external (26:57, 50:02).
  - Multiple attempts allowed (36:40). Double confirmation preferred (30:28).
- **MISSING:**
  - exact breaker price level (top/mid of the zone);
  - order type;
  - session/time filter (timing matters less on HTF, 37:33);
  - sizing ("dynamic", 46:26 — discretionary);
  - expiry of an OB.
- **ASSUMPTIONS NOT SUPPORTED:**
  - adding FVG/SMT requirements (named as optional "confluence", 58:10);
  - a fixed session window;
  - fixed 1% sizing as a source rule.
- **AMBIGUITIES (7):**
  1. timeframe pair [4, multiplier];
  2. OB = last down candle vs all consecutive [2];
  3. entry mode: single-confirmation breaker / double-confirmation / HTF-direct [3];
  4. stop: swept low vs breaker [2];
  5. at 2R: half-off vs BE [2];
  6. breaker entry price;
  7. range anchor (the "most immediate" rule stated; the nuanced alternative excluded).
- Interpretations ≥ **24** (× 4 timeframe pairs).

### C — PO3 / 50% rebalance (`HNuRp9Z1bMs`, non-verbatim analysis; verbatim captions now available and should be used to re-verify quotes)
- **SOURCE FACTS:**
  - NQ primary, ES comparison; bearish SMT = NQ makes a new high while ES fails (09:25).
  - Price rebalances into 50% of the range (01:21). Daily/H4/H1 alignment.
  - Window 09:15–11:30 EST, and 14:00 PM.
  - Prior FVG support traded through becomes resistance (inversion).
  - Entry: limit on a re-tap **or** stop order.
  - Stop above the SMT high. Target 50%. BE early ("right or right out", 15:11).
- **MISSING:**
  - range endpoints;
  - alignment tolerance;
  - SMT pivot synchronization;
  - FVG geometry;
  - the long-side wording.
- **ASSUMPTIONS NOT SUPPORTED:**
  - using Dhesi v3's inversion engine as "C" without disclosure (it would be the same trial family);
  - a bullish mirror presented as [STATED].
- **AMBIGUITIES (10):**
  1. range endpoints [4];
  2. alignment tolerance;
  3. window hard vs soft;
  4. meaningful-high definition;
  5. SMT synchronization;
  6. rejection close vs touch;
  7. FVG/inversion boundaries;
  8. entry limit vs stop [2];
  9. BE timeframe: entry-TF vs H1 [2];
  10. bullish mirror existence.
- Interpretations ≥ **16**.

### D — Little Rizzy (`AVVM-FyewLg`, timestamped transcript)
- **SOURCE FACTS:**
  - Establish trend first (15:04).
  - Descending trendline; measure the lowest-low candle to the line and project the same distance below (08:54–13:21).
  - First or second pattern best; fourth/fifth tired (14:25).
  - Entry example: close below the Bollinger middle (1:11:34).
  - Stop above the candle high (1:09:48), contradicted by "below the low" (29:08).
  - Exit on a trendline break, close preferred (29:08).
  - Avoid the NY open (1:15:06).
  - Crash-bottom: buy at the projection (early) or on a close above the BB middle (35:26–36:01).
- **MISSING:**
  - trendline construction;
  - Bollinger period;
  - uptrend-long trigger;
  - sizing;
  - crash-bottom stop.
- **ASSUMPTIONS NOT SUPPORTED:**
  - fixed pivot-lookback trendlines presented as source;
  - trading the NY open;
  - treating the crash-bottom setup as testable intraday.
- **AMBIGUITIES (9):**
  1. trendline construction;
  2. pattern ordinal 1st vs 1st–2nd [2];
  3. BB period;
  4. entry BB-mid close vs discretionary;
  5. short stop above-high vs below-low contradiction [2];
  6. trendline-exit close vs touch [2];
  7. crash-bottom entry projection vs BB-mid close [2];
  8. uptrend-long trigger missing;
  9. timeframe.
- Interpretations ≥ **12**.

### E — Trident (`ADnslyKOwFE`, non-verbatim analysis + secondary)
- **SOURCE FACTS:**
  - Hard 03:00–06:30 NY window ("means nothing without the time", 02:35).
  - 30m execution, Daily context.
  - Above the 200 EMA; stacked 5/9/13/21 EMAs, intertwining rejected.
  - Bullish FVG; a doji whose wick passes the FVG 50%; the next candle must close **below the doji high**, else invalid (07:35).
  - FX stop below the setup candle (10:28); gold uses no hard stop.
  - Target 1:20+, exit on EMA change or a large bearish candle.
  - Long-biased; no short model.
- **MISSING:**
  - FVG geometry and age;
  - doji threshold;
  - order type;
  - DST;
  - short side.
- **ASSUMPTIONS NOT SUPPORTED:**
  - a symmetric short;
  - a fixed 20R take-profit;
  - an emergency stop on gold presented as source.
- **AMBIGUITIES (9):**
  1. FVG geometry;
  2. doji threshold;
  3. "wick through 50%";
  4. EMA 13 vs 15 [2];
  5. stack ordering;
  6. stop ref setup candle vs doji [2];
  7. pre-window FVG eligibility [2];
  8. "large bearish candle";
  9. entry price.
- Interpretations ≥ **8**.
- **Execution note:** source instruments are spot FX/gold. Lucid is CME futures only, so any result must be repriced on 6E/6J/6C/MGC/GC.

### F — MMXM / OTE (`IB-fyWI5j8w`, non-verbatim analysis)
- **SOURCE FACTS:**
  - HTF bias 4H minimum.
  - 15m execution, 5m Silver Bullet refinement.
  - Windows 02:00–05:00, 07:00–10:00, 10:00–12:00 NY.
  - OTE 0.62 / **0.705 primary** / 0.79.
  - Stop 1.0, with an optional 0.90.
  - Target the accumulation low; −0.28/−0.62 extensions only with strong momentum.
  - BE after a displaced close beyond 0.20.
  - Add only at BE (+1%). Risk 1–1.5%. Fewer than 10 setups a month.
- **MISSING:**
  - bias classifier;
  - SMR swing algorithm;
  - displacement threshold;
  - fib anchors;
  - ADR threshold.
- **ASSUMPTIONS NOT SUPPORTED:**
  - automatic extension targets;
  - a mechanical "HTF bias" presented as source without labelling it a proxy.
- **AMBIGUITIES (10):**
  1. bias classifier;
  2. key-level set;
  3. Asian-range clock;
  4. sweep criterion;
  5. SMR swing;
  6. displacement threshold;
  7. fib anchor wick/body;
  8. entry 0.62/0.705/0.79 [3];
  9. stop 1.0/0.90 [2];
  10. OTE vs Silver Bullet precedence [2].
- Interpretations ≥ **12**.
- Same futures-repricing note as E.

### G — `SQEtBHOJW6I` (verbatim transcript, 2h50m; rule sheet invalidated)
- **SOURCE FACTS:**
  - Large-cap US stocks (TSLA, NVDA, AMD, ARM); often same-day options.
  - Pre-marked "levels of significance": prior-day low, weekly levels, S3/S4/R3 pivots.
  - At the level, read the **tape / Bookmap** for aggression ("big red orders hitting the market", "panic on the tape").
  - Enter on the break without waiting for the candle close, because waiting hurts R:R.
  - Stop just beyond the level (e.g. "break above 143").
  - Size up on earnings/news catalysts. "Lower the risk (denominator)".
- **MISSING:**
  - any quantitative tape criterion;
  - level-construction rules;
  - targets;
  - fixed exits.
- **ASSUMPTIONS NOT SUPPORTED:**
  - any of the rule sheet's IPP / Silver Bullet / FX variants;
  - a price-only "level break" system labelled as Ortani's (it drops the claimed edge).
- **Verdict:** not faithfully mechanizable without trade-aggressor and L2 data. Out of prop scope.

### H — Small-cap shorts (`52ZsDmFHqyY`, non-verbatim analysis + creator page)
- **SOURCE FACTS:** universe cap ~$1M–$100M (FRD <$200M), float 1–50M, price >$3; no biotech, energy or Chinese names. Per setup:
  - **GS:** gap 70%–1000% (page: >100%); skip if premarket volume >50M; crack of the consolidation after 11:00; stop above the consolidation high.
  - **BS:** 1-year resistance, trapped $ ≥ ~$150M, a "10:1" ratio (direction unresolved); stop above resistance.
  - **FRD:** ≥3 green days on rising volume; 300%/3d or 1000%/2d; ¼ starter, ¾ add next day if the bounce fails.
  - Size ≤ 10% of daily float and ≤ 1% of daily volume.
- **MISSING:**
  - triggers;
  - borrow/locate;
  - halts;
  - exits.
- **ASSUMPTIONS NOT SUPPORTED:**
  - current ticker lists;
  - assumed borrow;
  - ignoring SSR/halts (Part M).
- **AMBIGUITIES (11):**
  1. GS gap 70 vs 100% [2];
  2. consolidation definition;
  3. crack trigger;
  4. GS stop hard vs close [2];
  5. BS ratio direction [2];
  6. BS zone width;
  7. BS stop hard vs close [2];
  8. FRD starter red-close vs intraday failure [2];
  9. FRD cap 100M vs 200M [2];
  10. FRD add rule;
  11. point-in-time cap/float.
- Interpretations ≥ **12**.

## 4. Agent-1 implementation disagreements
**None assessable.** No mechanization, preregistration or trades exist yet (Agent 1 folder: `_source_transcripts`, `_source_reports`, `_data_tools` only).

Data-tool review:
- **Dukascopy:** URL scheme (0-based month), 24-byte record decode, divisor 1e3 for JPY/XAU and 1e5 otherwise, and the drop of zero-volume filler minutes are consistent with the stated format.
- **HistData:** "EST without DST" → UTC+5h follows HistData's own documentation as quoted. That claim is **UNVERIFIED by Agent 2** and should be cross-checked on overlapping minutes against Dukascopy. A ≥95% close agreement at lag 0 (vs lag ±60 min) settles it.

## 5. Trade-level replication — no trades exist. Protocol pre-fixed in `AGENT2_SURVIVOR_REPLICATIONS/README.md`.

## 6. Leakage tests — pre-registered attack list for when candidates exist
| Attack | Applies to | Control |
|---|---|---|
| 3-bar fractal needs bar i+1 | A, B, D, F | signal time must be ≥ confirmation bar close; leaked variant (use at bar i) must *improve* results, else pipeline lacks power |
| HTF candle completion | B, C, E (Daily context), F | HTF values available only at bin close; test with a deliberately 1-bin-early HTF |
| Session high/low, daily range, ADR | A, C, F | only prior/closed data |
| FVG completion (c3 close) | C, E, F | FVG usable only after c3 closes |
| SMT alignment | C | ES pivot must be confirmed by the same time as NQ; future-SMT leak control |
| Roll leakage | all futures | no back-adjusted series; roll gap handled as in Dhesi M6 |
| Point-in-time cap/float/borrow, survivorship | H | BLOCKED |
| News/event knowledge | A (news blackout) | calendar must be as-published, not revised |
| HistData timezone | E, F | lag test vs Dukascopy |

## 7. Execution audit — none to audit. Pre-fixed rules:
- **Futures:** $1.00 RT micros; 1 tick adverse on market/stop fills; gap-through stops at the open; one-bar-delay sensitivity is mandatory.
- **FX:** research on spot bid/ask is allowed, but a PROP claim requires repricing on CME futures (6E/6J/6C/6B, M6E, GC/MGC) including their tick and commission.
- **Trident gold's "no hard stop"** is not acceptable under the risk engine (a per-trade $325 cap). Any mechanization must add a stop and label it NON-SOURCE.
- **G, H:** FAIL_EXECUTION by construction in a Lucid futures account.

## 8. Statistical audit — no positive test exists.
Required when one does:
- mean, median, 10% trimmed mean;
- stationary bootstrap and session-clustered CI;
- Newey-West for daily PnL;
- year/month tables, MDD, ES(5%);
- top-1/5/10 PnL share;
- CSCV/PBO across the declared interpretation matrix;
- DSR with the **global** trial count (≥ 86 registered trials / 367 configs plus this program's ≥ 92 interpretations).

## 9. Placebos — pre-registered per family (used only when a survivor exists)
| Family | Placebos |
|---|---|
| A | random matched sweep times; time-shifted sweeps (±1 session); direction-flipped entries |
| B | random OB selection within range; shifted HTF range (1 leg earlier); breaker direction flip |
| C | randomized SMT partner (shuffled ES days); time-shifted ES; future-SMT leak control |
| D | randomized trendline anchors; time-shifted pattern |
| E | randomized FVG timing within window; shifted kill zone (+6h); non-doji placebo |
| F | random fib anchors; shifted displacement leg; randomized session window |
| G, H | not run (blocked) |

## 10. Cross-interpretation robustness — not assessable; each family's interpretation grid is fixed in §3, so a single-variant winner can be detected.

## 11. Global trial count

| Source | Count |
|---|---|
| Global ledger | 86 trials / 367 configs / 23 families |
| + Dhesi v3 dev and v3 fresh | 2 unregistered |
| + This program | 8 families / 19 sub-setups / **≥ 92 source-supported interpretations** (excl. G), 0 run |
| Agent 1's ledger | not found → **UNRESOLVED** |

## 12. Terminal verdict per family (IMPLEMENTATION / SOURCE-FAMILY)

| Family | Implementation verdict | Source-family verdict |
|---|---|---|
| A Liquidity Trap | NOT_IMPLEMENTED | OPEN (partly codable, 8 interps) |
| B Trader Mayne | NOT_IMPLEMENTED | OPEN — **most codable** (rule sheet's "[MISSING]" overturned) |
| C PO3 / 50% | NOT_IMPLEMENTED | OPEN; overlaps Dhesi family |
| D Little Rizzy | NOT_IMPLEMENTED | continuation OPEN; crash-bottom UNTESTABLE_SAMPLE |
| E Trident | NOT_IMPLEMENTED | OPEN (needs futures repricing) |
| F MMXM / OTE | NOT_IMPLEMENTED | OPEN (needs futures repricing) |
| G SQEtBHOJW6I | NOT_IMPLEMENTABLE | BLOCKED_DATA + OUT_OF_SCOPE; rule-sheet alternatives INVALID |
| H Small-cap shorts | NOT_IMPLEMENTABLE | BLOCKED_DATA + OUT_OF_SCOPE |

No family is ROBUSTLY_REJECTED, because none has been tested.

## 13. Survivors confirmed: **NONE**

## 14. Survivors rejected: **NONE** (no candidates)

## 15. Disputed findings
1. The rule sheet's B = [MISSING] and G = IPP / Silver Bullet / FX are **disputed by the verbatim transcripts**. Agent 1 must mechanize B from the transcript and must not implement any rule-sheet G variant.
2. Harvest route: the frozen protocol (Sierra continuous chart) vs the superseded Agent-2 offline-stitch plan. Resolved for the protocol.

## 16. Data required — see `AGENT2_DATA_GAPS.md`
- $0 Sierra CME FX + gold 1m harvest for E/F futures repricing, owner GUI.
- No paid data recommended.

## 17. Dhesi final-run status: **NOT RUN.** Open items:
- NQ untouched harvest + integrity JSON;
- ledger registration (3 entries);
- owner authorization file;
- recommended D3/D4 validator fixes by Agent 1 (new hash → new request);
- owner adjudication of CE-A2-01.

## 18. Next single action
**Owner:**
1. Adjudicate CE-2026-09-24-A2-01.
2. Quarantine the four pre-2024 `.dly` files.
3. Ask Agent 1 to apply the D3/D4 plumbing fixes before re-issuing the authorization request.

Then do the NQ Sierra harvest per protocol §2.3/§2.4, without scrolling the charts.
