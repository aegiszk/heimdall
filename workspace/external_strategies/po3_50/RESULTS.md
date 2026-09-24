# RESULTS — po3_50 (DEVELOPMENT; frozen prereg; see PREREGISTRATION.md)

| trial | inst | n | tr/yr | win | mean net R | median R | frictionless R | NW t | 95% CI | drop top5 | cost x1.5 | +years | verdict (frozen rule) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1_3m_overnight | MNQ | 42 | 22.1 | 0.57 | +0.111 | +0.068 | +0.125 | +0.77 | [-0.151, +0.393] | -0.121 | +0.104 | 2/3 | INCONCLUSIVE |
| C2_3m_overnight_H4 | MNQ | 33 | 19.8 | 0.58 | +0.172 | +0.148 | +0.186 | +0.84 | [-0.155, +0.505] | -0.123 | +0.165 | 2/3 | INCONCLUSIVE |
| C3_5m_overnight | MNQ | 25 | 13.5 | 0.48 | -0.052 | -0.005 | -0.041 | -0.42 | [-0.282, +0.152] | -0.213 | -0.058 | 1/3 | INCONCLUSIVE |
| C4_3m_h4range | MNQ | 34 | 20.4 | 0.62 | +0.055 | +0.132 | +0.069 | +0.43 | [-0.187, +0.328] | -0.153 | +0.048 | 2/3 | INCONCLUSIVE |

Trade logs: `results/trades_<trial>_<inst>.csv` (entry/exit provenance, reason codes, meta = why the trade exists).
R = net PnL / |entry fill − initial stop|. 'frictionless' = re-simulated with spread, slippage and commission set to 0.
