# AGENT2 SURVIVOR REPLICATIONS

Status 2026-09-24: **EMPTY — no Agent-1 SURVIVING_RESEARCH_CANDIDATE exists.** Agent 1's `workspace/external_strategies/` holds only source transcripts. No preregistration, no signal code, no trades.

Protocol for every future candidate (Part L), fixed now, before any result is seen:

1. Agent 2 reads only the candidate's **hashed preregistration**. Agent 2 does not import or read Agent 1's signal code before its own implementation is frozen (hash recorded here first).
2. Agent 2 writes `<family>_<variant>/agent2_impl.py` from the preregistration alone and hashes it.
3. Both implementations run on the identical data file (same SHA-256), on development data only (never pre-2024-07-01 CME equity-index rows before Dhesi completes).
4. Compare trade-by-trade: signal timestamp, direction, entry, stop, target, exit time, exit price, PnL. The requirement is 100% deterministic agreement or an itemised mismatch table with a root cause per row. The prereg text decides which side is wrong. If the text is ambiguous, the candidate is `DISPUTED` and the ambiguity is counted as an extra interpretation trial.
5. Part E sampling: 10 winners + 10 losers + 10 random (seeded, seed recorded before sampling), or all trades if n < 30, reconstructed from raw bars by hand-script.
6. Only after steps 1–5 pass may the Part F–J attacks run.
