"""Registers the two V2 DEV looks (one pooled trial per model) in the append-only trials ledger. Run once.
sr_per_trade = mean/std(ddof=1) of the frozen evaluator's net R (DEV_TRADES_<MODEL>.csv, manifest 37fcf7a3)."""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from trials_ledger import register_trial  # noqa: E402

PAIRS = {"TRIDENT_V2": ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "NZDUSD", "XAUUSD"],
         "MMXM_V2": ["EURUSD", "GBPUSD", "USDJPY"]}
FAMILY = {"TRIDENT_V2": "ext8_trident", "MMXM_V2": "ext8_mmxm_ote"}


def sr(r: pd.Series) -> float:
    return float(r.mean() / r.std(ddof=1))


for model in ("TRIDENT_V2", "MMXM_V2"):
    res = json.loads((HERE / f"DEV_RESULT_{model}.json").read_text())
    assert res["dev_gate"] == "FAIL" and res["prereg_aggregate"].startswith("37fcf7a3")
    r = pd.read_csv(HERE / f"DEV_TRADES_{model}.csv")["R"]
    notes = (f"V2 DEV look, pooled pairs, dev_gate FAIL -> KILLED (revenue sprint 2026-09-24); sealed FX/XAU "
             f"2025-01-01..2026-08-31 never read; verdict file {model.split('_')[0].lower()}_v2/{model}_DEV_VERDICT.md")
    if model == "TRIDENT_V2":
        i = r.idxmax()
        notes += (f"; METRIC DEFECT: one XAUUSD close-stop trade scored R={r[i]:.1f} (risk_override = doji range "
                  f"$0.11); sr_per_trade with it {sr(r):.4f} (registered, frozen-evaluator output), without it "
                  f"{sr(r.drop(i)):.4f} (n={len(r) - 1}); neither is a variance outlier")
    e = register_trial({
        "id": f"V2-{model}-DEV", "family": FAMILY[model],
        "dataset": ",".join(f"data/fx_histdata/{p}_1m_bid.parquet" for p in PAIRS[model]),
        "dataset_group": "FX_SPOT_HISTDATA", "data_window": {"start": "2022-01-01", "end": "2024-12-31"},
        "window_status": "DEV", "n_configs": 1, "verdict": "FAIL / KILLED",
        "sr_per_trade": sr(r), "n_trades": int(len(r)),
        "source": f"workspace/revenue_sprint_2026-09-24/DEV_RESULT_{model}.json; prereg aggregate {res['prereg_aggregate']}",
        "notes": notes})
    print(e["id"], e["sr_per_trade"], e["n_trades"], e["entry_hash"][:12])
