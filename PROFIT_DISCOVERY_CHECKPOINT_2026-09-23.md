# HEIMDALL — Profit Discovery checkpoint 2 (2026-09-23)

This continues `PROFIT_DISCOVERY_2026-09-23.md` and supersedes that file's §4 preliminary numbers, T13 status and §7 "no untouched history" claim.
Labels: [V] verified this session · [I] inferred · [U] unverified.
Data and scripts: `workspace/profit_discovery_2026-09-23/`. T13 audit: `workspace/t13_audit_2026-09-23/T13_AUDIT.md`.
Validator completion: `VALIDATION_COMPLETION_2026-09-23.md`, written by an independent checker.

## Background job recovery [V]

| Job | Result |
|---|---|
| Pool-log fetch | 406 of 406 pools written. 0 fatal errors. Timeout ranges were bisected; 0 pools flagged `failed`. |
| Candle fetch (GeckoTerminal) | 201 files for 200 seeded events, 189 of them with candles. 11 events had no candles; 489 of the 678 K≥3 events were not sampled by design. |
| Final analyses | `copy_sim_FINAL_gas066.txt`, `copy_sim_FINAL_gas020.txt`, `cluster_eval_FINAL.txt`. `copy_sim_results.parquet` holds the gas-$0.20 run. |
| Replay coverage | 866 sampled buys → 699 simulated. 153 skipped because the source swap routed through a non-v4 pool; 14 skipped for lack of a pre-state. 564 have a mirror exit. |
| Backfill probe | 20 wallets, 0 failed chunks. |

## Final wallet results (699 buys, 406 pools; supersedes the 181-buy preliminary)

| Rule, S=$500, d=3 blocks | Preliminary (181 buys) | Final (699 buys) | Final robustness |
|---|---|---|---|
| Median entry drift, d = 1–150 blocks | 0.0000 | **0.0000** | p90: 0.8% at d=3, 5.0% at d=50, 8.7% at d=150, 16.8% at d=600 |
| Mirror exit | mean +22.2%, median −19.7%, win 31% | mean **+19.3%**, median **−23.2%**, win 29.5% | 95% CI [−0.8%, +48.5%]. Drop top 5 → −1.1%; drop top 10 → −5.9%. The top 10 trades carry 130% of total PnL. |
| Source's own round trip (same trades) | mean −4.3%, median −12.9% | mean **−10.7%**, median **−15.5%** | — |
| Fixed 1 m exit | −3.1% / −1.3% | −3.1% / −1.7% | — |
| Fixed 5 m exit | −0.5% / −2.3% | +2.3% / −1.6% | CI [−0.5%, +5.7%]. Top 10 carry 140% of PnL. |
| Fixed 30 m exit | +9.2% / −2.4% | +12.9% / −2.2% (gas $0.66); +13.1% / −2.0% (gas $0.20) | CI [+5.9%, +20.7%], drop-10 +3.8%, before the honeypot correction |
| Fixed 60 m exit | +17.7% / −2.1% | +18.0% / −4.2% | CI [+8.8%, +28.7%], drop-10 +5.3%, before the honeypot correction |

Gas sensitivity is small: gas $0.20 vs $0.66 moves the mirror mean by about 1 point. Delay d=0 to d=600 blocks (0–60 s) changes nothing material. **Latency is not the binding constraint.**

### Honeypot correction (decisive) [V]
The replay assumes our sell succeeds at the pool price, which is false for honeypot tokens.
- 55 of the 699 buys are in tokens no tracked wallet ever sold. Their 30 m mean is +117% and their median +41%.
- In those pools, median sell-direction swaps in the next hour = **2**, against **342** elsewhere; **36% had zero sells**.

Re-scored, 30 m / 60 m exits:

| Scoring | 30 m | 60 m |
|---|---|---|
| (a) Zero-sell pools scored −100% | mean +7.7%, median −2.6%, CI [+0.8%, +15.3%], drop-10 −1.2% | mean +12.8%, drop-10 +0.1% |
| (b) Point-in-time filter: ≥5 sells in the pool in the 5 min before entry | n 530, mean +11.7%, CI [+3.9%, +20.3%], drop-10 +1.6% | mean +16.4%, drop-10 +1.3% |
| (b) minus 13 later-honeypot suspects | n 517, **mean +6.2%, median −3.3%, win 42%, drop-10 −1.3%** | mean +11.0%, drop-10 −2.6% |

Size sensitivity (30 m exit, drop-10 in brackets): S=$100 +15.9% (+5.3%) · S=$500 +13.1% (+3.8%) · **S=$2,000 +4.9% (−1.4%)**. Capacity is therefore at most about $500–1,000 per trade.

**Verdict for the copy-entry, fixed-exit rule:**
- ALPHA = **INCONCLUSIVE**. The mean is positive, but it depends on the tail and flips sign when the top 10 trades are dropped.
- It is sensitive to honeypot handling. Input-side hook fees are not modelled, which makes it optimistic.
- The window is contaminated: it is the discovery window, and 5 exit rules × 9 delays × 3 sizes were examined.
- EXECUTION = INCONCLUSIVE. DEPLOYMENT = N/A: it is not on the Lucid money path.

**Power:** per-trade SD is 0.975. A +5% useful edge needs about 2,348 trades at 80% power; +2% needs about 14,675.

### Multi-wallet cluster (K≥3 wallets in 10 min, 189 events with candles; rules frozen beforehand) [V]
- Entry A net: 5 m mean +34.6% (median −5.6%); 30 m +199% (median −22.5%, win 24%); 2 h +315% (median −36.7%); 6 h +103% (median −54%).
- Random-entry baseline on the same pools: −2% to −8%.
- The mean is lottery-driven. The top 10 events carry 113–115% of net PnL. Dropping them gives 30 m −31% and 2 h −45%.
- Requiring ≥$500 of USD volume in the exit window: 2 h mean −26%.
- The top event rose 74× on **$73** of volume in a **$5,160** pool.
- The liquidity cap uses post-event DexScreener liquidity, which is lenient on winners.

Verdict: ALPHA **FAIL on realizable basis / INCONCLUSIVE on raw**. The median is negative at every horizon. Not promoted.

## Historical backfill result [V]
- **"FomoPulse has no earlier index" ≠ "no chain history".** Robinhood Chain block 1 is 2026-04-30; mainnet runs from ~07-01.
  - The public RPC serves `eth_getLogs` for early ranges. Some ranges time out and need bisection.
  - Probe: 20 seeded tracked wallets, 2026-08-05 → 09-05. **13,714 token transfers in, 1,496 out, 13,462 distinct transactions, 2,553 tokens, 0 failed chunks.** For comparison, FomoPulse has 4,364 non-dust fills for the same wallets over 09-05→09-22.
  - Of 40 random incoming transactions, 8 contain a swap (7 v4, 1 v2) and 32 are handouts. So roughly 20% are real, priceable trades [I].
- **Contamination:** FomoPulse's wallet universe was chosen on about 09-05 from the fomo leaderboard, which reflects pre-09-05 performance.
  - Backfilled pre-09-05 trades of *these* wallets are **in-sample to selection**, so survivorship pushes returns upward.
  - A clean historical test needs a point-in-time universe of *all* FOMO wallets (ERC-4337 EntryPoint `0x4337084D…f108` UserOps plus Relay executor fills). That is reconstructable but expensive on the public RPC.
- Status: **feasible, not executed.** The recommended route is FomoPulse's own `ingest/rebuild.ts` with an earlier start block, or a paid RPC (quote required).

## FOMO leaderboard reconciliation
- **Official leaderboard: BLOCKED for read-only access** [V 2026-09-23].
  - `fomo.family/leaderboard` and `/profile/*` redirect to the landing page without login.
  - The API (`prod-api.fomo.family`) refuses non-browser clients (403/430).
  - No login was attempted.
- Schema per `cvxv666/fomo-robinhood-radar/docs/fomo-endpoints.md` (third-party capture 2026-09-04, **[U] today**):
  - `/v2/leaderboard/{24h|7d|30d}` returns 150 rows.
  - `pnl{window}` = realized PnL in USD for the window.
  - FomoPulse's code says fomo's figure is **account-wide across other chains**.
  - The per-user addresses fomo reports are internal and have zero on-chain events.
  - The External-Alpha lane found fomo's PnL formula **UNRESOLVED**: sources conflict between realized, realized + unrealized, and net cash flow.
- **Frozen universes:**
  - FomoPulse has 294 wallets (list frozen about 09-05, since fomo returns 403 to it). RHTrenches has 147 (since 08-27).
  - They overlap on **121 addresses**; all 119 handles present in both map to the same address. There are 26 RHTrenches-only and 173 FomoPulse-only wallets.
  - FomoPulse PnL is average-cost, chain-4663 only. RHTrenches has its own method.
  - Per the External-Alpha lane, the two disagree in **sign** of 30-day realized PnL on 21 of 121 common wallets (median |diff| $41,259). In aggregate both are negative: RHTrenches −$17.47M; FomoPulse −$11.60M over this window.
- **Conclusion:** a leaderboard is a *different population and PnL definition* (multi-chain, realized, current). Neither frozen tape universe equals today's top-150. **Never select wallets from any indexer's PnL**; rebuild PnL from chain data.

## T13 distinctness audit (full: `workspace/t13_audit_2026-09-23/T13_AUDIT.md`)
Verdict **REVISE-SPEC, leaning REJECT as specified.**
- **Same family as the killed spread.** Short HL / long Binance P&L = HL funding − BN funding, which is killed family (2) on a new asset list. The 10.95% interest components cancel between venues.
- **The discovery signal is largely a new-listing effect.** USELESS's first HL funding row is 09-08 and PONS's 08-31.
- **Hedges were mostly unavailable in the proposed windows.** PONS's Binance perp onboarded 2026-09-06; PURR has none; 21 of the top 60 onboarded after 2024-10.
- **Universe churn:** 234 HL perps, 56 delisted, 44 delisted inside the proposed window. Delisted names keep printing hourly `0.0` funding rows, a survivorship trap.
- **Costs and capacity:** 4 taker legs ≈ 19 bps (Binance fee [U]); capacity about $5–25k per name; 88 of 178 live perps capped at 3×.
- **Tails:** JELLY forced settlement, XPL +200%, POPCAT bad debt, and ADL on 2025-10-11.
- **Required if ever revived:** reframe as an alt HL−Binance spread; inherit the family-(2) decay and one-sidedness gates; point-in-time universe; hedge onboarded ≥7 days earlier; drop the first 30 days after listing; squeeze tail model. **Not pre-registered.**
- A failed T13 does **not** kill spot-hedged carry or other funding hypotheses automatically.

## Net-economics table (S3)
Economics that are UNKNOWN are penalized by default: rank below any measured, non-negative candidate.

| Candidate | Gross edge | Exec cost | Fees / funding | Slippage / impact | Capital | Capacity | Tail loss | Net deployable edge | Data can supply N? |
|---|---|---|---|---|---|---|---|---|---|
| W1 copy entry + fixed 30 m exit (RH chain) | Modelled +6–12% per trade (honeypot-adjusted), median −3% | Gas $0.20–0.66 × 2 (in model) | Pool LP fee in model; input-side hook fees **not** (optimistic) | In model (constant-L pool math); latency-insensitive | ~$16k (≈31 concurrent × $500) [I] | ≤ $500–1,000 per trade; negative drop-10 at $2k | −100% per trade (honeypot / rug / sell tax) | **INCONCLUSIVE; sign not robust** | Yes, prospectively: about 9 days of forward shadow for ~2,350 token-independent trades [I] |
| Wallet cluster K≥3 | Raw mean positive, realizable ≤ 0 | As W1 | ~2% RT assumed | Unrealizable tail | — | — | −100% | **≤ 0 (FAIL realizable)** | — |
| Mirror copy | Mean from tail, median −23% | As W1 | As W1 | As W1 | — | — | −100% | **≤ 0 (drop-10 −5.9%)** | — |
| T13 HL alt carry / spread | UNKNOWN (contaminated 21 d: a few names at 20–40% APR gross) | 19 bps RT + legging | Pays Binance funding | 10–20 bps premium, thin books | ~1× notional at 2× per leg | $5–25k per name | Squeeze / forced settlement / ADL | **UNKNOWN (penalized; family decayed before)** | Partially: small hedgeable universe per month |
| Polymarket maker rewards | UNKNOWN; ceiling $7,419/day across 36 markets | Quoting infrastructure | Maker fee 0, rebates 20–25% [V help centre]; fee schedule conflict UNRESOLVED | Adverse selection unmeasured | Inventory | Reward share unknown | Jump risk on news | **UNKNOWN (penalized)** | Only by live paper |
| Polymarket ≥90c favourites | +0.83c per $ (external paper to 2026-09-11) | Taker ~0.2c per $ at p=0.95 (0 as maker) | — | Near-resolution depth thin | Locked until resolution | Low | −100% per bet | ~+0.6c per $ per cycle [I] | Needs ~7,000 bets for 80% power; historical data reuse is **not** independent OOS |
| CME H4 overnight-gap fade (MNQ) | UNKNOWN; literature 2004–2018, cross-sectional, gross | ~$2–3 per trade (audit V5) | $1 RT | 1 tick per side (uncalibrated) | $50k prop account | 1–4 micros | Gap days | **UNKNOWN (penalized)**; Lucid-compatible | Only if edge ≥ ~$17 per trade (SR 0.2, N=155); a $8 per trade edge needs ~700 trades (more than 2 years). MNQ holdout already reused ≥5 times. |
| CME H6 post-16:00 reversal | UNKNOWN, weak literature | as H4 | as H4 | Thin post-16:00 liquidity | as H4 | as H4 | — | **UNKNOWN (penalized)** | as H4 |

## Top 5 (uncertainty-penalized)
1. **W1 forward shadow** (copy entry + fixed exit, with an on-chain sell-simulation honeypot check). The only candidate with *measured* economics and a positive point estimate. INCONCLUSIVE, fragile, $0 to test prospectively. Money path: self-custodied RH-chain wallet. **Owner decision:** not Lucid.
2. **CME H4 gap-fade.** Lucid-compatible and runs on owned data, but the edge is unknown and the holdout has been reused. Needs power and trial-count handling from the validator completion.
3. **Polymarket ≥90c favourites.** A small measured external edge; negative skew; about 7k bets needed.
4. **Polymarket maker rewards.** Platform-paid, but the economics are unknown until live measurement.
5. **T13, revised as the alt HL−Binance spread.** Demoted: same family that decayed, tiny capacity, severe tails.

Dropped: mirror copy and cluster copy (≤ 0 realizable), influencer fade (infeasible), Deribit VRP (negative), HL market making (fees), Kalshi (UAE).

## Red team
- **W1**
  - Positive mean rests on about 10 trades out of ~700.
  - Honeypots flip it once detection is imperfect.
  - Input-side hook fees are missing.
  - The one 17-day window is a memecoin-mania regime.
  - Crowding by other copiers is only partially in pool state.
  - Contract-level risks: mint, blacklist, ArbOS compliance voiding.
  - Needs a signing wallet, which is not currently authorized.
- **H4**
  - The mechanism faded after 2021 (NY Fed: overnight drift ≈ 0).
  - Close to the dead VWAP-reversion family.
- **Polymarket items:** skew and eligibility / terms [U].
- **T13:** see the audit.

## Winner: NONE.

## Validator completion (independent checker; full: `VALIDATION_COMPLETION_2026-09-23.md`)
- Status stays **TRUSTED WITH LIMITATIONS**; global TRUSTED not justified. Reviewer pass confirmed PnL engine, split, D1, D2;
  NW t vs statsmodels 1.5e-14; PSR/DSR exact. PARTIAL: walk_forward drops first of n+1 folds.
- Differential vs backtesting.py 0.6.6 (py3.12 extvenv): 559 trades, identical count/entry/exit bars; zero-slip diffs = 6 gap-through-
  target trades (Heimdall conservative by $7.00 total); production diffs = predicted slippage tax exactly.
- New defects: N1 MNQ-holdout reuse ≈ 12 configs/8 families on MNQ, ≈65 configs across MNQ/MES/ES (memory said 3); N2 max_dd gate
  is scale/length-dependent (ES-sized streams can be structurally rejected); N3 off-tick VWAP targets (conservative $0.095/tr);
  N4 zero-PnL trades dropped in 2 validators (latent); N6 iid prop MC (optimistic); N7 prop_engine default buffer 400 vs doc 325
  (validators pass 325); N8 16:00 bar flatten at 16:01.
- Gates: DISCOVERY (single dependence-aware test, one-sided α .10, pre-declared useful edge + N80, FDR q .10 over ledger) vs
  DEPLOYMENT (all convention-A thresholds + ledger deflation, real CSCV PBO, session-block bootstrap, prop pass vs contracts,
  fresh/prospective data only). With ledger SR0 ≈ 0.14/trade a DEPLOYMENT pass on the reused 2025-09→2026-06 window is
  practically unreachable — capital evidence must come from fresh/prospective data.
- Not done: strategy-specific simulators (inversion, okala, orderflow, intraday_momentum) not diffed externally; slippage and Lucid rule
  encodings remain uncalibrated/unverified.

## STATUS: CHECKPOINT — DO NOT REQUEST EXPERIMENT APPROVAL
Open: official FOMO leaderboard (login-blocked); full historical backfill (feasible, not executed); strategy-specific simulator diffs.
