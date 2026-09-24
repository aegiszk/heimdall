# How to Run Heimdall — Plain English

## What this is
An autonomous crypto trading system with a strict "judge" (the validation battery) that decides which
strategies are allowed to trade. Right now everything runs on **fake test data** so you can see it work
without touching an exchange or any real money.

## What you need
- A computer with Python 3.11 or newer.

## Step 1 — Unzip and open a terminal in the folder
    unzip trading-loop-S0.zip
    cd trading-loop

## Step 2 — Install the libraries
    pip install numpy pandas scipy pytest

## Step 3 — Prove the system is honest (run the tests)
    python -m pytest -q
Expect: "15 passed". This proves, among other things, that the judge REJECTS random noise and only
passes a real edge. If tests fail, stop — something is wrong, do not go further.

## Step 4 — Check the safety wall
    python tools/check_core_purity.py
Expect: "core purity OK". This confirms the trading code cannot secretly depend on the AI layer.
The money path is deterministic; the AI never places or approves a trade.

## Step 5 — Run the demo
    python loop.py
You will see three strategies judged on fake data. The funding-carry strategy PASSES; the other two
are KILLED. That is correct: only the strategy with a real edge is allowed toward real money.
Reading the output:
- DSR  = Deflated Sharpe (must be > 0.95). Corrects for luck and for testing many strategies.
- NWt  = statistical strength of the edge (must be > 2).
- maxDD = worst drop (must be smaller than 8%).
- PASS -> $1-5k rung  = allowed to start with a tiny amount of REAL money, same code.
- KILLED (...)        = failed one or more gates; not allowed to trade. The reasons are listed.

## What is real vs. what is a placeholder
REAL and tested now:
- The validation battery (the judge) and its proof against noise.
- The strategy funnel: wide cheap search, then a strict out-of-sample gate, with a firewall so a
  strategy can never peek at the data it will be judged on.
- The safety wall, the I7 "no real orders while the flag is off" block, the risk-monitor invariants.
Placeholders to finish on YOUR servers (they need live exchange/API access this sandbox does not have):
- Live connectors to OKX / Hyperliquid / Binance (structured, not yet tested against the real APIs).
- The realistic fill model needs calibrating against real order books.
- The AI meta-layer (regime advisory, weekly re-audit of the judge).

## The rule that keeps you safe
No real money moves until a strategy passes the judge on 90 days of paper. Passing only unlocks
$1-5k. It scales to $500k in steps, and only if the LIVE edge keeps matching the paper edge.
See truth/LIVE_GATE.md. This is the whole point: if an edge is fake, you find out at $2k, not $500k.

## Next steps (in order)
1. Point the connectors at real market data on your infra and confirm they pull funding/OHLCV.
2. Replace fake data with 2+ years of real BTC/ETH funding + price history.
3. Re-run the funnel on real data. Whatever passes the judge is a real candidate.
4. Build the S5 fill model against real order books, then arm the $1-5k rung.
