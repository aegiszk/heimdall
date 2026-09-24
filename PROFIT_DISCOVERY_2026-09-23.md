# HEIMDALL — Profit Discovery Program, session 2026-09-22/23

**STATUS: CHECKPOINT — RESEARCH INCOMPLETE. WINNER: NONE.**
Labels: [V] verified this session · [I] inferred · [U] unverified · [A] from an existing artifact.
Scripts and datasets: `workspace/profit_discovery_2026-09-23/`.

## Gates

| Gate | State | What is missing |
|---|---|---|
| S0 project truth | DONE | — |
| S1 broad discovery | FLOOR MET (≈15 families, 34 hypotheses, >40 sources, >20 repos) | Primary-source verification on several rows (many SSRN/journal pages returned 403) |
| S2 FOMO / wallet copy | PARTIAL | Follower sim on 58 of 406 pools; cluster test data incomplete; no forward holdout |
| S3 data/execution reality | PARTIAL | Net-edge tables built only for wallet copy |
| S4 ledger | DONE (below) | — |
| S5 tools | DONE (tools lane) | — |
| S6 red team | DONE for current top 3 | — |
| S7 frozen experiment | DRAFT (below) | Operator approval, then pre-register → hash → implement → test once |

## 1. State reconciliation

- **Intraday momentum** (`INTRADAY_MOMENTUM_PREREGISTRATION.md`) ran 2026-09-22 and FAILED. This was not in memory before this session. [V: `data/strategy_research/intraday_momentum_validation_2026-09-22.json`]
  - MNQ train: 296 trades, −$15.84/trade.
  - MNQ holdout: 198 trades, −$11.65/trade, NW t −1.65, 0 of 4 buckets ≥ 0.
  - Fresh window: MNQ +$12.80/trade and NQ +$74/trade, but ES, MES, M2K and MYM were all negative.
  - Consequence: fading the signal is **contaminated** (the idea came from this data) and is already contradicted by the fresh MNQ window.
- **Corrections to `HEIMDALL_WALLET_COPY_AUDIT_REPORT.md`** (2026-09-22). Its headline, that realized PnL is negative and paper PnL illusory, agrees with this session. These parts are wrong:
  - §6 follower grid: labelled VERIFIED but is a **synthetic model** (assumed $20k pools and 7.5% impact).
  - 115 ms p50 end-to-end latency, 25/60 ms feed latency: **never measured**, and not found in the cited rhfeed README.
  - RHTrenches "pagination / 250k fills since July": false. The API caps at 400 closed trades and 500 tape rows, with no cursor. [V]
  - FomoPulse PnL "FIFO": false. `pnl.ts` uses **average cost**. [V]
  - FomoPulse history "since July": false. The first fill is 2026-09-05. [V]
- **Known hooks are launchpad hooks, not fomo.family's** (tools lane, from Uniswap/hooklist, Doppler deployments and Kyber):
  - `0x4e34…a544` = Doppler `DopplerHookInitializer`.
  - `0xe5e7…e044` = Pons `V2MemeHook`.
- A separate lane, `VALIDATION_AUDIT_2026-09-22.md`, found backtest-backend defects D1–D4 (see §12).

## 2. Sequencer / latency: measured from this Windows host (Dubai; egress reported as IN) [V]

| Path | Measurement |
|---|---|
| Feed `wss://feed.mainnet.chain.robinhood.com` | Requires `permessage-deflate` (without it: HTTP 400, "Compression is required"). One message per L2 block. Feed `sequenceNumber` = L2 block + 2. Inter-block p50 101 ms, p90 173 ms. |
| Public RPC head vs feed, same block | p10 231 / p50 455 / p90 637 / p99 737 ms (includes 50 ms poll interval) |
| Public RPC RTT (`eth_blockNumber`) | p50 231 / p90 237 / p99 275 ms |
| Sequencer endpoint `https://sequencer.mainnet.chain.robinhood.com` | RTT p50 272 ms. `eth_chainId` is not served; it accepts submissions only. |
| FomoPulse block→DB | median ~1.2 s (its own `/api/status`) |
| RHTrenches block→tape | median 1.1 s, p90 1.3 s, WebSocket, QuickNode (its own `/api/status`) |
| Decode cost | Pure-Python keccak + RLP: 4.3 ms/tx, too slow for live use. rhfeed claims 4–70 µs [U] |
| Gas per FOMO-route swap | Median $0.66, p90 $2.03, max $4.30 (25 receipts; 0.085 gwei; ETH $2,752). A plain router swap is probably cheaper [U] |
| Block rate | ~10 blocks/s (1M blocks = 27.97 h). FomoPulse's code comment says "thirty blocks a second", which is wrong. |

- **Pre-execution visibility: NONE by any public path** [V].
  - The feed carries already-sequenced blocks, and FCFS ordering puts a follower at block N+1 at best.
  - A FOMO buy starts as a Solana Relay deposit that **does not name the token**. The token first appears in the solver's fill on chain 4663 (`chainstacklabs/fomo-solana-rh-listeners/docs/02-trade-lifecycle.md`).
  - Same-block copying is therefore impossible.
- **Achievable follower block** [I]:
  - From Dubai: ≈ N+3, since one-way ≈ RTT/2 ≈ 115–135 ms each way plus submission.
  - From a VPS near the sequencer: ≈ N+1. The sequencer sits behind Cloudflare and its location is unknown [U].
- **Attribution** (tools lane, from the chainstack docs): FOMO wallets are EIP-7702 accounts trading through the ERC-4337 EntryPoint `0x4337084D…f108`.
  - Buys are Relay solver fills from executor `0xb92fe925…fff4f`.
  - So `tx.from` is a bundler or solver, never the trader. Attribute trades via `UserOperationEvent` topic[2] or the executor Transfer recipient.

## 3. Discovery sources

- **FomoPulse** [V]:
  - 294 wallets, frozen since ~2026-09-05, because fomo.family returns 403 to its leaderboard fetch.
  - Ingest is `eth_subscribe` on ERC-20 `Transfer` logs for tracked wallets, followed by receipt reconstruction. It is router-agnostic.
  - Retention is 90 days of fills.
  - Full tape archived: **212,859 fills, 2026-09-05 07:38 → 2026-09-22 19:42 UTC**.
    - 97,758 are dust (handouts); 1,641 are stock tokens.
    - That leaves 68,044 real fills: 44,032 buys, 24,012 sells.
    - Pricing: 61,463 cash-leg, 5,557 estimated, 1,024 unpriced.
  - DEX mix: v4 54,894, v3 7,441, v2 2,079.
- **RHTrenches** [V]:
  - 147 wallets, data since ~2026-08-27.
  - Endpoints `/status /traders /tape /closed /flow /radar /labels /overview /tokens`, all capped.
  - Labels seen: 220 "potential honeypot", 155 "not a real buy (spoofed)", 79 "not a real buy (planted)", 40 "pile-in 28", plus "pool N m old" and "parked liquidity".
- **fomo.family API** (`prod-api.fomo.family`): Privy JWT; Cloudflare refuses non-browser clients (430 or 403). Unusable as a data source.

## 4. Copyability evidence

**Source wallets lose on a realized basis** [V: `persistence.py`, average cost, dust, stock and unpriced fills excluded]:

| Window | Realized PnL | Sold cost | Return | Win rate |
|---|---|---|---|---|
| H1 (09-05→09-14) | −$6.26M | $46.1M | −13.6% | 44.3% |
| H2 (09-14→09-22) | −$1.75M | $18.4M | −9.5% | 46.7% |
| Whole window | −$11.60M | $75.8M | −15.3% | — |

**Open bags:**
- Cost $23.5M.
- At mark: $408M. At a cap of 50% of pool liquidity: $27.0M.
- 78.8% of all paper MTM sits in one token, 8Stock, whose pool holds **$1,053** of liquidity.
- 71 positions are marked above their pool's total liquidity.
- Realized plus liquidity-capped MTM: **−8.2% on $99.3M deployed**.

**Persistence:**
- 141 wallets had ≥5 realized sells in both halves. Spearman H1→H2 is +0.19 on PnL and +0.19 on return.
- Top-quintile H1 wallets (n=29) realized **−9.3%** in H2 (median wallet −3.0%; 45% positive).
- The rest realized −9.4%.
- Followers vs H2 return: Spearman 0.003.

**Crowding:** median tracked wallet has 9,654 followers; the maximum is 531,828.

**Positions:** 49% of wallet-token positions were never sold within the window. Median buy→last-sell is 6.1 h.

**Follower simulator** (`copy_sim.py`) [V data, I model]:
- Replays Uniswap v4 PoolManager `0x8366…0951` `Swap` logs.
- Swap math: constant liquidity, event LP fee, measured output-side hook tax. Tick crossings and input-side hook fees are not modelled.
- Delay d: the follower is placed at the end of block (b + d − 1). d = 0 is an impossible pre-sequencing ceiling.
- Validation: sim d=0 round trips vs the wallets' own tape round trips, corr **0.77**. Mismatches trace to pools quoted in volatile tokens (e.g. INU/AAPL), which is why exits now convert at the source's own exit USD rate.

**PRELIMINARY results: 181 source buys from 58 of 406 pools**, a chronologically early subset.
- **Entry drift** (price vs the source's post-trade price):
  - median **0.0000** at d = 1, 3, 5, 10, 20, 50, 150 blocks.
  - p90: 0.0002 at 3, 0.0234 at 50, 0.054 at 150, 0.162 at 600 blocks.
  - So latency is **not** the binding constraint at the median. That contradicts the audit report's "1–5 s stampede" claim as a typical case.
- **Mirror exit, S=$500, d=3:** n=136, mean +22.2%, **median −19.7%, win 30.9%**.
  - Dropping the top 1 / 3 / 5 trades gives a mean of +12.6% / +4.9% / **−1.2%**.
  - Bootstrap 95% CI [−2%, +52%]; top trade +1,319%.
  - 55 tokens, 77 wallets.
  - This is **lottery-tail driven. It is not evidence of edge.**
- **The same trades for the source itself** (tape prices): mean −4.3%, median −12.9%.
- **Fixed-horizon exits, S=$500, d=3:**

  | Exit | Mean | Median | Win |
  |---|---|---|---|
  | 1 m | −3.1% | −1.3% | — |
  | 5 m | −0.5% | −2.3% | — |
  | 30 m | +9.2% | −2.4% | 40% |
  | 60 m | +17.7% | −2.1% | 44% |

  All are again median-negative with a positive tail.
- **Delay sensitivity:** means and medians are flat from d=0 to d=600. The economics are set by **what** the wallets pick, not by latency.

**Cluster consensus** (≥3 tracked wallets within 10 minutes):
- 678 events across 543 pools (K≥5: 240).
- Rules were frozen in `cluster_eval.py` **before** any outcome was computed.
- GeckoTerminal minute candles for 200 seeded events were still downloading at session end. **No outcome computed.**

## 5. Other lanes

**CME (research agent; no Heimdall backtests run):**
- DEAD per source:
  - overnight drift: ≈0 since 2021 (NY Fed, 2026-07)
  - fast trend on ES/NQ: Sharpe 0.84 → 0.12 after 2008 (arXiv 2607.01550)
  - intraday momentum in the 0DTE era: flat (non-peer-reviewed retest to 2026-08)
- Candidates:
  - H4 overnight-gap fade, gated on high VIX: Della Corte et al., cross-sectional, t≈3.9, sample 2004–2018, gross.
  - H6 post-16:00 closing-pressure reversal: Bogousslavsky-Muravyev, stocks to ~2018. Lenkey 2024 calls LETF effects economically insignificant.
- Blocked or underpowered: pre-FOMC (44.5 bps pre-2015, 9.2 bps 2016–19), TOM, OPEX, closing-imbalance feed (no data), VIX term structure (no data).

**Crypto / other (research agent, live API pulls):**
- HL long-tail funding: 60 top-OI coins, 21 days. Median 13.7% APR. USELESS 42.3%, XMR 41.7%, PONS 38.0%, PURR 37.5%, GRASS 31.5%, VVV 31.2%. The sign of the excess held day-to-day in 118 of 126 pairs. BTC 8.9%, ETH 9.7%.
- HL vs Binance alt spreads: 4–20 pts.
- History [V, my own check]: funding history goes back to 2024-10/11 for PURR and GRASS and 2026-01 for XMR. Spot hedge on HL exists only for PURR.
- Polymarket:
  - Favourites ≥90c earn +0.83c per $ (arXiv 2609.12878, to 2026-09-11). Absent in Sports; negative skew.
  - Maker rewards: 36 of the top 100 markets, $7,419/day in total. Taker fee = C·rate·p(1−p); makers get 20–25% rebates.
  - The UAE is not on the block list.
  - UNRESOLVED: a live market's fee schedule (0.03 / 0.25) conflicts with the help centre (Sports 0.05 / 20%).
- Dead or blocked:
  - Deribit variance risk premium: own calculation, +9.9 → +5.6 → +3.7 → **−2.7** vol pts from 2024H1 to 2026H2.
  - HL market making: tier-0 maker pays 0.015%.
  - CEX→HL lead-lag: needs ~700 ms [U].
  - Kalshi: the UAE is restricted.
  - Listings: latency.

## 6. Tools (S5, tools lane)

| Tool | Verdict | Reason |
|---|---|---|
| Vibe-Trading `quantlib/multipletesting.py` | PILOT, this module only | DSR, PBO (CSCV) and BH. Heimdall has no PBO. Verify against Bailey & López de Prado worked numbers. |
| skfolio `CombinatorialPurgedCV` | PILOT, checker side | — |
| chainstacklabs `robinhood-chain-sequencer-feed` (rhfeed) | PILOT, feed reader | Run `--verify` and `bench.py` locally. Feed is a soft confirmation. |
| chainstacklabs `fomo-solana-rh-listeners` | ADOPT as reference spec | Address registry; run `verify_registry.py` first. |
| orderflow-metrics | PILOT, formulas only | — |
| Freqtrade `lookahead.py` | REFERENCE | GPL: re-implement the pattern, don't import. |
| NautilusTrader | DEFER | — |
| hftbacktest | DEFER | Last push 2025-12-23; no depth data. |
| Hummingbot, LEAN | REFERENCE | — |
| DuckDB | ADOPT incrementally | — |
| Polars | PILOT | — |
| Nitro relay | PILOT | BSL licence use on chain 4663 is [U]. |
| cvxv666 radar | REFERENCE | fomo API map. |
| AGPL / no-licence repos | REFERENCE only | — |
| Sniper, "copy bot" and drainer repos | REJECT | Likely malware. |

## 7. Global trial ledger (this session)

| ID | Family | Status | Why |
|---|---|---|---|
| T1 | Intraday momentum r_ROD | DEAD (tested 09-22) | Negative in train and holdout |
| T2 | Fade r_ROD | DEAD / contaminated | Idea came from T1 data; fresh MNQ contradicts it |
| T3 | Overnight drift | DEAD per source | NY Fed 2026 |
| T4 | Overnight-gap fade (H4) | CANDIDATE, untested | 2y MNQ holdout already read by ≥4 experiments; only Sierra 07-01→09-18 is fresher (read once) |
| T5 | Post-16:00 reversal (H6) | CANDIDATE, untested | Weak evidence |
| T6 | Pre-FOMC / macro drift | UNDERPOWERED | ~16 events in 2y |
| T7 | Turn of month / OPEX | UNDERPOWERED or BLOCKED | Flat by 16:45 |
| T8 | Closing-imbalance feed | BLOCKED | No data |
| T9 | CTA fast trend on index futures | DEAD per source | arXiv 2607.01550 |
| T10 | VIX term-structure gate | BLOCKED | No data |
| T11 | ES/NQ/RTY/YM relative value, lead-lag | NO EVIDENCE | HFT scale |
| T12 | Roll effects | NO EVIDENCE | — |
| T13 | HL long-tail alt carry | CANDIDATE #1 | 21-day discovery window contaminated; 2024-10→2026-08 untouched |
| T14 | HL vs Binance alt spread | CANDIDATE | Variant of T13 |
| T15 | HLP deposit | NOT AN EDGE | 3.3% APR |
| T16 | HL market making | BLOCKED | Fees |
| T17 | CEX→HL lead-lag | BLOCKED | Latency |
| T18 | Token unlock shorts | PARTIAL | Unlock calendars paid |
| T19 | Listing announcements | BLOCKED | Latency |
| T20 | OI/funding cross-section | WEAK PRIOR | Negative after cost [U] |
| T21 | Polymarket favourites ≥90c | CANDIDATE | Thin; negative skew |
| T22 | Polymarket maker rewards | CANDIDATE #2 | Needs live measurement |
| T23 | Polymarket vs Kalshi | BLOCKED | UAE |
| T24 | Deribit variance risk premium | DEAD | Negative 2026H2 |
| T25 | HL TWAP front-running | WEAK | arXiv 2606.15715 |
| T26 | Naive 1:1 wallet copy (mirror) | NOT SUPPORTED | Median −20%, lottery mean, sources lose |
| T27 | Copy only skilled / realized leaders | NOT SUPPORTED | Top quintile −9.3% in H2 |
| T28 | Avoid crowded wallets | NO SIGNAL | Followers vs return ρ=0.003 |
| T29 | Copy entry, independent exit (fixed horizon) | NOT SUPPORTED (prelim) | Median negative at every horizon |
| T30 | Multi-wallet cluster (K≥3) | PENDING | Rules frozen, data downloading |
| T31 | Graduation continuation (Pons) | UNTESTED | — |
| T32 | Shadow / low-follower wallets | UNTESTED | — |
| T33 | Influencer fade | INFEASIBLE | No spot short |
| T34 | Solana-deposit pre-signal | DEAD | Deposit does not name the token |
| T35 | Stock-token dislocation | WATCH | Earlier research: only APs can mint or redeem |

**Contamination.** The FomoPulse window 09-05→09-22 is discovery data for every T26–T30 rule. No untouched historical wallet data exists (FomoPulse starts on 09-05). Validating any wallet rule therefore requires **prospective shadow data from 2026-09-23 onward**.

## 8. Top 3 and red team

**1. T13 — HL long-tail alt funding carry (delta-hedged)**
- For: a live payer (leveraged longs), 22 months of untouched history, no latency requirement, and the existing HL connector.
- Against:
  - Carry here is compensation for squeeze risk, i.e. negative skew, which breaks the controlled-tail requirement.
  - The same family died on the majors.
  - Hedgeable capacity is ~$10–50k per name [I].
  - Spot hedges are missing for most names.
  - Binance fees are [U].
  - The 21-day evidence is selection-biased: coins were picked for high funding.

**2. T22 — Polymarket maker rewards**
- For: the platform pays; there is no latency race.
- Against:
  - Reward share against competing makers is unmeasured.
  - Adverse selection on news.
  - Fee schedule UNRESOLVED.
  - Cannot be backtested; it needs a live paper measurement.

**3. T30 — Wallet cluster consensus**
- For: latency-insensitive (median drift 0), and a free replay is possible.
- Against:
  - The sources lose in aggregate.
  - Manipulation labels (spoofed / planted / pile-in) exist exactly for multi-wallet signals.
  - Positive-tail illusions like §4.
  - There is no untouched history.

**Red-team verdict:** none survives. #1 has the best data, but its tail risk is the core problem. #3 is outcome-pending. **WINNER: NONE.**

## 9. Next experiment (frozen DRAFT; needs operator approval, then pre-register and hash)

**T13 HL long-tail carry, test once.**
- Universe: every HL perp with a Binance USD-M perp, monthly rank by trailing-30-day HL funding.
- Position: short HL / long Binance, notional $10k per leg; top 5 names.
- Rebalance: monthly.
- Costs: 4 taker legs at the documented fee (Binance fee must be fetched and hashed first).
- PnL: hourly funding on both legs plus mark-to-market basis PnL from HL `candleSnapshot` and Binance klines.
- Liquidation: forced exit if one leg moves −30%.
- Split:
  - Discovery 2024-10 → 2025-09.
  - Holdout 2025-10 → 2026-08-31.
  - 2026-09 excluded as contaminated.
- PASS requires all of:
  - holdout net APR > 10%
  - 3 of 4 holdout quarters > 0
  - worst month > −5% of gross notional
  - skew of monthly returns > −1
- FAIL means the family is dead. No tuning of names, thresholds or tenors.

## 10. Unfinished, and how to finish it

1. **Pool-log fetch** (406 pools, running in background) → copy `logs/` into `workspace/profit_discovery_2026-09-23/`, then run `python copy_sim.py 0.66` and `python copy_sim.py 0.20`.
2. **GeckoTerminal candles** (200 events, running in background) → copy `ohlcv/` in, then `python cluster_eval.py`. The rules are already frozen.
3. **Prospective shadow recorder** from 2026-09-23 onward, for any wallet rule.
4. **Pre-registration of T13** after owner approval.

## 11. Evidence receipts

- Robinhood Chain docs: https://docs.robinhood.com/chain/ · /connecting/ · /gas-and-fees/
- FomoPulse: https://github.com/itsnex1s/fomopulse-robinhood-chain-tape (`apps/server/src/fomo.ts`, `ingest/subscribe.ts`, `ingest/parse.ts`, `ingest/lag.ts`, `pnl.ts`, `api/routes.ts`) and https://fomopulse.app/api/{status,limits,traders,tape}
- RHTrenches: https://rhtrenches.com/app.js and /api/{status,traders,tape,closed,labels,radar,flow}
- GeckoTerminal: https://api.geckoterminal.com/api/v2/networks/robinhood/pools/{pool}/ohlcv/minute
- chainstack: https://github.com/chainstacklabs/fomo-solana-rh-listeners (`docs/02-trade-lifecycle.md`)
- Chain RPC: https://rpc.mainnet.chain.robinhood.com (`eth_getLogs` on PoolManager `0x8366a39cc670b4001a1121b8f6a443a643e40951`, Swap topic `0x40e9cecb…112f`, Initialize topic `0xdd466e67…6438`)
- HL: https://api.hyperliquid.xyz/info (`fundingHistory`, `spotMeta`); ETH price from https://api.coingecko.com
- CME lane URLs: NY Fed Liberty Street 2026-07; dev.to/firmtape retest; arXiv 2607.01550; Della Corte et al. PDF; Cboe gamma-squeeze paper; NBER w31923; AIMS QFE 2024; QuantSeeker TOM; Imperial MSc thesis (Morand).
- Crypto lane URLs: HL fees and funding docs; Binance fundingRate; Deribit DVOL; Polymarket gamma API and help centre; Kalshi help; coinperps; arXiv 2609.12878 and 2606.15715; Keyrock unlocks.

## 12. Relevance to the backtest-backend audit

- **The backend can produce positive results**, so it is not uniformly negative:
  - always-long last-half-hour MNQ holdout: +$408
  - Casper FVG train: +$2,867
  - fresh MNQ momentum: +$716
- **Defects from `VALIDATION_AUDIT_2026-09-22.md` that bias verdicts:**
  - D1 `sr_trials_var=1.0` → ~0% gate acceptance at any edge.
  - D2 prop MC at 1 contract → "0% pass" is a sizing verdict, not an alpha verdict.
  - D3 5-minute bar stop-first ambiguity.
  - D4 Dhesi wrong-side stops.
- **Conventions to re-check,** each individually conservative (the audit found none wrong):
  - entry +1 adverse tick
  - stop +1 extra tick
  - stop wins on the same bar
  - target filled exactly
- **None of this session's wallet-copy numbers use the Heimdall backtester.** They come from an independent on-chain replay, validated against tape round trips (corr 0.77), so backend defects do not affect them.
