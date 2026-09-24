# BUGFIX — Family A entry order type (found during failure diagnosis, 2026-09-24)

**Rule (unchanged, preregistered):** sell when price trades above the internal high H while the anchor is intact
("as soon as the high is spiked out"); buy mirror below internal lows.

**Defect:** `liquidity_trap/strategy.py` submitted a harness `stop` order at H+1 tick. For shorts the harness
`stop` entry triggers when price FALLS to the level (sell-stop semantics), which was already true at placement.
Evidence: A1 MNQ — 1,436 of 1,454 fills (98.8%) were on the wrong side of the trigger by > 2 ticks
(`_program/zero_cost.json` diagnostic, recheck in the run log). The fidelity gate did not catch it because it
checked order geometry, not fill location. A4 (close-confirm, `close_at`) was not affected.

**Fix:** entry type `limit` (resting sell limit at H+1 tick / buy limit at L-1 tick; fills only when price trades
through by 1 tick). New test `test_liquidity_trap_short_fills_only_on_spike_above_internal`.

**Status of the first run:** A1/A2/A3 MNQ and A1 YM results from the first run are INVALID_IMPLEMENTATION (kept on
record, not used for verdicts). The corrected runs carry the suffix `_fix1` and are registered as NEW trials in
`data/trials_ledger.json` (the data window was read again). No rule or parameter was changed.
