# Complete Trading-Strategy Extraction: Trader Kane / 50% Rebalance Model

## Scope and conclusion

**Source video:** [Worlds BEST NQ Scalper Reveals His A+ Trading Strategy](https://youtu.be/HNuRp9Z1bMs) [1]  
**Video ID:** `HNuRp9Z1bMs`  
**Channel:** Chart Fanatics  
**Guest/strategy presenter:** Trader Kane  
**Reported runtime:** 1:14:44  
**Published:** 12 May 2025 (the public page reports “May 12, 2025”).

The video presents a **50% rebalance / Power of Three (PO3) reversal model**. The central idea is to wait for price to accumulate a range, manipulate or sweep a meaningful high/low, and then trade the reversal back toward the 50% midpoint of the relevant range. The model is framed as a way to take a “base hit,” not as a method for holding the entire ensuing trend.

**Important access limitation.** A complete verbatim transcript could not be acquired. `yt-dlp` and `youtube-transcript-api` were blocked by YouTube rate-limit/bot protection (HTTP 429/403 and `RequestBlocked`). The browser also received a Google/YouTube unusual-traffic page; the fetched YouTube page exposed metadata and description but no transcript lines, and displayed “Video unavailable” in the extraction. The detailed rule extraction below therefore combines the available multimodal audio/visual analysis of the video with the public video page and the publisher’s related strategy page. The multimodal tool explicitly warns that its output is **not a verbatim transcript**. Quotes attributed to the video are thus short speech excerpts reported by that analysis and should be re-verified against the original audio before automated implementation. Every rule is tagged as requested.

## Evidence tags

* **[STATED]** — spoken rule or claim attributed to the video. A timestamp and short quote are included when available. Because the transcript was inaccessible, “verbatim” means the wording returned by the audio analysis, not a transcript independently checked against the audio.
* **[VISUAL]** — chart/example feature reported by the multimodal visual analysis. The exact frame timestamp was not available unless stated.
* **[INTERPRETED]** — a faithful operational restatement needed to connect the speaker’s words into an ordered procedure. It is not an additional trading rule.
* **[MISSING]** — not supplied by the accessible video evidence; do not guess it.

The publisher’s related playbook is included only as a **cross-check** for terminology and the same model. It is not silently treated as proof that an item was spoken in the target video. Cross-check-only items are explicitly identified.

## 1. Instruments, markets, and chart timeframes

**Primary instrument.** [STATED] The main market is Nasdaq futures, referred to as **NQ**. The public description also says the episode covers applying NQ concepts to crypto markets [1].

**Correlation instrument.** [STATED] **ES** (S&P 500 futures) is used with NQ to identify SMT divergence. The reported example is: “NQ makes a new high while ES fails to make a new high.” (approximately 09:25; quote reported by audio analysis: “I look for the divergences between the two because it shows relative weakness on a single asset.”)

**Other markets shown.** [VISUAL] A BTCUSD/Bitcoin example is reported, with Ethereum used as the comparison asset for divergence. Exact exchange, contract, symbol, tick size, and data feed are [MISSING]. The analysis also describes futures and crypto as demonstrated asset classes.

**Higher-timeframe structure.** [STATED] The model is described across **Daily, 4-hour (H4), and 1-hour (H1)** charts, with a lower intraday chart used to execute. The reported video sequence is Daily for broad context, H4 and H1 for fractal/PO3 alignment, and M3/M5 (and in examples M3/M15) for precision. The exact fixed entry timeframe is [MISSING]; the examples are not fully consistent.

**Time window and timezone.** [STATED] The analysis reports **Eastern Standard Time (EST)**, with the most active window described as **09:15–11:30 EST**, a liquidity injection around **09:30 EST**, and a key manipulation/reversal time around **10:00 EST**. A PM opportunity around **14:00 EST** is also mentioned. These timezone labels are reported by the analysis and should be checked against the source’s actual daylight-saving convention. The video does not establish an exchange timezone or whether the rule changes during daylight-saving time. [MISSING]

**Days.** [VISUAL] Examples are described as a Thursday setup and a Monday/Tuesday setup. [MISSING] There is no reliable evidence that Thursday or Monday/Tuesday is a required trading day rather than merely the day of an example.

**News and scheduled events.** [MISSING] No explicit news filter, economic-calendar rule, blackout window, or event-handling instruction was recovered.

## 2. Core market model and directional bias

### 2.1 PO3 / AMD sequence

[STATED] The model uses a three-phase **Power of Three (PO3)** structure: accumulation, manipulation, distribution. The audio/visual analysis describes the phases as follows:

1. **Accumulation:** an initial range forms.
2. **Manipulation:** price trades beyond a meaningful prior high or low, creating a wick and taking liquidity.
3. **Distribution:** price moves in the intended direction after the manipulation.

[INTERPRETED] The bearish version is: establish a relevant range, allow price to run above a meaningful high, reject back below that area, and seek a move down toward the applicable 50% level. The bullish mirror is: establish a range, allow price to run below a meaningful low, reject back above it, and seek a move up toward the applicable 50% level. The video evidence does not provide a fully formal long checklist, so this symmetry is an interpretation of the stated bearish and bullish descriptions, not an independently stated rule.

### 2.2 50% rebalance objective

[STATED] The speaker’s directional requirement is reported at approximately **01:21**: “I always want to see price rebalance into 50% of the range and then continue with the trend.”

[STATED] The trading objective is reported at approximately **02:42**: “I don't need a big move. I just need to grab that base hit every single day and then I'm done.”

[INTERPRETED] The model is therefore not “enter in the direction of every breakout.” It seeks a reversal from manipulation back toward the midpoint of a selected dealing range, with continuation beyond 50% treated as optional rather than required.

[VISUAL] The public video description independently names “liquidity sweeps, divergence, PO3, and premium/discount zones” as subjects. The accessible video evidence does not specify an exact mathematical definition of the premium/discount zones beyond the use of a 50% midpoint. [MISSING] The precise range endpoints to use for each 50% calculation are not fully fixed.

### 2.3 Top-down bias

[STATED] The procedure is reported as a top-down alignment:

* Daily: establish the broad context and mark prior-day highs/lows.
* H4: check the corresponding range/PO3 behavior.
* H1: check whether the same PO3/manipulation pattern is present and identify a reversal area.
* Intraday: execute after the higher-timeframe conditions align.

[STATED] The analysis says all three higher timeframes should align at a key 50% level. [INTERPRETED] A setup should be rejected when Daily, H4, and H1 do not support the same 50%-rebalance narrative. The video does not state a numeric tolerance for “align,” whether the 50% levels must be identical, or whether one timeframe may override another. [MISSING]

## 3. Liquidity, manipulation, and SMT divergence

### 3.1 Liquidity/sweep behavior

[STATED] In the bearish case, manipulation is described as price trading above a prior high, including the previous day’s high in the Daily example. In the bullish case, it trades below a prior low. [VISUAL] The reported intraday example says NQ swept the **09:00 high** before the 10:00 reversal. [VISUAL] Another example is described as manipulation above an H4 high.

[INTERPRETED] A “sweep” in this report means a move beyond a previously marked high/low that is then rejected back into the prior range. This is the narrow behavior shown/described in the video, not a general definition imported from outside trading literature.

[STATED] The analysis describes the key event as a liquidity injection around **09:30 EST**, followed by manipulation/reversal around **10:00 EST**. The video does not define whether a sweep must exceed the level by a minimum number of ticks, whether a wick-only breach qualifies, or whether a candle close beyond the level invalidates the setup. [MISSING]

### 3.2 SMT divergence

[STATED] The reported short example is: **NQ makes a new high while ES does not make a new high**, interpreted as relative weakness in NQ. The corresponding bullish mirror is reported/strongly implied as one asset making a lower low while the comparison asset fails to make a lower low, but the exact spoken long wording is [MISSING].

[STATED] Approximately 09:25, the reported quote is: “I look for the divergences between the two because it shows relative weakness on a single asset.”

[INTERPRETED] For a short, the operational filter is: compare corresponding highs in NQ and ES; require NQ to take or exceed a reference high while ES fails to do the same; then look for the rejection/structural confirmation described below. For a long, use the opposite comparison only if the source’s intended mirror is confirmed. The video does not state the lookback, synchronization, acceptable price difference, or whether the divergence must occur on H1, M15, M3, or another exact timeframe. [MISSING]

### 3.3 Sweep expiry and reset

[INTERPRETED] The sequence implies that a sweep is followed by rejection and a single attempt at the inversion-zone/structure entry. [MISSING] The video does not state how long a sweep remains valid, whether the setup expires at the end of the 10:00 candle, whether a later retest can be used, or how the state resets after a failed entry. The Monday/Tuesday example indicates a later re-entry after a break-even result, but no formal reset rule is supplied.

## 4. Structural confirmation: FVG and inversion zones

### 4.1 Inversion zone

[STATED] An inversion zone is described as a prior **fair value gap (FVG)** that should have acted as support but is traded through and then acts as resistance, or the opposite for a bullish setup. The analysis states that price must reject the manipulated level and trade back into the internal range; this is called a “change of state of delivery.”

[INTERPRETED] The short-side sequence is: identify a former support/imbalance area, observe price trade through it, wait for the area to function as resistance, and use a rejection/breakdown from it as confirmation. The long side is the mirror only to the extent supported by the stated support/resistance reversal description.

[STATED] The reported entry alternatives are:

* place a **limit order** on a “re-tap” of the inversion zone after the sweep; or
* place a **sell stop/buy stop** beyond a structural level after manipulation is confirmed.

[VISUAL] The related publisher playbook, used only as terminology cross-check, describes a “breakdown candle closes below the inversion zone,” followed by a sell stop under that candle. It also reports a 3-minute execution after SMT and inversion-zone rejection. These details are consistent with, but not independently verified as verbatim from, the target video.

### 4.2 FVG definition and validity

[STATED] The video evidence identifies an inversion zone as a prior FVG but does not give the candle-by-candle definition of an FVG. [MISSING] The report therefore does not assume a three-candle gap rule, wick/body rule, minimum gap size, mitigation rule, fill rule, or deletion rule. [MISSING] It also does not establish whether an FVG remains valid after one touch, after a full fill, after a close through it, or only while it retains a support/resistance role.

### 4.3 Order blocks and structure

[STATED] The accessible evidence refers to “structural levels,” a manipulation point, an internal range, and inversion zones. [MISSING] No explicit order-block definition, candle selection rule, break-of-structure rule, change-of-character rule, swing algorithm, or minimum displacement requirement was recovered. Do not add an order-block or structure definition from ICT/SMC material.

## 5. Ordered entry logic

The following is the most faithful executable ordering available. Items marked [INTERPRETED] connect stated components and must not be mistaken for fully specified source rules.

### Setup A — bearish reversal / short

1. **Select the context.** [STATED] Use NQ as the traded instrument and ES as the comparison instrument. On the Daily chart, identify the relevant broader range and meaningful high/low, including a prior-day high where applicable.
2. **Establish the 50% hypothesis.** [STATED] Mark the 50% midpoint of the relevant range and seek a rebalance toward it. [MISSING] The exact high/low used for the range is not fixed.
3. **Require top-down alignment.** [STATED] Check Daily, H4, and H1 for aligned PO3/range behavior and a common 50% narrative. [MISSING] There is no numerical alignment tolerance.
4. **Wait for the time window when applicable.** [STATED] The analysis emphasizes 09:15–11:30 EST, especially the 09:30 liquidity injection and 10:00 manipulation/reversal. A PM opportunity around 14:00 EST is also mentioned. [MISSING] No hard “do not trade outside” rule is given.
5. **Wait for manipulation/liquidity sweep.** [STATED] Price trades above a relevant prior high. Examples include the 09:00 high, a prior-day high, or an H4 high. [MISSING] No minimum excursion, close/wick requirement, or exact reference-high selection rule is given.
6. **Check SMT.** [STATED] NQ makes a new high while ES fails to make a corresponding new high, showing relative weakness. [MISSING] The exact comparison lookback and timeframe are not defined.
7. **Require rejection back into the range.** [STATED] The manipulated level should be rejected and price should trade back into the internal range; this is described as a change of state of delivery. [MISSING] No exact close/touch/break test is specified.
8. **Require inversion-zone reaction.** [STATED] Price reacts from a prior FVG/inversion zone that has changed from support to resistance. [MISSING] No exact zone boundaries or validity/expiry rule is specified.
9. **Execute one of two stated entry styles.** [STATED] Either place a limit order on the retap of the inversion zone, or place a sell stop below a structural/breakdown level after confirmation. [VISUAL] The reported example uses a sell stop beneath a breakdown candle after the inversion-zone rejection.
10. **Place the short stop.** [STATED] Place it at/just above the manipulation/SMT high. [MISSING] The exact candle, wick/body reference, tick buffer, and whether the stop moves are not specified.
11. **Target the base hit.** [STATED] Use the 50% level of the relevant range/impulse/dealing range. [MISSING] The video evidence contains more than one range description and does not uniquely define the endpoints.
12. **Manage aggressively.** [STATED] Move the stop to break-even once the entry timeframe confirms movement in the intended direction. The reported management phrase is “You either need to be right or right out” (approximately 15:11), and the reported philosophy at approximately 14:15 is “The moment that I can claw this [risk] back is a win for me... I'm very fond of break-even trades.” [MISSING] The precise confirmation candle and timing are inconsistent across evidence; see contradictions below.
13. **Exit.** [STATED] Take the base-hit target at 50%; continuation beyond it is a bonus rather than the required objective. [MISSING] No partial-profit, trailing, time-stop, end-of-session, or runner rule is given.

### Setup B — bullish reversal / long

The video evidence supports the following mirror only at a high level:

1. [STATED/INTERPRETED] Build the Daily/H4/H1 50% context and PO3 alignment.
2. [STATED] Wait for manipulation below a meaningful low, such as a prior-day or structural low.
3. [INTERPRETED] Seek bullish SMT: the traded asset makes a lower low while the comparison asset does not make a corresponding lower low. The exact wording and example are [MISSING].
4. [STATED/INTERPRETED] Require rejection back into the range and a prior resistance-to-support inversion-zone reaction.
5. [STATED] Use a limit retap or buy stop above the confirmed structural/breakdown-equivalent level.
6. [STATED] Place the stop at/just below the manipulation/SMT low.
7. [STATED] Target 50% of the selected range.

The target video evidence does not provide a complete, timestamped long example. Exact long-side wick/close/touch/break rules, invalidation, re-entry, and management are [MISSING].

## 6. Entry execution details

**Limit execution.** [STATED] A limit can be placed on a “re-tap” of the inversion zone after the sweep. [MISSING] The order price within the zone, whether a first touch is required, and whether the zone may be partially filled are not specified.

**Stop execution.** [STATED] A sell stop/buy stop is placed below/above a structural level after confirmation. [VISUAL] The reported short example uses a sell stop under a breakdown candle following rejection of the inversion zone. [MISSING] No tick offset, order-cancellation time, slippage assumption, or rule for a gap through the stop is provided.

**Wick/close/touch/break requirements.** [STATED] The explanation uses sweep, rejection, retap, breakdown, and candle-close language, but the accessible evidence does not resolve which condition is mandatory for each entry type. [MISSING] Do not silently convert “rejection” into a wick-only rule or “breakdown candle” into a close-only rule unless the original audio/chart is rechecked.

## 7. Stops, targets, and management

### Stop-loss rules

**Short.** [STATED] The stop is at the high of the manipulation/SMT event; the analysis also phrases it as “just above the SMT high.” [MISSING] Exact candle identity, whether to use wick high or body high, and the buffer are not stated.

**Long.** [STATED] The mirror is a stop at the low of the manipulation/SMT event, or just below the SMT low. [MISSING] Exact candle, wick/body choice, and buffer are not stated.

**Stop movement.** [STATED] Stop is moved to break-even once the entry timeframe has closed or otherwise confirmed in the intended direction. [MISSING] The source does not specify whether break-even means entry price exactly, entry plus fees/commission, or entry plus a buffer; it also does not specify whether break-even is moved once per trade or can be adjusted again.

### Target

[STATED] The main target is the **50% midpoint** of the applicable key range. The analysis reports the philosophy as taking a consistent base hit rather than pursuing the whole move. [MISSING] The target range is variously described as the key range, impulse move, H1 dealing range, or higher-timeframe range. The precise range-selection algorithm is not recoverable from the available transcript evidence.

### Trade management

[STATED] The model favors early risk removal and accepts many break-even outcomes. [STATED] If price reaches 50% and continues, the extra movement is a bonus, not the core objective. [MISSING] No rule for scaling out, moving a stop after 50%, holding overnight, or closing at a session boundary is given.

## 8. Risk, sizing, and account rules

**Risk philosophy.** [STATED] The speaker emphasizes clawing back risk quickly and being comfortable with break-even trades. The reported quote at approximately 14:15 is: “The moment that I can claw this [risk] back is a win for me... I'm very fond of break-even trades.”

**Position size.** [VISUAL] One reported NQ example used one contract and produced 381 ticks, described as approximately $1,905. [MISSING] There is no general position-sizing formula, percentage-of-equity risk, fixed-dollar risk, maximum daily loss, maximum number of attempts, or contract-scaling rule.

**Risk/reward.** [INTERPRETED] The stated 50% objective and stop location define a trade-specific reward and risk distance, but the video does not state a minimum reward-to-risk threshold. [MISSING]

**Account/prop-firm constraints.** [MISSING] The public description contains sponsor/prop-firm links, but no rule from the target video establishes a drawdown limit, evaluation rule, payout rule, or risk limit. Such marketing content must not be converted into strategy logic.

## 9. Filters and discretion

**Patience.** [STATED] At approximately 18:52, the reported quote is: “It requires a lot of patience... 95% of people really lack this... they open the chart as soon as they wake up.” This affects the decision to wait for the specified setup rather than trade immediately at the start of the day.

**Intuition and repetition.** [STATED] At approximately 15:50, the reported quote is: “I can't teach my intuition... you can only do that through the reps.” This indicates a discretionary recognition skill that the speaker does not reduce to a formal rule. [MISSING] There is no codable threshold for “intuition,” “cleanest setup,” “strong momentum,” or “high probability.”

**Model focus.** [STATED] The analysis says the model should be followed rather than emotions, and that continuation after 50% is a bonus. [INTERPRETED] A discretionary decision is whether the setup is sufficiently clean and aligned before entry; the video does not provide a scoring rubric.

**Premium/discount.** [STATED—DESCRIPTION] The public description says the episode covers “premium/discount zones.” [MISSING] The video evidence available here does not recover the exact rule for how those zones filter longs and shorts, so no additional premium/discount condition is asserted.

**News, volatility, and spread filters.** [MISSING] No explicit news, volatility, spread, liquidity-quality, or instrument-correlation threshold was recovered.

## 10. Trade examples shown or described

The frame-level timestamps were not available because the source video could not be downloaded or played through the available browser session. The examples below are therefore tagged [VISUAL] and include the context reported by multimodal analysis, not independently verified chart coordinates.

### Example 1 — NQ short around 10:00 EST

[VISUAL] Instrument: NQ. Reported timeframes: M3/M15/H1. The setup occurred on a Thursday around 10:00 EST. NQ swept the 09:00 high, ES showed SMT divergence by failing to make a corresponding high, and price traded into an H1 inversion zone. The reported outcome was a win of **381 ticks on one contract**, approximately **$1,905**. [MISSING] Exact entry price, stop price, target price, candle sequence, chart timestamp, and whether the trade used a limit or stop order.

### Example 2 — Bitcoin short held about one month

[VISUAL] Instrument: Bitcoin/BTCUSD, with Weekly and Daily context. A Weekly PO3 was described, followed by a Daily rebalance toward 50%. SMT divergence was reported against Ethereum near the high. The trade was held for approximately one month, with price moving from around 100,000 toward the 50% target. [MISSING] Exact dates, exchange/symbol, entry, stop, size, target calculation, and whether the position was spot, perpetual, or futures.

### Example 3 — NQ short with break-even attempt and re-entry

[VISUAL] Instrument: NQ. Reported timeframes: M3/M15. On Monday/Tuesday, price manipulated above an H4 high and SMT formed. The first attempt was stopped at break-even. A second SMT formed and the trader re-entered; the second attempt reached the 50% target. [MISSING] Exact day, prices, candle sequence, whether the first trade was initially profitable before break-even, the re-entry expiry/reset rule, and whether the second setup was a new sweep or merely a retest.

### Example 4 — H1 dealing-range base hit (publisher cross-check)

[VISUAL—CROSS-CHECK ONLY] The publisher’s related strategy page describes a 3-minute execution after H1 PO3, SMT divergence, and an inversion-zone rejection. It says the trade used a sell stop below a breakdown candle, a stop just above the SMT high, and a target at 50% of the H1 dealing range; it further says the 11:00 hourly candle flipped bearish and the stop was moved to break-even before the 50% target was hit [2]. These details align with the target video’s reported model but are not treated as independently verified transcript evidence from the target video.

## 11. Contradictions and alternative rules

1. **Break-even trigger timeframe.** [STATED/CONFLICT] The analysis says break-even occurs when the entry timeframe, “e.g., H1 or M3/M5,” closes in the intended direction. The publisher cross-check specifies an 11:00 H1 candle in its example. [MISSING] A coder cannot know whether the trigger is always H1, always the execution chart, or whichever timeframe the trader subjectively chooses.
2. **Target range.** [STATED/CONFLICT] The target is called 50% of the key range, impulse move, H1 dealing range, or higher-timeframe range. [MISSING] These are not necessarily the same range. The endpoint-selection rule is a material unresolved dependency.
3. **Entry type.** [STATED/ALTERNATIVE] The model allows a limit on the inversion-zone retap or a stop beyond structural confirmation. [MISSING] The video does not state when one is preferred, whether both are valid for the same setup, or whether a limit may be used before a close confirms.
4. **Time restriction.** [STATED/CONFLICT] 09:15–11:30 EST is called the most active window, 10:00 is emphasized, and 14:00 is also described as viable. [MISSING] It is unclear whether the hours are hard eligibility windows or examples of high-liquidity periods.
5. **Long-side completeness.** [STATED/INTERPRETED] The model is presented as bidirectional in principle, but the accessible detailed examples are predominantly shorts. [MISSING] The exact long SMT, inversion, entry, and stop wording is not recoverable.
6. **Sweep confirmation.** [STATED/CONFLICT] The language includes “sweep,” “rejection,” “change of state,” “breakdown,” and “candle closing,” but the mandatory order and close/wick conditions are not fixed. This prevents an unambiguous event-driven implementation.
7. **Discretion versus mechanical rules.** [STATED/CONFLICT] The model is presented as repeatable/mechanical while the speaker also identifies intuition from “reps” as a key edge. [MISSING] No operational definition separates mechanical eligibility from discretionary trade selection.

## 12. Codability check

### Codable with reasonable fidelity

A backtest can represent the following without inventing many new rules: NQ as the primary market; ES as a comparison market; Daily/H4/H1 top-down context; a 50% midpoint objective; a bearish sweep above a selected high and bullish mirror below a selected low; an NQ-versus-ES non-confirmation filter; a prior support/resistance inversion-zone concept; two alternative order styles; a stop near the manipulation extreme; aggressive break-even management; and a base-hit exit at 50%.

### Not codable without explicit assumptions

The following are material blockers: exact range endpoints for each 50% level; exact swing/high/low selection; precise SMT lookback and synchronization; minimum sweep distance; wick versus close requirements; FVG candle definition and validity; inversion-zone boundaries; order price within a zone; stop buffer and wick/body reference; exact confirmation timeframe; expiry/reset and re-entry rules; news/day filters; session timezone behavior; position sizing; partial exits; and the rule for choosing between limit and stop entry.

A faithful implementation should expose these as configurable parameters and run sensitivity tests, rather than hiding assumptions inside code. It should preserve separate variants: **stop-after-breakdown**, **limit-on-retest**, and different break-even triggers. Results from those variants must not be reported as “the video strategy” until the missing rules are verified against the original recording.

## 13. Final verdict

**Verdict: partially specified, conceptually extractable, not yet uniquely backtestable.** The stable core is a multi-timeframe PO3 reversal: identify a meaningful range and midpoint, wait for a high/low manipulation, confirm relative-strength divergence between NQ and ES, observe a rejection/inversion-zone change, enter on either a retap or confirmed structural break, protect beyond the manipulation extreme, move to break-even early, and take the 50% base hit. However, the source evidence available in this environment does not support a complete verbatim transcript or resolve the exact price-action mechanics needed to produce one canonical algorithm. Any coding/backtest that fills the gaps would be an **interpreted variant**, not a complete transcription of the video.

## Explicit ambiguities and blockers

* YouTube transcript/captions and downloadable video were blocked by bot/rate-limit protection.
* Browser access reached a Google unusual-traffic page and the extracted YouTube page reported “Video unavailable.”
* The available multimodal analysis is not a verbatim transcript and did not provide frame timestamps for chart examples.
* Exact Daily/H4/H1 range endpoints and the applicable 50% range are not fixed.
* Liquidity reference selection, sweep distance, wick/close rule, and sweep expiry are absent.
* SMT lookback, timeframe, synchronization, and exact bullish mirror are absent.
* FVG definition, inversion-zone boundaries, mitigation/validity, and order-block/structure definitions are absent.
* Entry-type selection between limit retap and stop breakout is discretionary/unspecified.
* Stop candle, wick/body reference, buffer, fees adjustment, and later stop movement are absent.
* Break-even trigger timeframe and candle confirmation are inconsistent/underspecified.
* No general sizing, percentage risk, daily loss, number-of-attempts, or news filter is stated.
* Long-side examples and full long-side rules are not available.
* Exact dates, chart times, prices, and outcomes for the visual trade examples are not independently verifiable.

## References

[1]: https://www.youtube.com/watch?v=HNuRp9Z1bMs "Worlds BEST NQ Scalper Reveals His A+ Trading Strategy — Chart Fanatics"

[2]: https://www.chartfanatics.com/strategies/smt-divergence-po3 "SMT Divergence+PO3 — Chart Fanatics strategy page"

[3]: https://noembed.com/embed?url=https://www.youtube.com/watch?v=HNuRp9Z1bMs "Public oEmbed metadata for the target YouTube video"
