# HEIMDALL — Strategy research report, 2026-09-22

Evidence labels: **[V]** verified directly this session · **[A]** supported by an
existing artifact · **[I]** inferred · **[U]** unverified.

## 1. Executive decision

- **No deployable strategy exists.** Both strategies implemented today are
  **rejected by measured results**: the LuxAlgo POC sweep reclaim and the Casper
  opening-range FVG scalp. [V]
- **The next experiment, value-area re-acceptance, stopped at its own Stage 1
  data-fidelity gate.** It is not rejected. It is **blocked by missing data**. [V]
- **Dhesi FVG inversion remains the only positive candidate.** It is sparse and
  unvalidated: 13 holdout trades. [A]
- **Live trading stays prohibited.** `LIVE_TRADING_ENABLED=false`. No broker
  adapter, no orders, no credentials. Execution is still **blocked by execution
  access** until Lucid confirms R|Protocol or CQG API access in writing. [A]
- **Recommended next step:** do not start another candle-pattern test. Either
  (a) authorise a **cost quote only** for multi-year NQ/MNQ trade-level data,
  which is the one input that would make the value-area hypothesis testable, or
  (b) pause strategy tests until Lucid API access is confirmed. §16 has the
  details.

## 2. Why Sierra Chart was bought

Sierra Chart Package 3 (USD 26) was bought for four reasons: to get futures
order-flow and footprint data, test absorption/footprint strategies on it,
decide whether they had real edge, and archive the permitted data within one
billing period. [A: memory]

- Delivered: 67,772,289 NQ one-tick records, 3,850,741 footprint cells, and a
  90-day one-minute bid/ask archive for 12 CME futures. [A: `data/sierra/MANIFEST.md`]
- No further purchase is requested.
- The renewal date is **[U]**: it is not recorded locally. Nobody has
  cancelled or changed the subscription, and nobody will without your decision.

## 3. Data inventory and limitations

| Dataset | Coverage | Fields | Status |
|---|---|---|---|
| `data/MNQ_1m.parquet` | 707,185 rows, 2024-07-01 → 2026-06-30, 515 RTH sessions | OHLCV, no bid/ask | 0 duplicates, 0 non-finite OHLC [A] |
| `data/MES_1m.parquet`, `data/ES_1m.parquet` | about 2 years | OHLCV | [A] |
| `data/sierra/*_continuous_1m_latest_90d.parquet` | 90 days, 12 futures | OHLCV + bid/ask volume + delta | [A] |
| `data/sierra/tick/NQ_continuous_1m_footprint.parquet` | 146 RTH sessions, 2026-02-27 → 2026-09-21, 3,837,157 RTH cells | minute, price, volume, bid/ask volume, bar OHLC, session, contract | [V] |

Limits: no market-by-order data, no queue position, no order lifecycle. Sierra
quote-high/low fields are forbidden (16–20% of trades fall outside them).
Rolls are explicit (NQM→NQU 2026-06-16, NQU→NQZ 2026-09-15). Footprint cells
aggregate volume by minute, so the order of events inside a minute is lost. [A]

Sierra one-minute bars against footprint minute aggregates: 24,343 overlapping
minutes, close equal 98.3815%, volume equal 98.3815% (24,282 in RTH, same rate). [V]

**Holdout reuse:** the untouched 40% of the MNQ two-year archive has now been
read by three experiments (Dhesi, POC, FVG). The footprint holdout (from
2026-06-16) has been read by one (initiative v3). Each further read adds
multiple-testing burden, and the report for that test must say so. [I]

## 4. Strategy families already killed (do not revisit)

Funding carry · cross-venue funding spread · liquidation cascade · VWAP
reversion · trend pullback · time-structured scalp · filters on retail TA ·
ES swing breakout · null-entry 50/50 · Fabio IVB ORB+delta · Okala 80/20
v1/v2 · order-flow absorption v1 · footprint absorption v2 · initiative
continuation v3. Small-cap shorting was rejected as the wrong market. [A:
`HEIMDALL_MEMORY.md`]

These died for three reasons: the edge was already arbitraged or crowded, it
needed latency we don't have, or its execution-adjusted expectancy was negative.
A literal coin flip pays about **−$1.625 per trade** in stop-slippage tax. [A]

## 5. The one positive candidate: Dhesi FVG inversion

MNQ holdout: 13 trades, 38.46% wins, realized payoff 2.05, skew +0.79,
+$26.31 per trade, 3 of 4 walk-forward buckets positive. [A]

- **Verdict: interesting but not validated.** It is far below the 30-trade
  minimum and cannot pass the five-profit-day rule alone.
- Do not manufacture trades by loosening its definitions.
- JackTrades PO3 overlaps this family, so it does not add diversification.

## 6. Technical repositories

The full catalogue is in `HEIMDALL_TECHNICAL_RESEARCH.md` and its verdicts are
preserved. This table summarises them against the user's categories.

| Project | Verdict | Concrete benefit | Concrete limitation | Next verification |
|---|---|---|---|---|
| DuckDB | **Adopt incrementally** | SQL scans of Parquet without full loads; manifests, session summaries | Creates no edge; don't rewrite working code for it | Replace one pandas manifest or summary job and diff outputs |
| Polars | **Pilot narrowly** | Streams the 67.8M-tick and footprint transforms | Changes interfaces; benefit unmeasured | Benchmark one footprint aggregation against pandas, outputs identical |
| Prometheus-compatible metrics | **Defer to paper-trading phase** | Feed age and gaps, rejects, MLL floor, kill-cushion distance, heartbeat, strategy→risk latency | Nothing is live to monitor yet; must stay read-only, never able to change limits | Check current `prometheus_client` license and version when the executor exists [U] |
| skfolio | **Defer** | Purged and combinatorial cross-validation; allocation once multiple validated strategies exist | Allocating across rejected or sparse signals is false precision | Revisit when 2 or more strategies pass the holdout |
| Riskfolio-Lib | **Defer** | CVaR and drawdown formulas | A static allocator does not solve path-dependent trailing MLL; overlaps skfolio | Only for a specific comparison question |
| hftbacktest | **Blocked by missing data** (conditional, not rejected) | L2/L3 replay, latency and queue models, partial fills; 2.4.4 ships a cp314 Windows wheel [V] | Our data is trade-only. Queue claims would be precise-looking but fabricated | Obtain validated depth or MBO data first; the adapter POC is outcome-free |
| QuantConnect LEAN | **Reference only** | Event engine, order state, broker abstraction | C# migration would duplicate the risk engine; no Lucid trailing-MLL logic | Only against a concrete integration requirement |
| vectorbt | **Restricted sandbox** | Fast rejection screening of frozen variants | Its parameter-grid strength fuels overfitting; weak on path-dependent stops | Parity test on one frozen strategy only |
| Backtrader | **Reference only** | Familiar event API | GPL-3.0, last push in 2024, adds engine-parity burden | None planned |
| Qlib | **Defer** | ML experiment registry | Too few validated signals and labels; ML multiplies hypotheses | Revisit when a stable feature family exists |
| OpenBB | **Defer (research data only)** | One provider surface | Not tick, execution, or broker data; provider costs and entitlements vary | Check provider terms before any use |
| FinanceToolkit | **Rejected for current use** | Fundamentals formulas | Irrelevant to intraday futures order flow | — |
| yfinance | **Rejected for validation** | Rough exploratory context | Not exchange-grade; Yahoo personal-use terms | — |
| lightweight-charts | **Defer (UI later)** | Trade replay, PnL and MLL dashboard | Visualisation only | Once the paper executor exists |
| awesome-quant, Awesome-finance-skills, Agent-Reach | **Reference only (discovery)** | Leads for future projects | Catalogues; prompt-injection and provenance risk | Audit each dependency individually |
| ai-hedge-fund, Vibe-Trading, AutoHedge, TradingAgents, anthropics/financial-services | **Reference only** | Research orchestration, audit ledgers, report structure | Nondeterministic LLM opinions are not alpha; they get no order or risk authority | Keep outside the money path |

Two differences between existing documents, now resolved:

- **hftbacktest wording.** Memory says hftbacktest is "rejected with current
  trade-only data"; the technical research file says "conditional, not
  rejection". Both mean the same thing: **no use on current data**. The file's
  wording is kept.
- **hftbacktest on Windows.** The earlier file cited only a cp311 wheel. PyPI
  now also lists cp314 win_amd64, which matches this venv (Python 3.14.3). [V]

## 7. LuxAlgo MCP server

- Installed at `external/luxalgo-mcp-server`, commit
  `df8719c24318138d22f8125b0613e3495c32b586`, version 1.4.1. Public Library
  access only; no broker, no LuxAlgo credentials. [A]
- The repository is MIT, but each Pine script carries its own license:
  `poc-sweep-reclaim` is **CC BY-NC-SA 4.0** (non-commercial) and
  `session-sweep-ifvg-rr` is **MPL 2.0**. Neither may be copied into a
  commercial or live component without license review. [A]

## 8. The five YouTube strategies

Transcripts are in `workspace/youtube_transcripts/`. [A]

| Video | Creator | Verdict |
|---|---|---|
| e-QmGJU1XYc | TradingLab supply/demand | **Not faithfully testable from available rules.** Swing, impulse, consolidation, zone invalidation and "recent extreme" are undefined |
| WEhmadJArQo | Casper Trading opening-FVG | Scalp variant: **rejected by measured results** (§12). Day variant: not faithfully testable (limit price in the gap undefined). The creator's performance figures are claims, not verified |
| JlyaRai4Du8 | JackTrades PO3/FVG | **Not faithfully testable.** Accumulation, direction, "disrespect" and targets are discretionary. The 0.3–0.5R targets conflict with the execution tax, and it overlaps Dhesi |
| Io9iQUWdq54 | Trader Mayne | **Not faithfully testable.** Narrative multi-timeframe structure, a BTC swing example, and unresolved overnight rules |
| W0IDzp_v-1w | Mulham Trading | **Not faithfully testable.** Swing, "weakness", "aggressive", level choice and target are discretionary |

## 9. Jev triage is advisory only

- **Earlier ranking.** Jev ranked the LuxAlgo POC reclaim first (confidence
  0.46, low), and that candidate then failed decisively. [A]
- **Today's next-experiment ranking**
  (`data/strategy_research/next_experiment_triage_2026-09-22.json`): Jev
  selected value-area re-acceptance with confidence 0.80. It also gave that
  candidate the **lowest codifiability confidence (0.39)**. [V]
- Jev sets research order only. It is not evidence of edge, and it cannot alter
  a pre-registration, a risk limit, or an order path.

## 10. The LuxAlgo "POC" proxy against true volume-at-price

LuxAlgo's POC is built from lower-timeframe close and volume. Over 4,857 NQ
five-minute bars compared with the Sierra footprint: exact match 2.70%, median
error 21 ticks, 95th percentile 150.2 ticks. [A]

Because minute alignment is 98.38%, a timestamp mismatch cannot explain this.
**That script's "POC" is not a volume-at-price POC.**

## 11. LuxAlgo POC sweep reclaim: measured results

Frozen in `POC_RECLAIM_PREREGISTRATION.md`, SHA-256 `22EF5224…9B33FE`, hash
re-verified this session. [V]

| | Trades | Win % | Mean $ | Total $ | Payoff | Skew | Max consecutive losses |
|---|---|---|---|---|---|---|---|
| Train (309 sessions) | 307 | 29.97 | −8.46 | −2,596 | 1.448 | −0.09 | 13 |
| Holdout (206 sessions) | 205 | 37.56 | −5.20 | −1,065.50 | 1.297 | −0.53 | 8 |

- **Holdout buckets:** −$196, −$122, −$218.50, −$529. All four are negative.
- **Gate:** failed on DSR (2.98e-19), Newey-West t (−1.20), bootstrap lower
  bound (−0.222) and walk-forward minimum (−0.179).
- **Lucid Monte Carlo (10,000 runs):** 0.00% pass, 100% never reached target.

**REJECTED by measured evidence.** New evidence could not overturn this: it
loses in train and in every holdout bucket, and its signal is a faulty proxy.

## 12. Opening-range FVG scalp: measured results

Frozen in `OPENING_FVG_SCALP_PREREGISTRATION.md`, SHA-256 `6A074F0E…197F56D`,
hash re-verified. [V]

| | Trades | Win % | Mean $ | Total $ | Payoff | Skew | Max consecutive losses |
|---|---|---|---|---|---|---|---|
| Train | 107 | 38.32 | +26.79 | +2,867 | 2.406 | +1.07 | 9 |
| Holdout | 67 | 28.36 | +0.46 | +31 | 2.541 | +1.25 | 7 |

- **Holdout buckets:** +$151, −$166, +$370, −$324. Two of four are positive.
- **Gate:** failed on DSR (1.28e-05), Newey-West t (0.024), bootstrap lower
  bound (−0.271) and walk-forward minimum (−0.202).
- **Lucid Monte Carlo:** 0.64% pass against a 3.96% breakeven, 99.36% never
  reached target, and 67.5% of holdout days had no trade.

**REJECTED for deployment.** The training profit vanished on the holdout, the
same overfitting and regime pattern as v3. Changing its FVG, engulf, window,
stop or target would make it a new hypothesis.

## 13. Implementation review (checklist item D)

I read `core/alpha/research_candidates.py`, `core/alpha/prop_futures.py`
(`_simulate`, `_exit_price`, `_close_trade`) and
`tools/validate_research_candidates.py` directly. [V] **No defect was found
that invalidates either result.**

- **Entry.** Slipped once: the simulator uses close ± 1 tick, and the plan uses
  the same price only to size R.
- **Stop fill.** One more adverse tick; a gap through the stop fills at the
  worse of the open and the stop.
- **Same bar.** When stop and target share a bar, the stop wins.
- **Target.** Filled exactly.
- **Commission.** Subtracted once, in `_close_trade`. The Monte Carlo uses
  `commission_per_rt=0.0` on those already-net trade PnLs.
- **Signal timing.** Exits are evaluated from the bar after entry, and signals
  use only completed bars. The POC uses bar t−1's POC, a sweep at t and a
  reclaim close at t+1. The FVG uses bars t−2 and t, then later retest and
  engulf bars.
- **Sessions and split.** Grouping is by New York session date. The 60/40 split
  is chronological by session, and holdout buckets are consecutive session
  quarters.

Minor notes. Neither changes the verdicts:

- **POC parent-bar timestamps.** They mark the bucket start, so the "15:30"
  entry cutoff lets in a bar that closes at 15:35. Likewise, the 15:55 flatten
  executes at about 16:00 for five-minute bars and 15:56 for one-minute bars.
- **Fidelity diagnostic.** It picks POC ties with `idxmax`, a first-occurrence
  rule, not the strict running rule. This affects only the §10 diagnostic, not
  any trade.
- **Index coverage.** The codebase-memory index is from 2026-09-21 and does not
  cover these files (`tools/` is excluded). The review used direct source reads.

## 14. Untestable is not the same as rejected

- **Rejected by measured results (2):** POC sweep reclaim and the opening-FVG
  scalp.
- **Not testable without additional rules (5):** TradingLab, the Casper day
  variant, JackTrades, Trader Mayne, Mulham.
- **Blocked by missing data (1):** value-area re-acceptance (§16).

A discretionary trader in the untestable group may still have skill. The
statement is only that their published words do not contain a mechanical
system.

## 15. No tuning after results

- **Pre-registrations.** Both were written and hashed before their outcome
  runs, and both hashes still match.
- **The two strategies.** No rule, threshold, window, stop or target was
  changed after either result.
- **The value-area test.** It was also frozen and hashed before Stage 1 (§16).

## 16. Next experiment

**Selected:** prior-session value-area re-acceptance, the auction-market "80%
rule". It passes the independence test: its claim is acceptance of prior value
(time spent inside value), with no delta, bar pattern, FVG or VWAP. It shares
only the value-area *level* with dead absorption v1, which triggered on delta
absorption.

- **Pre-registration:** `VA_REACCEPTANCE_PREREGISTRATION.md`, SHA-256
  `5CD7D937D007D51C235E6EF48301E9E4144C06B15F797ED98CFCE84404EF1949`. [V]
- **Stage 1 (price levels only; no outcomes):** tests whether a 70% value area
  computed from one-minute close and volume puts both edges within 4 ticks of
  the true footprint value area in at least 80% of sessions.
- **Stage 1 result** (`data/strategy_research/va_proxy_fidelity_2026-09-22.json`):
  0.68% of 146 sessions pass. Median VAH error is 143 ticks and median VAL
  error 197.5 ticks, with 95th percentiles of 804 and 758, against a median true
  width of 790. Verdict: **FAIL**. [V]
- **Implementation check:** one session was traced by hand. Total volume
  matches exactly, and its proxy edges miss by 22 and 29 ticks. The shortfall is
  the approximation, not a code defect. The value-area function has four unit
  tests (`tests/test_value_area.py`).
- **Consequence:** under the frozen rule, Stage 2 **does not run**. The two
  years of MNQ OHLCV cannot express true value. The 146 footprint sessions are
  too few for an honest once-per-session test.
- **What would make it testable:** multi-year trade-level NQ or MNQ data.
  Memory records a Databento `trades` quote of **$237.26 for 2 years of NQ**
  (July 2026). That quote is stale, so the next step is a **fresh cost quote
  only**, with no purchase unless you explicitly approve.
- **Why not another pattern:** the alternative candle-pattern ideas all overlap
  dead families. Jev also ranked value-area re-acceptance well above them.

**Why it might survive the stop-slippage tax [I]:** targets are value-area
width, a median of 790 NQ ticks. That puts one tick of slippage near 1% of
reward, against the 20–50% seen in the dead scalps.

## 17. Live trading remains prohibited

- **Status now:** no live orders, no broker connection, no API keys, no
  withdrawal scopes, no wallet keys. `LIVE_TRADING_ENABLED=false`.
- **Rithmic/`async_rithmic`:** blocked until Lucid confirms in writing.
- **Tradovate:** unproven for Lucid.
- **Funded Futures Family:** bans automation. Human-emulation evasion will not
  be built.
- **Wallet copy (`meta/wallet_copy/`):** stays read-only and offline. Copying in
  the same block is not guaranteed and will never be claimed.

## 18. Sources

- YouTube: https://youtu.be/e-QmGJU1XYc · https://youtu.be/WEhmadJArQo ·
  https://youtu.be/JlyaRai4Du8 · https://youtu.be/Io9iQUWdq54 ·
  https://youtu.be/W0IDzp_v-1w
- LuxAlgo MCP: https://github.com/LuxAlgo/luxalgo-mcp-server (commit df8719c)
- Sierra: https://www.sierrachart.com/index.php?page=doc/IntradayDataFileFormat.html ·
  https://www.sierrachart.com/index.php?file=doc/Packages.php
- TypeSafe: https://docs.typesafe.ai/llms.txt
- hftbacktest wheels: https://pypi.org/project/hftbacktest/ (2.4.4, checked 2026-09-22)
- Repository links: `HEIMDALL_TECHNICAL_RESEARCH.md`
- Auction-market theory: J. Dalton, *Mind Over Markets* (value area, 80% rule).
  The rule is used here as a hypothesis source, not as evidence.

## Verification record (2026-09-22)

- Full suite: `2 failed, 84 passed in 179.43s`. Both failures are OKX
  `RequestTimeout` in the accepted files `tests/test_connectors_live.py` and
  `tests/test_history_real.py`. New value-area tests: 4 passed. [V]
- `core purity OK: /core is free of /meta imports`. [V]
