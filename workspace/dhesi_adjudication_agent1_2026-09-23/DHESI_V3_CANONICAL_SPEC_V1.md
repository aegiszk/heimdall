# DHESI V3 — CANONICAL SPECIFICATION V1 (new hypothesis, immutable)

- Frozen: 2026-09-23 by Agent 1 (canonical spec owner). No untouched (pre-2024-07-01) market data was read before or while writing this document.
- Status: **NEW HYPOTHESIS** developed on contaminated/development data. It is **not** a bug-fixed v2 (`DHESI_REOPEN_ADJUDICATION_2026-09-23.md`, SHA-256 `7693a320…ff7a1a`).
- Validation: see `DHESI_V3_VALIDATION_PROTOCOL_V1.md`. This spec may not change after its hash is recorded. Any change creates a V2 spec and a new ledger trial.

## 0. Normative definition and precedence

The hypothesis is **the unchanged frozen v3 code**, run with all switches on:
`InversionModelV3(contract="MNQ")` with `htf_24h=early_sweeps=session_pools=stop_guard=attempts=True`.

| Normative input | SHA-256 |
|---|---|
| `core/alpha/inversion_model.py` (v2 base class; supplies every rule not overridden) | `e32e88f1a309c8e259274fd181929c3aa19935e667bcf568ff31eb9fbbdd0037` |
| `core/alpha/inversion_model_v3.py` | `0ab7a5156e506c629110efe5253a6b93315072cd3f544490d80c2a746922bf85` |
| `core/risk/prop_engine.py` (`allowed_size`) | `5750672eea42047ae294415a14c795c783aef4348cd4af7bfc9eead0cae7a265` |
| `core/alpha/base.py` | `2d8c40e53bfdd0ab5f26ca90165b1cf7a38475e0429edd5f304c83eef1d78737` |

Precedence: **frozen code > this text**. The text below is a complete, deterministic restatement of the code, written so the model can be reimplemented without the code.

Existence proof: an independent reimplementation written from this rule set (`dhesi_v3_validator.py::reference_run`, which imports nothing from `core.alpha`) reproduces the frozen v3 development trades **49/49**. Entry time, side, entry, stop, TP1, contracts, exit time, exit price, exit reason and PnL all match (`selftest_dev_result.json`). The v2 configuration also matches 30/30.

Rule tags:
- **SOURCE_RULE**: stated in the Dhesi source (rule sheet SHA `98b931bc…6090`; transcript `UIGZtoGGPH4`, SHA `507a67a7…14be`).
- **EARLIER_FROZEN_RULE**: fixed in v1/v2 before v2 outcomes were read.
- **DEVELOPMENT_DERIVED_RULE**: introduced after reading v2 outcomes on the development data.
- **IMPLEMENTATION_NECESSITY**: needed to make the model computable; carries no strategy content.

Units: "points" are index points. "tick" = 0.25 points. The execution instrument is MNQ: $2.00/point, $0.50/tick.

## 1. Market, timezone, data

| ID | Rule | Tag |
|---|---|---|
| M1 | **Evidence price series:** NQ (E-mini Nasdaq-100) continuous 1-minute OHLCV. NQ and MNQ are one underlying family; only the NQ series is evidence. MNQ price data is never used as a second sample. | SOURCE_RULE (NQ); IMPLEMENTATION_NECESSITY (single series) |
| M2 | **Execution economics:** MNQ ($2.00/pt, tick $0.50, max 40 contracts, $1.00 round trip per contract). Applied to NQ prices; NQ and MNQ share the 0.25 tick. | IMPLEMENTATION_NECESSITY (Lucid 50K FLEX max 40 micros; confirmed commission in CLAUDE.md) |
| M3 | **Continuous-contract method:** front contract by volume-based rollover, **no back-adjustment** (raw prices; roll gaps are left in place). Development used Databento `.v.0` (volume-based, unadjusted); validation uses Sierra "Continuous Futures Contract – Volume Based Rollover", back-adjust None. | IMPLEMENTATION_NECESSITY |
| M4 | **Timestamps:** UTC, labelling the minute's **start**. Converted to `America/New_York` with the IANA tz database, so DST follows the tz database. | IMPLEMENTATION_NECESSITY |
| M5 | **Missing bars:** never filled, interpolated or forward-filled. A minute with no row does not exist for any rule. An aggregation bin with no minutes does not exist. | IMPLEMENTATION_NECESSITY |
| M6 | **Roll gaps:** no special handling. Pools, FVGs and swings computed across a roll are used as-is, identically to development. | IMPLEMENTATION_NECESSITY |

## 2. Sessions and time

| ID | Rule | Tag |
|---|---|---|
| T1 | **RTH frame:** 1m rows on weekdays (Mon–Fri ET) with ET clock time in [09:30, 16:00], **inclusive** of the row stamped 16:00. | EARLIER_FROZEN_RULE |
| T2 | **Session id:** the ET calendar date of an RTH row. Holidays and early closes are ordinary sessions containing whatever rows exist. | EARLIER_FROZEN_RULE |
| T3 | **Session ordinal:** sessions numbered in chronological order of the RTH frame. "k sessions back" uses these ordinals, not calendar days. | EARLIER_FROZEN_RULE |
| T4 | **Entry window:** an entry trigger (T-stamp of the 5m inversion bar, see E2) must have ET time in [10:00, 16:00]. | SOURCE_RULE ("I try to avoid anything before 10:00 AM") |
| T5 | **Sweep window:** sweeps are detected on every RTH row from 09:30. | DEVELOPMENT_DERIVED_RULE (prereg fix 2; v2 discarded pre-10:00 sweeps. The source's 10:00 rule is an entry filter) |
| T6 | **Overnight:** no position is ever held past the session's last RTH row (§7 X4). | EARLIER_FROZEN_RULE |
| T7 | **Burn-in:** trades in the first 20 RTH sessions of any evaluated series are discarded, because the rolling pools and FVG lookback are not yet populated. | IMPLEMENTATION_NECESSITY |

## 3. Bars

| ID | Rule | Tag |
|---|---|---|
| B1 | **15m and 5m bars:** from the RTH frame only. Right-closed, right-labelled bins on the ET clock: the bar labelled L contains RTH rows with stamp in (L−15m, L] (or 5m). O = first, H = max, L = min, C = last; session = session of the last row. Empty bins are dropped. Example: the 15m bar labelled 09:30 contains only the 09:30 row. | EARLIER_FROZEN_RULE |
| B2 | **HTF 4H and 1H bars:** from **all** 1m rows (24h, including overnight and Sunday evening). Bin start = the 18:00-ET-anchored multiple of the bin length. 4H bins start 18:00, 22:00, 02:00, 06:00, 10:00, 14:00 ET wall clock; 1H bins start on the hour. A bin contains rows whose start stamp s satisfies start ≤ s < start + length. Label (event time) = bin end, localized to ET with ambiguous = DST-flag True and nonexistent shifted forward. HTF bar session = ET date of (end − 1 minute + 6 hours). | DEVELOPMENT_DERIVED_RULE (prereg fix 1; motivated by the source's "10:00 AM … new 4-hour candle") |

## 4. Liquidity pools (computed once per session, before its first RTH row)

| ID | Rule | Tag |
|---|---|---|
| P1 | `prior_rth_high/low`: RTH high/low of the previous session. | EARLIER_FROZEN_RULE |
| P2 | `prior_day_high/low`: high/low over all 1m rows (24h) of the previous ET calendar date **present in the data** (Monday's is Sunday evening's rows). | EARLIER_FROZEN_RULE |
| P3 | `rolling20_high/low`: max/min of the RTH highs/lows of the 20 previous sessions. Undefined until 20 exist. | EARLIER_FROZEN_RULE (proxy for the source's "monthly highs/lows") |
| P4 | **Equal highs/lows:** collect every 1m RTH 3-bar fractal (§6 S1 applied to the 1m RTH frame as one continuous sequence) from sessions 1–20 back. Sort the fractal-high prices ascending and cluster greedily: a value joins the current cluster if \|v − mean(cluster)\| / mean(cluster) ≤ 0.0005, otherwise the cluster closes. Keep clusters with ≥ 2 members. Level = max (highs) or min (lows) of the cluster. Clusters with ≥ 3 members are also **major** (`stacked_equal_*`). | EARLIER_FROZEN_RULE |
| P5 | `asia_high/low`: high/low of rows with ET time in [20:00, 23:59] on the calendar evening before the session date. | DEVELOPMENT_DERIVED_RULE (prereg fix 3; the source names "session highs and lows") |
| P6 | `london_high/low`: high/low of rows with ET time in [02:00, 04:59] on the session date. | DEVELOPMENT_DERIVED_RULE (same) |
| P7 | **Sweep pools** (high list / low list) = P1, P2, P3, P4 (all clusters), P5, P6, in that order. Deduplicated on (kind, round(level/0.25)); the first occurrence is kept. | EARLIER_FROZEN_RULE + DEVELOPMENT_DERIVED_RULE (P5, P6) |
| P8 | **Major pools** (runner targets) = P4 clusters with ≥ 3 members + P3. | EARLIER_FROZEN_RULE |

## 5. Setup sequence (per session, per sweep, in sweep-time order)

| ID | Rule | Tag |
|---|---|---|
| S0 | **Liquidity sweep.** Walk the session's RTH rows in order (local index i). For every high-list pool with row high > level, append a pending sweep (expires at i+3, bias −1). For every low-list pool with row low < level, append one (expires i+3, bias +1). Then evaluate all pendings on this same row: drop any with i > expiry; fire a sweep event (time = this row, bias, pool) if close < level (bias −1) or close > level (bias +1); otherwise keep it. Duplicate pendings for the same pool are allowed and fire duplicate events. Events are ordered by time, stably. | EARLIER_FROZEN_RULE (source: "sweep a major liquidity pool") |
| S1 | **Fractal swing** (used by P4 and X1): at index i of a bar sequence, a swing high exists if H[i] > H[i−1] and H[i] ≥ H[i+1]; a swing low if L[i] < L[i−1] and L[i] ≤ L[i+1]. Its time = bar i's time; confirmation time = bar i+1's time; its session = bar i's session. | EARLIER_FROZEN_RULE |
| S2 | **FVG** on a bar sequence, at bar i ≥ 2 with c1 = bar i−2 and c3 = bar i. **Bullish** if H(c1) < L(c3): zone [H(c1), L(c3)]. **Bearish** if L(c1) > H(c3): zone [H(c3), L(c1)]. Formed time = c3's label; session = c3's session; "third-candle range" = [L(c3), H(c3)]. | EARLIER_FROZEN_RULE (source concept) |
| S3 | **Inversion events** on a bar sequence, in bar order. On bar i, only if bar i's session is an RTH session: (a) drop from the active set any FVG already inverted, or whose session is not an RTH session, or not 0–20 sessions back; (b) a bullish FVG inverts if close(i) < zone low, a bearish one if close(i) > zone high; mark them inverted; (c) for each bias b ∈ {−1, +1}, among the FVGs inverted on this bar with direction = −b, the one with the latest formed time (first in list order on ties) yields an event: time = bar i's label, session, bias b, zone, formed time, close(i), displacement = \|close(i) − open(i)\|. **After** that, FVGs formed at bar i join the active set, so an FVG cannot invert on its own formation bar. | EARLIER_FROZEN_RULE (source: "close through … inversion FVG") |
| S4 | **HTF timeframe choice** for a sweep at time t in session s: **4H** if any 4H FVG (inverted or not) has formed time < t and a session 0–20 sessions back from s; otherwise **1H**. | EARLIER_FROZEN_RULE (deterministic replacement for the source's "cleanest timeframe" discretion) |
| S5 | **HTF inversion:** the earliest inversion event on the chosen HTF with the same session and bias as the sweep, event time > t, and event ET time ≤ 16:00. None: skip this sweep. | EARLIER_FROZEN_RULE |
| S6 | **Displacement / volatility filter:** skip the sweep unless the HTF inversion's displacement ≥ **30.0 points**. This is the only volatility filter. The source's "market expanding" and "only moving 10 points … not high probability" are encoded here and nowhere else. | EARLIER_FROZEN_RULE (v2 revision) |
| S7 | **Retracement:** the first 15m bar of the session with label > inversion time, label ET time ≤ 16:00, and [low, high] overlapping the HTF zone (inclusive: max(lows) ≤ min(highs)). None: skip the sweep. | EARLIER_FROZEN_RULE (source: "pullback into … on the 15-minute") |
| S8 | **Sweep eligibility (attempt gating):** skip a sweep whose time < the exit time of this session's previous trade. | DEVELOPMENT_DERIVED_RULE (prereg fix 6) |

## 6. LTF confirmation, entry, stop, size, targets

Candidate LTF events are the **5m inversion events** (S3 applied to the 5m bars of B1, with the 5m sequence's own session numbering). They share the sweep's session and bias, and are taken in order of inversion time. The first candidate passing **all** of E1–E9 becomes the trade. A candidate failing any check is discarded and the **next** candidate is tried (rule R1). If none passes, the sweep produces no trade.

| ID | Rule | Tag |
|---|---|---|
| E1 | The candidate FVG's formed time ≥ retracement label **and** inversion time > retracement label. | EARLIER_FROZEN_RULE |
| E2 | If this session already has a trade: inversion time > that trade's exit time. | DEVELOPMENT_DERIVED_RULE (prereg fix 6) |
| E3 | Inversion ET time in [10:00, 16:00] (T4). | SOURCE_RULE |
| E4 | The candidate's third-candle range overlaps the HTF zone (inclusive). | EARLIER_FROZEN_RULE (source: LTF FVGs form "as price pulls back" into the HTF gap) |
| E5 | A 1m RTH row exists stamped exactly at the inversion time. This is the **entry bar**. | IMPLEMENTATION_NECESSITY |
| E6 | **Stop (LONG):** among the session's 15m swing lows (S1 on the whole 15m sequence) with swing time ≥ HTF inversion time and confirmation time ≤ entry time, take the latest by swing time: stop = its price − 0.25. **Stop (SHORT):** the same with swing highs: stop = price + 0.25. No such swing: discard the candidate. | EARLIER_FROZEN_RULE (proxy for the SOURCE_RULE "stop above the current 15-minute high") |
| E7 | **Entry price** = 5m inversion bar close + b × 0.25 (1 adverse tick). Entry time = the entry bar; the trade is managed from the next 1m row. | EARLIER_FROZEN_RULE |
| E8 | **Protective side + minimum stop:** require b × (entry − stop) ≥ **10.0 points**. Otherwise discard the candidate. | Side component = SOURCE_RULE (a stop is protective by definition). **10.0-point floor = DEVELOPMENT_DERIVED_RULE** |
| E9 | **Size / maximum stop:** contracts = min(floor(325 / (0.50 × stop_ticks)), 40), with stop_ticks = \|entry − stop\| / 0.25. If 0 (stop > 162.5 points), discard. Risk $ = contracts × \|entry − stop\| × 2; if > 325, discard. | EARLIER_FROZEN_RULE (risk engine `daily_buffer = 325`); the maximum stop of 162.5 pts is implied |
| E10 | **TP1:** the nearest sweep-list pool (P7) strictly beyond entry: the lowest high-list level > entry for LONG, the highest low-list level < entry for SHORT. None: discard the candidate. If its distance ≥ 1.5 × \|entry − stop\|, TP1 = that level; otherwise TP1 = entry + b × 1.5 × \|entry − stop\| (promoted). | EARLIER_FROZEN_RULE (source: "nearest opposing liquidity … 1:1.5 or 1:2") |
| E11 | **Runner target:** the nearest major pool (P8) strictly beyond TP1 in the trade direction. None: no runner target (the runner exits by stop/BE or flatten). | EARLIER_FROZEN_RULE (source: runners to major structural liquidity) |
| R1 | **Replacement-entry behaviour:** a candidate discarded by E6, E8, E9 or E10 does **not** end the setup; the next 5m inversion candidate of the same sweep is tried. | **DEVELOPMENT_DERIVED_RULE.** For E8 it was introduced in v3 code; the prereg text said "skip the setup". It contradicts the SOURCE_RULE "If I don't get my first entry … that's it for me". For E6, E9 and E10 it was already v2 code behaviour. |

## 7. Trade management and exits

Processing order on each 1m row after the entry bar, within the entry session only:

| ID | Rule | Tag |
|---|---|---|
| X1 | **Stop check first.** LONG: if open ≤ current stop, exit all remaining at min(open, stop − 0.25) (`gap_stop`); elif low ≤ stop, exit at stop − 0.25 (`stop`). SHORT mirrored: max(open, stop + 0.25); high ≥ stop gives stop + 0.25. **Same-bar stop and target: the stop wins.** | EARLIER_FROZEN_RULE |
| X2 | **TP1** (if not yet hit): LONG high ≥ TP1 (SHORT low ≤ TP1). Book 50% of the contracts at exactly TP1 (limit, no slippage). Half of an odd count is booked fractionally. Move the runner stop to **entry price** (breakeven). No further checks on this row. | SOURCE_RULE ("I always trim half … move my stop loss at break even"); fractional half = IMPLEMENTATION_NECESSITY |
| X3 | **Runner target** (only after TP1 on an earlier row, and if E11 exists): high ≥ target (LONG) or low ≤ target (SHORT) gives the remaining 50% exit at exactly the target. | EARLIER_FROZEN_RULE |
| X4 | **Session flatten:** if the row's ET time ≥ 16:00, stop scanning. Any open remainder exits at the close of the session's last RTH row − b × 0.25. If the entry bar is the session's last row, exit at its close − b × 0.25. | EARLIER_FROZEN_RULE |
| X5 | **PnL:** gross = Σ over exits of (fraction × contracts × b × (exit − entry) × 2). **net = gross − contracts × $1.00** (commission charged once on the full count). A trade is a **loss** if net < 0. | EARLIER_FROZEN_RULE |

## 8. Session-level limits

| ID | Rule | Tag |
|---|---|---|
| L1 | At most **3** trades per session, one position at a time. | DEVELOPMENT_DERIVED_RULE (prereg fix 6). Source: "win one, lose one … third try"; applying 3 after two wins is an interpretation. |
| L2 | Stop taking trades after **2 losing trades** in a session. | SOURCE_RULE |
| L3 | No dollar daily-loss stop other than L2 and the per-trade $325 risk cap (E9). | EARLIER_FROZEN_RULE |
| L4 | **Expiry / invalidation:** every sweep, inversion, retracement and LTF candidate is session-scoped and expires at session end. HTF FVGs expire when inverted or more than 20 sessions after their formation session. | EARLIER_FROZEN_RULE |

## 9. Explicitly excluded source elements (never applied)

Time-in-gap downgrade; stacked OB+FVG double violation; SMT divergence; discretionary "cleanest timeframe" (replaced by S4); "missed entry, sit out" (contradicted by R1); options; multi-day swing trades. Any of these would be a new hypothesis. ES is not excluded; it is a secondary replication market under §12 and the protocol.

## 10. DEVELOPMENT-DERIVED RULES (complete list)

T5 (sweeps from 09:30), B2 (24h HTF bins anchored 18:00), P5/P6 (Asia/London pools and their clock windows), S8/E2 (attempt gating), **E8 floor (10.0 points)**, **R1 (replacement entry)**, L1 (3 attempts).

## 11. OVERFIT-RISK REVIEW (values frozen as-is; untouched validation decides)

| Parameter | Value | Where it came from | Mechanistic rationale | Why it is frozen | Risk |
|---|---|---|---|---|---|
| E8 minimum stop | 10.0 pts | v3 prereg §5 cites two v2 losers (0.25-pt and 3-pt stops at 40 lots; −$100 and −$300). The adjudication showed this floor alone produced v2's sign flip (+$922 of +$1,063.50) via ~2 trades. | Friction ≤ 10% of risk: 2 ticks + $1 = $2 per contract vs $20 risk per contract at 10 pts. The 10% ratio itself is an unforced choice. | Changing it now would be a second post-hoc edit | **HIGH_OVERFIT_RISK** (it never bound on an accepted v3 dev trade: min accepted stop 20 pts; the side-only v3 differs by 1 trade) |
| R1 replacement entry | continue to next candidate | v3 code behaviour. Created the 2025-02-24 (+$484.50) and 2025-08-07 (+$467.00) replacement winners in the v2 ablation. | None in the source; the source says the opposite. | The v3 dev result was generated with it | **HIGH_OVERFIT_RISK** |
| L1 attempts | 3 per session, 2-loss stop | prereg fix 6, written after reading v2 | Source quote (partial) | Source-grounded | MODERATE |
| P5/P6 windows | 20:00–23:59, 02:00–04:59 ET | prereg fix 3 | Conventional Asia/London clock windows; no numeric search | Not tuned | MODERATE |
| B2 anchor | 18:00 ET, 4-hour bins | prereg fix 1, motivated by v2 entry-time histogram | Source: the 4H candle opens at 10:00; the CME day starts 18:00 | Source-derived | LOW |
| T5 sweep start | 09:30 | prereg fix 2 | Source 10:00 rule applies to entries | Source-derived | LOW |
| S6 displacement | 30.0 **raw** pts | v2 revision after the dev-data funnel diagnostic replaced an ATR proxy | Source: "only moving 10 points … not high probability" | Frozen before v2 outcomes | MODERATE, plus a **price-level non-stationarity** note: 30 pts ≈ 0.13% of NQ at 23,000 but ≈ 1.3% at 2,300 (2011). Early untouched years will produce fewer trades by construction. Declared now, not a post-hoc excuse. |
| E10 TP1 promotion | 1.5R | v1 proxy | Source "1:1.5 or 1:2" | v1-frozen | LOW |
| P4 tolerance | 0.0005 relative | v1 proxy | Dimensionless "equal" definition | v1-frozen | LOW |
| S0 reclaim | within 3 bars | v1 proxy | "Sweep" = trade through and close back | v1-frozen | LOW |
| P3/S3 lookback | 20 sessions | v1 proxy | ≈ one month ("monthly highs/lows") | v1-frozen | LOW |
| E9 risk cap | $325 | risk engine (CLAUDE.md §4) | Prop survival, not strategy | Not a strategy parameter | LOW |

## 12. Instrument generalisation (secondary markets only; frozen now, used only per protocol §7)

- **Minimum stop (E8), one method: friction ratio.** This is the same mechanism the v3 prereg gives for the 10-point floor.
  `floor_points = 10 × (2 × tick_value + commission_rt) / point_value`
  It reproduces MNQ exactly: 10 × (1.00 + 1.00) / 2 = **10.0**.
  - MES ($5/pt, 0.25 tick, $1 RT): **7.0 pts**
  - M2K ($5/pt, 0.10 tick, $1 RT): **4.0 pts**
  - MYM ($0.50/pt, 1.0 tick, $1 RT): **40.0 pts**
- **Displacement (S6), one method: same-day price-ratio equivalence to NQ.**
  `disp_min(market, s) = 30.0 × close_market(last RTH row of session before s) / close_NQ(last RTH row of session before s)`
  If NQ lacks that session: no trades that session.
- **All tick-denominated offsets** (1-tick stop offset, 1-tick slippage, pool dedupe) use the market's own tick. Sizing uses its tick value. $325 cap, 40 contracts, all ratios, windows and clocks unchanged.
- Canonical evidence series: ES, RTY, YM continuous (the same M3/M4 method). Execution economics: MES, M2K, MYM.
- **[U]** M2K and MYM commission of $1.00 RT is **UNVERIFIED** (CLAUDE.md confirms only MES/MNQ). It must be confirmed from a live Lucid source before any secondary run. If it differs, the formula above is applied mechanically with the confirmed value, and that is recorded before the run.

## 13. Hash of this file

The SHA-256 is recorded in `DHESI_V3_CANONICAL_SPEC_V1.sha256`. A file whose hash differs is not this specification.
