# RESULTS — trader_mayne (DEVELOPMENT; frozen prereg; see PREREGISTRATION.md)

| trial | inst | n | tr/yr | win | mean net R | median R | frictionless R | NW t | 95% CI | drop top5 | cost x1.5 | +years | verdict (frozen rule) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B1_H4_M15_breaker | MNQ | 52 | 27.7 | 0.10 | -0.435 | -1.009 | -0.419 | -3.28 | [-0.703, -0.111] | -0.760 | -0.442 | 1/3 | ROBUSTLY_REJECTED |
| B2_H1_M5_breaker | MNQ | 140 | 70.3 | 0.12 | -0.123 | -1.014 | -0.087 | -0.68 | [-0.469, +0.301] | -0.470 | -0.141 | 1/3 | INCONCLUSIVE |
| B3_D_H1_breaker | MNQ | 17 | 10.4 | 0.12 | +0.799 | -1.004 | +0.814 | +0.61 | [-1.006, +4.040] | -1.006 | +0.792 | 2/3 | INCONCLUSIVE |
| B4_H4_OB_limit | MNQ | 70 | 35.5 | 0.07 | -0.638 | -1.006 | -0.628 | -6.52 | [-0.830, -0.413] | -0.873 | -0.642 | 0/3 | ROBUSTLY_REJECTED |

Trade logs: `results/trades_<trial>_<inst>.csv` (entry/exit provenance, reason codes, meta = why the trade exists).
R = net PnL / |entry fill − initial stop|. 'frictionless' = re-simulated with spread, slippage and commission set to 0.
