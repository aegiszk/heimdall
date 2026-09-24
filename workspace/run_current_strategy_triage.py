"""Run advisory Jev triage over current YouTube and LuxAlgo candidates."""

from __future__ import annotations

import json

from meta.jev_strategy_triage import StrategyCandidate, triage_strategies


PROJECT = {
    "primary_target": (
        "LucidTrading 50K FLEX using CME micro futures, one-session positions, "
        "deterministic Heimdall risk engine, no live orders during research"
    ),
    "available_data": (
        "Two years of MNQ/MES/ES one-minute OHLCV; 90 days of Sierra NQ/MNQ/ES/MES/GC/MGC/CL/MCL/RTY/M2K/YM/MYM "
        "one-minute bid/ask volume; 67,772,289 Sierra NQ one-tick trade records with trade price, total/bid/ask volume. "
        "No MBO/order-book queue depth and no trusted quote-high/quote-low fields."
    ),
    "settled_constraints": (
        "Generic VWAP reversion, trend pullback, plain ORB, daily breakout, order-flow absorption, footprint reversal, "
        "and initiative continuation already failed. Dhesi FVG inversion is a sparse unvalidated candidate. "
        "Do not infer profitability, retune killed strategies, or use overnight strategies until permission is verified."
    ),
}


CANDIDATES = (
    StrategyCandidate(
        "youtube_supply_demand",
        "TradingLab validated-swing supply/demand retest",
        "Trend uses a swing low only after it breaks the prior high, mirrored for shorts. Zone is the full candle before an impulse. Enter on retest, stop beyond zone, target recent extreme, require at least 2.5R. 'Impulse', consolidation, swing selection, and recent extreme are not numerically defined.",
    ),
    StrategyCandidate(
        "youtube_open_fvg_scalp",
        "Casper 5-minute opening-range FVG scalp",
        "At 09:30 ET mark first 5-minute high/low. On 1-minute bars require a three-candle FVG through a boundary, retest, then body engulf of the retest candle. Enter on engulf close, stop one tick beyond deepest FVG retest, fixed 3R target. Entry cutoff, first-signal policy, exact FVG boundary, and same-bar fill ordering are unstated.",
    ),
    StrategyCandidate(
        "youtube_open_fvg_day",
        "Casper 15-minute opening-range FVG day trade",
        "Mark 09:30-09:45 ET high/low. On 5-minute bars require a three-candle FVG through a boundary. Place limit on the FVG, stop below or above the first candle in the pattern, fixed 2R target. Exact limit price within the gap, entry cutoff, first-signal policy, and same-bar fill ordering are unstated.",
    ),
    StrategyCandidate(
        "youtube_po3",
        "JackTrades 10:00 ET four-hour PO3",
        "At 10:00 ET seek 1-minute accumulation, manipulate into nearest 15-minute or fallback 5-minute FVG while forming the four-hour extreme, then require opposite FVG disrespect and a new 1-minute FVG that holds. Stop at four-hour manipulation extreme; target 1R-2R or accumulation high. Directional narrative, accumulation, timeframe fallback, respect, and target are discretionary. The sequence overlaps Heimdall's existing Dhesi FVG inversion family.",
    ),
    StrategyCandidate(
        "youtube_maine_multitf",
        "Trader Mayne multi-timeframe FVG/dealing-range reversal",
        "Weekly structure and premium FVG set bias; daily structure must align; H12/H1 sweep, breaker, FVG and market-structure shift trigger; optional 5-minute refinement. Stop above sweep, first partial near 2R, runner to higher-timeframe liquidity. Video is one BTC swing example and depends on 23 prior lessons. Overnight permission is unresolved and current Sierra archive is CME futures, not BTC.",
    ),
    StrategyCandidate(
        "youtube_hpr_rectangle",
        "Mulham high-probability-range rectangle setup",
        "On 15-minute bars find weakness at a prior extreme followed by aggressive break of opposite structure, then a pullback into an imbalance/key level. A same-direction wick sweep defines a body-to-wick rectangle; enter when a 1-minute candle closes beyond it, stop beyond rectangle/new high, target a nearby swing. Swing, aggressive break, key-level choice, placement, and target remain discretionary.",
    ),
    StrategyCandidate(
        "lux_poc_reclaim",
        "LuxAlgo POC Sweep Reclaim",
        "Public Pine source computes each parent candle POC from lower-timeframe close-volume. Current bar wicks through prior POC while its body stays inside; next bar must close beyond the swept POC. Signal logic is exact and NQ tick data can compute a truer price-volume POC, but source specifies no complete entry timing, stop buffer, target, session, or daily trade limit.",
    ),
    StrategyCandidate(
        "lux_session_sweep",
        "LuxAlgo Session Sweep & iFVG RR",
        "Public Pine source tracks fixed session range, requires an ATR-capped break and return inside within 10 bars, then a deterministic pivot trendline break. Default stop uses largest qualifying inverted FVG or ATR fallback and target is 2 ATR. Full source is available, but its trade direction naming and iFVG stop geometry require source-level audit before porting. It overlaps liquidity-sweep/FVG logic already present in Dhesi.",
    ),
    StrategyCandidate(
        "lux_unfinished_auction",
        "LuxAlgo Unfinished Auction references",
        "Public Pine source labels completed-session highs/lows lacking an excess tail using TPO count, single-print tail, optional volume ratio, and closing-bell exception; levels persist until repaired. NQ tick and one-minute data can reproduce better price-level profiles. The indicator identifies reference levels only and does not define a trade entry, stop, target, or maximum holding time.",
    ),
    StrategyCandidate(
        "lux_asia_sweep",
        "LuxAlgo Asia Sweep Reversals",
        "Library indicator tracks Asia session high/low, a sweep, then BOS/CHoCH and risk boxes. Futures data covers overnight sessions, but full source and exact defaults still require audit. It is a session-liquidity reversal and may overlap Dhesi/ICT rather than add an independent portfolio edge.",
    ),
)


if __name__ == "__main__":
    report = triage_strategies(PROJECT, CANDIDATES)
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
