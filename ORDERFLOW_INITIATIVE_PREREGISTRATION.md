# Order-flow initiative v3 — pre-registration

Status: frozen before outcome inspection. This is not a threshold revision of
dead absorption v1/v2. It tests the opposite microstructure claim: aggressive
trade flow that achieves price displacement may continue briefly.

Evidence basis:

- Local source: `Trading Philosophy and Order Flow Analysis_ Structured Rule
  Sheets.md`, Rule Sheet 2, which defines aggression/initiative as high effort
  with high price result.
- Kurov and Lasser, “Order flow, dealer profitability, and price formation,”
  Journal of Financial Economics 85 (2007), reports a strong short-run relation
  between S&P 500 futures price and order flow, with slightly negative long-run
  impact: https://doi.org/10.1016/j.jfineco.2006.05.010
- Jin et al., “Order book price impact in the Chinese soybean futures market,”
  finds order/trade imbalance predicts near-term futures price changes and that
  predictability diminishes at longer horizons:
  https://doi.org/10.1002/ijfe.2439

These papers motivate a falsifiable test; they do not establish profitability
in NQ after costs.

## Data and firewall

- Use `data/sierra/tick/NQ_continuous_1m_footprint.parquet` exactly as recorded
  in `data/sierra/MANIFEST.md`.
- Permitted fields: minute, trade price, volume, classified bid/ask volume, and
  trade-derived bar OHLC. SCID quote high/low fields remain forbidden.
- RTH is 09:30–16:00 America/New_York. Signals stop at 15:30; flatten at 15:55.
- At least 20 prior complete RTH sessions are required.
- Development report: sessions through 2026-06-15 (NQM-selected period).
- Untouched holdout: 2026-06-16 onward (NQU/NQZ-selected periods). Holdout is
  evaluated once. No threshold sweep, optimizer, or post-result amendment.

## Prior value area

Calculate previous-session POC and 68% value area from actual 0.25-point trade
price cells using the same deterministic lower-price tie break as v2. Current
session data cannot affect VAL/VAH.

## Long initiative breakout

A one-minute signal bar must satisfy every condition:

1. It trades through prior VAH and closes at least one tick above VAH.
2. It closes above its open and its body is at least 50% of its trade-price
   high-low range.
3. Its total classified delta is positive.
4. Ask volume in its two highest traded price levels is at least 20 contracts.
5. That ask volume is at least 3 times bid volume at those same levels, with the
   denominator floored at one contract.

The next observed one-minute bar is confirmation: it must close at or above
VAH, close no lower than the signal midpoint, and have non-negative delta.

## Short initiative breakout

Mirror the long rules at prior VAL: close at least one tick below VAL, bearish
body at least 50% of range, negative total delta, at least 20 bid contracts in
the two lowest levels, at least 3:1 versus ask volume there, followed by a bar
that holds at/below VAL, closes no higher than the signal midpoint, and has
non-positive delta.

If both directions somehow qualify in one minute, skip it. Take the earliest
fully confirmed event and at most one trade per session.

## Execution and risk

- Enter one MNQ contract at the bar after confirmation, one adverse 0.25 tick.
- Stop one tick beyond the opposite extreme of the signal bar.
- Skip non-positive risk, risk below four ticks, or total stopped loss above the
  fixed $325 daily buffer.
- Target exactly 1R. If stop and target are both touched in one bar, stop wins.
- Stop fills one adverse tick beyond the stop. Target fills at target. Session
  flatten fills at 15:55 close with one adverse tick.
- MNQ point value is $2. Subtract $1.00 round-turn commission once.

## Verdict gates

- Holdout must contain at least 30 trades.
- Holdout win rate must be at least 50% and net mean PnL must be positive.
- At least three of four chronological holdout buckets must have positive mean
  PnL.
- Lucid $325-buffer empirical Monte Carlo pass rate must exceed the settled
  3.96% economic breakeven rate.
- Passing means candidate for paper shadow only. Failure kills v3. Aggregate EV
  cannot override a failed gate.
