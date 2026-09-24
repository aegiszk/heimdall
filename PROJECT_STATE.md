# PROJECT_STATE.md — Heimdall one-page status (update each cycle)

## PHASE: Prop-account survival machine (pivoted from alpha-hunt). Target: LucidTrading 50K FLEX.

## SCOREBOARD
- Alpha edges tested: 3 | dead: 3 (funding carry, cross-venue spread, liquidation cascade). $0 lost.
- Risk engine: BUILT + validated. Mediocre 52%/1:1 strategy = 27% pass = +$584 EV/eval (breakeven 3.96%).
- Approach status: VALIDATED, positive-EV. First profitable direction in the project.

## DONE
- Full Heimdall skeleton (AlphaModel iface, validation battery [DSR/PBO/MC/bootstrap/NW], funnel, core-purity firewall).
- core/risk/prop_engine.py (trailing-MLL survival engine). 5 tests pass.
- prop_montecarlo.py (true pass-rate sim). Lucid rules + commissions confirmed.
- Default daily_buffer corrected 400 -> 325 (realistic sim).

## OPEN / NEXT
1. Ask Lucid: R|Protocol API access on LucidFlex? (BLOCKS execution adapter)
2. Prove a strategy that is >=50% win, ~1:1, tight tails, slippage-survivable (the only thing left).
3. Model unmodeled risks: negative skew, stop slippage, loss autocorrelation.
4. FFF human-emulation executor (secondary, parallel).

## DEAD / DO NOT REVISIT
- Funding carry, cross-venue spread, cascade (as edges). Funded Futures Family via API (ToS-banned).
- Any strategy that needs to hit +$3k FAST (5-day-min rule + risk-stall both punish it).
