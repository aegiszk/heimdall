"""Advisory Jev ranking of the next footprint-era experiment (2026-09-22).

Research order only. Jev output is not evidence of edge and cannot change a
pre-registration, a risk limit, or an order path.
"""

from __future__ import annotations

import json

from meta.jev_strategy_triage import StrategyCandidate, triage_strategies


PROJECT = {
    "primary_target": (
        "LucidTrading 50K FLEX using CME micro futures, one-session positions, "
        "deterministic Heimdall risk engine, no live orders during research"
    ),
    "available_data": (
        "Two years (515 RTH sessions) of MNQ/MES/ES one-minute OHLCV without bid/ask volume. "
        "Sierra NQ one-tick trades aggregated to 3,850,741 minute/price footprint cells covering only 146 RTH "
        "sessions (2026-02-27 to 2026-09-21). 90 days of one-minute bid/ask volume for twelve CME futures. "
        "No MBO/order-book depth and no trusted quote fields. A once-per-session strategy on the 146-session "
        "footprint archive can produce at most about 58 untouched-holdout trades."
    ),
    "settled_constraints": (
        "Dead: funding carry, cross-venue spread, liquidation cascade, VWAP reversion, trend pullback, plain ORB, "
        "daily breakout, indicator filters, swing breakout, null-entry scalp, Fabio IVB, Okala 80/20, absorption v1 "
        "(prior-session 68% value-area levels plus delta absorption), footprint absorption v2, initiative "
        "continuation v3, LuxAlgo POC sweep reclaim (its close-volume POC proxy matched true footprint POC in only "
        "2.7% of five-minute bars), and the Casper opening-range FVG scalp. Dhesi FVG inversion is sparse and "
        "unvalidated. The MNQ two-year holdout has already been read by three experiments and the footprint "
        "holdout by one, so every new test adds multiple-testing burden. A coin-flip setup loses about "
        "$1.60 per trade to stop slippage, so a real directional edge is required."
    ),
}


CANDIDATES = (
    StrategyCandidate(
        "va_reacceptance",
        "Prior-session value-area re-acceptance (auction-market 80% rule)",
        "Two-stage. Stage 1 measures, before any returns, whether prior-session 70% value-area edges computed "
        "from one-minute close-volume match true footprint value-area edges within 2 ticks on the 146 overlap "
        "sessions. If fidelity passes, Stage 2 runs on the 515-session MNQ archive; if not, only the footprint "
        "sessions are usable and the test is declared underpowered in advance. Signal: RTH opens outside prior "
        "value, price re-enters value, and two consecutive 30-minute periods close inside value. Entry at the "
        "second period close, stop one tick beyond the re-entry extreme, target the opposite value-area edge, "
        "flatten 15:55 ET, one trade per session. Shares the value-area level with dead absorption v1 but uses "
        "time-based acceptance instead of delta absorption.",
    ),
    StrategyCandidate(
        "poor_extreme_repair",
        "Prior-session poor high or low repair",
        "From footprint cells, a prior-session high or low is 'poor' when its extreme price traded in two or more "
        "separate minutes with no single-print excess tail. Next session, after the first 30 minutes, if price "
        "trades toward an unrepaired poor extreme, enter in its direction and target the extreme itself. Entry "
        "trigger and stop still need a pre-registered choice. Footprint-only, so at most 146 sessions; related to "
        "the LuxAlgo unfinished-auction reference-level idea, which defines levels but no trade.",
    ),
    StrategyCandidate(
        "nq_es_delta_divergence",
        "NQ versus ES one-minute delta divergence",
        "When NQ and ES one-minute cumulative delta diverge beyond a trailing percentile while prices move "
        "together, fade the laggard for a fixed 1R. Uses the 90-day bid/ask archive only (about 60 RTH sessions). "
        "Cross-index lead-lag at one-minute resolution is heavily competed and the latency wall already killed "
        "the liquidation-cascade thread.",
    ),
    StrategyCandidate(
        "pause_strategy_research",
        "Pause new strategy tests until execution access is confirmed",
        "Run no new outcome test. Keep both holdouts from further reuse, finish reporting, and wait for written "
        "Lucid confirmation of Rithmic R|Protocol or CQG API access before spending more research effort.",
    ),
)


if __name__ == "__main__":
    report = triage_strategies(PROJECT, CANDIDATES)
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
