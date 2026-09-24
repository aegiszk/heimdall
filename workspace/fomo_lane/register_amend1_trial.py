"""Registers the FOMO prospective re-registration (Amendment 1) as a PENDING trial BEFORE the amended recorder starts.
Run once. Window = restart date .. restart + 45 days (FOMO_PROSPECTIVE_PREREGISTRATION_AMENDMENT_1.md section 4)."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from trials_ledger import register_trial  # noqa: E402

start = pd.Timestamp.now("UTC").normalize()
e = register_trial({
    "id": "FOMO-PROSPECTIVE-AMEND1", "family": "copy_fixed_exit_safety",
    "dataset": "workspace/fomo_lane/data_amend1 (prospective recorder, Robinhood Chain 4663)",
    "dataset_group": "ROBINHOOD_CHAIN_FOMO",
    "data_window": {"start": start.strftime("%Y-%m-%d"), "end": (start + pd.Timedelta(days=45)).strftime("%Y-%m-%d")},
    "window_status": "PROSPECTIVE", "n_configs": 1, "verdict": "PENDING",
    "source": "FOMO_PROSPECTIVE_PREREGISTRATION.md 902263424c17...; FOMO_PROSPECTIVE_PREREGISTRATION_AMENDMENT_1.md fd87cfb8...",
    "notes": ("re-registration of the identical hypothesis after runs 1-4 were VOID (feed_missing_frac 0.865 > 5%); "
              "no outcome of runs 1-4 was computed (not looks); stopping: >=3,500 eligible_counted and >=14 days, or 45 days, "
              "clocks from the amended restart; checker ruling Agent 2, owner acknowledged 2026-09-24")})
print(e["id"], e["data_window"], e["entry_hash"][:12])
