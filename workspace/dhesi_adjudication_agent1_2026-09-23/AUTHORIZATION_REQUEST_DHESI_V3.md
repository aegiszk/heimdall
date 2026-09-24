# AUTHORIZATION REQUEST — Dhesi v3 untouched-history validation

**Status: READY_FOR_OWNER_AUTHORIZATION**

Prepared 2026-09-23 by Agent 1 (canonical spec owner). **No untouched data has been read and the validation has not been run.** This file is a request, not an authorization. Agent 1 does not create `REOPEN_APPROVED` or `DHESI_V3_RUN_AUTHORIZATION.txt`.

## What is being authorized

One run of the unchanged Dhesi v3 hypothesis (`DHESI_V3_CANONICAL_SPEC_V1.md`) on untouched NQ continuous 1-minute history, from Sierra's earliest continuous row (≈ 2011-09) through 2024-06-28. The run follows `DHESI_V3_VALIDATION_PROTOCOL_V1.md` and produces one verdict: PASS / FAIL / INCONCLUSIVE. Secondary ES/RTY/YM replication runs only if the primary is not FAIL.

## Preconditions (the validator or protocol enforces each)

| # | Precondition | State |
|---|---|---|
| 1 | Spec, protocol and validator frozen and hashed | DONE (below) |
| 2 | Validator refuses without authorization and with any changed frozen code | VERIFIED: "NOT AUTHORIZED: DHESI_V3_RUN_AUTHORIZATION.txt missing"; code-hash gate passes on the current tree |
| 3 | Reference engine ≡ frozen code on development data | VERIFIED: 49/49 identical (`selftest_dev_result.json`) |
| 4 | NQ history harvested from Sierra (metadata-only handling) | **PENDING, owner GUI step.** Chart: NQ continuous, Volume Based Rollover, back-adjust None, 1-minute, UTC, maximum days to load. Export through 2024-09-30 (for the equivalence gate). |
| 5 | `dhesi_v3_harvest_integrity.py <file>` → `DHESI_V3_HARVEST_INTEGRITY.json` with `all_gates_pass: true` | **PENDING** (script mechanics-tested on dev data only) |
| 6 | Ledger owner adds the missing `MNQ-dhesi-inversion-v3` (dev), `MNQ-dhesi-inversion-v3-fresh` (REUSED_HOLDOUT) and this cycle's forensic read, then registers `NQ-dhesi-inversion-v3-untouched` (FRESH) | **PENDING, ledger owner** |
| 7 | Secondary only: live confirmation of the M2K/MYM commission | PENDING (does not block the primary) |

"READY" means the hypothesis and protocol need no further strategy-definition decisions. The run itself stays physically blocked until preconditions 4–6 are met and the owner writes the authorization file.

## How to authorize (owner only)

Create `DHESI_V3_RUN_AUTHORIZATION.txt` in the repo root containing:
```
AUTHORIZED_BY_OWNER
validator  e52ba64722a70ac4d80df550809b8c37d7816c63872027d6c72d829cbd512710
spec       8f330ae21a7537586cf769b20b4727fddc4f4eee7aea9d94e36bd29aeb9c6059
protocol   49d8d8b98e139e4d7d88809e36bd8cb9376f7b0b40f5419bb41edd5c3d148793
integrity  <sha256 of DHESI_V3_HARVEST_INTEGRITY.json>
date       <UTC>
```
Then: `python workspace/dhesi_adjudication_agent1_2026-09-23/dhesi_v3_validator.py primary --nq <file>`. Exactly one run.

## Frozen artifact hashes (SHA-256)

| Artifact | SHA-256 |
|---|---|
| `DHESI_V3_CANONICAL_SPEC_V1.md` | `8f330ae21a7537586cf769b20b4727fddc4f4eee7aea9d94e36bd29aeb9c6059` |
| `DHESI_V3_VALIDATION_PROTOCOL_V1.md` | `49d8d8b98e139e4d7d88809e36bd8cb9376f7b0b40f5419bb41edd5c3d148793` |
| `dhesi_v3_validator.py` (executor) | `e52ba64722a70ac4d80df550809b8c37d7816c63872027d6c72d829cbd512710` |
| `dhesi_v3_harvest_integrity.py` | `6be444f49dd2efd89d8357e48cebb50120daa03fec41c351a51fa1c3bb30cec6` |
| `selftest_dev_result.json` | `b837f37ec58c498b976fbf587b5765af4ad70520493571acb6a3f6f238999e66` |
| `DHESI_REOPEN_ADJUDICATION_2026-09-23.md` | `7693a320dadb0acc238f747f0bd227e8421172b5dd53a846aa0f60d901ff7a1a` |

## Frozen code (normative; hash-checked by the validator)

| File | SHA-256 |
|---|---|
| `core/alpha/inversion_model.py` | `e32e88f1a309c8e259274fd181929c3aa19935e667bcf568ff31eb9fbbdd0037` |
| `core/alpha/inversion_model_v3.py` | `0ab7a5156e506c629110efe5253a6b93315072cd3f544490d80c2a746922bf85` |
| `core/risk/prop_engine.py` | `5750672eea42047ae294415a14c795c783aef4348cd4af7bfc9eead0cae7a265` |
| `core/alpha/base.py` | `2d8c40e53bfdd0ab5f26ca90165b1cf7a38475e0429edd5f304c83eef1d78737` |
| `tools/prop_montecarlo.py` (PROP report) | `c5aaee3311289e11f92d0abc42ab5738861f477a81e40d0fcaf7dfbdd7b88e23` |
| `tools/validate_inversion_model.py` (daily counts) | `5dffdb7c4a7f7166d8e28c0d8df13bcc2ab2314f7e5fd720a828e27f79c59165` |

## Input sources

| Input | SHA-256 |
|---|---|
| `DHESI_V3_PREREGISTRATION.md` | `c9d143e5f633297038c2d1425ccda16a43ca7b6e15a9f5176e69578aba23d843` |
| `Dhesi Trades ICT Strategy_ Structured Rule Sheet.md` | `98b931bce9e388a4f566a688c003478a5de08cf77001fb11b4fc3768ece56090` |
| Transcript `UIGZtoGGPH4_agent1.en-GB.json3` | `507a67a7a2a238c504605449d0aad3c30f140687c110c4ee8115537b0d9814be` |
| `data/MNQ_1m.parquet` (development) | `91670f3f43d3a3e5eb99608d9c335fef2a0e215cb365543cb0126aac9e2b5774` |
| `data/strategy_research/dhesi_v3_development_trades.csv` | `1e92a18911fb4ff9102220aeb6e4be6ec42435976bb4726e1175691f7542868c` |
| `tools/validate_inversion_v3.py` (original v3 runner, reference only) | `8c2f31c1061c5d86a233efe44bc9d27c1c8b83c0dd6d0b3151cd40ebe3d453b2` |
| `data/trials_ledger.json` (state read 2026-09-23) | `a4a797fc36a161743910aec2c1db652234e46b236424d7d70f6458b080c69064` |
| Sierra docs (fetched 2026-09-23) | `SierraChartHistoricalData.php`: CME 1-minute from June 2008, tick from 2011. `ContinuousFuturesContractCharts.html`: intraday 15-year limit. |

## What the owner should expect (so no result is a surprise)

- Power is limited. At the central frequency (~153 trades), a true +$40/trade edge passes about 52% of the time and a true +$20 about 21%. A true zero edge passes ≤ 5%. **INCONCLUSIVE is the most likely single outcome** unless the edge is large.
- The PROP axis is expected to show `PROP_PORTFOLIO_COMPONENT_ONLY`: the dev stream's Lucid MC pass rate is 0.22%, against a 3.96% breakeven.
- Two rules carry **HIGH_OVERFIT_RISK**: the 10.0-point minimum stop and replacement entry. They stay in, unchanged. The test decides.
