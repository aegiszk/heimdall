# MMXM_V2 — DEV RESULT: FAIL -> KILLED

Frozen manifest 37fcf7a3 (Agent 2 source audit PASS @ 64cc3fa). Evaluator evaluate_v2.py (frozen). DEV window FX
2022-01-01..2024-12-31 (not blind: read by V1). Sealed window NOT opened and will not be for this model.

| Metric | Value |
|---|---|
| n / per year | 438 / 147.7 |
| win rate | 0.269 |
| mean / median / 10% trimmed net R | -0.253 / -1.096 / -0.390 |
| mean GROSS R (before modelled costs) | -0.166 |
| profit factor | 0.696 |
| NW t | -3.39 |
| cluster bootstrap 95% CI / share of means > 0 | [-0.390, -0.109] / 0.00 |
| drop-top-5 mean R | -0.293 |
| cost x1.5 / x2 / 1-bar delay / stop-slip x3 | -0.440 / -0.520 / -0.256 / -0.313 |
| long / short | 224 @ -0.247 / 214 @ -0.258 |
| exits | {'stop': 297, 'target': 118, 'be': 23} |
| years | [{'year': 2022, 'count': 135, 'mean': -0.317, 'sum': -42.77}, {'year': 2023, 'count': 150, 'mean': -0.271, 'sum': -40.654}, {'year': 2024, 'count': 153, 'mean': -0.179, 'sum': -27.323}] |
| by pair | {'EURUSD': {'count': 145, 'mean': -0.2681}, 'GBPUSD': {'count': 150, 'mean': -0.2997}, 'USDJPY': {'count': 143, 'mean': -0.1882}} |

Gate checks: {'n_ge_30': True, 'mean_R_gt_0': False, 'median_not_catastrophic': False, 'drop_top5_gt_0': False, 'nw_t_gt_1_5': False, 'bootstrap_central_positive': False, 'cost_x1_5_gt_0': False, 'years_2_3_positive': False} -> every check except n fails.
Diagnosis: NO_SIGNAL (adverse). Negative before costs in every year, pair and direction; the OTE limit fills are adversely
selected (27% reach the leg extreme). Not an execution artifact.

Terminal state: **KILLED** (prereg: DEV FAIL -> KILLED; one corrected cycle only). No variant, no rescue.
