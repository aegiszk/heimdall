"""Reservoir (s3://hydromancer-reservoir, requester-pays) COST DISCOVERY — NOT YET EXECUTED.

Needs owner approval + AWS credentials (env AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY or a profile).
It performs ONLY:
  1. ListObjectsV2 on the exact date-partition prefixes each experiment needs (RequestPayer=requester).
  2. For a small sample of files: ranged GETs of the Parquet footer (last <=1 MiB) to read row-group
     statistics, so we can tell whether a coin subset (BTC/ETH/SOL, xyz:SP500/XYZ100) can be read
     selectively instead of downloading whole daily files.
It NEVER downloads a whole object. Output: reservoir_cost_discovery.json with bytes per experiment and
estimated charges at the verified ap-northeast-1 prices (AWS price list, published 2026-09-16/18):
  data transfer out to internet $0.114/GB (first 10 TB/month); LIST $0.0047 per 1,000;
  GET $0.0037 per 10,000.

Run (after approval):  pip install boto3 && python reservoir_cost_discovery.py
"""

from __future__ import annotations

import datetime as dt
import io
import json
import struct
from pathlib import Path

BUCKET = "hydromancer-reservoir"
REGION = "ap-northeast-1"
PRICE_EGRESS_PER_GB = 0.114
PRICE_LIST_PER_REQ = 0.0047 / 1000
PRICE_GET_PER_REQ = 0.0037 / 10000
FOOTER_SAMPLE_FILES = 3  # per dataset
MAX_FOOTER_BYTES = 1 << 20


def dates(a: str, b: str) -> list[str]:
    d0, d1 = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    return [(d0 + dt.timedelta(n)).isoformat() for n in range((d1 - d0).days + 1)]


H1_WINDOWS = [("2025-08-04", "2025-08-10"), ("2025-11-03", "2025-11-09"),
              ("2026-03-02", "2026-03-08"), ("2026-08-03", "2026-08-09")]
EXPERIMENTS = {
    # H1: bounded BTC/ETH/SOL subset; main-dex daily files contain all coins -> footer tells if selectable.
    "H1": [("by_dex/hyperliquid/fills/perp/all", d) for a, b in H1_WINDOWS for d in dates(a, b)],
    # H2: xyz dex only (SP500/XYZ100 rows), full listed history to the latest daily partition.
    "H2": [("by_dex/xyz/fills/perp/all", d) for d in dates("2025-10-13", "2026-09-22")],
    # H3: TWAP fills (all coins, small) over the post-paper period; price path reuses H1 windows / Tardis.
    "H3": [("by_dex/hyperliquid/fills/perp/twap_fills", d) for d in dates("2026-03-24", "2026-09-22")],
    # H4: liquidation fills, full history (small, only non-empty days exist).
    "H4": [("by_dex/hyperliquid/fills/perp/liquidations", d) for d in dates("2025-07-28", "2026-09-22")],
}


def footer_metadata(blob: bytes):
    """Parse Parquet FileMetaData from footer bytes only (metadata + 4-byte length + b'PAR1')."""
    import pyarrow.parquet as pq

    return pq.read_metadata(io.BytesIO(b"PAR1" + blob))


def footer_row_groups(s3, key: str, size: int) -> dict:
    """Ranged GETs only: read the Parquet footer and summarize row-group coin statistics."""
    import pyarrow.parquet as pq

    tail_len = min(size, 8)
    tail = s3.get_object(Bucket=BUCKET, Key=key, Range=f"bytes={size - tail_len}-{size - 1}",
                         RequestPayer="requester")["Body"].read()
    meta_len = struct.unpack("<I", tail[:4])[0]
    if tail[4:] != b"PAR1" or meta_len + 8 > MAX_FOOTER_BYTES:
        return {"key": key, "error": "not parquet or footer too large", "footer_len": meta_len}
    start = size - meta_len - 8
    blob = s3.get_object(Bucket=BUCKET, Key=key, Range=f"bytes={start}-{size - 1}",
                         RequestPayer="requester")["Body"].read()
    md = footer_metadata(blob)
    coin_idx = md.schema.names.index("coin") if "coin" in md.schema.names else None
    groups = []
    for i in range(md.num_row_groups):
        rg = md.row_group(i)
        stats = rg.column(coin_idx).statistics if coin_idx is not None else None
        groups.append({"rows": rg.num_rows, "bytes": rg.total_byte_size,
                       "coin_min": getattr(stats, "min", None), "coin_max": getattr(stats, "max", None)})
    return {"key": key, "rows": md.num_rows, "row_groups": len(groups),
            "coin_sorted_selectable": all(g["coin_min"] == g["coin_max"] for g in groups) if groups else None,
            "groups_head": groups[:10]}


def main() -> None:
    import boto3

    s3 = boto3.client("s3", region_name=REGION)
    report: dict = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "experiments": {}}
    list_calls = get_calls = 0
    for name, parts in EXPERIMENTS.items():
        total_bytes, objects, missing, footers = 0, 0, 0, []
        for prefix, day in parts:
            resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{prefix}/date={day}/", RequestPayer="requester")
            list_calls += 1
            contents = resp.get("Contents", [])
            if not contents:
                missing += 1
                continue
            for obj in contents:
                total_bytes += obj["Size"]
                objects += 1
                if len(footers) < FOOTER_SAMPLE_FILES and obj["Key"].endswith(".parquet"):
                    footers.append(footer_row_groups(s3, obj["Key"], obj["Size"]))
                    get_calls += 2
        gb = total_bytes / 1e9
        report["experiments"][name] = {
            "partitions_requested": len(parts), "partitions_missing": missing, "objects": objects,
            "bytes_full_files": total_bytes, "gb_full_files": round(gb, 3),
            "est_egress_usd_full_files": round(gb * PRICE_EGRESS_PER_GB, 2), "footer_samples": footers,
        }
    report["discovery_request_cost_usd"] = round(list_calls * PRICE_LIST_PER_REQ + get_calls * PRICE_GET_PER_REQ, 5)
    report["discovery_egress_upper_bound_usd"] = round(get_calls * MAX_FOOTER_BYTES / 1e9 * PRICE_EGRESS_PER_GB, 5)
    Path(__file__).with_name("reservoir_cost_discovery.json").write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "footer_samples"}
                      for k, v in report["experiments"].items()}, indent=1))
    print("discovery cost (requests):", report["discovery_request_cost_usd"], "USD")


if __name__ == "__main__":
    main()
