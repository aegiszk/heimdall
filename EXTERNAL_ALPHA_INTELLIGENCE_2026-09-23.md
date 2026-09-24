# HEIMDALL — External Alpha Intelligence Program (Phase 2), 2026-09-23

**STATUS: CHECKPOINT — MORE SEARCH REQUIRED.**
New primary data sources were still appearing in the final pass (Hydromancer Reservoir, the Tardis free samples, the HIP-3 CME-analog markets). The decisive wallet-level tests are blocked on one owner decision: an AWS account for the requester-pays S3 data.

**Labels:**
- [V] verified this session by fetch or command.
- [I] inferred from [V].
- [U] unverified.
- [A] taken from an existing repo artifact.

**Where the evidence lives:** scripts and raw captures are in `workspace/external_intel_2026-09-23/`.

**Scope:** this phase extends `PROFIT_DISCOVERY_2026-09-23.md` (PD). It does not repeat that report.
- PD's T1–T35 ledger stands, except where it is corrected below.
- Settled strategy failures were NOT rerun.
- The validator defects D1–D4 (`VALIDATION_AUDIT_2026-09-22.md`) were already applied by that audit's own historical-impact table. No new validator defect was found here.

## 0. Money-path conflict (surfaced, not resolved)

`CLAUDE.md` defines the current phase as Lucid 50K FLEX, which allows **CME futures only**.

Every Hyperliquid (HL) and Robinhood Chain candidate below needs a separate crypto account. That is Track B/C in `Heimdall.md`, not Lucid.

Only **H2** (HL CME-analog wallet flow used to forecast MES/MNQ) can reach the Lucid money path. The owner must decide whether a crypto account is in scope before any other candidate matters for profit.

## 1. Prior-research corrections

| # | Claim (source) | Correction | Evidence |
|---|---|---|---|
| C1 | "No untouched historical wallet data exists" (PD §7) | True for Robinhood Chain. **False for Hyperliquid.** Hydromancer Reservoir has every perp fill with wallet address, taker/maker flag, realized PnL, start position, builder, TWAP id and liquidation flags, from **2025-07-28**, updated daily. | [V] docs.hydromancer.xyz/reservoir/hyperliquid.md, schema-reference/fills.md |
| C2 | Wallet cohorts can be picked from leaderboard / indexer PnL (Gemini audit §5B, §11) | The two public indexers disagree per wallet. Over 30 days, on 121 common wallets, realized PnL disagrees **in sign for 21**, with a median absolute difference of **$41,259**. Example: Salem1299534 is +$352,823 on RHTrenches and −$915,339 on FomoPulse. Aggregate conclusions agree; per-wallet selection from either indexer is unreliable. | [V] `reconcile_indexers.py`, raw/tr_*.json |
| C3 | "fomo copy trading" mechanics | fomo.family's own page (FOMO Labs Inc., 2026-02-01) describes **notification + manual execution**, not mirroring. The auto-copy docs at `docs.onfomo.com` belong to a **different product** (a Hyperliquid perps app, "Smart Sentiment", closed beta). One 2026 review states "No copy trading features". Third-party bots exist (a "mofo bot" video). | [V] fomo.family/answers/how-does-copy-trading-work; docs.onfomo.com/llms.txt; klimentdukovski.com review |
| C4 | Fomo leaderboard PnL definition | **UNRESOLVED.** No official formula was found. Third parties say "realized", "realized + unrealized, average cost", and "net cash flow". A 2026-09-04 top-20 analysis (Foresight/KuCoin) says 80–90% of top-leader profit is unrealized. | [V] sources in §15 |
| C5 | RHTrenches "all-time" | Covers only **2026-08-27 onward** (`first_ts` 1787872060). "all" and "30d" are identical. | [V] /api/status |
| C6 | "CEX→HL lead-lag needs ~700 ms [U]" (PD T17) | Measured on one day (2026-09-01 BTC, Tardis): **Binance leads HL by ~500 ms**. Correlation of the Binance 100 ms return with the HL return 500 ms later is **0.203**, against ≤0.05 at every other lag. Public HL trade-feed delivery to a Tokyo collector: **p50 256 ms, p90 370, p99 735**. Binance: p50 3 ms. | [V] `leadlag_tardis.py` |
| C7 | Cascade kill: "real liquidation-bounce edge is sub-minute; our 4–12 s stack" (memory) | The **latency was assumed, never measured**, and the test used 1 h Binance OI proxies. HL liquidation fills now exist with ms timestamps (Reservoir `fills/perp/liquidations`). This is a *different data mechanism*, so a measurement-only recovery-path study is justified (H4). The old kill stands for its own test. | [V] Reservoir docs |
| C8 | Toxic-wallet signal is directly tradable | Top-decile HL wallet markout is **1.25–3.11 bps** (Zhai 2026). The HL base **taker fee is 4.5 bps** (maker 1.5). Copying as a taker is fee-negative before spread. | [V] arXiv 2608.04373; HL fee docs |

## 2. Source universe (inspected this session)

| Class | Sources actually inspected |
|---|---|
| Official protocol | HL docs: historical-data, info endpoint, WebSocket subscriptions, fees; trade.xyz docs: oracle-price, US equity indices; Hydromancer docs (llms.txt, reservoir, hyperliquid, tradexyz, fills schema); fomo.family answers page; docs.onfomo.com |
| Raw / historical data | Live HL `/info` (`recentTrades`, `metaAndAssetCtxs` main and `dex:"xyz"`, `fundingHistory` for 5 coins, 11 months); S3 probes of `hl-mainnet-node-data` and `hyperliquid-archive` (both requester-pays, anonymous access denied); Tardis `datasets.tardis.dev` free samples (HL + Binance BTC, 2026-09-01); RHTrenches + FomoPulse `/api/overview`, `/api/traders` at 24h/7d/30d/all |
| Academic | arXiv 2608.04373 (Zhai, identity), 2606.15715 (Barone & Lillo, TWAP), 2608.03616 (cascade branching), 2602.00776 (Binance microstructure ML), 2506.08718 (crypto price discovery), 2508.06788 (ES OFI), SSRN 6465720 (Albers et al., L4 HL dataset; page 403, abstract via search), Gao-Han-Li-Zhou JFE 2018 + Baltussen et al. JFE 2021 (intraday momentum) |
| Institutional | Man AHL, AQR trend bibliography, Cboe 0DTE paper, CME liquidity article. **Thin**: no firm publication changed any ranking (see §7). |
| Open source / engineering | Hydromancer Reservoir, Tardis.dev (HL coverage, `fastBook` from 2026-06-17), plus PD's tools lane (not repeated) |
| Practitioner | 0xArchive / Messari weekend price-discovery reports, Arrakis lead-lag thread (via search), coinmarketman provider comparison |
| Social | fomo.family leaderboards via the indexers; KuCoin/Foresight top-20 analysis; X articles (402/403, not read) |

## 3. Data assets we did not know we had access to

1. **HL `trades` with both wallets, free, live** [V]. `recentTrades` and the WS `trades` channel return `users: [buyer, seller]` on every print. A free prospective wallet-attributed tape can start at any time.
2. **Hydromancer Reservoir** (`s3://hydromancer-reservoir`, requester-pays, Parquet, region `ap-northeast-1`) [V docs]:
   - All HL perp fills from 2025-07-28, plus liquidation, ADL, TWAP and builder subsets.
   - 1 s candles.
   - **Daily position snapshots of every account**.
   - 1-minute, 20-level L2 books.
   - Trade[XYZ] from 2025-10-13.
   - Egress cost: **unquoted** [U]. It needs an AWS account and a cost check before any pull.
3. **HL official S3** (`hl-mainnet-node-data`: `node_fills_by_block`, `explorer_blocks`, `replica_cmds`, `misc_events_by_block`; `hyperliquid-archive`: L2 + `asset_ctxs`) [V]. Both are requester-pays; anonymous access returns `AccessDenied`. `replica_cmds` is the raw source for a full L4 book rebuild (the Zhai / Albers route).
4. **Tardis.dev first-of-month files, no key** [V]. HL + Binance trades download fine (6.1 MB / 27.9 MB for BTC on 2026-09-01). That gives 12+ free days per year for cross-venue replication.
5. **HIP-3 CME-analog perps with wallet IDs** [V live, 24h notional]:

   | Market | 24h notional | CME analog |
   |---|---|---|
   | `xyz:CL` | $360M | CL |
   | `xyz:SP500` | $222M | ES |
   | `xyz:XYZ100` | $215M | NQ-like index (not NQ itself) |
   | `xyz:GOLD` | $46M | GC |
   | `xyz:SILVER` | $121M | — |

   These are the Lucid instruments and the Sierra archive's instruments.

## 4. Major new market-structure findings

- **Identity carries short-horizon information on HL** [V paper]:
  - Toxicity rank persists across 10-day windows (ρ = 0.52).
  - Identity features raise 1 s out-of-sample R² from 10.88% to 12.31% (t = 9.2).
  - The effect replicated on a December 2025 sample.
  - It survives 200–300 ms feature delays.
  - No net-of-cost strategy was tested.
- **Visible TWAPs** [V paper]:
  - They pay about 9 bps less temporary impact than hidden metaorders, and leave 3.3–5.5 bps less permanent impact.
  - They are trend-following: +18.2 bps in the 30 minutes before start.
  - They show "more pronounced post-trade decay".
  - Hidden flow trading beside a same-side TWAP pays more adverse selection.
- **The trade.xyz index oracle is anchored to CME futures quotes 23/5.** When CME is closed it uses a 30-minute EMA of impact prices [V docs]. So during CME hours, HL index perps should follow ES/NQ, not lead them [I].
- **Weekend HL prices barely beat Friday's close as a CME-open forecast** [V secondary]: 50.7% of 191 observations, with a median improvement of 0.4 bps.
- **The public HL feed is ~0.25 s behind block time even from Tokyo** [V]. Any HL signal that decays within ~1 s is unreachable without a node or a paid stream. Hydromancer claims 135 ms vs 280 ms native [U, vendor claim].

## 5. Hyperliquid deep dive

**What can be reconstructed:**

| Item | Live | Historical | Source |
|---|---|---|---|
| Global trades with buyer and seller | free WS/REST | Reservoir fills (per-side rows) from 2025-07-28; `node_fills_by_block` | [V] |
| Maker vs taker | `crossed` in userFills | `crossed` column | [V] |
| userFills / orderUpdates / openOrders / clearinghouseState | per user; `userFillsByTime` last 10,000 fills only | fills: Reservoir; orders: `replica_cmds` only | [V] |
| Liquidations | `userEvents` per user; Hydromancer `liquidationFills` (paid) | Reservoir `liquidations/`, with `liquidation_mark_px` | [V] |
| TWAP states / slice fills | per user (`twapStates`); all active TWAPs via Hydromancer `perpTwapSnapshot` (paid) | Reservoir `twap_fills/` (`twap_id`) | [V] |
| BBO / L2 | free WS (20 levels) | Reservoir 1-minute 20-level; HL archive L2; Tardis | [V] |
| Asset contexts, funding, OI | free | `asset_ctxs` (HL S3); `fundingHistory` free | [V] |
| All positions | — | Reservoir daily snapshots | [V] |
| Full L4 book | Hydromancer L4 (paid) | rebuild from `replica_cmds` (requester-pays) | [V] |

**Answer to "positive forward markout, not historical PnL?":** yes. The fills schema supports per-wallet signed markouts at 100 ms–5 min, split by coin, maker/taker, size, `start_position` (flip vs add), builder and liquidation status. Discovery can run on 2025-08→2025-12 with a completely later test on 2026-01→2026-09.

**What is NOT yet done:** replication. Zhai's economic ceiling (≤3.1 bps top ventile) is already below taker cost. Real value would come from one of:
- (a) longer-horizon persistence (minutes to hours) that Zhai did not target;
- (b) maker-side use (skewing quotes, avoiding toxic fills);
- (c) cross-asset transfer (H2).

## 6. Fomo / Robinhood reconciliation

| Window (RHTrenches, 147 wallets) | Realized | Unrealized (marked) | Winners / losers |
|---|---|---|---|
| 24h | −$695,382 | +$299.4M | 15 / 40 |
| 7d | −$4,212,140 | +$299.4M | 25 / 78 |
| 30d (= all, since 08-27) | −$17,468,230 | +$299.4M | 15 / 111 |

- **FomoPulse** (294 wallets, frozen since 09-05): 30d realized −$11,601,185; winners/losers 48/216. The total matches PD's −$11.60M.
- **What the evidence explains:**
  - App-visible "PnL" is dominated by marks on illiquid pools. PD found that capping at 50% of pool liquidity turns $408M of marked value into $27.0M.
  - Realized cash outcomes are negative across windows and across both indexers.
  - Per-wallet numbers depend on the indexer (C2), e.g. on unknown cost basis for positions opened before an indexer's start date [I].
- **Not done:** app-side capture of Fomo's own number for the same wallet and window (needs the owner's logged-in app; the API refuses non-browser clients per PD); and a raw-chain cashflow audit per wallet.
- **Copy mechanism:** official copy is manual, so there is **no platform speed advantage and no batching** to exploit or suffer [V official page]. Follower slippage was measured by PD's replay: median entry drift 0 at d = 1–150 blocks.
- **Verdict on the Gemini report:** its headline stands. Its per-wallet cohort selection does not.

## 7. Institutional research findings

No institutional publication inspected produced a testable mechanism beyond the academic ones. Man AHL and AQR material was fund-marketing or classic trend bibliography. That is **not proof of absence**: the search was shallow and many PDFs returned 403.

Usable inputs:
- Cboe's 0DTE paper (gamma hedging and intraday dynamics).
- Baltussen et al. (hedging-demand intraday momentum; now flat in the 0DTE era per a 2022–2026 retest, and Heimdall's own test failed).
- CME's "beyond order-book depth" article (context only).

This lane stays open (§13).

## 8. Paper ledger (strongest, reproducible)

| Paper | Date | Market / sample | Signal | Reported effect | Costs? | OOS? | Our data? | Post-publication period available? | Status |
|---|---|---|---|---|---|---|---|---|---|
| Zhai, *Public Trader Identity* (2608.04373) | 2026-08 | HL, Jul 2026 (+ Dec 2025 replication) | wallet toxicity (10-day frozen) | top decile 1.25→2.11 bps (0.5 s→10 s); 1 s R² +13.2% | No | frozen-window + second sample | Yes (Reservoir) | Aug–Sep 2026 only; **Aug 2025–Jun 2026 unseen by the paper** | REPLICATE (H1) |
| Barone & Lillo, *Sunshine or Shade* (2606.15715) | 2026-06 | HL 201 perps, 2025-07-28→2026-03-23 | visible TWAP vs hidden metaorders | −8.9 bps temporary, −3.3 to −5.5 bps permanent; more post-trade decay | No | No | Yes (`twap_fills`) | **2026-03-24→now** | REPLICATE (H3) |
| Garcia Seuma, cascade branching (2608.03616) | 2026-08 | HL fills + Binance, 7 cascades | branching ratio | subcritical (0.03–0.28); no early warning | n/a | n/a | Yes | n/a | CONTEXT (H4) |
| Bieganowski & Ślepaczuk (2602.00776) | 2026-01 | Binance perps, 2022→2025-10 | OFI / spread / VWAP-dev ML, 3 s | taker net 0.13–7.0%/yr; makers hit on 2025-10-10 | Yes | walk-forward | Partly (Tardis) | Yes | KILL for us (3 s horizon, latency) |
| Albers et al., *An Open Book* (SSRN 6465720) | 2026 | HL L4 | dataset | — | — | — | route to L4 | — | DATA REFERENCE |
| Gao et al. JFE 2018 / Baltussen JFE 2021 | 2018/2021 | SPY / 60 futures | first→last half hour | — | — | — | yes | yes; flat 2022–26 (retest) and failed in our test | DEAD |

## 9. Second-order hypotheses (from mechanisms)

- **Retail takers lose; who takes the other side?** HL fills carry `builder` (front-end) and `crossed`. The winners are then measurable as maker wallets, HLP, and non-builder flow. Heimdall could identify builder-routed flow as uninformed and lean against it only as a maker, and maker fees are 1.5 bps at base tier [I].
- **Informed wallets on B move price on A:** H2. Do HL wallets that are toxic on `xyz:SP500`/`xyz:XYZ100` predict MES/MNQ at 1–15 minutes, a horizon Lucid can execute?
- **Visible TWAP completion leads to decay:** fade after completion (H3). Minutes horizon, latency-tolerant.
- **Forced liquidation leads to a recovery path:** measure the post-liquidation-cluster path from true fills (H4).
- **Alpha fails net of costs, so can execution be the edge?** Binance leads HL by ~500 ms. For any future HL execution, that is a free adverse-selection filter: never rest or take against a stale HL price while Binance has already moved (H5).
- **Leaderboard herding predicts reversal:** already tested by PD (followers vs return ρ = 0.003); no signal.

## 10. Hypothesis funnel (this phase; PD's T1–T35 unchanged unless noted)

| ID | Hypothesis | State | Reason |
|---|---|---|---|
| X1 | Copy toxic HL wallets as taker | KILLED | Markout 1–3 bps < 4.5 bps taker fee (C8) |
| X2 | Select wallets from indexer / leaderboard PnL | KILLED | Indexer sign disagreement 21/121 (C2) |
| X3 | Weekend HIP-3 price predicts CME open, then trade the open | KILLED | 50.7% hit, 0.4 bps (secondary); and nothing to trade before the open |
| X4 | 3 s microstructure ML (Binance) | KILLED for us | 0.13–7%/yr net; sub-second latency required |
| X5 | onfomo "copy trading" as the fomo mechanism | KILLED (wrong product) | C3 |
| X6 | HL index-perp vs CME carry (funding) | WATCH | `xyz:SP500` −1.65% annualized mean, 43.9% negative; `xyz:GOLD` +8.56% steady; `xyz:CL` −17.3% mean, swinging +27%→−80%. Likely term-structure compensation; not prop-compatible |
| X7 | ES order-book imbalance / queue | WATCH-BLOCKED | Needs MBO; literature: effects dissipate within ~1 s, below costs |
| H1 | HL wallet-identity flow, longer horizons / maker-side | SURVIVING (untested) | Replicable on unseen period |
| H2 | HL CME-analog wallet flow → MES/MNQ minutes | SURVIVING (untested) | Only Lucid-reachable candidate |
| H3 | Post-visible-TWAP decay | SURVIVING (untested) | Paper supports decay; magnitude unknown |
| H4 | HL liquidation-cluster recovery path | SURVIVING (measurement only) | Reopened on new data (C7) |
| H5 | Binance-lead adverse-selection filter | SURVIVING (execution) | Measured ~500 ms lead, one day |

PD's T13 (long-tail carry) and T22 (Polymarket maker) remain its top items. **Neither is displaced or confirmed by this phase.**

## 11. Top 5 (not reduced to 3)

**H2 — HIP-3 index-perp wallet flow → MES/MNQ**
- **Mechanism:** some HL participants trade `xyz:SP500`/`xyz:XYZ100` with information, or with persistent impact that ES has not absorbed at minute scale.
- **Who pays:** uninformed MES/MNQ counterparties at 1–15 minutes.
- **Data:**
  - Reservoir `by_dex/xyz/fills` from 2025-10-13.
  - Databento MES/MNQ/ES 1m to 2026-06-30 [A].
  - Sierra 90-day archive to 2026-09-21 [A].
- **Evidence for:** Zhai shows identity information persists on HL.
- **Evidence against:**
  - The oracle is CME-anchored.
  - HL notional is a tiny fraction of ES.
  - HL makers hedge on CME, so HL most likely follows [I].
- **OOS path:** score wallets Oct–Dec 2025, test Jan–Jun 2026 on Databento, then Jul–Sep 2026 on Sierra.
- **Execution:** Lucid, minute horizon; latency is tolerable.
- **Frictions:** $1 round turn plus slippage per memory (~$3.50 round turn on MES).
- **Capacity:** small; fine for 1–4 micros.
- **Cheapest falsification:** per-wallet ES 5-minute signed markout. If the top-decile holdout markout is < 1 MES tick net, kill.

**H1 — HL wallet-identity flow (replication + extension)**
- **Mechanism:** informed or fast wallets.
- **Who pays:** stale makers and uninformed takers.
- **Data:** Reservoir fills.
- **Evidence for:** Zhai (ρ = 0.52, replicated).
- **Evidence against:** tiny magnitude, fees, wallet rotation.
- **OOS path:** discovery Aug–Oct 2025, test Jan–Sep 2026 (never used by the paper except July).
- **Execution:** crypto account (Track B/C); maker-side only.
- **Frictions:** 1.5 bps maker, 4.5 bps taker.
- **Capacity:** moderate for maker.
- **Cheapest falsification:** does top-decile markout at 1–30 minutes exceed 6 bps round-trip? If not, only the maker-side filter remains.

**H3 — Post-visible-TWAP decay**
- **Mechanism:** transient impact from pre-announced flow reverts after completion.
- **Who pays:** the TWAP issuer's residual impact; liquidity that chased the tilt.
- **Data:** Reservoir `twap_fills` + 1 s candles.
- **Evidence for:** Barone & Lillo report stronger post-trade decay.
- **Evidence against:** permanent-impact differences are only 3–5 bps; the event-level reversal is unknown.
- **OOS path:** 2026-03-24 onward (after the paper's sample).
- **Execution:** crypto account, minutes horizon.
- **Frictions:** ~9–12 bps round trip as taker.
- **Capacity:** limited by the TWAP set.
- **Cheapest falsification:** post-completion mean reversion for TWAPs above the 90th percentile of notional/ADV. If < 12 bps at 5–60 minutes, kill.

**H4 — Liquidation-cluster recovery**
- **Mechanism:** forced flow overshoots.
- **Who pays:** liquidated traders.
- **Data:** Reservoir liquidations + 1 s candles.
- **Evidence for:** forced selling is concentrated (87.8% in 30 minutes, Oct 2025 case).
- **Evidence against:** the memory kill; the 2025-10-10 maker losses.
- **OOS path:** clusters after 2026-03.
- **Execution:** crypto account.
- **Frictions:** high during stress.
- **Capacity:** event-limited.
- **Cheapest falsification:** net recovery at 1–30 minutes vs a random-time baseline.

**H5 — Binance-lead execution filter**
- **Mechanism:** HL prints lag Binance by ~0.5 s.
- **Who pays:** it avoids adverse selection rather than earning.
- **Data:** Tardis free days.
- **Evidence for:** one day.
- **Evidence against:** one day only; our host may be ~0.25–1 s behind anyway.
- **OOS path:** 12 monthly days.
- **Execution:** only if an HL lane exists.
- **Frictions:** none added.
- **Capacity:** n/a.
- **Cheapest falsification:** is the lead stable across months and BTC/ETH/SOL?

## 12. What the Profit Discovery program missed

1. Hyperliquid historical wallet data (Reservoir; official node S3). PD searched Robinhood Chain wallet history only.
2. HIP-3 CME-analog markets: the only bridge from wallet data to Lucid.
3. Zhai 2026. The literature shows **markout persistence** exists on HL, just too small for taker copy.
4. Free Tardis samples, which make a $0 lead-lag measurement possible (turning its T17 [U] into a measured number).
5. fomo.family vs onfomo product identity, and indexer per-wallet disagreement.

## 13. Search saturation receipt

- **Pass 1 (adjacent mechanisms): 0DTE gamma / ES intraday.**
  - Result: practitioner claims only. The Cboe paper exists; no 2025–26 academic evidence of a net edge.
  - Intraday momentum is flat in the 0DTE era, and Heimdall's own test is dead.
  - **Did not change the top 5.**
- **Pass 2 (market-maker view): ES order-book imbalance / queue.**
  - Result: effects dissipate within ~1 s (2508.06788); needs MBO data.
  - HL maker economics are covered by H1/H5.
  - **Did not change the top 5.**
- **Pass 3 (data that could change the ranking).**
  - Result: **Tardis free samples (new)** and **HIP-3 CME-analog markets (new)**. The second *did* change the set: H2 entered as a new challenger.
  - Per the stop rule, research continues. Hence the STATUS.

**Still open:**
- the Reservoir cost quote;
- the institutional sweep (PDF access);
- the Fomo app-side capture;
- the Albers L4 methodology (SSRN 403).

## 14. Recommended next 3 experiments (by expected information value; not implemented)

1. **E1 — Reservoir cost quote + bounded pull.**
   - Needs owner approval of an AWS account; quote before any pull, per the standing rule.
   - Pull scope: fills for `hyperliquid` (BTC/ETH/SOL) and `xyz` (SP500, XYZ100), 2025-08→2026-09.
   - What it resolves: H2 and H1 together, with a frozen discovery/test split. It is the only experiment that can put a Lucid-executable signal on the table.
2. **E2 — Event studies on Reservoir `twap_fills` and `liquidations`** (same pull), for H3 and H4. Pre-register kill thresholds (§11) before looking at outcomes.
3. **E3 — $0 Tardis replication.**
   - Lead-lag and delivery latency on 12 first-of-month days, BTC/ETH/SOL.
   - Plus a one-hour live latency probe **from Heimdall's own host**.
   - This settles the unmeasured "4–12 s stack" claim behind C7.

A free prospective HL wallet-tape recorder (WS `trades`) is also worth starting as a data asset. It is listed, not implemented.

## 15. Evidence receipts

**Commands / scripts:**
- `workspace/external_intel_2026-09-23/leadlag_tardis.py` (2026/09/01):
  - HL 360,024 trades; Binance 3,602,361.
  - Delivery p50: HL 255.6 ms, Binance 3.1 ms.
  - Argmax lag +500 ms, correlation 0.203.
- `workspace/external_intel_2026-09-23/reconcile_indexers.py` + `raw/tr_*.json`, `raw/ov_*.json` (captured 2026-09-23).
- `raw/funding_*.json`: HL `fundingHistory` for `xyz:SP500` (n = 4,519, from 2026-03-18), `xyz:XYZ100` (8,264), `xyz:CL` (6,222), `xyz:GOLD` (6,582), `BTC` (8,277, mean +5.67% annualized).
- `curl https://hl-mainnet-node-data.s3.amazonaws.com/?list-type=2` returned "Anonymous users cannot invoke requests against Requester Pays buckets". `hyperliquid-archive` returned the same.
- HL `recentTrades` BTC sample: `"users": ["0x66f8…75a9", "0xba08…985c"]`, px 86,200.

**URLs:**
- https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
- …/for-developers/api/info-endpoint
- …/websocket/subscriptions
- …/trading/fees
- https://docs.hydromancer.xyz/reservoir.md
- …/reservoir/hyperliquid.md
- …/reservoir/tradexyz.md
- …/reservoir/schema-reference/fills.md
- https://docs.trade.xyz/perpetuals/mechanics/oracle-price.md
- …/markets/equity-indices/us.md
- https://arxiv.org/html/2608.04373
- https://arxiv.org/abs/2606.15715 (+ html v1)
- https://arxiv.org/html/2608.03616
- https://arxiv.org/html/2602.00776v1
- https://arxiv.org/abs/2506.08718
- https://arxiv.org/html/2508.06788
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6465720
- https://datasets.tardis.dev/v1/hyperliquid/trades/2026/09/01/BTC.csv.gz
- https://docs.tardis.dev/historical-data-details/hyperliquid
- https://0xarchive.io/blog/hyperliquid-weekend-price-discovery-in-24-7-markets
- https://messari.io/report/weekend-trading-evidence-of-price-discovery-in-hyperliquid-s-weekend-markets
- https://fomo.family/answers/how-does-copy-trading-work
- https://docs.onfomo.com/llms.txt
- https://klimentdukovski.com/articles/fomo-app-review/
- https://www.kucoin.com/news/flash/analysis-of-top-20-fomo-profit-leaders-reveals-key-investment-strategies
- https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0
- https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf
- https://rhtrenches.com/api/{status,overview,traders}
- https://fomopulse.app/api/{overview,traders}
