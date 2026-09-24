# HEIMDALL — Inputs Needed From the Owner

Complete this checklist without pasting passwords, API secrets, private keys,
seed phrases, recovery codes, or authentication cookies. Secrets will be
configured locally when their adapter is ready.

## Current critical inputs (2026-09-22)

Research is not blocked. The $26 Sierra acquisition is complete and no further
data purchase is currently requested. These are the only owner inputs that now
unlock materially new work:

1. **Next strategy source:** a new video/rule sheet that is not one of the dead
   families in `HEIMDALL_MEMORY.md`, or confirmation that HEIMDALL should select
   the next candidate from new public research. Local absorption v1/v2 are dead.
2. **Lucid API evidence:** written confirmation from Lucid for the exact 50K FLEX
   account that either Rithmic R|Protocol API access or CQG API access is enabled,
   including the chosen connection. Do not send login credentials.
3. **Production host:** whether eventual paper/shadow execution runs on this
   Windows machine, a VPS, or both; required uptime and maintenance window.
4. **Notification destination:** Telegram, email, Slack, or desktop, plus which
   events should alert (feed failure, signal, proposed order, fill, reject,
   risk stop, kill switch).
5. **Crypto track, only if it is next:** public tracked-wallet addresses; chain
   and approved DEX/router; watch-only/testnet/mainnet mode; maximum test capital;
   and an RPC provider quote. No private key or seed phrase.

Already complete: Sierra Package 3 activation, NQ/MNQ/ES/MES and secondary
futures bar archive, 67,772,289 NQ one-tick records, exact SCID format proof,
price-level footprints, deterministic risk engine, offline validation suite,
and read-only wallet recorder/replay foundation.

## Required first response

```text
PRIMARY TRACK: Futures / Robinhood brokerage crypto / Robinhood Chain / other exchange
OPERATING MODE: Research / Human approval / Session approval / Bounded autonomous

COUNTRY AND ACCOUNT ELIGIBILITY:
INITIAL CAPITAL:
MAX LOSS PER TRADE:
MAX DAILY LOSS:
MAX WEEKLY LOSS:
MAX TOTAL DRAWDOWN:
MAX POSITION SIZE:
MAX SIMULTANEOUS POSITIONS:
MAX ORDERS PER DAY:
MAX LEVERAGE:
MAX SLIPPAGE:
MAX FEES OR GAS PER TRADE:
MINIMUM UNTOUCHED CASH RESERVE:
OVERNIGHT/WEEKEND HOLDING ALLOWED:
AVERAGING DOWN ALLOWED:
KILL-SWITCH ACTION:

FIRST STRATEGY:
VIDEO OR RULE-SHEET FILE:
INSTRUMENT/TOKEN UNIVERSE:
TIMEFRAME:
ENTRY RULE:
STOP RULE:
EXIT RULE:
POSITION-SIZING RULE:
SESSION/TIMEZONE:
DO-NOT-TRADE FILTERS:
PRE-REGISTERED FAILURE THRESHOLDS:

HOSTING: Local Windows / VPS / both
NOTIFICATIONS: Telegram / Slack / email / desktop
MONTHLY DATA BUDGET:
MONTHLY INFRASTRUCTURE BUDGET:
MAXIMUM ONE-TIME DATA PURCHASE:
```

## Strategy material

- [ ] Exact first strategy selected.
- [ ] Original video URL.
- [ ] Transcript or local rule sheet.
- [ ] Screenshots/annotations for discretionary rules.
- [ ] Instrument, timeframe, and timezone.
- [ ] Exact entry conditions.
- [ ] Exact stop/invalidation condition.
- [ ] Exact exit and trade-management rules.
- [ ] Position-sizing rule.
- [ ] Avoidance filters.
- [ ] Personal trade log, including losses, if available.
- [ ] Minimum required trade count.
- [ ] Required holdout expectancy.
- [ ] Walk-forward stability requirement.
- [ ] Maximum allowed drawdown.
- [ ] Maximum adverse slippage.

## Futures and prop-firm inputs

- [ ] Exact Lucid product/account name.
- [ ] Current rule screenshots or authoritative links.
- [ ] Written confirmation that automation is allowed on that exact account.
- [ ] Written confirmation of Rithmic R|Protocol or CQG API access.
- [ ] Written confirmation of overnight-hold rules.
- [ ] Choice of Rithmic or CQG.
- [ ] Confirmation that Sierra Chart Package 3 is active.
- [ ] One month of NQ Sierra CSV.
- [ ] Exact CSV header and sample rows.
- [ ] Confirmation whether export contains candle bid/ask totals or
      price-level footprint/volume-at-price data.
- [ ] Intended production host and available trading hours.

Required Sierra columns:

```text
Date, Time, Open, High, Low, Close, Volume, BidVolume, AskVolume
```

## Robinhood brokerage inputs

- [ ] Country/residency and Robinhood eligibility confirmed.
- [ ] Robinhood Crypto enabled.
- [ ] Dedicated Agentic account available, if using MCP.
- [ ] Integration choice: Trading MCP or Crypto Trading API v2.
- [ ] Allowed trading pairs.
- [ ] Allowed order types.
- [ ] Fee tier and routing preference.
- [ ] Dedicated bounded-capital account approved.
- [ ] Per-order human confirmation preference.

Do not send Robinhood credentials. MCP authentication happens directly through
Robinhood; API keys will be created with minimum permissions and stored locally.

## Robinhood Chain inputs

- [ ] Dedicated bot-wallet public address.
- [ ] Wallet mode: watch-only, human-signed, software-signed, or hardware wallet.
- [ ] Testnet or mainnet.
- [ ] RPC provider: Alchemy, QuickNode, Chainstack, or another provider.
- [ ] RPC and WebSocket credentials configured locally.
- [ ] Archive-data access decision.
- [ ] Maximum ETH gas balance.
- [ ] Allowed base assets/stablecoins.
- [ ] Approved DEX, router, aggregator, and launchpad.
- [ ] Verified router/factory contract addresses and ABIs.
- [ ] Exact or bounded token-approval policy.
- [ ] Transaction-simulation requirement.
- [ ] Human signing/confirmation requirement.
- [ ] MEV/private-transaction requirement.
- [ ] Maximum capital per token.
- [ ] Minimum pool liquidity.
- [ ] Maximum order percentage of pool liquidity.
- [ ] Maximum price impact.
- [ ] Maximum top-holder concentration.
- [ ] Maximum deployer/developer concentration.
- [ ] Minimum token age.
- [ ] New-launch trading allowed or forbidden.
- [ ] Contracts with mint/pause/blacklist/tax/upgrade powers allowed or forbidden.

Never provide a private key or seed phrase. The bot wallet must be isolated from
the owner's principal wallets and initially carry only test funds.

## FomoPulse/RHTrenches research inputs

- [ ] Tracked traders or wallet addresses.
- [ ] Lookback period.
- [ ] Minimum trade size.
- [ ] Minimum wallet sample size.
- [ ] Whether signals require multiple-wallet confirmation.
- [ ] Required liquidity-growth confirmation.
- [ ] Required price/volume confirmation.
- [ ] Maximum signal delay.
- [ ] Sell-following rules.
- [ ] Partial-exit mirroring rules.
- [ ] Wash-trader and suspected-insider exclusions.
- [ ] Existing historical tape/archive, if any.

## Infrastructure and operations

- [ ] Host: local Windows, VPS/cloud, or both.
- [ ] Expected uptime and maintenance window.
- [ ] Internet reliability/failover requirements.
- [ ] Docker permitted or forbidden.
- [ ] Database choice.
- [ ] Notification channel.
- [ ] Notification events.
- [ ] Log-retention period.
- [ ] Dashboard required or not required.
- [ ] Remote emergency shutdown required or not required.
- [ ] Backup destination and recovery expectations.
- [ ] Development, paper, and live environments approved.

## Budget and authority

- [ ] Monthly data budget.
- [ ] Monthly RPC/infrastructure budget.
- [ ] Maximum one-time data purchase.
- [ ] Sierra $26 subscription approved and active or pending.
- [ ] Permission to request cost quotes without purchasing.
- [ ] Permission to install free dependencies.
- [ ] Paper/testnet account creation authority.
- [ ] Explicit live-order authority status.

Recommended initial authority statement:

```text
Cost quotes and free dependency installation are allowed. No paid purchase and
no live order may occur without my explicit approval. Begin in research/paper
mode and require my confirmation before every real order.
```

## Minimum package needed to begin

The smallest useful first delivery is:

1. Primary track.
2. Operating mode.
3. Exact risk limits.
4. First strategy and rule sheet.
5. Monthly budget.
6. For futures: one-month Sierra NQ CSV and Lucid API confirmation status.
7. For Robinhood Chain: dedicated public wallet address, testnet/mainnet choice,
   RPC provider, and intended execution venue.
