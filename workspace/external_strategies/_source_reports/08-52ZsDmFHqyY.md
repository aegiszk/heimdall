# Trading Strategy Extraction Report — Chart Fanatics / Steven Dux

## Source and access status

**Video:** [If You Only Watch One Trading Strategy Video, Make It This](https://youtu.be/52ZsDmFHqyY)  
**Video ID:** `52ZsDmFHqyY`  
**Channel:** Chart Fanatics  
**Source URL:** https://youtu.be/52ZsDmFHqyY  
**Reported duration:** approximately 1:07:43 from the public Podwise episode outline.  
**Related creator strategy page:** [Small-Cap Short Statistics](https://www.chartfanatics.com/strategies/small-cap-short-statistics) [1].

YouTube page and captions were not directly retrievable in this environment: `yt-dlp` received HTTP 429/403 responses, the YouTube transcript API reported an IP block, and the browser was redirected to Google's unusual-traffic page. No official caption file was recovered. I therefore used the available multimodal audio/visual analysis output, the public Chart Fanatics strategy page that embeds the same video, the page's timestamped figure captions, and a secondary episode outline. **The timestamped quoted phrases below are short phrases returned by the multimodal video analysis, not a verified verbatim caption transcript.** They are tagged [STATED] only where the analysis explicitly attributes the rule to the speaker; treat quotation fidelity as a blocker requiring manual YouTube verification before production backtesting.

The strategy is a **short-biased small-cap equity playbook with three separate setups**: Gap-Up Short (GS), Bounce Short (BS), and First Red Day (FRD). It is not an ICT/SMC system and contains no FVG, IFVG, order-block, or liquidity-sweep terminology. Those requested concepts are marked [MISSING].

## Executive verdict

The video describes a coherent discretionary framework, but it is **not directly codable without additional definitions**. The broad filters and setup families are reasonably clear. The exact trigger candle, confirmation standard, stop buffer, intraday time zone, target mechanics, and handling of partial exits are not fully specified. The highest-confidence mechanical components are the universe filters, the three setup families, the GS consolidation breakdown concept, the BS historical trapped-volume concept, the FRD consecutive-green-day/range thresholds, and the position-size caps. The lowest-confidence components are the volume-ratio direction, the meaning of “cracks,” the precise FRD starter trigger, and the exact stop/target implementation.

## Evidence legend

- **[STATED]** — rule explicitly spoken in the video according to the multimodal analysis, with a video timestamp and short quoted phrase.
- **[VISUAL]** — information read from a displayed chart/slide or from the creator's timestamped figure/visual description.
- **[INTERPRETED]** — a conservative operational reading needed to connect stated/visual evidence. It is not presented as the speaker's exact rule.
- **[MISSING]** — not supplied by the accessible evidence; do not guess it in a backtest.

## 1. Instruments, market, schedule, and global filters

### Instruments

[STATED, 03:39–03:51] The video presents an initial market-cap range of approximately **$1M–$100M**, float approximately **1M–$50M**, and price **above $3**. Evidence phrases: “initial market cap” and “must be over $3.00.” [VISUAL, 03:39–03:51] The displayed textbook parameter board labels low float as roughly 1–2M, mid float as 2–5M, and larger small-cap float as 5–10M; the public strategy page likewise describes the framework as U.S. small-cap equities.

[STATED, 07:16] FRD candidates may use a market-cap ceiling of **under $200M**. Evidence phrase: “market cap under 200M.” This is an alternative/exception to the $100M global textbook range, not a resolved replacement.

[STATED, 03:16] The speaker describes approximate opportunity frequency and win-rate statistics: GS “50–70 times/year” with “75%+” win rate; BS approximately “30 times/year” with “80%–85%” win rate; FRD approximately “5–10 times/year” with “up to 90%” win rate. These are performance claims, not guaranteed outcomes, and the accessible evidence does not state sample size or test period.

### Sectors and special risks

[STATED, 08:06] Avoid **biotech and energy** because of unpredictable volatility/news. Evidence phrase: “avoid biotech and energy.” [STATED, 08:43] Avoid **Chinese stocks** because of potential halts and extreme slippage. Evidence phrase: “avoid Chinese stocks.” [VISUAL, 08:06–08:43] The slide presents these as exclusions/risk filters, not merely preferences.

### Time, session, timezone, and days

[STATED, 06:19] Most relevant GS volume is described as occurring between **09:30 and 11:30**, and the trader looks for “mass consolidation” in this period. [STATED, 06:36] GS weakness/entry is after **11:00 AM**. Evidence phrase: “cracks the bottom of its consolidation range after 11:00 AM.” [INTERPRETED] These times appear to refer to the U.S. regular session, probably Eastern time because 09:30 is the U.S. equity open, but the video does not explicitly state a timezone. [MISSING] No explicit timezone, weekday filter, holiday rule, market-hours holiday treatment, or news-calendar rule is supplied. [MISSING] No exact pre-market start/end interval is supplied.

### News

[MISSING] No explicit earnings, offering, FDA, merger, halt-news, catalyst, or news-calendar filter is stated. The biotech/energy/Chinese exclusions are risk-category filters, not a complete news policy.

## 2. Global directional bias and concepts

[STATED, 06:55] The bias is overwhelmingly short after an extended move loses momentum. Evidence phrase: “fails to make a higher high and finally closes red.” [STATED, 03:16] The public analysis reports the speaker is approximately “98 99% short.” This is a directional preference, not a long-side setup.

[STATED, 04:31–05:10] BS logic is based on prior holders selling near break-even when price returns to a previous high-volume area. Evidence phrase: “original holders sell to break even.” [INTERPRETED] “Trapped volume” means prior high-volume trading near a price where holders may still be positioned and may sell when price revisits; it is not defined with a specific candle algorithm.

[MISSING] No formal definition of liquidity, buy-side liquidity, sell-side liquidity, sweep, wick sweep, close-through, equal highs/lows, FVG, IFVG, order block, or market-structure break is given. Do not import those concepts from ICT/SMC.

## 3. Setup A — Gap-Up Short (GS)

### Qualification and sequence

[STATED, 04:36] The video gives a broad morning gap range of approximately **70%–1000%**. Evidence phrase: “gaps up 70%–1000%.” [VISUAL, 03:39–05:37] The textbook board emphasizes small initial market cap, low float, price above $3, and a large percentage gap.

[STATED, 05:37 and 06:05] Avoid a same-day GS when pre-market volume exceeds approximately **50M shares** because the trade is too crowded. Evidence phrase: “pre-market volume exceeds 50 million.” [STATED, 06:19–06:36] The required order is: (1) gap up, (2) opening push, (3) mass consolidation during the high-volume morning, (4) volume dries/weakness develops, and (5) price “cracks” the bottom of consolidation after 11:00 AM. Evidence phrases: “mass consolidation” and “cracks the bottom.”

[INTERPRETED] The intended sequence is not to short the opening print. It is to wait for the opening expansion and a defined consolidation, then short the first meaningful breakdown/weakness. [MISSING] The exact consolidation timeframe, number of candles, minimum range, acceptable retests, and whether the breakdown requires a candle close below the range are not specified.

[STATED, 03:16] The setup is described as occurring roughly 50–70 times per year with a 75%+ win rate. [MISSING] No sample period, universe construction, borrow constraints, slippage, or definition of “win” is supplied.

### Entry execution

[STATED, 06:36] Entry follows the “cracks the bottom of its consolidation range” event after 11:00 AM as volume dries out. [INTERPRETED] A conservative backtest proxy would require a short only after an intraday bar closes below the consolidation low, but that close requirement is **not stated**. [MISSING] No order type, limit/market instruction, fill price, locate/borrow rule, partial-entry rule, or maximum chase distance is given.

[STATED, 17:40] Stop is “above the high of the consolidation range.” [MISSING] No tick/percentage buffer, wick-versus-body rule, stop-order type, or movement rule is stated. The public page says the same thing: stop around the consolidation high.

### Target and management

[STATED, 18:19] Average expected fade is approximately **26% from the intraday high**. Evidence phrase: “average expected fade is 26%.” [INTERPRETED] This is an empirical move expectation, not an explicit fixed take-profit level from the entry. [MISSING] No exact target formula, scale-out levels, trailing stop, time stop, end-of-day close rule, or halt-management rule is provided.

### GS failure/success examples

[STATED/VISUAL, 10:09–10:48] **BIRD** is shown as a failed/invalid GS example. The stock had more than 70M shares pre-market; evidence quote: “You do not want to use Gap Up Short... it squeezed all the way up.” Outcome: it squeezed upward rather than producing the desired fade. This example reinforces the >50M pre-market crowding avoidance rule.

[STATED/VISUAL, 11:55–12:08] **EEIQ** is shown as a successful GS example. Evidence: it gapped to approximately $9, spiked to approximately $12, and then faded. [MISSING] Exact entry, stop, cover prices, share size, and realized P&L are not supplied.

## 4. Setup B — Bounce Short (BS)

### Historical level and trapped-volume construction

[STATED, 03:00] Identify a level on approximately a **one-year chart** where a prior massive-volume spike failed. Evidence phrase: “1-year chart level.” [STATED, 06:35 and 09:34] The dollar-block calculation is **trapped volume × resistance price**, with an ideal block of approximately **$150M+**. Evidence phrase: “trapped volume times resistance price.”

[STATED, 04:31–05:10] When price returns months later, prior holders may sell at break-even and create resistance. [VISUAL, 09:34–09:55] The chart shows a prior high-volume advance/consolidation and a later return to the same price area. [INTERPRETED] A BS candidate therefore needs a prior high-volume price zone, later price return toward that zone, and weaker current demand than prior supply.

[MISSING] The speaker does not define how to select the one-year lookback window in calendar days, how to identify the exact level, whether the old volume must be in one candle or a zone, whether volume is adjusted for splits, or how far price may overshoot the zone before invalidation.

### Volume comparison and ratio ambiguity

[STATED, 08:35] Current estimated volume should be significantly lower than trapped volume; evidence example: “10:1 ratio.” [STATED, 08:21–08:31] The video analysis also reports “2:1 to 10:1 volume-to-trapped-volume ratio” and that higher ratios justify larger size. [INTERPRETED] The direction of this ratio is ambiguous: the public strategy page gives an example of 25M old trapped shares versus 10–15M current implied shares, which favors old supply/current demand by roughly 2:1, while the video-analysis wording says volume-to-trapped-volume. The exact numerator/denominator must be manually verified before coding.

[STATED, 09:55] Entry is sized near the historical consolidation/resistance level. Evidence phrase: “size in near the historical consolidation/resistance level.” [INTERPRETED] The level is the area where trapped holders are expected to sell, not a generic moving average or indicator level.

### Entry, stop, and outcomes

[STATED, 08:39] Stop is “above the historical resistance level.” [MISSING] Exact buffer, wick/body reference, close confirmation, maximum overshoot, and whether the resistance zone is the old high or the full consolidation are unspecified.

[STATED, 12:12] Expected fade depends on the approach: if price gaps directly into resistance, approximately **75% retracement** of the move is described; if price builds volume from the bottom into resistance, approximately **50% fade** is described. [INTERPRETED] These are scenario expectations, not necessarily fixed take-profit orders.

[STATED, 12:35] BS is described as about 30 occurrences per year with an 80%–85% win rate. [MISSING] No dataset, win definition, or costs are supplied.

### BS example

[STATED/VISUAL, 15:02–16:21] **ASTC** is shown as a successful BS. The move ran from about $2 to $6 and revisited historical resistance around **$5.60** on lower volume, then faded toward about **$2.50**. [MISSING] Exact entry timestamp, stop fill, covers, share size, and P&L are not available. The page's example describes the same historical high-volume area and weaker current demand.

## 5. Setup C — First Red Day (FRD)

### Qualification

[STATED, 07:30 and 09:03] The runner must have at least **three consecutive green days**, with increasing volume each day. Evidence phrase: “at least 3 consecutive green days with increasing volume.” [STATED, 08:12] Required range is approximately **300%+ over three days** or **1000%+ over two days**. [STATED, 07:16] FRD market cap is under **$200M**.

[STATED, 06:55] The turn is associated with failure to make a higher high and finally closing red. Evidence phrase: “fails to make a higher high and finally closes red.” [INTERPRETED] A red or flat day in the middle resets the consecutive-day count; the public strategy page explicitly states that reset, but the exact spoken timestamp could not be independently verified.

[STATED, 10:13] FRD is described as rare, approximately 5–10 times per year, with win rate “up to 90%.” [MISSING] No sample size or test methodology is given.

### Entry sequence

[STATED, 13:42] The video-analysis output says to enter a **one-quarter starter** on the first red-day close/fakeout. Evidence phrase: “1/4 starter position.” [STATED, 13:51 and 15:01] The remaining **three-quarters** is added on the following day if the morning bounce fails to clear the prior high. Evidence phrase: “morning bounce fails to clear the prior high.”

[INTERPRETED] The intended FRD order is: (1) qualify a multi-day parabolic run, (2) wait for the first red close/weakness, (3) take only a small starter, (4) on the next session add if a bounce cannot reclaim the prior high, and (5) short against the defined failure/consolidation area. [MISSING] It is unclear whether the starter is entered at the close, during the final red-day intraday failure, or only after close; “fakeout” is not defined; and no exact candle timeframe or close-through condition is supplied.

### Stop and targets

[STATED, 14:14] Stop is above the “highest consolidation point of the run.” [MISSING] Exact candle, wick/body choice, buffer, and whether the stop moves after the second entry are not provided. [INTERPRETED] This is a structural invalidation stop: the short thesis fails if the runner reclaims the relevant high/consolidation.

[STATED, 07:32] **SLV** is presented as a successful FRD in which multiple green days were followed by a red-day confirmation and a “massive drop.” [MISSING] Exact entry, stop, target, and P&L are unavailable.

[STATED/VISUAL, 06:13–07:32] The chart appears to show a multi-day parabolic advance, first red-day confirmation, and subsequent decline. [VISUAL] The displayed example is evidence of the sequence, not a quantified rule beyond the spoken thresholds.

## 6. Risk, sizing, and management

[STATED, 13:14] A single position should not exceed **10% of daily float** or **1% of daily volume** to avoid moving the market. Evidence phrase: “do not exceed 10% of the daily float or 1% of the daily volume.” [INTERPRETED] This is an upper cap on shares, not an account-risk percentage.

[STATED, 08:21–08:31] Position size should reflect the strength of the current-volume versus trapped-volume relationship; higher ratios justify larger size. The ratio direction is ambiguous as described above.

[STATED, 13:42–13:51] FRD position staging is 25% starter plus 75% conditional add. [MISSING] No account-level risk-per-trade percentage, dollar risk, leverage rule, margin rule, borrow fee rule, locate availability rule, or maximum loss/day rule is specified.

[STATED, 17:40; 08:39; 14:14] Structural stops are respectively above GS consolidation high, above BS historical resistance, and above FRD highest consolidation point. [MISSING] There is no exact stop buffer, hard-versus-close stop distinction, slippage model, halt plan, or stop movement rule.

[STATED, 18:19; 12:12; 07:32] Targets are expressed as average fades/retracements rather than fixed prices: GS about 26% from intraday high; BS about 75% or 50% depending on approach; FRD a large continuation unwind after red-day confirmation. [MISSING] No partial-profit schedule, trailing logic, time-based exit, end-of-day policy, or forced cover policy is stated.

## 7. Discretionary phrases and their decisions

| Phrase/evidence | Decision affected | Status |
|---|---|---|
| “mass consolidation” (06:19) | Whether the GS has formed a valid base before breakdown | [STATED], but consolidation is undefined |
| “cracks the bottom” (06:36) | GS entry trigger | [STATED], but wick/close/threshold is undefined |
| “as volume dries out” (06:36) | GS confirmation and timing | [STATED], but no volume threshold is defined |
| “crowded” / >50M pre-market (05:37, 06:05) | Skip or reduce same-day GS | [STATED], with explicit approximate threshold |
| “fails to make a higher high” (06:55) | FRD turn confirmation | [STATED], but reference high and timeframe are undefined |
| “fakeout” (13:42) | FRD starter entry | [STATED], but fakeout mechanics are undefined |
| “morning bounce fails to clear the prior high” (13:51, 15:01) | FRD add-on entry | [STATED], but no close/touch requirement is defined |
| “near the historical consolidation/resistance” (09:55) | BS entry location | [STATED], but zone width and overshoot are undefined |
| “significantly lower” / “10:1 ratio” (08:35) | BS qualification and size | [STATED], but ratio direction is ambiguous |
| “highest consolidation point” (14:14) | FRD stop reference | [STATED], but candle selection is undefined |
| “ideal block of $150M+” (06:35, 09:34) | BS quality filter | [STATED], but exact volume/price aggregation is undefined |

## 8. Contradictions and alternative rules

1. **GS gap threshold:** video analysis reports **70%–1000%** at 04:36, while the public creator page says the cleaner GS is generally **more than 100%**. Treat 70% as a broad video range and >100% as the stricter public-page baseline; this must be verified from the recording.
2. **Global market cap versus FRD:** textbook parameters are $1M–$100M, while FRD is reported under $200M. Implement separate setup-specific limits rather than one global cap.
3. **BS volume ratio:** the video-analysis wording says “volume-to-trapped-volume” and “2:1 to 10:1,” whereas the creator page's worked logic is old trapped volume greater than current implied volume (for example, 25M old shares versus 10–15M current shares). Do not code a ratio until numerator and denominator are verified.
4. **FRD entry timing:** “first red day close/fakeout” could mean an intraday close failure, the session close, or a displayed example annotation. The following-day bounce failure is clearer but still lacks candle/close rules.
5. **Stop semantics:** “above” may mean a wick high plus buffer, a body close, or a manual structural level. No buffer is stated.
6. **Targets:** fade/retracement statistics are descriptive averages, not explicit exits. They should not be converted silently into fixed take-profit rules.

## 9. Requested concepts that are absent

- **Liquidity definition:** [MISSING]. Only volume, float, trapped holders, and halt/slippage risk are discussed.
- **Sweep criteria:** [MISSING]. No sweep of highs/lows, wick reclaim, or stop-run definition is supplied.
- **FVG/IFVG:** [MISSING]. No fair-value-gap rule is stated or shown.
- **Order block:** [MISSING]. No order-block definition is stated or shown.
- **Structure definition:** [MISSING]. “Consolidation,” “higher high,” and “resistance” are used visually/discretionarily, without formal swing algorithms.
- **Long setup:** [MISSING]. The framework is short-biased; no long entry model is described.

## 10. Codability checklist

### What can be coded with explicit approximations

A research prototype can mechanically screen U.S. small-cap equities for price >$3, market cap/float bands, sector exclusions, gap percentage, pre-market volume, consecutive green days, 300%/1000% range thresholds, and daily float/volume position-size caps. It can also construct candidate GS, BS, and FRD events and log them for manual review.

### What cannot be coded faithfully without new assumptions

A faithful execution backtest cannot be built from the video alone because the exact GS consolidation and “crack” event are undefined; the BS historical zone and ratio direction are undefined; FRD “fakeout” and failed bounce are undefined; no candle timeframe is supplied for triggers; no timezone is explicitly stated; stop buffers are absent; targets are descriptive rather than executable; borrow/locate, halts, slippage, and partial-cover rules are absent; and news/day filters are absent.

### Safe implementation boundary

If coding now, label every assumption as a parameter and run sensitivity tests rather than claiming to reproduce the video. At minimum expose: `gap_threshold`, `consolidation_lookback`, `breakdown_requires_close`, `volume_dryup_definition`, `bs_zone_width`, `bs_ratio_direction`, `frd_starter_trigger`, `frd_bounce_failure_definition`, `stop_buffer`, `target_method`, `partial_exit_schedule`, `timezone`, and `halt/slippage model`. The resulting system would be an interpreted proxy, not the speaker's fully specified strategy.

## 11. Final verdict

The video presents a selective **small-cap short-statistics framework**, not a single universal entry pattern. Its three setups are:

1. **GS:** large gap and opening push, then consolidation and a post-11:00 breakdown as volume dries; skip crowded >50M-pre-market cases.
2. **BS:** return to a one-year historical high-volume resistance/trapped-holder area, with current demand materially weaker than prior trapped supply; short near resistance.
3. **FRD:** at least three consecutive green days and approximately 300% range, or a two-day approximately 1000% range; after first red confirmation, start small and add on a failed next-day bounce.

The evidence supports the high-level strategy and many numerical filters. It does **not** support silently inventing wick/close rules, exact swing definitions, buffer sizes, or exit mechanics. The correct backtesting verdict is therefore: **partially codable for candidate generation; not faithfully codable for execution without manual confirmation or additional assumptions.**

## References

[1]: https://www.chartfanatics.com/strategies/small-cap-short-statistics "Chart Fanatics — Small-Cap Short Statistics"

[2]: https://podwise.ai/episodes/8313988 "Podwise — If You Only Watch One Trading Strategy Video, Make It This"

[3]: https://youtu.be/52ZsDmFHqyY "YouTube — If You Only Watch One Trading Strategy Video, Make It This"

[4]: https://www.deciphr.ai/podcast/steven-dux---trading-27000-to-over-50-million "Deciphr — Steven Dux: Trading $27,000 to Over $50 Million"

## Explicit blockers

1. YouTube blocked direct retrieval from this sandbox with HTTP 429/403 and Google bot-detection; browser navigation was redirected to an unusual-traffic page.
2. No official transcript/caption file was obtained. The YouTube transcript API reported an IP block.
3. Timestamped quotations are short phrases from multimodal analysis and are not verified against an official caption transcript.
4. Exact order execution, candle timeframe, timezone, stop buffers, target orders, partial exits, borrow/locate, slippage, halt, news, and day filters are missing.
5. The BS volume-ratio direction and GS gap threshold have unresolved alternatives.
6. The public creator page is a related primary-source playbook and corroborates the video, but it should not be treated as a substitute for independently verified audio when wording differs.

---

**Report status:** Evidence-rich reconstruction completed with explicit uncertainty labels; manual video/transcript verification remains necessary before coding a claimed reproduction.

[1] [2] [3] [4]
