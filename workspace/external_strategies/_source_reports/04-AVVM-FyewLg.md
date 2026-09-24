# Complete Trading-Strategy Extraction: AVVM-FyewLg

**Source video:** [STEAL This SIMPLE Trading Strategy from The WORLD's #2 Futures Trader - Marci Silfrain](https://youtu.be/AVVM-FyewLg)  
**Channel:** Chart Fanatics  
**Reported duration:** 1:23:29  
**Guest identified by the YouTube title/description:** Marci Silfrain. The third-party transcript sometimes transcribes her name as “Mussie/Massi Safi”; this is a transcription error, not a second strategy or guest.  
**Report status:** Complete extraction of the available timestamped transcript, with chart examples and the speaker's stated caveats separated from interpretation.

## 1. Access and evidence status

`yt-dlp` was attempted for metadata, subtitles, and a low-resolution video download. Direct extraction failed because YouTube returned HTTP 429/403 responses and “Sign in to confirm you’re not a bot”; no video file or official caption file was obtained. The YouTube page itself was accessible for title, channel, description, duration, and transcript-section metadata, but its extracted page reported the video as unavailable. A third-party indexed transcript page ([Lily transcript page](https://lilys.ai/en/notes/trading-strategy-20260813/simple-trading-strategy-marci-silfrain)) supplied a timestamped English script; the companion page describes it as a full script, and the related transcript service reports 9,739 words. The transcript was used as the primary evidence below. Direct frame-by-frame video inspection was blocked, so chart descriptions labeled `[VISUAL]` are transcript-described chart visuals rather than independently inspected frames.

**Important evidence caveat:** The transcript is machine-generated/edited and has occasional speaker attribution, name, and chart-coordinate errors. Quotes below preserve the transcript wording closely, including uncertain phrasing where it matters. Where the speaker’s wording does not fully determine a rule, the report says `[MISSING]` or `[INTERPRETED]` rather than silently filling the gap.

## 2. Strategy identity and scope

The method is called **“Little Rizzy”** in the episode. It is a repeated, measured-move pattern combining: (1) price action and a directional trendline, (2) an equal-distance projection, and (3) two-standard-deviation Bollinger Bands used as a “reality”/overextension context. The guest says the idea is her visual way of seeing Fibonacci retracements and the buyer/seller ratio, not an ICT/SMC framework.

There are three related but distinct uses:

1. **Downtrend continuation / short setup:** after a drop and bounce, draw a descending trendline, measure the vertical distance from the lowest-low candle to the trendline, and project that distance below the low.
2. **Uptrend continuation / long setup:** use the inverse: after a pullback/bounce structure in an uptrend, measure from the highest-high candle to the trendline and project the same distance above the high.
3. **Crash-bottom / reversal location:** use the downtrend projection as a possible bottom/long area; either enter near the projected level (often early) or wait for a candle close back above the middle Bollinger Band (“reality”).

The episode also discusses a **multi-timeframe conflict procedure**: if two Little Rizzies point in opposite directions, wait for one to break or for sideways/up/down behavior to clarify which pattern is active.

## 3. Instruments, charts, and market context

- `[STATED]` The method is presented as applicable to multiple asset classes: futures, stocks, crypto, forex, and options are named in the episode’s discussion. **Evidence (1:02:56):** “no matter if you're a crypto trader… futures… forex… stock trader.” This is broad scope, not a prescribed tradable universe.
- `[STATED]` Examples use SPX/S&P, QQQ, Nasdaq/NDX, Bitcoin, Howard Hughes Holdings (HHH), silver, and gold. **Evidence (4:39–4:51):** “I was using QQQ to chart”; **Evidence (44:43–44:51):** silver; **Evidence (54:56–57:21):** Bitcoin; **Evidence (1:04:05–1:06:40):** HHH.
- `[STATED]` Establish a higher-timeframe market trend/context first. **Evidence (15:04–15:18):** “it’s really important to establish a overall trend for the market… the daily SPX is in a uptrend.”
- `[STATED]` The pattern can be used on any timeframe, but the guest prefers longer timeframes. **Evidence (14:55–15:04):** “you can do this on any time frame… I like it better on the longer time frames.”
- `[STATED]` Intraday examples include 5-minute, 10-minute, and 30-minute charts; a 1-minute chart may reveal a pattern hidden inside sideways 5-minute candles. **Evidence (15:23–15:29):** “5-minute… 10-minute… 30-minute”; **Evidence (1:14:19–1:14:49):** lower the timeframe to see a Little Rizzy “more clearly.”
- `[INTERPRETED]` A practical implementation would treat a higher-timeframe Little Rizzy as directional context and a lower-timeframe Little Rizzy as a possible execution aid, but the episode does not provide a formal multi-timeframe algorithm.

## 4. Time, sessions, days, and news

- `[STATED]` The guest avoids the New York session open because of volatility. **Evidence (1:15:06–1:15:17):** “I hate the New York session open… It’s too volatile… I stay out of New York’s open.”
- `[STATED]` She likes the London open and says other opens are acceptable, but gives no exact clock times. **Evidence (1:15:09–1:15:17):** “I like the London open… I like all the other opens.”
- `[STATED]` Intraday seasonality should be studied; the guest describes a historical bias toward weakness/shorting in the New York session and a tendency to shift late in the day. **Evidence (1:15:24–1:15:45):** “there’s seasonality within the day… study it”; **Evidence (1:16:44–1:16:56):** “a bias towards going short during the New York session… towards the end of the day it tends to shift.”
- `[STATED]` A cited 2008 study found buying the NY open and selling the NY close lost roughly 45%, while buying the NY close and selling the next NY open gained roughly 8%; the guest presents this as seasonality evidence, not as a complete Little Rizzy entry rule. **Evidence (1:15:45–1:16:20):** “lost like 45%… reverse… net positive… like 8%.”
- `[MISSING]` No timezone, exact New York/London session clock, exchange hours, weekday restriction, holiday rule, or holding-period cutoff is supplied. “Friday night 11:05” appears only as the timestamp/context of a chart being viewed, not a trading rule (1:14:55).
- `[STATED]` For crash/bottom context, consider GDP declining and unemployment rising. **Evidence (40:36–40:55):** “is GDP declining? Is unemployment rising?”
- `[STATED]` Mainstream-news saturation is used as a contrarian “priced in” cue. **Evidence (43:35–44:15):** “when it is headline news on CNN, it’s priced in… when it hits those… headline news, it’s over.” She also watches for non-trading friends calling about the asset (44:09–44:15).
- `[MISSING]` No scheduled-news calendar, release blackout, numerical GDP/unemployment threshold, or reproducible definition of “mainstream” is given. The media cue is discretionary.

## 5. Core definitions

### 5.1 Little Rizzy pattern

- `[STATED]` In a downtrend, the pattern begins with a price decline, a bounce, and a descending trendline drawn over the resulting structure. **Evidence (7:58–8:14):** “all we have is the price data up until this point… draw a trend line… down”; **Evidence (15:36–15:52):** “we start dropping… wait for the bounce… see if it’s forming a trend line down.”
- `[STATED]` The pattern name is the guest’s own label; she explicitly says she does not know or care about a conventional name. **Evidence (8:14–8:50):** “I don’t even know what they are… we’re going to call this pattern a little Rizzy.”
- `[STATED]` A downtrend remains intact while Little Rizzies continue forming, price continues lower, and projected downward points keep being reached. **Evidence (10:10–10:21):** “if it keeps forming these little rizzies and it keeps going down and it keeps hitting these points downwards.”
- `[STATED]` In the inverse/uptrend form, the structure is reversed: pullbacks occur within an uptrend and the equal-distance projection is upward. **Evidence (5:40–5:56):** “the same inverse pattern works”; **Evidence (23:45–24:22):** “this would be a little rizzy… on a uptrend… the height it’s going to go on the next move.”
- `[VISUAL]` The whiteboard/chart examples show repeated alternating legs with an individually drawn trendline for each pattern. Direct frames were not available; this is the transcript’s description of the chart. **Evidence (36:43–37:50):** “individual pattern with the individual trend line.”
- `[MISSING]` The episode never gives a formal candle-count, swing-point, pivot, slope, or minimum-touch definition for a trendline. “Here to here” chart gestures are not enough to code uniquely.

### 5.2 Equal-distance projection

- `[STATED]` For a downtrend, find the candle with the lowest low within the individual pattern. At that candle’s horizontal position, measure vertically from the low up to the descending trendline. The next projected move is the same distance below the low. **Evidence (8:54–9:34):** “find the low on the candle that has the lowest low… measure… to the top of the trend line… Let’s say this is $20… the next move down will be this distance.”
- `[STATED]` The lowest-low candle may be the first or last candle of the pattern, including a gap-down candle. **Evidence (13:35–13:58):** “sometimes the lowest point is the first candle… sometimes it’s the last… one might have gapped down.”
- `[STATED]` The projection is subtracted from the lowest low for a down move. **Evidence (13:13–13:21):** “expecting is a $20 move below… below the low.”
- `[STATED]` For an uptrend, measure from the highest-high candle to the trendline and project the same distance above the high. **Evidence (23:57–24:22):** “measure the distance… the height it’s going to go on the next move is from the high to the point… on the trend line.”
- `[STATED]` The projection is used both as a target and as a way to judge whether the trend is continuing. **Evidence (13:58–14:02):** “that’s how I like to gauge… which way is the trend going.”
- `[INTERPRETED]` A deterministic geometric form consistent with the wording is: `D = abs(trendline_value_at_extreme_candle - extreme_price)`; down target `= low - D`; up target `= high + D`. This is an interpretation because the speaker never states a formula, interpolation method, or treatment of gaps.
- `[MISSING]` It is not stated whether “low/high” means wick extreme, candle body, close, or an adjusted swing point. The words “lowest low” and “highest high” imply price extremes, but wick-vs-body is not explicitly defined.

### 5.3 Bollinger “reality” bands

- `[STATED]` The middle Bollinger line is called “reality”; near the middle is in reality, while trading above the upper or below the lower band is out of reality. **Evidence (10:53–11:19):** “the middle line is like reality… If it trades above here, you’re out of reality… bottom line… out of reality.”
- `[STATED]` The guest uses two standard deviations and says she uses the default rather than extending the bands. **Evidence (20:31–20:42):** “I just use the two standard deviation… I don’t extend them.”
- `[STATED]` In a downtrend, she prefers the first Little Rizzy to occur toward the upper band or middle/above-reality area; the inverse is the lower side for an uptrend. **Evidence (11:25–11:48):** “I like when the first one happens towards the top… when it’s going down… flip side… bottom side.”
- `[STATED]` As a trend fades, a Little Rizzy may form near the lower band but fail to complete; increasingly out-of-reality conditions and shrinking ranges are signs of fatigue. **Evidence (12:33–12:55):** “as the trend is fading… one towards the bottom that’s not going to finish”; **Evidence (14:25–14:39):** fourth/fifth pattern may mean the market is tired and “ready for a bounce.”
- `[STATED]` A projected Little Rizzy is not automatically exited merely because price reaches/exceeds a Bollinger edge; the guest says she would play the whole measured move. **Evidence (24:49–25:19):** “I would play the whole move… even if it brought me out of reality.”
- `[INTERPRETED]` Bollinger Bands are a context/filter and confirmation tool, not a standalone overbought/oversold signal. This follows from the guest’s combination of bands with trend, projection, and context; no standalone band cross is prescribed.
- `[MISSING]` Bollinger lookback period, price source, treatment of band recalculation during a trade, and exact “near”/“toward” thresholds are not stated.

### 5.4 Invalidation, reset, and pattern competition

- `[STATED]` A close above a descending trendline breaks a bearish Little Rizzy; the cue is that the setup is no longer working. **Evidence (14:02–14:17):** “if you start getting closes above this trend line… little rizzy broke… it’s not always going to work.”
- `[STATED]` A next candle close through the trendline is preferred over an immediate stop at a very close level because price may retest and bounce. **Evidence (29:08–29:34):** “I very much kind of like to wait for like an actual close”; **Evidence (29:34–29:47):** “if the next candle… closed below this trend line, I would get out.”
- `[STATED]` Sideways trading with no new Little Rizzies suggests an uptrend may be ending and the next pattern may be down. **Evidence (30:23–30:56):** “it’s not forming any more little rizzies… going sideways… the next little rizzy… might be down.”
- `[STATED]` When two patterns conflict, wait for one to break; sideways then up favors the bullish/upward pattern, while continued decline below the relevant trendline favors the bearish/downward pattern. **Evidence (1:08:39–1:09:16):** “you actually have two in play… wait for one of these to break… starts trading sideways… and goes up… if this continues to go down… this one is probably the one in play.”
- `[STATED]` A new trendline may not be drawn until a later candle confirms the structure; the guest admits she may only recognize it several candles later and miss the first move. **Evidence (38:34–39:00):** “I wouldn’t have drawn it in until like you have this candle… may not have realized it until three candles down.”
- `[MISSING]` No exact reset rule, maximum age, number of failed projections, or formal definition of “break” beyond a close/continued movement is supplied. No re-entry rule is supplied.

## 6. Ordered setups

### Setup A — Downtrend continuation / short

1. `[STATED]` Establish an overall downtrend and wait for an initial drop. **Evidence (15:04–15:18):** “establish a overall trend”; **Evidence (15:36–15:40):** “we start dropping… I sit, I wait for the bounce.”
2. `[STATED]` Wait for the bounce/pullback, then determine whether a descending trendline can be drawn. **Evidence (15:36–15:52):** “wait for the bounce… see if it’s forming a trend line down.”
3. `[STATED]` Prefer the first one or two patterns after the move begins; later fourth/fifth patterns are less attractive as the trend becomes tired. **Evidence (14:25–14:39):** “the first one or two… work the best… fourth… fifth… market’s getting tired.”
4. `[STATED]` Identify the candle with the lowest low in this individual pattern and measure vertically to the trendline at that candle. **Evidence (8:54–9:34).`
5. `[STATED]` Project the same distance below the low as the profit objective. **Evidence (13:13–13:21); (15:52–16:06):** “$20 below here… exit point for a profit.”
6. `[STATED]` Entry timing is partly discretionary. The broad description says she “might go short” once the drop, bounce, and descending trendline suggest the pattern. **Evidence (15:36–15:52):** “then I’m like, ‘Hmm, we might be forming a little rizzy.’ And so, I might go short here.” A later 5-minute example says the relevant candle should close below the Bollinger middle/range before entry. **Evidence (1:11:34–1:11:45):** “when you see this… close below the… mid-range of the Bollinger… you’d enter.”
7. `[STATED]` Place the stop slightly above the relevant high/trendline area, not necessarily exactly at the high. **Evidence (1:09:48–1:10:05):** “stop… right above the high of this candle”; **Evidence (1:11:39–1:11:56):** “not directly on the high, just slightly above.”
8. `[STATED]` Exit if the trendline breaks; in one explanation she prefers an actual candle close through the line rather than a mere touch/retest. **Evidence (29:08–29:47).`
9. `[STATED]` Apply a maximum loss regardless of the chart stop. **Evidence (29:47–30:07):** “always apply a max loss to all of your trades.”
10. `[STATED]` Do not take the short merely because a pattern exists if the market is already at a low/near the lower Bollinger edge; that is more favorable for a bounce/long. **Evidence (1:01:21–1:01:42):** “not a good time to go short… good time… for a bounce to go long.”

`[MISSING]` The video does not specify market/limit/stop order type, whether entry is at close or next bar open, exact number of bars allowed between bounce and entry, a precise trendline algorithm, slippage, or whether the stop is a fixed price, close-based exit, or both. The stop language is also internally inconsistent in one whiteboard passage (see Contradictions below).

### Setup B — Uptrend continuation / long

1. `[STATED]` Apply the same pattern in reverse for an uptrend. **Evidence (5:40–5:56):** “the same inverse pattern works.”
2. `[STATED]` Measure from the highest high to the trendline at the same candle and project an equal distance above the high. **Evidence (23:57–24:22).`
3. `[STATED]` The guest says she would generally play the whole projected move even if it reaches outside the Bollinger “reality” band. **Evidence (24:49–25:19).`
4. `[STATED]` A move that breaks below the uptrend structure invalidates the upward Little Rizzy; a new uptrend pattern would need to form afterward. **Evidence (26:58–27:50):** “the second it comes… down below here… all bets off… next… pattern… need… green candles.”
5. `[STATED]` In a lower-timeframe execution context, the preferred entry is aligned with a lower/discounted location rather than buying at a high. **Evidence (1:13:19–1:14:13):** “if we’re at a low point… prefer a buy”; a higher-timeframe bullish pattern may be paired with a lower-timeframe bullish pattern near its low.
6. `[MISSING]` Exact long entry trigger, long stop placement, target management, and confirmation rule are not fully specified for ordinary uptrend continuation. The episode provides the geometry and context, but most detailed stop/entry examples are for bearish measured moves or crash-bottom longs.

### Setup C — Crash-bottom / reversal long

1. `[STATED]` Use the downtrend projection to estimate a possible crash bottom/long-term entry zone. **Evidence (33:21–35:26):** the S&P 1929 projection “gave you the bottom of the crash.”
2. `[STATED]` One option is to buy near the projected level, recognizing that this can be early because large crashes take time to bottom. **Evidence (35:26–35:45):** “you could… buy here… usually a little early… when there’s a big crash, it takes time to bottom.”
3. `[STATED]` The alternative confirmation entry is a candle close above the middle Bollinger Band (“reality”). **Evidence (35:45–36:01):** “wait until you get a candle that closes above reality… entry.”
4. `[STATED]` Additional context may include a broader Fibonacci retracement and fundamentals/support; in April 2025 the guest cited a 50% retracement, excessive speed of the fall, and support before calling the bottom. **Evidence (52:35–53:06).`
5. `[STATED]` If the candidate bottom pattern fails/gets invalidated, watch for the inverse/uptrend pattern rather than insisting the bottom call was correct. **Evidence (53:12–53:38):** “it did not work… invalidated… watch for… inverse direction.”
6. `[MISSING]` No fixed confirmation candle timeframe, number of closes, stop, position size, or rule for scaling into a bottom is given.

## 7. Stops, targets, trade management, and risk

- `[STATED]` Target geometry is the equal measured move; for a short, the projected downward distance is the target, and for a long the upward distance is the target. **Evidence (13:13–13:21); (23:57–24:22).`
- `[STATED]` She does not automatically scale out at the Bollinger edge; she says she would play the whole Little Rizzy move. **Evidence (24:49–25:19).`
- `[STATED]` A trendline break/close is the principal invalidation exit. **Evidence (14:02–14:17); (29:08–29:47).`
- `[STATED]` A hard maximum loss should always be applied. **Evidence (29:47–30:07).`
- `[STATED]` Stop distance should be less than or equal to the potential profit distance; she has no minimum-R multiple beyond that preference. **Evidence (1:10:20–1:10:45):** “distance… to where your stop is… less than or equal to the profit… no minimum threshold.”
- `[STATED]` She prefers not to take later/downstream patterns after a large move; first or second after an uptrend are preferred. **Evidence (1:10:45–1:11:34).`
- `[STATED]` She encourages letting winners run until the projected pattern completes, saying the trades she lets run make most of her money. **Evidence (1:19:28–1:20:19).`
- `[MISSING]` No fixed risk percentage, contract/share quantity formula, leverage rule, partial profit-taking, break-even movement, trailing stop, time stop, maximum daily loss, maximum simultaneous positions, or daily trade limit is supplied.
- `[MISSING]` For long crash-bottom entries, the exact protective stop is absent. For shorts, “slightly above the high” and “close through the trendline” are stated, but the relationship between the two is not fully formalized.

## 8. Liquidity, FVG/IFVG, order blocks, and structure terminology

- `[MISSING]` The video does not define liquidity, liquidity pools, stop sweeps, equal highs/lows, inducement, displacement, FVG/IFVG, order blocks, breaker blocks, or ICT/SMC structure rules. These must not be imported into a backtest.
- `[STATED]` The guest’s broad conceptual objective is to infer the ratio of buyers to sellers. **Evidence (4:01–4:11):** “we’re trying to figure out the ratio of buyers and sellers.” This is explanatory philosophy, not a codable liquidity rule.
- `[VISUAL]` The host mentions a lower-timeframe “break of structure” while discussing the 1-minute view (1:18:18–1:18:34), but this is the host’s description and is not defined or adopted as an additional entry condition by the guest. Treating it as a formal BOS rule would be an unsupported import.

## 9. Discretionary language and the decision it changes

| Timestamp | Tagged phrase/evidence | Decision affected |
|---|---|---|
| 4:15 | `[STATED]` “which way is the trend going… when could it possibly bottom” | Overall directional context and bottom-search objective. |
| 11:25–11:48 | `[STATED]` “I like when the first one happens towards the top… or the middle” | Prefer early downtrend patterns near upper/middle band; inverse for uptrend. |
| 12:33–12:55 | `[STATED]` “as the trend is fading… one towards the bottom that’s not going to finish” | Treat a lower-band pattern as possible trend fatigue rather than a normal continuation. |
| 14:25–14:39 | `[STATED]` “first one or two… work the best… fourth… fifth… market’s getting tired” | Pattern selection; later patterns are lower preference. |
| 15:36–15:52 | `[STATED]` “we might be forming… I might go short here” | Entry is discretionary rather than triggered by a fully specified event. |
| 19:11–19:33 | `[STATED]` “it was a little risky… I told everyone… it’s going to turn here” | Real-time turning-point call; no numerical risk criterion. |
| 24:49–25:19 | `[STATED]` “I would play the whole move” | No automatic scale-out at Bollinger edge. |
| 29:08–29:47 | `[STATED]` “might do it… I very much kind of like to wait for… an actual close” | Stop/exit may be chart-dependent; preference is close confirmation. |
| 35:26–36:01 | `[STATED]` “you could… buy here… or… wait… closes above reality” | Early versus confirmation bottom entry. |
| 38:34–39:00 | `[STATED]` “may not have realized it until three candles down” | Pattern recognition can be delayed; missed entries are accepted. |
| 40:36–40:55 | `[STATED]` “is GDP declining? Is unemployment rising?” | Crash context filter. |
| 43:35–44:15 | `[STATED]` “when it is headline news… it’s priced in” | Contrarian/news-context filter. |
| 52:56–53:06 | `[STATED]` “too much support… dropped too fast, too hard” | 2025 bottom judgment beyond the measured pattern. |
| 1:01:21–1:01:42 | `[STATED]` “not a good time to go short… good time… bounce to go long” | Reject late shorts near a projected/BB low; favor bounce. |
| 1:08:39–1:09:16 | `[STATED]` “wait for one of these to break” | Resolve competing patterns. |
| 1:10:45–1:11:34 | `[STATED]` “prefer… first one after an uptrend… probably wouldn’t… down here” | Avoid late continuation setups after a large move. |
| 1:13:19–1:14:13 | `[STATED]` “if we’re at a low point… prefer a buy”; “if we’re at highs… we want to be selling” | Location filter overrides blindly taking every pattern. |
| 1:15:06–1:16:56 | `[STATED]` “I hate the New York session open” and seasonality claims | Session filter and directional intraday bias. |
| 1:20:35–1:22:36 | `[STATED]` “practice… you’re going to make a lot of mistakes”; “longer time frames… easier” | Implementation requires discretionary training; not a plug-and-play system. |

## 10. Trade/chart examples and outcomes

| Approx. timestamp | Instrument/context | Setup and stated result |
|---|---|---|
| 4:39–4:51 | QQQ, 2022 | `[STATED]` The guest says she posted the prediction about two weeks ahead and was “off by a dollar and a day.” This is a claimed historical call, not a fully documented trade with entry/stop/size. |
| 19:01–19:33 | Intraday 5-minute chart posted on X | `[STATED]` She considered the turn risky, set a projected price using the pattern, and says price hit it. Exact instrument, entry, stop, and timestamp are not given. |
| 33:11–38:00 | S&P, monthly, 1929 crash | `[VISUAL]` A descending trendline and lowest-low projection produce a bottom close to the crash bottom. `[STATED]` Immediate buy could be early; alternatively wait for a candle close above the middle band. Multiple individual Rizzies continue down until one fails. |
| 39:20–42:41 | Nasdaq, weekly, dot-com crash | `[VISUAL]` One large downtrend Little Rizzy projects a level described as an early buy/long-term entry basis. `[STATED]` Fundamentals such as GDP and unemployment should be checked. |
| 44:55–47:24 | NDX/Nasdaq, 2008 crash | `[STATED]` A measured distance is “41,” described as a possible long entry level. Sideways action suggests trend change; entry could be at the projected area or after a candle breaks/closes above the middle Bollinger Band. Uptrend Rizzies then project upward. |
| 47:24–48:14 | 2018 drop | `[VISUAL]` A large drop is shown with a Little Rizzy that comes close to the subsequent move; the transcript calls it “close/perfect” but gives no exact trade execution. |
| 48:14–49:43 | 2020/COVID crash and reversal | `[STATED]` A huge drop followed by a bounce and repeated downward Rizzies continues lower; after the downtrend stops, inverse/upward Rizzies project the next move up. |
| 51:30–53:38 | April 2025 market correction | `[STATED]` A large measured move came close to the bottom; the guest considered entering around that level. A 50% Fibonacci retracement from the AI bull run plus support and the speed of the drop led her to post “the bottom’s in.” A candidate pattern could be invalidated, in which case she watches for the inverse pattern. |
| 54:56–57:21 | Bitcoin current chart, long-term/monthly context | `[STATED]` A still-forming downtrend pattern measures roughly $30,000 and projects into the $50,000 area; she says BTC may come under $60,000 toward $50,000 and would not go long at that point. She says a short could be held to the projected level, while acknowledging that such a long-term short is not her normal strategy. |
| 57:50–1:00:03 | Nasdaq intraday call | `[STATED]` With Nasdaq down over 2%, near the lower Bollinger band, a completed/turning Rizzy and a separate trendline projection led her to forecast about 25,900; she says price hit 25,900. Exact entry and position sizing are absent. |
| 1:04:05–1:08:10 | HHH monthly chart | `[STATED]` An incomplete bullish Little Rizzy from around an $81 price projects toward roughly $175 if it completes. This is combined with a fundamental thesis about Howard Hughes Holdings becoming a Berkshire-like holding company; it is an investment thesis, not a fully specified trade. |
| 1:08:39–1:13:19 | Nasdaq 5-minute/hourly competing patterns | `[STATED]` Two opposing patterns are active. Wait for one to break; sideways then up favors the upward pattern, continued down/below trendline favors the downward one. Stops are described as slightly beyond the relevant high, and example reward/risk is said to be over 2:1, but exact coordinates depend on the chart. |
| 1:14:19–1:17:27 | 5-minute chart zoomed to 1-minute | `[VISUAL]` Sideways 5-minute candles contain a clearer 1-minute Little Rizzy and lower-timeframe trend change. The guest recommends zooming in when a pattern may be present. No exact execution rule is supplied. |

## 11. Contradictions and alternative rules

1. **Stop side/wording ambiguity:** The clearest later short example places the stop “right above the high”/“slightly above” (1:09:48–1:10:05; 1:11:39–1:11:56). Earlier, while discussing a sell exit, the transcript says she “might do it like below the low here” (29:08–29:29), which is geometrically inconsistent with a conventional short stop and may reflect the chart orientation or transcript error. Do not code the earlier phrase without reviewing the original frame.
2. **Close-based versus immediate invalidation:** She says closes above the bearish trendline break the pattern (14:02–14:17), but also says to get out if the trendline breaks and to apply a max loss (29:08–30:07). A backtest must choose whether an intrabar breach, a close, or a hard stop exits first; the video does not resolve this.
3. **Entry trigger ambiguity:** The broad intraday description permits a discretionary short once a drop, bounce, and trendline appear (15:36–15:52), whereas the later example says entry follows a close below the Bollinger mid-range (1:11:34–1:11:45). The latter is not explicitly stated as universal.
4. **Trendline construction:** Historical examples draw an individual line for each Rizzy, but real-time remarks admit the line may only be recognized several candles later (36:43–37:50; 38:34–39:00). A hindsight-drawn line will overstate codability and performance.
5. **Bottom entry:** The method permits both buying at the projected bottom and waiting for middle-band confirmation (35:26–36:01). These are alternative setups, not a single mandatory rule.
6. **Bollinger edge:** The guest calls out-of-reality conditions a reason to expect mean reversion, but also says to play the whole measured move even outside the band (11:21; 24:49–25:19). The band is context, not an automatic take-profit.
7. **Trendline continuity:** She explicitly rejects using one trendline across the whole 1929 decline, preferring individual pattern lines, while acknowledging that traders can use one long line (36:43–37:50). The preferred rule is individual lines, but the alternative is mentioned.

## 12. Codability check

### Directly codable after explicit parameter choices

- Two-standard-deviation Bollinger Bands, once the missing lookback/source are chosen.
- Equal-distance geometry, if the extreme price and trendline value are defined.
- Target formula as an equal projection above/below the pattern extreme.
- A close beyond a specified trendline as an invalidation event.
- Optional middle-band-close confirmation for crash-bottom long entries.
- Broad session exclusion of the New York open, once a timezone and exact open window are supplied.
- A general reward-distance constraint: stop distance `<=` measured profit distance.

### Not uniquely codable from the video

- Identifying the initial drop, bounce, and exact trendline anchor points.
- Defining a Little Rizzy with objective candle count/swing rules.
- Wick versus body versus close for the extreme measurement.
- Whether “close below/above” is required for every entry or only examples.
- How to resolve two overlapping patterns beyond waiting for one to break.
- Exact entry order, fill timing, slippage, and stop priority.
- Long-side stop and management rules.
- News/media/fundamental filters, which are qualitative and discretionary.
- Session timezone and exact no-trade window.
- Position sizing and portfolio risk.

A faithful backtest therefore needs a **parameterized interpretation layer** and should report results across alternative definitions. It should not claim to reproduce the guest’s strategy exactly unless those choices are explicitly documented as assumptions.

## 13. Final verdict

The complete strategy described is a **fractal, trend-following equal-distance projection method (“Little Rizzy”) contextualized by two-standard-deviation Bollinger Bands**. In a bearish sequence, wait for a drop and bounce, draw a descending line, measure from the lowest-low candle to the line, project the same distance below the low, and exit/abandon on a trendline failure or hard max loss. In a bullish sequence, invert the geometry. For crash bottoms, use the projected downside level as an early long area or wait for a candle close back above the Bollinger middle line. Prefer early patterns, avoid late shorts near a lower-band low, use broader trend/fundamental context, and avoid the New York open.

The episode supplies enough information to build a **family of testable approximations**, but not a single unambiguous mechanical strategy. The highest-risk sources of backtest distortion are hindsight trendline drawing, subjective pattern selection, unspecified Bollinger parameters, unresolved stop/entry contradictions, and qualitative context filters. No liquidity sweep, FVG/IFVG, order-block, ICT/SMC, or other outside rule should be added.

## 14. Explicit ambiguity/blocker list

- Direct YouTube video and official captions were blocked by bot/HTTP restrictions; no independent frame inspection was possible.
- Third-party transcript has occasional transcription/name/speaker errors.
- Exact trendline anchors and Little Rizzy boundaries are not defined.
- Wick/body/close basis of “lowest low/highest high” is not explicit.
- Bollinger lookback, source, and “near/toward” thresholds are missing.
- Universal entry trigger is not specified; broad “might go short” conflicts with one close-below-middle-band example.
- Stop language is contradictory in one passage; later short examples say slightly above the high.
- Long-side stop and management are missing.
- No sizing, risk percentage, leverage, trade count, or portfolio limits are given.
- No timezone, exact session windows, weekday rules, or news-release schedule is given.
- “Mainstream news priced in,” GDP/unemployment, support, and “too fast/too hard” are discretionary.
- No formal reset/expiry/re-entry rule is given after a failed or completed pattern.
- Historical examples report approximate outcomes, not complete trade records with fills, costs, and sizes.
- “320%” is a biographical/competition claim in the episode, not a verified backtest statistic for this rule set.

## Source links

1. [YouTube video](https://youtu.be/AVVM-FyewLg)
2. [YouTube watch page](https://www.youtube.com/watch?v=AVVM-FyewLg)
3. [Timestamped third-party transcript used for evidence](https://lilys.ai/en/notes/trading-strategy-20260813/simple-trading-strategy-marci-silfrain)
4. [Independent summary cross-check](https://youtubesummary.com/summary/AVVM-FyewLg)

*This report records what the video says and does not constitute trading or investment advice.*
