# HEIMDALL — Agent 2: audit of Agent 3's Top 5 (2026-09-23)

**STATUS: COMPLETE, except the Pons on-chain graduation count** (the public RPC rate-limited us: 429; not retried).

- No implementation, no paid downloads.
- Agent 3's `[VERIFIED]` labels were not accepted; each claim was rechecked against primary sources or free data.

## 1. Pre-registration file conflict — RESOLVED: timing, not path/worktree
- **Is the file real?** Yes. `FOMO_PROSPECTIVE_PREREGISTRATION.md` exists at the repo root.
  - Its mtime is 2026-09-23 08:38:48 +04:00 (04:38:48 UTC).
  - Its `.sha256` file was written at 04:38:50 UTC.
  - SHA-256 = `902263424c170fb7920c0a0880f056a8c7cc1b80e9a8dd5f2708a883c72fbc39`, matching the `.sha256` file [V].
- **Why Lane B said it didn't exist:** Lane B's `ls` ran at ~04:35 UTC, before the file was frozen. `LANE_B_REPORT.md` was then written at 04:50 UTC **without re-checking**.
- **Resolution:** this was a Lane B error, not a missing artifact. A correction is appended to `LANE_B_REPORT.md`. The directory is not a git repo and there are no worktrees.

## 2–4. Agent 3 claims: survived / downgraded / falsified

| Claim | Verdict | Evidence |
|---|---|---|
| W1 is lottery-driven, negative median | **SURVIVED** | Matches the Lane B audit. |
| H2 causal arrow reversed in CME hours | **SURVIVED** (Lane B measured it: NQ leads 10/10) | — |
| NYSE imbalance at 15:50, **Nasdaq at 15:55** | **FALSIFIED (Nasdaq part)** | Nasdaq NOII starts **15:50** ET (every 10 s to 15:55, then every 1 s) — nasdaqtrader.com Closing Cross FAQ. |
| Pons V2 anti-snipe "80%+ decaying over minutes", entry at graduation after fees clear | **FALSIFIED** | Official docs: snipe tax is **99% → 0 over the first 5 s after the curve OPENS** (~25% at 1 s, ~3% at 2 s), buys only. It is not a graduation-time fee. |
| Pons graduation into "$50k+ locked liquidity", impact <1.5% | **FALSIFIED / UNRESOLVED size** | Bitquery: **4.2 ETH** threshold for native-quoted launches (≈$11.5k at ETH ≈ $2,750); per-config for ERC-20 quotes. The docs' example shows a 100 ETH config. Liquidity is permanently locked (true). |
| "Block N+1 after graduation" has an economic basis | **FALSIFIED** | Docs: graduation seeds the v4 pool "of the same size, at the same price". There is no price discontinuity to arbitrage. The hook keeps charging the curve-phase fee. |
| HL intra-venue basis is "different from dead work" | **DOWNGRADED** | It is dead family #1 (single-venue funding carry) with a same-venue hedge. See §5. |
| "Polymarket $7,400+/day ceiling" | **DOWNGRADED** (number stale) | Live, full pagination: **774 rewarded markets, $11,235/day**. It is still gross revenue, not edge. |
| Weekend HL→CME: "TD Securities: HL priced 80% of weekend moves" | **UNVERIFIED** (no source given). Our own free test: CME open incorporates **61–74%** of the HL weekend move. | See §5. |
| HL validators "clustered in AWS Tokyo, 2–3 ms", OrdoFi "sealed-bid backrun auction", "Pools.trade by Uniswap Labs" | **UNVERIFIED** (no primary URLs in the report) | Not load-bearing for the Top 5; not re-litigated. |
| "Lucid permits Sunday 18:00 trading, 100% verified" | **UNVERIFIED** (no source). Memory only says "resume 6:00 pm". | — |

## 5. Top-5 audit table

| | 1. Cash-MOC → ES/MES | 2. Polymarket rewards MM | 3. HL spot-perp carry | 4. HL weekend → CME Sunday open | 5. Pons V2 graduation |
|---|---|---|---|---|---|
| Mechanism verified? | Publication times verified (both 15:50). Price-pressure-in-futures mechanism **not** verified. | Reward program verified (live API fields). | **Yes:** HL funding = premium + clamp(interest), interest 0.01%/8 h paid to shorts. | **Partly:** open incorporates 61–74% of the HL move (n=23 MES, 26 MNQ). | Graduation mechanics verified; **no** price event at graduation. |
| Causal variable observable? | Real-time imbalance is a paid exchange feed. ES volume/delta is **not** the imbalance. | Yes (own quotes, book). | Yes (funding, basis). | Yes (HL 1 h candles before the open). | Yes (events). |
| Historical data? | **Paid only** (Databento `imbalance` on XNYS.PILLAR / XNAS.ITCH; NYSE TAQ imbalances). Free: 2 sample days on the NYSE FTP (2026-04-01/02, NYSE-listed only). | Trades yes; historical book mids / reward earnings **no**. | Free: 5000 h of candles plus funding. | Free: HL 1 h back to 2026-02-26; CME owned. | Free chain logs (count incomplete: RPC 429). |
| Proxy / fidelity risk | High if ES delta is used as a proxy. | Trade-based markouts include bid-ask bounce. | Hourly closes (no spread). | Opening-print fill is unrealistic. | — |
| Execution realism | Lucid-compatible (15:50–16:00). | Needs quoting infrastructure, eligibility [U]. | Crypto account, capital-heavy. | Lucid Sunday session [U]. | Signing wallet (not authorized). |
| Fees / subsidies | $1 / $3.50 RT + ticks. | 91% of rewarded markets have fees enabled; maker rebates per help centre (PD). | Spot 0.070% / perp 0.045% taker; USDC lend 3.57% opportunity cost [V]. | $1 / $3.50 RT. | Hook fee = curve fee; snipe tax only in the first 5 s. |
| Capacity | High. | Market-limited; reward share unknown. | HYPE decent; UBTC/UETH/USOL spot thin. | 1 event per week. | Tiny pools (~$11.5k quote side). |
| Tail risk | Imbalance flips at 15:55–16:00. | Jump-to-resolution. | Short-perp margin on rallies; Unit-bridge custody risk for UBTC/UETH/USOL. | Weekend news. | Rug / honeypot class. |
| Data contamination | MNQ holdout reused ~12 configs; intraday-momentum window overlaps. | None. | Recomputed now. | These 23–26 weekends are now **discovery**. | — |
| New vs graveyard? | Cash-MOC: new. ES-close-flow: adjacent to dead intraday momentum / H6. | New. | **No:** dead family #1. The reopen is justified only by a validator defect (below). | Adjacent to X3 (killed open-forecast); the post-open drift variant is new. | Adjacent to the FOMO copy family. |
| Cheapest honest falsification | Databento **cost quote** (free API call; needs key) for `imbalance`, 15:50–16:00, ~1 year, then a pre-registered test. | Prospective paper-quoting measurement with book mids and reward attribution. | **Done (below).** | **Done (below):** prospective weekends needed. | Finish the free graduation count plus forward-return replay. |

**Test results:**
- **HL carry** (2026-02-26 → 09-23, net of base-tier round-trip fees and basis change):

  | Pair | Hold net, annualized | Excess over USDC lend (3.57%) |
  |---|---|---|
  | HYPE | 8.59% | +5.0 pp |
  | ETH | 5.00% | +1.4 pp |
  | BTC | 4.33% | +0.8 pp |
  | SOL | 0.60% | −3.0 pp |

  All are before perp margin dilution.
- **Why reopening family #1 is legitimate:** `core/alpha/carry.py:14` charges the fee **every hourly bar held** (`ret = pos*(f - fee)`, fee=2e-5): ≈17.5%/yr of phantom cost. The economic fact that changed is **nothing**: the old kill was defective. Correctly computed, it is a low-excess treasury-like carry, not alpha. **Verdict: DOWNGRADED.**
- **Weekend test, realistic 18:01 ET entry, trading sign(residual):**

  | Pair | t at 15 / 60 / 120 min | n |
  |---|---|---|
  | MES | 0.48 / 0.97 / −0.23 | 23 |
  | MNQ | 0.37 / 1.86 / 0.88 | 26 |

  Most of the apparent predictability sits in the first minute after the reopen, which isn't capturable. **Verdict: WATCH / underpowered.**
- **Polymarket:**
  - Gross subsidy upper bound: median 5.6%/yr on posted liquidity; top market 31 bps/day.
  - Clean adverse selection: **unmeasured**. Trade-only markouts include the bounce, so they cannot separate spread from adverse selection.

## 6. Candidates worth a real experiment
1. **Weekend HL→CME, prospective only.** It needs Lucid's Sunday-session permission verified first.
2. **Cash-MOC,** only after a paid-data cost quote. The ES-close-flow variant needs pre-registration **before** touching the last fresh Sierra window.
3. **Polymarket,** only as a live paper measurement (not a backtest).

HL carry = downgraded (treasury product). Pons = falsified as specified.

## 7. Exact data required
- **MOC:** Databento `imbalance` schema, XNYS.PILLAR + XNAS.ITCH, S&P 500 constituents, 15:50–16:00 ET, ≥12 months. **Cost quote only.**
- **Weekend:** prospective HL `xyz:SP500`/`XYZ100` (the recorder already captures them) plus CME Sunday opens.
- **Polymarket:** live order-book snapshots plus own quote logs.

## 8. Cheapest next falsification
Weekend: freeze the rule now (sign of HL-move-minus-18:01-gap, 60-minute hold). Then evaluate on the next ≥26 weekends. There is **no** historical re-use.

## 9. WINNER: NONE

## Artifacts (this folder)
- `hl_spot_perp_carry.py/.json`
- `weekend_hl_cme.py/.json`, `weekend_rule_realistic_entry.json`, `weekend_MES.csv`, `weekend_MNQ.csv`
- `polymarket_subsidy_vs_adverse.py/.json`
- `pons_v2_counts.py` (incomplete run)

## Sources
- https://www.nasdaqtrader.com/trader.aspx?id=openclose
- https://www.nyse.com/publicdocs/nyse/NYSE_Opening_and_Closing_Auctions_Fact_Sheet.pdf
- https://ftp.nyse.com/Historical%20Data%20Samples/TAQ%20NYSE%20ORDER%20IMBALANCES/
- https://databento.com/docs/examples/equities/auction-imbalance
- https://databento.com/blog/NYSE-imbalance-feeds
- https://docs.ponsfamily.com/v2
- https://docs.bitquery.io/docs/blockchain/robinhood/pons-api/
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
- https://gamma-api.polymarket.com/markets
- https://data-api.polymarket.com/trades
