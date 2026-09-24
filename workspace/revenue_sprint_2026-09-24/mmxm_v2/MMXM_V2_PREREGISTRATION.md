# MMXM_V2_PREREGISTRATION

Hypothesis ID: MMXM_V2. Frozen 2026-09-24 BEFORE any V2 PnL. BASE_SHA a1486c4738bb96babaed396fe9163a86a679506b.
Mechanism (source claim): with a weekly bias, a run of a previous-day/week key level near the day open, followed by a
displaced 15m body close through structure (smart-money reversal), retraces into the OTE and delivers to the leg extreme.
Spec: `MMXM_V2_SOURCE_SPEC.md` (M1-M10, context, assumptions). Code: `mmxm_v2/strategy.py`, `Cfg()` defaults ONLY:
ote 0.62, stop 0.90, BE close beyond 0.20, displacement body >= 50%, expiry 17:00 NY end of FX day, max hold 3 days.
Instruments EURUSD GBPUSD USDJPY; 15m signal / 1m fill; sells in bearish weeks, buys in bullish weeks.
Entry: limit at 0.62 placed when the displacement leg's swing is confirmed. Stop 0.9. Target 0 (leg extreme).
Alternatives: exactly 1 interpretation. Fidelity: PASS (all stated rules implemented or declared not-implemented as
non-entry refinements: second leg, scaling, ADR, HTF PDAs).
Falsification: DEV gate FAIL -> KILLED; sealed FAIL -> KILLED.

## Data and roles
| Window | Dates (UTC) | Role | Status |
|---|---|---|---|
| DEV | 2022-01-01 .. 2024-12-31 (45-day indicator warm-up before start; signals counted inside only) | development gate | already read by V1 (E1-E4 / F1-F3) -> NOT blind |
| SEALED | 2025-01-01 .. 2026-08-31 | one-shot validation | UNREAD; opened at most once, only after DEV PASS + Agent 2 audit PASS + registered trial |
Dataset: HistData 1m BID parquets `data/fx_histdata/<PAIR>_1m_bid.parquet` (bulk-data-v1); SHA-256 in `V2_PREREG_MANIFEST.json`.
Spot FX/XAU: no rolls. Timestamps EST-no-DST -> UTC per vendor documentation.

## Execution / cost model (frozen, `workspace/external_strategies/common/harness.py` SPECS, unchanged)
BID bars; ask = bid + spread (EURUSD 0.3, GBPUSD 0.6, USDJPY 0.4, USDCAD 0.6, NZDUSD 0.7 pips; XAU $0.20); +0.2 pip ($0.05 XAU)
slippage on market/stop fills; $7 per lot round trip. ALL are research assumptions. Same-bar: stop beats target; no target
credit in the entry minute; entry minute touching the stop = stop-out; pending limit cancelled if the stop level trades first.
One open position per instrument; first fill wins. Close-event exits fill at the 1m close ending the signal bar.

## Statistics (pooled across instruments; one model = one trial)
n, trades/yr, mean/median/10%-trimmed-mean net R, PF, NW t, date-clustered bootstrap (4,000, seed 7) 95% CI and share of
bootstrap means > 0, max DD (R), top-1/top-5 share, drop-top-5 mean, per-year and per-pair tables, cost x1.5 and x2
(re-simulated), one-bar delay (signal +1 bar; close entries become market), stop-slip x3.

## DEVELOPMENT GATE (frozen; all required)
n >= 30; mean net R > 0; median R >= -1.05; drop-top-5 mean > 0; NW t > 1.5; >= 80% of cluster-bootstrap means > 0;
cost x1.5 mean > 0; >= 2/3 of eligible years (>= 5 trades) positive and >= 2 eligible years; fidelity status accepted.
DEV FAIL -> model KILLED (no rescue, no variant). One corrected cycle only (addendum G).

## SEALED ONE-SHOT GATE (frozen)
PASS iff: mean net R > 0; cluster-bootstrap 95% lower > 0; drop-top-5 > 0; cost x1.5 > 0; max single trade <= 25% of total
net R; >= 2/3 of eligible half-years (>= 3 trades) positive and >= 2 eligible half-years.
FAIL iff mean <= 0 or bootstrap 95% upper < +0.05R. Otherwise INCONCLUSIVE (prospective evidence only, no historical rescue).
Execution plausibility is checked separately in the CME translation study; spot PASS is not deployable on Lucid by itself.

## Trial accounting
Local: EXT8 program 62 looks (58 valid + 4 invalid) incl. V1 E (24) and F (9); V2 adds 1 DEV look per model and at most 1
sealed look per model. Global: all ledger configs (Agent 2 count 433 at 2026-09-24) — DSR reported at both.
Registration: `V2-<MODEL>-DEV` and `V2-<MODEL>-SEALED` in data/trials_ledger.json after Agent 2's ledger PR merges (hash-chain
coordination); the sealed run refuses without its registered id.
