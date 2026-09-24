# FINANCIAL_INVARIANTS.md — Hard Invariants (truth file)

These hold at ALL times. A breach triggers the named action immediately, before any further trading.
Modeled on P2PLY's solvency invariant + wallet-monitor tripwire.

## I1 — Delta neutrality (carry + any hedged sleeve)
`abs(net_delta_usd) <= EPSILON_DELTA` across ALL venues combined.
Breach → risk monitor flattens the offending sleeve. Carry is never allowed to run naked directional.

## I2 — Cross-venue margin buffer
`maintenance_margin_ratio(perp_leg) <= MMR_CEILING` on every venue independently.
The spot leg cannot post margin to the perp venue instantly, so the buffer must absorb cross-venue lag.
Breach → auto-deleverage the perp leg BEFORE the exchange can liquidate.

## I3 — Funding-flip guard (carry thesis validity)
If funding crosses `FUNDING_FLIP_THRESHOLD` against the position, the carry thesis is invalidated.
Action → unwind the sleeve. Never hold-and-hope a carry position through a funding flip.

## I4 — Portfolio gross leverage cap
`sum(abs(notional_i)) / equity <= GROSS_LEVERAGE_CAP`.
Breach → block new orders; reduce to cap.

## I5 — Per-strategy capital cap
Each active family is bounded by its admin-approved slice. A family cannot exceed its slice even if the
aggregator requests more. Enforced at execution, read from config, never from caller input.

## I6 — Attribution completeness (solvency-analog)
Every fill persists with originating `signal_id` → `verifier_verdict_id`. No orphan fills.
Reconciliation: `sum(position_ledger) == exchange_reported_positions` within tolerance each cycle.
Breach → halt + incident report (this is the loop's solvency invariant).

## I7 — Live flag
No order reaches a real venue while `LIVE_TRADING_ENABLED=false`. The flag is flipped only by the
`LIVE_GATE` procedure, never by a strategy or an LLM.

Thresholds (EPSILON_DELTA, MMR_CEILING, FUNDING_FLIP_THRESHOLD, GROSS_LEVERAGE_CAP) are defined in
`RISK_LIMITS.md` and the admin config row. Changing them is an admin action, logged.
