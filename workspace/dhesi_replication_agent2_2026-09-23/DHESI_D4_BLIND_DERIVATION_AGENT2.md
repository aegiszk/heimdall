# Dhesi D4 — blind stop-rule derivation (Agent 2)

**Work order start (UTC):** 2026-09-23T15:03:18.705Z. This file was written before reading any Agent 1 artifact, and before re-reading `core/alpha/inversion_model.py`, `core/alpha/inversion_model_v3.py`, or `DHESI_V3_PREREGISTRATION.md` in this work order.

## Independence disclosure (mandatory)

**Agent 1 artifacts: blind.** None read. `workspace/dhesi_adjudication_agent1_2026-09-23/` is untouched.

**Outcomes: NOT blind.** Before this work order, Agent 2 had already:
- Read `VALIDATION_AUDIT_2026-09-22.md` D4. It says v2 "takes the stop from the latest 15m swing without checking side; 5/30 MNQ trades have long-stop ≥ entry or short-stop ≤ entry, exit instantly as gap_stop (`inversion_model.py:836`)"; v3 `stop_guard` (`inversion_model_v3.py:224`) guards this.
- Run the frozen `tools/validate_inversion_v3.py` once (2026-09-23) and seen these outcomes:
  - v2 reproduction: −$446.38 (30 trades).
  - stop_guard-only ablation: +$617.13 (26 trades).
  - v3 holdout: +$34.8/trade (n=20).
  - Fresh window: +$94.6/trade (n=4).

This derivation therefore cannot be outcome-blind. It is derived from the primary texts below; the outcome knowledge is declared so a reviewer can discount it.

## Primary sources used
1. **Original video transcript** `UIGZtoGGPH4`, fetched this work order to `UIGZtoGGPH4_transcript.json` (2354 snippets). Stop passages, verbatim:
   - S1: "My stop loss for the day trade would be above the current 15-minute high. Right? We should not retrace back into the 15-minute high because that might lead us into a change in the state of delivery and our 15-minute inversion ... might be inversed and now we're playing on the wrong side."
   - S2: "We then want to see price react and break below them. That's where we then enter. Stop loss above that high."
   - S3: "you can enter off the inversion, stop above the current high"
   - S4: "Your stop loss should I always say should be at the high or near the high because we can tap back into this area here and still respect the bearish PD arrays ... I always try to have a wider stop loss to let my trades breathe ... Let the chart do the invalidating, not your P&L."
   - S5 (long example): "We have a bullish fair value gap being respected down here, right? We have a low. This low should be protected. ... So, I keep my stop loss here. I get my entry here."
   - S6: "I'm comfortable putting my stop loss a little bit higher above these recent highs"
2. **Rule sheet** `Dhesi Trades ICT Strategy_ Structured Rule Sheet.md` §3: "place the stop loss just above or below the most recent Lower Timeframe swing high or low that caused the LTF inversion."

## Derivation
- **D-1 (semantic).** The stop is an **invalidation level**. It is the structural extreme whose breach means the thesis is wrong (S1, S4: "let the chart do the invalidating").
  - For a short, the thesis is "price will not retrace back above the high that preceded the breakdown".
  - For a long, the thesis is "this low should be protected" (S5).
- **D-2 (which extreme).** It is the high (short) or low (long) formed by the move that **produced the LTF inversion**: the pullback/retracement extreme that price broke away from to trigger entry (S2: "break below them ... Stop loss above *that* high"; rule sheet: "that caused the LTF inversion"). "Current" (S1, S3) and "recent" (S6) refer to this extreme at entry time, not to an arbitrary earlier swing.
- **D-3 (geometry follows from D-1/D-2).** At entry, the short-side invalidation high is by construction **strictly above** the entry price, because price has just broken *down* away from it. For a long, the low is strictly **below** entry. A short stop at or below entry, or a long stop at or above entry, **does not describe the rule at all**: it would stop the trade out on the entry print and "invalidate" a thesis the market has not contradicted. No source passage supports that.
- **D-4 (buffer).** "Just above/below" (rule sheet) and "at the high or near the high ... wider stop" (S4). The source mandates no exact buffer, so any small fixed tick buffer beyond the extreme is an implementation constant, not a rule change.
- **D-5 (what to do if a mechanical swing detector returns a wrong-side level).** A detector that picks "the latest 15m swing" *by time* can return an extreme that price has already passed (e.g., a 15m swing high below the current entry price after a rally). Per D-2, that level is **not** "the high that caused the inversion", so it is a detector error. The rule-faithful correction is to use the correct extreme: the highest high (short) or lowest low (long) of the pullback leg ending at entry. The sources do **not** say "skip the trade" in this case. **Skipping is a conservative implementation choice, not the literal rule.**

## Frozen decision criteria for classifying D4 (set BEFORE reading code)
| Class | Condition |
|---|---|
| **BUG** | v2 can emit a stop on the wrong side of entry (short stop ≤ entry or long stop ≥ entry). The fix only prevents or corrects such stops, without changing which setups qualify, entry, targets, or stops on trades where v2 was already on the correct side. |
| **INTERPRETATION_CHANGE** | The fix changes stop placement on correct-side trades too (different extreme, different buffer), or changes stop semantics in a way the primary texts allow but do not uniquely determine. |
| **POST_HOC_CHANGE** | The fix was chosen or tuned after viewing v2 outcomes and alters trade selection or exits beyond wrong-side prevention (e.g., drops trades by a PnL-correlated criterion not derivable from the texts). |
| **UNRESOLVABLE** | The primary texts cannot determine the correct behavior for the cases the fix touches. |

**Required reproduction:** identify every v2 trade with a wrong-side stop via a separate calculation path (my own code reading the trade logs and prices, not the strategy module). Then check whether the stop_guard/v3 changes are confined to exactly those trades, plus their knock-on effects (e.g., the one-entry-per-session slot).
