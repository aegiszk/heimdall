"""Pre-validation hardening tests for the Dhesi v3 one-shot validator (D3) and harvest integrity (D4).
SYNTHETIC data only (plus Agent 2's existing synthetic trade ledgers). No reserved or market outcome data."""
import importlib.util
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "workspace" / "dhesi_adjudication_agent1_2026-09-23"
DRY = ROOT / "workspace" / "agent2_external_strategy_audit_2026-09-24" / "dhesi_synthetic_dryrun"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HI = _load("hi_mod", D / "dhesi_v3_harvest_integrity.py")
V = _load("val_mod", D / "dhesi_v3_validator.py")


# ------------------------------------------------------------------------------------------ D4 fixtures
def synth_bars(start="2024-06-03 13:30", end="2024-06-05 20:00", seed=1, step_sd=3.0):
    idx = pd.date_range(start, end, freq="1min", tz="UTC", inclusive="left")
    rng = np.random.default_rng(seed)
    c = 18000 + np.cumsum(rng.normal(0, step_sd, len(idx)))
    c = np.round(c * 4) / 4
    o = np.r_[c[0], c[:-1]]
    h, lo = np.maximum(o, c) + 0.25, np.minimum(o, c) - 0.25
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c,
                         "volume": rng.integers(1, 500, len(idx)).astype(float)}, index=idx)


def test_clean_rows_pass():
    assert HI.row_integrity(synth_bars())["gate1_rows_valid"]


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_nonfinite_volume_fails(value):
    df = synth_bars(); df.iloc[100, df.columns.get_loc("volume")] = value
    r = HI.row_integrity(df)
    assert not r["gate1_rows_valid"] and r["nonfinite_cells"]["volume"] == 1


def test_negative_volume_fails():
    df = synth_bars(); df.iloc[5, df.columns.get_loc("volume")] = -1.0
    r = HI.row_integrity(df)
    assert not r["gate1_rows_valid"] and r["negative_volume_rows"] == 1


def test_zero_volume_is_valid_and_counted():
    df = synth_bars(); df.iloc[5, df.columns.get_loc("volume")] = 0.0
    r = HI.row_integrity(df)
    assert r["gate1_rows_valid"] and r["zero_volume_rows"] == 1


@pytest.mark.parametrize("col", ["open", "high", "low", "close"])
def test_ohlc_nan_fails(col):
    df = synth_bars(); df.iloc[7, df.columns.get_loc(col)] = np.nan
    r = HI.row_integrity(df)
    assert not r["gate1_rows_valid"] and r["nonfinite_cells"][col] == 1


def test_ohlc_geometry_violation_fails():
    df = synth_bars(); df.iloc[9, df.columns.get_loc("high")] = df["low"].iat[9] - 1.0
    assert not HI.row_integrity(df)["gate1_rows_valid"]


def test_duplicate_row_fails():
    df = synth_bars(); df = pd.concat([df.iloc[:50], df.iloc[49:50], df.iloc[50:]])
    r = HI.row_integrity(df)
    assert not r["gate1_rows_valid"] and r["duplicate_timestamps"] == 1


def test_non_monotonic_fails():
    df = synth_bars(); df = pd.concat([df.iloc[:50], df.iloc[51:52], df.iloc[50:51], df.iloc[52:]])
    r = HI.row_integrity(df)
    assert not r["gate1_rows_valid"] and r["non_monotonic_steps"] >= 1


def test_missing_row_is_reported_as_gap():
    df = synth_bars(start="2024-06-03 13:30", end="2024-06-03 20:01")
    gap = df.drop(df.index[60])
    assert HI.coverage(gap)["intra_rth_gaps_gt_1min"] == 1 and HI.coverage(df)["intra_rth_gaps_gt_1min"] == 0


def test_validator_row_integrity_refuses_before_engines():
    df = synth_bars(); df.iloc[3, df.columns.get_loc("volume")] = np.nan
    assert not V.require_row_integrity(df)["gate1_rows_valid"]


# ---- gate 3 (equivalence): shift / timezone on a synthetic "contaminated window" series
def eq_pair(seed=3):
    ref = synth_bars(start="2024-07-01 13:30", end="2024-07-12 20:00", seed=seed)
    return ref.copy(), ref["close"]


def test_equivalence_identical_passes():
    nq, ref = eq_pair()
    assert HI.equivalence(nq, ref, [])["gate3_series_equivalence"]


def test_one_minute_shift_fails():
    nq, ref = eq_pair()
    shifted = nq.set_axis(nq.index + pd.Timedelta(minutes=1))
    r = HI.equivalence(shifted, ref, [])
    assert not r["gate3_series_equivalence"] and r["lags_strictly_better_than_0"] == [-1]


def test_wrong_timezone_fails():
    nq, ref = eq_pair()
    wall_as_utc = nq.set_axis(nq.index.tz_convert("America/New_York").tz_localize(None).tz_localize("UTC"))
    assert not HI.equivalence(wall_as_utc, ref, [])["gate3_series_equivalence"]


def test_naive_index_treated_as_utc_and_reported():
    nq, ref = eq_pair()
    naive = nq.set_axis(nq.index.tz_localize(None))
    r = HI.row_integrity(naive)
    assert r["index_timezone"] == "naive" and HI.equivalence(naive, ref, [])["gate3_series_equivalence"]


def test_roll_dates_outside_range_flagged():
    df = synth_bars()
    assert not HI.rolls_check(df, [pd.Timestamp("2030-01-01").date()])["gate4_roll_dates_consistent"]


# ------------------------------------------------------------------------------------------ D3 comparison
def _dry():
    f = pd.read_csv(DRY / "synthetic_seed1_frozen_trades.csv")
    r = pd.read_csv(DRY / "synthetic_seed1_ref_trades.csv")
    return V.ledger(f, "frozen"), V.ledger(r, "reference")


def test_ledgers_carry_required_fields():
    fz, _ = _dry()
    for c in ("trade_id", "signal_ts", "side", "session", "sweep_pool", "entry_ts", "entry_price", "stop_price",
              "tp1_price", "runner_target_price", "position_size_contracts", "exit_ts", "exit_price", "reason",
              "gross_pnl", "costs", "pnl"):
        assert c in fz.columns
    assert fz["trade_id"].is_unique and np.allclose(fz["costs"], fz["contracts"] * 1.0)


def test_comparison_passes_on_agent2_synthetic_231():
    fz, rf = _dry()
    c = V.compare_ledgers(fz, rf)
    assert c["result"] == "PASS" and c["matched_trades"] == 231 and c["field_mismatch_count"] == 0
    assert all(v == 0.0 for v in c["max_abs_numeric_diff"].values())


def test_comparison_fails_on_single_field_and_itemises():
    fz, rf = _dry()
    rf.loc[10, "exit_price"] += 0.25
    rf.loc[20, "reason"] = "TAMPERED"
    c = V.compare_ledgers(fz, rf)
    assert c["result"] == "FAIL" and c["field_mismatch_count"] >= 2
    assert {m["field"] for m in c["field_mismatches"]} >= {"exit_price", "reason"}
    assert c["max_abs_numeric_diff"]["exit_price"] == pytest.approx(0.25)


def test_comparison_fails_on_missing_trade():
    fz, rf = _dry()
    c = V.compare_ledgers(fz, rf.drop(index=5).reset_index(drop=True))
    assert c["result"] == "FAIL" and c["missing_on_reference"] == [fz.loc[5, "trade_id"]]


def test_authorization_requires_all_bound_hashes(tmp_path, monkeypatch):
    auth = tmp_path / "AUTH.txt"
    monkeypatch.setattr(V, "AUTH_FILE", auth)
    me = V.sha(Path(V.__file__))
    auth.write_text(f"AUTHORIZED_BY_OWNER\nvalidator {me}\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="NOT AUTHORIZED"):
        V.check_authorization()
    full = "AUTHORIZED_BY_OWNER\n" + "\n".join(
        [me, V.sha(V.SPEC_FILE), V.sha(V.PROTOCOL_FILE), V.sha(V.AMENDMENT_FILE), V.sha(V.INTEGRITY_TOOL)])
    auth.write_text(full, encoding="utf-8")
    assert V.check_authorization() == me


def test_real_authorization_file_absent():
    assert not (ROOT / "DHESI_V3_RUN_AUTHORIZATION.txt").exists()
