"""Stitch NQ quarterly footprints with a prior-session-volume roll rule."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


CONTRACTS = ("NQM26", "NQU26", "NQZ26")


def _with_session(path: str | Path, contract: str) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    minute = pd.DatetimeIndex(frame["minute"])
    minute = minute.tz_localize("UTC") if minute.tz is None else minute.tz_convert("UTC")
    frame["minute"] = minute
    frame["session"] = minute.tz_convert("America/New_York").date
    frame["contract"] = contract
    return frame


def stitch_footprints(paths: dict[str, str | Path], destination: str | Path) -> pd.DataFrame:
    if tuple(paths) != CONTRACTS:
        raise ValueError(f"paths must be ordered exactly as {CONTRACTS}")
    frames = {contract: _with_session(path, contract) for contract, path in paths.items()}
    volumes = pd.concat(
        [
            frame.groupby("session", sort=True)["volume"].sum().rename(contract)
            for contract, frame in frames.items()
        ],
        axis=1,
    ).fillna(0)
    sessions = list(volumes.index.sort_values())
    selected: dict[object, str] = {}
    current = 0
    for position, session in enumerate(sessions):
        while current + 1 < len(CONTRACTS) and volumes.loc[session, CONTRACTS[current]] == 0:
            current += 1
        if current + 1 < len(CONTRACTS) and position > 0:
            previous = sessions[position - 1]
            old_volume = volumes.loc[previous, CONTRACTS[current]]
            next_volume = volumes.loc[previous, CONTRACTS[current + 1]]
            if old_volume > 0 and next_volume > old_volume:
                current += 1
        if volumes.loc[session, CONTRACTS[current]] > 0:
            selected[session] = CONTRACTS[current]

    parts = []
    for contract, frame in frames.items():
        wanted = {session for session, chosen in selected.items() if chosen == contract}
        if wanted:
            parts.append(frame[frame["session"].isin(wanted)])
    result = pd.concat(parts, ignore_index=True).sort_values(["minute", "price"], kind="stable")
    duplicate = result.duplicated(["minute", "price"])
    if duplicate.any():
        raise ValueError(f"duplicate minute/price cells after roll: {int(duplicate.sum())}")
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(destination, index=False, compression="zstd")
    return pd.DataFrame(
        [(session, selected[session], int(volumes.loc[session, selected[session]])) for session in selected],
        columns=["session", "contract", "rth_volume"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination")
    parser.add_argument("--nqm", required=True)
    parser.add_argument("--nqu", required=True)
    parser.add_argument("--nqz", required=True)
    args = parser.parse_args()
    selection = stitch_footprints(
        {"NQM26": args.nqm, "NQU26": args.nqu, "NQZ26": args.nqz},
        args.destination,
    )
    print(selection.groupby("contract").agg(first=("session", "min"), last=("session", "max"), sessions=("session", "size")))
    print(f"sessions={len(selection)} path={args.destination}")


if __name__ == "__main__":
    main()
