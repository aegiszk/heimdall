# Dhesi Trades ICT Strategy: Structured Rule Sheet

This rule sheet is extracted from the Chart Fanatics YouTube video, *"If You Only Watch One ICT Trading Video, Make It This"* featuring Dhesi Trades. It breaks down his specific execution rules, primarily focusing on his "Inversion Model" setup.

## 1. Instrument(s) and Session/Time Window

Dhesi Trades strictly focuses his trading on the S&P 500 (ES) and Nasdaq (NQ). Between the two, he maintains a strong preference for NQ due to its consistent volatility. As he states, "I only trade ES and NQ because I've been most comfortable with them, especially NQ because I just feel like it moves very well, it has enough volatility throughout the day to actually trade... I try not to mingle with too many tickers."

Regarding time windows and killzones, he explicitly avoids the early morning open. He prefers to wait until after 10:00 AM ET when the new 4-hour candle opens, noting, "I try to avoid anything before 10:00 AM... there's so much volatility kicking in and there's no real direction," and "I like to trade during 10:00 AM because it's the new 4-hour candle opening. The new 4-hour candle is very important to me."

While his primary focus is the New York session, he emphasizes that the setup is viable across all global sessions provided there is sufficient market volatility. He explains, "Every session is tradable. There's so much volatility in the market that I can go look at Asia session if this setup is presenting itself, it'll work. London session, it'll work. New York session, it'll work."

## 2. Exact Entry Setup (The Inversion Model)

Dhesi describes himself as a "reactionary trader," meaning he waits for a specific sequence of events to unfold across multiple timeframes before executing a trade. The entry sequence follows four distinct steps.

| Step | Action | Description | Exact Quote |
| :--- | :--- | :--- | :--- |
| 1 | Liquidity Sweep (The Draw) | Price must sweep a major liquidity pool, such as session highs/lows, monthly highs/lows, or equal highs/lows. | "What I look for is session highs and lows, monthly highs and lows, and also when you're looking at equal lows and equal highs. I prioritize monthly highs and lows over all of them just because I feel like they have the higher probability in terms of having a reversal from that area." |
| 2 | HTF Inversion (The Shift) | Following the sweep, price must displace in the opposite direction and completely violate (close through) a Higher Timeframe (4-Hour or Daily) Fair Value Gap (FVG), creating an "Inversion FVG." | "If we go through the fair value gap and the market does not respect it, that to me gives me an indication that that is an inversion fair value gap after a key buy-side liquidity has been taken out." |
| 3 | LTF Retracement | Wait for price to pull back into the newly created HTF Inversion FVG. | "My job as a trader is to play the pullback into our bearish PD arrays on the 15-minute timeframe." |
| 4 | LTF Inversion (Entry Trigger) | As price pulls back on the Lower Timeframe (15m, 5m, or 1m), LTF FVGs will form. The entry is triggered the exact moment one of these LTF FVGs is inversed (violated) in the direction of the new HTF bias. | "Once that lower timeframe fair value gap gets inversed... that's my confirmation. That's where I enter the trade here." |

## 3. Stop Placement Rule

His stop loss placement is strictly dictated by market structure rather than arbitrary point or dollar values. The rule is to place the stop loss just above or below the most recent Lower Timeframe swing high or low that caused the LTF inversion. 

He explains the logic behind this placement: "My stop loss for the day trade would be above the current 15-minute high. Right? We should not retrace back into the 15-minute high because that might lead us into a change in the state of delivery, and our 15-minute inversion... might be inversed and now we're playing on the wrong side."

## 4. Target Rule

Dhesi employs a two-part targeting system that secures a base hit while allowing runners to capture larger structural moves.

For the initial target (TP1), he aims for the nearest opposing liquidity pool, such as local lows or highs, generally securing a 1:1.5 or 1:2 Risk/Reward ratio. He states, "My target would be down here where the current sell-side rests from before."

For the runners target (TP2), he leaves a portion of his position open to target major structural liquidity, such as trendline liquidity or stacked equal lows/highs. He notes, "I let my runners go for 1 to 5, 1 to 10 R trades... I say when the move starts for the downside, all these lows that are stacked are going to get taken out together in one single session."

## 5. Risk Per Trade & Sizing

While Dhesi does not specify an exact fixed dollar amount or percentage of his account risked per trade, he maintains a consistent dollar risk by adjusting his contract size based on current market volatility. He explains, "If your size down, it doesn't matter to you. Right? I'm still risking the same amount, dollar value, it's just I'm sizing down now because the market is moving so much."

His trade management involves a strict trimming rule. He always trims 50% of his position at the initial target (TP1) and immediately moves his stop loss to breakeven. He details this process: "I always trim half. Always, always, always. So let's say I have four contracts here, the market moves down in my favor, I take two off, right? I move my stop loss at break even... Now I'm risk-free."

Furthermore, he adheres to a strict daily loss limit of a maximum of two losses per day. He states, "If I take two losses, and this is something that I haven't changed in years and I don't ever change in trading. If I take two losses, I'm done for the day. If I win one, lose one, I'll give myself a third try."

## 6. Filters & Avoidance Rules

Dhesi utilizes several specific filters to avoid low-probability setups and protect his capital.

| Filter Type | Rule Description | Exact Quote |
| :--- | :--- | :--- |
| Time Filter | Avoid trading before 10:00 AM ET. | "Any move before 10, I'm not too interested in... it just becomes a little bit more... kind of gambling to me, because there's so much volatility kicking in and there's no real direction." |
| Time-in-Gap Filter | If price stalls or chops around inside an inversion gap for too long, the setup is voided or downgraded. | "When the market stays too long in the same gap, to me it takes away from the move... it becomes lower probability." |
| Volatility Filter | Only trade when the market is expanding. Avoid low-volatility environments. | "If this whole thing is happening and the market is only moving 10 points, that's not high probability." |
| Stacked PD Arrays | If an Order Block and a FVG are stacked together, price must violate *both* before considering it a valid inversion. | "The confirmation I'm looking for is a violation of the fair value gap and the order block. Normally if it's just a fair value gap, I'm more than happy taking that, but in this case here, I do need that extra confirmation." |
| Missed Entry | If the initial entry is missed, sit out rather than chasing the trade. | "If I don't get my first entry, I'm usually, that's it for me, right? I'm usually like, okay, I'm just gonna wait for the next session or whatever." |

## 7. Discretionary / Feel-Based Elements ⚠️

Certain elements of Dhesi's strategy rely on trader experience and discretion, making them difficult to strictly code into an automated algorithm.

One such element is timeframe selection. He uses discretion to find the "cleanest" chart for his setup. If the 4-Hour chart appears messy, he will drop to the 1-Hour chart to locate the model. He explains, "I wasn't comfortable with that 4-hour, so I broke it down into an hourly. And I found comfort in that hourly, right? So wherever your model presents itself, whether it's the 4-hour or hourly, as long as it's basing off the higher timeframe... you're fine."

Another discretionary element is the use of SMT Divergence (e.g., ES making a higher high while NQ makes a lower high). He occasionally uses this as an added confluence but does not consider it a mandatory rule for entry. He notes, "I don't use it every single day, but it's an added extra confluence... you gotta look at like ES and NQ and see if one's taken a high and the other one isn't."

---

## Live Trades Shown in Video

The video details two specific live trades executed by Dhesi, demonstrating the application of his rules in real market conditions.

**Trade 1: NQ Day Trade (Short)**
This trade occurred around June 5th, based on the options P&L shown. Executed on the NQ 1-minute chart, the setup began with the market leaving equal lows below. Price rejected a 15-minute bearish FVG, and Dhesi waited for a 1-minute bullish FVG to be violated (inversed) to the downside. He entered short on the close below the 1-minute FVG. The stop loss was placed just above the recent 1-minute swing high, with the target set at the equal lows resting at the bottom of the chart. He trimmed half his position at a 1:2 R/R, moved his stop to breakeven, and let the runners hit the final target. The options P&L for this trade showed a return of +$27,025.05 (+227%).

**Trade 2: NQ Swing Trade (Long)**
This swing trade took place in mid-November (approximately Nov 14th - 17th) and utilized the NQ Daily, 4H, and 1H charts. The market gapped up on the weekly open, leaving a massive gap. Price subsequently sold off to fill the gap, leaving equal lows intact, and tapped into a Monthly bullish FVG and Monthly Order Block. Because the 4H chart was "sloppy," he dropped to the 1H chart. He waited for a 1H bearish FVG to be violated (inversed) to the upside and entered long on the retest of the 1H inversion FVG. The stop loss was placed below the recent structural swing low, targeting relative equal highs resting at the 26,100 level. This massive multi-day swing trade resulted in a 1:5 or 1:6 R/R payout.
