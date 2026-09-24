# LIVE_GATE.md — Capital Arming & Ramp (truth file)

Two independent gates. Passing the first ONLY unlocks the $1–5k rung — nothing more.

## GATE 1 — Paper → tiny real ($1–5k)
Per strategy, independently:
- Passed the full validation battery (`VALIDATION_BATTERY.md`) on OOS + walk-forward
- ≥ 90 days paper, ≥ min trade count
- No invariant breaches during the paper window

On pass → flip `LIVE_TRADING_ENABLED=true` for that strategy ONLY, capital = $1–5k, SAME CODE.
Purpose of the tiny-real rung: measure what the paper sim lied about (slippage, funding timing,
cross-venue latency, partial fills, API failure). This is the only test that matters.

## GATE 2 — Tiny real → ramp
Live edge must track paper edge:
- `realized_edge >= 0.60 * paper_edge` over the rung window, AND
- realized maxDD <= paper maxDD * tolerance, AND
- zero invariant breaches

## Ramp rungs
```
$1–5k  →  $50k  →  $150k  →  $500k
```
Each step re-runs GATE 2 at the new size. Edge must survive size (slippage scales non-linearly).
Any rung where realized edge craters below tolerance → HALT, drop back one rung, investigate.

## Kill conditions (any rung)
- Drawdown crosses `RISK_LIMITS` kill-switch threshold → flatten_all, drop to paper, incident report.
- Invariant breach → per `FINANCIAL_INVARIANTS.md`.
- Live edge < 0.60 * paper for two consecutive windows → strategy retired to paper.

## Ownership
Flag flips and rung promotions are admin actions, logged with the config row that authorized them.
No strategy, aggregator, or LLM can promote itself.
