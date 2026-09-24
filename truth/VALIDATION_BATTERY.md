# VALIDATION_BATTERY.md — Checker Spec (truth file)

The checker is the fund's edge. Every gate is a deterministic inequality computed from backtest output.
The checker never sees the maker's reasoning. All thresholds live here and in the admin-approved config
row — a maker cannot change them.

## Funnel

```
SCREEN (Stage A)  — TRAIN slice only, cheap, ranked. Holdout never touched.
   ↓ shortlist (top 8–12)
FIREWALL          — any factor that touched holdout is DISQUALIFIED
   ↓
GATE (Stage B)    — untouched OOS + walk-forward; full battery below
```

`nb_trials` for the Deflated Sharpe is counted at the GATE = size of shortlist only. Screen-stage trials do NOT reset the holdout.

## The battery (a signal must pass ALL to reach the $1–5k rung)

| # | Test | Threshold | Source / purpose |
|---|---|---|---|
| 1 | Walk-forward (sequential OOS) | consistent across all folds | performance persistence |
| 2 | CPCV (combinatorial purged CV) | — | generates PBO; López de Prado AFML ch.7 |
| 3 | PBO (prob. of backtest overfit) | **< 5%** | is the in-sample best overfit? |
| 4 | Deflated Sharpe Ratio | **prob > 0.95** at true nb_trials | multiple-testing correction; vectorbt formula |
| 5 | Monte Carlo permutation test | p < 0.05 | is PnL path better than shuffled luck? (Vibe-Trading) |
| 6 | Bootstrap Sharpe CI | lower bound > 1.0 | stability of risk-adjusted return |
| 7 | Newey-West t-stat | **> 2.0** | autocorrelation/heteroskedasticity-robust alpha inference |
| 8 | Max drawdown | **< 8%** | hard risk gate |
| 9 | Min trade count | ≥ configured floor | 90 quiet days can't fake a pass |
| 10 | Free-parameter cap | ≤ configured max | fewer params = less overfit; feeds nb_trials |
| 11 | OOS window | ≥ 24 months equivalent | regime coverage |

We implement all of these ourselves (permissive, audited). No external validation dependency on the money path.

## Verification debt (the failure mode to police)

A checker tuned once against a dead regime lets everything pass while feeling rigorous. Cure: the meta-layer
recalibration auditor runs weekly against the STATE.md outcomes log and reports precision/recall drift of the
gate. Recalibration changes require an admin config edit — the checker cannot loosen itself.

## Anti-patterns explicitly guarded

- Low rejection rate is a WARNING, not success. Expected reject rate 40–60%.
- Never accept a raw Sharpe as a pass criterion — always deflated.
- Never let screen and gate share data.
