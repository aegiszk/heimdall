# RESULTS — liquidity_trap (DEVELOPMENT; frozen prereg; see PREREGISTRATION.md)

| trial | inst | n | tr/yr | win | mean net R | median R | frictionless R | NW t | 95% CI | drop top5 | cost x1.5 | +years | verdict (frozen rule) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1_k1_spike_nearest | MNQ | 1454 | 728.5 | 0.69 | -0.025 | +0.059 | -0.019 | -1.90 | [-0.051, +0.001] | -0.037 | -0.028 | 0/3 | INVALID_IMPLEMENTATION |
| A2_k2_spike_nearest | MNQ | 1191 | 596.7 | 0.68 | -0.027 | +0.064 | -0.021 | -1.81 | [-0.055, +0.002] | -0.038 | -0.030 | 0/3 | INVALID_IMPLEMENTATION |
| A3_k1_spike_split | MNQ | 1409 | 705.9 | 0.67 | -0.026 | +0.054 | -0.020 | -1.98 | [-0.052, +0.000] | -0.037 | -0.029 | 0/3 | INVALID_IMPLEMENTATION |
| A4_k1_close_nearest | MNQ | 987 | 495.2 | 0.58 | +0.013 | +0.050 | +0.023 | +0.47 | [-0.038, +0.073] | -0.021 | +0.008 | 1/3 | INCONCLUSIVE |
| A1_k1_spike_nearest | YM_S | 173 | 710.0 | 0.67 | +0.008 | +0.058 | +0.016 | +0.17 | [-0.081, +0.088] | -0.042 | +0.003 | 1/1 | INVALID_IMPLEMENTATION |
| A1_k1_spike_nearest_fix1 | MNQ | 1119 | 560.7 | 0.58 | -0.001 | +0.084 | +0.015 | -0.03 | [-0.054, +0.057] | -0.028 | -0.009 | 1/3 | INCONCLUSIVE |
| A2_k2_spike_nearest_fix1 | MNQ | 857 | 429.4 | 0.53 | -0.051 | +0.049 | -0.036 | -1.80 | [-0.108, +0.007] | -0.083 | -0.058 | 0/3 | ROBUSTLY_REJECTED |
| A3_k1_spike_split_fix1 | MNQ | 1039 | 520.6 | 0.57 | -0.010 | +0.066 | +0.004 | -0.35 | [-0.064, +0.050] | -0.041 | -0.016 | 1/3 | INCONCLUSIVE |
| A1_k1_spike_nearest_fix1 | YM_S | 125 | 513.0 | 0.52 | +0.024 | +0.025 | +0.047 | +0.27 | [-0.159, +0.227] | -0.151 | +0.012 | 1/1 | INCONCLUSIVE |

Trade logs: `results/trades_<trial>_<inst>.csv` (entry/exit provenance, reason codes, meta = why the trade exists).
R = net PnL / |entry fill − initial stop|. 'frictionless' = re-simulated with spread, slippage and commission set to 0.
