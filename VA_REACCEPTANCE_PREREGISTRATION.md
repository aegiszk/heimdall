# Value-Area Re-acceptance — Pre-registration

Frozen on 2026-09-22 before any outcome for this hypothesis was computed.
Stage 1 below reads price levels only. It never computes a trade or a return.
Stage 2 is frozen now but runs only after Stage 1 passes and the owner approves
spending another read of the MNQ holdout.

## Hypothesis and source

Auction-market theory (Dalton, "Mind Over Markets"; the "80% rule"): when the
regular session opens outside the prior session's value area, returns inside
it, and is accepted there, the auction tends to traverse value to the opposite
edge. The causal claim is acceptance of prior value, not delta or pattern shape.

Independence from dead families: absorption v1 used the prior-session 68% value
area as its level but triggered on delta absorption. This test shares the level
concept and nothing else: no delta, no bar pattern, no FVG, no VWAP. Plain ORB,
VWAP reversion and trend pullback do not reference prior value.

## Stage 1 — proxy fidelity (no outcomes)

Question: do value-area edges computed from one-minute close/volume reproduce
true volume-at-price value-area edges? The LuxAlgo POC proxy failed this kind
of check (2.7% exact match), so Stage 2 may not rely on a proxy without it.

- Source: `data/sierra/tick/NQ_continuous_1m_footprint.parquet` only.
- Session: the file's `session` column, RTH cells 09:30-15:59 ET.
- True profile: sum `volume` by `price` (one-tick resolution).
- Proxy profile: per minute, total volume and `bar_close`; assign each minute's
  whole volume to its close, summed by price. Same trades, so any difference is
  the close-volume approximation alone.
- Value area (both profiles, identical algorithm): POC is the highest-volume
  price, ties choose the lower price. From the POC, repeatedly add the adjacent
  unincluded price above or below with greater volume, ties add the lower price.
  Stop when included volume is at least 70% of session volume. VAL and VAH are
  the lowest and highest included prices.
- PASS if both |VAH_proxy - VAH_true| <= 4 ticks and |VAL_proxy - VAL_true| <=
  4 ticks in at least 80% of sessions. Otherwise FAIL.
- Report: sessions, pass rate, median and 95th-percentile absolute error for
  each edge.
- FAIL ends the experiment. It is NOT rerun on the 146 footprint sessions alone:
  a once-per-session setup there yields too few untouched trades to judge.

## Stage 2 — outcome test (frozen, not yet run)

- Instrument: MNQ, one contract; `data/MNQ_1m.parquet`; America/New_York RTH
  09:30-15:59.
- Prior value: previous RTH session's 70% value area from the Stage 1 proxy
  algorithm, prices at one tick.
- Setup: the 09:30 bar open is above prior VAH (short case) or below prior VAL
  (long case). An open inside value means no trade that session.
- Re-entry: the first one-minute close inside [VAL, VAH].
- Acceptance: the two consecutive 30-minute periods on the 09:30 grid that
  begin after the re-entry minute both have their last one-minute close inside
  [VAL, VAH].
- Entry: close of the second accepted period plus one adverse tick. No entry
  after 14:30 ET. One trade per session.
- Stop: short, one tick above the session high from 09:30 through the entry bar;
  long, one tick below the session low over the same span.
- Target: the opposite value-area edge, exact fill. Skip if the target is not
  beyond the slipped entry in the trade direction.
- Risk cap: skip if stop distance times $2.00 exceeds $300, which keeps a single
  loss inside the existing $325 daily buffer. This constant comes from the risk
  engine, not from results.
- Stop fill: one additional adverse tick. Stop wins when stop and target share a
  bar. Flatten 15:55 ET at close minus one adverse tick. $1.00 round-turn
  commission.
- Split and gates: the first 60% of sessions train, the final 40% are holdout,
  with four consecutive holdout buckets. Same metrics, Heimdall gate and 10,000-run
  Lucid Monte Carlo as the 2026-09-22 candidates. This would be the fourth read of
  this holdout, and the report must say so.
- No threshold, window, or rule changes after any Stage 1 or Stage 2 output.
