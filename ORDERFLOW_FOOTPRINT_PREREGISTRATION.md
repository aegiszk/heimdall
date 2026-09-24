# Order-flow absorption v2 — price-level footprint pre-registration

Status: frozen before outcome inspection. V1 is dead and may not be tuned or
reopened. V2 is a materially different test enabled by Sierra one-trade records
with trade price and exchange-classified bid/ask volume at each price.

No threshold sweep or post-result revision is permitted. A later version needs
a named diagnostic, a new frozen document, and untouched data.

## Data and roll construction

- Source files: the full NQM26-CME, NQU26-CME, and NQZ26-CME Parquets listed in
  `data/sierra/MANIFEST.md`.
- Use only `ts`, `close` (trade price), `volume`, `bid_volume`, and
  `ask_volume`. Sierra SCID `high` and `low` are forbidden because the archive
  integrity check found frequent trade/quote inconsistencies.
- Fail closed unless every used record has `num_trades == 1`, non-negative
  volume, and `bid_volume + ask_volume == volume`.
- Sort by timestamp. The two documented NQU backward jumps are retained.
- Session label: America/New_York trading date; 18:00 ET belongs to the next
  trading date. Strategy data is RTH 09:30 through 16:00 ET.
- Contract order is NQM26, NQU26, NQZ26. Before an overlap, use the only
  contract available. During overlap, remain on the current contract until the
  next contract's *previous completed RTH session* volume exceeds the current
  contract's. Switch on the following session and never switch backward.
- Aggregate the selected contract into one-minute price-level cells, rounded
  to the exact 0.25 NQ tick: total, bid, and ask volume at each trade price.
- At least 20 complete prior RTH sessions are required.

## Prior-session value area

For each current session, derive POC and 68% value area from the selected
contract's previous complete RTH session using actual volume at trade price.

1. Sum volume at each 0.25 price.
2. POC is the highest-volume price; ties choose the lower price.
3. Starting at POC, add the immediately adjacent upper or lower tick with
   greater volume; ties add the lower tick first. Missing ticks have zero.
4. Stop at 68% of session volume. Extremes are VAL and VAH.

No current-session observation can affect these levels.

## Footprint absorption event

Signal bars are 09:30 through 15:30 ET. Maximum one trade per session; take the
earliest fully confirmed event.

For a short at prior VAH, the candidate minute must:

- trade at or above VAH and close at least one tick back below VAH;
- have at least 20 ask-side contracts in its two highest traded price levels;
- have ask volume in those two levels at least 3 times bid volume there, with
  denominator floored at one contract;
- concentrate at least 20% of the minute's ask volume in those two levels.

For a long at prior VAL, mirror the rule: trade at or below VAL, close at least
one tick back above VAL, and apply the same 20-contract, 3:1, and 20%
requirements to bid volume in the two lowest traded price levels.

The fixed 3:1 imbalance and 20% concentration express the source claim of
large aggressive effort at the extreme. The 20-contract floor prevents ratios
created by negligible volume. They are hypotheses, not calibrated values.

## Confirmation, execution, and costs

Within the next two one-minute bars, the first confirmation must:

- for a short: have negative delta, close below open, and close below the
  absorption minute midpoint;
- for a long: have positive delta, close above open, and close above the
  absorption minute midpoint.

Enter one MNQ contract at the next minute open plus one adverse 0.25 tick.
Skip if the next bar begins after 15:30 ET. Stop one tick beyond the absorption
trade-price extreme. Skip non-positive risk, risk below four ticks, or a loss
including costs above the fixed $325 daily buffer. Target is exactly 1R.

Conservative bar ordering: if stop and target are both reachable in one minute,
stop wins. Stop fills one adverse tick beyond its level. Target fills at its
level. Flatten at 15:55 ET close with one adverse tick. One MNQ point is $2;
subtract the confirmed $1.00 round-turn commission once per trade.

## Evaluation firewall and verdict

- One family, one fixed specification, zero parameter search.
- Chronological first 50% of selected sessions is train/report-only; the last
  50% is untouched holdout.
- Report event funnel, trade count, win rate, mean PnL, realized reward/risk,
  skew, maximum loss, exit reasons, and four chronological holdout buckets.
- Minimum 30 holdout trades; fewer is a frequency failure.
- Holdout win rate must be at least 50%, net mean PnL after all defined costs
  must be positive, and at least three of four holdout buckets must have
  positive mean PnL.
- Run the unchanged Lucid $325-buffer Monte Carlo. Its pass rate must exceed the
  settled 3.96% economic breakeven rate.
- Passing means only “candidate for paper shadow / longer untouched sample.”
  Any failed gate kills v2. Aggregate EV cannot override a gate.
