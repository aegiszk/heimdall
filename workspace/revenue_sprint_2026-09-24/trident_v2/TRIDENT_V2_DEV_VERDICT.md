# TRIDENT_V2 — DEV RESULT: FAIL -> KILLED

Frozen manifest 37fcf7a3 (Agent 2 source audit PASS @ 64cc3fa). Evaluator evaluate_v2.py (frozen). DEV window FX/XAU
2022-01-01..2024-12-31 (not blind: read by V1). Sealed window 2025-01..2026-08 NOT opened and will not be for this model.

| Metric | Value |
|---|---|
| n / per year | 91 / 30.5 |
| win rate | 0.231 |
| mean / median / 10% trimmed net R | +1.967 / -1.230 / -0.743 |
| NW t | +0.76 |
| cluster bootstrap 95% CI / share of means > 0 | [-1.22, +7.85] / 0.65 |
| top-1 / top-5 share of total R | 1.31 / 1.51 |
| drop-top-5 mean R | -1.068 |
| cost x1.5 / x2 / 1-bar delay / stop-slip x3 | +1.509 / +1.050 / +1.886 / +1.514 |
| years | [{'year': 2022, 'count': 24, 'mean': -0.846, 'sum': -20.293}, {'year': 2023, 'count': 34, 'mean': 6.294, 'sum': 213.992}, {'year': 2024, 'count': 33, 'mean': -0.447, 'sum': -14.737}] |
| by instrument (count, mean R) | {'EURUSD': {'count': 10, 'mean': -2.357}, 'GBPUSD': {'count': 14, 'mean': -1.8931}, 'NZDUSD': {'count': 11, 'mean': -1.2179}, 'USDCAD': {'count': 12, 'mean': -1.3428}, 'USDJPY': {'count': 24, 'mean': 0.4449}, 'XAUUSD': {'count': 20, 'mean': 12.3934}} |

Gate checks: {'n_ge_30': True, 'mean_R_gt_0': True, 'median_not_catastrophic': False, 'drop_top5_gt_0': False, 'nw_t_gt_1_5': False, 'bootstrap_central_positive': False, 'cost_x1_5_gt_0': True, 'years_2_3_positive': False}
Failed: median_not_catastrophic, drop_top5_gt_0, nw_t_gt_1_5, bootstrap_central_positive, years_2_3_positive.

**Disclosed measurement artifact (does not change the verdict):** the top trade (XAUUSD 2023-10-19) has R = 234 because gold
uses a close-based stop and R is measured against the doji low, which sat $0.11 below entry. Excluding that single trade:
n 90, mean -0.617R, median -1.245R. The frozen rule is applied as written; the FAIL is
stronger, not weaker, without the artifact. Future gold close-stop designs need a risk floor defined BEFORE outcomes.

Terminal state: **KILLED** (prereg: DEV FAIL -> KILLED; one corrected cycle only, addendum G). No variant, no rescue.
