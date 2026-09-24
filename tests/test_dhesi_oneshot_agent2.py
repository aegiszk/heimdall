"""Agent 2 one-shot infrastructure tests (converter D5, report D2, ledger marker semantics, binding preflight).
Synthetic data only; no reserved data."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / "workspace" / "dhesi_v3_oneshot_agent2"
sys.path.insert(0, str(ROOT / "tools"))
import trials_ledger as tl  # noqa: E402


def _load(name, p):
    s = importlib.util.spec_from_file_location(name, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


CONV = _load("conv", W / "dhesi_v3_sierra_convert.py")
REP = _load("rep", W / "dhesi_v3_report.py")
BIND = _load("bind", W / "dhesi_v3_binding.py")

SIERRA = ("Date, Time, Open, High, Low, Last, Volume, NumberOfTrades, BidVolume, AskVolume\n"
          "2023/6/5, 13:30:00, 100.00, 101.00, 99.50, 100.75, 12, 10, 5, 7\n"
          "2023/6/5, 13:31:00, 100.75, 101.25, 100.50, 101.00, 0, 0, 0, 0\n"
          "2023/6/5, 13:33:00, 101.00, 101.50, 100.75, 101.25, 30, 20, 10, 20\n")


def test_converter_bar_start_utc_no_fill(tmp_path):
    src = tmp_path / "x.txt"; src.write_text(SIERRA)
    meta = CONV.convert(src, tmp_path / "x.parquet")
    df = pd.read_parquet(tmp_path / "x.parquet")
    assert str(df.index.tz) == "UTC" and df.index[0] == pd.Timestamp("2023-06-05 13:30", tz="UTC")
    assert len(df) == 3                                   # 13:32 missing stays missing (M5: never filled)
    assert df["close"].tolist() == [100.75, 101.0, 101.25] and df["volume"].tolist() == [12.0, 0.0, 30.0]
    assert meta["duplicate_timestamps"] == 0 and meta["unparsable_timestamps"] == 0
    assert "100.75" not in json.dumps(meta)               # metadata only, no prices echoed


def test_converter_rejects_wrong_header(tmp_path):
    src = tmp_path / "bad.txt"; src.write_text("Date,Time,Open,High,Low,Close\n2023/6/5,13:30:00,1,1,1,1\n")
    with pytest.raises(SystemExit):
        CONV.convert(src, tmp_path / "bad.parquet")


def test_converter_never_reorders_so_gate1_blocks(tmp_path):
    import importlib.util as iu
    s_ = iu.spec_from_file_location("hi", ROOT / "workspace/dhesi_adjudication_agent1_2026-09-23/dhesi_v3_harvest_integrity.py")
    hi = iu.module_from_spec(s_); s_.loader.exec_module(hi)
    lines = SIERRA.strip().split("\n")
    src = tmp_path / "o.txt"; src.write_text("\n".join([lines[0], lines[2], lines[1], lines[3]]) + "\n")
    meta = CONV.convert(src, tmp_path / "o.parquet")
    df = pd.read_parquet(tmp_path / "o.parquet")
    assert meta["non_increasing_steps_left_for_gate1"] == 1 and not df.index.is_monotonic_increasing
    assert hi.row_integrity(df)["gate1_rows_valid"] is False


def test_converter_reports_duplicates(tmp_path):
    src = tmp_path / "d.txt"; src.write_text(SIERRA + "2023/6/5, 13:33:00, 101.00, 101.50, 100.75, 101.25, 30, 20, 10, 20\n")
    assert CONV.convert(src, tmp_path / "d.parquet")["duplicate_timestamps"] == 1


def test_invalidated_markers_void_verdicts_but_originals_remain_looks():
    led = tl.load_ledger()
    v = tl.voided_ids(led)
    assert {"EXT8-A1_k1_spike_nearest-MNQ", "EXT8-A2_k2_spike_nearest-MNQ", "EXT8-A3_k1_spike_split-MNQ",
            "EXT8-A1_k1_spike_nearest-YM_S"} <= v
    c = tl.verdict_counts(led, "EXT8-")
    assert c["VOID_INVALIDATED"] == 4 and c["CORRECTION_MARKER"] == 4
    assert c.get("INCONCLUSIVE", 0) + c.get("ROBUSTLY_REJECTED", 0) == 58
    w = {"start": "2024-07-01", "end": "2026-06-30"}
    ids = {e["id"] for e in tl.trials_for_window(w, tl.IDX, led)}
    assert "EXT8-A1_k1_spike_nearest-MNQ" in ids                      # voided run is still a look
    assert "EXT8-A1_k1_spike_nearest-MNQ-INVALIDATED" not in ids     # marker is not a model


def test_marker_semantics_on_synthetic_ledger(tmp_path):
    p = tmp_path / "l.json"
    base = {"family": "t", "dataset": "d", "dataset_group": "G", "data_window": {"start": "2020-01-01", "end": "2020-12-31"},
            "window_status": "DEV", "n_configs": 1}
    tl.register_trial({**base, "id": "X1", "verdict": "ROBUSTLY_REJECTED"}, p)
    tl.register_trial({**base, "id": "X1-INVALIDATED", "verdict": "INVALID_IMPLEMENTATION", "is_null_control": True}, p)
    tl.register_trial({**base, "id": "fixA", "verdict": "INCONCLUSIVE", "voids": None}, p)
    led = tl.load_ledger(p)
    assert tl.voided_ids(led) == {"X1"} and tl.verify_ledger(led) == []
    assert tl.verdict_counts(led) == {"VOID_INVALIDATED": 1, "CORRECTION_MARKER": 1, "INCONCLUSIVE": 1}
    assert tl.nb_trials(base["data_window"], "G", led) == 2


def test_dhesi_trials_registered_append_only():
    led = tl.load_ledger()
    ids = [e["id"] for e in led["entries"]]
    for i in ("MNQ-dhesi-inversion-v3", "MNQ-dhesi-inversion-v3-reused-2026Q3", "NQ-dhesi-inversion-v3-untouched"):
        assert i in ids
    e = {e["id"]: e for e in led["entries"]}
    assert e["MNQ-dhesi-inversion-v3-reused-2026Q3"]["window_status"] == "REUSED_HOLDOUT"
    assert e["NQ-dhesi-inversion-v3-untouched"]["verdict"] == "PENDING"
    assert tl.verify_ledger(led) == []


def _fake_run(tmp_path, verdict="INCONCLUSIVE", cmp_result="PASS"):
    d = tmp_path / "run"; (d / "primary_run").mkdir(parents=True)
    rng = np.random.default_rng(0)
    n = 120
    sess = pd.date_range("2015-01-05", periods=n, freq="7D").strftime("%Y-%m-%d")
    pnl = rng.normal(20, 250, n).round(2)
    t = pd.DataFrame({"trade_id": [f"{s}|1|x" for s in sess], "session": sess, "side": 1, "pnl": pnl,
                      "gross_pnl": pnl + 3, "costs": 3.0, "contracts": 3})
    t.to_csv(d / "primary_run" / "FROZEN_ENGINE_TRADES.csv", index=False)
    (d / "primary_run" / "ENGINE_COMPARISON.json").write_text(json.dumps({"result": cmp_result}))
    (d / "dhesi_v3_untouched_primary.json").write_text(json.dumps({
        "result": {"verdict": verdict, "n": n, "mean": float(pnl.mean()), "boot_lo95": -1, "boot_hi95": 50,
                   "stress_mean": 1.0, "years": [{"year": 2015, "count": 50, "sum": -100.0, "mean": -2.0}]},
        "prop_report_only": {"pass_rate": 0.01}}))
    return d


def test_report_copies_alpha_and_separates_axes(tmp_path):
    r = REP.main(_fake_run(tmp_path))
    assert r["ALPHA"]["verdict"] == "INCONCLUSIVE"
    assert {"EXECUTION", "RISK", "PROP_ECONOMICS"} <= set(r)
    assert r["PROP_ECONOMICS"]["label"] == "PROP_PORTFOLIO_COMPONENT_ONLY"
    assert r["EXECUTION"]["pre_MNQ_listing_2019_05_06"]["n"] > 0
    assert 0 <= r["ALPHA"]["achieved_power"]["P_pass_if_true_mu_eq_mu_min"] <= 1
    assert r["ALPHA"]["dsr_descriptive"]["K_global"] > r["ALPHA"]["dsr_descriptive"]["K_dhesi_family"]


def test_report_invalid_run_reports_no_statistics(tmp_path):
    r = REP.main(_fake_run(tmp_path, verdict="INVALID", cmp_result="FAIL"))
    assert set(r) == {"ALPHA", "note"} and r["ALPHA"]["verdict"] == "INVALID"


def test_preflight_refuses_without_owner_artifacts(tmp_path):
    if not BIND.BINDING.exists():
        pytest.skip("binding not generated yet")
    nq = tmp_path / "nq.parquet"; pd.DataFrame({"close": [1.0]}).to_parquet(nq)
    r = BIND.preflight(nq)
    assert r["preflight"] == "REFUSED"
    assert any("authorization" in e or "integrity" in e for e in r["errors"])
