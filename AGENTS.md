# AGENTS.md — Heimdall (canonical rules for ALL agents: Claude Code, Codex, Manus, any)
# Identical canon to CLAUDE.md. Read HEIMDALL_MEMORY.md first, then this.

## 0. READ MEMORY FIRST
Also read **TOOLING.md** — the HELMOR standard tool stack (rtk, caveman, nub, sqz, agentmemory,
codebase-memory-mcp, Understand-Anything, LCC/RCC/CX roster). Use those tools by default.

Before doing ANYTHING, read `HEIMDALL_MEMORY.md`. It is the single source of truth for all settled
decisions, dead ends, confirmed numbers, and current state. If this file and memory disagree, MEMORY WINS
for settled facts. Never re-derive something already marked settled. Never contradict a logged verdict.

## 1. WHAT HEIMDALL IS (current phase)
An autonomous **prop-account survival machine**. Goal: pass prop-firm challenges (primary target:
LucidTrading 50K FLEX) and KEEP the payouts without blowing the account. This is NOT an alpha-hunting
hedge fund anymore — three alpha edges (funding carry, cross-venue spread, liquidation cascade) were
tested and ALL DIED (funding arbed out, crowded thin, fast unreachable at our latency). The pivot:
we don't need alpha, we need risk discipline. Proven: a mediocre 52%/1:1 strategy passes ~27% under our
risk engine = positive EV (breakeven is 3.96%).

## 2. HARD RULES (non-negotiable)
- Money path is DETERMINISTIC. `/core` may NEVER import `/meta`. Enforced by `tools/check_core_purity.py`
  — run it after any change; a violation fails the build.
- Maker != Checker. A strategy cannot grade itself or widen its own risk limits.
- The risk engine (`core/risk/prop_engine.py`) is the product. Strategy is secondary. Never weaken a
  risk limit to make a backtest look good.
- No real money / no live orders until validated. `LIVE_TRADING_ENABLED=false` default.
- LIVE DATA DISCIPLINE: training data is stale. For anything money/market/tool-related, DO NOT trust
  remembered repos/APIs/numbers. Require live proof (a real fetch/quote with source) before adopting.
- WRITE-TO-MEMORY RULE: only record a spec as fact WITH its exact source. If two sources conflict, mark
  UNRESOLVED — never silently pick one. (This rule exists because a hallucinated DLL number was once
  written as "confirmed" and poisoned the plan.)

## 3. CONFIRMED TARGET NUMBERS — LucidTrading 50K FLEX (from screenshots, 2026-07)
- Starting capital $50,000 | Profit target $3,000 | Max Loss Limit $2,000 EOD-TRAILING | Daily Loss Limit: NONE
- Consistency: none in funded | Max size 4 mini / 40 micro | Min 5 days of >= $150 profit | Payout after 5 days
- Automation: EXPLICITLY ALLOWED (eval + funded). API via Rithmic/CQG. Python permitted.
- Commissions (confirmed): MES/MNQ $1.00 round-turn; ES/NQ $3.50 round-turn.

## 4. RISK ENGINE (the edge)
`core/risk/prop_engine.py` — trailing-MLL survival. Key params (defaults):
- daily_buffer = **325** (CORRECTED from 400 after realistic sim: 325 > 400 > 500 pass-rate at every win-rate)
- kill_cushion = 400 (flatten this far ABOVE the real MLL floor — we die above their line, never at it)
- protect_green_at = 500 (once up this much intraday, tighten stop; NEVER round-trip a green day)
- session_flatten = 16:45 EST | min_profit_day = 150
Four-layer defense priority: MLL-cushion FLATTEN_NOW > daily_buffer STOP_DAY > green-protect > session flatten.
Proven: obeying `check()` the account cannot touch the real $2,000 MLL.

## 5. STRATEGY REQUIREMENT (the only thing left to prove)
We do NOT need alpha. We need a strategy that is a true >= 50% win, ~1:1 payoff, with CONTROLLED TAILS
(no negative skew) and realistic slippage survivability. The real failure mode is "never reached target"
(risk-stalled), NOT dying on drawdown. So the strategy must reach +$3k steadily over 5+ days without
large losing days. Pacing > aggression.

## 6. EXECUTION
Rithmic + `async_rithmic` (headless Linux, WebSocket). BLOCKED pending Lucid confirming R|Protocol API
access on LucidFlex. Fallback: Tradovate raw REST (unproven for Lucid). Do NOT build the adapter until
Lucid answers. FFF (Funded Futures Family) is a SECONDARY target — it BANS API bots, so it needs a
human-emulation (GUI-clicking) executor, higher void risk. Same risk engine, different hands.

## 7. HOW TO WORK
- Read the assigned WORK ORDER. Only touch files it names.
- Every work order includes a Step-0 DATA-SANITY block. Do it, paste output.
- Run `tools/check_core_purity.py` + `pytest -q` before declaring done (ignore only the known OKX-timeout tests).
- Paste real numbers. No tuning to force a pass. Report fail-reasons honestly.
- If a result overturns a prior belief, SAY SO — that's the system working.
