# HEIMDALL — Pre-validation hardening release (2026-09-24)

**STATUS: READY_FOR_CHECKER** (decided by Jev, confidence 0.81 ≥ 0.80; P(READY)=0.90). Branch `agent1/prevalidation-hardening-2026-09-24`, base `8f70789801a2fc02b94f3159ebf3bf1b583d347c`.
NO Dhesi validation run. NO reserved (pre-2024-07-01 CME index) data read. NO new strategy research. Frozen code,
canonical spec and Protocol V1 are byte-identical to base.

## 1. Changed files and classification

| File | STRATEGY_LOGIC_CHANGE | VALIDATION_INFRA_CHANGE | What |
|---|---|---|---|
| `workspace/dhesi_adjudication_agent1_2026-09-23/dhesi_v3_validator.py` | NO | YES (also VALIDATION_DECISION_RULE: engine disagreement → INVALID) | D3 dual-ledger persistence + comparison gate; D4 pre-engine row-integrity refusal; 5-hash authorization binding; D1 comment; synthetic/dev engine self-test modes |
| `…/dhesi_v3_harvest_integrity.py` | NO | YES | D4: volume + full row validity, geometry, monotonic, timezone, gaps, roll-date range, lag −1/0/+1 stamp-shift check; pure testable functions; counts only |
| `…/PROTOCOL_AMENDMENT_1.md` (new) | NO | YES (protocol amendment) | supersedes Protocol V1 §4.5; extends §2.4 gate 1; authorization binding |
| `…/AUTHORIZATION_REQUEST_DHESI_V3.md` | NO | YES (binding inputs only) | new validator / integrity-tool hashes; amendment hash; auth-file template |
| `…/selftest_engines_dev/*`, `…/selftest_engines_synthetic/*`, `*.log` (new) | NO | evidence | D3 self-test outputs (consumed dev MNQ; synthetic walk) |
| `…/JEV_ADVISORY_REVIEW_2026-09-24.json`, `…/SECRET_SCAN_2026-09-24.json` (new) | NO | evidence | advisory Jev judgments; redacted secret scan |
| `tests/test_dhesi_hardening.py` (new) | NO | tests | 26 synthetic D3/D4 tests |
| `tests/test_gates_split.py` | NO | tests | ledger test split: historical snapshot vs live invariants + append regression |
| `tools/secret_scan.py` (new) | NO | tooling | tree + history scan, values never printed |
| `meta/jev_prevalidation_review.py` (new) | NO | advisory (/meta) | Jev second opinion; no secret value in payload |
| `meta/jev_release_decisions.py` (new) + `…/JEV_RELEASE_DECISIONS_2026-09-24.json` | NO | decision tooling (/meta) + record | Jev decides file classes, junk status, secret status, release status; thresholds + escalation |
| `EXTERNAL_8_PROGRAM_HANDOFF_TO_CHECKER.md`, `workspace/external_strategies/_program/make_checker_handoff.py` (new) | NO | handoff | generated from artifacts at 8f70789 |
| `PREVALIDATION_HARDENING_2026-09-24.md` (this file) | NO | documentation | — |

Evidence for "STRATEGY_LOGIC_CHANGE = NO" (deterministic, governs): function-level SHA-256 comparison of the validator
against base — `reference_run`, `_rth`, `_resample`, `_bins24`, `_inversions`, `_fractals`, `_clusters`, `_dedupe`,
`evaluate`, `stationary_bootstrap`, `prop_report`, `truncate_untouched`, `sessions_after_burn_in`, `floor_points`,
`check_frozen_code`, `integrity`, `selftest_dev`, `sha` UNCHANGED; changed only `check_authorization`, `primary`,
`secondary`; added `_integrity_module`, `ledger`, `compare_ledgers`, `run_both_engines_and_persist`,
`require_row_integrity`, `synthetic_walk`, `selftest_engines`. Frozen code (`core/alpha/inversion_model.py`,
`inversion_model_v3.py`, `base.py`, `core/risk/prop_engine.py`, `tools/prop_montecarlo.py`,
`tools/validate_inversion_model.py`), `ref_dhesi.py`, spec and Protocol V1: hash-identical to base.

**Decisions by Jev** (owner instruction 2026-09-24: Jev takes the release's judgment calls; `meta/jev_release_decisions.py`,
`jev-1.13.0`, output `workspace/dhesi_adjudication_agent1_2026-09-23/JEV_RELEASE_DECISIONS_2026-09-24.json`). Code
supplies only verified facts; decisions below the thresholds (Choice confidence < 0.80; junk deletion needs
P ≥ 0.90) are ESCALATED to the owner, never overridden. Jev never supplies facts (hashes, tests, trades).
- File classes decided: validator → validation_decision_rule_change (0.92); PROTOCOL_AMENDMENT_1 →
  validation_decision_rule_change (0.88); harvest integrity (0.99) and authorization request (0.97) →
  validation_infrastructure_change; tests/tools → tests_or_tooling (0.92–1.00); reports, logs, self-test outputs →
  evidence_or_documentation (0.93–1.00). **No file decided as strategy_logic_change.**
- ESCALATED (below 0.80): classification of `meta/jev_prevalidation_review.py` (0.75) and `meta/jev_release_decisions.py` (0.53).
- Earlier advisory pass (`JEV_ADVISORY_REVIEW_2026-09-24.json`) is retained for the record.

## 2. D3 — reference-engine trade persistence
In `primary`, after integrity and BEFORE any statistic: frozen and reference engines run on the same rows; both
ledgers are written to `primary_run/{FROZEN,REFERENCE}_ENGINE_TRADES.{csv,parquet}` with trade_id, signal_ts,
session, side, sweep_pool, entry_ts/price, stop, tp1, runner target, contracts, exit_ts/price, reason, tp1_hit,
risk_dollars, gross_pnl, costs, pnl; `ENGINE_COMPARISON.json` holds counts, matched count, missing ids both ways,
every field mismatch, max |diff| per numeric field, PASS/FAIL. Gate = 100% agreement on 16 fields (tol 1e-9).
FAIL ⇒ result INVALID; `evaluate()` is not called. Tests: comparator PASS on Agent 2's 231/231 synthetic ledgers
(max diff 0 on every field); FAIL + itemisation on a 1-field tamper and on a dropped trade. End-to-end on final bytes:
consumed dev MNQ → PASS 49/49, 0 missing, max |diff| 0.0; synthetic 2-year walk → PASS (1 trade; proves the
pipeline, not depth — depth is the 231-trade and 49-trade evidence).

## 3. D4 — volume integrity
Gate 1 now: valid/unique/strictly increasing stamps; finite O/H/L/C/**volume**; volume ≥ 0; OHLC geometry; zero
volume valid and counted; nothing imputed. Gate 2 coverage + gap counts; gate 3 equivalence with lag −1/0/+1
(a strictly better neighbour lag fails = stamp shift); gate 4 roll dates inside file range. The validator repeats
gate 1 on consumed rows and refuses to start engines (INVALID). Synthetic tests: NaN / +inf / −inf / negative / zero
volume, OHLC NaN (×4), geometry, missing row (gap count), duplicate row, non-monotonic, 1-minute shift, wrong timezone,
naive index, roll date outside range. Counts-only scope under Protocol V1 §2.4 is stated in Amendment 1 §A2.

## 4. Spec/code consistency
Re-run: spec, Protocol V1, frozen code, `ref_dhesi.py` hash-identical; `reference_run` byte-identical (asserted during
the patch); runtime agreement frozen≡reference on all 16 fields for 49/49 dev and 231/231 synthetic trades.
No economically material mismatch → **no BLOCKED_SPEC_CODE_MISMATCH**. Governance conflict surfaced (not silently
resolved): Protocol V1 §4.5 said the verdict stands on frozen code despite disagreement; this work order requires
INVALID. Resolved by explicit, hash-bound `PROTOCOL_AMENDMENT_1.md` (owner/checker to accept).

## 5. New infrastructure hashes (SHA-256)
| Artifact | Old | New |
|---|---|---|
| `dhesi_v3_validator.py` | e52ba64722a70ac4d80df550809b8c37d7816c63872027d6c72d829cbd512710 | 940aa3ac57a9e0baac09471f31221b424e382069e0b1dc056c9421617b629985 |
| `dhesi_v3_harvest_integrity.py` | 6be444f49dd2efd89d8357e48cebb50120daa03fec41c351a51fa1c3bb30cec6 | 2c223a41ac4c029348f042d0e81e255b7d13be2a856651530a25c26e216d90fc |
| `PROTOCOL_AMENDMENT_1.md` | — | 74f3340f24d8147f74b08d35eb8cf2a246fd798a9a59a28c998977ba8910400e |
| `AUTHORIZATION_REQUEST_DHESI_V3.md` | fcbc85d1f11dbd0b4ac7d2d263d5250ad0dde1e3641ee5ff1117790f234cc5bb | e5b0d374fdfb7b48b3d3d373ee29d9ed3fb3ce41bf2ee44b422aa8bccbb4b804 |
| `DHESI_V3_CANONICAL_SPEC_V1.md` | 8f330ae2…9c6059 | unchanged |
| `DHESI_V3_VALIDATION_PROTOCOL_V1.md` | 49d8d8b9…148793 | unchanged |
| `ref_dhesi.py` | e205afd6…79ed8f | unchanged |
| `selftest_dev_result.json` | b837f37e…999e66 | unchanged |
All files LF, byte-exact, matching the committed convention of every frozen artifact (verified from git blobs). Note for checker: the `.gitattributes` comment says frozen artifacts are CRLF, but their committed blobs are LF; the comment is wrong, the hashes are of LF bytes (not edited in this PR).

## 6. Ledger test repair
`test_ledger_integrity_and_reference_numbers` replaced by: (A) `test_ledger_historical_snapshot_reference_numbers`
— asserts 65 configs and SR-trials variance 0.003449473183343993 (rel 1e-9) plus the FOMO 153/6 counts on the
first 86 hash-chain entries, pinned by entry #86 (`FOMO-F13`, entry_hash 5a133b31…bd9c60); a hash chain makes the
prefix immutable and immune to back-dated `registered_at`. (B) `test_ledger_current_invariants` — chain valid, ids
unique, prefix intact (append-only), provenance fields present, exact-window configs ≥ 65, nb_trials ≥ snapshot,
variance finite and ≥ 0. (C) `test_ledger_append_changes_live_stats_but_not_snapshot` — appends a back-dated trial to
a copy: live nb_trials +1 and variance changes; snapshot assertions unchanged. Historical constant NOT edited.

## 7. External-8 checker handoff
`EXTERNAL_8_PROGRAM_HANDOFF_TO_CHECKER.md` (generated): 58 valid + 4 invalidated trial ids, prereg + amendment
hashes, Family A bug provenance, datasets/windows, cost assumptions, 8 transcript hashes + owner zip hash, claimed
verdicts. Link check: 0 missing references, 0 hash drift, 4/4 core documents identical to 8f70789.
Correction recorded (not a new conclusion): STATE §9's "62 valid trials" should read 58 valid + 4 invalidated = 62 looks.

## 8. Secret / repository hygiene
**SECRET_SCAN_FINDINGS (1 item, 2 scopes)** — `tools/secret_scan.py`, 995 blobs across all history + working tree:
- `workspace/dhesi_replication_agent2_2026-09-23/dhesi_validation_harness.py` line 38 (commit a3367a3 onward):
  credential TYPE = authorization sentinel string (`TOKEN = "<redacted>"`, 37 chars, the line Agent 2's harness
  requires in the owner's authorization file). Not an external credential (Jev advisory: authorization_sentinel 0.99).
  Risk: any agent reading the repo can reproduce the sentinel, so it offers no protection against an agent writing
  the authorization file; the real control is process (owner-only file, never committed). Owner decision.
- No Databento / AWS / GitHub / OpenAI / private-key / bearer / URL-credential / committed `.env` hits.
Status decided by Jev: SECRET_SCAN_FINDINGS (confidence 0.92).
Junk root files (tracked, 0 bytes): `$50k`, `HL`, `Stage`, `TAKER`, `tuple[float`, `tuple[int`. Jev decided
P(unambiguous generated junk) = 0.18 / 0.17 / 0.15 / 0.17 / 0.22 / 0.23 — all below the 0.90 deletion threshold →
KEPT and listed for the owner; nothing deleted in this PR.

## 9. Tests
- `tools/check_core_purity.py`: OK.
- `pytest tests workspace/external_strategies/common`: **279 passed, 1 skipped, 2 failed** — the 2 are network-only:
  `tests/test_connectors_live.py::test_live_public_connectors` and
  `tests/test_history_real.py::test_btc_real_history_and_funnel_verdicts` (OKX public API unreachable from this host).
  Includes 26 D3/D4 tests, 3 ledger tests, 18 external-program tests.
- Dhesi synthetic equivalence: comparator on Agent 2's 231/231 synthetic ledgers (all 16 fields, max diff 0); dev e2e 49/49.

## 10. Remaining blockers (unchanged by this release unless stated)
1. NQ untouched harvest not done (owner Sierra GUI step) → `DHESI_V3_HARVEST_INTEGRITY.json` absent.
2. Ledger trials `MNQ-dhesi-inversion-v3` (dev), `-v3-fresh`, `NQ-dhesi-inversion-v3-untouched` not registered.
3. Owner authorization file absent (must now name 5 hashes, Amendment 1 §A3).
4. Agent 2 certification of this release and acceptance of Protocol Amendment 1.
5. D2 reporting gap (top-5 share, DSR, power, PROP label) still open (post-hoc derivable from persisted ledger).
6. D5 Sierra export → parquet converter not frozen by hash.
7. `.dly` pre-2024 hazard files still in `C:/SierraChart/Data` (owner quarantine decision, CE-2026-09-24-A2-01).
8. Authorization-sentinel string in Agent 2's harness (§8).

## 11. Agent 2 audit instructions
1. `git fetch && git checkout agent1/prevalidation-hardening-2026-09-24`; confirm base `8f70789`.
2. `sha256sum` every file in §5; confirm frozen code/spec/protocol/ref_dhesi unchanged vs base (`git diff 8f70789 --stat`).
3. Re-derive the function-level diff yourself: every rule/statistics function in the validator byte-identical to base.
4. Read `PROTOCOL_AMENDMENT_1.md`; accept or reject the §4.5 supersession and the §2.4 counts-only scope.
5. `python -m pytest -q tests/test_dhesi_hardening.py tests/test_gates_split.py`; then the full suite.
6. Re-run `python workspace/dhesi_adjudication_agent1_2026-09-23/dhesi_v3_validator.py selftest-engines-dev` (consumed
   dev data only) and compare to `selftest_engines_dev/ENGINE_COMPARISON.json`.
7. Try to break the gate: tamper one field in a copy of a persisted ledger and run `compare_ledgers`; drop one row.
8. Confirm `primary` never calls `evaluate()` when the comparison fails and refuses before engines on bad rows.
9. `python tools/secret_scan.py` → expect the single sentinel finding only.
10. Verify `EXTERNAL_8_PROGRAM_HANDOFF_TO_CHECKER.md` against the ledger and artifacts; do NOT run any strategy.
Do not run `primary`/`secondary`; do not read pre-2024-07-01 CME index rows.
