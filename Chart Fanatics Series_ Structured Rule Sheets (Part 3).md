# Chart Fanatics Series: Structured Rule Sheets (Part 3)

This document presents a technical breakdown of trading strategies extracted from five professional trading interviews. Each strategy is organized into a structured rule sheet focusing on codifiable parameters, verbatim quotes, and specific trade management protocols.

---

## Rule Sheet 1: John Einar Sandvand's 0DTE Breakeven Iron Condor
**Video Title:** "0DTE Breakeven Iron Condor Strategy" (Theta Profits)
**URL:** https://youtu.be/Fj41ojAdwJ8
**Speaker:** John Einar Sandvand

### 1. Instrument(s) and Session/Time Windows
The strategy is executed exclusively on **SPX (S&P 500 Index) options** using a **0DTE (Zero Days to Expiration)** timeframe. Sandvand employs a systematic approach to entry, distributing trades throughout the trading day. The initial entry typically occurs 10 to 15 minutes after the market open, once volatility has stabilized. Subsequent entries are placed at hourly intervals, specifically at 1:00 PM, 2:00 PM, and 3:00 PM ET. He emphasizes that statistical data indicates the final three hours of the trading session are the most profitable for this specific model.

### 2. Exact Entry Setup
The core of the entry relies on a **Stabilization Rule**, where the trader waits for the market to exhibit minimal directional movement. Sandvand states, "Enter trades when the market has stabilized a bit, for instance when you see 2-3 five-minute candles at more or less the same level." The execution involves selling an Iron Condor by entering one credit spread at a time—usually the call side first, followed immediately by the put side—to ensure the collection of equal premiums.

| Parameter | Specification |
| :--- | :--- |
| **Short Strike Selection** | Typically between 10–15 Delta |
| **Premium Target** | Equal premium per side ($100–$200); $200–$400 total |
| **Spread Width** | Standard starting width of 30 points |
| **Execution Method** | Legging in (Call side first, then Put side) |

### 3. Stop Placement Rule
The stop loss protocol is highly mechanical and designed to protect against large directional moves while allowing time decay to work. Sandvand defines the rule as follows: "The stop loss is set separately on the call and the put side — equal to the total premium collected for the full Iron Condor." Stops are placed only on the short options using **OCO (One Cancels Other)** orders, consisting of a Stop Limit order with a 40-point buffer and a Stop Market order placed 30 points further out as a final safeguard.

### 4. Target Rule and Trade Management
The strategy follows a "set and forget" approach until specific triggers are met. The primary exit rule is to "leave the trade on until the stop loss hits or the shorts reach the value of 5 cents." If a stop loss is triggered on one side, the total premium collected from the opposing side typically offsets the loss, resulting in a breakeven outcome. Upon a stop-out, the remaining long option is generally closed immediately, though it may be held briefly if market momentum suggests it could gain enough value to contribute to a profit.

### 5. Risk and Sizing
Sandvand maintains strict capital preservation rules. He advises to "never risk more than 1-2% of your account on any single day with this strategy — as measured by your stop losses." Furthermore, he restricts the use of available buying power to a maximum of 50% on any given day. A typical day involves managing between 6 and 10 simultaneous Iron Condor positions.

### 6. Filters and Discretionary Elements ⚠️
The primary technical filter is the **Stabilization Filter**, which uses 5-minute candle patterns to avoid entering during high-momentum moves. Discretionary elements include the judgment of market "stability" and the management of the remaining long leg after a stop-out. Sandvand also applies a **Risk Filter**, skipping new entries if existing positions are under threat or if the daily risk limit has been reached.

---

## Rule Sheet 2: Tyler Goedtel's 1:175 RR EMA Strategy
**Video Title:** "The 1:175 RR Strategy Breakdown" (TG Capital)
**URL:** https://youtu.be/ADnslyKOwFE
**Speaker:** Tyler Goedtel

### 1. Instrument(s) and Session/Time Windows
Tyler Goedtel focuses on major **USD pairs**, including USDCAD, NZDUSD, EURUSD, GBPUSD, and USDJPY, as well as **Gold (XAUUSD)**. He explicitly avoids AUDUSD due to poor historical performance. His trading is strictly confined to the **London Killzone**, specifically between **3:00 AM and 6:30 AM ET**. He does not look for new entries after the 6:30 AM window closes.

### 2. Exact Entry Setup
The strategy is a high-reward trend-following model that aligns lower-timeframe entries with higher-timeframe narratives. A trade is only valid if price is above the **200 EMA** for longs or below it for shorts. Furthermore, the 5, 9, 13, and 21 EMAs must be "stacked" in perfect order and not intertwined. The entry sequence, which he calls the **Trident Pattern**, involves the following steps:

1.  **FVG Formation:** A Fair Value Gap (FVG) must print, typically on the 3:00 AM candle.
2.  **Doji Rejection:** "I look for... a doji candle... and it's going to [have] a wick that wicks through it [the FVG]... the consequent encroachment or the 50% [level]."
3.  **Indicator Confirmation:** Using the "[BullTrading] 1m Easy Scalping Sys V3.0," candles must be colored bright green or black for longs.
4.  **Validation:** "The next candle after this doji candle closes below this high... if it closes above the high I'll invalidate the trade."

### 3. Stop Placement and Risk Management
For USD pairs, Goedtel uses a **10-pip hard stop** placed "below this candle low here [the entry/doji candle]." However, for Gold, he states, "I don't use a hard stop loss. I will wait for a close below this candle," to avoid being stopped out by volatility wicks. He targets a minimum Risk-to-Reward (RR) of **1:20**, with his primary target being higher-timeframe liquidity zones identified on the Daily chart.

### 4. Trade Management and Filters
Trade management is based on trend persistence. He advises to "ride the trend until like the EMAs crossover or if I get like a... strong bearish candle [or an Inverted FVG]." The primary filter is **HTF Alignment**; entries must align with the Daily chart narrative. If the EMAs are crossing or intertwined, it is considered a low-probability condition and the trade is skipped.

### 5. Discretionary Elements and Live Trades ⚠️
Exit management involves a degree of intuition, as he monitors the tape for signs of trend exhaustion. A notable trade shown in the video is a **USDCAD Long** from October 8, 2024, which entered at 3:30 AM ET and resulted in a **175R payout**. Another example on **USDJPY** from November 12, 2024, demonstrated a similar expansion after price wicked into the 50% level of a 30-minute FVG.

---

## Rule Sheet 3: Pat's One-Minute Scalping Strategy
**Video Title:** "ONE MINUTE SCALPING STRATEGY" (Trad with Pat)
**URL:** https://youtu.be/aKD4qOKvU5c
**Speaker:** Pat

### 1. Instrument(s) and Session/Time Windows
This scalping strategy is applied across **Futures, Forex, Crypto, and Stocks**, with specific focus on US100 (Nasdaq), US30 (Dow Jones), Bitcoin, and Gold. The strategy is centered entirely on the volatility generated by the **9:30 AM EST candle**, representing the US stock market open.

### 2. Exact Entry Setup
The entry setup is a four-step mechanical process designed to identify and trade opening range manipulation:

1.  **Opening Range:** Identify the high and low of the 15-minute 9:30 AM EST candle once it closes.
2.  **Fibonacci Application:** Mark the top and bottom of this candle and extend the Fibonacci levels.
3.  **ATR Confirmation:** Use the **ATR Candle Size indicator** (Length 96). "If the candle is larger than the ATR, it signals an unusually large move. My calculation is a simple 100% of ATR."
4.  **Directional Trigger:** If the 9:30 candle is bearish, place a buy limit order at the range bottom. If the candle is bullish, place a sell limit order at the range top.

| Step | Action |
| :--- | :--- |
| **Identify Range** | Mark 15-min 9:30 AM Candle High/Low |
| **Filter** | 15-min candle body > ATR line |
| **Execution** | Switch to 1-min chart for Limit Order placement |
| **Entry Point** | Range Boundary (Top for Sells, Bottom for Buys) |

### 3. Stop Placement and Targets
Pat suggests a flexible stop loss, stating, "For the stop loss, we can go with a one to one, you can go with a one to 1.5, but ideally you look left and if there's some sort of price action here, you can adjust the stop loss accordingly." The primary targets are the **38.2% and 61.8% Fibonacci levels**. Once the first target is hit, the trader should "set my stops to break even, make this a risk-free trade."

### 4. Discretionary Elements and Filters ⚠️
The primary filter is the **ATR Confirmation**; if the opening candle is smaller than the ATR line, the trade is skipped. Discretionary elements include adjusting the stop loss based on historical price action ("looking left") and choosing to hold for extended targets based on higher-timeframe supply and demand zones.

---

## Rule Sheet 4: Trader Yush's Order Flow Strategy
**Video Title:** "Trader Yush Interview" (ChartFanatics)
**URL:** https://youtu.be/hvyf6frvCcA
**Speaker:** Trader Yush

### 1. Instrument(s) and Session/Time Windows
Trader Yush specializes in **NQ (Nasdaq futures)** using a 2-minute timeframe and **ES (S&P 500 futures)** using a 3-minute timeframe. He exclusively trades the **New York Session (9:30 AM – 4:00 PM EST)**. While he does not trade the overnight session, he utilizes levels generated between 9:00 PM and 9:29 AM EST to establish his intraday context.

### 2. Exact Entry Setup
Yush defines his "Areas of Interest" using four specific criteria, requiring at least two to align for a valid trade:
1.  **Market-Generated Levels:** PDH/PDL, OVH/OVL, and the 30-second ORB High/Low.
2.  **Volume Profile:** Value Areas and Low Volume Nodes.
3.  **Big Trades Indicator:** Filters for large orders (75+ lots for NQ, 200+ lots for ES).
4.  **Delta Profile:** Identifying Absorption and Trapped Participants.

For a **Range Reversal**, he waits for price to reach the edge of a Value Area and looks for a "false breakout." He states, "If I see absorption... or aggressive buyers coming in but there's not much follow-through... this is an aggressive entry." For **Trend trades**, he enters on pullbacks into Low Volume Nodes once aggressive participants on the wrong side are confirmed trapped.

### 3. Trade Management and Risk
Yush employs tight stops based on the immediate rejection candle, stating, "I'll put a stop just below this wick low [or above the wick high]." His first target is the midpoint of the range, at which point he moves the stop to breakeven: "Immediately after this TP is hit... my stop would go break-even... Never let a trade that's working go red." He typically risks **15 points to target 60+ points**.

### 4. Filters and Discretionary Elements ⚠️
He strictly avoids trading in the middle of a range, calling it a "No-Trade Zone." Discretionary elements include **Tape Reading** via the DOM to judge market speed and adjusting the "Big Trades" filter based on current market liquidity. He also utilizes high-impact news (CPI/NFP) as a filter to identify days with sufficient liquidity for large liquidation moves.

---

## Rule Sheet 5: Marci Silfrain's "Little Rizzy" Strategy
**Video Title:** "Marci Silfrain Interview" (Chart Fanatics)
**URL:** https://youtu.be/AVVM-FyewLg
**Speaker:** Marci Silfrain

### 1. Instrument(s) and Session/Time Windows
The **"Little Rizzy"** strategy is described as fractal and applicable to all instruments, including QQQ, Bitcoin, SPX, and NDX. While it works on all timeframes, Silfrain prefers the Daily, Weekly, and Monthly charts for higher probability. She explicitly avoids the New York session open, stating it is "usually net negative," and prefers the **London open** for her entries.

### 2. Exact Entry Setup
The strategy is based on a **Measured Move** pattern triggered by a trendline rejection:

1.  **Trendline:** Draw a trendline connecting recent lower highs (downtrend) or higher lows (uptrend).
2.  **Anchor Point:** Identify the candle with the lowest low (in a downtrend) or highest high (in an uptrend).
3.  **Measurement:** Measure the vertical distance from that extreme point to the trendline directly above/below it on the same candle.
4.  **Execution:** "You want to come in and draw a trend line... find the low on the candle that had the lowest low... and you measure from right here to the top of the trend line... directly up the same candle... the next move down will be this distance."
5.  **Entry:** Enter on the rejection or bounce from the trendline.

### 3. Stop Placement and Targets
The pattern is invalidated if a candle closes on the opposite side of the trendline: "If the next candle like closed below [for longs] this trend line I would I would get out." The target is a **1:1 extension** of the measured distance. She notes, "I would play the whole move even if it brought me out of reality [Bollinger Bands] because they're that powerful that they usually tend to finish."

### 4. Filters and Discretionary Elements ⚠️
Silfrain uses **Bollinger Bands (2 SD)** as a filter, referring to the area between the bands as "reality." Patterns forming near the outer bands or the middle line are preferred. She also applies a **Mainstream Media Filter**, avoiding trades when a move becomes headline news on CNN, as it suggests the move is "priced in." Discretionary elements include the real-time identification of the correct trendline and judging market exhaustion after multiple consecutive patterns.

### 5. Historical Examples
The strategy has been used to predict major market bottoms, including the 1929 crash, the 2000 Dotcom bust, and the 2020 Covid crash. Current projections mentioned in the video include a Bitcoin target of **~$50,000** and a long-term move for Howard Hughes Holdings (HHH) from $80 to **$175**.
