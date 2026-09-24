# Autonomous Crypto Trading Loop — Master Spec

**Codename:** TBD (rename before S0) · **Owner:** X / HELMOR · **Status:** pre-S0 · **v0.1**

> Money path is deterministic. LLMs never sit on the money path — only the meta-layer.
> Verification rigor is the scarce resource. The gate decides what trades, not human taste.
> No real capital until the paper gate passes. No size until the live gate passes.

---

## 0. Thesis

A funding-carry **core** (boring, market-neutral, pays the rent) plus an **alpha factory** that
generates, tests, and kills hypotheses faster than edges decay. The loop *is* the fund; alpha is its
output, not its input. Every edge — quant or LLM — implements one `AlphaModel` interface, is screened
wide-and-cheap in-sample, and only survivors face a strict out-of-sample validation battery. What
survives earns capital in a stepped ramp: paper → $1–5k real → $50k → $150k → $500k.

## 1. Non-negotiables (hard rules)

1. `LIVE_TRADING_ENABLED=false` until the paper gate passes. Flag, not vibes. (cf. P2PLY peer-marketplace flag.)
2. Deterministic money path. LLM output can inform regime/recalibration; it can NEVER place, size, or approve an order.
3. Maker ≠ checker. A strategy cannot grade itself or widen its own risk limits. Checker reads only admin-approved config rows. (cf. P2PLY control-verifier.)
4. Risk monitor runs in an isolated worktree with its own creds, read-only except `flatten_all`. It cannot be overridden by any maker or checker.
5. Screen data and gate data are firewalled. A factor that touched the holdout is disqualified.
6. Every stopping condition is a deterministic inequality over an observable. Never "the agent says it's done."

## 2. Architecture — five processes, one state layer, one kill switch

Each process runs in its own git worktree (no shared context between maker and monitor).

| Process | Cadence | Role | LLM? |
|---|---|---|---|
| Ingest | 1m–1h | OKX + Hyperliquid + Binance → funding, basis, OI, OHLCV → duckdb/parquet | No |
| Makers (N) | on data | Each family emits `Signal(conviction∈[-1,1])`, point-in-time | Optional (LLM = candidate only) |
| Checker | on candidate | Runs validation battery, applies gate; reads admin config only | No |
| Execution | on verified | Cross-venue delta-neutral order construction; paper sim first | No |
| Risk monitor | 1m | Delta, cross-venue margin, drawdown → kill switch | No |
| Meta-layer | hourly/weekly | Regime detection, verifier recalibration, incident triage | Yes (off money path) |

State layer: `STATE.md` (loop memory, lessons) + Postgres (trades, fills, attribution). Kill switch: separate process, whitelisted actions only.

## 3. The AlphaModel contract (from ai-hedge-fund v2, hardened)

```
AlphaModel (ABC)
 ├─ QuantModel   # pure math: carry, OI-extreme, vol-regime, Alpha101 factors
 └─ LLMAgent     # LLM forms a view; candidate only, same gate

predict(asset, timestamp) -> Signal(conviction ∈ [-1,+1], reasoning, metadata)
  MUST be point-in-time: only data with ts <= timestamp. 0.0 = abstain.
```

Views (AlphaModel) are strictly separated from positions (portfolio construction + sizing). Quant and LLM models are interchangeable behind the interface.

## 4. Alpha families (v1)

- **Funding carry (core):** short Hyperliquid perp + long OKX spot, collect funding while delta-neutral. Base sleeve. Unwind on funding-flip (see invariants).
- **Funding/OI-extreme mean-reversion:** fade tail-percentile funding + open-interest crowding (liquidation-cascade unwind).
- **Vol-regime momentum:** trend-follow BTC/ETH perps only when regime filter says trend-on; flat otherwise. Positive-skew diversifier against carry's negative skew.
- **Alpha101 (screened pool):** all 101 WorldQuant factors run in the funnel's screen stage; shortlist only reaches the gate.
- **TradingAgents LLM debate (candidate):** bull/bear/manager as one `LLMAgent`. Runs paper, must clear the same gate. Expected to fail on crypto cost/latency/noise — gate decides, not us.

## 5. The two-stage funnel (why "all 101 straight to gate" is banned)

```
Stage A — SCREEN (cheap, in-sample only)
  all 101 + variants + designed families run on TRAIN slice they never leave
  ranked by trials-aware score
        │
     ── FIREWALL ── holdout never seen by Stage A
        │
Stage B — GATE (strict, out-of-sample + walk-forward)
  only shortlist (~8-12 survivors) faces the full validation battery
  small nb_trials at the gate → honest, passable bar
```

Rationale: best-of-N Sharpe under pure noise grows ~√(2·ln N). Sending ~2000 trials straight to the gate makes luck look like edge and forces PBO to reject real edges too. Wide cheap search, narrow strict confirmation. See `VALIDATION_BATTERY.md`.

## 6. Portfolio construction + sizing

Convictions aggregate (weighted by model-weight × confidence, thresholded) → target weights → **Riskfolio-Lib CVaR / risk-parity** sizing across families → position targets, capped per `RISK_LIMITS.md`. Funding-accrual and maintenance-margin math mirror QuantConnect/Lean's Binance-futures model (reimplemented in Python).

## 7. Venues & stack

- **Execution:** OKX (spot hedge leg, unified margin), Hyperliquid (perp, richer funding) — cross-venue, ccxt + hyperliquid-python-sdk.
- **Reference feed:** Binance (deepest tape, lead-lag research). OpenBB (Deribit IV, research only — AGPL, isolated from money path).
- **Compute/engine:** Python, vectorbt (backtest + Deflated Sharpe), Riskfolio-Lib (sizing), duckdb/parquet (data), Neon Postgres (state/attribution), Railway (runners), nub (script runner).
- **Agents:** Claude Code LCC/RCC + Codex CX1–4, disjoint-file worktree build (cf. P2PLY 6-agent). Truth files auto-load via CLAUDE.md / AGENTS.md.
- **License posture:** money path permissive-only where feasible; OpenBB research-only; internal-use only, money path not resold.

## 8. Repo layout

```
/core           deterministic money path (no LLM imports allowed here — CI-enforced)
  /data         connectors, ingest, duckdb schema
  /alpha        AlphaModel base + families + alpha101 pool
  /funnel       screen stage, firewall, shortlist
  /validation   the battery (walk-forward, CPCV, PBO, DSR, MC-perm, bootstrap, NW)
  /portfolio    aggregation + Riskfolio sizing
  /execution    cross-venue order construction, paper broker, fills+slippage model
  /risk         isolated monitor + kill switch
/meta           LLM layer (regime, recalibration auditor, incident triage)
/truth          FINANCIAL_INVARIANTS.md RISK_LIMITS.md SCHEMA_TRUTH.sql
                VALIDATION_BATTERY.md LIVE_GATE.md
STATE.md        loop memory + lessons
```

CI rule: `/core` may not import from `/meta`. Breaks the build if violated. This is the deterministic-money-path guarantee, enforced.

## 9. Sprint plan

| Sprint | Deliverable |
|---|---|
| S0 | Repo, worktrees, truth files, config, secrets vault, read-only connectors, paper broker, Postgres schema |
| S1 | Data pipeline (funding/basis/OI/OHLCV); funding-carry as first `AlphaModel`; vectorbt backtest |
| S2 | **Validation battery** (built early — it's the edge): walk-forward, CPCV, PBO, DSR, MC-permutation, bootstrap Sharpe CI, NW t, param-count cap |
| S3 | AlphaModel interface + funnel (screen → firewall → gate); 3 designed families + Alpha101 pool |
| S4 | Portfolio construction + Riskfolio CVaR/risk-parity sizing |
| S5 | Cross-venue paper execution: delta-neutral construction, realistic slippage/funding fills (Lean math), attribution |
| S6 | Isolated risk monitor + kill switch + incident log; whitelist-gated agent handoffs |
| S7 | LLM meta-layer: regime detection, weekly verifier recalibration, curiosity-budget review harness |
| S8 | 90d paper run → graduation eval → arm `LIVE_GATE` (tiny-real procedure) |

## 10. Economics reality

$500k target. Carry on majors realistically nets high-single to low-double-digit % APR after fees/slippage once crowded; funding spikes are episodic, not a faucet. Factory sleeves add diversification, not guarantees. Token cost $40–90/day is cleared with margin only at target size — sub-$100k the loop is uneconomic against token cost, which is exactly why real capital is gated behind proof, not hope.
