# AGENT2 DATA GAPS (checker-side, independent of Agent 1's requests)

Rule: $0 and owned sources first. A paid request must name the provider, dataset, schema, fields, dates, bytes, cost and the strategy it unblocks. **No paid download is requested in this file.** Prices marked [U] are UNVERIFIED and need a live quote before any owner decision.

## 0. Hard constraint on all eight families until Dhesi completes

CME equity-index rows (NQ/ES/YM/RTY and micros) **before 2024-07-01 are reserved** for the Dhesi one-shot run. External-strategy research on index futures may use only:
- `data/{MNQ,MES,ES}_1m.parquet` (2024-07-01 → 2026-06-30, DEVELOPMENT);
- Sierra 2026 per-contract `.scid` / 90-day exports (CONSUMED/DEVELOPMENT).

About 2 years of 1-minute data is thin for HTF-driven setups. Family B's D/H1 or W/D pairs yield only a few dozen setups a year. This limitation is structural until the Dhesi run completes and the window becomes REUSED_HOLDOUT.

## 1. Owned / subscription-covered ($0 marginal)

| Need | Source | Status | Families |
|---|---|---|---|
| NQ + ES 1m synchronized (SMT) | `data/MNQ_1m.parquet` + `data/ES_1m.parquet` (dev) | OWNED | A, B, C |
| YM 1m (Liquidity-Trap example market) | Sierra MYM/YM 2026 `.scid` (≈90d–4 mo) | OWNED, short | A |
| CME FX futures 6E/6J/6C/6B, micro M6E; GC/MGC 1m, 2008+ | Sierra CME historical service, included in current subscription per `SIERRA_HARVEST_PLAN.md` [V, Sierra docs as cited there] | **NOT YET HARVESTED**. Owner GUI step, no reserved-data conflict (not equity index) | E (Trident, FX + gold, 03:00–06:30 NY), F (MMXM/OTE, FX), A (EURUSD example) |
| DXY proxy | CME `DX` futures (ICE, not CME) — **not** in the CME entitlement [U]; fallback: build a DXY-weighted basket from 6E/6J/6B/6C/6S futures | GAP (fallback $0) | F (DXY context mention only) |
| Long daily index history (1929, 2000, 2008 crash examples) | Free daily index history (e.g. Stooq/FRED) [U: coverage and licence to verify] | GAP ($0 candidates) | D (crash-bottom reversal) |

**User note (2026-09-24): "pull up more data if needed, we have Sierra subscription."**
- CME FX/metals history for E and F is the first harvest to do. It is covered, not reserved, and needed.
- Agent 2 did **not** start that harvest. It needs the Sierra GUI: Sierra is not running and no DTC port is listening, verified 2026-09-24. Sierra's storage-unit setting can affect existing `.scid` files (documented hazard in `SIERRA_HARVEST_PLAN.md`).
- The NQ untouched harvest for Dhesi must be done by the **owner**, not by an agent watching the screen. Rendering 2011–2024 NQ charts to an agent is a reserved-data read (protocol §2.4).

## 2. Blocked — not solvable with owned/free data at adequate fidelity

### G — `SQEtBHOJW6I` (Jay Ortani, large-cap stock tape reading)
- The source edge is reading **time-and-sales aggressor flow and the Bookmap order book** at key levels on TSLA/NVDA/AMD/ARM, often executed in same-day options.
- Needed:
  - US equity trades with aggressor side plus L2/MBO book for the named tickers;
  - options quotes if options execution is replicated.
- Paid candidate: Databento `XNAS.ITCH`, schemas `trades` + `mbp-10`, symbols TSLA/NVDA/AMD, 2024-07 → 2026-06. Bytes and cost [U] — a quote is needed.
- **Also out of mission scope:** Lucid 50K FLEX is a futures account. Stocks and options cannot be traded there (CLAUDE.md §3).
- **Recommendation:** BLOCKED_DATA + OUT_OF_SCOPE. Do not buy.

### H — Small-cap shorts (Gap-Up Short, Bounce Short, First Red Day)
Part M requires point-in-time data. Status of each input:

| Required point-in-time field | $0 source | Adequate? |
|---|---|---|
| Daily + intraday OHLCV incl. **delisted** tickers | none free at intraday; paid: Databento `DBEQ`/`XNAS.ITCH`, Polygon flat files [U cost] | NO |
| Shares outstanding (for cap) | SEC EDGAR XBRL `dei:EntityCommonStockSharesOutstanding`, dated by filing | PARTIAL: quarterly steps, misses dilution between filings (offerings are the norm in this universe) |
| Float | 10-K public float (annual, $ not shares) | NO for 1–50M float screens |
| Corporate actions / reverse splits | EDGAR 8-K text | PARTIAL, manual |
| Halts (LULD, T1/T12) | Nasdaq Trader halt history [U: depth] | PARTIAL |
| SSR (Rule 201) | derivable from prior close −10% | YES once prices exist |
| **Borrow availability / locate fee / HTB history** | none free; broker current-day files only | **NO — irreducible** |
| Premarket volume (GS >50M filter) | needs extended-hours trades | paid only |

- **Verdict: BLOCKED_DATA.** Short availability cannot be faked (Part M).
- It is also **out of scope**: the Lucid futures account cannot short equities.
- **Recommendation:** do not buy until the owner decides a separate equity-short account is in scope.

### D — Little Rizzy crash-bottom reversal
- The data is not the blocker; **event count** is. The source examples are 1929, 2000, 2008, 2018, 2020 and 2025, so perhaps ≤ 10 qualifying events per century on HTF.
- No data purchase can make that statistically testable.
- **Verdict: UNTESTABLE_SAMPLE**, independent of data.

## 3. Summary

| Family | Data state | Action |
|---|---|---|
| A Liquidity Trap | OWNED (NQ/ES dev); YM short | none |
| B Trader Mayne | OWNED (dev); HTF pairs thin in 2 yrs | none until Dhesi done |
| C PO3/50% | OWNED (NQ+ES dev, synchronized) | none |
| D Little Rizzy | continuation: OWNED; crash-bottom: untestable n | free daily history optional |
| E Trident | **needs CME FX + GC 1m harvest** ($0, Sierra) | owner GUI harvest |
| F MMXM/OTE | **needs CME FX 1m harvest** ($0, Sierra); DXY fallback basket | owner GUI harvest |
| G Ortani tape | BLOCKED_DATA + OUT_OF_SCOPE | none |
| H Small-cap shorts | BLOCKED_DATA + OUT_OF_SCOPE | none |
