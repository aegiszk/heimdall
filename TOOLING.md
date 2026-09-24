# TOOLING.md — HELMOR standard tooling (all agents MUST use, Heimdall + every project)

Agents: read this alongside CLAUDE.md / AGENTS.md / HEIMDALL_MEMORY.md. These tools are the HELMOR
standard stack. Use them by default; do not substitute ad-hoc alternatives.
NOTE: confirm exact current invocation/flags against the tool's own --help before first use each session
(no stale syntax — the same live-data discipline applies to our own tools).

## Runner
- **nub** — universal Node.js script runner. Run project scripts through `nub` (not raw node/ad-hoc),
  so execution is consistent across agents and machines.

## Dedup / retrieval
- **rtk** — install via Homebrew ONLY (not cargo — cargo has a name collision with an unrelated crate).
  Use for its retrieval/toolkit role as in other HELMOR projects.
- **sqz** — dedup fallback. Use when rtk's primary dedup path isn't applicable.

## Output compression
- **caveman** (skill) — compress agent output using caveman grammar (~65-75% fewer tokens, full technical
  accuracy preserved). Activate for verbose/long agent responses to save tokens. Do NOT use caveman for
  the truth files, memory, or anything a human reads for decisions — those stay full-English and precise.

## Three-layer memory architecture (cross-session context)
- **agentmemory** — episodic / cross-session memory.
- **codebase-memory-mcp** — structural / always-on codebase memory.
- **Understand-Anything** — semantic / periodic memory.
- Plus the Heimdall project files: HEIMDALL_MEMORY.md (source of truth), PROJECT_STATE.md (status).
  When these conflict, the Heimdall project files win for settled Heimdall facts.

## Agent roster & worktrees (multi-agent builds)
- **LCC, RCC** — Claude Code agents. **CX1–CX4** — Codex agents. Antigravity for LCC+RCC.
- One isolated git worktree per process/task (see scripts/setup_worktrees.sh). Risk monitor / risk engine
  stays in a STRICTLY isolated worktree — never shared context with a strategy agent.
- Global CLAUDE.md / AGENTS.md configs apply. Disjoint-file assignment across agents (no two agents edit
  the same file) — same discipline as the P2PLY multi-agent build.

## Standing rules (from HELMOR practice)
- Never show raw base units in any financial UI — always human amounts.
- Live deployed git commit is the source of truth for custody/live changes — never build from a local folder.
- Verify tool availability before use; if a tool's syntax changed, correct it and note it in memory.
