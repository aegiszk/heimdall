# PREREGISTRATION - Family E: ADnslyKOwFE Trident

Frozen 2026-09-24 BEFORE any PnL was computed in this program. Code: `trident/strategy.py` + `common/harness.py` (hashes in `_program/PREREG_MANIFEST.json`). Source evidence: `trident/SOURCE_MATRIX.md`.

## Interpretations

| ID | FVG window (middle candle open, ET) | Exit | Side |
|---|---|---|---|
| E1_long_kz0300_20R | 03:00-06:30 | fixed 20R target | long |
| E2_long_kz0300_emacross | 03:00-06:30 | 30m close with EMA5 < EMA21 | long |
| E3_long_fvg0230_20R | 02:30-06:30 | 20R | long |
| E4_short_mirror_20R | 03:00-06:30 | 20R | short (mirror; weak source) |

All: 30m ET bars; doji body <= 25% of range, low < FVG 50%, open & close >= FVG top; doji and confirmation inside
03:00-06:30; confirmation close < doji high; EMA 5>9>13>21 and close > EMA200 (30m) at confirmation; entry at the
confirmation close; FX stop = doji low - 1 pip; XAU = exit on 30m close below the doji low (+ catastrophic stop 3x
the doji range; R measured vs the doji low); max hold 10 days. Six instruments -> 24 trials.
Frequency-fidelity note (pre-PnL funnel): ~1 setup/yr/pair vs the creator's claimed 6-8 -> expected TOO_SPARSE.

## Research assumptions (not source rules)
doji threshold 0.25; 'body not inside the FVG' read as body above the gap; EMA200 on 30m; XAU catastrophic stop.

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
