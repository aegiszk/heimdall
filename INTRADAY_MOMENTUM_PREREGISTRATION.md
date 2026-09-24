# Market Intraday Momentum (rest-of-day → last half hour) — Pre-registration

Frozen 2026-09-22, before any outcome of this signal was computed on any Heimdall
dataset. This hypothesis has never been tested in Heimdall. It is not a variant
of a dead strategy: it has no entry pattern, stop, target, level or indicator.
It is a fixed-clock, one-trade-per-day timing rule.

## Source (verified from the primary paper)

Baltussen, Da, Lammers & Martens, "Hedging demand and market intraday
momentum", Journal of Financial Economics 142 (2021) 377-403,
https://www3.nd.edu/~zda/intramom.pdf . Statements used, verified from the text:

- r_ROD is the return from the previous market close to 30 minutes before the
  close. It "positively and significantly" predicts r_LH, the last-30-minute
  return.
- Timing strategy η(r_ROD): long the last half hour if r_ROD > 0, otherwise
  short.
- For equity index futures, "trading hours ... are based on the trading hours
  of their underlying markets".
- Table 6, equity index futures, 1974-2020: 6.86% annualised, SR 1.73, success
  rate 0.55.
- "We do not consider transaction costs."

Related: Gao, Han, Li & Zhou, JFE 2018 ("Market intraday momentum"), SPY
1993-2013.

## Mechanism: who pays us, and why it might persist

Option dealers who are short gamma, and leveraged-ETF rebalancing, must trade in
the direction of the day's move, largely near the close. They pay price impact
to whoever is already positioned in that direction.

It might persist because these flows are mechanical, not discretionary. This is
INFERRED, not verified: growth in leveraged ETFs and short-dated options since
2020 may have enlarged them.

It might be dead because it was published in 2018 and 2021, faster traders can
pre-position, and all three studies' samples end by 2020. Our data
(2024-07 → 2026-09) is entirely after publication, so this is a true
post-publication test.

## Exact rules (no free parameters)

- Clock: America/New_York. One-minute bars are stamped at bar start, so
  "price at HH:MM" is the close of the bar stamped HH:MM − 1 minute.
- Session: weekday RTH bars from 09:30 to 15:59.
- Previous close C0: close of the last RTH bar of the previous RTH session
  (15:59 normally; the last bar on an early-close day).
- P1530: close of the 15:29 bar. P1600: close of the 15:59 bar.
- Signal: r_ROD = P1530 / C0 − 1. Long if > 0, short if < 0, no trade if 0.
- No trade in a session missing the 15:29 or 15:59 bar (early closes), or with
  no previous RTH session.
- Entry: P1530 plus one adverse tick. Exit: P1600 minus one adverse tick. No
  stop, no target, one trade per day, flat every night.
- Costs: tick 0.25 point. Round-turn commission $1.00 for MNQ/MES and $3.50 for
  ES. One contract.

## Data

- **Screen and holdout:** `data/MNQ_1m.parquet`, `data/MES_1m.parquet` and
  `data/ES_1m.parquet` (Databento, 2024-07-01 → 2026-06-30). Sessions are split
  60/40 chronologically; the last 40% is the holdout, reported in four
  consecutive buckets.
- **Fresh window:**
  `data/sierra/{MNQ,MES,ES,NQ,M2K,MYM}_continuous_1m_latest_90d.parquet`,
  sessions 2026-07-01 → 2026-09-18 (the last complete session; 2026-09-21 is
  partial). The Sierra files alone supply C0 for 2026-07-01, because they start
  2026-06-23.
- **Primary instrument, chosen before outcomes:** MNQ. It has the lowest
  round-trip friction in basis points of notional: about 0.4 bp, against about
  0.9 bp for MES and 0.8 bp for ES.

## Checker and pass/fail rule (frozen)

- Returns per trade = net PnL / $50,000 (about MNQ notional, unlevered).
  Heimdall `run_gate(DEFAULT_GATE_CFG)` runs on the primary holdout with
  nb_trials = 1 and n_params = 0, because the rule comes unchanged from the
  paper.
- **PASS** only if all of these hold:
  1. MNQ holdout `run_gate` passes.
  2. MNQ holdout mean net PnL > 0, with at least 3 of 4 holdout buckets at a
     net total ≥ 0.
  3. MNQ fresh-window mean net PnL > 0.
- Anything else is **FAIL**. The signal family is then DEAD for Heimdall on
  these markets. No thresholds, no volatility or gamma filters, no alternative
  cut times.
- **Reported but not gating:**
  - MES, ES and the other fresh-window instruments;
  - two-tick-per-side cost stress;
  - the always-long last-half-hour benchmark;
  - the r_ONFH (Gao) signal as a paper-comparison diagnostic only. It can
    never be selected.
- **On PASS:** research candidate for paper trading only, then shadow trading,
  and no live order without owner approval. A PASS on about 2 years is still
  not deployment proof.
