# HEIMDALL — technical project and research shortlist

Reviewed 2026-09-22 from project-owned documentation, official documentation,
primary repositories, and academic papers. A repository is not adopted merely
because it is popular. It must close a verified HEIMDALL gap without weakening
the deterministic money path.

## Applicable installed skills

- `academic-researcher`: used for this review to assess research questions,
  methodology, findings, limitations, and reproducibility.
- `API Integration Specialist`: appropriate only after Lucid confirms the exact
  Rithmic/CQG interface; useful for authentication, idempotency, rate limits,
  recovery, and structured-error design.
- `architecture` / `software-architecture`: useful when an execution runtime is
  selected; not needed to change the already-proven risk engine today.
- `MCP Integration`: applicable only if the Robinhood Trading MCP track becomes
  primary.
- `autonomous-agent-patterns`: appropriate for research orchestration and
  monitoring, never for discretionary risk changes or direct order authority.

No third-party skill is accepted as trading evidence, and none can bypass the
holdout, execution-cost, core-purity, or live-order gates.

## Use now or prototype locally

### Polars

- Repository: https://github.com/pola-rs/polars
- Purpose: Rust-backed lazy/streaming dataframe engine.
- HEIMDALL fit: high. The current 67.8-million-record archive exposed avoidable
  pandas CPU/memory costs. Polars can stream Parquet and accelerate footprint,
  volume-bucket, and cross-contract transformations.
- Boundary: data preparation only; it does not validate a strategy.
- Decision: benchmark against one existing deterministic transformation before
  adding it as a dependency.

### DuckDB

- Repository: https://github.com/duckdb/duckdb
- Documentation: https://duckdb.org/docs/current/guides/file_formats/query_parquet
- License: MIT.
- HEIMDALL fit: high for SQL inspection, manifest reconciliation, session-level
  summaries, and direct Parquet scans without a server.
- Decision: useful analytical utility; not part of live order routing.

### orderflow-metrics

- Repository: https://github.com/twowaymind/orderflow-metrics
- License: MIT; dependency-free Python port available.
- Provides trade imbalance, VPIN, information-driven bars, price impact,
  implementation shortfall, and streaming estimators.
- HEIMDALL fit: medium-high as an independently testable reference for new
  event-time order-flow hypotheses. Its level-1 OFI functions need quote-size
  updates that our Sierra archive does not contain; trade imbalance and
  volume-bucket functions match fields we actually possess.
- Decision: audit formulas/tests and compare outputs against a small internal
  implementation before adopting. Never import it into `/core` blindly.

### skfolio

- Repository: https://github.com/skfolio/skfolio
- License: BSD-3-Clause.
- Relevant capability: walk-forward and combinatorial purged cross-validation
  with purge/embargo controls.
- HEIMDALL fit: medium. It can strengthen portfolio-level validation and guard
  overlapping-label leakage, but it does not create edge and must not become a
  hyperparameter-search loophole.
- Decision: evaluate as a checker-side addition after multiple live candidates
  exist; current single-strategy tests already use chronological holdout and
  walk-forward gates.

## Evaluate for execution architecture later

### Sierra Chart DTC Protocol

- Official specification:
  https://www.sierrachart.com/index.php?page=doc/DTCProtocol.php
- Official server documentation:
  https://www.sierrachart.com/index.php?page=doc/DTCServer.php
- Open protocol for market data, historical data, and trading over TCP/WebSocket.
- HEIMDALL fit: potentially high as a read-only local market-data bridge and
  simulated execution interface.
- Blocker: production trading still depends on the exact broker/prop connection
  and permissions. DTC does not override Lucid or Rithmic authorization.

### NautilusTrader

- Repository: https://github.com/nautechsystems/nautilus_trader
- License: LGPL-3.0.
- Production-grade Rust/Python event-driven engine with backtest/live parity,
  tick/custom data, persistence, and order-state machinery.
- HEIMDALL fit: technically strong, but replacing the proven risk engine would
  create unnecessary migration risk. It is most useful as a reference or outer
  event/execution runtime around deterministic HEIMDALL components.
- Decision: no rewrite. Run a bounded adapter feasibility spike only after the
  chosen broker API is confirmed.

### async_rithmic

- Documentation: https://async-rithmic.readthedocs.io/en/latest/
- Repository: https://github.com/imax09-wq/async_rithmic-Public
- License: MIT. Supports separate market-data, order, history, and PnL plants.
- Caveat: the public repository currently has very low adoption, so connection,
  recovery, idempotency, and order-state behavior require independent audit.
- Decision: blocked until Lucid confirms R|Protocol API access on the exact 50K
  FLEX account. No credentials or order tests before that.

## Full platform catalogue

Status meanings:

- **Benchmark now**: small, isolated component that closes a current verified
  gap without changing the deterministic money path.
- **Sandbox**: worth reproducing in an isolated environment; no production or
  live-order authority.
- **Reference**: extract architecture or tests, but do not import the platform.
- **Defer**: real capability, but the present asset class, data, license, or
  project phase makes integration wasteful.

| Project | Status | What HEIMDALL can take | Reason not to adopt wholesale |
|---|---|---|---|
| [ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | Reference | Mandates, pluggable agent/alpha layout, Jev provider example | The project explicitly calls itself educational and says it does not execute trades. Its stock/fundamental workflow is not evidence for futures edge. |
| [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | **High-priority sandbox** | Local-data loaders, run artifacts, Shadow Account, MCP tool separation, point-in-time checks, Robinhood connector profiles, committed mandates, pre-trade gate, audit ledger, kill switch | It is a large, fast-changing agent platform. LLM-generated signal code and its backtester cannot replace HEIMDALL's checker or deterministic risk engine without independent parity tests. Broker order tools must remain outside the research/MCP surface. |
| [AutoHedge](https://github.com/The-Swarm-Corporation/AutoHedge) | Reference | Director/quant/risk/execution agent separation and structured logs | Current execution support is Solana, while HEIMDALL's primary target is CME futures. Multi-agent claims do not establish out-of-sample edge or prop-rule compliance. |
| [Anthropic financial-services](https://github.com/anthropics/financial-services) | Reference | Research-agent packaging, financial skills, connector patterns, staged work products | The repository explicitly requires qualified human review and says its agents do not recommend investments, execute transactions, or bind risk. It is an analyst-workflow kit, not a trading engine. |
| [OpenBB](https://github.com/OpenBB-finance/OpenBB) | Sandbox later | One data-access surface for Python, REST and MCP; provider adapters | It does not supply free institutional data or execution. Provider entitlements, provenance, and point-in-time correctness still need validation; it does not improve the paid Sierra archive by itself. |
| [LEAN](https://github.com/QuantConnect/Lean) | Architecture reference | Mature event loop, brokerage abstraction, order state, portfolio/accounting models, backtest/live parity | A C#-centred platform migration would duplicate current working risk logic. Its generic execution model does not automatically solve Sierra order-flow or Lucid/Rithmic access. |
| [Qlib](https://github.com/microsoft/qlib) | Defer | Feature/model/experiment registries and reproducible ML workflow | Its strongest path is equity factor modeling. Applying its automated ML/RL surface to one futures contract would multiply hypotheses before HEIMDALL has a stable feature family and fresh final holdout. |
| [Backtrader](https://github.com/mementum/backtrader) | Defer | Simple event-driven strategy API examples | GPL-3.0, latest repository push observed in 2024, and documented broker adapters include legacy interfaces. It offers less execution realism than the stronger engines under review. |
| [vectorbt](https://github.com/polakowo/vectorbt) | Restricted sandbox | Fast vectorized screening and deterministic indicator parity tests | Its greatest strength—thousands of parameter combinations—also accelerates backtest overfitting. It may run frozen preregistered variants, never choose thresholds on the holdout. Some features are commercial PRO capabilities. |
| [Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) | Defer | CVaR/drawdown/risk-measure formulas if HEIMDALL becomes multi-strategy | It is a portfolio allocator. A one-account intraday prop-survival system needs path-dependent trailing-loss enforcement, not static portfolio optimization. |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) | Reference/sandbox | Point-in-time data safeguards, auditable agent debates, provider abstraction | LLM opinions are not executable alpha and may not modify risk or submit orders. Its news/fundamental stock workflow is not matched to NQ microstructure. |
| [FinanceToolkit](https://github.com/JerBouma/FinanceToolkit) | Defer | Transparent formulas for company fundamentals | Financial statements and equity ratios do not address the current futures/order-flow problem. |
| [yfinance](https://github.com/ranaroussi/yfinance) | Do not use for validation | Convenient exploratory equity/index context | Its README identifies Yahoo data as personal-use research data. It is neither tick-accurate, exchange-grade, nor a replacement for Sierra/CME data. |
| [awesome-quant](https://github.com/wilsonfreitas/awesome-quant) | Discovery reference | Ongoing project discovery across quant categories | It is a catalogue, not audited runtime code or profitability evidence. Each linked dependency needs its own review. |
| [Awesome-finance-skills](https://github.com/RKiding/Awesome-finance-skills) | Quarantined reference | Possible news/research workflow ideas | Prediction and sentiment skills are unvalidated for HEIMDALL; external content introduces prompt-injection, provenance, and freshness risks. No skill may reach `/core` or live execution. |
| [Agent-Reach](https://github.com/Panniantong/Agent-Reach) | Defer | Isolated discovery of public X/Reddit/YouTube discussions | Scraped social content is noisy and adversarial, platform terms must be checked, and popularity is not price edge. It may inform hypotheses but never create trading facts. |
| [Lightweight Charts](https://github.com/tradingview/lightweight-charts) | UI later | Fast browser charting for trade review and risk dashboards | Visualization does not create or validate edge. Add it only after the research/execution contract is stable. |
| [Freqtrade](https://github.com/freqtrade/freqtrade) | **Crypto sandbox candidate** | Dry-run operations, persistence, lookahead analysis, backtest artifacts, exchange integration | GPL-3.0 and candle-oriented assumptions require isolation. Hyperoptimization conflicts with preregistration unless tightly disabled. It does not provide same-block wallet-copy execution. |
| [Hummingbot](https://github.com/hummingbot/hummingbot) | **Crypto execution reference** | Exchange connectors and reusable order-lifecycle executors for market making, arbitrage, TWAP and directional positions | Its operational focus is crypto exchange execution, not Solana wallet mirroring or futures prop rules. Connector code needs credential, retry, reconciliation and venue-specific audit. |
| [RD-Agent](https://github.com/microsoft/RD-Agent) | Defer/research reference | Experiment automation and factor/model co-optimization patterns | Current package advertises Linux and is demonstrated mainly with Qlib/equities. Automated factor search creates a large multiple-testing burden; it cannot self-certify results. |
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) | Reference | Financial data/tool orchestration and report workflows | The open examples are primarily equity-research notebooks and external data/API workflows, not deterministic execution or futures microstructure. |
| [vn.py](https://github.com/vnpy/vnpy) | Execution architecture reference | Gateway/CTA/event-engine patterns and futures-domain design | Its strongest connector ecosystem targets Chinese venues. A Lucid/Rithmic path is not established, and adopting the framework would duplicate HEIMDALL components. |
| [CPZ Quant](https://github.com/CPZ-Lab/cpz-quant) | **Validation sandbox** | Purged/CPCV validation, probability of backtest overfitting and deflated Sharpe | Young project; every statistic and default must be reproduced against primary papers and known fixtures before it can grade HEIMDALL. It strengthens the checker but does not produce edge. |

## hftbacktest — conditional recommendation, not rejection

### hftbacktest

- Repository: https://github.com/nkaz001/hftbacktest
- License: MIT. PyPI 2.4.4 provides a CPython 3.11 Windows AMD64 wheel, so the
  Windows migration itself is not a blocker.
- Strength: tick-by-tick L2 market-by-price and L3 market-by-order replay,
  exchange/local timestamps, configurable feed/order latency, queue-position
  models, partial-fill models, multi-asset simulation, and Rust live prototypes
  for Binance Futures and Bybit.
- Local data audit: `NQZ26_CME_1tick_full.parquet` has one `ts`, OHLC fields,
  trade count, total volume, bid volume, and ask volume. It has no depth-update
  events, displayed quantity at each book level, order IDs, or distinct
  exchange/receive timestamps. The footprint file aggregates the same signed
  trade volume by minute and price. Those files cannot identify our place in a
  resting-order queue or measure feed latency.
- Model limitation: replayed orders do not alter the historical book, so the
  framework explicitly assumes our size has negligible market impact. Its
  documentation warns that taker and some partial fills can be unrealistic.
- **Futures decision:** defer queue/latency claims until a Sierra/CME depth feed
  and timestamp semantics are obtained and validated. A trade-only conversion
  would throw away the framework's main accuracy advantage and create a
  precision-looking but uncalibrated fill model.
- **Crypto decision:** sandbox candidate. Its collector can capture Binance or
  Bybit depth, trades and local receive timestamps prospectively. Collection
  requires a separate approved network work order; results still require paper
  calibration before any live use.
- **Immediate useful work:** define an adapter contract and prove, using a tiny
  public sample, that event ordering, book reconstruction and conservative queue
  models behave as documented. Do not install it into HEIMDALL's production
  environment or use it to retest the dead v1-v3 strategies.

### Old VPIN notebooks and generic trading-bot collections

- Rejected as production dependencies when they are Python-2 notebooks,
  untested strategy dumps, or lack explicit costs, holdout, and leakage guards.
- They may supply formulas to independently reproduce, never profitability
evidence.

## Jev semantic-fit check

TypeSafe Jev 1.13.0 scored 29 repositories against the next two HEIMDALL phases
using public repository summaries and the explicit deterministic-risk/data
constraints. This was a semantic relevance check, not a security or correctness
verdict. It used 6,296 input tokens and 443 output tokens.

Top scores were Polars 3.41/4, DuckDB 3.22, CPZ Quant 3.04, NautilusTrader 2.65,
hftbacktest 2.64, skfolio 2.31, LEAN 2.25, vn.py 2.17, and Vibe-Trading 2.14.
Confidence was moderate (0.50-0.59 for most of the top group), so the factual
reasoning and bounded statuses above take precedence over the ranking.

## Research result: initiative continuation v3

The literature-supported change from absorption reversal to short-horizon
initiative continuation was frozen before outcome inspection in
`ORDERFLOW_INITIATIVE_PREREGISTRATION.md`.

- Data: 3,850,741 price-level cells, 146 sessions.
- Funnel: 80 initiative bars, 64 confirmations, 64 entries.
- Development: 36 trades, 55.56% wins, +$9.50/trade.
- Untouched holdout: 28 trades, 39.29% wins, -$12.68/trade, -$355 total.
- Walk-forward: one of four holdout buckets positive.
- Lucid Monte Carlo: 0% pass; 100% never reached target.
- Verdict: `FAIL_V3`. The apparent development profit did not survive the
  contract/time holdout. Do not tune or retry this specification.

## Academic interpretation

Published futures research supports a short-run relationship between order flow
and price, but that is not equivalent to executable edge after spread,
commission, slippage, and regime change. HEIMDALL v3 is direct evidence of that
gap: the same-direction relation looked profitable in development and reversed
out of sample. Future work should test a different causal hypothesis or improve
data class—not optimize v3 thresholds.
