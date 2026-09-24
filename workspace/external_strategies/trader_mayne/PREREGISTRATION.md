# PREREGISTRATION - Family B: coBMd1vk2Lo Trader Mayne HTF range / OB / LTF breaker

Frozen 2026-09-24 BEFORE any PnL was computed in this program. Code: `trader_mayne/strategy.py` + `common/harness.py` (hashes in `_program/PREREG_MANIFEST.json`). Source evidence: `trader_mayne/SOURCE_MATRIX.md`.

## Interpretations

| ID | HTF->LTF | Entry | Stop | Target | Mgmt | Expiry |
|---|---|---|---|---|---|---|
| B1_H4_M15_breaker | 4h->15m | LTF close above the swing high that generated a swept LTF swing low (after OB touch); entry <= 50% of range; min 2R | sweep extreme -1 tick | HTF range high | stop to BE at +2R | 30 HTF bars / HTF close beyond range low / target first |
| B2_H1_M5_breaker | 1h->5m | same | same | same | same | same |
| B3_D_H1_breaker | 1D->1h | same | same | same | same | same |
| B4_H4_OB_limit | 4h | limit at OB top (long) / bottom (short); min 2R; in discount | OB far edge -1 tick | range high | BE at +2R | same |

MNQ 24h, holds across sessions allowed (max 12 days). Both directions. 4 trials.

## Research assumptions (not source rules)
OB = <=3 consecutive opposite candles ending at the leg extreme; range low = leg extreme between broken swing and MSB; one attempt per setup; BE (not half) at 2R.

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
