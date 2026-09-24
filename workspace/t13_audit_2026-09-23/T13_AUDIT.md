# T13 AUDIT — HL long-tail funding carry, delta-hedged on Binance (2026-09-23)

Scope: research/audit only. No funding levels, carry returns, spread stats or PnL computed over 2024-10..2026-08.
Only metadata (listing/delisting timestamps, interval gaps with rate values discarded), docs, today's snapshots.
Scripts + raw outputs in this folder: probe1.py..probe6b.py, hl_metaAndAssetCtxs.json, bn_exchangeInfo.json,
bn_fundingInfo.json, hl_spotMeta.json, bn_spot_trading.json, top60_hedge_map.json, hl_universe_dates.json,
bn_interval_history.json, depth_snapshot.json.

## VERDICT: REVISE-SPEC (leaning REJECT as currently specified)

The spec as written ("short HL perp where HL funding is high, long Binance perp") is **mechanically the killed
HL-vs-Binance funding SPREAD family on a different asset list**. The perp-perp hedge pays Binance funding, so PnL = HL
funding − Binance funding, which is family (2). The ~11% "HL floor" is the same 0.01%/8h interest term Binance also
charges, so it cancels in a perp-perp hedge. The discovery evidence is further contaminated by new-listing effects
(USELESS HL listed 2026-09-08, PONS 2026-08-31), so it is mostly not a persistent-carry signal. Both are defects in the
spec. Neither refutes the idea. Also, the proposed discovery window cannot be traded for most of the named coins
because no Binance hedge existed yet.

## Item table

| # | Item | Finding | Evidence | Label |
|---|---|---|---|---|
| 1 | Distinctness | Perp-perp hedge ⇒ payoff = HL_fund − BN_fund = family (2). Differences: asset universe (long-tail), not payer/mechanism. HL floor 0.00125%/h and BN interest 0.01%/8h are both 10.95% APR and cancel. Spot hedge (HL spot or BN spot) would be a different mechanism (outright carry = family (1) on alts, fee-dominated). | HL funding doc; BN funding FAQ; hl ctx `funding`=0.0000125 for BTC/ETH/PURR/VVV today | VERIFIED (formulas); INFERRED (family equivalence) |
| 2 | PIT universe | `meta.universe` fields: name, szDecimals, maxLeverage, marginTableId, isDelisted, onlyIsolated, marginMode. No listing-date field. Listing proxy = first `fundingHistory` row (startTime=0). Delist proxy = last 1d `candleSnapshot`. Universe = 234 perps, 56 delisted, 178 live. Alive counts: 2024-10-01: 135; 2025-04-01: 170; 2025-10-01: 177; 2026-04-01: 190; 2026-08-31: 177. 74 of the 178 live coins were listed after 2024-10-01. Earliest funding row is 2023-05-12, so coins listed before that are left-censored. Relisted names (XMR first row 2026-01-15) need a manual check. HIP-3 dex perps are not included. | probe1/probe6 → hl_universe_dates.json | VERIFIED (counts); INFERRED (proxies) |
| 2b | Delisted history | fundingHistory for delisted coins (JELLY, MATIC, FTM, YZY) is still retrievable. **Trap:** they keep printing `fundingRate "0.0"` hourly rows after delisting (to 2026-09-22), with empty l2Book and no candles. Using isDelisted alone would inject fake zero-funding hours. Last-candle dates: JELLY 2025-03-26, YZY 2026-05-05, MATIC 2024-09-09. REQ and OM have no candles. | probe3/probe4 | VERIFIED |
| 3 | Delisted/survivorship | 44 of the 56 delisted perps were delisted inside 2024-10..2026-08. A today-universe test drops all of them, including the squeeze/settlement names (JELLY) where the short-carry loss would sit. | hl_universe_dates.json | VERIFIED (count); INFERRED (bias direction) |
| 4 | Hedge availability | Top-60 by OI: 4 have no BN perp (kPEPE, CASHCAT, PURR, kBONK; kPEPE/kBONK probably map to 1000PEPE/1000BONK, mapping unresolved). 21 of the 60 had their BN perp onboard after 2024-10-01. 6 were onboarded after 2025-10-01 (LIT, PONS, MON, GRAM, CHIP, MEGA). Named coins: USELESS BN 2025-08-15, VVV 2025-01-29, GRASS 2024-11-08, PONS 2026-09-06 (after the holdout), XMR 2020, PURR none. BN spot missing for XMR, VVV, PONS, GRASS, USELESS, SPX, FARTCOIN. PURR has HL spot only (same venue, no cross-venue hedge). | top60_hedge_map.json (exchangeInfo onboardDate) | VERIFIED |
| 5 | Normalization | HL pays hourly. F = avgPremium + clamp(0.00125%/h − P, ±0.05%). Cap 4%/h. BN fundingInfo today: 469 symbols at 4h, 319 at 8h, 3 at 1h. Caps are ±2% for new alts and ±0.3% for BTC. Since 2025-05-02 BN moves an interval to 1h after a cap/floor hit. Since 2026-01-02 it reverts to 4h after 16 calm hourly cycles. fundingInfo shows only the current interval, so history must come from fundingTime gaps (done: GRASS/VVV/USELESS/FARTCOIN are 4h from onboard, XMR 8h). Each has one 8h gap at 2026-06-24 04:00→12:00, a missing settlement rather than an interval change. Normalize each BN print by its own realized gap to the previous print, spread over the following hours as announced/accrued. Do not forward-fill the rate. | bn_fundingInfo.json; bn_interval_history.json; BN FAQ | VERIFIED (current + gaps); INFERRED (method) |
| 6 | Fees | HL base tier: 0.045% taker / 0.015% maker, rolling 14-day volume, staking discounts up to 40%. No change-dates in the docs. BN USD-M VIP0: 0.05% / 0.02%, 10% off with BNB. The official page rendered "No records found" in the fetch, so this rate comes from third-party sources. 4 taker legs ≈ 2×4.5 + 2×5.0 = **19 bps of notional per round trip**, before spread and impact (HL alt spreads today are 0.1–25 bps). | HL fees doc; BN page failed; finder.com | HL VERIFIED; BN UNVERIFIED (3rd-party) |
| 7 | Legging | Two venues and two APIs, with no atomic cross-venue fill. HL L1 fills and BN matching are independent. On thin books (bid10 < $500 for USELESS/GRASS/PURR today) a marketable HL short will partially fill. Needs: HL-first IOC with a size cap, hedge only the filled qty on BN, max unhedged notional and time limits, and a kill path that flattens the filled leg if the hedge rejects (BN min notional/lot, reduce-only, 1h-interval/cap states). | design inference | INFERRED |
| 8 | Basis | HL oracle = stake-weighted median of validators' weighted median of Binance/OKX/Bybit/Kraken/Kucoin/Gate/MEXC/HL spot (3,2,2,1,1,1,1,1). Coins with primary spot on HL (PURR/HYPE-type) exclude external sources until liquid. Mark = median(oracle+150s EMA basis, HL book median, CEX perp mids 3/2/2/1/1). Long-tail HL premium today reaches 10–20 bps (USELESS premium 0.00197). Basis moves on entry and exit are a first-order cost. | HL oracle + robust-price docs; hl ctx `premium` | VERIFIED (docs/snapshot) |
| 9 | Margin/liq/ADL | 88 of 178 live HL perps have maxLeverage 3 and 56 have 5. All six named alts are 3x except XMR (5x). Maintenance = half the initial margin at max leverage, so 16.7% at 3x. Only 8 onlyIsolated perps, all delisted. ADL triggers on negative account value and ranks by (mark/entry)·(notional/equity). Cross ADL first fired 2025-10-11 and can close ONE leg of a hedge. At 2x on each leg a $10k hedged position locks ~$5k on HL + ~$5k on BN = $10k capital (1x gross on capital). At 1.5x it locks ~$13.3k. A short-squeeze of +33% liquidates a 3x HL short, and the BN long gain sits on another venue with no cross-margin. | hl meta marginTables; HL liquidation/margin/ADL docs; WuBlockchain | VERIFIED (params); INFERRED (lockup) |
| 10 | Capacity | Snapshot (2026-09-23): HL bid depth (the short-entry side) within 50 bps: USELESS ~$19–29k, GRASS ~$3k (finest levels) / ~$116k (4-sig aggregation), VVV $15–154k, XMR $28–237k, PONS $47–102k, PURR <$1k. BN ask50: USELESS $70k, GRASS $115k, VVV $78k, XMR $250k, PONS $63k. HL l2Book returns only 20 levels, so wide bands need nSigFigs aggregation (approximate). Practical hedged size is roughly **$5–25k per name per entry at ≤~20 bps impact**. Total across 5–10 names is low six figures at most. | depth_snapshot.json | VERIFIED (snapshot); INFERRED (capacity) |
| 11 | Squeeze/tail | JELLY (2025-03-26): squeeze pushed a short onto HLP, validators delisted and settled at $0.0095. XPL hyperp (2025-08): +200% in minutes, ~$46M of shorts liquidated, HL added a 10x mark cap. POPCAT (2025-11): manipulation left $4.9M of HLP bad debt. 2025-10-11: first cross-margin ADL. The persistent high-funding long-tail coins are exactly where crowded longs, thin books and squeezes coincide, so the short-HL leg carries these tails. Discretionary validator settlement adds a non-modelable venue tail. | CoinDesk JELLY; HL community incident doc; The Block/crypto.news XPL; CoinDesk/Halborn POPCAT; WuBlockchain ADL | VERIFIED (reported by sources) |
| 12 | Survivorship | Three biases stack. (a) Universe: today's list drops 44 in-window delistings. (b) Selection: the discovery ranking uses funding observed in 2026-09, and 2 of the top-6 were listed ≤3 weeks earlier (listing-premium effect). (c) Hedge: requiring a BN perp *today* admits coins whose hedge didn't exist in-window. All three bias carry upward. | items 2–4 | VERIFIED (facts); INFERRED (direction) |

## Adversarial distinctness argument
- Same payer class (leveraged longs on HL), same formula family, same hedge venue, same PnL identity as the killed spread.
  The only new ingredient is a universe of thinner, newer, more squeezable coins.
- Prior: the BTC spread decayed ~7x as capital arrived. Long-tail spreads should decay even faster, because capacity
  is tiny (item 10), the trade is easy to copy, and new listings cause episodic spikes that fade (USELESS/PONS).
  Expected persistence per coin is low. Any edge would come from rotation onto new listings, and that drags in
  new-listing basis, 3x leverage and squeeze risk.
- The "11.6% floor" is not edge. Both venues charge the same 10.95% APR interest term, so a perp-perp hedge nets
  ~0 of it. Only a spot hedge captures it, and that is family (1) carry, which fees killed.

## Required spec changes (if the idea continues)
1. Restate the target as **HL−BN per-hour funding SPREAD on alts**. Explicitly inherit the family-(2) kill criteria
   (decay check per 6-month bucket, ≥70% one-signed, net of the 19 bps plus spread and impact per round trip).
2. Build a PIT universe: HL alive = first_funding ≤ t < last_candle (not isDelisted). Drop the post-delist 0.0 rows.
   Relisted names need manual review.
3. Hedge eligibility at t: BN perp onboardDate ≤ t − buffer (e.g. 7d) and status TRADING at t. No-hedge coins are
   excluded, not proxied. Most of the named coins drop out of the discovery window.
4. Exclude the first N days after an HL or BN listing (for example 30d) as a pre-registered rule, and report with
   and without it.
5. BN normalization: divide each print by its realized interval, taken from the fundingTime gap. Flag missing
   settlements (2026-06-24). Model interval switches to 1h under cap.
6. Costs: 4 taker legs at 19 bps plus measured half-spread plus impact at the chosen size, taken from depth
   snapshots (and later a recorded L2 feed). Charge an entry/exit basis penalty (HL premium).
7. Tail model: squeeze scenarios (+33%/+100%/+200% in under 10 min), forced settlement or delisting at an adverse
   price, single-leg ADL. Margin at ≤2x per leg. Capacity cap per name ≤ $10–25k.
8. Windows: the discovery window 2024-10..2025-09 has few hedgeable long-tail coins. Pre-register a minimum-coin
   count per month, or the test is underpowered (compare the carry holdout n_trades=0 failure).
9. The HEIMDALL mandate is prop-account survival on CME futures (Lucid). T13 needs HL and BN accounts, collateral
   on two venues, and crypto venue risk. Flag this as out of mandate before any further spend.

## URLs read
- https://api.hyperliquid.xyz/info (metaAndAssetCtxs, spotMeta, fundingHistory, candleSnapshot, l2Book)
- https://fapi.binance.com/fapi/v1/exchangeInfo, /fapi/v1/fundingInfo, /fapi/v1/fundingRate (timestamps only), /fapi/v1/depth
- https://api.binance.com/api/v3/exchangeInfo?permissions=SPOT
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/robust-price-indices
- https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/oracle
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/auto-deleveraging
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/margin-tiers
- https://www.binance.com/en/fee/futureFee (failed to render rates)
- https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031
- Search-result sources (snippets, not full reads): finder.com/cryptocurrency/trading/binance-futures-fees;
  coindesk.com 2025/03/26 JELLY; hyperliquid-co.gitbook.io community-docs 2025-26-03_incident;
  theblock.co/post/368486; crypto.news XPLUSD; coindesk.com 2025/11/13 POPCAT; halborn.com Nov-2025;
  wublockchain.medium.com cross-margin ADL.
