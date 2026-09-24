# Dhesi Inversion Model v3 — Pre-registration

Frozen on 2026-09-22 before any v3 outcome was computed. v2
(`core/alpha/inversion_model.py`) stays unchanged as the historical record.

## Why v3 exists: defects found in v2

These were found by reading the v2 source and its trade log
(`data/prop_futures/inversion_model_MNQ_1m_trades.csv`, 30 MNQ trades,
−$446.38 over the whole period).

1. **HTF candles were wrong.** 4H/1H bars were built from RTH-only minutes on a
   midnight clock, so the 4H candles were 09:30-12:00 and 12:00-16:00. Dhesi's
   4H candle opens at 10:00 ET on the 24-hour futures chart (rule sheet §1).
   Result: no v2 entry happened before 12:05 ET, and 10 of 30 trades were
   flattened at the close without reaching stop or target. Overnight bars were
   also dropped, which creates false gaps between sessions.
2. **Pre-10:00 sweeps were discarded.** The 10:00 rule is an entry filter (§1,
   §6). v2 also discarded any liquidity sweep before 10:00.
3. **Session liquidity was missing.** Dhesi names "session highs and lows" as a
   pool (§2 step 1). v2 had no Asia or London pools.
4. **Wrong-side stops (bug).** In 5 of 30 trades the stop was on the wrong side
   of entry. Risk was measured with `abs()`, so these trades stopped out
   instantly.
5. **Tiny stops lose to friction (bug-class).** A 0.25-point and a 3-point stop
   sized to 40 contracts and lost $100 and $300 to commission and slippage.
6. **One trade per day is stricter than the source.** Dhesi's stated rule is
   two losses and done; after one win and one loss he takes a third try (§5).

## v3 rules

Everything not listed here is identical to v2: equal-high/low clustering, the
30-point HTF displacement body, the 20-session FVG lookback, 15m retracement,
5m LTF inversion entry, 15m-swing stop, TP1 promotion to 1.5R, 50% trim, and
breakeven on the runner.

- **HTF bars:** built from all 24-hour minutes. 4H bins start at 18:00 ET
  (18:00, 22:00, 02:00, 06:00, 10:00, 14:00 wall clock); 1H bins start on the
  hour. A bin contains the minutes whose start time lies inside it, and its
  event timestamp is the bin end. A bin belongs to the RTH session on the ET
  date of (bin end − 1 minute + 6 hours).
- **Pools** add `asia_high/low` (20:00-23:59 ET the evening before the session)
  and `london_high/low` (02:00-04:59 ET on the session date), from 24-hour data.
- **Sweeps** count from 09:30 ET. New entries still require an LTF inversion at
  or after 10:00 ET.
- **Stop validity:** skip the setup unless the stop is on the protective side
  and at least 10.0 MNQ points from the slipped entry. The 10-point floor comes
  from friction, not results: with 2 ticks of slippage plus $1 round-turn
  commission per contract, friction is at most 10% of dollar risk.
- **Attempts:** at most 3 trades per session, one position at a time, stop after
  2 losses. Each later attempt needs a sweep and an entry after the previous
  exit.
- **Instrument:** MNQ only. ES/MES are not tested; v2's displacement bug on
  those contracts is not fixed here.

## Data and evaluation

- **Development (already seen by v1/v2, NOT evidence):** `data/MNQ_1m.parquet`,
  2024-07-01 → 2026-06-30, 60/40 chronological split with four holdout buckets.
  Reported for diagnosis and ablation only.
- **Fresh window (never seen by any Dhesi version):** `data/MNQ_1m.parquet`
  history to 2026-06-30 for lookback, stitched to
  `data/sierra/MNQ_continuous_1m_latest_90d.parquet` from 2026-07-01 00:00 UTC.
  Only trades from 2026-07-01 through the last complete RTH session count.
  Before any trades are computed, overlap closes (2026-06-23 → 06-30) must match
  on at least 95% of minutes. Otherwise the fresh window is invalid and is not
  run.
- **Costs:** unchanged. One adverse tick on entry, stop and flatten; gap
  through the stop; $1.00 round-turn per contract; the same bar resolves as the
  stop.
- **Gate and Monte Carlo:** the same metrics, gate and Lucid 10,000-run
  simulation as `tools/validate_inversion_model.py`, with up to 3 trades per
  day.

## Decision rule (fixed now)

- **v3 is DEAD** if any of these is true: development whole-period mean
  PnL/trade ≤ 0; development holdout mean ≤ 0; fewer than 3 of 4 development
  holdout buckets ≥ $0; or fresh-window mean ≤ 0.
- **If none is true, v3 is a SURVIVING RESEARCH CANDIDATE, not validated.** The
  development data was seen before, and the fresh window is too short to
  confirm. It can only falsify. Validation would need forward paper trading
  from 2026-09-22.
- Ablations (each fix alone) are reported only to show where any change comes
  from. They cannot be picked as the result.
- **No v4 on this data.** If v3 dies, the thread closes on this data.
