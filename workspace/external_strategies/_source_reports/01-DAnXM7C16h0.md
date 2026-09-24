# Complete Trading-Strategy Extraction: Liquidity-Trap Model

## Source and acquisition

**Source video:** [STEAL This EASY Liquidity TRAP Trading Strategy - $500K+ (PERFECT Sniper Entries)](https://youtu.be/DAnXM7C16h0) [1]  
**Video ID:** `DAnXM7C16h0`  
**Channel:** Chart Fanatics  
**Presenter/trader:** Marco Acetony (the transcript also renders variants of the surname).  
**Displayed duration:** 1:49:37.  

The official YouTube page was inspected. It exposed the title, chapter list, description, and a transcript entry, but the browser-rendered player itself was unavailable. `yt-dlp` and `youtube-transcript-api` were attempted in the shell; YouTube returned timeouts, 403/429 responses, or a sign-in/bot challenge, so no official caption file or video download was obtained. A third-party transcript mirror, InfoCaptor, returned a long timestamped transcript covering the full video; that transcript is the evidence base for this report. The transcript includes the whiteboard and chart demonstrations as spoken descriptions. Consequently, claims marked **[VISUAL]** below mean a chart/whiteboard observation narrated in the transcript, not an independently frame-verified measurement. No rule is inferred from generic ICT/SMC knowledge.

**Evidence tags:** **[STATED]** = explicitly spoken rule or fact, with timestamp and quote; **[VISUAL]** = chart/whiteboard feature described as shown; **[INTERPRETED]** = conservative mechanical interpretation needed to make the speaker's language operational; **[MISSING]** = not supplied by the video/transcript.

## Executive conclusion

The model is a **liquidity-first reversal/continuation framework**. Marco first identifies a high or low that was respected and then left by a directional move. That move is said to induce retail traders to enter around the respected area, leaving resting stop orders on the opposite side. The intended trade is taken **only after price trades through the liquidity level**, not before it: “buy below lows, sell above highs.” A higher-timeframe liquidity target supplies the directional bias; a lower-timeframe sweep supplies execution. The strategy is deliberately not a fixed candlestick pattern and is fractal from daily/4-hour down to 1-minute.

The most important hard rule is that a prior high/low must be taken before the corresponding trade is allowed. For a bullish scenario, if price has first taken a high and then falls, Marco will not buy merely at a pullback or retail order-block/FVG area; he waits for the relevant low to be traded below. For a bearish scenario, after price has taken a low and moved up, he waits for the relevant high to be traded above. After the sweep, he normally market-executes and places the stop just beyond the left-side high/low that invalidates the idea. He targets opposing liquidity, not a fixed R multiple.

The video does **not** provide a fully deterministic backtest specification. It leaves material discretion around which swing counts, how much reaction is enough, the exact target-selection hierarchy, the precise time window beyond New York examples, the exact definition of “taken” (intrabar touch versus close), and position sizing. It therefore supports a faithful discretionary implementation or a parameterized research prototype, but not a single unambiguous algorithm without additional assumptions.

## 1. Instruments, sessions, time zone, and market context

- **Instruments shown:** Dow Jones futures/YM, Nasdaq futures/NQ, and EURUSD. The speaker says the method can be applied to other assets and to any chart in front of him. **[STATED]** At 04:04 in the chart examples: “Whatever chart is in front of me is the chart I'm trading.”
- **Asset breadth:** He recommends learners cap the watch list at about two or three pairs/assets. **[STATED]** 35:50: “I would cap myself out at about two three pairs on my watch list.”
- **Fractal timeframes:** The concept may be applied from daily and 4-hour through 1-hour, 15-minute, 5-minute, and 1-minute. **[STATED]** 12:28: “This could happen on the daily… all the way down to the one minute.”
- **Typical execution timeframe:** The 5-minute is described as his normal “do-it-all” timeframe in the YM example. **[STATED]** 42:32: “This is usually the time frame I'm hanging out on.” He sometimes drops to 1-minute for more opportunities, while warning that it also creates more ways to be stopped. **[STATED]** 47:04 in the transcript’s chart section: “more opportunity on M1 but also more opportunity to uh get slapped up.”
- **Preferred session/time zone:** The concrete examples use New York time. Stock open is 9:30 a.m. New York. **[STATED]** 42:16: “I'm always trading with New York time. So, stock open is 9:30 a.m. for me.”
- **Time window:** He says he trades one specific time window and treats activity outside it as irrelevant, but does not state the complete start/end times in the video. **[STATED]** 49:26–50:00: “I have a specific time window… What you people need to understand is what happens outside of the time window is completely irrelevant to me.” **[MISSING]** Exact window start, end, weekdays, daylight-saving convention, and whether it is always New York session are not stated. The YM example is about 1.5 hours after the New York stock open; the live NQ example runs through late morning and tries to exit before lunch. **[STATED]** 42:16 and 46:16.
- **London/Asia:** London and Asia moves are used as chart context and liquidity sources, not necessarily as entry sessions. In the YM example, Asia high/low and London price action are marked, then the trade is taken after New York stock open. **[VISUAL]** 43:51–44:08 and 45:04–45:39.
- **News:** He will not enter before a scheduled news release. He normally waits approximately 2–4 minutes after the release. **[STATED]** 07:24 in the NQ example: “I'll never enter before news… Usually typically 2 minutes, 3 minutes, 4 minutes, somewhere in that range.” No list of news events or a formal news calendar rule is given. **[MISSING]** News blackout window before release, acceptable event tiers, and whether this applies to all instruments are unspecified.
- **Stock open:** He marks 9:30 a.m. because it is important for futures/index behavior and usually looks for entries after the open. **[STATED]** 42:58–43:20: “Typically, I'm looking for entries after the open.”
- **Correlation/divergence:** He does not use correlated markets or SMT-style divergence. **[STATED]** 04:04: “Whatever chart is in front of me is the chart I'm trading… I have never personally used it.”

## 2. Core definitions and liquidity logic

### 2.1 Liquidity

- Liquidity is defined narrowly as resting orders, especially stop-loss orders. **[STATED]** 03:55–04:16: “In my opinion, liquidity is just resting orders in the market… usually… stop losses.”
- The location of resting liquidity is inferred from trader behavior. If traders enter near a high or low and price moves away, their stops are expected beyond that high or low. **[STATED]** 04:16–04:32: “If I understand certain traders are entering at a high or a low then I'll understand that there's going to be resting liquidity there.”
- Not every high or low is liquidity. A high/low becomes relevant when price respects it and moves away, which is treated as evidence that positions were induced or built there. **[STATED]** 03:34–03:55 and 13:03–14:00. **[INTERPRETED]** For coding, “respected and moved away” is a relational swing condition, but the video does not specify a minimum number of bars, distance, or volatility threshold.
- The simple directional shorthand is: **buy below lows; sell above highs**. **[STATED]** 10:06–10:23: “I will never look to take longs above the lows only below… Buy below lows, sell above highs.”
- A high or low that has just been swept is treated as having no remaining liquidity above/below it for the immediate model, until price subsequently approaches it, respects it, and moves away again. **[STATED]** 29:12–29:48 and 44:08–44:44. The speaker qualifies that “nothing’s 100%.”
- Equal/relative equal highs and lows can be liquidity. **[STATED]** 41:40–41:57: YM relative equal lows are called “an area of liquidity.” **[VISUAL]** The chart shows equal lows marked as a target for sells.

### 2.2 Inducement and traps

- A directional move that takes a previous high is interpreted as inducing buyers who see momentum or a BOS/market-structure break. A later move back to the low or an associated POI can produce a false reaction and build sell-side liquidity below the low. **[STATED]** 04:32–05:26.
- Conversely, a move that takes a previous low induces sellers; reactions back up toward highs can be false and build buy-side liquidity above those highs. **[STATED]** 08:19–11:20.
- A “trap” is therefore the zone where retail traders are expected to enter after the apparent structure break, before the true liquidity sweep in the opposite direction. **[INTERPRETED]** The speaker explicitly says retail labels such as BOS, breaker, order block, and FVG can be the areas used to induce liquidity, but does not define a separate trap indicator.
- The strategy waits for the trap move to complete. **[STATED]** 18:40: “wait again for this to form… this trap move to the downside. And then… the opportunity of riding this back up to the highs.”
- Reactions in an inducement zone are expected to be false/short-lived. **[STATED]** 10:06: “if there is reactions in this blue box… I understand it to be false and it's going to be shortlived.”

### 2.3 Structural, internal, and external liquidity

- **Structural liquidity** is the set of internal highs/lows left by swings in the move; the speaker uses the term broadly rather than giving a bar-by-bar definition. **[STATED]** 17:10 in the NQ example: “all this price action… is… structure liquidity.” **[INTERPRETED]** A coder would need a swing-identification rule.
- **External liquidity** is generally the top/bottom of a larger range or higher-timeframe swing; **internal liquidity** forms inside that range on lower timeframes. **[STATED]** 28:01–28:20: “The top of the range… bottom of the range… on the way up… forms some sort of internal.”
- The preferred relationship is to enter from swept internal liquidity and target external liquidity. **[STATED]** 28:20–28:48: “I'm taking entries off internal liquidity… targeting external.”
- Once external liquidity is taken, reversals often occur, but this is qualified as typical rather than guaranteed. **[STATED]** 28:35: “Typically once external is taken, there's reversals that occur.”
- Internal and external are relative to the chosen higher/lower timeframe; they are not fixed labels. **[STATED]** 11:37–12:28. **[MISSING]** No objective timeframe mapping or swing-distance threshold is supplied.

## 3. Directional bias and setup separation

There are two mirror-image setups. They share the same logic but should be coded separately because their trigger, stop side, and target side differ.

### Setup A — Bullish liquidity sweep: buy below a low

1. On the higher timeframe, identify a high that was taken or a bullish directional leg in which a low was respected and price moved away upward. This implies resting sell-side liquidity below the respected low. **[STATED]** 21:02–21:43 and 57:56–58:15.
2. Confirm there is a logical opposing liquidity target above. A low sweep alone is not enough; the speaker repeatedly says the trade must have a target and directional logic. **[STATED]** 11:20–11:54: “I'm always targeting liquidity and taking an entry after liquidity is taken.”
3. Wait for the bullish trap/inducement sequence. Price may first take an old high, induce buyers, and return toward a low/POI. Do not buy at the retail pullback zone or above the low. **[STATED]** 24:43–25:23 and 18:01–18:20.
4. Wait until price **trades below the selected low**. This is the non-negotiable trigger. **[STATED]** 24:43–25:23: “I will not buy this asset pair until this low is taken out.”
5. After the low is taken, execute the buy. The basic spoken rule is entry after liquidity is taken; the live example sometimes waits for a lower-timeframe reaction/close to add rather than treating every first touch as a complete entry. **[STATED]** 06:17–06:32 and 26:32–27:06. **[INTERPRETED]** The base trigger is a low sweep; a confirming close is optional in the examples, not a universal rule.
6. Place the stop below the relevant invalidating low. In futures, the speaker says the stop is literally one or two ticks below/above the level when the market feed is centralized. **[STATED]** 16:54 and 09:07 in the NQ example. **[MISSING]** Whether “below” means wick low, candle low, swing extreme, or a fixed tick offset is not fully formalized beyond examples.
7. Target opposing/internal-to-external liquidity above. Do not use a random fixed-R target. **[STATED]** 32:08–33:35 and 28:20–28:48.

### Setup B — Bearish liquidity sweep: sell above a high

1. On the higher timeframe, identify a low that was taken or a bearish directional leg in which a high was respected and price moved away downward. This implies resting buy-side liquidity above the respected high. **[STATED]** 02:58–03:34 and 13:25–14:00.
2. Confirm there is a logical opposing liquidity target below. **[STATED]** 31:34–31:51: “I need to make sure I'm targeting liquidity.”
3. Wait for a bearish trap/inducement sequence. Price may first take a low, induce sellers, and rally toward a high/POI. Do not sell at the retail pullback zone or below the high. **[STATED]** 08:19–10:23 and 25:23–25:43.
4. Wait until price **trades above the selected high**. **[STATED]** 25:23–25:43: “I will not look to take a sell until this high right here is taken out.”
5. Execute the sell as soon as the high is taken. **[STATED]** 31:01–31:19: “once the high is taken… That's why I'm taking a sell entry.” In the YM example, he says he market-executes “as soon as the high is spiked out.” **[STATED]** 46:33–47:09.
6. Place the stop above the relevant left-side high. For futures, the stop is normally one or two ticks above the high. **[STATED]** 31:19 and 09:07 in the NQ example.
7. Target opposing liquidity below. **[STATED]** 31:34–31:51 and 46:16–47:27.

## 4. Exact entry/execution rules and sequence

### Hard sequence

The most faithful common sequence is:

**(a) identify a respected swing → (b) observe the move away → (c) infer resting liquidity on the opposite side → (d) identify the higher-timeframe target and bias → (e) wait for the opposite-side liquidity sweep → (f) execute in the reversal direction → (g) protect beyond the invalidating swing → (h) target opposing liquidity.** **[INTERPRETED]** This ordering consolidates repeated spoken rules; the speaker does not present it as a numbered checklist.

- **Long:** select a low with liquidity below; allow price to trade below it; buy after the low is taken; stop below the low; target highs/liquidity above. **[STATED]** 06:17–06:32, 16:54–17:10, and 24:43–25:23.
- **Short:** select a high with liquidity above; allow price to trade above it; sell after the high is taken; stop above the high; target lows/liquidity below. **[STATED]** 30:41–31:19 and 46:16–47:09.
- **Order type:** he prefers market execution rather than limit orders, because he came from forex where spread could prevent a limit from being tagged. **[STATED]** 46:33–46:51: “I personally don't use limits too much… I just market execute.”
- **Touch/break/close:** the trigger language is “taken,” “spiked,” or “traded below/above.” This is generally an intrabar breach, not a required close. **[STATED]** 46:51–47:09 and 09:25 in the NQ example. **[MISSING]** The video never gives a universal precise rule distinguishing wick touch, tick penetration, candle close, or close back inside. The live example separately uses a strong 5-minute close above a low to justify adding, demonstrating that confirmation can be discretionary/optional rather than part of the base trigger. **[STATED]** 26:32–27:06.
- **Sequence of multiple sweeps:** price may take internal liquidity more than once before the move. The trader waits for a reaction that makes sense in the larger picture; he does not impose a one-sweep-only rule. **[VISUAL]** NQ live example, 25:59–28:36, where lows are spiked multiple times before confidence increases.
- **Expiry/reset:** if the required low/high has not been taken, no trade. If price moves away without the sweep, the unfilled liquidity becomes a future target or future setup, potentially the next day or week. **[STATED]** 25:59–26:50. **[MISSING]** No numeric time expiry, number-of-bars expiry, or rule for deleting a level after a new higher-timeframe event is given.
- **Strict no-chase rule:** if a bullish scenario takes a high but has not taken the required low, do not buy anywhere in between; if a bearish scenario has not taken the required high, do not sell anywhere in between. **[STATED]** 24:43–25:43 and 18:01–18:20.
- **Scale-in rule:** additional entries must independently fit the model; a winning first trade or partial does not authorize arbitrary add-ons. **[STATED]** 19:49–20:55. In the live NQ example, he adds after another low is traded and after risk is reduced, with a specific invalidation level. **[VISUAL]** 30:29–31:48.

## 5. Stop-loss rules

- **Short stop:** above the high that was swept or the relevant left-side high covering the trade. **[STATED]** 31:19: “stop loss above that high.” In NQ, he says “my stop covers this high on the left hand side.” **[STATED]** 08:32–09:25 in the NQ example.
- **Long stop:** below the low that was swept or the relevant left-side low. **[STATED]** 32:24–32:41 and 16:54–17:10.
- **Futures buffer:** one or two ticks beyond the high/low. **[STATED]** 09:07: “I do keep mine literally like a tick or two above the high.” The mirrored long-side buffer is implied by “above or below depending if you're buying or selling,” but the exact long quote is not supplied. **[INTERPRETED]** Use one/two ticks as the stated futures example, not as a guaranteed universal constant.
- **Forex buffer:** larger/well above or below because of spread, different feeds, and possible manipulation. The exact buffer is not given. **[STATED]** 08:49–09:07. **[MISSING]** Pip buffer, broker-feed tolerance, and slippage policy.
- **Stop movement:** once price makes favorable progress and establishes a new low/high that should not be revisited, he trails behind that newer swing and reduces risk. **[STATED]** 32:41–33:20. In live NQ, stops are rolled after a 30-minute rejection, after taking a high, and as price advances. **[VISUAL]** 30:29–30:52 and 37:35–39:35.
- **Break-even:** he does not generally move to break-even unless he has taken a partial or closed most of the trade. **[STATED]** 32:41–33:20.
- **No fixed stop size:** stop distance varies with the relevant swing and instrument. **[MISSING]** No maximum ticks, ATR multiple, percentage risk, or time-based stop is stated.

## 6. Targets and trade management

- **Target selection:** opposing liquidity is the primary target. For a buy, target highs where sellers’ stops may rest; for a sell, target lows where buyers’ stops may rest. **[STATED]** 11:20–11:37 and 31:34–31:51.
- **Internal versus external target:** he may take a lower-timeframe/internal partial and hold the remainder for the higher-timeframe/external target. **[STATED]** 46:51–47:43.
- **No arbitrary R targets:** he rejects taking partials at random 1:3 or 1:5 levels if those prices do not correspond to chart liquidity. **[STATED]** 33:20–34:10.
- **Partials are optional and trader-specific:** he says he is not a big fan of partials in the whiteboard explanation, but in the YM example he usually takes 50%, or 70% when very confident in the higher-timeframe bias, then holds the rest. **[STATED]** 32:08–33:20 and 47:09–47:43. This is an explicit management variation, not a contradiction in the entry model.
- **Trailing:** after favorable movement, trail beneath the latest protected low for a long or above the latest protected high for a short. **[STATED]** 32:41–33:20; the short-side mirror is **[INTERPRETED]** from the stated directional symmetry because a specific short trailing example is not verbally spelled out.
- **Do not cut because of ordinary candle noise:** in the live NQ trade, he says to set the stop/target and not let intervening candle closures create an emotional early exit. **[STATED]** 44:07–44:41.
- **Time-of-day management:** he prefers to be out before New York lunch when volume is expected to slow, but he does not change the chart target solely because of that. **[STATED]** 46:16–47:22.
- **No requirement to catch the exact top/bottom:** direction and bias matter more than a perfect entry. **[STATED]** 52:42–53:15: “You don't need the very top to catch that sell. You don't need the very bottom to catch that buy.”

## 7. Risk, sizing, and filters

- **Risk percentage:** not stated. **[MISSING]** There is no fixed percentage per trade, daily loss limit, maximum simultaneous risk, or account-level drawdown rule for this strategy.
- **Position sizing:** examples show five micro contracts initially, three contracts added, and four accounts in the live NQ segment. **[VISUAL]** 25:28: “Only got five micros”; 31:28: “add another three contracts.” This is example-specific, not a sizing formula. **[MISSING]** No account-size-to-contract formula or dollar-risk calculation is supplied.
- **Risk reduction:** the trader first reduces risk by moving the stop behind a new swing and may then scale additional volume only when the lower-timeframe liquidity sequence supports it. **[STATED]** 26:32–27:06 and 30:29–31:48.
- **Higher-timeframe bias filter:** the trade must align with a logical higher-timeframe liquidity target/bias. **[STATED]** 31:34–31:51 and 57:56–59:24.
- **Liquidity filter:** no trade if the relevant liquidity has not formed or has not been taken. **[STATED]** 14:16–15:06 and 36:52–37:15.
- **Chop filter:** stay out of prolonged ranging price action when no clear liquidity target/sweep is present. **[STATED]** 56:41–57:19: “if you learn how to stay out of price action like this, it'll avoid you a lot of losses.”
- **News filter:** do not enter before news; wait about 2–4 minutes after release. **[STATED]** 07:24–07:40 in the NQ example.
- **Session filter:** only trade the trader’s chosen time window; exact window is absent. **[STATED]** 49:26–50:00; **[MISSING]** exact boundaries/days.
- **Other indicators/tools:** no moving averages or indicator rule is presented. Fibonacci, support/resistance, order blocks, FVGs, breaker structures, and trendlines are described as ways retail traders may interpret the chart or as concepts that can help locate induced liquidity, not as required filters. **[STATED]** 05:10–05:26, 13:03–13:25, and 37:36–38:26.

## 8. FVG, IFVG, order blocks, and structure validity

- **Order blocks/FVGs/BOS/breakers:** the speaker mentions them as retail areas where traders may enter after a break or pullback. They can temporarily work and thereby help create liquidity. **[STATED]** 05:10–05:26 and 09:08–09:28.
- **They are not required entry definitions:** he says he does not refine the area to an imbalance and is more concerned that the high/low is taken. **[STATED]** 08:14–08:32 in the NQ example: “I don't like to refine it too much… It's unnecessary in my opinion.”
- **FVG/imbalance can be a visual location:** the transcript describes “an imbalance above,” a “massive inefficiency,” and possible red boxes, but no three-candle gap formula, fill rule, mitigation rule, or validity rule is supplied. **[VISUAL]** 04:36–05:10 in the NQ chart; 07:58–08:14. **[MISSING]** Formal FVG definition, IFVG definition, body/wick requirements, minimum gap size, fill percentage, invalidation, and whether an FVG can independently trigger a trade.
- **Structure/BOS:** a prior high/low break is said to induce retail traders who call it BOS or market-structure shift. The speaker does not use BOS as the final entry trigger; the sweep of the opposite liquidity is the trigger. **[STATED]** 04:32–05:10, 13:52–14:09, and 18:55–19:13.
- **Validity of a structural liquidity level:** a high/low is useful when it was respected and price moved away; after it is swept, the immediate liquidity is considered consumed. **[STATED]** 13:25–14:00 and 29:12–29:48. **[MISSING]** No formal pivot algorithm or minimum displacement.
- **IFVG:** the acronym is not used as a separately defined concept in the transcript. **[MISSING]** No IFVG rule exists in the source.

## 9. Every discretionary phrase and the decision it affects

| Timestamp | Phrase/evidence | Decision affected |
|---|---|---|
| 05:44–06:01 | “you have to be patient… sit on your hands… allow the market to build liquidity” | Wait rather than enter while the prerequisite swing/liquidity is absent. **[STATED]** |
| 12:10–12:28 | “I don't want it to [be viewed] as a pattern” | Do not copy a fixed visual template; interpret the logic in context. **[STATED]** |
| 14:16–15:06 | “why would I be trading?” after a large one-directional move | Stand aside until new liquidity forms. **[STATED]** |
| 18:23–18:40 | “highest probability way… wait… for this trap move” | Prefer waiting for the false move/sweep over anticipating the reversal. **[STATED]** |
| 25:23–25:43 | “if the market does not run this low, I will not involve myself” | Hard no-trade/reset rule for an uncompleted long setup. **[STATED]** |
| 28:01–28:48 | “usually, not all the time” | Internal-to-external targeting is a tendency, not a guarantee. **[STATED]** |
| 29:30–29:48 | “Obviously, nothing's 100%” | Liquidity-consumption inference is probabilistic. **[STATED]** |
| 31:34–31:51 | “I need to make sure there's logic” | Reject random lows/highs as targets. **[STATED]** |
| 32:41–33:20 | “this low should not be revisited” | Trail behind a newly protected swing. **[STATED]** |
| 33:35–34:10 | “random… RR point” | Do not partial at a fixed R unless chart liquidity also supports it. **[STATED]** |
| 35:17–35:50 | “unless that high or low gets taken, you're not really doing anything” | Remain flat until the trigger sweep. **[STATED]** |
| 36:52–37:15 | “I won't be buying unless these lows are taken… won't be selling until these highs are taken” | Explicit strict long/short trigger. **[STATED]** |
| 38:08–38:26 | “unlearn to relearn”; retail concepts can work temporarily to induce liquidity | Do not automatically trade OB/FVG/BOS reactions in their conventional direction. **[STATED]** |
| 42:16–43:20 | “heart of New York session”; “typically… after the open” | Prefer the selected New York window and avoid pre-open entries in the example. **[STATED]** |
| 49:26–50:00 | “what happens outside… completely irrelevant” | Ignore signals outside the chosen window. **[STATED]** |
| 52:42–53:15 | “You don't need the very top… very bottom” | Do not over-refine entry at the cost of missing a valid directional trade. **[STATED]** |
| 57:19–59:24 | “for the most part… but… nothing's ever 100%”; “look for your confirmation” | A marked liquidity level creates an opportunity, not an automatic order. **[STATED]** |
| Live NQ 26:32–27:06 | “if we can get a nice five-minute close above, I will add” and “nothing convincing like I won't take anything now” | Add only with timing plus a convincing close/reaction; discretionary confirmation. **[STATED]** |
| Live NQ 28:05–28:36 | “I’ll let price tell me when the bottom is in” | Do not try to pick the exact extreme; wait for reaction. **[STATED]** |
| Live NQ 33:19–34:38 | “last resort area”; “I’m not convinced otherwise” | Maintain or invalidate the trade based on evolving chart confidence; no numeric threshold. **[STATED]** |
| Live NQ 39:35–40:15 | “I might close out full… might close out a partial”; “if it doesn't reach it… no profits” | Timing can alter exit size, but target remains planned. **[STATED]** |

## 10. Trade examples shown

### 10.1 YM/Dow Jones sell example

- **Context:** Dow Jones/YM futures; 30-minute context, 5-minute execution. Relative equal lows are marked as downside liquidity. The example occurs in the heart of New York, roughly 1.5 hours after the 9:30 a.m. New York stock open. **[STATED]** 41:24–42:32.
- **Precondition:** London/early session first sweeps a low and rallies, then takes a high and induces buyers. Asia high/low are marked. **[VISUAL]** 43:20–44:44.
- **Trap/build:** After stock open, price chops, leaves equal highs, respects a low, and moves away. That move is treated as building liquidity below the low. **[VISUAL]** 45:04–45:39.
- **Entry:** The bullish move sweeps internal highs; the trader sells as the relevant high is spiked/taken. **[STATED]** 46:01–47:09.
- **Stop:** Above the overall high/left-side high. **[STATED]** 46:33–47:09.
- **Target:** The engineered equal lows, with a possible higher-timeframe target beyond. **[STATED]** 46:16–47:43.
- **Management/outcome:** He says a partial may be 50%, or 70% if very confident, with the remainder held to the higher-timeframe target. The transcript describes approximately 1:3.6 to the first low and approximately 1:10 to the higher-timeframe target. **[STATED]** 47:09–50:17. Exact fill prices and whether the displayed trade was personally executed are not fully documented; it is described as a recent example and “textbook.” **[MISSING]** Exact date, entry price, stop price, final fill, and realized P/L.

### 10.2 EURUSD higher-timeframe example / directional case study

- **Context:** A large bullish EURUSD move from a low to a high is discussed on a higher timeframe, followed by roughly 1.5 weeks/10 trading days of range. **[STATED]** 53:53–57:01.
- **Bias:** Despite tempting short arguments based on Fibonacci, order blocks, FVGs, and a 50% range level, the speaker says that if looking for buys, he would only buy below a particular low. **[STATED]** 55:04–57:19.
- **Reason:** A high was taken; price pulled back to an extreme low, respected it, and moved away, leaving liquidity below the low. **[STATED]** 57:37–58:15.
- **Entry logic:** The low must be run, and then lower-timeframe confirmation/reaction is sought; any reaction below a particular structural high may be false within the bullish higher-timeframe context. **[STATED]** 59:06–59:56.
- **News visual:** A later spike is associated by the presenters with FOMC/news; it first sweeps internal liquidity, induces buyers, and then the broader low-to-high structure remains intact. **[VISUAL]** transcript section labeled 00:15–01:55 after the EUR discussion. Exact event/date is not reliably recoverable from the transcript. **[MISSING]** No executed EURUSD order or realized outcome is shown in the transcript.

### 10.3 NQ/Nasdaq 15m/5m/1m sell example

- **Context:** NQ; 15-minute higher-timeframe chart, then 5-minute and 1-minute. A selloff leaves internal lows and a large inefficiency below. London prints a low; internal highs are run shortly before New York open. **[VISUAL]** 03:48–05:48 in the NQ chart section.
- **Bias/strict rule:** Since a high was taken, buyers are considered induced. The trader will not buy unless the specified low/close is taken; reactions at the low before that are expected to be false. **[STATED]** 06:26–06:43.
- **News/session filter:** A spike occurs after 8:30 a.m. New York news; he will not enter before news and waits 2–4 minutes after release. **[STATED]** 07:24–07:40.
- **Short entry:** He will not sell unless the high is taken. Once taken, he enters, with the stop covering the left-side high. **[STATED]** 07:58–09:25.
- **Target:** Opposing lows and higher-timeframe downside liquidity; possible lower-timeframe partial and higher-timeframe final target. **[STATED]** 09:25–09:44.
- **Outcome:** The transcript provides the setup logic but not a clean final realized P/L for this particular chart example. **[MISSING]**

### 10.4 NQ April 1 bullish example

- **Context:** NQ, April 1; 5-minute execution around New York stock open. Several lows were respected four times, then a bullish move occurred and a selloff finally took those lows. **[VISUAL]** 12:24–13:12 in the NQ April 1 section.
- **Bias:** The repeated low sweeps/trap remove buyers and create confluence for a bullish move, but the speaker still requires the higher-timeframe liquidity pairing. **[STATED]** 12:55–13:12.
- **Strict rule:** A high has been taken and buyers were induced; he will not look for a buy until the specified low is taken. **[STATED]** 13:32–14:09.
- **Entry:** After stock open, price spikes up and clears internal liquidity, inducing buyers; once trading below all relevant liquidity and after a prior low sweep, the area becomes a buy location. **[VISUAL]** 15:06–16:38.
- **Stop:** Below the buy area/low. **[STATED]** 16:54–17:10.
- **Target/management:** Target internal highs to the left; he took a small partial above the first high, not at a fixed R. If a later high is taken, he would not buy a pullback until the required low is again taken. **[STATED]** 17:10–18:20.
- **Outcome:** The transcript does not give a final close or realized result for this April 1 example. **[MISSING]**

### 10.5 Live NQ/New York trade

- **Initial context:** After stock open, price induces buyers and hunts multiple lows. At 10:00 a.m. the 4-hour candle closes and price spikes into the buy area below lows. Targets include London highs, relative equal highs, and a 4-hour high. **[VISUAL]** 23:36–24:22.
- **Initial size:** Five micro contracts. First target is approximately 320 ticks from the average entry area. **[VISUAL]** 25:28.
- **Stop:** Initially below PDL/previous-day low and then adjusted around the lower-timeframe extreme. **[VISUAL]** 25:02–25:28.
- **Additional trigger:** The 5-minute low is spiked. The trader considers adding after a convincing 5-minute close above; he rejects a weak close. **[STATED]** 26:15–27:06.
- **Scale-in:** After a lower-timeframe high is taken and a pullback occurs, he plans to add below the 10:19 low; he adds three contracts when that low is traded, with the scale-in invalid if price does not hold above 23142. **[VISUAL]** 30:29–31:48.
- **Management:** He rolls the original stop below newer lows after a 30-minute rejection, covers risk as highs are taken, and tracks internal highs as targets. **[VISUAL]** 30:29–31:48 and 37:35–39:35.
- **Exit:** He takes partials after highs are taken, takes additional partials as time approaches New York lunch, and closes the remainder at the final high/target. The trade lasts about 1 hour 50 minutes; the speaker reports about $1,600 per account across four accounts, approximately $6,400 total. **[STATED]** 46:41–48:25. This is the clearest fully narrated live outcome.

## 11. Contradictions and alternative rules

1. **Partials:** The whiteboard says he is “not the biggest fan” of partials and prefers holding to targets; the YM and live NQ examples do take partials, often 50–70% or at internal highs. **[STATED]** 32:08–33:20 versus 47:09–47:43 and 46:41–48:25. Resolution: entry/target logic is fixed; partial policy is discretionary and trader-specific.
2. **Immediate entry versus confirmation:** The base short rule says enter as soon as the high is taken. The live long examples wait for reaction, timing confluence, or a convincing 5-minute close before adding. **[STATED]** 31:01–31:19, 26:32–27:06. Resolution: initial trigger is a sweep; additional confirmation/scale-in is optional and discretionary.
3. **Stop movement:** The whiteboard says trail once price moves away and a swing should not be revisited; the live trade sometimes holds the original stop through pullback and only rolls it when the chart gives the required signal. **[STATED]** 32:41–33:20 and live NQ 33:39–34:38. Resolution: no fear-based movement; move only after a newly protected swing/structural event.
4. **Session specificity:** He uses New York time and examples, but says the model can be traded at any time if that is the trader’s chosen window. **[STATED]** 49:26–50:00 and 10:51–11:10. Resolution: New York is the demonstrated preference, not a fully stated universal requirement.
5. **FVG/OB use:** These tools are named as possible retail POIs and visual areas, but he says refining to an imbalance is unnecessary. **[STATED]** 05:10–05:26 and 08:14–08:32. Resolution: do not code FVG/OB as mandatory unless testing an explicitly labeled variant.

## 12. Codability check

### Directly codable after choosing a swing algorithm

- Instrument and timeframe inputs.
- New York session clock and 9:30 stock-open marker.
- No entry before a specified news release and a 2–4 minute waiting interval, if a news feed is available.
- Long trigger: price trades below a selected low, then buy; short trigger: price trades above a selected high, then sell.
- Futures stop offset of one or two ticks beyond the selected swing, as an explicit test parameter.
- Target at a selected opposing liquidity level.
- Partial/trailing variants can be parameterized.

### Not uniquely codable from the video

- What exact bars constitute a “high,” “low,” “respected,” “move away,” “internal,” “external,” “structural,” “relative equal,” or “extreme.”
- Minimum displacement, number of retests, time spent, or volatility needed to create liquidity.
- Whether a sweep is an intrabar wick touch, one-tick break, candle close beyond, or close back inside.
- Which of several nearby highs/lows is the selected liquidity level.
- How higher-timeframe bias is resolved when higher-timeframe liquidity points conflict.
- Exact time-window start/end, days, and daylight-saving handling.
- News-event list, news source, and treatment of unscheduled headlines.
- Exact rules for choosing first/internal versus final/external target.
- Exact partial percentages in all cases, exact trailing distance, and when a stop is allowed to move.
- Position sizing, risk percentage, max trades, max concurrent exposure, and daily loss limits.
- Formal FVG, IFVG, order-block, breaker, BOS, or market-structure-shift definitions.
- Time-based expiry or reset after a setup fails to sweep.

### Minimum assumptions required for a research implementation

Any backtest must publish its assumptions rather than presenting them as the video’s rules. At minimum it must choose a pivot/fractal definition, a displacement threshold, a sweep/touch rule, a lookback window for eligible highs/lows, a target-selection hierarchy, a news calendar, and a risk-sizing model. Each assumption should be tested as a parameterized variant. The resulting performance would be a test of a mechanized interpretation, not proof that the video specifies that exact algorithm.

## 13. Final verdict

The video gives a coherent discretionary foundation: **wait for liquidity to build, determine bias from where liquidity sits and which opposing liquidity is available, then trade only after the relevant high/low is swept; protect beyond the swept swing and target opposing liquidity.** Its strongest explicit constraints are “buy below lows, sell above highs,” the no-chase rule, market execution, and the one/two-tick futures stop example.

It is **not fully codable without added assumptions**. The missing swing, displacement, sweep, confirmation, target, timing, and risk definitions are material. A faithful coding project should preserve two separate long/short setups, tag every added assumption, and run sensitivity tests over those assumptions. It should not silently convert the named FVG/OB/BOS concepts into ICT/SMC rules, because the speaker explicitly treats them as optional retail interpretations and focuses on the liquidity event itself.

## Ambiguities and blockers

1. Official YouTube captions/video download were blocked by YouTube timeouts, 403/429 responses, and bot/sign-in challenges.
2. The browser-rendered YouTube player was unavailable, so chart visuals could not be independently inspected frame by frame; chart observations above come from the timestamped transcript’s narration and are labeled **[VISUAL]**.
3. The transcript mirror occasionally resets timestamp formatting around the EURUSD section; the report retains the transcript’s local timestamps and identifies the surrounding section.
4. Exact session window, trading days, and timezone daylight-saving handling are absent beyond the stated New York-time examples and 9:30 stock-open marker.
5. The video does not define exact swing/pivot mechanics, minimum displacement, sweep semantics, candle-close requirements, expiry, target hierarchy, or position sizing.
6. The video does not define FVG, IFVG, order block, breaker, or BOS mechanically; IFVG is not separately discussed.
7. Several chart examples have narrated context but no fully documented fills, prices, dates, or final P/L. Only the final live NQ trade has a clear reported outcome.

## References

[1]: https://youtu.be/DAnXM7C16h0 "STEAL This EASY Liquidity TRAP Trading Strategy - $500K+ (PERFECT Sniper Entries)"
[2]: https://my.infocaptor.com/hub/summaries/chart-fanatics/steal-this-easy-liquidity-trap-trading-strategy-%24500k%2B-perfect-sniper-entries-DAnXM7C16h0 "InfoCaptor timestamped transcript mirror for the video"

## Transcript provenance

The local transcript artifact used for extraction was copied to the job workspace as `/home/ubuntu/jobs/2bac636f9c3a_a0/transcript_source.md` (SHA-256: `f12d4dca32f9c676ce336dd09f08de6fa9cf3fdb1b53f5948104f3a4c010b02a`).

[2]
/* The source page itself is cited above through the reference definition. */
![Transcript source page](https://my.infocaptor.com/hub/summaries/chart-fanatics/steal-this-easy-liquidity-trap-trading-strategy-%24500k%2B-perfect-sniper-entries-DAnXM7C16h0)

*End of report.*

[2]: https://my.infocaptor.com/hub/summaries/chart-fanatics/steal-this-easy-liquidity-trap-trading-strategy-%24500k%2B-perfect-sniper-entries-DAnXM7C16h0 "Timestamped transcript mirror"
