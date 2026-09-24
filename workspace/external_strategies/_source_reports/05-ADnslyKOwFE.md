# Complete Trading-Strategy Extraction Report

## Source and access status

- **Source URL:** https://youtu.be/ADnslyKOwFE (resolved to https://www.youtube.com/watch?v=ADnslyKOwFE)
- **Video title:** **STEAL This INSANE Simple 90% Win Rate Trading Strategy (1:20+ RR) - TG Capital**
- **Channel:** Chart Fanatics; guest/trader identified as Tyler / TG Capital.
- **Displayed duration:** 48:15.
- **Page metadata:** 718K views and “1y ago” at the time of inspection; page description contains Chart Academy, Apex Trader Funding, NinjaTrader, and other promotional links.
- **Transcript acquisition:** **No direct transcript was obtainable.** `yt-dlp` failed because YouTube returned HTTP 429/403 and “Sign in to confirm you’re not a bot”; browser player access was also blocked with `LOGIN_REQUIRED` / Error 153. The YouTube page itself exposed title, description, comments, and duration, but not captions. An audiovisual-analysis pass was available and returned timestamped rule extraction, but it explicitly warns that it is **not a verbatim transcript**. Therefore, quotations below are included only where the analysis supplied a short quote; all other wording is tagged as visual/secondary/inferred rather than presented as verbatim speech.
- **Supplementary sources consulted:** YouTubeSummary’s indexed AI summary and a Vocus article in Chinese that reconstructs the strategy. These are treated as **secondary corroboration, not primary evidence**. A Reddit thread contained no substantive rules. An embedded YouTube player could not play the video.

## Evidence-tag convention

- **[STATED]**: spoken rule or claim with a timestamp and short quote supplied by the audiovisual extraction. Because the original transcript was unavailable, the quote should be treated as an extracted quotation rather than independently verified word-for-word against audio.
- **[VISUAL]**: chart/example or indicator observation reported by the audiovisual analysis.
- **[INTERPRETED]**: a conservative mechanical reading of a stated/visual rule; not an additional rule claimed by the trader.
- **[MISSING]**: not available or not defined in the accessible evidence. No outside ICT/SMC definitions have been imported.

## Executive rule set (one explicit setup)

The accessible evidence supports one explicit setup: a **bullish/long “Trident” setup** on a 30-minute chart during the New York-time London Kill Zone. The broad sequence is:

1. [STATED] Work only during approximately **03:00–06:30 New York time**, and stop seeking new entries after 06:30. The audiovisual extraction places this at approximately **02:35** and states the setup has no value without timing.
2. [STATED] Use a **30-minute execution chart** and a **daily chart** for the higher-timeframe narrative/management, approximately **02:58 and 03:52**.
3. [STATED] Prefer a long/bullish environment: price above the **200 EMA**, with **5, 9, 13, and 21 EMAs stacking** rather than crossing/intertwining, approximately **05:14, 06:08, and 13:51**.
4. [STATED/VISUAL] Wait for a bullish FVG, commonly reported around the 03:00 candle (one example is reported at 02:30; see contradictions below). The doji then wicks through the FVG’s 50% level/consequent encroachment, approximately **06:58 and 17:08**.
5. [STATED] The candle immediately after the doji must close **below the doji’s high** for the long setup. If it closes above the doji high, reject/invalidate the setup, approximately **07:35**.
6. [STATED/VISUAL] Execute after confirmation; the reported stop is below the setup/doji candle low, normally around 10 pips on USD pairs. Gold is an explicit exception: no hard stop is reportedly used; instead, wait for a 30-minute close below the key level, approximately **01:01, 01:07, 10:28, and 13:18**.
7. [STATED/INTERPRETED] Seek at least **1:20 risk-to-reward**, then ride the trend and exit when invalidation/weakness appears, including EMA changes/crossing or a large bearish candle. The exact target-selection rule and whether 1:20 is a fixed limit order or a minimum planned objective are not fully specified.

This is not a complete deterministic algorithm because the video’s formal definitions for FVG, doji, EMA “stacking,” liquidity, structure, entry price, expiry/reset, position sizing, and exits are not fully available in the accessible evidence.

## Instruments and markets

- [STATED] The audiovisual extraction lists **USDCAD/CAD, NZDUSD, EURUSD, GBPUSD, USDJPY, and XAUUSD/gold**, with the list appearing around **10:28–12:47**. The secondary indexed summary also lists these instruments.
- [STATED] **AUDUSD is avoided** because backtesting “didn’t work well” (timestamp unavailable in the accessible analysis; the indexed summary reports it without a primary timestamp).
- [STATED] The trader is described as long-biased and as favoring naturally bullish assets such as **gold and Nasdaq/NQ/ENQ** (approximately **03:52** and in the source summary). The exact ticker naming is inconsistent across sources: the audiovisual analysis says NQ, while the indexed summary says ENQ.
- [MISSING] Broker/symbol specifications, contract size, pip convention for each instrument, spread/slippage assumptions, and whether the strategy is intended for spot FX, CFDs, futures, or all of them.
- [MISSING] A complete instrument whitelist is not available. The listed pairs may be examples rather than an exhaustive universe.

## Time, session, timezone, days, and news

- [STATED] **Session:** London Kill Zone; approximately **03:00–06:30 New York time**. Quote supplied by the secondary reconstruction: “This setup means nothing without the time.” The audiovisual extraction places the rule at **02:35** and says to stop looking after 06:30.
- [STATED] The trader strongly emphasizes that the setup is worthless outside the time window; the audiovisual analysis gives the quote “Don't try and predict the market, just react to it” at approximately **10:15** and the indexed reconstruction gives “This setup means nothing without the time...”
- [INTERPRETED] A conservative implementation would allow new signals only when the relevant confirmation occurs within 03:00–06:30 New York time. It is **not established** whether an FVG may form before 03:00 and be traded after 03:00.
- [MISSING] Exact daylight-saving handling for New York time, whether 03:00–06:30 is EST/ET year-round, and whether “London Kill Zone” is anchored to London time instead.
- [MISSING] Permitted weekdays, holidays, weekend handling, market-open gaps, and rollover rules.
- [MISSING] News-event filter. No evidence was obtained for high-impact-news avoidance, scheduled-news blackout minutes, or a rule for holding through news.

## Timeframes and directional bias

- [STATED] **30-minute chart:** execution and pattern identification; approximately **02:58**.
- [STATED] **Daily chart:** higher-timeframe narrative, take-profit context, and longer management; approximately **03:52**.
- [STATED] The trader is **long-biased**, with gold/Nasdaq described as naturally bullish assets; approximately **03:52** and the indexed summary.
- [STATED] For longs, price should be above the **200 EMA**; approximately **13:51**. The secondary reconstruction says below 200 EMA implies bearish preference, but no complete short procedure is provided.
- [INTERPRETED] The evidence supports a long filter, not a symmetric long/short strategy. Do not automatically invert the long rules for shorts.
- [MISSING] Exact higher-timeframe structure definition: no formal swing-high/swing-low, trend-break, close-vs-wick, or multi-timeframe alignment rule is provided.

## Indicators and confluence

### EMA stack

- [STATED] Use **5, 9, 13, and 21 EMAs**; approximately **05:14**.
- [STATED] The EMAs should be “stacking” / aligned like a wave to show strong momentum; approximately **05:14**.
- [STATED] If EMAs are “intertwining” or crossing, the condition is low probability and should be ignored; approximately **06:08**.
- [INTERPRETED] A coding implementation must choose a numerical ordering and a tolerance for “intertwining”; the video evidence does not supply either. Do not silently choose one.
- [MISSING] Whether EMA values are calculated on close, typical price, or another input; whether stack order must be strict on every bar; how long the stack must persist; and whether the stack is checked on the 30-minute or daily chart.

### 200 EMA and other indicators

- [STATED] Price above the 200 EMA is a bullish preference filter for longs; approximately **13:51**.
- [STATED/VISUAL] The audiovisual analysis reports a proprietary/blurred indicator later visible as **“BullTrading 1m Easy Scalping Sys V3.0_pine5,”** around **01:20 and 13:25**. It reports candle-color guidance: “Bright Green”/strong bullish or “Black”/lower-volume bullish; exact interpretation is not independently verifiable because the video could not be viewed directly in this environment.
- [MISSING] The indicator’s source code, precise candle-color logic, whether it is required or merely confluence, and whether the 1-minute name conflicts with the 30-minute execution timeframe.
- [MISSING] Whether Bollinger Bands are a formal rule. The indexed summary mentions Bollinger Bands and price near the top band, but no primary timestamped rule was available.
- [MISSING] No other indicator parameters or thresholds are codable from the evidence.

## Entry setup: bullish Trident sequence

### Step 1: bullish FVG

- [STATED/VISUAL] A bullish FVG should print during/near the Kill Zone; the audiovisual extraction places this in the “Trident Pattern” section at approximately **06:58/17:08** and says it usually prints on the 03:00 candle or between 02:30 and 03:30.
- [VISUAL] A USDCAD example is reported with an FVG at **02:30** (example discussion around **21:14**); a USDJPY example is reported with an FVG at **04:00** (example context around **11:58**).
- [MISSING] The speaker’s own geometric definition of an FVG is unavailable. The evidence does not state the required candle count, whether the gap is wick-to-wick or body-to-body, minimum size, direction, whether it must remain open, or whether partial fills invalidate it.
- [MISSING] No explicit FVG expiry, reset, maximum age, or rule for multiple simultaneous FVGs is available.

### Step 2: doji and 50% interaction

- [STATED/VISUAL] After the FVG, wait for a doji-like candle; its wick must pass through the FVG’s **50% level**, called “consequent encroachment” in the analysis, approximately **06:58/17:08**.
- [STATED] The narrative is that sellers try to push into the FVG but buyers defend it, leaving a long lower wick; approximately **10:03**.
- [MISSING] Exact doji definition: no body-to-range percentage, maximum body size, wick ratio, minimum range, color, or allowable close location is provided.
- [MISSING] Exact 50% calculation: the evidence does not say whether the midpoint is based on the FVG’s wicks, candle bodies, or another range convention.
- [MISSING] It is not established whether merely touching 50% suffices or whether the wick must close back above it; the audiovisual extraction says “wicks through,” but no stricter close condition is provided.

### Step 3: next-candle confirmation and invalidation

- [STATED] The **immediately following candle** must close **below the doji’s high** for a long; approximately **07:35**. Supplied quote: “If it [the follow-up candle] closes above the high [of the Doji], I'll invalidate the trade... it's just not as highly probable.”
- [INTERPRETED] The order is FVG → doji with 50% wick interaction → exactly one next candle closes below doji high → entry/confirmation. A later candle cannot substitute unless the video says so; no such substitution rule was found.
- [MISSING] Whether “below the doji’s high” means strictly `<`, `<=`, or a close below the high after intrabar touch; no buffer is provided.
- [MISSING] Whether entry occurs at the confirming candle close, at its open, on a retracement, or by limit order at a level.
- [MISSING] Whether a confirming candle that closes below the doji high but below the FVG, below the doji low, or with a bearish body is rejected. No full candle-quality rule is available.

### Optionality, expiry, and reset

- [STATED] The trader describes the setup as low-frequency and patience-dependent; the audiovisual analysis quotes approximately 8–10 entries per pair per year at **00:50/08:35**.
- [MISSING] No explicit “must satisfy all conditions” statement with an optional/confluence hierarchy was recovered. It is not known whether EMA stack, 200 EMA, candle-color indicator, FVG, doji, and 50% interaction are all mandatory or whether some are preferences.
- [MISSING] No setup expiry, cancellation after a missed confirmation, maximum bars between FVG and doji, one-trade-per-session rule, duplicate-signal rule, or reset after invalidation is stated.

## Liquidity, FVG/IFVG, order blocks, and structure

- [STATED] Gold is described as having “liquidity wicks,” used to justify not using a hard stop; approximately **01:07/13:18**.
- [STATED/SECONDARY] The indexed summary mentions exiting on “IFVG / FVG invalidation,” but no primary timestamped quote or formal definition was available.
- [MISSING] Liquidity-pool definition, liquidity sweep criteria, equal-high/equal-low rule, external/internal liquidity distinction, sweep wick-vs-close condition, and required sequence are not available.
- [MISSING] FVG validity and mitigation rules are not defined beyond the doji wick through a 50% level.
- [MISSING] IFVG definition, conversion event, validity, and exact exit/invalidation rule are not available.
- [MISSING] No order-block setup, order-block definition, mitigation, breaker, or order-block validity rule was found.
- [MISSING] No formal market-structure-shift, break-of-structure, change-of-character, swing-point, or close-vs-wick rule was found.

## Entry execution

- [STATED/VISUAL] The audiovisual analysis says the entry follows confirmation and describes the USDCAD example as having an **8.4-pip stop**, approximately **16:01/21:14**.
- [INTERPRETED] The most conservative sequence is to enter only after the immediate post-doji candle has closed and passed the below-doji-high condition.
- [MISSING] Exact order type (market, stop, or limit), entry price, allowable slippage, spread filter, partial fills, and whether the order is placed at the confirmation close or next bar open.
- [MISSING] No rule for entries if price has already moved materially beyond the doji/FVG before the trader can execute.

## Stop-loss rules

### FX / USD-pair long stop

- [STATED] Stop is described as below the low of the setup/entry candle; approximately **10:28**. The audiovisual analysis also says “below the low of the entry candle setup” and the indexed summary says “below the dogee candle low.”
- [VISUAL] Typical USD-pair stop is reported as approximately **10 pips**; USDCAD example is reported at **8.4 pips**.
- [MISSING] The evidence conflicts or is imprecise about whether the reference is the doji low, confirmation-candle low, or another “key candle” low. It does not state whether the stop is below the wick or body, the exact price offset, spread adjustment, tick buffer, or whether the stop is fixed after entry.
- [MISSING] No short-side stop rule is available.

### Gold stop exception

- [STATED] For gold/XAUUSD, the trader reportedly does **not** use a hard stop because of liquidity wicks; instead he waits for a **30-minute candle close below the key level**, approximately **01:07/13:18**.
- [INTERPRETED] This is a close-based invalidation rather than a broker stop. It creates potentially unbounded intrabar/adverse risk and cannot be safely backtested without an exact key-level definition and execution assumption.
- [MISSING] Exact key level, whether the close must be below doji low/FVG/other level, how gaps are handled, maximum loss, emergency stop, and short-side gold behavior.

## Targets and trade management

- [STATED] Minimum/targeted risk-reward is reported as **1:20**; the video title itself says “1:20+ RR.” The audiovisual analysis places this in the strategy overview and examples; the secondary summary calls it “minimum 1:20.”
- [STATED] The trader reportedly rides the trend until EMA crossing/change or a large bearish candle; audiovisual timestamps approximately **11:13 and 14:45**.
- [STATED/SECONDARY] The indexed summary adds FVG/IFVG invalidation as an exit reason, but the exact original wording and timestamp were not obtained.
- [VISUAL/SECONDARY] The analysis mentions high-probability target areas such as 50% of a previous range or external liquidity, approximately **11:13/14:45**; no formal target formula is available.
- [INTERPRETED] The strategy is not shown as a simple fixed 20R take-profit system. “1:20 minimum” appears to be a selection/expectancy objective, while examples run far beyond 20R; do not encode a fixed TP without further evidence.
- [MISSING] Exact target price, whether 20R must be available before entry, scaling, partial take-profit, break-even movement, trailing stop, time stop, weekend exit, daily close handling, and treatment of open trades outside the Kill Zone.
- [MISSING] No unambiguous rule for taking profit if price reaches 20R before the daily exit/invalidation condition.

## Risk, sizing, and prop-firm constraints

- [STATED] A career-best result is reported as approximately **$51,000 on $1,000 risk**, described as **1:51 RR**, around **00:05/08:00**. The source title’s “1:20+” and this example are not a position-sizing formula.
- [STATED] The indexed summary reports risking **$1,000 on a $200,000 account**; exact primary timestamp unavailable.
- [STATED] The trader reportedly prefers “fully balanced-based” prop firms and warns that equity/high-water-mark drawdown can burn an account after an intraday gain retraces; this is a trading-environment preference, not a signal condition.
- [STATED] Examples named in secondary material include Alpha Capital, Think Capital, and FTMO; verify current firm rules independently before relying on this statement.
- [MISSING] No fixed percent risk per trade, dollar-risk formula, leverage, maximum simultaneous positions, daily loss limit, correlated-pair rule, or compounding rule.
- [MISSING] No sizing method for the gold no-hard-stop exception. This is a major codability and risk-control blocker.

## Filters and discretionary language

| Evidence | Phrase / rule | Decision affected |
|---|---|---|
| [STATED] ~02:35 | “London Kill Zone,” 03:00–06:30 NY | Whether a signal can be considered at all. |
| [STATED] ~05:14 | EMAs “stacking” | Trend/momentum qualification. |
| [STATED] ~06:08 | EMAs “intertwining” / crossing are low probability | Skip or reject a setup. |
| [STATED] ~07:35 | Follow-up close above doji high invalidates it | Reject the long setup. |
| [STATED] ~10:15 | “Don't try and predict the market, just react to it.” | Wait for confirmation rather than anticipatory entry. |
| [STATED] ~01:07/13:18 | Gold has “liquidity wicks”; no hard stop | Replace hard stop with close-based invalidation. |
| [STATED] ~11:13/14:45 | Ride trend; exit on EMA change/large bearish candle | Discretionary exit/management. |
| [STATED/SECONDARY] | “A+ setup,” patience, 8–10 entries per year | Selectivity and trade frequency; no numerical test supplied. |
| [MISSING] | “Strong bullish,” “naturally bullish,” “key level,” “large bearish candle” | Exact thresholds and codable definitions. |

The largest discretionary components are EMA “stacking,” doji classification, “strong” or “large” candle/color classification, identifying the key candle/level for gold, deciding whether a prior FVG remains valid, and deciding when trend weakness warrants exit.

## Contradictions and alternative rules

1. **FVG timing:** the general description says around the 03:00 candle or 02:30–03:30, while the USDCAD example is reported at **02:30** and the session is said to begin at 03:00. It is unclear whether pre-window formation may be traded after 03:00 or whether 02:30 is merely chart context. [CONTRADICTION/MISSING]
2. **Stop reference:** one extraction says below the “entry candle setup,” while the indexed summary says below the doji low. These are not necessarily the same candle. [CONTRADICTION]
3. **1:20 vs 1:51 vs 175R:** 1:20 is presented as a minimum/objective, while a career example is 1:51 and USDCAD is reported above 175R. This suggests discretionary trend-running, not a fixed 20R exit, but the exact rule is missing. [CONTRADICTION/INTERPRETED]
4. **EMA 13 vs 15:** the indexed summary reports “13 or 15” in one place; the audiovisual analysis reports 13. Use 13 only as the best-supported value, and flag the discrepancy. [CONTRADICTION]
5. **Candle-color indicator:** the audiovisual analysis reports bright green or black as bullish, while the secondary summary reports bright green and blue as different bullish strengths. The indicator’s source logic is unavailable. [CONTRADICTION/MISSING]
6. **Long-only versus short:** the video is repeatedly described as long-biased, but the request’s need for long and short rules cannot be satisfied. No complete short trigger, stop, target, or inversion rule was found. [MISSING]
7. **Gold stop:** “no hard stop” conflicts with deterministic risk sizing unless an emergency-loss rule exists; no such rule was found. [MISSING]

## Trade examples shown/reported

### USDJPY

- [VISUAL] Context: EMA stack during the London Kill Zone; approximately **11:58**.
- [VISUAL] FVG reportedly printed around **04:00**; doji wicked to/through the FVG 50% level; following candle closed below the doji high.
- [VISUAL] Reported outcome: approximately **28R**, with outcome timestamp around **14:26**.
- [MISSING] Exact date, chart screenshot, entry price, stop price, target/exit price, whether 28R is realized or maximum excursion, and whether the trade was live or a historical example.

### USDCAD

- [VISUAL] Context: price above 200 EMA with stacking EMAs; approximately **21:14** in the visual discussion.
- [VISUAL] FVG reportedly printed at **02:30** and Trident confirmation followed.
- [VISUAL] Stop reported as **8.4 pips**; approximately **16:01**.
- [VISUAL] Reported outcome: over **175R** on the daily timeframe.
- [MISSING] Exact entry, stop/exit prices, date, whether the stop was doji-low or another candle low, and whether “over 175R” is a theoretical chart move or realized trade.

### Career-best payout

- [STATED] Approximately **$51,000** on **$1,000 risk**, described as **1:51 RR**, around **00:05/08:00**.
- [MISSING] Instrument, setup details, entry/exit, dates, account rules, and whether fees/slippage were included.

### Other examples

- [MISSING] No additional individually reconstructable trade examples with sufficient context and outcome were accessible. Comments on the YouTube page mention a user trying the method on 15-minute gold and reporting profit, but that is a viewer anecdote, not a video trade example and should not be used as evidence.

## What is not established

The following requested details remain unavailable or undefined: a full verbatim transcript; formal three-candle FVG geometry; formal doji threshold; precise midpoint convention; liquidity/sweep definition; order-block definition; IFVG conversion/validity; market-structure definition; close-versus-wick requirements except the doji-high confirmation; entry price/order type; exact long stop buffer; any short setup; gold’s key invalidation level and maximum risk; target calculation; scaling and trailing; reset/expiry; days; holidays; news; spread/slippage; position sizing; and exact DST/timezone implementation.

## Codability check

| Component | Deterministic from evidence? | Reason |
|---|---:|---|
| Symbol list | Partly | Examples are listed, but universe and market type are not complete. |
| Session | Mostly | 03:00–06:30 New York is supplied, but DST and pre-window FVG treatment are unresolved. |
| Timeframes | Yes, broadly | 30-minute execution and daily context are repeatedly reported. |
| 200 EMA filter | Partly | Above-200-EMA long preference is stated; exact timeframe and strictness are not. |
| EMA stack | No | “Stacking/intertwining” lacks ordering/tolerance/persistence definitions. |
| FVG | No | Geometry, size, age, fill, and expiry are absent. |
| Doji | No | No quantitative body/wick definition. |
| FVG midpoint interaction | Partly | 50% wick interaction is stated; midpoint convention and touch/close semantics are absent. |
| Next-candle confirmation | Mostly | Next candle must close below doji high; strict inequality and other candle filters are missing. |
| Entry execution | No | Market/limit/stop and exact price are absent. |
| FX stop | No | “Below low” is ambiguous and buffer is absent. |
| Gold stop | No | Key level and max-loss logic are absent; no hard stop is not safely deterministic. |
| Target | No | 1:20, trend-running, 50% previous range, and external liquidity are not reconciled into one rule. |
| Risk sizing | No | No fixed risk fraction or sizing formula. |
| Short side | No | No complete short setup. |
| Backtestable as written | **No** | Too many undefined discretionary and execution components. |

## Final verdict

The video appears to present a **low-frequency, bullish Trident/FVG reversal-continuation idea**: use the 30-minute chart in the 03:00–06:30 New York London Kill Zone, prefer price above the 200 EMA with 5/9/13/21 EMAs stacked, require a bullish FVG, wait for a doji wick through its 50% level, reject the setup if the next candle closes above the doji high, then enter with a tight low-based stop and seek at least approximately 20R while managing on higher-timeframe trend weakness. Gold is treated differently with a close-based invalidation rather than a hard stop.

That is the most complete faithful extraction possible from the available evidence. It is **not yet a complete coding specification or safe backtesting algorithm**. The missing FVG/doji/structure/liquidity definitions, ambiguous stop reference, discretionary exits, unresolved timing contradiction, absent short rules, and no-hard-stop gold exception must be clarified from the original audio/video or from the trader before implementation. No ICT/SMC definitions or rules have been imported beyond terms explicitly reported as used in the video.

## Access blockers

1. YouTube watch page and player were blocked by bot/login verification; no direct captions were exposed.
2. `yt-dlp` failed with HTTP 429/403 and no player response.
3. Embedded playback failed with YouTube Error 153.
4. The available audiovisual analysis is timestamped but explicitly non-verbatim; exact quotes and fine chart details require direct video/transcript access.
5. Secondary summary pages may contain AI reconstruction errors and were used only to cross-check, not to fill gaps silently.

## References

1. [YouTube video](https://www.youtube.com/watch?v=ADnslyKOwFE)
2. [Indexed YouTubeSummary page](https://youtubesummary.com/summary/ADnslyKOwFE) (secondary AI summary; not a transcript)
3. [Vocus reconstruction](https://vocus.cc/article/692c10f2fd89780001595902) (secondary article; not the original video)
4. [FakeTrades page](https://app.faketrades.in/s/steal-this-insane-simple-90-win-rate-trading-strategy-1-20-rr-tg) (secondary automated decoding/backtest; not primary evidence)
5. [Reddit discussion](https://www.reddit.com/r/Forexstrategy/comments/1mss1t9/tg_capital_90_win_rate_strategy_from_the_youtube/) (no additional substantive rules)
*Report prepared 2026-09-23. All times are video timestamps unless explicitly marked as New York time.*
