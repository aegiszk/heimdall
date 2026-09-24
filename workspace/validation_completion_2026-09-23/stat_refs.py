"""Independent references for Heimdall's metrics.py (run in extvenv: statsmodels 0.15.0, scipy).
metrics.py is loaded by file path (no package import side effects); formulas re-derived here."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("hm", ROOT / "core" / "validation" / "metrics.py")
hm = importlib.util.module_from_spec(spec); spec.loader.exec_module(hm)

rng = np.random.default_rng(7)
res = {"nw_max_abs_diff": 0.0, "psr_max_abs_diff": 0.0, "dsr_max_abs_diff": 0.0}
for n in (30, 57, 100, 493, 2000):
    for _ in range(20):
        e = rng.standard_normal(n)
        x = 0.1 + np.convolve(e, [1, 0.4], "same") * rng.uniform(0.5, 2)
        lags = int(np.floor(4 * (n / 100.0) ** (2 / 9)))
        ols = sm.OLS(x, np.ones(n)).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
        res["nw_max_abs_diff"] = max(res["nw_max_abs_diff"], abs(float(ols.tvalues[0]) - hm.newey_west_tstat(x)))
        # PSR, Bailey & Lopez de Prado 2012 eq: z = (SR-SR*) sqrt(n-1) / sqrt(1 - g3 SR + (g4-1)/4 SR^2)
        sr = x.mean() / x.std(ddof=1); g3 = stats.skew(x); g4 = stats.kurtosis(x, fisher=False)
        for bench in (0.0, 0.05):
            ref = stats.norm.cdf((sr - bench) * np.sqrt(n - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))
            res["psr_max_abs_diff"] = max(res["psr_max_abs_diff"], abs(ref - hm.probabilistic_sharpe_ratio(x, bench)))
        # DSR, Bailey & Lopez de Prado 2014: SR0 = sqrt(V) ((1-g) Z^-1(1-1/N) + g Z^-1(1-1/(N e)))
        for V, N in ((0.0, 1), (1.0, 2), (0.004, 25)):
            g = 0.5772156649
            sr0 = 0.0 if N <= 1 else np.sqrt(V) * ((1 - g) * stats.norm.ppf(1 - 1 / N) + g * stats.norm.ppf(1 - 1 / (N * np.e)))
            ref = stats.norm.cdf((sr - sr0) * np.sqrt(n - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))
            res["dsr_max_abs_diff"] = max(res["dsr_max_abs_diff"], abs(ref - hm.deflated_sharpe_ratio(x, V, N)))
res["SR0_conventionB_nb2_var1"] = hm.expected_max_sharpe(1.0, 2)
res["SR0_nb25_var_1_over_200"] = hm.expected_max_sharpe(1 / 200, 25)
res["SR0_nb25_var_0.004"] = hm.expected_max_sharpe(0.004, 25)
res["SR0_nb40_var_0.004"] = hm.expected_max_sharpe(0.004, 40)
# walk_forward fold usage: which trades are scored?
r = np.arange(1, 61, dtype=float)
folds = np.array_split(r, 5 + 1)
res["walk_forward_first_fold_ignored_len"] = len(folds[0])
res["walk_forward_n_scored_of_60"] = int(sum(len(f) for f in folds[1:]))
print(json.dumps(res, indent=1))
(HERE / "stat_refs.json").write_text(json.dumps(res, indent=1))
