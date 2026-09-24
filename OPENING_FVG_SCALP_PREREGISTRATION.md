# Opening-Range FVG Scalp — Pre-registration

Frozen before any outcome run on 2026-09-22.

## Source signal

Casper Trading video `WEhmadJArQo`, transcript retrieved on 2026-09-22. The
video specifies the 09:30 five-minute range, one-minute FVG breakout, FVG
retest, engulf confirmation, stop one tick beyond the deepest retest, and 3R
target. The mechanical interpretations below resolve visual-only ambiguity
before results.

## Data and split

- Instrument: MNQ, one contract.
- Source: existing `data/MNQ_1m.parquet`; no network calls.
- RTH session: America/New_York.
- Chronological split: first 60% of RTH sessions train, final 40% untouched
  holdout; four consecutive holdout walk-forward buckets.

## Signal

- Opening range is the 09:30 through 09:34 ET candle high and low.
- Bullish FVG at minute `t`: `low[t] > high[t-2]`; the confirmation candle
  closes above the opening-range high. Gap is `[high[t-2], low[t]]`.
- Bearish FVG: `high[t] < low[t-2]`; confirmation closes below opening-range
  low. Gap is `[high[t], low[t-2]]`.
- Use the first qualifying FVG after 09:35. It expires at 11:00 ET.
- Retest is the first later one-minute candle whose range overlaps the gap.
- Bullish engulf confirmation is the first later bullish candle with body high
  strictly above the retest candle body high and body low no higher than the
  retest candle body low. Bearish is mirrored.

## Execution

- First completed setup per session only; no overlapping trades.
- Market entry at engulf close plus one adverse MNQ tick.
- Long stop one tick below the minimum low from retest through engulf; short
  stop one tick above the maximum high.
- Fixed target: 3R from slipped entry, as stated in the video.
- Stop fill: one additional adverse tick. Target fill: exact target.
- Session flatten: 15:55 ET close minus one adverse tick.
- Round-turn commission: $1.00; MNQ point value: $2.00.
- If stop and target occur in one bar, stop wins.

## Gates

Same untouched holdout, walk-forward, execution-tax, Heimdall gate, and Lucid
Monte Carlo reporting as the POC test. No post-result changes.
