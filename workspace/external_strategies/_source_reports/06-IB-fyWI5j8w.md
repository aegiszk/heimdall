# Complete Trading-Strategy Extraction Report

## Source and acquisition status

- **Source URL:** https://youtu.be/IB-fyWI5j8w (canonical watch URL: https://www.youtube.com/watch?v=IB-fyWI5j8w)
- **Video ID:** `IB-fyWI5j8w`
- **Title:** *TAKE This EASY ICT Trading Strategy For Prop Firms (INSANE Entries)*
- **Channel:** Chart Fanatics
- **Presenter identified in the available analysis:** Omo / NBB Trader.
- **Duration:** Search indexing reports approximately 1:21:53; the available machine video analysis produced evidence through approximately 31:29 and two trade examples. Exact full duration was not independently verified because YouTube blocked direct extraction.
- **Transcript status:** **No verbatim transcript was obtained.** `yt-dlp` was installed and attempted, but YouTube returned “Sign in to confirm you’re not a bot.” `youtube_transcript_api` was also attempted and returned `IpBlocked`. The browser was redirected to a Google/YouTube unusual-traffic page. The platform speech-to-text utility accepts local files only and could not fetch the URL. Therefore, statements below are based on the available AI video/audio/visual analysis artifact, not a word-for-word transcript. Short quoted phrases are only used where that artifact explicitly reported them; they should be treated as reported wording, not independently verified verbatim audio.
- **Visual inspection status:** The available video-analysis tool reported visual whiteboard/chart content and timestamp ranges. No original media file could be downloaded, so individual chart frames could not be independently paused or OCR-checked.

## Evidence-label convention

- **[STATED]** — the available audio analysis attributes the rule or phrase to the presenter. Each such item has a timestamp and a short quoted phrase as required, but the quote is not independently verified against a verbatim transcript because YouTube was inaccessible.
- **[VISUAL]** — a chart, whiteboard, or annotation reported as visibly shown.
- **[INTERPRETED]** — a mechanical interpretation of the stated/visual material, included only to make the process legible for coding; it is not claimed to be the speaker’s exact rule.
- **[MISSING]** — not established by the accessible evidence; do not fill it in from ICT/SMC conventions.

## Strategy identity and high-level architecture

[VISUAL] **02:23–04:51:** The whiteboard reportedly shows “MMXM + OTE.” The analysis says MMXM is presented as the market-structure/framework component and OTE as the entry component. The framework is a higher-timeframe liquidity/price-delivery narrative; OTE is a Fibonacci retracement zone used after a reversal/displacement leg.

[STATED] **02:23–04:51 — quote: “MMXM + OTE.”** The presenter reportedly identifies the framework as MMXM and the execution as OTE. [MISSING] The transcript is unavailable, so the exact expansion of MMXM and whether every setup must use both components cannot be verified word-for-word.

[INTERPRETED] The intended sequence appears to be: establish higher-timeframe context and liquidity; recognize an accumulation–manipulation–distribution model; wait for reversal/displacement; enter on a retracement into OTE or a lower-timeframe FVG alternative; manage toward the opposite side of the accumulation/liquidity range.

## Instruments and markets

[STATED] **General instrument universe — no exact timestamp in the available artifact:** Forex is the primary market, with USDJPY and EURUSD shown as examples; DXY is also mentioned. [MISSING] The exact allowed watchlist, whether indices/futures/crypto are permitted, and whether the examples are representative or exhaustive are not stated in the accessible evidence.

[VISUAL] The two reported examples are a USDJPY sell and an EURUSD buy. No independently inspectable chart frame was available.

## Timeframes, session, timezone, days, and news

| Item | Extracted rule | Evidence/status |
|---|---|---|
| Higher-timeframe context | 4-hour and Daily charts; the analysis says the presenter limits HTF analysis to at least 4H to avoid lower-timeframe noise/variance. | [STATED] 02:23–04:51 — quote reported as “4H minimum”; [VISUAL] whiteboard/chart discussion. Exact candle-selection method is [MISSING]. |
| Main execution chart | 15-minute chart is preferred for filtering noise. | [STATED] general section; timestamp not independently supplied — quote reported as “15-minute” / “filtering noise.” Exact audio timestamp [MISSING]. |
| Refinement | 5-minute chart is used for a Silver Bullet entry or an FVG inside a 15-minute leg/wick. | [STATED] general section and 11:50–14:43 discussion; quote reported as “wicky” and “5m FVG.” Exact rule wording [MISSING]. |
| Timezone | New York / Eastern Time. | [STATED] general section; exact timestamp [MISSING]. |
| London open window | 02:00–05:00 New York time. | [STATED] general section; exact timestamp [MISSING]. |
| New York open window | 07:00–10:00 New York time. | [STATED] general section; exact timestamp [MISSING]. |
| London close window | 10:00–12:00 New York time, described as relevant especially when high-impact news such as Consumer Confidence is at 10:00. | [STATED] general section; exact timestamp [MISSING]. |
| Typical daily completion | Day profiles often complete by 15:00 New York time. | [STATED] general section; exact timestamp [MISSING]. |
| Trading days | [MISSING] No reliable weekday rule was recovered. |
| News filter | A relationship to high-impact news/Consumer Confidence at 10:00 is mentioned, but whether news is a mandatory filter, a reason to use London Close, or merely contextual is not clear. | [STATED] general section; exact timestamp [MISSING]; operational rule [MISSING]. |
| Session order in examples | Asian range/accumulation, London manipulation, then New York distribution/expansion are shown in the sell model. | [VISUAL] 04:52–09:23. |

## Directional bias and higher-timeframe reference levels

[STATED] **Bias alignment:** The analysis reports that setups should align with higher-timeframe bias; for example, look for an MMXM sell model only when the HTF is bearish. Quote reported: “HTF bias” / “only favor a setup if it aligns.” Exact sentence timestamp [MISSING].

[STATED] **Liquidity/reference levels:** The presenter reportedly uses Previous Day High/Low (PDH/PDL), Previous Week High/Low (PWH/PWL), 4H/Daily Fair Value Gaps, order blocks, breaker blocks, and mitigation blocks as higher-timeframe key levels. Quote reported: “where liquidity rests.” Timestamp **02:23–04:51**.

[VISUAL] **02:23–04:51:** PDH/PDL and PWH/PWL are reportedly written/referenced as places where liquidity rests. [MISSING] The precise definition of liquidity (resting stop orders, equal highs/lows, or another criterion) is not explicitly recoverable.

[INTERPRETED] For coding, “bearish HTF bias” cannot safely be reduced to a single indicator or moving-average test. It should remain a manually supplied state or a separately specified, user-configurable classifier because the video does not define the exact swing/close criteria for bias.

## Core sell-model sequence (reported ordered conditions)

The following is the most complete recoverable order for the main setup. The EURUSD buy example indicates a mirrored bullish version, but the exact mirrored rule set is not fully specified.

1. **HTF location/context.** Price is near or inside a higher-timeframe key level, such as a 4H/Daily FVG, and the directional bias agrees with the intended side. [STATED] General analysis; quote reported as “key level” and “HTF bias.” Exact timestamp [MISSING].
2. **Accumulation.** An initial range forms, illustrated by the Asian range. [VISUAL] **04:52–09:23**; quote reported as “Asian range (Accumulation).” [MISSING] Exact range start/end times, whether Asia must be used every time, and how to calculate its high/low are not specified.
3. **Manipulation/liquidity run.** For a sell, price runs above the Asian high and/or PDH and/or into the HTF key level during London. [VISUAL] **04:52–09:23**. [STATED] General analysis; quote reported as “runs above the PDH.” [MISSING] Whether a sweep requires only a wick, a candle close above, a close back below, or a minimum distance is not defined.
4. **SMR/reversal peak.** A peak forms and price begins shifting away from the manipulation. [STATED] General analysis; quote reported as “Smart Money Reversal (SMR).” [MISSING] The exact swing algorithm and confirmation condition are absent.
5. **Displacement/break.** Price breaks the relevant swing low for a sell with a clean, large-bodied/engulfing candle closing through the level. [STATED] **11:50–14:43** — quote reported as “clean break,” “wicky,” and “displacement.” [VISUAL] The analysis reports side-by-side weak wicky closes versus a large-bodied clean break.
6. **Define the retracement leg.** Draw Fibonacci from reversal high to displacement low for a sell. [VISUAL] **26:28–29:25** reports OTE levels and the 0.90 refinement. [STATED] General analysis; quote reported as “0.62, 0.705, 0.79.” Exact fib-anchor conventions and whether candle wicks or bodies are used are [MISSING].
7. **Entry zone.** Primary OTE levels are 0.62, 0.705 (primary), and 0.79. [STATED] General analysis; quote reported as “0.62, 0.705 (Primary OTE), and 0.79.” [MISSING] Whether any touch qualifies, whether a candle must close in the zone, and whether all three levels are separate orders are not defined.
8. **Secondary entry if the first break is weak.** If the first break is “wicky”/lacks displacement, wait for a later retracement into a 5-minute FVG inside the 15-minute leg. This is called “Silver Bullet.” [STATED] General analysis; quote reported as “wicky” and “Silver Bullet.” [MISSING] The exact required sequence, FVG construction, expiration, and whether this is an alternative to or an add-on to OTE are not fully specified.
9. **Distribution target.** Trade away from the manipulation peak toward the opposite side of the accumulation range, with extensions if momentum is strong. [VISUAL] **04:52–09:23**; [STATED] general risk/target section. [MISSING] Exact target-selection priority when multiple liquidity pools exist.

[VISUAL] **04:52–09:23:** The reported sell diagram is Asian accumulation → London run higher/manipulation into a level → New York expansion/distribution lower. The analysis says to trade the distribution side/right side of the curve, not the counter-directional retracement.

[STATED] **04:52–09:23 — quote: “Only trade the Distribution side.”** This is reported as a central directional restriction. [INTERPRETED] A countertrend long during the retracement is not part of the main sell model.

## Bullish/buy setup

[VISUAL] **EURUSD example, reported as Mar 27–28:** Price was in a Daily FVG, swept PDL during the London/New York transition, formed an SMR/reversal, and displaced through a swing high. The entry used a retracement into a breaker leg/OTE area; price missed 62% but reached a 5-minute FVG (“Silver Bullet”) and then expanded higher.

[INTERPRETED] The bullish mirror would be: bullish HTF context; accumulation; sell-side liquidity run (e.g., PDL/Asian low); bullish reversal; displacement through a swing high; retracement into bullish OTE/breaker or 5m FVG; target buy-side liquidity/opposite range. This mirror is an interpretation, not a fully stated specification.

[MISSING] The video evidence does not establish whether bullish OTE is drawn from displacement low to reversal high, whether the same 0.62/0.705/0.79 values and 0.90 stop refinement apply identically, or exactly which candle/leg defines the bullish breaker.

## Liquidity, sweep, and structure definitions

| Concept | Extracted evidence | Codability status |
|---|---|---|
| Liquidity | PDH, PDL, PWH, PWL and HTF FVG/key-level areas are used as places where liquidity rests/price reacts. | [STATED]/[VISUAL] 02:23–04:51 and general analysis. Exact formal definition [MISSING]. |
| Sweep/run | Sell example runs the Asian high and/or PDH before reversing; buy example sweeps PDL. | [VISUAL] examples. Wick-versus-close, penetration threshold, and reclaim requirement [MISSING]. |
| Accumulation | Asian range in the illustrated day profile. | [VISUAL] 04:52–09:23. Exact time window/range construction [MISSING]. |
| Manipulation | Session run through a range extreme or toward HTF level before reversal. | [STATED]/[VISUAL]. No exact numeric sweep criterion. |
| SMR | Reversal peak/shift after manipulation. | [STATED] general analysis. No deterministic swing definition. |
| Displacement | Large-bodied/engulfing clean break closing through a swing; wicky closes are weak. | [STATED]/[VISUAL] 11:50–14:43. Minimum body size, close location, number of candles, and required follow-through [MISSING]. |
| Structure break | Sell breaks swing low; buy breaks swing high. | [STATED] general analysis and examples. Swing lookback/algorithm [MISSING]. |
| FVG | 4H/Daily FVGs are HTF key levels; 5m FVG can be an entry refinement. | [STATED]/[VISUAL]. The three-candle gap definition, wick/body boundaries, fill rule, and invalidation are [MISSING]. |
| IFVG | [MISSING] No accessible evidence establishes an IFVG rule. Do not import one. |
| Order block | OB is listed among key levels; no construction/validation rule is recovered. | [STATED] general list; operational definition [MISSING]. |
| Breaker block | Displacement through the reversal swing is described as a breaker/block context, especially in the EURUSD example. | [STATED]/[VISUAL]. Exact candle origin, invalidation, and entry boundary [MISSING]. |
| Mitigation block | Listed as a key level only. | [STATED] general list; operational definition [MISSING]. |
| Structure validity | [MISSING] No explicit rule for internal versus external structure, equal highs/lows, fractals, close confirmation, or invalidation. |

## Entry execution

[STATED] Primary entry is a retracement into OTE levels **0.62, 0.705, and 0.79**, with 0.705 identified as primary. Quote reported: “0.62, 0.705 (Primary OTE), and 0.79.” Timestamp: general analysis; the whiteboard OTE drawing is reported at **26:28–29:25**.

[STATED] Secondary/Silver Bullet entry uses a 5-minute FVG inside the 15-minute leg when the first break lacks clean displacement. Quote reported: “If the first break lacks displacement (is ‘wicky’), wait for a second retracement.” Timestamp: general analysis; related displacement discussion **11:50–14:43**.

[MISSING] The evidence does not specify market order versus limit order; whether an entry occurs on first touch, close, or confirmation; whether one may place orders at all three OTE levels; slippage/spread handling; partial fills; entry expiration; maximum bars after displacement; or whether an unfilled OTE order is canceled at session end.

[INTERPRETED] A code implementation should expose these as parameters rather than silently choose values.

## Stop-loss rules

[STATED] The initial stop is at the 1.0/100% Fibonacci level. Quote reported: “1.0 (100%) level.” Timestamp: general risk section; OTE refinement shown **26:28–29:25**.

[STATED] A refined stop may be placed at 0.90/90% after displacement is confirmed. Quote reported: “0.90 (90%) level.” Timestamp: **26:28–29:25**.

[STATED] The rationale reported is that if price reaches 90%, it is statistically likely to reach the 100% stop, so the 90% stop can improve reward-to-risk; a reported illustration changes approximately 1.6R to 2.2R. Quote reported: “90% level” and “100% stop loss.” Timestamp: **26:28–29:25**.

[MISSING] Exact candle/swing/wick/body anchor; whether 1.0 is at the reversal extreme, displacement extreme, or fib extension boundary; any spread/buffer; whether stops are moved immediately or only after a qualifying close; and whether the 0.90 rule is optional, mandatory, or only for a certain setup are not established.

[INTERPRETED] For a conservative backtest, model 1.0 and 0.90 as two separate variants, not as one combined rule.

## Targets and trade management

[STATED] Initial target is the original accumulation low for a sell (or the analogous opposite accumulation extreme for a buy). Quote reported: “original accumulation low.” Timestamp: general risk/target section; sell model **04:52–09:23**.

[STATED] Extension targets are Fibonacci levels **-0.28** and **-0.62** if momentum is strong. Quote reported: “-0.28 and -0.62.” Timestamp: general risk/target section.

[STATED] Move the stop to break-even after price closes beyond the 0.20/20% Fibonacci level with displacement. For the sell this is described as price closing below 0.20. Quote reported: “close below the 0.20 (20%) Fibonacci level with displacement.” Timestamp: general risk/target section.

[STATED] Scaling is allowed only after the first position reaches break-even; a second Silver Bullet entry may risk an additional 1% while the original position is protected. Quote reported: “If a trade is at BE.” Timestamp: **18:28–22:42** and general risk section.

[MISSING] Whether break-even includes fees/spread, whether the original position is partially closed, exact partial-take-profit rules, whether extensions are fixed or discretionary, what “strong momentum” means, and whether all positions share one stop/target are not specified.

## Risk, sizing, frequency, and filters

[STATED] Typical risk is **1%–1.5% per trade**. Quote reported: “1% to 1.5%.” Timestamp: general risk section. [MISSING] Account-equity basis, stop-distance sizing formula, leverage, maximum simultaneous risk, daily loss cap, and whether 1.5% is only for A+ setups are absent.

[STATED] A second entry after break-even may risk an additional **1%**. Quote reported: “additional 1%.” Timestamp: general risk section.

[STATED] **18:28–22:42 — quote: “Frequency is not your best friend.”** The reported guidance is fewer, higher-quality setups, with fewer than 10 trades per month preferred over frequent 1-minute scalping. [MISSING] Whether “less than 10” is a hard limit, a historical observation, or a preference is unclear.

[STATED] **29:26–31:29:** ADR (Average Daily Range), reportedly based on a 5-day average, is used to ensure sufficient room remains for the day’s move. Quote reported: “ADR” and “5-day average.” [MISSING] Exact ADR formula, whether high-low or true range, pip/percentage units, remaining-room threshold, and how it interacts with target selection are absent.

[MISSING] No exact spread, commission, slippage, volatility, market-open, or prop-firm news restriction was recovered. The Consumer Confidence mention does not establish a complete news policy.

## Discretionary language and its decision impact

| Reported phrase/concept | Decision affected | Label and timestamp |
|---|---|---|
| “wicky” | Reject/avoid the first weak break; wait for a 5m FVG/Silver Bullet. | [STATED] general analysis; displacement discussion 11:50–14:43. |
| “clean break” / large-bodied candle | Accept displacement and permit OTE/retracement logic. | [STATED]/[VISUAL] 11:50–14:43. |
| “Bodied candles ‘tell the story’” | Subjective assessment of displacement quality. | [STATED] 11:50–14:43; quote reported exactly in analysis. |
| “strong momentum” | Permit extension targets -0.28/-0.62. | [STATED] general target section; objective test [MISSING]. |
| “higher-quality setups” | Trade less frequently/selectively. | [STATED] 18:28–22:42. |
| “frequency is not your best friend” | Avoid high-frequency 1m scalping. | [STATED] 18:28–22:42. |
| “enough room” based on ADR | Filter out trades whose target/move is too close to expected daily range. | [STATED] 29:26–31:29; exact threshold [MISSING]. |
| “once displacement is confirmed” | Allows 0.90 stop refinement. | [STATED] 26:28–29:25; confirmation test [MISSING]. |
| “when a trade is at BE” | Allows scale-in/additional risk. | [STATED] 18:28–22:42; exact BE convention [MISSING]. |
| “ditch OTE for a Breaker” | Reported as a discretion/subjectivity point in the analysis summary. | [MISSING]/[INTERPRETED] Exact decision rule and timestamp not recovered. |

## Trade examples shown/reported

### Example 1 — USDJPY sell, reported March 4–6

[VISUAL]/[STATED] The reported context is bearish HTF bias with price entering a 4H/Daily FVG. During London, price ran the Asian high into the level (manipulation), formed an SMR peak, and displaced through a swing low. The entry retraced into approximately the 70.5%–79% OTE zone during New York. Price then moved through the 20% level with displacement, the stop was moved to break-even, and the accumulation-low target was reached.

- **Outcome:** reported profitable.
- **Reported return:** approximately **2.5R–3.7R**, depending on the stop refinement.
- **Evidence status:** [STATED]/[VISUAL] general analysis; no exact chart timestamp or independently inspectable frame was available.
- [MISSING] Exact entry time/price, stop price, target price, position size, spread, candle OHLC, and whether the result is gross/net.

### Example 2 — EURUSD buy, reported March 27–28

[VISUAL]/[STATED] The reported context is price inside a Daily FVG. Price swept PDL during the London/New York transition, formed an SMR/reversal, and displaced through a swing high. Price reportedly missed the 62% fib level but reached a 5m FVG/Silver Bullet inside the leg; entry was described as a retracement into approximately 50% of the breaker leg/OTE area. Price expanded higher toward HTF liquidity targets.

- **Outcome:** reported profitable.
- **Evidence status:** [STATED]/[VISUAL] general analysis; no exact chart timestamp or independently inspectable frame was available.
- [MISSING] Exact bullish fib anchors, entry trigger, stop, target, R multiple, time of entry, and whether the 50% breaker-leg reference supersedes or supplements the stated 0.62/0.705/0.79 OTE levels.

[MISSING] No other complete trade examples could be reliably extracted from the accessible artifact. If the 1:21:53 indexed duration is correct, the available analysis may not cover all later examples.

## Contradictions and alternative rules

1. **OTE values versus the EURUSD example:** The general rule lists 0.62/0.705/0.79, but the buy example is reported to use approximately 50% of the breaker leg/OTE area and a 5m FVG after 62% was missed. This may be a separate Silver Bullet/Breaker alternative, but the precedence is not stated. Label: [STATED]/[MISSING].
2. **1.0 stop versus 0.90 stop:** Both are presented. The 0.90 level is a refinement after displacement, not clearly a universal replacement. Backtest as variants. Label: [STATED]/[INTERPRETED].
3. **Clean displacement versus Silver Bullet after a weak break:** The main path requires clean displacement, while a weak/wicky first break may lead to a later 5m FVG entry. The exact reset/expiry and whether the initial weak break invalidates or merely delays the setup are missing. Label: [STATED]/[MISSING].
4. **“Only distribution” versus breaker/OTE retracement:** The model says to trade away from manipulation, yet the entry necessarily retraces toward the reversal leg. The intended distinction appears to be directional objective versus entry pullback, but this is an interpretation. Label: [VISUAL]/[INTERPRETED].
5. **News/session timing:** The London-close/news mention is not sufficient to establish a no-trade news rule. Label: [MISSING].

## Codability check

### What can be encoded without adding outside knowledge

A configurable skeleton can encode: market symbol; HTF source (4H/Daily); execution timeframe (15m); refinement timeframe (5m); New York session windows as reported; manual or externally supplied HTF bias; PDH/PDL/PWH/PWL and selected HTF FVG/key-level inputs; Asian range as a configurable accumulation range; a sell-side manipulation run; a manually or algorithmically supplied SMR swing; displacement through a swing; Fibonacci anchors; OTE levels 0.62/0.705/0.79; optional 0.90 versus 1.0 stop variants; accumulation extreme target; -0.28/-0.62 extensions; 0.20 break-even trigger; 1%–1.5% risk variants; and post-break-even 1% scale-in.

### What cannot be encoded faithfully without additional definitions

The following are blockers to a deterministic faithful backtest: exact session/range boundaries; formal HTF bias; liquidity definition; sweep penetration/close/reclaim criteria; swing/fractal algorithm; displacement body/close thresholds; exact FVG and breaker construction; fib wick-versus-body anchors; touch/close/confirmation entry semantics; pending-order expiration; stop buffer; exact target priority; momentum and ADR thresholds; news rules; position sizing details; partial exits; and complete trade-example data.

### Suggested non-fabricating implementation modes

1. **Strict mode:** Require manual labels for bias, key level, manipulation, SMR, displacement, and FVG/OB/breaker; only automate fib levels, risk arithmetic, stop variants, target levels, and break-even logic.
2. **Parameterized research mode:** Implement every ambiguous item as a parameter grid and report sensitivity; do not select a default as though it came from the video.
3. **Evidence mode:** Store each signal with its evidence label and source timestamp, and keep the OTE, Silver Bullet, 1.0-stop, 0.90-stop, and 50%-breaker alternatives as separate setup IDs.

## Final verdict

The recoverable strategy is a **higher-timeframe MMXM/accumulation–manipulation–distribution framework with 15-minute reversal/displacement confirmation and OTE retracement entries, plus a 5-minute FVG/Silver Bullet alternative**. The strongest explicit numeric rules recovered are OTE **0.62/0.705/0.79**, initial stop at **1.0**, optional refined stop at **0.90** after displacement, target at the accumulation extreme with possible **-0.28/-0.62** extensions, break-even after a displaced close beyond **0.20**, typical risk **1%–1.5%**, and a possible additional **1%** only after the first trade is at break-even. However, the strategy is **not fully deterministic from the accessible evidence**. The missing transcript, inability to download the original video, unformalized liquidity/structure/displacement/FVG definitions, and unresolved OTE-versus-breaker/Silver-Bullet precedence mean that a faithful coding/backtest requires explicit manual labels or user-approved parameterization. No ICT/SMC definitions beyond what the video analysis reported have been imported.

## Explicit ambiguities and blockers

- YouTube bot verification prevented `yt-dlp` metadata/subtitle/media retrieval.
- `youtube_transcript_api` was blocked by the network/IP.
- Browser navigation was redirected to an unusual-traffic page.
- No verbatim transcript is available; timestamped quotes are reported by an AI video-analysis artifact and are not independently transcript-verified.
- Original chart frames/video could not be downloaded for independent visual inspection.
- Available analysis evidence ends around 31:29 despite search indexing indicating approximately 1:21:53; later material may be unexamined.
- Exact definition of MMXM, SMR, liquidity, sweep, displacement, FVG, IFVG, OB, breaker, mitigation block, and structure is incomplete.
- Exact timezone/session boundaries, weekday policy, and news policy are not fully operationalized.
- Exact entry touch/close/order semantics, expiry/reset, stop anchors/buffers/movement, targets/partials, sizing, ADR formula/threshold, and all trade-example prices/outcomes are missing.
- No reliable IFVG rule was recovered; none has been invented.

## Acquisition artifacts

- `/home/ubuntu/jobs/2bac636f9c3a_a5/video_IB-fyWI5j8w_analysis_20260923_155717.md` — available AI visual/audio analysis artifact.
- `/home/ubuntu/jobs/2bac636f9c3a_a5/video_analysis.txt` — analysis invocation log.
- `/home/ubuntu/jobs/2bac636f9c3a_a5/transcript.log` — transcript API failure log.
- `/home/ubuntu/jobs/2bac636f9c3a_a5/metadata.log` — yt-dlp bot-verification failure log.
- `/home/ubuntu/jobs/2bac636f9c3a_a5/thumb.jpg` — downloaded YouTube thumbnail; not sufficient to verify the video’s chart examples.

*Report prepared from the accessible evidence only; absent details are intentionally marked [MISSING] rather than inferred from outside trading knowledge.*
