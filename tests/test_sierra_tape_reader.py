"""Offline tests for tools/sierra_tape_reader.py (synthetic recorder CSV + synthetic .scid)."""

import importlib.util
import struct
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("str_", ROOT / "tools" / "sierra_tape_reader.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

T0 = 1_790_000_000_000_000  # unix us, minute-aligned below


def row(seq, typ, us, vol=1, backfill=0):
    return [seq, typ, us, us * 1000 + 5_000_000, 100.0, vol, 99.75, 100.0, 5, 7, 0, 0, 0, 0, 1, 1, backfill]


def write(tmp, rows):
    p = tmp / "X_20260923.csv"
    pd.DataFrame(rows).to_csv(p, header=False, index=False)
    return p


def test_clean_sequence_passes(tmp_path):
    df = r.load(write(tmp_path, [row(1, 6, T0), row(2, 2, T0 + 10), row(3, 1, T0 + 20)]))
    v = r.validate(df)
    assert v["PASS"] and v["trades"] == 2 and v["quote_updates"] == 1 and v["sequence_gaps"] == 0


def test_gap_marker_and_duplicate_are_reported(tmp_path):
    rows = [row(1, 2, T0), row(2, 2, T0 + 5), row(2, 2, T0 + 5), row(5, 0, T0 + 9), row(6, 1, T0 + 12)]
    v = r.validate(r.load(write(tmp_path, rows)))
    assert not v["PASS"]
    assert v["duplicates_dropped"] == 1 and v["sequence_gaps"] == 1 and v["missing_sequence_numbers"] == 2 and v["markers"] == 1


def test_fidelity_against_synthetic_scid(tmp_path):
    base = (T0 // 60_000_000 + 1) * 60_000_000
    rows, recs, seq = [], [], 1
    for minute in range(4):
        for k, (typ, vol) in enumerate([(2, 3), (1, 2), (2, 1)]):
            us = base + minute * 60_000_000 + k * 1000
            rows.append(row(seq, typ, us, vol)); seq += 1
            bv, av = (vol, 0) if typ == 1 else (0, vol)
            recs.append(struct.pack("<q4f4I", us + r.SC_EPOCH_US, 0, 0, 0, 100.0, 1, vol, bv, av))
    scid = tmp_path / "X.scid"
    scid.write_bytes(b"SCID" + struct.pack("<II", 56, 40) + b"\0" * 44 + b"".join(recs))
    f = r.fidelity(r.load(write(tmp_path, rows)), scid)
    assert f["PASS"] and f["minutes"] == 2 and f["recorded_volume"] == f["scid_volume"] == 12
