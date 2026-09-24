# Memory supersession table — 2026-09-23

Source of authority: `VALIDATION_AUDIT_2026-09-22.md`, defects D1–D4 and §9. That audit's own status is "TRUSTED WITH LIMITATIONS".
Independent completion review is in progress: `VALIDATION_COMPLETION_2026-09-23.md`, when present.

Rules for this table:
- The old line stays in `HEIMDALL_MEMORY.md` for history.
- The **current reading** column governs.
- Verdict axes are ALPHA / EXECUTION / PROP, each PASS / FAIL / INCONCLUSIVE / N/A.

| # | Old statement (location) | Current reading | Why |
|---|---|---|---|
| S1 | "Battery proven vs noise … TRUSTWORTHY" (`HEIMDALL_MEMORY.md:20`) | The battery reliably **rejects** (null acceptance ≤4.8%) but is a **weak detector**: a per-trade SR 0.10 edge is accepted 6–9% of the time at N 30–100, SR 0.20 51% at N=200. It cannot establish absence of a sparse or moderate edge. | Audit §3, §6 |
| S2 | Every "Lucid MC 0% pass / 100% never_target" (`:238-243`, `:330`, `:365`, `:473`, `:500`, `:520`, `:534`, `STRATEGY_RESEARCH_2026-09-22.md` §11–12) | A PROP-axis verdict at **1 contract, 80 days** only. ALPHA = N/A from these lines. | D2 |
| S3 | Pass-rate grid "52%/1:1 @325 = 27.32%" (`:213`); "Proven: a mediocre 52%/1:1 strategy passes ~27%" (`CLAUDE.md:16`, `AGENTS.md:17`) | CONDITIONAL. Depends on Lucid rules the simulator encodes but nobody has verified: MLL lock level, eval time limit, and whether reaching the target before 5 qualifying days ends the eval (the sim counts it as a fail). Also 1-lot sizing. Treat the number as UNRESOLVED, not "proven". | Audit §8 last row, D2 |
| S4 | Null-entry "−$1.625 EV/trade … structural tax" (`:271-274`) | The magnitude rests on **uncalibrated** slippage (1-tick stop, 0-tick target). The direction (stop fills worse than target fills) stands; the dollar value is an assumption. | Audit §5 "Slippage ticks are UNCALIBRATED" |
| S5 | Dhesi v2 "CONFIRMED PORTFOLIO CANDIDATE #1" (`:365`); "Live Candidate #1 (Portfolio Ready)" (`AGENT_HANDOFF.md:63`); "the only positive but sparse candidate" (`AGENT_HANDOFF.md:95`) | ALPHA **INCONCLUSIVE**: 13 trades, 95% CI [−135, +188], ~1,000 trades needed. The v2 code takes wrong-side stops on 5 of 30 trades (D4); a labelled rerun is needed. Neither "positive candidate" nor "dead" is supported. | D4, §9 |
| S6 | Initiative v3 "DEAD … exact overfitting/regime failure" (`:521`) | ALPHA **INCONCLUSIVE**: 28 holdout trades, CI [−37, +12] contains the dev estimate +9.50. Keep "do not tune"; drop "proven overfit". | §9 |
| S7 | LuxAlgo POC holdout "−$5.20/tr, REJECTED" (`:534`) | −$5.20 is the **worst-case** intrabar bound (5m stop-first). Tick-resolved −$2.24, best case +$2.08. ALPHA FAIL still stands (gross ≈ 0; the proxy "POC" is not a real POC). | D3 |
| S8 | LuxAlgo / Casper FVG "gate fail (dsr …)" (`:534-539`) | The gate call (convention B, `sr_trials_var=1.0`) could not accept **anything** (D1). The verdicts stand only because gross edge ≈ 0: holdout gross t 0.10 for FVG, gross −3.39 for POC. | D1 |
| S9 | Absorption v1, footprint v2, Okala v1/v2 "DEAD" (`:402-409`, `:464-505`) | EXECUTION/FREQUENCY FAIL as specified (0 trades). ALPHA = N/A: untested, not refuted. | §9 |
| S10 | "SCOREBOARD: 11 strategies dead" (`:409`) and similar (`:287`, `:398`, `PROJECT_STATE.md`) | Recount on three axes. ALPHA FAIL with measured ~0 gross: VWAP reversion, time scalp, trend pullback, POC, Casper FVG, intraday momentum. INCONCLUSIVE: Dhesi v2, initiative v3. ALPHA N/A (frequency): absorption v1/v2, Okala. Funding carry/spread/cascade are unaffected (own logic, not the futures battery). | Audit §9 |
| S11 | Every gate run under convention A (`nb_trials=1`) | **Under-deflated**: ~20+ strategies reused the MNQ 60/40 holdout, and PBO was never computed. Any future PASS on that holdout needs a trial-count-aware DSR. | §6 |
| S12 | `HEIMDALL_MEMORY.md` 09-23 blocks "Profit discovery" / "External Alpha Intelligence" | The provisional parts belong in `PROFIT_DISCOVERY_CHECKPOINT_2026-09-23.md` / `EXTERNAL_ALPHA_INTELLIGENCE_2026-09-23.md` and `AGENT_HANDOFF.md`. My (profit-discovery) block has been trimmed to verified facts. The External Alpha block is another lane's and is **flagged, not edited**: its "SURVIVING (untested)" list is provisional. | Owner rule 2026-09-23 |
| S13 | "No untouched wallet history" (`PROFIT_DISCOVERY_2026-09-23.md` §7) | FALSE as stated. Robinhood Chain logs back to 2026-04-30 are served by the public RPC (verified 2026-09-23). Only the FomoPulse **index** starts on 09-05. Hyperliquid also has wallet-level history (Hydromancer, from 2025-07-28, per the External Alpha lane). | `PROFIT_DISCOVERY_CHECKPOINT_2026-09-23.md` |
