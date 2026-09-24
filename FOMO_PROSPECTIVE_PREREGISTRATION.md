# FOMO prospective copy-entry / fixed-30-minute-exit — Pre-registration

**Frozen 2026-09-23, before any prospective outcome was recorded.**
- Every FOMO result through 2026-09-23 is DEVELOPMENT data (`workspace/fomo_lane/fomo_trials_dev.json`, 153 configs / 6 families).
- This is ONE new trial on data that does not yet exist.
- Discovery-gate test only. It authorizes no capital, no signing and no live order.

## Hypothesis
Buys by active FOMO wallets on Robinhood Chain (4663) carry positive short-horizon continuation. A follower who:
- observes each buy through the public sequencer feed,
- passes only point-in-time safety checks,
- buys $500 of the same token through the same pool, and
- exits exactly 30 minutes later

earns a positive **net** mean return per trade, after LP fees, measurable hook fees, price impact and gas.

## Source events (all point-in-time)
- **Buy event:** an ERC-20 `Transfer` from the Relay executor `0xb92fe925DC43a0ECdE6c8b1a2709c170Ec4fFf4f` to a **FOMO wallet**.
  - FOMO wallet = code starts `0xef0100` and delegates to `Simple7702Account` `0xe6cae83bde06e4c305530e199d7217f42808555b`.
  - The same transaction must contain exactly one identifiable swap (Uniswap v2, v3 or v4, or a Pancake v3 fork) whose output token is the transferred token.
  - Anything else is logged as UNROUTABLE and excluded; the exclusion rate is reported.
- **Sell event:** a FOMO wallet's ERC-4337 `UserOperationEvent` (EntryPoint `0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108`) whose transaction sells a token. Used only for rolling wallet statistics.
- **Universe U(T):** FOMO wallets with **≥10 recorded buy events in the 72 h before T**, counted from the recorder's own chain data.
  - Warm-up uses the same logic on the 72 h of chain logs before recording starts.
  - No indexer or leaderboard PnL is ever used for selection.
- **Notional filter:** source buy ≥ $100. Value = tokens received × DexScreener `priceUsd` fetched at detection time (point-in-time). If the price is unavailable, the event is excluded and counted.
- **Covariates, recorded but NOT used for selection:** each wallet's rolling realized PnL (average cost, own data), trade count, capital deployed, win/loss distribution, token concentration, holding periods, liquidity traded, drawdown and 72 h persistence.
  - Any selection on these is a SEPARATE future hypothesis.

## Safety filters (information before entry only; all must pass)
- **S1 prior sells:** ≥5 sell-direction swaps in the same pool by transactions other than the source's, within the 300 s before the source block.
  - If the recorder has not yet observed the pool for 300 s, S1 counts only observed history. Coverage is flagged.
- **S2 transfer simulation:** `eth_call` of `token.transfer(poolAddressOrPoolManager, 1% of source amount)` from the source wallet at the latest block does not revert.
- **S3 depth:** the modelled price impact of a $500 buy at the entry state is ≤ 5%.
- **Not modelled, reported:** v4 hook sell-path behaviour beyond S2, and mint/blacklist/pause authority. Bytecode selector presence is logged as a covariate.

## Execution model
- **Clock:** `t_arr(b)` = local arrival time (ns) of L2 block b on `wss://feed.mainnet.chain.robinhood.com` (block = sequenceNumber − 2, measured 2026-09-23).
- **One-way sequencer latency:** `ow` = half the median round trip to `https://sequencer.mainnet.chain.robinhood.com`, re-measured every 10 minutes.
- **Follower timing:** submission time `t_sub = t_arr(b_src) + processing + extra_delay`.
  - Processing is the recorder's measured decode, decision and signing-equivalent time.
  - The follower transaction reaches the sequencer at `t_sub + ow`.
  - Target block `b_tgt` = the first block with `t_arr(b) − ow ≥ t_sub + ow`.
- **Entry state:**
  - PRIMARY is pessimistic: pool state at the END of `b_tgt` (the follower lands last in its block).
  - Optimistic: END of `b_tgt − 1`. Reported, never primary.
- **Fill math:**
  - v2: constant product with fee. v3/v4: constant liquidity inside the current tick (tick crossings ignored; flagged).
  - LP fee from pool state. Output-side hook/transfer tax is measured per pool from the source's own fill (event amount vs transfer amount) and applied to both legs.
  - Input-side hook fees are not observable, so a sensitivity of +1% per side is reported.
- **Exit:**
  - Exit block = first block with `t_arr ≥ t_arr(b_tgt) + 1800 s`.
  - Sell of the received tokens at the END-of-block state, same fee and tax model.
  - At exit time, S2 is re-run as an exit-sellability check. If it reverts, or the pool has no state, the trade scores **−100%**.
- **Gas:** $0.66 per swap, the median measured on FOMO-route swaps on 2026-09-23. Charged on both legs.
- **Primary latency variant:** the measured path from this host, extra_delay = 0.
- **Additional variants,** each a secondary report and never a gate: extra_delay ∈ {100, 250, 500, 1000, 2000, 5000} ms, plus the next block (`b_src + 1`).
- **Size:** $500 fixed. Overlapping positions are allowed; each event is independent.

## Primary statistic and discovery gate
- **Statistic:** per-trade net return `(proceeds − 500 − gas)/500` under the PRIMARY variant.
- **Minimum useful edge (MUE):** +5.0% net per trade.
- **Uncertainty:** token-cluster bootstrap, 10,000 resamples, seed 20260923. One-sided 90% bounds.
- **Verdicts:**
  - **PASS:** lower bound > 0 **and** the mean excluding the top 1% of trades by return is > 0.
  - **FAIL:** upper bound < MUE.
  - **INCONCLUSIVE:** anything else.
  - **UNDERPOWERED** (added label): effective N below target at the stopping time.
- **Design effect:** 1.39, from development pool clustering. Required N at 80% power ≈ 3,274; frozen target **N = 3,500 eligible trades**.
- **Stopping:** evaluate once, when both ≥3,500 eligible trades **and** ≥14 calendar days are reached, or at 45 days, whichever comes first.
- **No interim outcome analysis.** Interim reports may state only counts and integrity metrics: events, exclusions by reason, feed gaps, RPC errors.
- **Reported, not gating:**
  - optimistic state;
  - every latency variant;
  - input-fee sensitivity;
  - medians and drop-top-10;
  - day-block bootstrap;
  - wallet and cohort clusters;
  - an unfiltered comparison (no S1–S3).

## What kills the hypothesis
- FAIL.
- PASS failing its own tail condition, i.e. mean ≤ 0 excluding the top 1% (reported as INCONCLUSIVE-TAIL, never PASS).
- Recorder integrity failure: > 5% of blocks missing timing, or > 10% of events unroutable without explanation. Result: VOID; a new pre-registration is required.
- Any post-hoc change to filters, exits, sizes or thresholds, which creates a new hypothesis.

## Scope and authority
- Discovery only. DEPLOYMENT = N/A.
- A PASS justifies only a separately pre-registered deployment-grade test (fresh data, trial-count correction, capacity and tail analysis) and an owner decision on a self-custodied wallet.
- No keys, no signing, no orders in this experiment.
