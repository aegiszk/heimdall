"""Tests for the split validator (core/validation/gates.py) and the trials ledger (tools/trials_ledger.py)."""
import json
import os
import shutil
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config import DEFAULT_GATE_CFG
from core.validation import battery, gates, metrics
from tools import trials_ledger as tl

GOOD_EXEC = {"cost_model_id": "lucid_mnq_rt1_slip1tick_v1", "capacity_estimate": 10.0, "tail_loss_estimate": 150.0}


def clustered_series(rng, n_clusters, per_cluster, mu, sd_cluster, sd_noise):
    eff = rng.normal(0.0, sd_cluster, n_clusters)
    vals = np.repeat(eff, per_cluster) + rng.normal(0.0, sd_noise, n_clusters * per_cluster) + mu
    cl = np.repeat(np.arange(n_clusters), per_cluster)
    return vals, cl


# --------------------------------------------------------------------------- discovery gate
def test_null_discovery_pass_rate_at_most_about_alpha_under_clustering():
    rng = np.random.default_rng(123)
    sims, passes = 300, 0
    for i in range(sims):
        v, cl = clustered_series(rng, 60, 5, 0.0, 1.0, 1.0)
        res = gates.discovery_gate(v, cl, min_useful_edge=0.3, alpha=0.10, n_boot=400, seed=i)
        passes += res["verdict"] == "PASS"
    rate = passes / sims
    # nominal 0.10; allow Monte Carlo error (sd ~0.017 at 300 sims) + small percentile-bootstrap bias
    assert rate <= 0.15, rate


def test_iid_bootstrap_would_overreject_the_same_clustered_null():
    """Control: ignoring the clustering (iid resampling) over-rejects on the same null."""
    rng = np.random.default_rng(123)
    sims, passes = 300, 0
    for i in range(sims):
        v, _ = clustered_series(rng, 60, 5, 0.0, 1.0, 1.0)
        iid_cl = np.arange(len(v))  # each trade its own cluster = iid bootstrap
        passes += gates.discovery_gate(v, iid_cl, min_useful_edge=0.3, n_boot=400, seed=i)["verdict"] == "PASS"
    assert passes / sims > 0.15


def test_strong_edge_discovery_pass_and_never_authorizes_capital():
    rng = np.random.default_rng(7)
    v, cl = clustered_series(rng, 100, 4, 0.6, 0.5, 1.0)
    res = gates.discovery_gate(v, cl, min_useful_edge=0.2, n_boot=1000)
    assert res["verdict"] == "PASS"
    assert res["authorizes_capital"] is False


def test_discovery_fail_when_useful_edge_excluded_and_na_on_empty():
    rng = np.random.default_rng(8)
    v, cl = clustered_series(rng, 200, 3, -0.5, 0.2, 1.0)
    assert gates.discovery_gate(v, cl, min_useful_edge=0.2)["verdict"] == "FAIL"
    empty = gates.discovery_gate([], None, min_useful_edge=0.2)
    assert empty["verdict"] == "N/A" and empty["authorizes_capital"] is False


def test_discovery_inconclusive_underpowered_small_sample():
    rng = np.random.default_rng(9)
    v = rng.normal(0.05, 1.0, 40)
    res = gates.discovery_gate(v, None, min_useful_edge=0.1, min_useful_sr=0.1)
    assert res["verdict"] == "INCONCLUSIVE"
    assert "UNDERPOWERED" in res["flags"]
    assert res["method"] == "moving_block"


def test_clusters_inflate_ci_vs_iid():
    rng = np.random.default_rng(11)
    v, cl = clustered_series(rng, 50, 8, 0.0, 1.0, 0.5)
    c = gates.cluster_bootstrap_mean_ci(v, cl, n_boot=2000, seed=0)
    i = gates.cluster_bootstrap_mean_ci(v, np.arange(len(v)), n_boot=2000, seed=0)
    assert (c["ci_hi"] - c["ci_lo"]) > 1.5 * (i["ci_hi"] - i["ci_lo"])
    assert c["design_effect"] > 3.0 and abs(i["design_effect"] - 1.0) < 0.25
    assert c["n_eff"] < len(v) / 3
    assert c["n_clusters"] == 50


def test_moving_block_detects_autocorrelation():
    rng = np.random.default_rng(12)
    e = rng.normal(size=2000)
    x = np.empty_like(e)
    x[0] = e[0]
    for t in range(1, len(e)):
        x[t] = 0.6 * x[t - 1] + e[t]
    res = gates.cluster_bootstrap_mean_ci(x, None, n_boot=2000, seed=0, block_len=40)
    assert res["design_effect"] > 2.0  # AR(1) 0.6 long-run variance ratio = (1+rho)/(1-rho) = 4


def test_required_n_matches_reference_and_scales_with_design_effect():
    assert gates.required_n(0.10, 0.10, 0.80) == 451          # VALIDATION_COMPLETION section 6
    assert gates.required_n(0.20, 0.10, 0.80) == 113
    assert gates.required_n(0.10, 0.05, 0.80) == 619           # 618.3 -> ceil (doc table rounds to 618)
    assert gates.required_n(0.10, 0.10, 0.80, 2.0) == pytest.approx(2 * 450.8, abs=1)
    assert gates.required_n(0.10, 0.10, 0.80, 0.5) == 451      # floored at deff 1
    with pytest.raises(ValueError):
        gates.required_n(0.0)


def test_benjamini_hochberg():
    mask = gates.benjamini_hochberg([0.001, 0.2, 0.03, 0.04], q=0.10)
    assert mask.tolist() == [True, False, True, True]


# --------------------------------------------------------------------------- all-folds consistency
def test_all_folds_consistency_scores_every_trade_and_legacy_drops_first_fold():
    x = np.arange(60, dtype=float)
    res = gates.subperiod_consistency_all_folds(x, 5)
    assert res["n_scored"] == 60 and sum(res["fold_sizes"]) == 60 and len(res["fold_sharpes"]) == 5
    legacy_folds = np.array_split(x, 5 + 1)
    assert len(legacy_folds[0]) == 10                          # legacy never scores these 10 trades
    assert len(metrics.walk_forward(x, 5)) == 5                # legacy behaviour unchanged
    # a series whose ONLY losing stretch is the first sixth: legacy passes, all-folds catches it
    rng = np.random.default_rng(0)
    y = np.concatenate([rng.normal(-1.0, 0.5, 50), rng.normal(1.0, 0.5, 250)])
    assert min(metrics.walk_forward(y, 5)) > 0
    assert gates.subperiod_consistency_all_folds(y, 5)["min_sharpe"] < 0


# --------------------------------------------------------------------------- deployment gate
def _edge_stream(n=600, mu=40.0, sd=100.0, seed=1):
    return np.random.default_rng(seed).normal(mu, sd, n)


def _matrix(seed=0, T=600, N=10):
    rng = np.random.default_rng(seed)
    M = rng.normal(0, 1, (T, N))
    M[:, 0] += 0.4
    return M


REQUIRED_AXES = {"ALPHA", "EXECUTION", "DEPLOYMENT"}


def _check_schema(res):
    assert set(res["axes"]) == REQUIRED_AXES
    for ax in res["axes"].values():
        assert ax["verdict"] in gates.VERDICTS and isinstance(ax["reasons"], list)
    assert res["RISK"]["verdict"] in gates.VERDICTS
    assert isinstance(res["deployment_eligible"], bool)


@pytest.mark.parametrize("status", ["DEV", "REUSED_HOLDOUT"])
def test_deployment_gate_fails_dev_or_reused_window(status):
    res = gates.deployment_gate(_edge_stream(), window_status=status, nb_trials=1, ledger_sr_trials_var=None,
                                candidate_matrix=_matrix(), execution=GOOD_EXEC, risk_per_trade=100.0,
                                declared_capital=50_000, n_boot=300)
    _check_schema(res)
    assert res["axes"]["ALPHA"]["verdict"] == "FAIL"
    assert "reused_window" in res["axes"]["ALPHA"]["reasons"]
    assert res["axes"]["DEPLOYMENT"]["verdict"] == "FAIL" and not res["deployment_eligible"]


def test_deployment_gate_strong_edge_fresh_window_passes_all_axes():
    res = gates.deployment_gate(_edge_stream(), window_status="FRESH", nb_trials=65,
                                ledger_sr_trials_var=0.00345, candidate_matrix=_matrix(), execution=GOOD_EXEC,
                                risk_per_trade=100.0, declared_capital=50_000, n_boot=300)
    _check_schema(res)
    assert res["axes"]["ALPHA"]["verdict"] == "PASS", res["axes"]["ALPHA"]
    assert res["axes"]["EXECUTION"]["verdict"] == "PASS"
    assert res["RISK"]["verdict"] == "PASS"
    assert res["axes"]["DEPLOYMENT"]["verdict"] == "PASS" and res["deployment_eligible"]
    assert res["metrics"]["sr_trials_var_used"] == pytest.approx(0.00345)
    assert res["metrics"]["subperiod"]["n_scored"] == 600
    assert res["thresholds"] == {k: DEFAULT_GATE_CFG[k] for k in sorted(DEFAULT_GATE_CFG)}


def test_deployment_gate_without_pbo_matrix_capped_inconclusive():
    res = gates.deployment_gate(_edge_stream(), window_status="PROSPECTIVE", nb_trials=1, ledger_sr_trials_var=None,
                                execution=GOOD_EXEC, risk_per_trade=100.0, declared_capital=50_000, n_boot=300)
    assert res["axes"]["ALPHA"]["verdict"] == "INCONCLUSIVE"
    assert "pbo_unavailable" in res["axes"]["ALPHA"]["reasons"]
    assert res["axes"]["DEPLOYMENT"]["verdict"] == "INCONCLUSIVE"


def test_deployment_gate_missing_execution_fields_inconclusive():
    res = gates.deployment_gate(_edge_stream(), window_status="FRESH", nb_trials=1, ledger_sr_trials_var=None,
                                candidate_matrix=_matrix(), execution={"cost_model_id": "x"},
                                risk_per_trade=100.0, declared_capital=50_000, n_boot=300)
    ex = res["axes"]["EXECUTION"]
    assert ex["verdict"] == "INCONCLUSIVE"
    assert {"missing_capacity_estimate", "missing_tail_loss_estimate"} <= set(ex["reasons"])
    assert res["axes"]["DEPLOYMENT"]["verdict"] != "PASS"


def test_deployment_gate_sr_trials_var_floored_at_one_over_n_and_ledger_deflation_bites():
    x = _edge_stream(n=300, mu=12.0, sd=100.0, seed=3)  # SR ~0.12 per trade
    lo = gates.deployment_gate(x, window_status="FRESH", nb_trials=1, ledger_sr_trials_var=0.0,
                               candidate_matrix=_matrix(), execution=GOOD_EXEC, n_boot=200)
    hi = gates.deployment_gate(x, window_status="FRESH", nb_trials=65, ledger_sr_trials_var=0.00345,
                               candidate_matrix=_matrix(), execution=GOOD_EXEC, n_boot=200)
    assert lo["metrics"]["sr_trials_var_used"] == pytest.approx(1 / 300)
    assert hi["metrics"]["sr0"] > 0.1 and hi["metrics"]["dsr"] < lo["metrics"]["dsr"]


def test_max_dd_pathology_exists_in_legacy_and_is_quarantined_to_risk_axis():
    """N2: at sd $400/trade a positive edge (SR 0.10) is failed by legacy max_dd as N grows; the new gate
    reports it on RISK only, never as an ALPHA reason."""
    x = np.random.default_rng(5).normal(40.0, 400.0, 2000)
    legacy = battery.run_gate(x / 50_000, DEFAULT_GATE_CFG, 1, 0.0)
    assert "max_dd" in legacy.reasons                       # documented legacy pathology (unchanged)
    res = gates.deployment_gate(x, window_status="FRESH", nb_trials=1, ledger_sr_trials_var=None,
                                candidate_matrix=_matrix(), execution=GOOD_EXEC, risk_per_trade=400.0,
                                declared_capital=50_000, n_boot=200)
    assert "max_dd" not in res["axes"]["ALPHA"]["reasons"]
    assert res["RISK"]["verdict"] == "FAIL" and "max_dd" in res["RISK"]["reasons"]
    assert res["RISK"]["max_dd_R"] == pytest.approx(res["RISK"]["max_dd_amount"] / 400.0)
    assert res["RISK"]["max_dd_frac_capital"] == pytest.approx(res["RISK"]["max_dd_amount"] / 50_000)
    assert "RISK:max_dd" in res["axes"]["DEPLOYMENT"]["reasons"]


def test_legacy_run_gate_still_callable_and_unchanged_thresholds():
    assert DEFAULT_GATE_CFG == {"dsr_min": 0.95, "nw_t_min": 2.0, "boot_lo_min": 0.0, "max_dd_max": 0.08,
                                "min_trades": 30, "max_params": 6, "wf_min_sharpe": 0.0,
                                "pbo_max": 0.05, "mc_p_max": 0.05, "wf_splits": 5, "pbo_S": 8}
    r = battery.run_gate(np.random.default_rng(0).normal(0.001, 0.01, 200), DEFAULT_GATE_CFG, 1, 0.0)
    assert isinstance(r, battery.GateResult)


# --------------------------------------------------------------------------- ledger
@pytest.fixture
def ledger_copy(tmp_path):
    p = tmp_path / "ledger.json"
    shutil.copy(tl.LEDGER_PATH, p)
    return p


def test_ledger_integrity_and_reference_numbers():
    led = tl.load_ledger()
    assert tl.verify_ledger(led) == []
    W = tl.HOLDOUT_6040
    exact = [e for e in led["entries"] if e["data_window"] == W and not e["is_null_control"]]
    assert sum(e["n_configs"] for e in exact) == 65           # VALIDATION_COMPLETION section 7
    assert tl.empirical_sr_trials_var(W, tl.IDX, led) == pytest.approx(0.003449473183343993, rel=1e-9)
    assert tl.nb_trials(W, tl.IDX, led, "configs") >= 65
    fomo_w = {"start": "2026-09-05T07:38Z", "end": "2026-09-22T19:42Z"}
    assert tl.nb_trials(fomo_w, "ROBINHOOD_CHAIN_FOMO", led) == 153
    assert tl.nb_trials(fomo_w, "ROBINHOOD_CHAIN_FOMO", led, "families") == 6
    assert all(e["window_status"] == "DEV" for e in led["entries"] if e["dataset_group"] == "ROBINHOOD_CHAIN_FOMO")


def test_ledger_append_only(ledger_copy):
    led = tl.load_ledger(ledger_copy)
    first = led["entries"][0]
    with pytest.raises(ValueError, match="append-only"):
        tl.register_trial({**first, "verdict": "PASS"}, ledger_copy)
    new = {"id": "TEST-prospective-1", "family": "test", "dataset": "x", "dataset_group": tl.IDX,
           "data_window": {"start": "2026-10-01", "end": "2026-12-31"}, "window_status": "PROSPECTIVE",
           "n_configs": 1, "verdict": "PENDING"}
    e = tl.register_trial(new, ledger_copy, registered_at="2026-09-23T00:00:00+00:00")
    after = tl.load_ledger(ledger_copy)
    assert after["entries"][-1]["id"] == "TEST-prospective-1" and e["prev_hash"] == led["entries"][-1]["entry_hash"]
    assert tl.verify_ledger(after) == []
    # tampering with an existing entry is detected and blocks further appends
    after["entries"][3]["verdict"] = "PASS"
    ledger_copy.write_text(json.dumps(after))
    assert tl.verify_ledger(tl.load_ledger(ledger_copy))
    with pytest.raises(RuntimeError, match="integrity"):
        tl.register_trial({**new, "id": "TEST-2"}, ledger_copy)


def test_window_freshness_and_gate_inputs(ledger_copy):
    led = tl.load_ledger(ledger_copy)
    assert not tl.window_is_fresh(tl.HOLDOUT_6040, tl.IDX, led)
    assert not tl.window_is_fresh({"start": "2026-07-01", "end": "2026-09-18"}, tl.IDX, led)  # already read
    future = {"start": "2026-10-01", "end": "2026-12-31"}
    assert tl.window_is_fresh(future, tl.IDX, led)
    gi = tl.gate_inputs(tl.HOLDOUT_6040, tl.IDX, led, declared_status="FRESH")
    assert gi["window_status"] == "REUSED_HOLDOUT"             # declaration cannot override the ledger
    gp = tl.gate_inputs(future, tl.IDX, led, declared_status="PROSPECTIVE")
    assert gp["window_status"] == "PROSPECTIVE" and gp["nb_trials"] == 1
    res = gates.deployment_gate(_edge_stream(), **{k: gi[k] for k in ("window_status", "nb_trials",
                                                                       "ledger_sr_trials_var")},
                                candidate_matrix=_matrix(), execution=GOOD_EXEC, n_boot=200)
    assert res["axes"]["ALPHA"]["verdict"] == "FAIL" and "reused_window" in res["axes"]["ALPHA"]["reasons"]
