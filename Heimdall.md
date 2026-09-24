# HEIMDALL — Autonomous Trading System Blueprint

> `HEIMDALL_MEMORY.md` remains the source of truth for settled facts, tested
> results, dead strategies, and risk-engine decisions. This document defines
> the forward build plan.

## Mission

Build a verifiable trading system that can progress safely through four modes:

1. Research and alerts only.
2. Human approval for every proposed order.
3. Session-approved automation inside fixed deterministic limits.
4. Bounded autonomous execution after paper and small-capital validation.

The system may ultimately support three separate execution tracks:

- CME futures and prop-firm accounts, with LucidTrading 50K FLEX as the current
  primary target.
- Broker-based cryptocurrency trading through Robinhood's Crypto Trading API
  or Trading MCP when account eligibility is confirmed.
- Self-custodied trading on Robinhood Chain through verified EVM contracts and
  RPC infrastructure.

These tracks must not share credentials, wallets, broker state, or execution
adapters. Strategies may share the validation funnel and risk concepts only
where their market mechanics genuinely match.

## Non-negotiable architecture

- `/core` is deterministic and may never import `/meta`.
- Jev and other AI systems remain in `/meta` and cannot authorize trades,
  change risk limits, grade their own profitability, or bypass validation.
- Maker is not checker: strategy generation, statistical validation, risk
  enforcement, and execution are separate components.
- `LIVE_TRADING_ENABLED=false` remains the default.
- No paid data purchase without a quoted cost and explicit owner approval.
- No live order without explicit owner authorization until the operating mode
  is deliberately changed.
- Secrets stay in local environment variables or a secrets manager. Passwords,
  seed phrases, private keys, and recovery codes never enter source control,
  logs, prompts, or chat.
- Every external order uses an idempotency key or unique client order ID.
- Every adapter must support read-only health checks, bounded timeouts, rate
  limits, structured errors, and a deterministic kill switch.

## What Jev does

Jev is the research-routing layer, not the trader. The current integration in
`meta/jev_strategy_triage.py` can evaluate local rule sheets for:

- Mechanical codifiability.
- Compatibility with the target instrument and venue.
- Whether available data can test the defining claim.
- Which candidate deserves the next bounded falsification test.
- When evidence is insufficient and human review is required.

Jev output is advisory evidence. Profitability must still be established using
deterministic code, realistic costs, untouched holdout data, walk-forward
stability, and the existing validation battery.

## Track A — CME futures and prop firms

### Current state

- Primary account target: LucidTrading 50K FLEX.
- Risk engine: `core/risk/prop_engine.py`.
- Existing paid data: MNQ, MES, and ES one-minute parquets covering
  2024-07-01 through 2026-06-30.
- Sierra Chart order-flow POC: passed. The NQ export contains real, separate
  bid/ask volume and reconciles to total volume with 0.00% material mismatch.
- Sierra archive: validated 90-day, one-minute continuous data for NQ, MNQ, ES,
  MES, GC, MGC, CL, MCL, RTY, M2K, YM, and MYM, plus BTC perpetual comparison
  feeds. Exact ranges and hashes are in `data/sierra/MANIFEST.md`.
- Live portfolio candidate: Dhesi Inversion Model on MNQ. Its recorded holdout
  geometry is positive but too sparse to pass an evaluation alone.
- NQ/MNQ bar-level absorption v1: pre-registered and killed on frequency (zero
  trades). Its one-minute aggregation could not reproduce price-level footprint
  bubbles; do not loosen the frozen thresholds.
- NQ price-level footprint absorption v2: also pre-registered and killed on
  frequency (zero candidates across 126 eligible sessions). The 20% extreme
  concentration condition was the terminal choke; do not tune or retry it.
- Sierra one-tick archive: 67,772,289 NQ trades across NQM26/NQU26/NQZ26 are
  preserved raw and as Parquet. A continuous 146-session price-level footprint
  is ready for materially different hypotheses. Exact hashes and data caveats
  are in `data/sierra/MANIFEST.md`.

### Immediate milestone

The Sierra acquisition milestone is complete. Select and pre-register a
materially different futures hypothesis using the existing bar/tick archive.
Both absorption variants are dead; MBO/order-book queue claims remain out of
scope because this archive contains trades and classified aggressor volume, not
queue history.

### Execution milestone

No futures adapter is built until the owner supplies written confirmation for
the exact Lucid account covering automated trading and Rithmic R|Protocol or
CQG API access. The adapter must initially run read-only, then paper, then shadow,
then human-approved live orders.

## Track B — Robinhood brokerage crypto

Robinhood brokerage crypto is separate from Robinhood Chain. Possible
integration methods are:

- Robinhood Trading MCP using a dedicated Agentic account.
- Robinhood Crypto Trading API using signed requests and narrowly scoped keys.

Before implementation, confirm jurisdiction/account eligibility, supported
assets, fee tier, routing, order types, and whether a dedicated bounded-capital
account is available.

The first adapter must be read-only and expose:

- Account health and buying power.
- Holdings and open orders.
- Supported trading pairs.
- Best bid/ask and estimated execution price.
- Fee and slippage estimates.

Order submission remains disabled until a crypto strategy independently passes
the funnel. The dead funding-carry, cross-venue spread, and liquidation-cascade
strategies must not be revived.

## Track C — Robinhood Chain

Robinhood Chain is an EVM-compatible Arbitrum L2 using chain ID `4663` and ETH
for gas. This track uses a dedicated self-custodied bot wallet and production RPC
provider. It does not use Robinhood brokerage credentials.

### Data layer

- Production RPC and WebSocket endpoint from Alchemy, QuickNode, Chainstack, or
  another approved provider.
- Archive access for historical logs and backtesting.
- Verified pool, router, factory, token, and launchpad contracts.
- Independent reconstruction of swaps, transfers, liquidity, holders, and pool
  state from chain data.
- FomoPulse and RHTrenches may supply discovery signals but are not execution
  sources or sole sources of truth.
- The first read-only/offline slice now exists in `meta/wallet_copy/`: immutable
  EVM observations, canonical append-only JSONL recording, duplicate and
  timestamp guards, deterministic replay, latency, and adverse-drift metrics.
  It has no RPC, signing, key, or order capability.

### Security layer

- A new low-balance wallet used only by HEIMDALL.
- Testnet before mainnet.
- Exact or bounded token allowances; no default unlimited approvals.
- Transaction simulation before signing.
- Contract-code and proxy inspection.
- Token checks for minting, pausing, blacklisting, mutable fees, transfer taxes,
  honeypots, ownership, upgradeability, liquidity locks, and holder concentration.
- Maximum gas, slippage, price impact, and pool-share limits.
- Emergency revocation and wallet-drain response procedure.

### Candidate research paths

- Tracked-wallet behavior.
- New-pool discovery.
- Liquidity growth.
- Multi-wallet confirmation.
- Price/volume continuation.
- Holder-distribution improvement.

Copying a public wallet is not presumed profitable. Every signal must account
for observation delay, selection bias, gas, pool fees, slippage, price impact,
MEV/sandwich exposure, partial exits, failed transactions, and rug risk.

## Risk controls shared by all tracks

Each execution track must define and enforce:

- Maximum capital allocated.
- Maximum position and order size.
- Maximum loss per trade, day, week, and account.
- Maximum simultaneous exposure.
- Maximum orders per period.
- Maximum slippage, fees, gas, and price impact.
- Permitted instruments and venues.
- Permitted sessions and holding periods.
- Stale-data and disconnected-feed behavior.
- Reconciliation between internal and broker/onchain state.
- Kill-switch actions: stop entries, cancel orders, flatten positions, disable
  credentials, and require manual restart.

AI output can never relax these controls.

## Validation ladder

Every strategy follows the same evidence ladder:

1. Rule-sheet completeness and discretion-gap audit.
2. Data-sanity report with rows, range, gaps, NaNs, extremes, and source.
3. Deterministic implementation with fixed assumptions.
4. In-sample screen separated by a firewall from untouched holdout.
5. Statistical battery and walk-forward analysis.
6. Realistic fees, spread, slippage, latency, rejects, and partial fills.
7. Paper execution.
8. Shadow execution against live market data.
9. Human-approved small-capital deployment.
10. Bounded autonomy only if live behavior remains within registered tolerances.

Failure at any stage returns the candidate to research or kills it. Risk limits
and tests may not be weakened to rescue a strategy.

## Operating modes

### Research only

The system gathers data, tests candidates, and sends alerts. It has no execution
credentials.

### Human approval

The system prepares a complete proposed order including thesis, entry, size,
stop, target, expected fees/slippage, expiration, and risk impact. The owner
must approve before submission.

### Session-approved automation

The owner approves a strategy, instruments, session, capital envelope, and kill
conditions for a bounded period. Deterministic code executes only inside that
envelope.

### Bounded autonomous

The system may execute without routine confirmation but cannot change its
strategy, universe, risk limits, capital allocation, or validation status.
Deployment requires proven paper, shadow, and small-capital performance plus
successful kill-switch and recovery drills.

## Infrastructure

The production design requires:

- A stable host or VPS with automatic restart.
- Separate environments and credentials for development, paper, and live.
- Structured append-only decision and order logs.
- Database storage for market data, signals, orders, fills, positions, and
  reconciliation events.
- Health checks for data freshness, clock drift, API availability, balances,
  positions, and permissions.
- Notifications for signals, approvals, submissions, fills, rejects, stops,
  feed failures, and kill switches.
- Remote emergency shutdown with authenticated access.
- Backups and a documented recovery procedure.

## Recommended build order

1. Keep absorption v1 and footprint v2 dead; do not tune or rerun them.
2. Obtain the remaining owner inputs in `HEIMDALL_INPUTS_NEEDED.md`.
3. Add a read-only Robinhood Chain feed adapter only after the provider,
   endpoint cost, chain/router addresses, and tracked wallets are verified.
4. Run wallet observations through the existing recorder/replay paper ledger.
5. Validate one strategy per market before building its execution adapter.
6. Add human-approved execution.
7. Run paper, shadow, and small-capital stages.
8. Consider bounded autonomy only after the observable gates pass.

## Current hold condition

Research and read-only components may proceed autonomously. No new paid service,
execution adapter, signing key, approval, or live-order capability is authorized.
Same-block wallet copying is not a guaranteed property of public post-trade
feeds and must not be represented as one.
