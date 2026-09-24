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

## Data licensing note

`data/` contains vendor data (Databento, Sierra Chart, FirstRate samples, Tardis free tier). Check that each developer's access complies with those vendors' terms before sharing further. Keep this repository **private**.
