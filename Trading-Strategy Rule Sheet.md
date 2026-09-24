# Trading-Strategy Rule Sheet

## (1) Scope and source-access notes

This sheet reconstructs rules from the eight supplied research reports. It is a **source-faithful rule sheet, not a summary of the videos and not trading advice**. The reports preserve four evidence tags:

- **[STATED]** — a rule or claim attributed to the source. In this sheet every [STATED] item includes the video ID, a video timestamp, and a short quote.
- **[VISUAL]** — a chart, whiteboard, indicator, or example feature reported as shown. It is not upgraded to a spoken rule.
- **[INTERPRETED]** — a conservative operational restatement that connects source components; it is not an additional source rule.
- **[MISSING]** — not supplied by the accessible evidence. No missing rule is repaired with generic ICT/SMC or trading knowledge.

The source-access situation materially differs by video. Video `DAnXM7C16h0` had a timestamped third-party transcript mirror, although the official YouTube player and captions were blocked. Video `AVVM-FyewLg` had a timestamped third-party transcript. Videos `HNuRp9Z1bMs`, `ADnslyKOwFE`, `IB-fyWI5j8w`, `SQEtBHOJW6I`, and `52ZsDmFHqyY` were primarily reconstructed from timestamped audiovisual-analysis artifacts and/or related pages; those reports explicitly warn that the quoted wording is not an independently verified verbatim transcript. Video `coBMd1vk2Lo` was inaccessible for transcript and visual content; only metadata and chapter labels were available.

Accordingly, the sheet preserves the reports' evidence status instead of normalizing confidence. A quote attributed to a non-verbatim audiovisual artifact remains tagged [STATED] only where the underlying report explicitly classified it as a spoken rule; it should be manually re-checked against the original recording before implementation. Related publisher pages are used only as cross-checks and are identified as such.

### Compact per-video coverage table

| Video ID | Strategy / setups retained separately | Source coverage | Rule-sheet consequence |
|---|---|---|---|
| `DAnXM7C16h0` | Liquidity-trap reversal: bullish sweep long and bearish sweep short | Timestamped third-party transcript; official player/captions blocked | Strongest source coverage, but swing, sweep, session, sizing, and target details remain discretionary or missing |
| `coBMd1vk2Lo` | Trader Mayne / ICT blueprint; possible breaker-block variant | YouTube metadata and chapter labels only; transcript/video inaccessible | Substantive rules, examples, and codability fields are [MISSING] |
| `HNuRp9Z1bMs` | 50% rebalance / PO3 bearish reversal and bullish mirror | Non-verbatim audiovisual analysis plus related publisher cross-check | Core PO3/50%/SMT/inversion logic retained; exact range and execution semantics remain unresolved |
| `AVVM-FyewLg` | Little Rizzy downtrend short, uptrend long, crash-bottom reversal long | Timestamped third-party transcript; video frames blocked | Geometry and discretionary context retained; formal pattern and execution details remain incomplete |
| `ADnslyKOwFE` | Bullish Trident/FVG setup; gold exception | Non-verbatim audiovisual analysis and secondary corroboration | 30-minute/NY kill-zone/FVG-doji-next-candle sequence retained; FVG, doji, stop, target, and short rules remain incomplete |
| `IB-fyWI5j8w` | MMXM/AMD sell model and bullish mirror; OTE and Silver Bullet alternatives | Non-verbatim audiovisual analysis; no official transcript/video | OTE, stop, target, break-even, risk, and session values retained as reported; definitions and precedence remain missing |
| `SQEtBHOJW6I` | No defensible single strategy; conflicting IPP, T-Rex/2 PM Silver Bullet, and generic ICT analyses | No transcript; incompatible AI passes; secondary metadata only | Do not merge the alternatives; detailed rules and examples are unverified [INTERPRETED]/[VISUAL] or [MISSING] |
| `52ZsDmFHqyY` | Small-cap short statistics: Gap-Up Short, Bounce Short, First Red Day | Non-verbatim audiovisual analysis plus related creator strategy page | Universe filters and setup families are clear; triggers, buffers, execution, exits, borrow, and risk remain incomplete |

## (2) Instruments

### `DAnXM7C16h0` — Liquidity-trap model

- **[STATED]** (DAnXM7C16h0 @ 04:04; “Whatever chart is in front of me is the chart I'm trading.”) The method is presented as applicable to whatever chart is being traded; examples include Dow futures/YM, Nasdaq futures/NQ, and EURUSD. The watch list is recommended to remain small: **[STATED]** (DAnXM7C16h0 @ 35:50; “I would cap myself out at about two three pairs on my watch list.”)
- **[STATED]** (DAnXM7C16h0 @ 12:28; “This could happen on the daily… all the way down to the one minute.”) The model is fractal from Daily/H4 through intraday charts. **[STATED]** (DAnXM7C16h0 @ 42:32; “This is usually the time frame I'm hanging out on.”) The 5-minute chart is the normal all-purpose execution view; 1-minute can provide more opportunity but more ways to be stopped. **[STATED]** (DAnXM7C16h0 @ 47:04; “more opportunity on M1 but also more opportunity to uh get slapped up.”)
- **[MISSING]** The complete instrument whitelist, broker/feed assumptions, contract specifications, and whether the same stop buffer applies across futures and FX are not stated.

### `coBMd1vk2Lo` — ICT blueprint

- **[STATED]** (coBMd1vk2Lo @ page metadata; “Forex Trading Strategy”) The title frames the subject as forex. **[STATED]** (coBMd1vk2Lo @ page description; “across both traditional markets and crypto.”) The description says the concepts apply across traditional markets and crypto.
- **[MISSING]** Exact pairs, crypto symbols, exchange/broker, futures versus spot/CFD status, and any instrument whitelist are unavailable. Chapter labels such as “Breaker block strategy” do not identify a tradable instrument.

### `HNuRp9Z1bMs` — 50% rebalance / PO3

- **[STATED]** (HNuRp9Z1bMs @ general source description; “NQ”) Nasdaq futures are the principal market. **[STATED]** (HNuRp9Z1bMs @ approximately 09:25; “I look for the divergences between the two because it shows relative weakness on a single asset.”) ES is used as the comparison market for NQ/ES SMT divergence.
- **[VISUAL]** BTCUSD/Bitcoin is reported as another example, with Ethereum used for comparison. The exact exchange, contract, and feed are [MISSING].
- **[MISSING]** The report does not establish a complete symbol list or whether the examples imply a universal market rule.

### `AVVM-FyewLg` — Little Rizzy

- **[STATED]** (AVVM-FyewLg @ 1:02:56; “no matter if you're a crypto trader… futures… forex… stock trader.”) The speaker presents the method across crypto, futures, forex, stocks, and options.
- **[STATED]** (AVVM-FyewLg @ 04:39–04:51; “I was using QQQ to chart.”) Examples include QQQ/SPX/S&P, Nasdaq/NDX, Bitcoin, HHH, silver, and gold. These are examples, not a complete universe.
- **[MISSING]** Market-specific contract, spread, borrow, and order-execution assumptions are not supplied.

### `ADnslyKOwFE` — Trident

- **[STATED]** (ADnslyKOwFE @ 10:28–12:47; reported instrument list: “USDCAD… NZDUSD… EURUSD… GBPUSD… USDJPY… XAUUSD.”) The reported examples use those FX pairs and gold. **[STATED]** (ADnslyKOwFE @ approximately 03:52; “gold and Nasdaq”/naturally bullish assets) Gold and Nasdaq/NQ are described as favored bullish instruments, although ticker naming differs across secondary sources.
- **[STATED]** (ADnslyKOwFE @ source summary, timestamp unavailable; “AUDUSD” did not work well in backtesting.) AUDUSD is reportedly avoided; the exact primary timestamp is [MISSING].
- **[MISSING]** Complete universe, market type, pip convention, broker, spread, slippage, and whether the listed pairs are exhaustive are not supplied.

### `IB-fyWI5j8w` — MMXM/OTE

- **[STATED]** (IB-fyWI5j8w @ 02:23–04:51; “Forex is the primary market.”) Forex is the principal market, with USDJPY and EURUSD shown. DXY is also mentioned.
- **[VISUAL]** The reported trade examples are a USDJPY sell and EURUSD buy. **[MISSING]** Exact watchlist, exchange/feed, permitted markets, and whether indices/crypto are allowed are not established.

### `SQEtBHOJW6I` — inaccessible/conflicting strategy identity

- **[MISSING]** The complete instrument scope is not verifiable. Secondary metadata identifies a live Nvidia trade, but that does not establish the strategy’s universe.
- **[INTERPRETED]** One non-verbatim analysis pass reported ES/NQ futures; another reported EURUSD, NAS100, XAUUSD, GBPUSD, and USDJPY. Because these conflict, neither is accepted as a source rule. The source report explicitly says not to combine them.

### `52ZsDmFHqyY` — small-cap short statistics

- **[STATED]** (52ZsDmFHqyY @ 03:39–03:51; “initial market cap” and “must be over $3.00.”) The broad screen is approximately $1M–$100M initial market cap, approximately 1M–50M float, and price above $3. **[VISUAL]** The board reportedly distinguishes roughly 1–2M low float, 2–5M mid float, and 5–10M larger small-cap float.
- **[STATED]** (52ZsDmFHqyY @ 07:16; “market cap under 200M.”) FRD candidates may use an under-$200M cap ceiling; this is an alternative/setup-specific limit rather than a resolved replacement for the global $100M board.
- **[STATED]** (52ZsDmFHqyY @ 08:06; “avoid biotech and energy.”) Biotech and energy are excluded because of unpredictable volatility/news. **[STATED]** (52ZsDmFHqyY @ 08:43; “avoid Chinese stocks.”) Chinese stocks are excluded because of halt and slippage risk.
- **[MISSING]** Borrow/locate availability, share-class treatment, exchange, halt policy, and the exhaustive universe are not supplied.

## (3) Time / session

### Liquidity-trap model — `DAnXM7C16h0`

- **[STATED]** (DAnXM7C16h0 @ 42:16; “I'm always trading with New York time. So, stock open is 9:30 a.m. for me.”) New York time and the 9:30 stock open anchor the examples. **[STATED]** (DAnXM7C16h0 @ 42:58–43:20; “Typically, I'm looking for entries after the open.”) Entries are generally sought after the open.
- **[STATED]** (DAnXM7C16h0 @ 49:26–50:00; “What you people need to understand is what happens outside of the time window is completely irrelevant to me.”) A chosen time window is treated as hard context. **[MISSING]** Its exact start/end, weekdays, DST convention, and whether it is always the NY session are absent.
- **[STATED]** (DAnXM7C16h0 @ 07:24; “I'll never enter before news… Usually typically 2 minutes, 3 minutes, 4 minutes.”) He avoids entry before scheduled news and commonly waits roughly 2–4 minutes afterward. Event tiers, blackout-before-news time, and calendar source are [MISSING].

### Trader Mayne / ICT blueprint — `coBMd1vk2Lo`

- **[STATED]** (coBMd1vk2Lo @ 18:00 page chapter; “High time frame setup”) and **[STATED]** (coBMd1vk2Lo @ 26:12 page chapter; “Low time frame execution”) identify topics, not rules.
- **[MISSING]** Chart timeframes, session, timezone, kill zones, days, news, holidays, and holding windows are all unavailable. The chapter labels cannot be converted into timing rules.

### 50% rebalance / PO3 — `HNuRp9Z1bMs`

- **[STATED]** (HNuRp9Z1bMs @ reported timing section; “09:15–11:30 EST”) The active window is reported as 09:15–11:30 EST, with a 09:30 liquidity injection and around 10:00 manipulation/reversal. **[STATED]** (HNuRp9Z1bMs @ reported PM discussion; “14:00 EST”) A PM opportunity around 14:00 is also mentioned.
- **[MISSING]** The report does not establish whether those are hard eligibility windows, whether EST means year-round ET, or whether 14:00 is a separate setup. No news filter is recovered. Example weekdays are not requirements.

### Little Rizzy — `AVVM-FyewLg`

- **[STATED]** (AVVM-FyewLg @ 1:15:06–1:15:17; “I hate the New York session open… It’s too volatile… I stay out of New York’s open.”) The speaker avoids the NY open. **[STATED]** (AVVM-FyewLg @ 1:15:09–1:15:17; “I like the London open… I like all the other opens.”) London and other opens are preferred/acceptable.
- **[STATED]** (AVVM-FyewLg @ 1:15:24–1:15:45; “there’s seasonality within the day… study it.”) Intraday seasonality should be studied. **[MISSING]** Exact timezone/clock, weekdays, holidays, and holding cutoff are not given. GDP/unemployment and headline-news cues are discussed for crash context but are not a scheduled-news filter.

### Trident — `ADnslyKOwFE`

- **[STATED]** (ADnslyKOwFE @ approximately 02:35; “London Kill Zone” and 03:00–06:30 New York time) New entries are sought in approximately 03:00–06:30 New York time. **[STATED]** (ADnslyKOwFE @ approximately 10:15; “Don't try and predict the market, just react to it.”) The timing model favors reaction, not prediction.
- **[MISSING]** DST handling, exact London-versus-New-York anchoring, weekdays, holidays, and news blackout are not specified. It is unresolved whether an FVG formed around 02:30 can be traded after 03:00.

### MMXM/OTE — `IB-fyWI5j8w`

- **[STATED]** (IB-fyWI5j8w @ general timing section; “4H minimum”) Higher-timeframe context is at least 4H, with Daily also used. **[STATED]** (IB-fyWI5j8w @ general timing section; “15-minute” and “filtering noise”) 15-minute is the preferred main execution/filter chart; 5-minute refines a Silver Bullet/FVG.
- **[STATED]** (IB-fyWI5j8w @ general timing section; “02:00–05:00 New York time”) London open window is 02:00–05:00 NY time. **[STATED]** (IB-fyWI5j8w @ general timing section; “07:00–10:00 New York time”) NY open window is 07:00–10:00. **[STATED]** (IB-fyWI5j8w @ general timing section; “10:00–12:00 New York time”) London close window is 10:00–12:00, with Consumer Confidence at 10:00 mentioned as context. **[STATED]** (IB-fyWI5j8w @ general timing section; “by 15:00 New York time”) Daily profiles often complete by 15:00.
- **[MISSING]** Weekdays, DST, exact news handling, and whether these windows are hard filters are absent.

### Conflicting/inaccessible episode — `SQEtBHOJW6I`

- **[MISSING]** Exact timing cannot be recovered. **[INTERPRETED]** Non-verbatim Pass B alleged 14:00–15:00 New York time with 5-minute context and 1-minute execution; Pass C alleged London/New York only; Pass A supplied no reliable session rule. The alternatives must remain separate and unverified.

### Small-cap short statistics — `52ZsDmFHqyY`

- **[STATED]** (52ZsDmFHqyY @ 06:19; “between 09:30 and 11:30”) GS volume/consolidation is focused on the U.S. regular-session morning. **[STATED]** (52ZsDmFHqyY @ 06:36; “cracks the bottom of its consolidation range after 11:00 AM.”) The GS weakness/entry occurs after 11:00 AM.
- **[INTERPRETED]** These clocks likely refer to U.S. Eastern time because 09:30 is the U.S. equity open, but the source does not say so. **[MISSING]** Exact timezone, weekdays, holidays, premarket boundaries, and news calendar are not supplied.

## (4) Direction / bias

### Liquidity-trap model — two mirror setups (`DAnXM7C16h0`)

The strategy separates a **bullish sweep long** from a **bearish sweep short**. Liquidity is resting orders, especially stops: **[STATED]** (DAnXM7C16h0 @ 03:55–04:16; “liquidity is just resting orders in the market… usually… stop losses.”) A high/low becomes relevant when respected and followed by a move away: **[STATED]** (DAnXM7C16h0 @ 03:34–03:55; “not every high or low is liquidity.”)

- **Long bias:** **[STATED]** (DAnXM7C16h0 @ 10:06–10:23; “Buy below lows, sell above highs.”) A bullish setup buys only after the selected low has been taken, with opposing highs/liquidity as the draw. **[STATED]** (DAnXM7C16h0 @ 24:43–25:23; “I will not buy this asset pair until this low is taken out.”)
- **Short bias:** **[STATED]** (DAnXM7C16h0 @ 25:23–25:43; “I will not look to take a sell until this high right here is taken out.”) A bearish setup sells only after the selected high is taken, with lows/liquidity below as the draw.
- **Internal/external orientation:** **[STATED]** (DAnXM7C16h0 @ 28:20–28:48; “I'm taking entries off internal liquidity… targeting external.”) Higher-timeframe target logic must be present; a sweep by itself is not sufficient. **[STATED]** (DAnXM7C16h0 @ 31:34–31:51; “I need to make sure I'm targeting liquidity.”)
- **[MISSING]** Swing-selection, displacement, conflicting higher-timeframe bias, and minimum reaction rules are not fixed.

### 50% rebalance / PO3 — `HNuRp9Z1bMs`

- **[STATED]** (HNuRp9Z1bMs @ approximately 01:21; “I always want to see price rebalance into 50% of the range and then continue with the trend.”) Bias is organized around a selected dealing range and 50% rebalance.
- **[STATED]** (HNuRp9Z1bMs @ reported top-down section; “Daily… H4… H1”) Daily sets broad context, H4 checks the range/PO3, H1 checks the same behavior and reversal area, and intraday execution follows alignment.
- **[INTERPRETED]** Bearish means a range, run above a meaningful high, rejection back inside, and move toward 50%; bullish is the mirror below a low. The report states that the exact long wording is incomplete. **[MISSING]** Exact range endpoints and alignment tolerance.

### Little Rizzy — `AVVM-FyewLg`

- **[STATED]** (AVVM-FyewLg @ 15:04–15:18; “it’s really important to establish a overall trend for the market… the daily SPX is in a uptrend.”) Establish broader trend first.
- **[STATED]** (AVVM-FyewLg @ 1:13:19–1:14:13; “if we’re at a low point… prefer a buy”; “if we’re at highs… we want to be selling”) Location affects whether a pattern is used for long or short.
- **[INTERPRETED]** Downtrend continuation, uptrend continuation, and crash-bottom reversal are separate setups; no single trendline projection should be treated as both a continuation and reversal signal without the stated context.

### Trident — `ADnslyKOwFE`

- **[STATED]** (ADnslyKOwFE @ approximately 03:52; “long-biased”) The approach is long-biased, with gold/Nasdaq described as naturally bullish. **[STATED]** (ADnslyKOwFE @ approximately 13:51; “above the 200 EMA”) For longs, price above the 200 EMA is preferred.
- **[INTERPRETED]** The evidence supports a bullish setup, not a complete symmetric short system. **[MISSING]** No short trigger, short stop, or short target is available.

### MMXM/OTE — `IB-fyWI5j8w`

- **[STATED]** (IB-fyWI5j8w @ 02:23–04:51; “HTF bias”) Setups should align with higher-timeframe bias; a bearish MMXM sell is favored only when HTF is bearish. **[INTERPRETED]** Bias is a supplied/manual state unless a separate, source-approved swing classifier is added. The bullish mirror is inferred from the EURUSD example; exact long wording is [MISSING].

### `coBMd1vk2Lo` and `SQEtBHOJW6I`

- **[MISSING]** `coBMd1vk2Lo` has no accessible bias procedure. `SQEtBHOJW6I` has no reliable bias procedure; trend/BOS/CHoCH statements are only [INTERPRETED] outputs of incompatible non-verbatim analyses and cannot be merged.

### Small-cap short statistics — `52ZsDmFHqyY`

- **[STATED]** (52ZsDmFHqyY @ 06:55; “fails to make a higher high and finally closes red.”) The global bias is overwhelmingly short after an extended move loses momentum.
- **[STATED]** (52ZsDmFHqyY @ 03:16; “98 99% short.”) The speaker is described as approximately 98–99% short. This is a preference, not a complete long-side model. **[MISSING]** No long setup is described.

## (5) Entry setup in exact order

### Strategy A — Liquidity-trap bullish long (`DAnXM7C16h0`)

1. **Select a respected low and observe the move away.** **[STATED]** (DAnXM7C16h0 @ 13:03–14:00; “not every high or low is liquidity.”) The low must be contextually respected and followed by movement away; the exact swing algorithm is [MISSING].
2. **Establish higher-timeframe direction and an opposing target.** **[STATED]** (DAnXM7C16h0 @ 11:20–11:54; “I'm always targeting liquidity and taking an entry after liquidity is taken.”) A low sweep without a logical target is not enough.
3. **Allow the inducement/trap sequence.** **[STATED]** (DAnXM7C16h0 @ 18:40; “wait again for this to form… this trap move to the downside.”) Do not buy the apparent retail pullback before the sweep.
4. **Wait for price to trade below the selected low.** **[STATED]** (DAnXM7C16h0 @ 24:43–25:23; “I will not buy this asset pair until this low is taken out.”) This is the hard trigger.
5. **Buy after the low is taken.** **[STATED]** (DAnXM7C16h0 @ 06:17–06:32; “taking an entry after liquidity is taken.”) A confirming lower-timeframe reaction/close can be used to add confidence but is not established as universal.
6. **Protect below the invalidating low.** **[STATED]** (DAnXM7C16h0 @ 16:54–17:10; “stop loss below the low.”) Futures examples use one or two ticks, but exact low/buffer semantics are [MISSING].
7. **Target opposing highs/liquidity.** **[STATED]** (DAnXM7C16h0 @ 31:34–31:51; “targeting liquidity.”) Internal liquidity may be a partial and external liquidity the larger objective.

### Strategy B — Liquidity-trap bearish short (`DAnXM7C16h0`)

1. Select a respected high, observe the move away, and establish bearish higher-timeframe logic. **[STATED]** (DAnXM7C16h0 @ 02:58–03:34; “this high… is going to be liquidity.”)
2. Identify a logical low/liquidity target. **[STATED]** (DAnXM7C16h0 @ 31:34–31:51; “I need to make sure I'm targeting liquidity.”)
3. Wait for the trap/inducement sequence; do not short the apparent retail break before the high sweep. **[STATED]** (DAnXM7C16h0 @ 08:19–10:23; “sell above highs.”)
4. Wait for price to trade above the selected high. **[STATED]** (DAnXM7C16h0 @ 25:23–25:43; “I will not look to take a sell until this high right here is taken out.”)
5. Sell after the high is taken, normally at market. **[STATED]** (DAnXM7C16h0 @ 46:33–47:09; “I just market execute… as soon as the high is spiked out.”)
6. Place the stop above the swept/left-side high. **[STATED]** (DAnXM7C16h0 @ 31:19; “stop loss above that high.”)
7. Target opposing lows/liquidity. **[STATED]** (DAnXM7C16h0 @ 46:16–47:27; “target” the lows below.)

### Strategy C — Trader Mayne / ICT blueprint (`coBMd1vk2Lo`)

- **[MISSING]** The exact first condition, order of conditions, timeframe hierarchy, long/short separation, breaker variant, expiry, reset, and trigger semantics are unavailable. Chapter labels are not enough to construct a sequence.

### Strategy D — 50% rebalance / PO3 bearish reversal (`HNuRp9Z1bMs`)

1. Use NQ with ES as comparison and identify the Daily/H4/H1 range/PO3 context. **[STATED]** (HNuRp9Z1bMs @ 02:23–04:51; “Daily… H4… H1.”)
2. Mark the selected range midpoint. **[STATED]** (HNuRp9Z1bMs @ approximately 01:21; “rebalance into 50% of the range.”) Exact endpoints are [MISSING].
3. Require top-down alignment. **[STATED]** (HNuRp9Z1bMs @ reported alignment section; “all three higher timeframes should align.”) Tolerance and override logic are [MISSING].
4. Wait for the session context where applicable. **[STATED]** (HNuRp9Z1bMs @ reported timing section; “09:15–11:30 EST.”) The hard/soft nature of the window is [MISSING].
5. Wait for manipulation above a meaningful high. **[STATED]** (HNuRp9Z1bMs @ reported sweep section; “trading above a prior high.”) Reference-high and wick/close criterion are [MISSING].
6. Require bearish SMT: NQ makes a new high while ES fails to make a corresponding high. **[STATED]** (HNuRp9Z1bMs @ approximately 09:25; “NQ makes a new high while ES fails to make a new high.”)
7. Require rejection back into the range/change of delivery. **[STATED]** (HNuRp9Z1bMs @ reported inversion section; “change of state of delivery.”) Close/touch/break semantics are [MISSING].
8. Require a prior FVG to invert from support to resistance. **[STATED]** (HNuRp9Z1bMs @ reported inversion section; “a prior fair value gap… should have acted as support but is traded through and then acts as resistance.”)
9. Choose one of the reported entry alternatives: limit on inversion-zone retap or sell stop beyond structural confirmation. **[STATED]** (HNuRp9Z1bMs @ reported entry section; “place a limit order on a ‘re-tap’… or… a sell stop.”)
10. Place the stop at/above manipulation or SMT high. **[STATED]** (HNuRp9Z1bMs @ reported stop section; “just above the SMT high.”)
11. Target the 50% midpoint/base hit. **[STATED]** (HNuRp9Z1bMs @ reported target section; “50% midpoint.”)
12. Move to break-even after intended-direction confirmation and favor the base hit over holding the whole move. **[STATED]** (HNuRp9Z1bMs @ approximately 15:11; “You either need to be right or right out.”)

### Strategy E — 50% rebalance / PO3 bullish mirror (`HNuRp9Z1bMs`)

- **[INTERPRETED]** The faithful mirror is: aligned higher-timeframe range/PO3; manipulation below a meaningful low; bullish SMT if confirmed; rejection back inside; resistance-to-support inversion; limit retap or buy stop; stop below the manipulation low; target 50%. The report explicitly says the detailed long wording is incomplete. **[MISSING]** Exact long example, SMT wording, fib/range anchors, and management are not available.

### Strategy F — Little Rizzy downtrend continuation short (`AVVM-FyewLg`)

1. Establish a downtrend. **[STATED]** (AVVM-FyewLg @ 15:04–15:18; “establish a overall trend.”)
2. Wait for a drop and bounce/pullback. **[STATED]** (AVVM-FyewLg @ 15:36–15:52; “we start dropping… wait for the bounce.”)
3. Draw/recognize a descending trendline. **[STATED]** (AVVM-FyewLg @ 15:36–15:52; “see if it’s forming a trend line down.”) Candle/pivot/touch criteria are [MISSING].
4. Prefer the first one or two patterns; treat fourth/fifth as fatigue/lower quality. **[STATED]** (AVVM-FyewLg @ 14:25–14:39; “the first one or two… work the best… fourth… fifth… market’s getting tired.”)
5. Identify the lowest-low candle and measure vertically to the descending trendline. **[STATED]** (AVVM-FyewLg @ 08:54–09:34; “find the low on the candle that has the lowest low… measure… to the top of the trend line.”)
6. Project that distance below the low. **[STATED]** (AVVM-FyewLg @ 13:13–13:21; “expecting is a $20 move below… below the low.”)
7. Enter when the pattern/confirmation is judged adequate; a later 5-minute example uses a close below the Bollinger middle/range. **[STATED]** (AVVM-FyewLg @ 1:11:34–1:11:45; “close below the… mid-range of the Bollinger… you’d enter.”)
8. Stop slightly above the relevant high/trendline area. **[STATED]** (AVVM-FyewLg @ 1:09:48–1:10:05; “stop… right above the high of this candle.”)
9. Exit if the trendline breaks, with a preference for actual close confirmation. **[STATED]** (AVVM-FyewLg @ 29:08–29:47; “I very much kind of like to wait for like an actual close.”)
10. Apply a maximum loss. **[STATED]** (AVVM-FyewLg @ 29:47–30:07; “always apply a max loss to all of your trades.”)

### Strategy G — Little Rizzy uptrend continuation long (`AVVM-FyewLg`)

1. Apply the pattern in reverse in an uptrend. **[STATED]** (AVVM-FyewLg @ 05:40–05:56; “the same inverse pattern works.”)
2. Measure from the highest-high candle to the trendline and project the same distance above the high. **[STATED]** (AVVM-FyewLg @ 23:57–24:22; “measure the distance… the height it’s going to go on the next move.”)
3. Prefer lower/discounted location rather than buying at a high. **[STATED]** (AVVM-FyewLg @ 1:13:19–1:14:13; “if we’re at a low point… prefer a buy.”)
4. **[MISSING]** Ordinary long entry trigger, stop, and exact confirmation are not specified; only the geometry and context are stated.

### Strategy H — Little Rizzy crash-bottom reversal long (`AVVM-FyewLg`)

1. Use the downtrend projection as a possible bottom/long zone. **[STATED]** (AVVM-FyewLg @ 33:21–35:26; the projection “gave you the bottom of the crash.”)
2. Either buy near the projected level, accepting that it may be early, or wait for confirmation. **[STATED]** (AVVM-FyewLg @ 35:26–35:45; “you could… buy here… usually a little early.”)
3. Confirmation alternative: wait for a candle close above the middle Bollinger line/reality. **[STATED]** (AVVM-FyewLg @ 35:45–36:01; “wait until you get a candle that closes above reality… entry.”)
4. Add broader fundamentals/support/50% Fibonacci context if used. **[STATED]** (AVVM-FyewLg @ 52:35–53:06; “50% retracement… support… bottom’s in.”)
5. If invalidated, watch for the inverse/uptrend pattern. **[STATED]** (AVVM-FyewLg @ 53:12–53:38; “it did not work… invalidated… watch for… inverse direction.”)
6. **[MISSING]** Fixed stop, timeframe, size, and scaling are absent.

### Strategy I — Trident bullish setup (`ADnslyKOwFE`)

1. Restrict new setup consideration to the 03:00–06:30 New York Kill Zone. **[STATED]** (ADnslyKOwFE @ approximately 02:35; “This setup means nothing without the time.”)
2. Use 30-minute execution/pattern identification and Daily context/management. **[STATED]** (ADnslyKOwFE @ approximately 02:58; “30-minute chart.”) **[STATED]** (ADnslyKOwFE @ approximately 03:52; “daily chart.”)
3. Prefer bullish context: price above 200 EMA and 5/9/13/21 EMA stacking. **[STATED]** (ADnslyKOwFE @ approximately 05:14; “5, 9, 13, and 21 EMAs.”) **[STATED]** (ADnslyKOwFE @ approximately 06:08; “intertwining.”) Cross/intertwining is low probability and should be ignored, but numerical stack order is [MISSING].
4. Require a bullish FVG near/during the window. **[STATED]** (ADnslyKOwFE @ approximately 06:58; “bullish FVG.”) FVG geometry, age, and expiry are [MISSING].
5. Wait for a doji-like candle whose wick passes through the FVG 50%/consequent-encroachment level. **[STATED]** (ADnslyKOwFE @ approximately 06:58–17:08; “wicks through” the FVG 50% level.) Doji threshold and midpoint convention are [MISSING].
6. Require the immediately following candle to close below the doji high. **[STATED]** (ADnslyKOwFE @ approximately 07:35; “If it closes above the high [of the Doji], I'll invalidate the trade.”)
7. Enter after confirmation. **[INTERPRETED]** The safest ordering is after the confirming candle closes; exact order type and fill price are [MISSING].
8. Use a long stop below the setup/doji/key candle low for FX; gold uses close-based invalidation instead of a hard stop. **[STATED]** (ADnslyKOwFE @ approximately 10:28; “below the low of the entry candle setup.”) **[STATED]** (ADnslyKOwFE @ approximately 01:07/13:18; “liquidity wicks” and no hard stop for gold.)
9. Seek approximately 1:20 or greater opportunity and ride trend until weakness. **[STATED]** (ADnslyKOwFE @ approximately 11:13/14:45; “1:20+ RR.”) **[STATED]** (ADnslyKOwFE @ approximately 11:13/14:45; exit on “EMA crossing/change or a large bearish candle.”)

### Strategy J — MMXM/OTE bearish sell (`IB-fyWI5j8w`)

1. Establish HTF bias and location at a 4H/Daily key level, such as PDH/PDL, PWH/PWL, HTF FVG, OB, breaker, or mitigation block. **[STATED]** (IB-fyWI5j8w @ 02:23–04:51; “where liquidity rests.”) The formal definitions are [MISSING].
2. Identify accumulation, illustrated by the Asian range. **[VISUAL]** (IB-fyWI5j8w @ 04:52–09:23; “Asian range (Accumulation).”)
3. Wait for manipulation above the Asian high/PDH or into the HTF key level. **[STATED]** (IB-fyWI5j8w @ general sell-model analysis; “runs above the PDH.”) Wick/close/reclaim criteria are [MISSING].
4. Identify SMR/reversal peak. **[STATED]** (IB-fyWI5j8w @ general sell-model analysis; “Smart Money Reversal (SMR).”) Swing algorithm is [MISSING].
5. Require displacement/clean break below the relevant swing low. **[STATED]** (IB-fyWI5j8w @ 11:50–14:43; “clean break” and “displacement.”) Minimum body/close thresholds are [MISSING].
6. Draw fib from reversal high to displacement low. **[VISUAL]** (IB-fyWI5j8w @ 26:28–29:25; OTE drawing). Exact wick/body anchors are [MISSING].
7. Enter in 0.62/0.705/0.79 OTE, with 0.705 primary. **[STATED]** (IB-fyWI5j8w @ 26:28–29:25; “0.62, 0.705 (Primary OTE), and 0.79.”)
8. If the first break is weak/wicky, wait for a later 5-minute FVG/Silver Bullet entry inside the 15-minute leg. **[STATED]** (IB-fyWI5j8w @ 11:50–14:43; “If the first break lacks displacement (is ‘wicky’), wait for a second retracement.”)
9. Stop at 1.0, with optional 0.90 refinement after confirmed displacement. **[STATED]** (IB-fyWI5j8w @ 26:28–29:25; “0.90 (90%) level” and “1.0 (100%) level.”)
10. Target original accumulation low; use -0.28/-0.62 extensions only with strong momentum. **[STATED]** (IB-fyWI5j8w @ general target section; “original accumulation low.”) **[STATED]** (IB-fyWI5j8w @ general target section; “-0.28 and -0.62.”)
11. Move stop to break-even after a displaced close beyond 0.20. **[STATED]** (IB-fyWI5j8w @ general risk section; “close below the 0.20 (20%) Fibonacci level with displacement.”)
12. Add only after the initial trade is at break-even; the second Silver Bullet entry may risk an additional 1%. **[STATED]** (IB-fyWI5j8w @ 18:28–22:42; “If a trade is at BE.”)

### Strategy K — MMXM/OTE bullish mirror (`IB-fyWI5j8w`)

- **[VISUAL]** (IB-fyWI5j8w @ reported EURUSD example; “swept PDL… displaced through a swing high.”) The bullish example is HTF FVG context, PDL sweep, SMR, bullish displacement, and retracement into breaker/OTE or 5-minute Silver Bullet. **[INTERPRETED]** The mirror is a bullish low sweep followed by high break, OTE/Silver Bullet retracement, and target toward buy-side liquidity. **[MISSING]** Exact bullish fib anchors, stop, entry precedence, and target are not supplied.

### Strategy L — Conflicting episode (`SQEtBHOJW6I`)

- **[MISSING]** No exact sequence can be selected. **[INTERPRETED—CONFLICTING]** Candidate sequences are (a) BOS/CHoCH → failed countertrend candle → IPP retest; (b) draw on liquidity/IRL→ERL → MSS/displacement → FVG retest; and (c) HTF POI → sweep → lower-timeframe CHoCH → OB/FVG. They must remain alternatives, not a hybrid.

### Strategy M — Gap-Up Short (`52ZsDmFHqyY`)

1. Screen the small-cap universe, including price >$3 and the cap/float filters. **[STATED]** (52ZsDmFHqyY @ 03:39–03:51; “must be over $3.00.”)
2. Require a large morning gap, reported broadly as 70%–1000% and more strictly as >100% on the related page. **[STATED]** (52ZsDmFHqyY @ 04:36; “gaps up 70%–1000%.”) The two thresholds are retained as an unresolved alternative.
3. Reject/avoid a same-day setup if premarket volume exceeds 50M shares. **[STATED]** (52ZsDmFHqyY @ 05:37–06:05; “pre-market volume exceeds 50 million.”)
4. Wait for the opening push and mass consolidation during the high-volume morning. **[STATED]** (52ZsDmFHqyY @ 06:19–06:36; “mass consolidation.”)
5. Wait for volume to dry and price to crack the consolidation bottom after 11:00. **[STATED]** (52ZsDmFHqyY @ 06:36; “cracks the bottom of its consolidation range after 11:00 AM.”)
6. Short on that breakdown/weakness. **[INTERPRETED]** A close below the consolidation low is a conservative proxy, not a source rule. Exact trigger and order type are [MISSING].
7. Stop above the consolidation high. **[STATED]** (52ZsDmFHqyY @ 17:40; “above the high of the consolidation range.”)
8. Treat 26% average fade as descriptive expectation, not an automatic target. **[STATED]** (52ZsDmFHqyY @ 18:19; “average expected fade is 26%.”)

### Strategy N — Bounce Short (`52ZsDmFHqyY`)

1. On approximately a one-year chart, identify a prior massive-volume failed move and resistance area. **[STATED]** (52ZsDmFHqyY @ 03:00; “1-year chart level.”)
2. Quantify the trapped block as trapped volume × resistance price, ideally approximately $150M+. **[STATED]** (52ZsDmFHqyY @ 06:35/09:34; “trapped volume times resistance price.”)
3. Wait for price to return months later toward the old area, with current demand materially lower than old trapped supply. **[STATED]** (52ZsDmFHqyY @ 04:31–05:10; “original holders sell to break even.”)
4. Resolve the reported volume ratio before coding; the source reports both “10:1 ratio” and a conflicting direction/example. **[STATED]** (52ZsDmFHqyY @ 08:35; “10:1 ratio.”) **[MISSING]** Numerator/denominator, zone width, and overshoot are unresolved.
5. Size near historical resistance. **[STATED]** (52ZsDmFHqyY @ 09:55; “size in near the historical consolidation/resistance level.”)
6. Stop above historical resistance. **[STATED]** (52ZsDmFHqyY @ 08:39; “above the historical resistance level.”)
7. Treat 75% or 50% fade figures as scenario expectations, not fixed exits. **[STATED]** (52ZsDmFHqyY @ 12:12; “75% retracement” and “50% fade.”)

### Strategy O — First Red Day (`52ZsDmFHqyY`)

1. Require at least three consecutive green days with increasing volume. **[STATED]** (52ZsDmFHqyY @ 07:30–09:03; “at least 3 consecutive green days with increasing volume.”)
2. Require approximately 300%+ range over three days or 1000%+ over two days. **[STATED]** (52ZsDmFHqyY @ 08:12; “300%+ over three days” and “1000%+ over two days.”)
3. Use the under-$200M FRD cap alternative. **[STATED]** (52ZsDmFHqyY @ 07:16; “market cap under 200M.”)
4. Wait for failure to make a higher high and the first red close/weakness. **[STATED]** (52ZsDmFHqyY @ 06:55; “fails to make a higher high and finally closes red.”)
5. Enter a one-quarter starter on the first red-day close/fakeout. **[STATED]** (52ZsDmFHqyY @ 13:42; “1/4 starter position.”) Exact intraday/close semantics are [MISSING].
6. Add the remaining three-quarters on the following day if the morning bounce fails to clear the prior high. **[STATED]** (52ZsDmFHqyY @ 13:51/15:01; “morning bounce fails to clear the prior high.”)
7. Stop above the highest consolidation point of the run. **[STATED]** (52ZsDmFHqyY @ 14:14; “highest consolidation point of the run.”)

## (6) Liquidity rules

### Explicit liquidity model

- **`DAnXM7C16h0`:** Liquidity means resting orders/stops near highs and lows. **[STATED]** (DAnXM7C16h0 @ 03:55–04:16; “resting orders… usually… stop losses.”) Equal/relative-equal highs/lows qualify as liquidity. **[STATED]** (DAnXM7C16h0 @ 41:40–41:57; “an area of liquidity.”) A respected swing that moves away implies stops on the opposite side. **[INTERPRETED]** The required operational event is a trade beyond the selected swing, followed by reversal-direction execution. **[MISSING]** Minimum penetration, wick-versus-close, close-back-inside, pivot lookback, and expiry.
- **`HNuRp9Z1bMs`:** Manipulation is a run above a meaningful high for shorts or below a meaningful low for longs. **[STATED]** (HNuRp9Z1bMs @ reported sweep section; “trading above a prior high.”) A sweep is conservatively interpreted as breach plus rejection back inside; minimum excursion and close rule are [MISSING]. SMT is a comparison filter, not a standalone entry.
- **`IB-fyWI5j8w`:** PDH/PDL/PWH/PWL and HTF FVG/OB/breaker/mitigation areas are reported places “where liquidity rests.” **[STATED]** (IB-fyWI5j8w @ 02:23–04:51; “where liquidity rests.”) The Asian range is the illustrated accumulation pool. **[MISSING]** Formal stop-order definition, sweep penetration, and reclaim.
- **`52ZsDmFHqyY`:** The framework uses float, volume, trapped holders, and volume-at-price rather than ICT liquidity. **[MISSING]** No high/low sweep, equal-high/low, or resting-stop definition is stated.
- **`coBMd1vk2Lo`, `AVVM-FyewLg`, `ADnslyKOwFE`, `SQEtBHOJW6I`:** The requested formal liquidity/sweep definitions are [MISSING]. Terms appearing in inaccessible or conflicting analyses must not be imported.

## (7) FVG / IFVG / order-block / structure rules

### Rules actually supported

- **`DAnXM7C16h0`:** FVGs, order blocks, BOS, breakers, and similar retail POIs are discussed as possible inducement areas, not required entry definitions. **[STATED]** (DAnXM7C16h0 @ 05:10–05:26; “retail labels such as BOS, breaker, order block, and FVG can be the areas used to induce liquidity.”) The speaker says he does not refine the area to an imbalance. **[STATED]** (DAnXM7C16h0 @ 08:14–08:32; “I don't like to refine it too much… It's unnecessary in my opinion.”) **[MISSING]** Formal FVG/IFVG/OB geometry, validity, mitigation, breaker conversion, and structure algorithm.
- **`HNuRp9Z1bMs`:** A prior FVG can become an inversion zone when support is traded through and then acts as resistance, or vice versa. **[STATED]** (HNuRp9Z1bMs @ reported inversion section; “a prior fair value gap… should have acted as support but is traded through and then acts as resistance.”) **[MISSING]** Three-candle FVG definition, wick/body boundaries, minimum size, fill, expiry, and exact inversion-zone boundaries. No order-block or BOS rule is recovered.
- **`IB-fyWI5j8w`:** HTF FVGs, 5-minute FVG, OB, breaker, and mitigation blocks are named as levels or alternatives. **[STATED]** (IB-fyWI5j8w @ general analysis; “5m FVG.”) **[MISSING]** Formal construction and validity for all of them; no IFVG rule.
- **`ADnslyKOwFE`:** The setup requires a bullish FVG and its 50% interaction, but the source does not define the three-candle geometry. **[STATED]** (ADnslyKOwFE @ approximately 06:58/17:08; “FVG’s 50% level” and “consequent encroachment.”) **[MISSING]** FVG boundaries, size, expiry, fill, IFVG, OB, breaker, and market structure.
- **`coBMd1vk2Lo`:** Chapter labels mention “Breaker block strategy,” but all construction, failure, retest, and validity rules are [MISSING].
- **`AVVM-FyewLg`:** No ICT/SMC definitions are supplied. A host mention of lower-timeframe BOS is not adopted as a rule. **[VISUAL]** (AVVM-FyewLg @ 1:18:18–1:18:34; host mentions a lower-timeframe “break of structure.”) **[MISSING]** FVG/IFVG/OB/breaker/liquidity definitions.
- **`SQEtBHOJW6I`:** The three incompatible analysis passes refer to IPP, FVG, OB, breaker, MSS, BOS, and CHoCH, but no reliable source rule is available. **[MISSING]** All formal definitions and validity rules.
- **`52ZsDmFHqyY`:** The small-cap framework does not use FVG/IFVG/order-block rules. **[MISSING]** Liquidity sweep and ICT structure concepts are absent.

## (8) Entry execution

- **Liquidity-trap model:** Market execution is preferred. **[STATED]** (DAnXM7C16h0 @ 46:33–46:51; “I personally don't use limits too much… I just market execute.”) A breach is generally treated as the trigger, not a required closing candle. **[STATED]** (DAnXM7C16h0 @ 46:51–47:09; “as soon as the high is spiked out.”) **[MISSING]** Exact touch/tick/close/reclaim rule, spread, slippage, chase limit, and pending-order expiry.
- **PO3/50%:** Limit on inversion-zone retap or stop beyond structural confirmation are both stated. **[STATED]** (HNuRp9Z1bMs @ reported entry section; “limit order on a ‘re-tap’… or… sell stop.”) **[MISSING]** Which is preferred, precise zone price, close/touch semantics, partial fills, and cancellation.
- **Little Rizzy:** Entry can be discretionary after the drop/bounce/trendline, with a later close below the Bollinger middle used in one example. **[STATED]** (AVVM-FyewLg @ 15:36–15:52; “I might go short here.”) **[MISSING]** Order type, exact price, confirmation and chase rules.
- **Trident:** Entry follows the immediate post-doji confirmation, but order type and price are missing. **[MISSING]** Market/limit/stop, confirmation close versus next open, slippage, and maximum chase.
- **MMXM/OTE:** Entry is retracement into OTE 0.62/0.705/0.79 or a 5-minute FVG/Silver Bullet alternative. **[STATED]** (IB-fyWI5j8w @ 26:28–29:25; “0.62, 0.705 (Primary OTE), and 0.79.”) **[MISSING]** Touch/close, order type, fib anchor, expiry, and OTE-versus-Silver-Bullet precedence.
- **Small-cap shorts:** GS shorts after consolidation breakdown, BS near historical resistance, FRD starter/add sequence. **[MISSING]** Order type, exact bar/timeframe, borrow/locate, fill, partial entry, chase distance, and halt handling.
- **`coBMd1vk2Lo` and `SQEtBHOJW6I`:** [MISSING] No defensible execution rule.

## (9) Long stop loss

- **Liquidity-trap long (`DAnXM7C16h0`):** below the swept/relevant left-side low. **[STATED]** (DAnXM7C16h0 @ 16:54–17:10; “stop loss below the low.”) Futures examples use one or two ticks beyond the level. **[STATED]** (DAnXM7C16h0 @ 09:07; “a tick or two above the high,” stated for the mirrored short.) **[INTERPRETED]** The long mirror is one/two ticks below in the futures example. FX buffer is larger because of spread/feed differences. **[MISSING]** Exact pip/tick, wick/body, slippage, and maximum distance.
- **PO3 long (`HNuRp9Z1bMs`):** at/just below the manipulation/SMT low. **[STATED]** (HNuRp9Z1bMs @ reported stop section; “just below the SMT low.”) Exact candle, buffer, and wick/body choice [MISSING].
- **Little Rizzy uptrend long:** [MISSING] Ordinary continuation-long stop is not supplied. Crash-bottom long stop is also [MISSING].
- **Trident FX long:** below setup/entry/doji/key candle low, reported around 10 pips or 8.4 pips in USDCAD example. **[STATED]** (ADnslyKOwFE @ approximately 10:28; “below the low of the entry candle setup.”) The doji-versus-confirmation candle reference conflicts and buffer is missing.
- **Trident gold long:** no hard stop; close-based invalidation below an unspecified key level. **[STATED]** (ADnslyKOwFE @ approximately 01:07/13:18; “liquidity wicks”; “does not use a hard stop.”) Key level, emergency stop, and maximum loss [MISSING].
- **MMXM/OTE long:** use 1.0/100% or optional 0.90/90% fib stop variants. **[STATED]** (IB-fyWI5j8w @ 26:28–29:25; “0.90 (90%) level” and “1.0 (100%) level.”) Bullish anchor semantics [MISSING].
- **`coBMd1vk2Lo`, `SQEtBHOJW6I`, `52ZsDmFHqyY`:** [MISSING] No reliable long stop rule; `52ZsDmFHqyY` has no long setup.

## (10) Short stop loss

- **Liquidity-trap short (`DAnXM7C16h0`):** above the swept/relevant left-side high. **[STATED]** (DAnXM7C16h0 @ 31:19; “stop loss above that high.”) One or two ticks above is a futures example. **[STATED]** (DAnXM7C16h0 @ 09:07; “a tick or two above the high.”) FX buffer is larger but unspecified. **[MISSING]** Exact buffer, wick/body, spread, and maximum risk.
- **PO3 short (`HNuRp9Z1bMs`):** at/just above the manipulation/SMT high. **[STATED]** (HNuRp9Z1bMs @ reported stop section; “just above the SMT high.”) Candle and buffer [MISSING].
- **Little Rizzy short (`AVVM-FyewLg`):** slightly above the relevant high/trendline area. **[STATED]** (AVVM-FyewLg @ 1:09:48–1:10:05; “right above the high of this candle.”) There is a conflicting earlier transcript phrase, “below the low here,” at 29:08–29:29. It is preserved under contradictions rather than repaired.
- **Trident short:** [MISSING] No complete short setup or short stop is available.
- **MMXM/OTE short:** 1.0/100% initial or 0.90/90% refined stop after displacement. **[STATED]** (IB-fyWI5j8w @ 26:28–29:25; “90% level” and “100% stop loss.”) Exact fib anchor and optionality [MISSING].
- **Small-cap GS/BS/FRD:** above consolidation high, historical resistance, or highest run-consolidation point. **[STATED]** (52ZsDmFHqyY @ 17:40; “above the high of the consolidation range.”) **[STATED]** (52ZsDmFHqyY @ 08:39; “above the historical resistance level.”) **[STATED]** (52ZsDmFHqyY @ 14:14; “highest consolidation point of the run.”) Buffer, candle, hard/close stop, and movement are [MISSING].
- **`coBMd1vk2Lo`, `SQEtBHOJW6I`:** [MISSING] No reliable short stop.

## (11) Targets / trade management

### Liquidity-trap model

- Opposing liquidity is the primary target. **[STATED]** (DAnXM7C16h0 @ 11:20–11:37; “I'm always targeting liquidity.”) Internal partial and external higher-timeframe target are both possible. **[STATED]** (DAnXM7C16h0 @ 46:51–47:43; “internal” versus “external” target.)
- Fixed arbitrary R targets are rejected. **[STATED]** (DAnXM7C16h0 @ 33:20–34:10; “random… RR point.”) Partials vary: not favored in one explanation, commonly 50%, or 70% when highly confident in YM example. **[STATED]** (DAnXM7C16h0 @ 32:08–33:20; “usually takes 50%, or 70% when very confident.”)
- Trail behind a newly protected swing and do not generally move to break-even until a partial/most of the trade is closed. **[STATED]** (DAnXM7C16h0 @ 32:41–33:20; “this low should not be revisited.”) He prefers to be out before NY lunch but does not replace the chart target with a fixed time target. **[STATED]** (DAnXM7C16h0 @ 46:16–47:22; “I do want to be out of this before this lunch hour occurs ideally.”)
- **[MISSING]** Exact partial percentage hierarchy, trailing distance, target priority, and time-stop rule.

### PO3 / 50% rebalance

- Target the 50% midpoint/base hit. **[STATED]** (HNuRp9Z1bMs @ approximately 02:42; “I don't need a big move. I just need to grab that base hit.”) Extensions are optional/bonus. **[STATED]** (HNuRp9Z1bMs @ reported target section; “continuation beyond it is a bonus.”)
- Move stop to break-even after intended-direction confirmation. **[STATED]** (HNuRp9Z1bMs @ approximately 14:15; “The moment that I can claw this [risk] back is a win for me... I'm very fond of break-even trades.”)
- **[MISSING]** Exact confirmation candle/timeframe, partials, runner, target-range endpoints, and time exit.

### Little Rizzy

- Target the equal measured move; do not automatically exit at a Bollinger edge. **[STATED]** (AVVM-FyewLg @ 24:49–25:19; “I would play the whole move.”)
- Exit/invalidate on trendline break, with actual close preferred. **[STATED]** (AVVM-FyewLg @ 14:02–14:17; “if you start getting closes above this trend line… little rizzy broke.”)
- Let winners run until projected pattern completes. **[STATED]** (AVVM-FyewLg @ 1:19:28–1:20:19; “the trades I let run make most of my money.”)
- **[MISSING]** Partials, break-even, trailing, time-stop, and daily management.

### Trident

- Seek at least approximately 1:20 opportunity, but the target is not shown as a fixed 20R limit. **[STATED]** (ADnslyKOwFE @ approximately 11:13/14:45; “1:20+ RR.”)
- Ride until EMA change/crossing, large bearish candle, or other weakness. **[STATED]** (ADnslyKOwFE @ approximately 11:13/14:45; “EMA crossing/change or a large bearish candle.”)
- **[MISSING]** Exact target, scale-out, break-even, trailing, and time/weekend exit. The 1:20, 1:51 career example, and reported 175R USDCAD example are not reconciled into one fixed exit.

### MMXM/OTE

- Initial target is original accumulation low; extensions are -0.28/-0.62 with strong momentum. **[STATED]** (IB-fyWI5j8w @ general target section; “original accumulation low.”) **[STATED]** (IB-fyWI5j8w @ general target section; “-0.28 and -0.62.”)
- Break-even after displaced close beyond 0.20. **[STATED]** (IB-fyWI5j8w @ general target section; “close below the 0.20 (20%) Fibonacci level with displacement.”)
- Add only when first position is at BE; an extra 1% may be risked. **[STATED]** (IB-fyWI5j8w @ 18:28–22:42; “additional 1%.”)
- **[MISSING]** Partial schedules, extension threshold, fees/spread in BE, and time exit.

### Small-cap shorts

- GS average expected fade is 26% from intraday high. **[STATED]** (52ZsDmFHqyY @ 18:19; “average expected fade is 26%.”)
- BS expected fade is approximately 75% if price gaps directly into resistance and approximately 50% if it builds volume from the bottom. **[STATED]** (52ZsDmFHqyY @ 12:12; “75% retracement” and “50% fade.”)
- FRD is a large continuation unwind after first red confirmation. **[VISUAL]** (52ZsDmFHqyY @ 06:13–07:32; chart shows a multi-day advance, red confirmation, and decline.) **[MISSING]** Fixed targets, partial covers, trailing, time stops, end-of-day cover, and halt policy.

### `coBMd1vk2Lo` and `SQEtBHOJW6I`

- **[MISSING]** Targets and management are not recoverable. Conflicting AI outputs for `SQEtBHOJW6I` must not be merged.

## (12) Risk / sizing

- **`DAnXM7C16h0`:** **[MISSING]** No fixed percentage, dollar risk, account formula, daily loss limit, max concurrent positions, or trade-count limit. Five micros initially and three added in an NQ example are visual examples, not a formula. **[VISUAL]** (DAnXM7C16h0 @ 25:28/31:28; “five micros”; “add another three contracts.”)
- **`HNuRp9Z1bMs`:** A one-contract NQ example is reported as 381 ticks/$1,905. **[VISUAL]** (HNuRp9Z1bMs @ reported trade example; “381 ticks… approximately $1,905.”) **[MISSING]** No risk percentage, sizing formula, daily loss, or maximum exposure.
- **`AVVM-FyewLg`:** Apply a maximum loss. **[STATED]** (AVVM-FyewLg @ 29:47–30:07; “always apply a max loss to all of your trades.”) **[MISSING]** The amount, percentage, size formula, and daily limits.
- **`ADnslyKOwFE`:** A career result is reported as $51,000 on $1,000 risk/1:51 RR. **[STATED]** (ADnslyKOwFE @ approximately 00:05/08:00; “$51,000 on $1,000 risk.”) **[MISSING]** No fixed percentage, size formula, daily loss, or gold sizing rule. No

- **`IB-fyWI5j8w`:** Typical risk is 1%–1.5% per trade. **[STATED]** (IB-fyWI5j8w @ general risk section; “1% to 1.5%.”) A second entry after BE may risk an additional 1%. **[STATED]** (IB-fyWI5j8w @ general risk section; “additional 1%.”) **[MISSING]** Equity basis, sizing formula, leverage, daily cap, and maximum simultaneous risk.
- **`52ZsDmFHqyY`:** Position size should not exceed 10% of daily float or 1% of daily volume. **[STATED]** (52ZsDmFHqyY @ 13:14; “do not exceed 10% of the daily float or 1% of the daily volume.”) FRD uses a 25% starter plus 75% conditional add. **[STATED]** (52ZsDmFHqyY @ 13:42–13:51; “1/4 starter position.”) **[MISSING]** Account-risk percentage, dollar loss, leverage, borrow costs, and daily loss limit.
- **`ADnslyKOwFE`:** A reported $51,000 on $1,000 risk is an outcome example, not a sizing formula. **[STATED]** (ADnslyKOwFE @ approximately 00:05/08:00; “$51,000 on $1,000 risk.”) **[MISSING]** Fixed percentage/dollar risk, simultaneous exposure, and gold sizing are not supplied.
- **`coBMd1vk2Lo` and `SQEtBHOJW6I`:** [MISSING] No defensible risk or sizing rule. For `SQEtBHOJW6I`, alleged 1% risk/two-loss limits come only from an unverified analysis pass and are not accepted as stated source rules.

## (13) Filters

### `DAnXM7C16h0` — liquidity-trap filters

- **News:** avoid entry before scheduled news and generally wait 2–4 minutes afterward. **[STATED]** (DAnXM7C16h0 @ 07:24; “I'll never enter before news… Usually typically 2 minutes, 3 minutes, 4 minutes.”)
- **Session:** trade only the chosen time window; exact boundaries are missing. **[STATED]** (DAnXM7C16h0 @ 49:26–50:00; “what happens outside of the time window is completely irrelevant to me.”)
- **Liquidity completion:** no trade until the relevant high/low is formed and taken. **[STATED]** (DAnXM7C16h0 @ 36:52–37:15; “won't be selling until these highs are taken.”)
- **Higher-timeframe logic:** require a logical target and bias rather than a random sweep. **[STATED]** (DAnXM7C16h0 @ 31:34–31:51; “I need to make sure there's logic.”)
- **Chop:** stand aside from prolonged ranging price action without a clear liquidity target/sweep. **[STATED]** (DAnXM7C16h0 @ 56:41–57:19; “stay out of price action like this.”)
- **[MISSING]** News-event tiers, spread/volatility filters, day-of-week, minimum reward, and exact session times.

### `coBMd1vk2Lo` — inaccessible ICT blueprint

- **[MISSING]** News, spread, volatility, day, session, instrument, HTF-alignment, and quality filters. Page chapters do not establish filters.

### `HNuRp9Z1bMs` — 50% PO3

- Top-down Daily/H4/H1 alignment and SMT are reported filters. **[STATED]** (HNuRp9Z1bMs @ approximately 09:25; “I look for the divergences between the two.”) **[MISSING]** No formal tolerance, exact lookback, event/news filter, spread rule, or hard session exclusion.
- A base-hit objective and break-even philosophy are selective management filters, not a minimum-R rule. **[STATED]** (HNuRp9Z1bMs @ approximately 02:42; “I just need to grab that base hit.”)

### `AVVM-FyewLg` — Little Rizzy

- Avoid NY open volatility. **[STATED]** (AVVM-FyewLg @ 1:15:06–1:15:17; “It’s too volatile… I stay out of New York’s open.”)
- Favor early patterns, especially first or second, and avoid late patterns as fatigue develops. **[STATED]** (AVVM-FyewLg @ 14:25–14:39; “the first one or two… work the best.”)
- Use Bollinger “reality” and broader trend/location as context. **[STATED]** (AVVM-FyewLg @ 10:53–11:19; “the middle line is like reality.”)
- Crash context may include declining GDP, rising unemployment, rapid falls, support, and headline saturation. **[STATED]** (AVVM-FyewLg @ 40:36–40:55; “is GDP declining? Is unemployment rising?”) These cues are discretionary, not formal calendar thresholds.
- **[MISSING]** Exact Bollinger period, trendline geometry, volatility threshold, day filter, and reproducible news definition.

### `ADnslyKOwFE` — Trident

- Time is a hard emphasis: approximately 03:00–06:30 NY. **[STATED]** (ADnslyKOwFE @ approximately 02:35; “This setup means nothing without the time.”)
- Prefer 200 EMA bullish location and stacked 5/9/13/21 EMAs; reject intertwining/crossing. **[STATED]** (ADnslyKOwFE @ approximately 05:14/06:08; “stacking” and “intertwining.”)
- The immediate next-candle doji-high rule is an explicit rejection filter. **[STATED]** (ADnslyKOwFE @ approximately 07:35; “If it closes above the high [of the Doji], I'll invalidate the trade.”)
- **[MISSING]** Exact EMA ordering, doji threshold, FVG threshold, news/day/spread filter, and long/short symmetry.

### `IB-fyWI5j8w` — MMXM/OTE

- Require HTF bias and key-level context. **[STATED]** (IB-fyWI5j8w @ 02:23–04:51; “HTF bias.”)
- Prefer clean displacement; reject or defer weak/wicky breaks to a Silver Bullet alternative. **[STATED]** (IB-fyWI5j8w @ 11:50–14:43; “clean break” and “wicky.”)
- ADR, based on a reported 5-day average, is used to ensure sufficient room remains. **[STATED]** (IB-fyWI5j8w @ 29:26–31:29; “ADR” and “5-day average.”)
- Trade fewer, higher-quality setups; fewer than 10 per month is described as preferable. **[STATED]** (IB-fyWI5j8w @ 18:28–22:42; “Frequency is not your best friend.”)
- **[MISSING]** ADR formula/threshold, exact news rule, spread, day filter, and objective quality score.

### `SQEtBHOJW6I` — filters unavailable

- **[MISSING]** The conflicting Pass A/B/C outputs mention “clear,” “energetic,” “major,” “unmitigated,” and session filters, but no one version is source-verifiable. They cannot be promoted into filters.

### `52ZsDmFHqyY` — small-cap filters

- Market-cap, float, price, sector, premarket volume, gap, range, and volume filters are the core screen. **[STATED]** (52ZsDmFHqyY @ 03:39–03:51; “initial market cap” and “must be over $3.00.”)
- Avoid biotech/energy and Chinese stocks. **[STATED]** (52ZsDmFHqyY @ 08:06/08:43; “avoid biotech and energy”; “avoid Chinese stocks.”)
- Skip a same-day GS when premarket volume exceeds 50M. **[STATED]** (52ZsDmFHqyY @ 05:37–06:05; “pre-market volume exceeds 50 million.”)
- Use the FRD consecutive-green-day, rising-volume, and range thresholds. **[STATED]** (52ZsDmFHqyY @ 07:30–09:03; “at least 3 consecutive green days with increasing volume.”)
- **[MISSING]** News-calendar/earnings/FDA/offerings filters, borrow/locate, halt/slippage, and exact float-rotation threshold in the video rule sheet.

## (14) Discretionary elements and the decision each affects

| Video / timestamp | Evidence and discretionary phrase | Decision affected |
|---|---|---|
| `DAnXM7C16h0` @ 05:44–06:01 | **[STATED]** “you have to be patient… sit on your hands… allow the market to build liquidity” | Wait instead of entering before a prerequisite swing/liquidity event |
| `DAnXM7C16h0` @ 18:23–18:40 | **[STATED]** “highest probability way… wait… for this trap move” | Prefer sweep/reversal confirmation over anticipation |
| `DAnXM7C16h0` @ 28:01–28:48 | **[STATED]** “usually, not all the time” | Treat internal-to-external targeting as a tendency, not certainty |
| `DAnXM7C16h0` @ 31:34–31:51 | **[STATED]** “I need to make sure there's logic” | Reject arbitrary target highs/lows |
| `DAnXM7C16h0` @ 52:42–53:15 | **[STATED]** “You don't need the very top… very bottom” | Do not over-refine a valid directional entry |
| `HNuRp9Z1bMs` @ approximately 14:15 | **[STATED]** “The moment that I can claw this [risk] back is a win for me” | Favor early risk removal/BE |
| `HNuRp9Z1bMs` @ approximately 15:50 | **[STATED]** “I can't teach my intuition… you can only do that through the reps” | Setup quality remains a discretionary recognition skill |
| `AVVM-FyewLg` @ 15:36–15:52 | **[STATED]** “we might be forming… I might go short here” | Timing and pattern acceptance are discretionary |
| `AVVM-FyewLg` @ 35:26–36:01 | **[STATED]** “you could… buy here… or… wait… closes above reality” | Choose early projected-bottom entry versus confirmation entry |
| `AVVM-FyewLg` @ 1:08:39–1:09:16 | **[STATED]** “wait for one of these to break” | Resolve competing bullish/bearish patterns |
| `ADnslyKOwFE` @ approximately 05:14 | **[STATED]** “stacking” | Accept/reject momentum context; numerical ordering is missing |
| `ADnslyKOwFE` @ approximately 10:15 | **[STATED]** “Don't try and predict the market, just react to it” | Require observed confirmation rather than anticipation |
| `ADnslyKOwFE` @ approximately 11:13/14:45 | **[STATED]** “large bearish candle” | Decide when trend weakness warrants exit; size threshold missing |
| `IB-fyWI5j8w` @ 11:50–14:43 | **[STATED]** “wicky” / “clean break” | Choose primary OTE path versus later Silver Bullet path |
| `IB-fyWI5j8w` @ 18:28–22:42 | **[STATED]** “Frequency is not your best friend” | Trade selectively and avoid high-frequency entries |
| `IB-fyWI5j8w` @ 29:26–31:29 | **[STATED]** “ADR” / “5-day average” | Decide whether enough daily range remains |
| `52ZsDmFHqyY` @ 06:19–06:36 | **[STATED]** “mass consolidation” / “cracks the bottom” | Decide whether GS has formed and broken a valid base; thresholds missing |
| `52ZsDmFHqyY` @ 08:35 | **[STATED]** “10:1 ratio” | Qualify/size BS; ratio direction is unresolved |
| `52ZsDmFHqyY` @ 13:42–15:01 | **[STATED]** “1/4 starter position” / “morning bounce fails to clear the prior high” | Stage FRD entry; exact close/fakeout mechanics missing |
| `SQEtBHOJW6I` @ all reported passes | **[INTERPRETED]** “clear,” “energetic,” “major,” “unmitigated,” “proximal,” “distal” | Candidate analyses do not establish source rules; decisions remain [MISSING] |
| `coBMd1vk2Lo` @ all chapters | **[MISSING]** Transcript and video unavailable | Every discretionary decision is unresolved |

## (15) Contradictions / alternative rules with both timestamps

1. **`DAnXM7C16h0` trigger semantics:** The general language supports an intrabar breach: **[STATED]** (DAnXM7C16h0 @ 46:51–47:09; “as soon as the high is spiked out.”) A live example also waits for confirmation/addition: **[STATED]** (DAnXM7C16h0 @ 26:32–27:06; “if we can get a nice five-minute close above, I will add.”) The base sweep trigger and optional confirmation/add are not a single deterministic rule.
2. **`DAnXM7C16h0` partials:** The speaker says he is not a big fan of partials and also uses 50%/70% examples: **[STATED]** (DAnXM7C16h0 @ 32:08–33:20; “usually takes 50%, or 70% when very confident.”) **[MISSING]** No universal percentage or confidence test.
3. **`coBMd1vk2Lo` duration:** Page representations differ by about one second, 1:00:27 versus 1:00:28. **[STATED]** (coBMd1vk2Lo @ page metadata; duration values reported in the source audit.) This is metadata, not a strategy contradiction; substantive content remains [MISSING].
4. **`HNuRp9Z1bMs` target range:** The target is described as 50% of a key range, impulse, H1 dealing range, or higher-timeframe range. **[STATED]** (HNuRp9Z1bMs @ reported target section; “50% midpoint.”) **[MISSING]** Endpoint selection is not resolved.
5. **`HNuRp9Z1bMs` break-even timeframe:** General analysis says entry-timeframe confirmation; related publisher cross-check specifies an H1 candle. **[STATED]** (HNuRp9Z1bMs @ approximately 15:11; “You either need to be right or right out.”) **[VISUAL—CROSS-CHECK ONLY]** (HNuRp9Z1bMs @ publisher example; 11:00 H1 candle.) These alternatives must be tested separately.
6. **`HNuRp9Z1bMs` entry type:** Limit on inversion retap versus stop beyond structural confirmation. **[STATED]** (HNuRp9Z1bMs @ reported entry section; “limit order on a ‘re-tap’… or… sell stop.”) Preference/precedence is [MISSING].
7. **`AVVM-FyewLg` short stop wording:** Later examples say above the high: **[STATED]** (AVVM-FyewLg @ 1:09:48–1:10:05; “right above the high of this candle.”) An earlier transcript passage says below the low: **[STATED]** (AVVM-FyewLg @ 29:08–29:29; “might do it like below the low here.”) The report flags the earlier wording as geometrically inconsistent/transcription or chart-orientation error; it must not be silently repaired.
8. **`ADnslyKOwFE` FVG timing:** General timing places the FVG at the 03:00 candle/02:30–03:30, while a USDCAD example reports 02:30. **[VISUAL]** (ADnslyKOwFE @ approximately 21:14; FVG at 02:30.) **[STATED]** (ADnslyKOwFE @ approximately 02:35; 03:00–06:30 window.) Whether pre-window FVG formation is eligible is [MISSING].
9. **`ADnslyKOwFE` stop reference:** General rule says below the entry/setup candle: **[STATED]** (ADnslyKOwFE @ approximately 10:28; “below the low of the entry candle setup.”) Secondary reconstruction says below the doji low. **[STATED/SECONDARY]** (ADnslyKOwFE @ indexed-summary rule; “below the dogee candle low.”) The stop reference is unresolved.
10. **`ADnslyKOwFE` reward target:** The source presents 1:20+ and a $51,000/$1,000 1:51 example, while USDCAD is reported above 175R. **[STATED]** (ADnslyKOwFE @ approximately 00:05/08:00; “$51,000 on $1,000 risk.”) **[STATED]** (ADnslyKOwFE @ approximately 11:13/14:45; “1:20+ RR.”) These are not a fixed 20R exit rule.
11. **`ADnslyKOwFE` EMA parameter:** One secondary summary reports 13 or 15; audiovisual analysis reports 13. **[STATED]** (ADnslyKOwFE @ approximately 05:14; “5, 9, 13, and 21 EMAs.”) **[MISSING]** The discrepancy is unresolved; 13 is retained as best-supported, not silently substituted.
12. **`IB-fyWI5j8w` stop:** Initial 1.0 stop versus refined 0.90 stop after displacement. **[STATED]** (IB-fyWI5j8w @ 26:28–29:25; “0.90 (90%) level” and “1.0 (100%) level.”) **[MISSING]** Whether 0.90 is optional, setup-specific, or universal.
13. **`IB-fyWI5j8w` OTE versus breaker/Silver Bullet:** General OTE values are 0.62/0.705/0.79: **[STATED]** (IB-fyWI5j8w @ 26:28–29:25; “0.62, 0.705 (Primary OTE), and 0.79.”) EURUSD example is reported to miss 62% and use a 5-minute FVG/approximately 50% breaker leg: **[VISUAL]** (IB-fyWI5j8w @ reported EURUSD example; “missed the 62% fib… 5m FVG/Silver Bullet.”) Precedence is [MISSING].
14. **`SQEtBHOJW6I` strategy identity:** Pass A reports IPP; Pass B reports T-Rex/2 PM Silver Bullet; Pass C reports generic ICT/order flow. **[INTERPRETED—CONFLICTING]** (SQEtBHOJW6I @ Pass A 00:15–09:15; Pass B 00:15–04:10; Pass C 01:12–21:40.) No pass is transcript-verified, so no hybrid may be constructed.
15. **`SQEtBHOJW6I` instruments/session/management:** Pass B alleges ES/NQ and 14:00–15:00 NY; Pass C alleges FX/metals/indices and London/New York; Pass A gives no session. **[INTERPRETED—CONFLICTING]** (SQEtBHOJW6I @ Pass B and Pass C sections.) All are unverified.
16. **`52ZsDmFHqyY` GS gap threshold:** Video analysis reports 70%–1000%. **[STATED]** (52ZsDmFHqyY @ 04:36; “gaps up 70%–1000%.”) Related creator page describes the cleaner GS as generally >100%. **[VISUAL/CROSS-CHECK]** (52ZsDmFHqyY @ related creator page; “more than 100%.”) Keep separate variants.
17. **`52ZsDmFHqyY` BS volume ratio:** Video wording says volume-to-trapped-volume and “10:1.” **[STATED]** (52ZsDmFHqyY @ 08:35; “10:1 ratio.”) Related page example uses old trapped shares greater than current implied shares. **[VISUAL/CROSS-CHECK]** (52ZsDmFHqyY @ related creator page; 25M old versus 10–15M current.) Numerator/denominator cannot be chosen faithfully.
18. **`52ZsDmFHqyY` FRD entry timing:** first red-day close/fakeout versus intraday failure versus next-day add. **[STATED]** (52ZsDmFHqyY @ 13:42; “1/4 starter position.”) **[STATED]** (52ZsDmFHqyY @ 13:51/15:01; “morning bounce fails to clear the prior high.”) The starter trigger remains ambiguous.

## (16) Every trade example shown

The following inventory preserves examples reported by the eight reports. It does not turn a visual or unverified example into a universal rule.

### `DAnXM7C16h0` — liquidity-trap examples

1. **NQ live trade:** **[VISUAL]** (DAnXM7C16h0 @ 23:36–24:10) NQ after stock open; lows were stabbed, buyers induced, and liquidity hunted. **[STATED]** (DAnXM7C16h0 @ 23:57; “spiked it right into my area I want to take a buy from below these lows.”) Multiple internal lows were taken; five micros initially and later add-on volume are reported. **[VISUAL]** (DAnXM7C16h0 @ 26:32–31:48) Stops were reduced/rolled, additional lows were used, and the trade reached the upside target. Exact fill, stop, and P/L details are incomplete.
2. **YM/Dow Jones sell example:** **[VISUAL]** (DAnXM7C16h0 @ 41:24–46:01) 30-minute context/5-minute execution, New York session, Asia high/low, equal lows as downside liquidity, bullish inducement and high sweep. **[STATED]** (DAnXM7C16h0 @ 46:33–47:09; “as soon as the high is spiked out.”) The short targets equal lows and possibly higher-timeframe liquidity; management uses optional 50%/70% partials. **[STATED]** (DAnXM7C16h0 @ 48:25–48:49; “$6,400 across four accounts.”) Exact date, prices, and realized fill data are [MISSING].
3. **Other narrated NQ/forex examples:** **[VISUAL]** (DAnXM7C16h0 @ 04:04–21:43) Whiteboard and chart cases illustrate bullish and bearish sweep logic, but no complete fill/stop/target record is supplied. Do not infer a trade outcome.

### `coBMd1vk2Lo` — inaccessible

- The page labels a “Chart examples” section starting at 47:32. **[STATED]** (coBMd1vk2Lo @ 47:32 page chapter; “Chart examples.”) **[MISSING]** Every instrument, setup, entry, stop, target, outcome, and chart detail is unavailable.

### `HNuRp9Z1bMs` — PO3/50% examples

1. **NQ short around 10:00 EST:** **[VISUAL]** (HNuRp9Z1bMs @ reported example) NQ swept the 09:00 high; ES failed to make a corresponding high; price entered an H1 inversion zone; outcome reported as 381 ticks/$1,905 on one contract. Exact entry/stop/target and chart timestamp are [MISSING].
2. **Bitcoin short:** **[VISUAL]** (HNuRp9Z1bMs @ reported BTC example) Weekly PO3/Daily 50% rebalance with ETH SMT; held about one month toward the 50% target. Exact dates, entry, size, and outcome are [MISSING].
3. **NQ Monday/Tuesday re-entry:** **[VISUAL]** (HNuRp9Z1bMs @ reported Monday/Tuesday example) H4-high manipulation and SMT; first attempt BE, second SMT/re-entry reached 50%. Reset/expiry and prices are [MISSING].
4. **Publisher cross-check only:** **[VISUAL—CROSS-CHECK]** (HNuRp9Z1bMs @ related publisher example) H1 PO3/SMT/inversion rejection, 3-minute execution, sell stop below breakdown candle, BE after 11:00 H1 candle, 50% H1 target. This is not independently verified target-video transcript evidence.

### `AVVM-FyewLg` — Little Rizzy examples

1. **QQQ 2022:** **[STATED]** (AVVM-FyewLg @ 04:39–04:51; “I was using QQQ to chart.”) The guest says a prediction was posted about two weeks ahead and was off by a dollar and a day; no trade fill/size/stop is supplied.
2. **Intraday 5-minute/X example:** **[STATED]** (AVVM-FyewLg @ 19:01–19:33; “it was a little risky… it’s going to turn here.”) A projected price was reportedly hit; instrument and execution details are [MISSING].
3. **S&P 1929 monthly crash:** **[VISUAL]** (AVVM-FyewLg @ 33:11–38:00) Descending trendline/lowest-low projection comes near crash bottom; early projected buy versus close-above-reality confirmation is shown.
4. **Nasdaq dot-com weekly:** **[VISUAL]** (AVVM-FyewLg @ 39:20–42:41) Large downtrend projection is presented as an early long-term entry basis; fundamentals are discussed.
5. **NDX 2008 crash:** **[STATED]** (AVVM-FyewLg @ 44:55–47:24; measured distance “41”) Projected long area, sideways trend change, middle-band close alternative, and subsequent upward Rizzies are described.
6. **2018 drop:** **[VISUAL]** (AVVM-FyewLg @ 47:24–48:14) Projection comes near the subsequent move; exact execution absent.
7. **2020/COVID:** **[STATED]** (AVVM-FyewLg @ 48:14–49:43; “huge drop followed by a bounce”) Repeated downward Rizzies continue, then inverse upward patterns after downtrend stops.
8. **April 2025 correction:** **[STATED]** (AVVM-FyewLg @ 51:30–53:38; “the bottom’s in”) Measured projection, 50% retracement, support, and speed of decline inform bottom call; invalidation leads to inverse pattern watch.
9. **Bitcoin monthly:** **[STATED]** (AVVM-FyewLg @ 54:56–57:21; projected “$50,000”) A still-forming downtrend projects toward $50,000; the speaker says she would not go long there and could hold a short to the projection, although this is not her normal strategy.
10. **Nasdaq intraday:** **[STATED]** (AVVM-FyewLg @ 57:50–1:00:03; “25,900”) A lower-band/turning pattern forecast about 25,900 and reportedly hit it; execution absent.
11. **HHH monthly:** **[STATED]** (AVVM-FyewLg @ 1:04:05–1:08:10; “around an $81 price… roughly $175”) Incomplete bullish Rizzy projects toward approximately $175 alongside a fundamental thesis; not a fully specified trade.
12. **Competing Nasdaq patterns:** **[STATED]** (AVVM-FyewLg @ 1:08:39–1:13:19; “wait for one of these to break”) Opposing patterns are resolved by sideways/up versus continued down/trendline break; exact coordinates are missing.
13. **5-minute to 1-minute zoom:** **[VISUAL]** (AVVM-FyewLg @ 1:14:19–1:17:27) A clearer lower-timeframe Rizzy and trend change are shown; no precise execution rule.

### `ADnslyKOwFE` — Trident examples

1. **USDJPY:** **[VISUAL]** (ADnslyKOwFE @ approximately 11:58/14:26) EMA stack, London Kill Zone, FVG around 04:00, doji wick through 50%, next candle below doji high; reported result approximately 28R. Exact dates/prices and realized-versus-excursion status are [MISSING].
2. **USDCAD:** **[VISUAL]** (ADnslyKOwFE @ approximately 16:01/21:14) Price above 200 EMA, stacked EMAs, FVG around 02:30, Trident confirmation, 8.4-pip stop, reported >175R daily move. Exact fills and date are [MISSING].
3. **Career-best payout:** **[STATED]** (ADnslyKOwFE @ approximately 00:05/08:00; “$51,000 on $1,000 risk”) Instrument/setup/entry/exit are [MISSING].
4. **Viewer anecdote:** Comments mention 15-minute gold profit, but it is not a source trade example and is excluded from the rule set.

### `IB-fyWI5j8w` — MMXM/OTE examples

1. **USDJPY sell, reported March 4–6:** **[VISUAL]** (IB-fyWI5j8w @ reported example) Bearish HTF FVG, Asian-high run, SMR, bearish displacement, OTE 70.5%–79%, 0.20 displaced close, BE, accumulation-low target; reported 2.5R–3.7R depending on stop variant. Exact fills/prices are [MISSING].
2. **EURUSD buy, reported March 27–28:** **[VISUAL]** (IB-fyWI5j8w @ reported example) Daily FVG, PDL sweep, SMR, bullish displacement, missed 62%, 5-minute Silver Bullet/approximately 50% breaker-leg retracement, expansion higher. Exact fib anchors, stop, target, and R are [MISSING].

### `SQEtBHOJW6I` — unverified alleged examples

The report lists these only as **[INTERPRETED—UNVERIFIED]**, not as verified source trades: EURUSD long around 02:10 (reported 1.08455 entry/1.08395 stop/1.08650 target); NAS100 short around 05:25 (18225/18260/18150); XAUUSD short around 08:40 (2306.20/2311.50/2290.00, alleged 80% partial at 1:2); GBPUSD long around 12:15 (1.26450/1.26250/1.27000); USDJPY short around 15:00 (155.800/156.100/155.000). The secondary article instead says a live Nvidia trade made over $50,000, with no reconstructable entry/stop/target. Because the analysis passes conflict and no transcript is available, none of these examples is accepted as a verified rule illustration.

### `52ZsDmFHqyY` — small-cap examples

1. **BIRD failed GS:** **[STATED/VISUAL]** (52ZsDmFHqyY @ 10:09–10:48; “You do not want to use Gap Up Short”) Premarket volume exceeded 70M and the stock squeezed upward; this supports the >50M crowding avoidance rule. Exact trade fields are [MISSING].
2. **EEIQ successful GS:** **[STATED/VISUAL]** (52ZsDmFHqyY @ 11:55–12:08; “gapped to approximately $9… spiked to approximately $12… faded”) Exact entry, stop, covers, size, and P/L are [MISSING].
3. **ASTC successful BS:** **[STATED/VISUAL]** (52ZsDmFHqyY @ 15:02–16:21; “historical resistance around $5.60”) Move from about $2 to $6 returned on lower volume and faded toward about $2.50. Exact fill, stop, size, and P/L are [MISSING].
4. **SLV successful FRD:** **[STATED/VISUAL]** (52ZsDmFHqyY @ 06:13–07:32; “at least 3 consecutive green days”/“massive drop”) Multi-day parabolic run, first red-day confirmation, subsequent decline. Exact entry, stop, target, and P/L are [MISSING].

## (17) Codability check

### EXACTLY CODABLE

The following can be encoded as **source-labelled components** without pretending that undefined parts are resolved: `DAnXM7C16h0` long/short sweep direction (“buy below lows, sell above highs”), market-execution preference, opposing-liquidity objective, and one/two-tick futures example; `HNuRp9Z1bMs` 50% base-hit objective, NQ/ES SMT example, and PO3 accumulation/manipulation/distribution concept; `AVVM-FyewLg` equal-distance projection geometry as a parameterized measurement, two-standard-deviation Bollinger mention, trendline-close invalidation preference, and first/second-pattern preference; `ADnslyKOwFE` 30-minute/Daily context, approximately 03:00–06:30 NY window, 200 EMA preference, listed EMA periods, FVG-to-doji-50%-interaction narrative, next-candle-below-doji-high rejection condition, and gold close-based exception; `IB-fyWI5j8w` 15-minute/5-minute/4H-Daily architecture, OTE values 0.62/0.705/0.79, 1.0 versus 0.90 stop variants, 0.20 BE trigger, accumulation target, -0.28/-0.62 extension values, and 1%–1.5%/additional-1% reported risk variants; `52ZsDmFHqyY` price/cap/float/sector screens, >50M GS crowding filter, three-green-day/rising-volume and 300%/1000% FRD thresholds, 25%/75% staging, and stated structural stop references.

These are **not complete strategies**. “Exactly codable” means the numeric or directional statement itself can be represented, not that all surrounding definitions, fills, or risk controls are known.

### AMBIGUOUS / DISCRETIONARY

The following remain materially judgment-based: what counts as a respected swing, internal/external liquidity, a sweep, rejection, SMT synchronization, an inversion zone, SMR, displacement, “clean” versus “wicky,” trendline construction, Bollinger “near/toward,” EMA “stacking/intertwining,” doji classification, “large bearish candle,” GS “mass consolidation”/“crack,” BS “near resistance,” volume-ratio direction, FRD “fakeout,” target-range selection, target priority, and choice between limit/stop/market execution. The reports repeatedly use intuition, patience, logic, confidence, higher-quality, and strong momentum without operational thresholds.

### MISSING

Material fields missing from at least one or more strategies include: exact swing/fractal algorithms; wick-versus-close requirements; FVG/IFVG/OB/breaker construction and validity; range endpoints; session/DST/day rules; news calendar and blackout; order prices and order type; spread/slippage/borrow/locate/halt handling; stop buffers and emergency stops; expiry/reset/re-entry; target hierarchy; partial/trailing/time exits; account-risk formula; daily loss limits; maximum concurrent risk; complete long/short mirror rules; and fully documented trade-example fills/outcomes. `coBMd1vk2Lo` is substantively unavailable, and `SQEtBHOJW6I` has no defensible single strategy because its analyses conflict.

### FINAL VERDICT

**Not faithfully codable as a single deterministic rule sheet or backtest without adding assumptions.** The eight videos do not describe one strategy; they contain distinct setup families, and several are deliberately discretionary. `DAnXM7C16h0`, `HNuRp9Z1bMs`, `AVVM-FyewLg`, `ADnslyKOwFE`, `IB-fyWI5j8w`, and `52ZsDmFHqyY` support parameterized research prototypes with explicit manual labels or sensitivity variants. `coBMd1vk2Lo` cannot be reconstructed beyond metadata/chapter topics. `SQEtBHOJW6I` must remain unresolved rather than being turned into an invented hybrid. Any implementation should preserve evidence tags, separate each setup, expose every ambiguity as a parameter, and report results as a mechanized interpretation rather than as a reproduction of the source rules.

## References

[1]: https://youtu.be/DAnXM7C16h0 "DAnXM7C16h0 — Liquidity-trap model"
[2]: https://youtu.be/coBMd1vk2Lo "coBMd1vk2Lo — Trader Mayne / ICT blueprint"
[3]: https://youtu.be/HNuRp9Z1bMs "HNuRp9Z1bMs — 50% rebalance / PO3 model"
[4]: https://youtu.be/AVVM-FyewLg "AVVM-FyewLg — Little Rizzy"
[5]: https://youtu.be/ADnslyKOwFE "ADnslyKOwFE — Trident setup"
[6]: https://youtu.be/IB-fyWI5j8w "IB-fyWI5j8w — MMXM/OTE"
[7]: https://youtu.be/SQEtBHOJW6I "SQEtBHOJW6I — live order-flow episode"
[8]: https://youtu.be/52ZsDmFHqyY "52ZsDmFHqyY — Steven Dux small-cap short statistics"

### Additional source-access references

[9]: https://my.infocaptor.com/hub/summaries/chart-fanatics/steal-this-easy-liquidity-trap-trading-strategy-%24500k%2B-perfect-sniper-entries-DAnXM7C16h0 "Timestamped transcript mirror used for DAnXM7C16h0"
[10]: https://www.chartfanatics.com/strategies/small-cap-short-statistics "Related Chart Fanatics strategy page used as a cross-check for 52ZsDmFHqyY"

*Prepared from the eight supplied research reports and the two independent spot-checks noted above. This document intentionally preserves uncertainty and does not repair missing rules.*
