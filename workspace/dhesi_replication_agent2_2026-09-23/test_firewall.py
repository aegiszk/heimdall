"""Firewall tests for dhesi_validation_harness.py (gates only; the strategy is never imported or run).

Builds a complete, internally consistent fake chain in a temp dir (fake spec/protocol/sources/dataset/manifest/ledger/
authorization), asserts ALL-PASS, then breaks one link at a time and asserts ABORT with the right reason.
Run: python -m pytest -q test_firewall.py
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("harness", HERE / "dhesi_validation_harness.py")
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture
def chain(tmp_path):
    repo = tmp_path
    (repo / "spec.md").write_text("canonical spec v1")
    (repo / "spec.sha256").write_text(sha(repo / "spec.md") + "  spec.md\n")
    (repo / "protocol.md").write_text("protocol v1")
    (repo / "strategy.py").write_text("# frozen strategy")
    (repo / "validator.py").write_text("# validator")
    (repo / "data.parquet").write_bytes(b"UNTOUCHED-BYTES")
    binding = {"spec_path": "spec.md", "spec_sha256": sha(repo / "spec.md"),
               "protocol_path": "protocol.md", "protocol_sha256": sha(repo / "protocol.md"),
               "strategy_sources": {"strategy.py": sha(repo / "strategy.py")},
               "validator_sha256": sha(repo / "validator.py"),
               "dataset": {"path": "data.parquet", "sha256": sha(repo / "data.parquet"), "dataset_group": "CME_EQUITY_INDEX"},
               "eval_window": {"start": "2010-01-01", "end": "2024-06-30"}}
    bp = repo / "binding.json"
    bp.write_text(json.dumps(binding))
    (repo / "auth.txt").write_text(f"{H.TOKEN}\nBINDING_SHA256={sha(bp)}\n")
    (repo / "manifest.json").write_text(json.dumps({"datasets": [{"path": "data.parquet", "sha256": sha(repo / "data.parquet"), "previously_read": "NO"}]}))
    (repo / "ledger.json").write_text(json.dumps({"entries": [{"id": "old", "dataset_group": "CME_EQUITY_INDEX",
                                                                "data_window": {"start": "2024-07-01", "end": "2026-06-30"}}]}))
    return repo


def gates(repo, **kw):
    args = dict(binding_p=repo / "binding.json", auth_p=repo / "auth.txt", manifest_p=repo / "manifest.json",
                ledger_p=repo / "ledger.json", lock_p=repo / "RUN_LOCK.json", repo=repo, validator_p=repo / "validator.py")
    args.update(kw)
    return H.check_gates(**args)


def test_all_consistent_passes(chain):
    g = gates(chain)
    assert g["ok"], g["problems"]


@pytest.mark.parametrize("mutate,expect", [
    (lambda r: (r / "spec.md").write_text("EDITED"), "spec hash mismatch"),
    (lambda r: (r / "protocol.md").write_text("EDITED"), "protocol hash mismatch"),
    (lambda r: (r / "strategy.py").write_text("# tweaked"), "strategy source changed"),
    (lambda r: (r / "validator.py").write_text("# tweaked"), "validator"),
    (lambda r: (r / "data.parquet").write_bytes(b"OTHER"), "dataset hash mismatch"),
    (lambda r: (r / "auth.txt").write_text("BINDING_SHA256=deadbeef\n"), "owner authorization token missing"),
    (lambda r: (r / "auth.txt").write_text(H.TOKEN + "\nBINDING_SHA256=deadbeef\n"), "does not bind"),
    (lambda r: (r / "manifest.json").write_text(json.dumps({"datasets": [{"path": "data.parquet", "sha256": "x", "previously_read": "YES"}]})), "previously read"),
    (lambda r: (r / "ledger.json").write_text(json.dumps({"entries": [{"id": "leak", "dataset_group": "CME_EQUITY_INDEX", "data_window": {"start": "2020-01-01", "end": "2020-06-30"}}]})), "trial-ledger overlap"),
    (lambda r: (r / "RUN_LOCK.json").write_text("{}"), "RUN_LOCK exists"),
    (lambda r: (r / "binding.json").unlink(), "binding file missing"),
    (lambda r: (r / "spec.sha256").write_text("0000"), "sidecar"),
])
def test_each_broken_link_aborts(chain, mutate, expect):
    mutate(chain)
    g = gates(chain)
    assert not g["ok"]
    assert any(expect in p for p in g["problems"]), g["problems"]


def test_real_workspace_currently_refuses():
    """With no canonical spec/protocol/binding/authorization in place, the real harness must refuse."""
    g = H.check_gates(HERE / "VALIDATION_BINDING_V1.json", HERE / "AUTHORIZATION.txt", HERE / "FRESHNESS_MANIFEST.json",
                      H.ROOT / "data" / "trials_ledger.json", HERE / "RUN_LOCK.json")
    assert not g["ok"]
