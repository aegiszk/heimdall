import pandas as pd

from core.alpha.orderflow_footprint import volume_area


def test_volume_area_uses_actual_price_levels_and_lower_tie_break():
    levels = pd.DataFrame(
        {
            "price": [99.75, 100.0, 100.25],
            "volume": [30, 40, 30],
        }
    )

    val, vah = volume_area(levels)

    assert val == 99.75
    assert vah == 100.0
