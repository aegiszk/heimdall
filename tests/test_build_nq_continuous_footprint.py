import pandas as pd

from tools.build_nq_continuous_footprint import stitch_footprints


def _write(path, sessions_and_volumes):
    rows = []
    for session, volume in sessions_and_volumes:
        rows.append(
            {
                "minute": pd.Timestamp(f"{session} 14:30:00", tz="UTC"),
                "price": 100.0,
                "volume": volume,
                "bid_volume": volume,
                "ask_volume": 0,
            }
        )
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def test_rolls_one_session_after_next_contract_wins_and_never_switches_back(tmp_path):
    paths = {
        "NQM26": _write(tmp_path / "m.parquet", [("2026-06-08", 100), ("2026-06-09", 90), ("2026-06-10", 200)]),
        "NQU26": _write(tmp_path / "u.parquet", [("2026-06-08", 50), ("2026-06-09", 120), ("2026-06-10", 100), ("2026-06-11", 300)]),
        "NQZ26": _write(tmp_path / "z.parquet", [("2026-06-11", 1)]),
    }

    selection = stitch_footprints(paths, tmp_path / "continuous.parquet")

    assert selection[["session", "contract"]].astype(str).to_records(index=False).tolist() == [
        ("2026-06-08", "NQM26"),
        ("2026-06-09", "NQM26"),
        ("2026-06-10", "NQU26"),
        ("2026-06-11", "NQU26"),
    ]
