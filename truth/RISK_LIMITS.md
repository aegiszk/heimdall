# RISK_LIMITS.md — Risk Parameters (truth file)

All values are defaults for review — set final numbers in the admin-approved config row before S5.
The risk monitor and checker read these; makers cannot write them.

## Kill switch
- `KILL_SWITCH_DRAWDOWN = 5%` of allocated capital (intraday) → flatten_all
- Monitor cadence: 1 minute, isolated worktree, own creds, read-only except flatten

## Position / leverage
- `GROSS_LEVERAGE_CAP = 3x` (portfolio, review per rung)
- `PER_STRATEGY_SLICE`: set per family in config; sum <= total allocated
- `MAX_POSITION_PCT = 2%` of capital per single position (v1)

## Delta / margin (see FINANCIAL_INVARIANTS)
- `EPSILON_DELTA`: max abs net USD delta before flatten (set at S5 from fill granularity)
- `MMR_CEILING`: perp-leg maintenance-margin ratio ceiling (well above exchange liq level)
- `FUNDING_FLIP_THRESHOLD`: funding level against position that invalidates carry

## Concurrency (operator cognitive ceiling)
- Max concurrent active strategies (v1): start at 3, hard cap 7 (operator situational-awareness limit)
- Above 7 the operator drops information; loops degrade to neglect

## Curiosity budget (operator discipline, not automated)
- 2–4 hrs/week reviewing meta-layer reasoning regardless of alarms. Logged. Non-optional.
