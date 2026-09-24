# Order-flow absorption v1 — pre-registration

Status: frozen before outcome inspection. This document defines the only v1
candidate to be implemented and tested. No threshold sweep or post-result
revision is permitted. A later revision requires a named diagnostic, a new
pre-registration, and a clean untouched dataset.

## Source claim and testable reduction

Source: Rule Sheet 2 in `Trading Philosophy and Order Flow Analysis_ Structured
Rule Sheets.md`, based on https://youtu.be/Pz8f0wWW12M.

The source is explicitly discretionary. Its testable sequence is:

1. Price reaches a pre-defined volume-profile level.
2. Aggressive volume pushes into the level with high effort but low price result.
3. Opposite aggressive volume produces directional price result within about
   three minutes.
4. Enter the reversal, stop beyond the absorption area, target at least 2R.

This v1 tests a bar-level mechanical proxy. Sierra Package 3 bars do not contain
MBO, queue state, or price-by-price footprint cells. A failure kills this proxy;
it does not prove a skilled discretionary footprint reader has no edge.

## Data and instrument

- Signal and execution instrument: MNQ continuous one-minute bars from
  `data/sierra/MNQ_continuous_1m_latest_90d.parquet`.
- Required columns: open, high, low, close, volume, bid_volume, ask_volume,
  delta. Delta is ask_volume minus bid_volume.
- Time zone: UTC index converted to America/New_York for session rules.
- Session: weekdays, 09:30 through 16:00 ET. New entries are allowed from 09:30
  through 15:30 ET. All positions flatten no later than 15:55 ET.
- At least 20 complete prior RTH sessions are required before any signal.
- Maximum one entry per session; take the earliest valid setup.

## Prior-session volume-profile proxy

The key levels are the previous complete RTH session's 68% value-area high and
low. Because the export has bar volume rather than volume-at-price, allocate
each one-minute bar's entire volume to its close rounded to the nearest 1.00 NQ
point (four ticks). This limitation must appear in every report.

1. Sum volume by rounded close-price bucket.
2. POC is the highest-volume bucket; ties choose the lower price.
3. Starting at the POC, repeatedly add the immediately adjacent upper or lower
   bucket with greater volume; ties add the lower bucket first.
4. Stop when included volume is at least 68% of session volume.
5. The lowest and highest included bucket prices are prior VAL and VAH.

No current-session data may affect these levels.

## Rolling effort baselines

For each current-session bar, compute baselines from all RTH one-minute bars in
the previous 20 complete sessions only:

- `abs_delta_q90`: 90th percentile of absolute delta.
- `abs_delta_q75`: 75th percentile of absolute delta.
- `range_median`: median of high minus low.

Percentiles use pandas' default linear interpolation. Zero-volume bars are kept;
non-finite or negative volume fields fail closed.

## Short setup at prior VAH

An absorption bar must satisfy all conditions:

- high is at least `VAH - 1.00`;
- close is at or below VAH;
- delta is positive and absolute delta is at least `abs_delta_q90`;
- bar range is positive and no greater than `range_median`.

Within the next three one-minute bars, the first confirmation bar must satisfy:

- delta is negative and absolute delta is at least `abs_delta_q75`;
- close is below open;
- absolute body is at least 50% of the bar range;
- close is below the absorption bar's midpoint.

## Long setup at prior VAL

Mirror the short rules:

- low is at most `VAL + 1.00`;
- close is at or above VAL;
- delta is negative and absolute delta is at least `abs_delta_q90`;
- bar range is positive and no greater than `range_median`;
- confirmation within three bars has positive delta of at least
  `abs_delta_q75`, closes above its open, has body at least 50% of range, and
  closes above the absorption bar's midpoint.

## Entry, stop, target, and costs

- Enter one MNQ contract at the next one-minute bar open, plus one adverse tick
  for longs or minus one adverse tick for shorts. If no next bar exists before
  15:30 ET, skip.
- Initial stop is one tick beyond the absorption bar extreme.
- Skip if entry-to-stop distance is non-positive or the one-contract stop loss,
  including the $1.00 round-turn commission, exceeds the $325 daily buffer.
- Fixed target is 2R from entry.
- After price reaches +1R, move the stop to entry for later bars.
- If stop and +1R/target are both possible in one bar, apply the adverse ordering:
  initial stop first, then target; breakeven activates only for later bars.
- Stop gaps fill at the worse of the bar open or one tick through the stop.
- Ordinary stop fills include one adverse tick. Target fills at the target.
- Session flatten fills at 15:55 close with one adverse tick.
- Subtract $1.00 round-turn commission exactly once per trade.

## Evaluation firewall and verdict

- One family, one fixed specification, zero free strategy parameters.
- Chronological first 50% train / last 50% untouched holdout.
- Train is used only for a gross sanity report, not selection or threshold edits.
- Report holdout trade count, win rate, mean PnL, realized reward/risk, skew,
  maximum loss, exit reasons, and four chronological walk-forward bucket means.
- Run the existing validation battery and Lucid prop Monte Carlo with the fixed
  $325 buffer and existing risk-engine rules.
- Minimum evidence gate: at least 30 holdout trades. Fewer is a frequency fail,
  regardless of aggregate PnL.
- Stability gate: at least three of four walk-forward holdout buckets must have
  positive mean trade PnL. Aggregate EV cannot override this gate.
- Execution gate: net mean PnL after the defined costs must be positive and must
  clear the known stop-slippage tax.
- No result may be described as proven profitable from this 90-day archive.
  Passing makes it a candidate for a longer untouched sample or paper shadow;
  failing kills v1.
