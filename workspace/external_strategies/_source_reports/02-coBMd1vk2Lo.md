# Trading-Strategy Extraction Report: `coBMd1vk2Lo`

## Executive finding

**Verdict: the complete trading strategy cannot be extracted reliably from the available evidence.** The public YouTube page exposes the title, channel, duration, description, and auto-generated chapter labels, but not the transcript text or playable chart footage in this environment. Direct extraction was blocked by YouTube anti-bot responses, and the available caption endpoints returned no caption payload. Consequently, this report does **not** reconstruct ICT/SMC rules from general knowledge and does **not** turn chapter labels into trading rules.

The only defensible conclusion is that the video is presented as a Trader Mayne / Chart Fanatics explanation of ICT concepts for forex and crypto. The exact definitions, sequence, execution logic, invalidation rules, examples, and risk parameters remain **[MISSING]**.

## Source and acquisition record

- **Source URL:** https://youtu.be/coBMd1vk2Lo
- **Canonical URL:** https://www.youtube.com/watch?v=coBMd1vk2Lo
- **Video ID:** `coBMd1vk2Lo`
- **Title:** *The SIMPLE $10 Million ICT Blueprint They Don’t Want You To See (Forex Trading Strategy)* **[STATED]**
- **Channel:** Chart Fanatics **[STATED]**
- **Guest named in the description:** Trader Mayne **[STATED]**
- **Published date shown by YouTube:** September 14, 2025 **[STATED]**
- **Duration:** approximately 1:00:27–1:00:28, with the two public page representations differing by about one second **[STATED]**
- **Description framing:** “On this episode of Chart Fanatics, Trader Mayne, an 8-figure forex and crypto trader, breaks down ICT concepts in one of the simplest guides available. Learn how to apply these powerful trading models across both traditional markets and crypto.” **[STATED]**
- **Transcript acquisition status:** **Unavailable.** `yt-dlp` was attempted with metadata, subtitle listing, automatic subtitles, and multiple player clients. YouTube returned HTTP 429/403 responses and “Sign in to confirm you’re not a bot.” `youtube_transcript_api` was redirected to a Google anti-bot page. Direct timed-text requests returned HTTP 200 with zero-byte bodies. The browser page also redirected to a Google unusual-traffic page. Public mirrors either timed out or presented a CAPTCHA. No transcript text was obtained.
- **Video/visual acquisition status:** **Unavailable.** The browser could not load a playable video or chart frames. The YouTube page exposed an Open Graph thumbnail URL, but a thumbnail is insufficient to inspect the chart demonstrations, candle geometry, or trade outcomes. No visual rule is therefore asserted.

## Timestamped page evidence

The following are YouTube's **auto-generated chapter labels**, not transcript evidence and not proof that each section contains a codable rule. They are included only to identify where the blocked source appears to discuss each topic.

| Timestamp | Chapter label | Evidence classification |
|---|---|---|
| 0:00 | Introduction | [STATED] page chapter label; substantive content [MISSING] |
| 2:55 | Price action concepts | [STATED] page chapter label; definitions [MISSING] |
| 7:05 | Market structure analysis | [STATED] page chapter label; structure rule [MISSING] |
| 11:17 | Points of interest | [STATED] page chapter label; POI definitions [MISSING] |
| 13:34 | Liquidity and draw | [STATED] page chapter label; liquidity/draw rules [MISSING] |
| 16:32 | Premium vs discount | [STATED] page chapter label; range/equilibrium rule [MISSING] |
| 18:00 | High time frame setup | [STATED] page chapter label; setup conditions [MISSING] |
| 21:46 | Execution technique | [STATED] page chapter label; execution conditions [MISSING] |
| 26:12 | Low time frame execution | [STATED] page chapter label; lower-timeframe trigger [MISSING] |
| 29:13 | Breaker block strategy | [STATED] page chapter label; breaker definition and validity [MISSING] |
| 34:08 | Risk management | [STATED] page chapter label; sizing and management [MISSING] |
| 38:13 | Pros and cons | [STATED] page chapter label; claims [MISSING] |
| 47:32 | Chart examples | [STATED] page chapter label; every example, context, and outcome [MISSING] |

The public page states “Follow along using the transcript” and displays “Show transcript,” but the transcript body was not delivered to the browser or extraction clients. **[STATED] page UI status; transcript content [MISSING].**

## Strategy extraction by requested field

### Instruments and market scope

The title identifies a **forex trading strategy**. The description says the models are applicable across “traditional markets and crypto.” The exact instruments, pairs, symbols, exchange, contract type, broker feed, or whether the examples use forex, crypto, futures, or another market are **[MISSING]**. No instrument should be inferred from the title alone.

### Time, session, timezone, hours, days, and news

The video has chapters titled “High time frame setup,” “Low time frame execution,” and “Chart examples,” but no accessible transcript or visual evidence specifies chart timeframes, trading session, kill zone, timezone, permitted hours, trading days, holidays, or news restrictions. All of these are **[MISSING]**.

### Directional bias

A high-timeframe section is listed at 18:00 **[STATED]**, but the bias procedure is not available. The report cannot determine whether bias comes from market structure, liquidity draw, premium/discount location, higher-timeframe order flow, a daily/weekly narrative, or another process. Bullish and bearish bias rules are **[MISSING]**.

### Ordered entry conditions and setup separation

The page suggests a multi-stage explanation because it separately lists high-timeframe setup, execution technique, and low-timeframe execution. That is a **[STATED] chapter sequence**, not enough evidence to specify a strategy. The following are all **[MISSING]**:

1. The exact first condition and the order of all subsequent conditions.
2. Whether the setup requires a liquidity event before structure confirmation, or structure confirmation before a return to a point of interest.
3. Required chart timeframe for each condition.
4. Whether a condition is based on a wick, candle close, touch, displacement, break, reclaim, or retest.
5. Whether conditions are mandatory, optional, or mutually exclusive.
6. The expiry window, reset rule, and whether a missed entry invalidates the setup.
7. Whether long and short setups are exact mirrors or have different rules.
8. Whether the “breaker block strategy” is a separate setup or a variant of the primary setup.

No deterministic entry algorithm is asserted because doing so would require inventing unavailable content.

### Liquidity definitions and sweep criteria

“Liquidity and draw” is an auto-generated chapter label at 13:34 **[STATED]**. The video’s actual definition of liquidity is **[MISSING]**. It is unknown whether the speaker means equal highs/lows, prior session highs/lows, swing points, trendline liquidity, inducement, internal/external liquidity, resting stops, or another category. Sweep criteria are also **[MISSING]**, including whether a sweep requires a wick beyond a level, a close beyond it, a return inside, displacement away, a specific timeframe, or a subsequent structure event.

### FVG, IFVG, order block, breaker block, and structure definitions

The accessible page does not supply transcript definitions. Exact rules for the following are **[MISSING]**:

- Fair value gap (FVG): candle count, gap boundaries, minimum size, wick/body treatment, mitigation, and invalidation.
- Inverse fair value gap (IFVG): whether this term is used, its conversion condition, and its validity.
- Order block: qualifying candle, displacement requirement, body/wick boundaries, mitigation, and invalidation.
- Breaker block: the chapter indicates that the concept is discussed at 29:13 **[STATED]**, but the failed-order-block condition, break requirement, retest rule, zone boundaries, and expiry are **[MISSING]**.
- Market structure: swing definition, fractal/lookback requirement, break-of-structure versus change-of-character wording, close/wick rule, and timeframe hierarchy are **[MISSING]**.
- Points of interest: ranking, confluence requirements, selection rule, and whether multiple zones may coexist are **[MISSING]**.

### Entry execution

“Execution technique” at 21:46 and “Low time frame execution” at 26:12 are **[STATED]** chapter labels. Limit order versus market order, exact entry price, zone fill rule, confirmation requirement, spread/slippage handling, partial entry logic, and maximum entry attempts are **[MISSING]**. No discretion can be safely mechanized.

### Stop-loss rules

Long and short stop-loss placement is **[MISSING]**. The available evidence does not identify the relevant candle, swing, wick, body, zone edge, buffer, spread allowance, fixed-pip offset, volatility adjustment, or whether the stop moves after entry. Breakeven timing, stop advancement, trailing logic, and invalidation before entry are also **[MISSING]**.

### Targets and management

Target selection and position management are **[MISSING]**. The report cannot determine whether targets are opposing liquidity, a prior high/low, an FVG, a fixed reward-to-risk multiple, a session range, or discretionary. Partial profit-taking, scale-out percentages, runner treatment, break-even rules, time-based exits, and end-of-session exits are **[MISSING]**.

### Risk and sizing

A “Risk management” chapter appears at 34:08 **[STATED]**, but its content is inaccessible. Risk per trade, daily loss limit, maximum concurrent positions, correlation treatment, sizing formula, leverage, account type, prop-firm constraints, and risk changes after wins or losses are **[MISSING]**.

### Filters

No reliable evidence is available for news filters, spread filters, volatility filters, day-of-week filters, session filters, instrument filters, higher-timeframe alignment, minimum reward-to-risk, or setup-quality thresholds. All are **[MISSING]**.

### Discretionary language and decisions it affects

The transcript and video are unavailable, so every discretionary phrase and the decision controlled by it are **[MISSING]**. In particular, this report cannot determine how the speaker uses terms such as “high probability,” “strong,” “clean,” “obvious,” “significant,” “near,” “ideally,” “if you want,” or “I like to.” Such wording must not be converted into code without the original utterance and surrounding chart context.

### Contradictions and alternative rules

No contradictions or alternative rule versions can be assessed because the primary evidence is unavailable. **[MISSING]**. The one visible metadata inconsistency is duration: one public representation shows 1:00:28 and another shows 1:00:27. This is a page-rendering discrepancy, not a strategy contradiction.

## Trade examples shown

The page labels a “Chart examples” section beginning at 47:32 **[STATED]**. Because the video and chart frames could not be loaded, the report cannot identify:

- the instrument and date for each example;
- the higher-timeframe context and directional bias;
- the liquidity event and point of interest;
- the exact entry, stop, target, and management;
- whether the example was live, replayed, or hypothetical;
- the outcome, including win, loss, scratch, or unresolved trade;
- whether any example illustrates an alternative or failed setup.

Every trade example and outcome is therefore **[MISSING]**.

## Codability check

**Not codable from the available evidence.** A backtest-ready implementation would require, at minimum, explicit definitions for swing points and liquidity, a timeframe hierarchy, an ordered trigger sequence, candle-close versus wick rules, zone construction, zone validity and expiry, entry execution, stop placement, target selection, management, risk sizing, and filters. None of those details can be recovered from the accessible page metadata without risking fabrication.

Any code written from this report would be a generic ICT/SMC strategy invented by the implementer rather than an extraction of this video. That would violate the source-faithfulness requirement.

## Explicit ambiguities and blockers

1. YouTube page requests were rate-limited or redirected to anti-bot pages.
2. `yt-dlp` could not extract metadata or subtitles because YouTube returned HTTP 429/403 and required sign-in to confirm the requester was not a bot.
3. `youtube_transcript_api` was blocked by a Google unusual-traffic response.
4. Direct `timedtext` requests returned empty responses.
5. Multiple alternate player clients returned `LOGIN_REQUIRED` with “Sign in to confirm you’re not a bot.”
6. Public transcript mirrors either timed out or returned CAPTCHA pages.
7. The browser could not load the playable video, so visual chart verification was impossible.
8. The available page exposes only auto-generated chapter labels, which are not a substitute for a transcript.
9. No exact strategy rule, trade example, or chart annotation is asserted beyond the page metadata quoted above.

## References

[1]: https://www.youtube.com/watch?v=coBMd1vk2Lo "The SIMPLE $10 Million ICT Blueprint They Don’t Want You To See (Forex Trading Strategy)"
[2]: https://youtu.be/coBMd1vk2Lo "YouTube short URL for the source video"
[3]: https://www.chartfanatics.com "Chart Fanatics website linked from the video"
[4]: https://app.chartacademy.com/masterclasses/496 "Chart Academy masterclass link listed in the video description"

*Prepared as a source-faithful extraction. This report is not trading advice and does not validate the profitability of any strategy.*
