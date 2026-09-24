"""Session value area, as frozen in VA_REACCEPTANCE_PREREGISTRATION.md."""

from __future__ import annotations

from collections.abc import Mapping


def value_area(profile: Mapping[float, float], fraction: float = 0.70) -> tuple[float, float, float]:
    """Return (poc, val, vah) for a price -> volume profile.

    POC is the highest-volume price, ties choose the lower price. From the POC,
    repeatedly add the adjacent unincluded traded price above or below with
    greater volume, ties add the lower price, until included volume reaches
    ``fraction`` of the total.
    """
    prices = sorted(price for price, volume in profile.items() if volume > 0)
    total = float(sum(profile[price] for price in prices))
    if not prices or total <= 0:
        raise ValueError("value_area needs a profile with positive volume")

    poc_i = min(range(len(prices)), key=lambda i: (-profile[prices[i]], prices[i]))
    lo = hi = poc_i
    included = float(profile[prices[poc_i]])
    while included < fraction * total:
        below = profile[prices[lo - 1]] if lo > 0 else None
        above = profile[prices[hi + 1]] if hi + 1 < len(prices) else None
        if above is None or (below is not None and below >= above):
            lo -= 1
            included += float(profile[prices[lo]])
        else:
            hi += 1
            included += float(profile[prices[hi]])
    return float(prices[poc_i]), float(prices[lo]), float(prices[hi])
