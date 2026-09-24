# POC Sweep Reclaim — Pre-registration

Frozen before any outcome run on 2026-09-22.

## Source signal

LuxAlgo Library `poc-sweep-reclaim`, public Pine source retrieved through the
installed LuxAlgo MCP server at commit
`df8719c24318138d22f8125b0613e3495c32b586`.

## Data and split

- Instrument: MNQ, one contract.
- Source: existing `data/MNQ_1m.parquet`; no network calls.
- Parent bars: five-minute RTH bars, 09:30 through 15:59 America/New_York.
- Parent-bar POC: replay the Pine proxy exactly. Iterate the five chronological
  one-minute sub-bars, aggregate volume by sub-bar close, and keep the first
  price whose running aggregate strictly exceeds the previous maximum.
- Chronological split: first 60% of RTH sessions train, final 40% untouched
  holdout. Holdout is also split into four consecutive walk-forward buckets.

## Signal

For parent bar `t`, let `POC[t]` be its proxy POC.

- Buyside sweep on `t`: `high[t] > POC[t-1]` and
  `max(open[t], close[t]) < POC[t-1]`.
- Sellside sweep: `low[t] < POC[t-1]` and
  `min(open[t], close[t]) > POC[t-1]`.
- Bullish reclaim on `t+1`: buyside sweep on `t` and
  `close[t+1] > POC[t-1]`.
- Bearish reclaim: sellside sweep on `t` and
  `close[t+1] < POC[t-1]`.

## Execution wrapper

LuxAlgo defines the signal but not a complete strategy. Heimdall adds this
fixed wrapper before seeing results:

- Take only the first valid reclaim per RTH session; never overlap positions.
- Signal window: 09:40 through 15:30 ET.
- Market entry at confirmation close plus one adverse MNQ tick.
- Long stop one tick below swept POC; short stop one tick above it.
- Skip if entry is not on the valid side of the stop.
- Fixed target: 1R from slipped entry. This matches Heimdall's pre-existing
  near-1:1 prop-survival requirement; it is not claimed as LuxAlgo's exit.
- Stop fill: one additional adverse tick. Target fill: exact target.
- Session flatten: 15:55 ET close minus one adverse tick.
- Round-turn commission: $1.00; MNQ point value: $2.00.
- If stop and target occur in one five-minute bar, stop wins.

## Gates

Report train, untouched holdout, four holdout buckets, execution-tax-adjusted
win rate, realized payoff ratio, mean PnL, skew, maximum consecutive losses,
standard Heimdall gate, and Lucid Monte Carlo. No threshold or rule changes
after outcomes.
