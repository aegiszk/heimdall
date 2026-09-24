# D4 — Agent 2 vs Agent 1 comparison (written after both verdicts were frozen)

**Frozen hashes (SHA-256):**

| Artifact | Hash | Frozen at |
|---|---|---|
| Agent 2 derivation | `ad50dd00…eb1b` | — |
| Agent 2 verdict | `881c3e77…9f26` | 15:12:25Z |
| Agent 1 adjudication | `af81b828…fb83` | 15:17:47Z |

Agent 1's adjudication was read only after Agent 2's verdict was frozen. Disagreements are preserved, not harmonized.

| Question | Agent 2 | Agent 1 | Agreement |
|---|---|---|---|
| Wrong-side stop is an implementation bug | BUG | A (implementation bug) | **AGREE** |
| 10-point floor | POST_HOC_CHANGE | C (post-hoc) | **AGREE** |
| Skip/continue after a failed guard | INTERPRETATION_CHANGE; source says stop at the correct extreme, not skip | B (interpretation); **also flags that the code *continues* to the next LTF event while the prereg text says "skip the setup"** | **AGREE**; Agent 1 adds a prereg/code mismatch Agent 2 did not state explicitly |
| Overall D4-as-applied | Bug bundled with post-hoc and interpretation changes; the sign-relevant parts are non-bug | **C. POST-HOC STRATEGY CHANGE** | **AGREE** in substance |
| Does the bug fix rescue v2? | No. Direct removal of the 5 wrong-side trades = −$411.88 (no knock-on) | No. Side-only (with continue rule) = −$304.88; holdout −$0.62/trade | **AGREE** on sign |
| Dollar attribution of −$446 → +$617 | Bug direct +$34.50; floor direct +$400.00; 3 skip-enabled replacements +$629.00 | Side (incl. its replacements) +$141.50; floor (incl. its replacements) +$922.00 | **DISAGREE ON METHOD, NOT TOTALS.** Agent 2 isolates replacement trades as their own component; Agent 1 attributes them sequentially to the rule that enabled them (side first, then floor). Both reconcile exactly to +$617.12. Agent 1's sequential order credits the 2025-08-07 +$467 replacement to the side fix and 2025-02-24 +$484.50 to the floor. **Preserved; neither is wrong; they answer different questions.** |
| "D4 flipped v2" (Agent 2's own earlier claim) | Retracted (correction appended 15:12Z) | Refuted | **AGREE** |
| Status of v3 "fresh" window 2026-07 → 09 | Earlier Agent 2 docs called it "fresh / first read". The manifest written this cycle already lists it as previously_read = YES. | REUSED_HOLDOUT (≥ 6 intraday-momentum trials and 3 order-flow trials read this dataset group) | **AGREE now.** Agent 2's earlier "fresh" wording was wrong. |
| Reopen verdict | Not justified as "bug rescue"; defensible only as a new, frozen spec tested once on untouched data | **REOPEN_REQUIRES_NEW_HYPOTHESIS** | **AGREE** |
| Validation market | MNQ from 2019-05 with NQ warmup | NQ continuous with MNQ economics; all untouched history (possibly back to 2010, depth [U]) | **DIFFER.** Agent 1's is more powerful (N ≈ 355 vs ≈ 135). Agent 2 defers to Agent 1's spec ownership. |
| Pass criteria | Draft: n ≥ 30, mean > $20, year-cluster lower bound > 0, ≥ 4 positive years | mean > 0 with a block-bootstrap lower bound > 0; ≥ 60% positive years; no trade > 25% of net; FAIL if upper bound < $20 | **DIFFER.** Agent 2's draft is superseded by whatever canonical spec is frozen; the harness reads criteria from the spec. |
| Power | Not computed | $20/trade edge needs ~53 years on NQ; single pass can only detect ≥ $38–62/trade | **Accept Agent 1's analysis** (not independently recomputed here). |
