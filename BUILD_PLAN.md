# HEIMDALL — Build Plan (followed systematically, top to bottom)

Rule: implement a layer, TEST it, only then move down. The validation battery is proven against
pure noise BEFORE anything depends on it. Money path stays free of /meta (CI-enforced).

- [x] [S1] Data: duckdb schema + ccxt ingest (sandbox-untested) + synthetic OHLCV/funding generator for offline test
- [x] [S2] Validation battery (THE EDGE): metrics (Sharpe, maxDD, Newey-West), DSR/PSR, CSCV-PBO,
       Monte-Carlo permutation, bootstrap Sharpe CI, walk-forward. PROOF: rejects noise, accepts real
       signal, and fails the same signal under high nb_trials (multiple-testing).
- [x] [S3] Alpha families: carry (done), oi_extreme reversion, vol_regime momentum + funnel (screen->firewall->gate)
- [x] [S4] Portfolio: conviction aggregation + CVaR/vol-target sizing (lean, self-implemented; no heavy deps)
- [x] [S5] Execution: paper broker with realistic slippage + funding-accrual fills (honest fill model)
- [x] [S6] Risk monitor: invariant checks (I1 delta, I2 margin, I3 funding-flip, kill switch) + incident log
- [x] [S7] Meta: deterministic regime detector (vol/Markov) + verifier recalibration auditor (LLM hook stubbed)
- [x] [S8] Orchestration: loop.py wiring all sub-loops; paper backtest+graduation harness on synthetic data
- [FINAL] full pytest + core-purity; package; simple-English run instructions
