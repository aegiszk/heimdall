# Autonomous Crypto Trading Loop (codename: TBD)

**New machine / new developer: start with [SETUP.md](SETUP.md)** (clone with submodules, pinned env, `tools/fetch_bulk_data.py` for the ~8.7 GB of bulk data).

Funding-carry core + alpha factory. Deterministic money path; LLMs only in `/meta`.
Verification is the edge. No real capital until `truth/LIVE_GATE.md` gate 1 passes.

## Layout
- `core/`  deterministic money path (may NOT import `meta/` — enforced by `tools/check_core_purity.py`)
- `meta/`  LLM layer (regime, recalibration, incident triage)
- `truth/` invariants, risk limits, schema, validation battery, live gate
- `scripts/setup_worktrees.sh`  one worktree per process (LCC/RCC/CX build)

## Verify
    python tools/check_core_purity.py
    pytest -q

## Jev research triage

Jev is isolated in `meta/` and is advisory only. It can compare local strategy
rule sheets for codifiability, target-market fit, and whether the currently
available data can test the defining signal. It cannot emit trade signals,
change risk limits, or place orders.

Set `TYPESAFE_API_KEY`, then compare one or more Markdown rule-sheet files:

    python tools/jev_triage_strategies.py "Trading Philosophy and Order Flow Analysis_ Structured Rule Sheets.md"

Use `--dry-run` to inspect the structured state and question IDs without making
an API call. Files containing multiple `## Rule Sheet` sections are split into
individual candidates before evaluation. Every report sets
`human_review_required=true`; profitability still requires deterministic
implementation and the existing holdout/walk-forward funnel.

## Sprints: see truth/SPEC.md (S0 done = this scaffold)
