# Setting up Heimdall on a new machine

Read `CLAUDE.md`, then `HEIMDALL_MEMORY.md`, before changing anything. Those are the project rules and the settled state.

## 1. Clone (with the LuxAlgo submodule)

```bash
git clone --recurse-submodules https://github.com/aegiszk/heimdall.git
cd heimdall
```

Every file is checked out byte-exact (`.gitattributes: * -text`). The frozen Dhesi artifacts and `core/` files are verified by SHA-256 of their exact bytes, including their CRLF line endings. **Do not** re-save them with an editor that changes line endings, and do not set `core.autocrlf=true` for this repo.

## 2. Python environment

Main environment: Python **3.14.3** (the project also runs on ≥ 3.11 per `pyproject.toml`; the lock was produced on 3.14.3).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.lock.txt
```

Secondary environment (used only by `workspace/validation_completion_2026-09-23/`, Python **3.12.10**):

```bash
python3.12 -m venv workspace/validation_completion_2026-09-23/extvenv
workspace/validation_completion_2026-09-23/extvenv/Scripts/pip install -r workspace/validation_completion_2026-09-23/requirements-extvenv.lock.txt
```

LuxAlgo MCP server (submodule, optional): `cd external/luxalgo-mcp-server && npm install`.

## 3. Bulk data (≈ 8.7 GB, not in git)

Raw market data and large logs are too big for git. They are stored as assets of the GitHub release named in `tools/bulk_manifest.json`:
- Sierra tick/1m exports;
- Tardis free trades;
- Hyperliquid tape;
- HistData FX;
- profit-discovery wallet logs;
- two NQ event-atlas parquets.

```bash
gh auth login            # needs read access to aegiszk/heimdall
python tools/fetch_bulk_data.py
```

The script downloads every part, checks each part's SHA-256, extracts to the original paths, and re-verifies every file.

To publish a new bulk snapshot (maintainers only):
1. `python tools/pack_bulk_data.py --version N`
2. `gh release create bulk-data-vN bulk_release/*`
3. Commit the updated `tools/bulk_manifest.json`.

## 4. Secrets and machine-local items (never in git)

| Item | How to recreate |
|---|---|
| `.env` | copy `.env.example`, fill in (`TYPESAFE_API_KEY`, `DATABASE_URL`, …) |
| `DHESI_V3_RUN_AUTHORIZATION.txt` | **owner only**, per `workspace/dhesi_adjudication_agent1_2026-09-23/AUTHORIZATION_REQUEST_DHESI_V3.md` |
| Sierra Chart install and its `C:/SierraChart/Data` | install Sierra Chart; its own data directory is not part of the repo |

## 5. Verify

```bash
python tools/check_core_purity.py
pytest -q
```

Only the known OKX-timeout tests are expected to fail.

## 6. Access for other developers

- The repo is **private**. The owner adds each developer under GitHub → aegiszk/heimdall → Settings → Collaborators.
- Each developer then runs `gh auth login` with their own account. `fetch_bulk_data.py` needs that access too.

## 7. Working rules for agents and developers (summary; the canon is CLAUDE.md / AGENTS.md §8)

1. Setup is steps 1–5 above, in order. Do not start work until `check_core_purity.py` passes and pytest shows only the known OKX network failures.
2. Several agents write to this tree at the same time. Sync before and after work:
   `git pull --rebase` → commit only your own files → `git push`.
3. Never delete, move or revert files you did not create, including temp/scratch copies, without the owner's approval.
4. Never commit:
   - bulk data (see the `.gitignore` BULK DATA block);
   - any file > 50 MB;
   - `.env`;
   - `DHESI_V3_RUN_AUTHORIZATION.txt`;
   - virtualenvs.
5. New large data goes into a new bulk snapshot (§3: pack → `gh release create bulk-data-vN` → commit the manifest). It never goes into git.
6. Never alter frozen artifacts or their line endings. Their SHA-256 hashes gate the Dhesi one-shot validation.
7. The reserved data firewall still applies: no CME equity-index rows before 2024-07-01 may be read until the Dhesi run completes (see `HEIMDALL_MEMORY.md` and `workspace/agent2_external_strategy_audit_2026-09-24/`).
8. Bulk snapshot `bulk-data-v1` was taken 2026-09-24 ~09:00 (UTC+4). The live HL tape recorder keeps appending locally after that.

## Data licensing note

`data/` contains vendor data (Databento, Sierra Chart, FirstRate samples, Tardis free tier). Check that each developer's access complies with those vendors' terms before sharing further. Keep this repository **private**.
