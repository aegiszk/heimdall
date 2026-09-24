#!/usr/bin/env bash
# One isolated worktree per loop process. Risk monitor MUST stay isolated (SPEC I4/monitor).
set -euo pipefail
git worktree add ../wt-ingest    -b wt/ingest
git worktree add ../wt-maker     -b wt/maker
git worktree add ../wt-checker   -b wt/checker
git worktree add ../wt-execution -b wt/execution
git worktree add ../wt-risk      -b wt/risk      # isolated: own creds, read-only except flatten
git worktree add ../wt-meta      -b wt/meta      # LLM layer, off money path
echo "worktrees created. Assign: LCC->maker RCC->checker CX1->ingest CX2->execution CX3->risk CX4->meta"
