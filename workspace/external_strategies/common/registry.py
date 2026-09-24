"""Program registry: which family/interpretation runs on which instrument and data window.

WINDOWS (fixed before any outcome):
- CME index futures DEV: Databento MNQ/ES 1m 2024-07-01 .. 2026-06-30 (already REUSED by earlier Heimdall
  experiments -> DEV/diagnostic only, never evidence of out-of-sample edge).
- YM Sierra 90d 2026-06-24 .. 2026-09-21: REUSED (read by earlier multi-market work) -> DEV replication only.
- FX/XAU (HistData, never read by any Heimdall experiment before 2026-09-24):
      DEV     2022-01-01 .. 2024-12-31   (used now)
      FRESH   2025-01-01 .. 2026-08-31   (SEALED: reserved for validation of survivors; not read here)
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(HERE))
import harness as hz  # noqa: E402

FX_DEV = (pd.Timestamp("2022-01-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC"))
FX_FRESH = (pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2026-09-01", tz="UTC"))
PIP = {"EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCAD": 0.0001, "NZDUSD": 0.0001, "USDJPY": 0.01, "XAUUSD": 0.01}


def load_mod(family: str):
    p = BASE / family / "strategy.py"
    spec = importlib.util.spec_from_file_location(f"strat_{family}", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


_CACHE: dict = {}


def fut(name: str) -> pd.DataFrame:
    if name not in _CACHE:
        _CACHE[name] = hz.load_futures(name)
    return _CACHE[name]


def fx_dev(pair: str) -> pd.DataFrame:
    k = ("fxdev", pair)
    if k not in _CACHE:
        d = hz.load_fx(pair)
        _CACHE[k] = d[(d.index >= FX_DEV[0]) & (d.index < FX_DEV[1])]
    return _CACHE[k]


def jobs():
    """Yield (family, cfg, instrument, spec_name, data_fn, gen_fn) for every registered trial."""
    A = load_mod("liquidity_trap")
    for c in A.CONFIGS:
        yield "liquidity_trap", c, "MNQ", "MNQ", (lambda: fut("MNQ")), (lambda m, c=c: A.generate(m, c))
    # pre-declared single replication of A1 on the source's other named market (YM, Sierra 90d, REUSED)
    yield ("liquidity_trap", A.Cfg("A1_k1_spike_nearest", k=1, tick=1.0), "YM_S", "YM", (lambda: fut("YM_S")),
           (lambda m: A.generate(m, A.Cfg("A1_k1_spike_nearest", k=1, tick=1.0))))
    B = load_mod("trader_mayne")
    for c in B.CONFIGS:
        yield "trader_mayne", c, "MNQ", "MNQ", (lambda: fut("MNQ")), (lambda m, c=c: B.generate(m, c))
    C = load_mod("po3_50")
    for c in C.CONFIGS:
        yield "po3_50", c, "MNQ", "MNQ", (lambda: fut("MNQ")), (lambda m, c=c: C.generate(m, fut("ES"), c))
    D = load_mod("little_rizzy")
    for c in D.CONFIGS:
        yield "little_rizzy", c, "MNQ", "MNQ", (lambda: fut("MNQ")), (lambda m, c=c: D.generate(m, c, 0.25))
        yield "little_rizzy", c, "ES", "ES", (lambda: fut("ES")), (lambda m, c=c: D.generate(m, c, 0.25))
        yield ("little_rizzy", c, "XAUUSD", "XAUUSD", (lambda: fx_dev("XAUUSD")),
               (lambda m, c=c: D.generate(m, c, 0.01)))
    E = load_mod("trident")
    for c in E.CONFIGS:
        for p in E.PAIRS:
            yield ("trident", c, p, p, (lambda p=p: fx_dev(p)),
                   (lambda m, c=c, p=p: E.generate(m, c, p, PIP[p])))
    F = load_mod("mmxm_ote")
    for c in F.CONFIGS:
        for p in F.PAIRS:
            yield "mmxm_ote", c, p, p, (lambda p=p: fx_dev(p)), (lambda m, c=c: F.generate(m, c))
