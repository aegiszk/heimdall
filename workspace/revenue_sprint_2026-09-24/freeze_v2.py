"""(Re)writes V2_PREREG_MANIFEST.json: SHA-256 of every frozen V2 file + datasets. Run only before any V2 PnL.
Each run appends the previous aggregate to `supersedes` so the freeze history is auditable."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FILES = ["trident_v2/strategy.py", "trident_v2/TRIDENT_V2_SOURCE_SPEC.md", "trident_v2/TRIDENT_V2_PREREGISTRATION.md",
         "mmxm_v2/strategy.py", "mmxm_v2/MMXM_V2_SOURCE_SPEC.md", "mmxm_v2/MMXM_V2_PREREGISTRATION.md",
         "evaluate_v2.py", "fidelity_v2.py", "freeze_v2.py"]
SHARED = ["workspace/external_strategies/common/harness.py", "workspace/external_strategies/common/stats.py",
          "workspace/external_strategies/common/registry.py"]
DATA = [f"data/fx_histdata/{p}_1m_bid.parquet" for p in ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "NZDUSD", "XAUUSD"]]
MUST_NOT_READ_BEFORE_SEALED = [
    "data/sierra/GC_continuous_1m_latest_90d.parquet (2026-06-23..2026-09-21 overlaps sealed XAU window)",
    "data/sierra/MGC_continuous_1m_latest_90d.parquet (same)",
    "C:/SierraChart/QUARANTINE_sealed_fx_xau_dly_2026-09-24/* (EURUSD/XAUUSD spot + GC/MGC daily; see SEALED_FX_DLY_QUARANTINE.json)",
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


rel = ["workspace/revenue_sprint_2026-09-24/" + f for f in FILES] + SHARED
files = {r: sha(ROOT / r) for r in rel}
agg = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
old = json.loads((HERE / "V2_PREREG_MANIFEST.json").read_text()) if (HERE / "V2_PREREG_MANIFEST.json").exists() else {}
sup = old.get("supersedes", []) + ([old["aggregate_sha256"]] if old.get("aggregate_sha256") and old["aggregate_sha256"] != agg else [])
out = {"frozen_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "base_sha": "a1486c4738bb96babaed396fe9163a86a679506b", "note": "frozen before any V2 PnL",
       "files": files, "datasets": {d: sha(ROOT / d) for d in DATA}, "must_not_read_before_sealed": MUST_NOT_READ_BEFORE_SEALED,
       "aggregate_sha256": agg, "supersedes": sup}
(HERE / "V2_PREREG_MANIFEST.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(agg, "supersedes", sup)
