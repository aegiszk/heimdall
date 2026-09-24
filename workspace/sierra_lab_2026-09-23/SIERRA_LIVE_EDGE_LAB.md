# HEIMDALL — Sierra Live Edge Lab, cycle 1 (2026-09-23)

**Written by:** Agent 2 (same session).

**Scope:**
- No orders, no optimization, no threshold mining, no paid data.
- `HEIMDALL_MEMORY.md` was not edited (checker role).

**Labels:**
- [V] verified this session.
- [I] inferred.
- [U] unverified.

**Overall:** the recorder is built but not yet proven live. Studies A and B ran at 1-minute resolution. Study C has insufficient data. **Hypothesis: NONE.**

## 1. Recorder status — BUILT, NOT YET PROVEN LIVE

**Source:** `tools/sierra_acsil/HeimdallTapeRecorder.cpp` (SHA-256 `2C909F6F…AC8B`).
- Compiled locally with MSVC 2022 Build Tools against Sierra's own `ACS_Source` headers.
- The DLL (`D1498D26…AE4E`, 156,672 B) exports `scsf_HeimdallTapeRecorder` [V dumpbin].
- It is installed as `C:\SierraChart\Data\HeimdallTapeRecorder_64.dll`. It is inert until added to a chart.

**Behaviour:**
- Read-only. It calls `sc.GetTimeAndSales()` only; no order or position function.
- Append-only CSV per symbol per UTC day in `C:\SierraChart\Data\HeimdallTape\`, plus an events log (start/backfill, `sequence_gap`, `sc_ts_marker`, `sequence_reset_or_wrap`, `write_failed`).

**Field availability** (from `scstructures.h` / `scconstants.h`, not assumed):

| Wanted | Status |
|---|---|
| Exchange / SC timestamp | **SC DateTime, UTC, µs field (feed time)** — AVAILABLE |
| Local receive timestamp | **UNAVAILABLE.** The recorder writes `local_proc_ns`, the time the study call processed the batch. That lags receipt by up to the chart update interval. The host clock is ~15 s fast and drifting (SNTP offsets are logged by the HL recorder and can be reused). |
| Sequence number | `Sequence` (Sierra-assigned uint32, "may wrap") — AVAILABLE. An **exchange** sequence number is UNAVAILABLE. |
| Price, size | AVAILABLE |
| Aggressor | `Type`: 1 = at bid or lower, 2 = at ask or higher (CME FIX aggressor per Sierra docs) — AVAILABLE |
| Best bid/ask updates | `Type 6` records with Bid/Ask/BidSize/AskSize, plus TotalBid/AskDepth — AVAILABLE |
| Unbundled trade info | `UnbundledTradeIndicator` 0/1/2, `NumberOfTrades` — AVAILABLE |
| Gap marker | `Type 0 = SC_TS_MARKER` — AVAILABLE |
| MBO / queue position | **UNAVAILABLE** (not inferred) |
| Session | Not a field. It is derived offline from the timestamp. |

**Heimdall interface:**
- The recorder writes files. `tools/sierra_tape_reader.py` reads them (validate: schema, gaps, markers, duplicates, backward jumps; fidelity: per-minute volume and bid/ask volume vs Sierra's `.scid` for the same symbol).
- Tests: `tests/test_sierra_tape_reader.py` 3 passed [V].
- The money path is untouched.

**Fidelity / gap proof:** NOT YET DONE. It needs Sierra running with the study on charts (owner GUI step, §9).

## 2. Sierra data preserved

**Included history (official doc `SierraChartHistoricalData.php`) [V]:**
- "Tick by tick data for futures contracts on the CME/NYMEX/COMEX/CBOT begins at 2011."
- It is included with the Standard/Advanced service packages at no extra charge.
- Bid/ask trade volume comes from the FIX Aggressor field.
- The account's package tier (Package 3) is inferred to qualify, because NQ ticks downloaded [I].
- **Subscription expiry date: unknown to me (owner input).**

**What is on disk now** (`data/sierra/scid_snapshot_2026-09-23/INVENTORY.json`, 44 files with SHA-256; 236 MB of copies made):

| Scope | Storage | Coverage |
|---|---|---|
| NQ (NQM26 / NQU26) | 1-tick | Hashes match the existing MANIFEST |
| NQZ26 | 1-tick | **Changed** since MANIFEST: 2.60M → 2.66M records, new SHA `69751369…` |
| MNQZ26 | 1-tick | Since 2026-09-06 |
| ES, RTY, YM, CL, GC and all other micros | **1-minute only** | ES from 2026-02-27; CL from 2026-04-02; GC from 2026-03-22 |

**Harvest plan (not executed; needs the Sierra GUI):**
1. Global Settings → Intraday Data Storage Time Unit = **1 Tick**.
2. For each front and next contract, open a chart and let the download run.
   - Priority: CL, GC, ES, NQ, RTY, YM.
   - Depth: last 24 months first.
3. **Back up the current 1-minute `.scid` files first.** Re-downloading at 1-tick replaces the file (they are snapshotted above).

**Size estimate [I]:** NQ ≈ 1.37 GB per contract-quarter (40 B/record). So ~4–6 GB per symbol-year for ES/NQ, less for the rest. That is ≈40 GB for 2 years × 6 symbols; C: has ~125 GB free.

## 3. EIA / CL results (Study A) — 1-minute resolution only

**Setup:**
- Events: official EIA WPSR schedule, Wednesdays 10:30 ET, plus the holiday shifts 2026-05-28 and 2026-09-10 at Thu 12:00 ET (eia.gov schedule page).
- n = **24 events**, 2026-04-08 → 2026-09-16.
- Front contract = the max-volume CL contract that day.
- Placebo: 10:30 ET on non-release weekdays, n = 94.

| Metric | EIA events | Placebo |
|---|---|---|
| \|displacement\| 0–1 min | **17.96 ticks** | 8.76 |
| Volume intensity 0–1 min vs prior 30-min median | **2.06×** | 1.13× |
| Same-minute corr(signed flow, displacement) | 0.64 | 0.58 |
| Mean signed move 1→2 / 2→5 / 5→15 min | +3.5 (t 1.37) / +2.2 (t 0.75) / +1.3 (t 0.21) ticks | −0.3 / +1.5 / +1.7 |
| Continuation after the first minute, 1→5 min (in its direction) | mean −1.25 ticks (t −0.30); continued in 41.7% of events | −1.16; 45.7% |
| 1→15 min continuation | +4.96 ticks (t 0.65) | −4.5 (t −1.27) |
| MAE 1→5 min for an entry at the 1st-minute close | median 11.5 ticks | 12.0 |

**Reading:**
- EIA adds information *inside the first minute* (~2× displacement and volume).
- After the first minute there is **no measurable continuation or reversal** at 1-minute resolution, and adverse excursion is the same as on ordinary days.
- **Sub-minute windows (0–5 s, 5–15 s, 15–30 s, 30–60 s): INSUFFICIENT DATA.** CL is stored at 1-minute. They need the tick harvest.
- Artifacts: `eia_cl_response.json`, `eia_cl_events.csv`, `eia_cl_placebo.csv`.

## 4. Cross-index results (Study B) — 1-minute resolution

**Setup:**
- ES/NQ/RTY/YM, Sierra continuous 1-minute with exchange-aggressor bid/ask volume, RTH, ~19.7k minutes, 12 ordered pairs × h ∈ {1, 5}.
- A full 1-minute delay before the target window. Leave-one-week-out OOS.
- Baseline: the target's own returns (lags 1–5), 15-minute return, and own flow (lags 1–5).

| Quantity | Range across pairs |
|---|---|
| ΔR² from source lagged flow | **−0.17 to +0.04 pp** |
| Placebo (source flow 60 min earlier) | −0.10 to +0.20 pp |
| Placebo (previous day, same minute) | −0.10 to +0.06 pp |
| **Positive control** (contemporaneous source flow, leaked) | **+2.9 to +39.0 pp** — the pipeline has power |

**Fixed-decile economic check** (top/bottom 10% of the incremental prediction):
- Most moves are **wrong-signed** (e.g., RTY→NQ −3.1 ticks, t −3.7).
- The only right-signed ones with |t| > 2: ES→RTY h1 +0.49 ticks (t 2.8) and ES→YM h1 +0.56 ticks (t 2.6), i.e. **0.18–0.21× friction** (~2.7 ticks). Across 24 tests these are marginal.
- The open / midday / final-hour strata are in `cross_index_flow.json` (descriptive only).
- **Reading:** indexes co-move strongly within the minute, but lagged cross-market flow carries no usable information at ≥1-minute delay. Sub-minute cross-index lead-lag needs tick data (only NQ has it) → INSUFFICIENT.

## 5. Live tape results (Study C) — INSUFFICIENT DATA
- It needs the live recorder running.
- Historical NQ ticks exist, but they were already used by the absorption/footprint/initiative thread. Reusing them for sequence studies would contaminate that holdout.
- Not run.

## 6. Effect size vs friction

| Phenomenon | Conditional move | Uncertainty | Frequency | Stability | Friction | Move / friction | Class |
|---|---|---|---|---|---|---|---|
| CL EIA first minute (\|disp\|) | 18 ticks unsigned; direction unknown before release | — | 1 per week | — | ~2 ticks + commission [U for CL] | n/a (not directional) | INFORMATION (volatility), NOT TRADABLE AS IS |
| CL EIA post-first-minute continuation | −1.25 ticks | t −0.30 | 1 per week | No | ~2 ticks | 0.6 (wrong side) | **NO INFORMATION** (1 m) |
| CL EIA sub-minute | — | — | — | — | — | — | **INSUFFICIENT DATA** |
| Cross-index lagged flow (best pair) | +0.5 ticks | t 2.6–2.8 of 24 tests | ~400/pair/90 d | Placebo-level ΔR² | ~2.7 ticks | 0.18–0.21 | **INFORMATION BUT NOT ECONOMIC** (at best) |
| Live tape sequences | — | — | — | — | — | — | **INSUFFICIENT DATA** |

## 7. What we learned that we did not know before
1. Sierra's included history reaches back to **2011 at tick level** for all six target markets, at no extra charge [V doc]. Heimdall has used ~3.5 months of NQ ticks only.
2. Every non-NQ local file is **1-minute**, so sub-minute CL/ES/RTY/YM research is impossible until harvested.
3. Sierra's T&S API gives a gap-detectable **Sierra sequence**, unbundled-trade flags and quote updates. It does **not** give an exchange sequence number or a network receive time [V headers].
4. EIA moves CL about 2× within the first minute, but **nothing measurable remains after minute 1** at 1-minute resolution.
5. Cross-index flow is fully contemporaneous. The lagged version adds nothing at ≥1 minute.
6. Process: a uint32 wraparound in my first `.scid` reader flipped the sign of signed flow (corr −0.49). A sanity check caught it and it was fixed before any conclusion.

## 8. One best hypothesis: **NONE**
No phenomenon was causally plausible, repeatable, materially larger than friction, and outside the graveyard.

## 9. Exact next experiment (one)

**CL EIA at tick level.** Measurement only, pre-registered windows, no entries:
1. **Owner (GUI, ~15 min):**
   - Launch Sierra.
   - Set Intraday Data Storage Time Unit = 1 Tick.
   - Open CL front-month charts for the last 24 months of contracts (back up `CL*.scid` first; snapshot already taken).
   - Also add *Heimdall Tape Recorder (read-only)* to one live CL chart and one live NQZ26 chart.
   - Set Global Settings: Number of Time & Sales records to keep ≥ 100,000; chart update interval ≤ 100 ms.
2. **Me:**
   - Run `tools/sierra_tape_reader.py validate` and `fidelity` after one RTH session (recorder proof, pass/fail).
   - Then run the frozen EIA windows (pre-event, 0–5 s, 5–15 s, 15–30 s, 30–60 s, 1–2 min, 2–5 min) on ~100 events. Same metrics as §3; no thresholds.

## Artifacts
- `workspace/sierra_lab_2026-09-23/`: `scid_io.py`, `eia_cl_response.py/.json`, `eia_cl_events.csv`, `eia_cl_placebo.csv`, `cross_index_flow.py/.json`.
- `tools/sierra_acsil/HeimdallTapeRecorder.cpp` (+ `_64.dll`).
- `tools/sierra_tape_reader.py`, `tests/test_sierra_tape_reader.py`.
- `data/sierra/scid_snapshot_2026-09-23/`.
