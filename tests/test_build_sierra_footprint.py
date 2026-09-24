import pandas as pd
import pyarrow.parquet as pq

from tools.build_sierra_footprint import build_footprint


def test_aggregates_rth_ticks_by_minute_and_price_across_batches(tmp_path):
    source = tmp_path / "ticks.parquet"
    destination = tmp_path / "footprint.parquet"
    pd.DataFrame(
        {
            "ts": pd.to_datetime(
                [
                    "2026-09-01 13:29:59Z",
                    "2026-09-01 13:30:00Z",
                    "2026-09-01 13:30:01Z",
                    "2026-09-01 13:30:02Z",
                    "2026-09-01 13:31:00Z",
                ],
                utc=True,
            ),
            "close": [100.0, 100.0, 100.0, 100.25, 100.25],
            "num_trades": [1, 1, 1, 1, 1],
            "volume": [1, 2, 3, 4, 5],
            "bid_volume": [1, 2, 0, 4, 0],
            "ask_volume": [0, 0, 3, 0, 5],
        }
    ).to_parquet(source, index=False)

    source_rows, output_rows = build_footprint(source, destination, batch_size=2)
    result = pq.read_table(destination).to_pandas()

    assert source_rows == 5
    assert output_rows == 3
    assert result[["minute", "price", "volume", "bid_volume", "ask_volume"]].to_dict("records") == [
        {"minute": pd.Timestamp("2026-09-01 13:30:00+00:00"), "price": 100.0, "volume": 5, "bid_volume": 2, "ask_volume": 3},
        {"minute": pd.Timestamp("2026-09-01 13:30:00+00:00"), "price": 100.25, "volume": 4, "bid_volume": 4, "ask_volume": 0},
        {"minute": pd.Timestamp("2026-09-01 13:31:00+00:00"), "price": 100.25, "volume": 5, "bid_volume": 0, "ask_volume": 5},
    ]
    first_bar = result[result["minute"] == pd.Timestamp("2026-09-01 13:30:00+00:00")].iloc[0]
    assert (first_bar.bar_open, first_bar.bar_high, first_bar.bar_low, first_bar.bar_close) == (
        100.0,
        100.25,
        100.0,
        100.25,
    )
