# Sierra untouched-history harvest — smallest GUI procedure (Agent 2)

**Entitlement [V, Sierra docs]:**
- CME/NYMEX/COMEX/CBOT tick-by-tick history from 2011 (1-minute from 2008-06) is included with the Standard/Advanced service at no extra charge.
- Intraday continuous charts load up to 15 years.
- Package 3 already downloaded NQ ticks [V]. Nothing to buy.

**Backups (done before any download):**
- `data/sierra/scid_snapshot_2026-09-23/` holds 44 futures `.scid` files with SHA-256 in `INVENTORY.json`.
- `data/sierra/tick_raw/` holds NQM26/NQU26.

**Destructive-risk rule:** Sierra does not document what happens to an *existing* `.scid` when the storage unit changes. So every chart below points only at contracts that **do not exist on disk**:
- Index roots: contracts ≤ June 2024. The local index files are all 2026 contracts.
- CL/GC: contracts ≤ May 2026 (CLK26 / GCJ26). Local CL starts at CLM26, local GC at GCM26.

| Priority | Roots | Window | Storage | Chart symbol (continuous, loads backwards) | Days to Load | Est. contracts | Est. disk [I] | Why this resolution |
|---|---|---|---|---|---|---|---|---|
| 1 | MNQ + NQ | 2019-01 → 2024-06 | 1 Minute | `MNQM24-CME`, `NQM24-CME` | 2,100 | 22 each (MNQ from Jun-19 contract) | ~0.1 GB each | Dhesi v3 is 1-minute OHLCV. NQ gives pre-May-2019 warmup (MNQ listed 2019-05). |
| 2 | ES + MES | 2019-01 → 2024-06 | 1 Minute | `ESM24-CME`, `MESM24-CME` | 2,100 | 22 each | ~0.1 GB each | Not in Dhesi v3 (MNQ only); future use |
| 3 | RTY + M2K | same | 1 Minute | `RTYM24-CME`, `M2KM24-CME` | 2,100 | 22 each | ~0.1 GB each | future use |
| 4 | YM + MYM | same | 1 Minute | `YMM24-CBOT`, `MYMM24-CBOT` | 2,100 | 22 each | ~0.1 GB each | future use |
| 5 | CL | 2024-05 → 2026-04 | **1 Tick** | `CLK26-NYMEX` | 760 | ~24 monthly | ~3–6 GB | EIA 0–1 s … 1–2 min windows need ticks |
| 6 | GC | 2024-05 → 2026-03 | 1 Tick | `GCJ26-COMEX` | 760 | ~12 active months | ~2–4 GB | if disk/time permit |

**Roll treatment** (fixed now; applied offline when building the validation parquet):
- Per-contract files are kept verbatim. The continuous series is built by **prior-session volume leader, non-back-adjusted**. This matches the development data's Databento `MNQ.v.0` construction and the existing Sierra archive rule.

## GUI steps (owner, ~10 charts total)
1. Global Settings → Data/Trade Service Settings → Common Settings → **Intraday Data Storage Time Unit = 1 Minute**. Note the current value first so it can be restored.
2. For each row 1–4 symbol:
   - File → New Chart.
   - Chart → Chart Settings → Symbol = the symbol above.
   - **Continuous Futures Contract = Volume Based Rollover**, back-adjust OFF.
   - Data Limiting → **Days to Load = 2100** → OK.
   - Wait until the chart stops downloading.
3. Change the storage unit to **1 Tick**. Repeat step 2 for `CLK26-NYMEX` then `GCJ26-COMEX` with Days to Load = 760.
4. Restore the storage unit to the value noted in step 1.
5. **Do not** open any 2026-contract chart while the storage unit is on a non-default value.
6. **Do not scroll or visually inspect the 2019–2024 index charts.** They are the untouched validation period. Close them once loaded.
7. Tell Agent 2. I run `scid_integrity.py` (timestamps/metadata only), then build and hash the continuous validation parquet. The owner/agent does not look at prices.

**Honesty note:** the owner seeing the charts while they download is unavoidable GUI exposure. It must be recorded, but it is not an outcome query. Minimise it by closing charts after download.

## REVISION 2 (firewall work order)

**Verified depth bounds** (Sierra docs + CME listing notices; exact first-record dates are set by `scid_integrity.py` after download):

| Root | Earliest possible | Basis |
|---|---|---|
| NQ, ES (CME), YM (CBOT), CL (NYMEX), GC (COMEX) | **1-minute from 2008-06**; tick from 2011 per one sentence of the doc, "at least ~2013" per another (**UNRESOLVED doc conflict**) | Sierra `SierraChartHistoricalData.php` |
| RTY | **2017-07-10** | Russell 2000 returned to CME that day (CME press release 2017-04-12); before that it traded on ICE |
| MNQ, MES, M2K, MYM | **2019-05-06** | Micro E-mini launch (CME clearing notice Chadv19-118) |

Intraday continuous charts are limited to 15 years, so one chart ending at June 2024 reaches back to about 2009-07. 2008-06 → 2009-06 needs a second NQ chart (symbol `NQM09-CME`, Days to Load 400).

| Priority | Chart symbol | Continuous | Days to Load | Storage | Contracts generated | Est. disk [I] |
|---|---|---|---|---|---|---|
| **PRIMARY** | `NQM24-CME` | Volume Based Rollover, no back-adjust | 5,475 (15 y) | 1 Minute | ~60 quarterly (NQU09 … NQM24) | ~0.25 GB |
| PRIMARY (depth) | `NQM09-CME` | same | 400 | 1 Minute | ~5 | ~0.02 GB |
| PRIMARY (micro economics cross-check) | `MNQM24-CME` | same | 1,880 | 1 Minute | 21 (MNQM19 … MNQM24) | ~0.08 GB |
| Secondary | `ESM24-CME`, `MESM24-CME` | same | 5,475 / 1,880 | 1 Minute | ~60 / 21 | ~0.25 / 0.08 GB |
| Secondary | `RTYM24-CME`, `M2KM24-CME` | same | 2,550 (from 2017-07) / 1,880 | 1 Minute | ~28 / 21 | ~0.1 / 0.08 GB |
| Secondary | `YMM24-CBOT`, `MYMM24-CBOT` | same | 5,475 / 1,880 | 1 Minute | ~60 / 21 | ~0.25 / 0.08 GB |
| Exploratory (not Dhesi) | `CLK26-NYMEX` | same | 760 | **1 Tick** | ~24 monthly | 3–6 GB |
| Exploratory | `GCJ26-COMEX` | same | 760 | 1 Tick | ~12 | 2–4 GB |

**Roll behavior:**
- The raw files stay per contract.
- The canonical series is built offline by `blind_build.py`: prior-session volume leader, never backward, no back-adjust, hard end 2024-06-30.
- Tested on already-seen 2026 MNQ files: roll dates 2026-06-16 (M→U), which matches the MANIFEST NQ roll, and 2026-09-16 (U→Z).
- Tick-stored contracts are aggregated to 1-minute bars from the trade price only.

**Backup:** 44 futures `.scid` files were re-verified byte-identical to `data/sierra/scid_snapshot_2026-09-23/INVENTORY.json` today.
