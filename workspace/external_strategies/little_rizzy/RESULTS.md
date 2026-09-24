# RESULTS — little_rizzy (DEVELOPMENT; frozen prereg; see PREREGISTRATION.md)

| trial | inst | n | tr/yr | win | mean net R | median R | frictionless R | NW t | 95% CI | drop top5 | cost x1.5 | +years | verdict (frozen rule) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1_F_short_1h_pivot | MNQ | 321 | 161.3 | 0.25 | +0.099 | -0.660 | +0.125 | +0.60 | [-0.186, +0.475] | -0.175 | +0.085 | 2/3 | INCONCLUSIVE |
| D1_F_short_1h_pivot | ES | 299 | 151.7 | 0.25 | -0.062 | -0.657 | -0.004 | -0.60 | [-0.245, +0.145] | -0.199 | -0.090 | 1/3 | INCONCLUSIVE |
| D1_F_short_1h_pivot | XAUUSD | 498 | 166.9 | 0.23 | -0.170 | -0.639 | -0.067 | -2.53 | [-0.305, -0.031] | -0.245 | -0.212 | 0/3 | ROBUSTLY_REJECTED |
| D2_F_short_4h_pivot | MNQ | 82 | 42.2 | 0.26 | -0.108 | -0.652 | -0.099 | -0.82 | [-0.409, +0.218] | -0.381 | -0.113 | 0/3 | INCONCLUSIVE |
| D2_F_short_4h_pivot | ES | 73 | 36.9 | 0.23 | +0.023 | -0.674 | +0.048 | +0.10 | [-0.402, +0.528] | -0.412 | +0.011 | 1/3 | INCONCLUSIVE |
| D2_F_short_4h_pivot | XAUUSD | 134 | 45.7 | 0.22 | -0.095 | -0.711 | -0.061 | -0.69 | [-0.362, +0.212] | -0.354 | -0.111 | 1/3 | INCONCLUSIVE |
| D3_F_short_1h_bb | MNQ | 207 | 105.6 | 0.29 | -0.038 | -0.544 | -0.021 | -0.40 | [-0.215, +0.151] | -0.174 | -0.046 | 1/3 | INCONCLUSIVE |
| D3_F_short_1h_bb | ES | 211 | 107.9 | 0.27 | -0.037 | -0.551 | +0.003 | -0.35 | [-0.217, +0.153] | -0.164 | -0.057 | 1/3 | INCONCLUSIVE |
| D3_F_short_1h_bb | XAUUSD | 330 | 111.6 | 0.24 | -0.124 | -0.544 | -0.030 | -1.74 | [-0.273, +0.037] | -0.230 | -0.160 | 0/3 | ROBUSTLY_REJECTED |
| D4_G_long_1h_pivot | MNQ | 295 | 148.6 | 0.35 | +0.151 | -0.383 | +0.172 | +1.89 | [-0.036, +0.351] | +0.014 | +0.141 | 3/3 | INCONCLUSIVE |
| D4_G_long_1h_pivot | ES | 290 | 145.7 | 0.33 | -0.054 | -0.428 | -0.008 | -0.75 | [-0.206, +0.108] | -0.156 | -0.076 | 1/3 | INCONCLUSIVE |
| D4_G_long_1h_pivot | XAUUSD | 458 | 153.5 | 0.26 | -0.073 | -0.555 | +0.025 | -0.85 | [-0.216, +0.090] | -0.175 | -0.115 | 1/3 | INCONCLUSIVE |

Trade logs: `results/trades_<trial>_<inst>.csv` (entry/exit provenance, reason codes, meta = why the trade exists).
R = net PnL / |entry fill − initial stop|. 'frictionless' = re-simulated with spread, slippage and commission set to 0.
