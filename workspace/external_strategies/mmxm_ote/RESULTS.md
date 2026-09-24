# RESULTS — mmxm_ote (DEVELOPMENT; frozen prereg; see PREREGISTRATION.md)

| trial | inst | n | tr/yr | win | mean net R | median R | frictionless R | NW t | 95% CI | drop top5 | cost x1.5 | +years | verdict (frozen rule) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F1_ote62_sl100_PD | EURUSD | 24 | 8.9 | 0.25 | -0.396 | -1.058 | -0.191 | -1.82 | [-0.832, +0.093] | -0.911 | -0.414 | 1/3 | INCONCLUSIVE |
| F1_ote62_sl100_PD | GBPUSD | 29 | 10.1 | 0.45 | +0.261 | -1.016 | +0.355 | +0.78 | [-0.357, +0.966] | -0.222 | +0.214 | 3/3 | INCONCLUSIVE |
| F1_ote62_sl100_PD | USDJPY | 14 | 5.1 | 0.43 | +0.064 | -1.039 | +0.146 | +0.14 | [-0.670, +0.804] | -0.785 | +0.023 | 2/3 | INCONCLUSIVE |
| F2_ote705_sl90_PD | EURUSD | 19 | 7.2 | 0.11 | -0.713 | -1.163 | -0.310 | -2.30 | [-1.233, +0.039] | -1.240 | -0.812 | 0/3 | INCONCLUSIVE |
| F2_ote705_sl90_PD | GBPUSD | 26 | 9.0 | 0.23 | -0.158 | -1.128 | +0.197 | -0.36 | [-0.880, +0.633] | -1.021 | -0.269 | 2/3 | INCONCLUSIVE |
| F2_ote705_sl90_PD | USDJPY | 13 | 4.7 | 0.31 | +0.246 | -1.109 | +0.409 | +0.34 | [-0.807, +1.312] | -1.160 | +0.162 | 2/3 | INCONCLUSIVE |
| F3_ote62_sl90_PDPW | EURUSD | 27 | 9.9 | 0.19 | -0.655 | -1.088 | -0.534 | -3.35 | [-1.168, -0.055] | -1.289 | -0.699 | 0/3 | INCONCLUSIVE |
| F3_ote62_sl90_PDPW | GBPUSD | 28 | 9.7 | 0.36 | -0.027 | -1.084 | +0.148 | -0.08 | [-0.616, +0.574] | -0.499 | -0.113 | 2/3 | INCONCLUSIVE |
| F3_ote62_sl90_PDPW | USDJPY | 11 | 4.0 | 0.55 | +0.653 | +2.022 | +0.775 | +1.08 | [-0.267, +1.557] | -0.604 | +0.593 | 2/3 | INCONCLUSIVE |

Trade logs: `results/trades_<trial>_<inst>.csv` (entry/exit provenance, reason codes, meta = why the trade exists).
R = net PnL / |entry fill − initial stop|. 'frictionless' = re-simulated with spread, slippage and commission set to 0.
