# PREREGISTRATION - Family A: DAnXM7C16h0 liquidity-trap reversal

Frozen 2026-09-24 BEFORE any PnL was computed in this program. Code: `liquidity_trap/strategy.py` + `common/harness.py` (hashes in `_program/PREREG_MANIFEST.json`). Source evidence: `liquidity_trap/SOURCE_MATRIX.md`.

## Interpretations

| ID | Instr./TF | Session | Dir | Entry | Stop | Target | Mgmt | Params |
|---|---|---|---|---|---|---|---|---|
| A1_k1_spike_nearest | MNQ 5m signal / 1m fill | entries 09:30-11:30 ET, flat 12:00 | both | stop order 1 tick beyond internal swing | anchor +/- 2 ticks | nearest untaken opposing swing | none; pending expires 11:30 | k=1 |
| A2_k2_spike_nearest | same | same | both | same | same | same | same | k=2 |
| A3_k1_spike_split | same | same | both | same | same | 50% nearest, 50% 2nd | BE after first partial | k=1 |
| A4_k1_close_nearest | same | same | both | close of the first 5m bar that spikes the level and closes back | same | nearest | same | k=1 |
| A1 YM replication | YM Sierra 90d, tick 1.0 | same | both | as A1 | as A1 | as A1 | as A1 | k=1 |

Mechanism: stops rest beyond respected swings; an extreme that swept an older swing holds none. Re-entry allowed when flat. 5 trials.

## Research assumptions (not source rules)
pivot width k; anchor = pivot whose own bars took an older confirmed swing; lookback current+previous session day; window 09:30-11:30 / flat 12:00; no news filter (no calendar on disk).

## Common protocol (all interpretations in this family)
- Cost model (`common/harness.py` SPECS): futures trade prices; market/stop fills +1 tick adverse; stop exits +1 tick
  adverse (gap-through fills at the worse open); limits need a 1-tick trade-through; commission MNQ $1.00 RT, ES
  $3.50 RT, YM $3.50 RT (YM = ASSUMPTION). FX/XAU: HistData BID bars; ask = bid + modelled spread (EURUSD 0.3,
  GBPUSD 0.6, USDJPY 0.4, USDCAD 0.6, NZDUSD 0.7 pips; XAU $0.20); +0.2 pip ($0.05 XAU) slippage on market/stop
  fills; $7 per lot RT commission. ALL FX costs are RESEARCH ASSUMPTIONS; x1.25/x1.5/x2 re-simulated.
- Same-bar semantics: stop beats target in the same minute; no target credit in the entry minute; an entry minute
  that also touches the stop is a stop-out; pending entries cancel if the stop level trades first.
- Rolls: Databento continuous MNQ/ES Panama back-adjusted at instrument_id changes (gap = first open of the new
  contract minus last close of the old; error <= one minute's move); YM Sierra roll 2026-09-14 00:00 UTC.
- Sequencing: every order resolved independently; one position at a time per interpretation+instrument; first FILL wins.
- Windows: MNQ/ES DEV 2024-07-01..2026-06-30 (REUSED, diagnostic only); YM Sierra 2026-06-24..2026-09-21 (REUSED);
  FX/XAU DEV 2022-01-01..2024-12-31; FX/XAU FRESH 2025-01-01..2026-08-31 SEALED (not read).
  DHESI firewall: no NQ/MNQ/ES/MES data before 2024-07-01 is read (`load_futures` asserts).
- Role: every result here is DEVELOPMENT evidence. Nothing here validates.
- Metrics: net R per trade (R = net / |fill - initial stop|; XAU close-stop designs vs the declared invalidation),
  NW t, date-clustered bootstrap 95% CI, and the work-order section 10 list.
- Falsification (fixed now, per interpretation): ROBUSTLY_REJECTED if n >= 30 and mean net R <= 0 with the 95%
  cluster-bootstrap upper bound < +0.05R; INCONCLUSIVE if n < 30 or the CI straddles 0 without positive evidence;
  CANDIDATE only if mean net R > 0, NW t > 2, cost x1.5 still > 0, drop-top-5 still > 0 and >= 2/3 of calendar
  years positive; candidates then face the section-14 adversarial battery before any SURVIVING label.
- No parameter may change after PnL is seen. A changed rule = a new hypothesis ID.
