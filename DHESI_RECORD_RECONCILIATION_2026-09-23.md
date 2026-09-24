# Dhesi — project-record reconciliation (2026-09-23)

**Written by:** Agent 2. This supersedes any earlier Dhesi statement that conflicts with it. Historical artifacts are **not** edited destructively; this file and appended corrections carry the correction.

## Authoritative interpretation

| # | Statement | Evidence |
|---|---|---|
| 1 | The wrong-side stop (D4) **was a real implementation bug**: 5 of 30 v2 MNQ trades had a stop on the wrong side of entry and exited instantly (−$2 to −$10 each). | `workspace/dhesi_replication_agent2_2026-09-23/d4_reproduce.json`; Agent 1 §3–4 |
| 2 | **Bug-only correction does not rescue v2.** Removing the wrong-side trades gives −$411.88. The side check with the code's continue rule gives −$304.88 whole period, and the holdout becomes −$0.62/trade. | Agent 2 `d4_reproduce.json`; Agent 1 `DHESI_REOPEN_ADJUDICATION_2026-09-23.md` §2 |
| 3 | The reported −$446.38 → +$617.12 swing **is not caused by the bug**. It comes from a **post-hoc 10-point stop floor**, written after v2's losing trades were read, plus **skip/continue-enabled replacement trades**. It rests on about 2–3 trades. | Agent 2 `d4_knockon.json` (23 common trades identical; 3 replacements = +$629); Agent 1 §4 |
| 4 | The **positive full v3 result is a NEW DEVELOPMENT-DERIVED HYPOTHESIS**. Its changes were designed after reading v2 results on the same data. | `DHESI_V3_PREREGISTRATION.md` "Why v3 exists" |
| 5 | **2026-07-01 → 2026-09-18 is REUSED, not fresh**, for the CME index dataset group (≥ 6 intraday-momentum trials and 3 order-flow trials read it before v3). v3's "+$94.6/trade, n=4" there is **not evidence**. | Agent 1 §6 |
| 6 | **Prior Dhesi state = INCONCLUSIVE**: not robustly dead, and not falsely killed. MNQ Dhesi was never killed. | Agent 1 §1, §10; `VALIDATION_AUDIT_2026-09-22.md` §9 |

## Withdrawn statements (do not cite)
- "D4 flipped v2 from −$446 to +$617" / "D4 flips the sign": `workspace/tick_discovery_2026-09-23/TICK_EDGE_DISCOVERY.md` §0, §5 row 13, §5b.
- "Dhesi … FALSE KILL" / "sign-flipped by the D4 wrong-side-stop bug": same file, §5 row 13, §6 item 5.
- "Fresh window … first read" for 2026-07 → 09: same file, §5b; also the word "fresh" in `data/strategy_research/dhesi_v3_validation_2026-09-22.json`.

## Current status
- **Dhesi v3 = new hypothesis awaiting a canonical spec + protocol + owner authorization.**
- The only admissible evidence is **untouched** history before 2024-07-01 (not yet on disk), run **once** through the firewalled harness in `workspace/dhesi_replication_agent2_2026-09-23/`.
