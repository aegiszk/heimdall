# PREREGISTRATION - Family C: HNuRp9Z1bMs 50% rebalance / PO3

Frozen 2026-09-24 BEFORE any PnL was computed in this program. Code: `po3_50/strategy.py` + `common/harness.py` (hashes in `_program/PREREG_MANIFEST.json`). Source evidence: `po3_50/SOURCE_MATRIX.md`.

## Interpretations

| ID | Exec TF | Range low | H4 PO3 required | Stop | Target | BE | Flat |
|---|---|---|---|---|---|---|---|
| C1_3m_overnight | 3m | extreme since 18:00 ET | no | NQ extreme since 10:00 +/- 1 tick | 50% of [range low, extreme] | last completed 15m candle extreme taken | 16:00 ET |
| C2_3m_overnight_H4 | 3m | since 18:00 | yes | same | same | same | same |
| C3_5m_overnight | 5m | since 18:00 | no | same | same | same | same |
| C4_3m_h4range | 3m | previous H4 bin 06:00-10:00 | no | same | same | same | same |

Entry (all): first exec-TF close through the inversion-FVG edge, 10:00-11:30, after NQ swept its 09:00-hour extreme
during the 10:00 hour while ES had NOT swept its own 09:00-hour extreme (checked through entry). One setup per side
per day. MNQ traded, ES for SMT. 4 trials. Tue-Thu subset is descriptive only.
Frequency-fidelity note (pre-PnL): ~20 setups/yr vs the creator's "most days".

## Research assumptions (not source rules)
manipulation hour 10:00-11:00; SMT window 10:00 to entry; inversion FVG = most recent same-direction 3-candle FVG after 09:30 ending by the manipulation extreme; flat 16:00.

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
