"""Quote Databento costs for MNQ Fabio ORB tests without pulling data."""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass


DATASET = "GLBX.MDP3"
START = "2024-07-01T00:00:00Z"
END = "2026-07-01T00:00:00Z"
STOP_COST_USD = 50.0


@dataclass(frozen=True)
class QuoteRequest:
    label: str
    schema: str
    symbols: str
    stype_in: str = "continuous"


def main() -> int:
    args = parse_args()
    if not os.getenv("DATABENTO_API_KEY"):
        print("BLOCKED: DATABENTO_API_KEY is not set; cannot run no-charge Databento get_cost quotes.")
        print("No data was pulled and no charge was incurred.")
        print(f"quote_window start={args.start} end={args.end} dataset={DATASET}")
        print("phase_a_request schema=ohlcv-1m symbols=MNQ.v.0 stype_in=continuous")
        print("phase_b_requests schema=mbp-1/mbo symbols=MNQ.v.0 and NQ.v.0 stype_in=continuous")
        return 2

    import databento as db

    client = db.Historical()
    requests = [QuoteRequest("phase_a_mnq_ohlcv_1m", "ohlcv-1m", "MNQ.v.0")]
    if args.phase_b:
        requests.extend(
            [
                QuoteRequest("phase_b_mnq_mbp1", "mbp-1", "MNQ.v.0"),
                QuoteRequest("phase_b_mnq_mbo", "mbo", "MNQ.v.0"),
                QuoteRequest("phase_b_nq_mbp1", "mbp-1", "NQ.v.0"),
                QuoteRequest("phase_b_nq_mbo", "mbo", "NQ.v.0"),
            ]
        )

    print("DATABENTO COST QUOTES ONLY")
    print("method=Historical.metadata.get_cost no_data_pull=true")
    print(f"dataset={DATASET} start={args.start} end={args.end}")
    rows = [["label", "schema", "symbols", "stype_in", "estimated_cost_usd", "decision"]]
    stop = False
    for req in requests:
        cost = float(
            client.metadata.get_cost(
                dataset=DATASET,
                symbols=req.symbols,
                schema=req.schema,
                stype_in=req.stype_in,
                start=args.start,
                end=args.end,
            )
        )
        decision = "STOP_REPORT" if cost > STOP_COST_USD else "QUOTE_OK_WAIT_FOR_APPROVAL"
        stop = stop or cost > STOP_COST_USD
        rows.append([req.label, req.schema, req.symbols, req.stype_in, f"{cost:.6f}", decision])
    print_table(rows)
    if stop:
        print(f"GUARDRAIL: at least one quote exceeded ${STOP_COST_USD:.2f}; do not pull.")
        return 3
    print("GUARDRAIL: all quoted costs are <= $50.00. Still do not pull until human approval.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="No-charge Databento get_cost quotes for Fabio ORB work.")
    parser.add_argument("--start", default=START)
    parser.add_argument("--end", default=END)
    parser.add_argument("--phase-b", action="store_true", help="Also quote MBP-1/MBO tick-level data.")
    return parser.parse_args()


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(row[i]).rjust(widths[i]) for i in range(len(row))))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


if __name__ == "__main__":
    sys.exit(main())
