# Dhesi D4 — Agent 2 independent verdict

Recorded before reading any Agent 1 artifact. The derivation was frozen first: `DHESI_D4_BLIND_DERIVATION_AGENT2.md`, SHA-256 `ad50dd0009e374632c1b15692b1af6523416c97b0a23cd0e09e82f25dfd2eb1b`.

## Separate calculation path (reproduction)
- **`d4_reproduce.py`:** classifies v2's own trade log (`data/prop_futures/inversion_model_MNQ_1m_trades.csv`, 30 trades, −$446.38) by protective stop distance = side × (entry − stop).
  - **WRONG_SIDE (≤ 0): 5 trades, −$34.50.** Instant `gap_stop` exits of −$2 to −$10 each:
    - 2024-08-07 13:25
    - 2024-11-20 12:05
    - 2025-01-31 14:15
    - 2025-08-07 14:40
    - 2026-04-28 14:05
  - **TINY (0 < d < 10 pts): 2 trades, −$400.00.** Both sized to 40 contracts:
    - 2025-02-24 12:55 (0.25 pt)
    - 2025-12-11 13:55 (3.00 pt)
  - **VALID: 23 trades, −$11.88.**
- **`d4_knockon.py`:** stop_guard-only ablation on development data, diffed by entry timestamp against the v2 log.
  - Removes **exactly** those 7 trades.
  - Leaves the 23 common trades **identical** (−$11.88 in both).
  - **Adds 3 replacement trades** made possible because the session's one-entry slot is freed: 2025-02-24 13:50 short +$484.50 (runner target), 2025-08-07 14:55 long +$467.00 (runner flattened at session close), 2025-12-11 15:35 short −$322.50 (stop).
  - Guard total = −$11.88 + $629.00 = **+$617.12** (matches the frozen validator's ablation to the cent).

## Classification against the frozen criteria

| Component of `stop_guard` | Trades touched | PnL effect | Class | Reason |
|---|---|---|---|---|
| Wrong-side prevention (d ≤ 0) | 5 | +$34.50 | **BUG** | Confined to wrong-side trades; the 23 correct-side trades are unchanged; primary texts (D-1…D-3) make a wrong-side stop impossible under the rule. |
| 10-point minimum stop floor | 2 | +$400.00 | **POST_HOC_CHANGE** | Written after the v2 trade log was read (the prereg cites these two trades' $100 / $300 losses); changes selection beyond wrong-side prevention; not derivable from the source (which only says "wider stop to let trades breathe"). Economically defensible ex ante (friction ≤ 10% of risk), but by the frozen criteria it is post-hoc. |
| Skip (instead of moving the stop to the correct extreme), which enables later same-session entries | 3 new trades | +$629.00 | **INTERPRETATION_CHANGE** | D-5: the source says the stop belongs at the extreme that caused the inversion, not "skip". Replacement entries are an artifact of the skip choice. The source's "missed entry → sit out" is ambiguous about invalid setups. |

## Verdict
1. **D4 is a real BUG** (5 wrong-side stops). Its **direct** economic effect is small: −$34.50 of instant losses, plus 5 occupied session slots.
2. **The claim "D4 flips v2 from −$446 to +$617" is NOT supported.** I made that claim myself in `TICK_EDGE_DISCOVERY.md`, and I am correcting it. The flip decomposes into:

   | Source | Effect |
   |---|---|
   | Bug fix | +$34.50 |
   | Post-hoc 10-point floor | +$400.00 |
   | Three skip-enabled replacement trades | +$629.00 |

   Two replacement runners supply +$951.50. **The positive sign rests on n = 3 trades.**
3. **Consequence for reopening (my view; Agent 1 owns the decision):**
   - The development-period improvement of v2 → v3 is **not evidence of edge**. It is post-hoc-contaminated and tiny-sample.
   - A *fresh-data* test of the **frozen v3 package** (floor and skip included, now fixed rules) remains methodologically legitimate. Post-hoc choices made on development data do not contaminate genuinely untouched data.
   - Reopening justified on "the kill was a bug" grounds alone: **not justified.** Reopening as "one frozen spec, one untouched-data test": **defensible**, but that is a new trial, not a rescued one.
4. Overall `stop_guard` class: **BUG (component) bundled with POST_HOC_CHANGE and INTERPRETATION_CHANGE.** The sign-relevant parts are the non-bug parts.
