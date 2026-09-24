"""Trade-level comparison Agent 2 vs Agent 1 (unit-safe timestamps). usage: compare_trades.py mine.csv theirs.csv"""
import json
import sys

import numpy as np
import pandas as pd


def key(df):
    t = pd.to_datetime(df["t_entry"], utc=True).astype("datetime64[ns, UTC]")
    return t.astype("int64").astype(str) + "|" + df["side"].astype(int).astype(str)


def compare(mine: pd.DataFrame, theirs: pd.DataFrame) -> dict:
    a, t = mine.assign(k=key(mine)), theirs.assign(k=key(theirs))
    j = a.merge(t, on="k", suffixes=("_a2", "_a1"))
    mm = {c: int((~np.isclose(j[f"{c}_a2"].astype(float), j[f"{c}_a1"].astype(float), atol=1e-6)).sum())
          for c in ("entry", "stop0", "R")}
    mm["t_exit"] = int((pd.to_datetime(j["t_exit_a2"], utc=True) != pd.to_datetime(j["t_exit_a1"], utc=True)).sum())
    mm["reason"] = int((j["reason_a2"].astype(str) != j["reason_a1"].astype(str)).sum())
    return dict(n_a2=len(a), n_a1=len(t), matched=len(j), only_a2=len(a) - len(j), only_a1=len(t) - len(j),
                field_mismatch=mm, mismatch_rate=round((len(a) + len(t) - 2 * len(j) + max(mm.values())) / max(1, len(t)), 4))


if __name__ == "__main__":
    print(json.dumps(compare(pd.read_csv(sys.argv[1]), pd.read_csv(sys.argv[2]))))
