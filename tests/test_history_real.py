import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.data.history import REQUIRED_COLUMNS, load_history
from loop import run_paper_backtest


def test_btc_real_history_and_funnel_verdicts():
    venue_perp = os.environ.get("HEIMDALL_HISTORY_VENUE_PERP")
    venue_spot = os.environ.get("HEIMDALL_HISTORY_VENUE_SPOT")
    if venue_perp or venue_spot:
        df = load_history(
            "BTC",
            venue_perp=venue_perp or "okx",
            venue_spot=venue_spot or "okx",
        )
    else:
        df = load_history("BTC")

    assert list(df.columns) == REQUIRED_COLUMNS
    assert len(df) >= 24 * 365 * 2
    assert (df.index[-1] - df.index[0]).days >= 730
    assert not df[REQUIRED_COLUMNS].isna().any().any()

    periods_per_year = 24 * 365
    mean_funding_bps_annualized = df["funding"].mean() * periods_per_year * 10_000
    pct_funding_positive = (df["funding"] > 0).mean() * 100
    mean_basis_bps = df["basis_noise"].mean() * 10_000

    print(
        "\nBTC real history:",
        f"rows={len(df)}",
        f"range={df.index[0].isoformat()}->{df.index[-1].isoformat()}",
        f"mean_funding_bps_annualized={mean_funding_bps_annualized:.2f}",
        f"pct_funding_positive={pct_funding_positive:.2f}",
        f"mean_basis_bps={mean_basis_bps:.2f}",
    )

    for fam, res in run_paper_backtest(df=df):
        print(fam.name, res.passed, round(res.dsr, 3), round(res.nw_t, 2), res.reasons)
