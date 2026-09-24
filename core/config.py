"""Gate thresholds (money-path config). In production these live in an admin-approved DB row."""
DEFAULT_GATE_CFG = {
    "dsr_min": 0.95, "nw_t_min": 2.0, "boot_lo_min": 0.0, "max_dd_max": 0.08,
    "min_trades": 30, "max_params": 6, "wf_min_sharpe": 0.0,
    "pbo_max": 0.05, "mc_p_max": 0.05, "wf_splits": 5, "pbo_S": 8,
}
