# AI Strategy Validation and Orderflow/Gamma Trading: Structured Rule Sheets

---

## Rule Sheet 1: AI Pathways / Strategy Validation Terminal
**Video Title:** "AI PATHWAYS / STRATEGY VALIDATION TERMINAL"
**URL:** https://youtu.be/nLQhKkjkuWI
**Speaker:** Brendan (Math/Econ graduate from UCLA, former investment banker)

### Assessment
**⚠️ IMPORTANT: This video is PURELY EDUCATIONAL/MARKETING content and does NOT provide concrete, codifiable trading rules.** It is a high-level overview of an AI-driven strategy validation system, not a manual for executing trades.

---

### 1. Instrument(s) and Session/Time Windows

The system analyzes 30 liquid assets, including:
*   **ETFs:** SPY, QQQ, and various sector ETFs.
*   **Commodities:** Gold, Oil.
*   **Bonds, Cryptocurrencies (BTC, ETH), and Large-cap Stocks (AAPL, NVDA).**

The analysis is based on **daily bars** using 15 years of historical data (2010–2025). There are no intraday killzones or specific time windows for entry mentioned.

---

### 2. Exact Entry Setup

**No exact entry setup is provided.** The speaker discusses testing "every popular strategy in its base form" (Trend Following, Mean Reversion, Momentum, Breakouts) using AI, but does not define the specific mechanical triggers (e.g., specific indicator values).

He identifies **Mean Reversion** (specifically **RSI Revert** and **Keltner Revert**) as the most robust category across the 15-year dataset, but the exact parameters for these are not disclosed.

---

### 3. Stop Placement Rule

**Not mentioned.** The video focuses on the statistical validation of strategies rather than the mechanics of individual trade execution.

---

### 4. Target Rule and Trade Management

**Not mentioned.**

---

### 5. Risk Per Trade or Sizing Rule

**No specific rules provided.** The speaker mentions that a necessary layer for any strategy is "Risk Management & Sizing" to "cap the tail" and "size to volatility," but he does not provide the actual formulas or percentages used in his terminal.

---

### 6. Filters & Avoidance Rules

The speaker uses a **"Validation Funnel"** to filter out weak strategies during the backtesting process:
*   **Sharpe Ratio:** Must be > 0.5 on unseen data.
*   **Drawdown:** Must be < 35%.
*   **Overfitting Check:** Sharpe Ratio must be < 2.5 (to ensure results are realistic) and the Out-of-Sample Sharpe must be within a certain range of the In-Sample Sharpe.
*   **Sample Size:** A minimum of 30 trades per strategy.

---

### 7. Discretionary / Feel-Based Elements ⚠️

The speaker suggests using a **Market Regime** filter (such as a Hidden Markov Model) to decide which strategy type to deploy:
*   **Momentum/Trend Strategies:** Deploy during trending or bull markets.
*   **Mean Reversion Strategies:** Deploy during "choppy" or ranging markets.

The decision of which regime the market is currently in appears to be the primary discretionary or model-driven filter.

---

### 8. Specific Live Trades Shown

**None.** The video displays backtest results, scatter plots, and performance metrics, but no individual live trade executions.

---

### Summary

This video is a **conceptual overview** of using AI for backtesting and strategy validation. It lacks the specific parameters (e.g., "Buy when RSI(14) crosses below 30") required to codify a functional trading system.

---

---

## Rule Sheet 2: Fazz's Orderflow + Gamma GEX + Volume Profile Strategy
**Video Title:** "MY COMPLETE ORDERFLOW + GAMMA GEX LEVELS + VOLUME PROFILE STRATEGY"
**URL:** https://youtu.be/I81JTRDOR5M
**Speaker:** Fazz (Menthor Q platform)

### 1. Instrument(s) and Session/Time Windows

**Instrument:** Nasdaq 100 Futures (NQ).

**Time Windows:**
*   **Overnight Session (18:00 - 09:30 ET):** Used to draw the Overnight Volume Profile.
*   **Cash Session (09:30 - 16:00 ET):** Used for determining bias and intraday profiles.
*   **Execution Timeframe:** 1-minute chart for entry confirmation.

---

### 2. Exact Entry Setup

The setup requires four conditions to align in a specific order:

1.  **Gamma Regime (Bias):** Determine the regime via the Menthor Q platform.
    *   **Positive Gamma:** Expect a "balanced," "choppy," or "stable" market. Ideal for mean reversion/failed auction setups.
    *   **Negative Gamma:** Expect a "trending" and "volatile" market. Ideal for breakout setups.
2.  **Key Levels:** Identify Gamma GEX levels (GEX 1-5), Call Resistance 0DTE, Put Support 0DTE, and HVL (High Volume Level).
3.  **Volume Profile Context:** Use the overnight session profile (18:00 - 09:30).
    *   **For Shorts:** Price must be above the Value Area High (VAH) in a positive gamma regime.
    *   **For Longs:** Price must be below the Value Area Low (VAL).
4.  **Orderflow Confirmation:** Wait for price to tap a GEX level outside the Value Area.
    *   **Trigger Quote:** "What we need to see guys is absorption of buyers... a lot of buyers stepping in but getting no follow-through... and then we see aggressive sellers on the order flow stepping in, aggressive delta, and they are getting a follow-through."

---

### 3. Stop Placement Rule

Stops are placed based on the candle cluster where the order flow confirmation occurred.
> "Put our stops right above here" or "stops right below here," referring to the high/low of the rejection candle where absorption and aggressive delta were observed at the key level.

---

### 4. Target Rule and Trade Management

Targets are based on key volume profile levels or fixed ratios.
*   **Volume Targets:** "You can target the value area high," or "target the other level" (e.g., the next GEX level).
*   **Fixed Ratios:** Aim for a "1 to 1.5" or "1 to 2 risk to reward."

---

### 5. Risk Per Trade or Sizing Rule

The video does not specify a concrete percentage risk per trade or contract sizing rule. The focus is entirely on the Risk:Reward ratio.

---

### 6. Filters & Avoidance Rules

*   **Bank Holidays:** Consolidation is expected; big moves are avoided. "Since it was a bank holiday this day, I was not expecting a big move."
*   **Regime Filtering:**
    *   **Positive Regime:** Fade the edges (Mean Reversion).
    *   **Negative Regime:** Look for aggressive breakouts. "In a negative regime, we're going to have very strong breakouts above the call resistance."
*   **Level Strength:** GEX 1 is the strongest level, followed by 2 and 3. GEX 4 and 5 are considered "a little weak" but still act as secondary key levels.

---

### 7. Discretionary / Feel-Based Elements ⚠️

*   **Absorption Interpretation:** Identifying "absorption" requires visually assessing volume bubbles on an order flow chart to see if aggressive participants are failing to move price.
*   **Level Conversion:** Manually converting QQQ levels to NQ levels using indicator settings.
*   **General Guidance:** "Use it with discretion... let the price tell you what it's going to do."

---

### 8. Specific Live Trades Shown

**Trade 1 (June 19):**
*   **Setup:** Positive Gamma, price above VAH, tapping GEX 3.
*   **Entry:** After absorption of buyers and aggressive seller delta.
*   **Stop:** Above rejection high.
*   **Target:** 1:1.5 R:R.
*   **Outcome:** Win.

**Trade 2 (June 18):**
*   **Setup:** Positive Gamma, price below VAL, tapping GEX 3.
*   **Entry:** Absorption of sellers followed by aggressive buyer delta.
*   **Outcome:** Win (price returned to VAH).

**Trade 3 (Negative Gamma Example):**
*   **Setup:** Negative Gamma (volatile), bearish bias (POC lower than previous day).
*   **Entry:** Price tapped GEX 1 and VAH, showed absorption.
*   **Outcome:** Win (aggressive trend downward).

---

### Summary

This strategy is a **hybrid mechanical-discretionary system** that combines high-level options market data (Gamma GEX) with traditional Volume Profile and real-time Orderflow confirmation. It provides clear "if/then" scenarios based on the market regime but requires discretionary skill to read the order flow bubbles for final entry.
