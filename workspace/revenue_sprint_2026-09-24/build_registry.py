"""Builds STRATEGY_REGISTRY.json (addendum D): one canonical entry per strategy, exactly one state, live_enabled=false.
Trial ids are read from data/trials_ledger.json by family; hashes are computed from files present at build time.
States: SOURCE_RESEARCH DEVELOPMENT PREREGISTERED VALIDATION_READY VALIDATING VALIDATED_ALPHA SHADOW LIVE_PILOT_READY
LIVE_PILOT SCALED FAILED INCONCLUSIVE BLOCKED_DATA BLOCKED_EXECUTION. Rebuild whenever a state changes (append the
previous file's content hash to `history`)."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "STRATEGY_REGISTRY.json"
STATES = {"SOURCE_RESEARCH", "DEVELOPMENT", "PREREGISTERED", "VALIDATION_READY", "VALIDATING", "VALIDATED_ALPHA", "SHADOW",
          "LIVE_PILOT_READY", "LIVE_PILOT", "SCALED", "FAILED", "INCONCLUSIVE", "BLOCKED_DATA", "BLOCKED_EXECUTION"}


def sha(rel):
    if not rel or not (ROOT / rel).exists():
        return None
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


led = json.loads((ROOT / "data" / "trials_ledger.json").read_text())["entries"]


def trials(fam=None, prefix=None):
    return [e["id"] for e in led if (fam and e["family"] == fam) or (prefix and e["id"].startswith(prefix))]


FX = {p: f"data/fx_histdata/{p}_1m_bid.parquet" for p in ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "NZDUSD", "XAUUSD"]}
DH = "workspace/dhesi_adjudication_agent1_2026-09-23/"
RS = "workspace/revenue_sprint_2026-09-24/"
E8 = "workspace/external_strategies/"

S = [
    # ---- active lanes
    dict(strategy_id="DHESI_V3", family="dhesi_inversion", state="PREREGISTERED", spec=DH + "DHESI_V3_CANONICAL_SPEC_V1.md",
         code="core/alpha/inversion_model_v3.py", data=[], trials=trials("dhesi_inversion"),
         reason="Validator + integrity hardened (PR #1 merged a1486c4, Amendment 1 accepted). Untouched NQ harvest (owner GUI) and "
                "owner authorization pending. Agent 2 owns validation."),
    dict(strategy_id="TRIDENT_V2", family="ext8_trident", state="PREREGISTERED", spec=RS + "trident_v2/TRIDENT_V2_SOURCE_SPEC.md",
         code=RS + "trident_v2/strategy.py", data=list(FX.values()), trials=[],
         reason="Frozen 2026-09-24 (manifest 00763a96). Awaiting Agent 2 spec audit, then DEV gate. Fidelity PASS_WITH_DECLARED_OMISSION."),
    dict(strategy_id="MMXM_V2", family="ext8_mmxm_ote", state="PREREGISTERED", spec=RS + "mmxm_v2/MMXM_V2_SOURCE_SPEC.md",
         code=RS + "mmxm_v2/strategy.py", data=[FX["EURUSD"], FX["GBPUSD"], FX["USDJPY"]], trials=[],
         reason="Frozen 2026-09-24 (manifest 00763a96). Awaiting Agent 2 spec audit, then DEV gate."),
    dict(strategy_id="FOMO_PROSPECTIVE", family="fomo_prospective", state="VALIDATING", spec="FOMO_PROSPECTIVE_PREREGISTRATION.md",
         code="workspace/fomo_lane/fomo_recorder.py", data=[], trials=[],
         reason="Prospective recording; outcomes sealed until stopping rule (>=3,500 eligible AND >=14 days, cap 45 days). "
                "Recorder outage 2026-09-23 10:25 -> 2026-09-24 10:29 local; restarted as run 4 (unchanged code db2f0f36)."),
    dict(strategy_id="CL_EIA_SUBMINUTE", family="eia_cl", state="BLOCKED_DATA", spec="workspace/sierra_lab_2026-09-23/SIERRA_LIVE_EDGE_LAB.md",
         code="workspace/sierra_lab_2026-09-23/eia_cl_response.py", data=[], trials=[],
         reason="1-minute study: no information after minute 1; sub-minute windows need the CL tick harvest (Sierra, owner GUI). "
                "Fallback lane per addendum Q."),
    # ---- superseded V1 / external-8 terminal states
    dict(strategy_id="TRIDENT_V1_E1_E4", family="ext8_trident", state="INCONCLUSIVE", spec=E8 + "trident/PREREGISTRATION.md",
         code=E8 + "trident/strategy.py", data=list(FX.values()), trials=trials("ext8_trident"),
         reason="TOO_SPARSE + EXECUTION_SENSITIVE; EMA200 hard gate unfaithful -> superseded by TRIDENT_V2."),
    dict(strategy_id="MMXM_V1_F1_F3", family="ext8_mmxm_ote", state="INCONCLUSIVE", spec=E8 + "mmxm_ote/PREREGISTRATION.md",
         code=E8 + "mmxm_ote/strategy.py", data=[FX["EURUSD"], FX["GBPUSD"], FX["USDJPY"]], trials=trials("ext8_mmxm_ote"),
         reason="Undisclosed outside-KZ day veto + 60-bar cap -> superseded by MMXM_V2."),
    dict(strategy_id="EXT8_A_LIQUIDITY_TRAP", family="ext8_liquidity_trap", state="INCONCLUSIVE", spec=E8 + "liquidity_trap/PREREGISTRATION.md",
         code=E8 + "liquidity_trap/strategy.py", data=["data/MNQ_1m.parquet"], trials=trials("ext8_liquidity_trap"),
         reason="NO_SIGNAL (~0R gross over ~1,000 trades; A2 ROBUSTLY_REJECTED). Not reopened this cycle."),
    dict(strategy_id="EXT8_B_TRADER_MAYNE", family="ext8_trader_mayne", state="FAILED", spec=E8 + "trader_mayne/PREREGISTRATION.md",
         code=E8 + "trader_mayne/strategy.py", data=["data/MNQ_1m.parquet"], trials=trials("ext8_trader_mayne"),
         reason="REJECTED_IMPLEMENTATION_NOT_FAMILY (H4 variants robustly negative; B4 worse than random placebo)."),
    dict(strategy_id="EXT8_C_PO3", family="ext8_po3_50", state="INCONCLUSIVE", spec=E8 + "po3_50/PREREGISTRATION.md",
         code=E8 + "po3_50/strategy.py", data=["data/MNQ_1m.parquet", "data/ES_1m.parquet"], trials=trials("ext8_po3_50"),
         reason="TOO_SPARSE; SMT rule caps frequency (creator frequency claim unsupported). Not reopened."),
    dict(strategy_id="EXT8_D_LITTLE_RIZZY", family="ext8_little_rizzy", state="INCONCLUSIVE", spec=E8 + "little_rizzy/PREREGISTRATION.md",
         code=E8 + "little_rizzy/strategy.py", data=["data/MNQ_1m.parquet", "data/ES_1m.parquet", FX["XAUUSD"]], trials=trials("ext8_little_rizzy"),
         reason="D4 MNQ FRAGILE/REGIME/TAIL dependent; XAU shorts rejected; crash-bottom BLOCKED_DATA. Not reopened."),
    dict(strategy_id="EXT8_G_ORTANI_TAPE", family="ext8_conflicting_episode", state="BLOCKED_DATA", spec=E8 + "conflicting_episode/SOURCE_MATRIX.md",
         code=None, data=[], trials=[], reason="Needs historical full-depth US equity book; thresholds unstated (BLOCKED_SOURCE); DO_NOT_BUY."),
    dict(strategy_id="EXT8_H_SMALLCAP_SHORTS", family="ext8_small_cap_shorts", state="BLOCKED_DATA", spec=E8 + "small_cap_shorts/SOURCE_MATRIX.md",
         code=None, data=[], trials=[], reason="Needs PIT float/cap/borrow; DO_NOT_BUY; equities not tradable on Lucid."),
    # ---- historical (HEIMDALL_MEMORY.md)
    dict(strategy_id="DHESI_V2", family="dhesi_inversion", state="INCONCLUSIVE", spec=None, code="core/alpha/inversion_model.py", data=["data/MNQ_1m.parquet"],
         trials=[t for t in trials("dhesi_inversion") if "v2" in t], reason="13 holdout trades; superseded by DHESI_V3."),
    dict(strategy_id="ORDERFLOW_INITIATIVE_V3", family="orderflow_initiative", state="INCONCLUSIVE", spec="ORDERFLOW_INITIATIVE_PREREGISTRATION.md",
         code="core/alpha/orderflow_initiative.py", data=[], trials=trials("orderflow_initiative"), reason="28 holdout trades, CI contains dev estimate; do not tune."),
]
for fam, sid, why in [("okala8020", "OKALA_8020", "0 trades both revisions"), ("fabio_orb", "FABIO_ORB_DELTA", "dead"),
                      ("luxalgo_poc", "LUXALGO_POC_RECLAIM", "holdout negative; proxy POC invalid"),
                      ("casper_fvg", "CASPER_OPENING_FVG", "holdout ~0"), ("intraday_momentum", "INTRADAY_MOMENTUM", "holdout negative"),
                      ("target_sweep", "TARGET_SWEEP_GRID", "all cells dead"), ("quality_filter", "QUALITY_FILTERS", "dead"),
                      ("swing_trend", "ES_SWING_TREND", "16 holdout trades"), ("vwap_reversion", "VWAP_REVERSION", "~0 gross"),
                      ("time_scalp", "TIME_SCALP", "~0 gross"), ("trend_pullback", "TREND_PULLBACK", "~0 gross"),
                      ("orderflow_absorption", "ORDERFLOW_ABSORPTION_V1", "0 trades (frequency)"),
                      ("orderflow_footprint", "ORDERFLOW_FOOTPRINT_V2", "0 trades (frequency)"),
                      ("wallet_persistence", "FOMO_WALLET_PERSISTENCE", "alpha fail"), ("crowding", "FOMO_CROWDING", "no signal"),
                      ("mirror_copy", "FOMO_MIRROR_COPY", "<=0 realizable"), ("cluster_consensus", "FOMO_CLUSTER_CONSENSUS", "fail realizable"),
                      ("copy_fixed_exit", "FOMO_COPY_FIXED_EXIT", "historical discovery only; tested prospectively by FOMO_PROSPECTIVE")]:
    S.append(dict(strategy_id=sid, family=fam, state="INCONCLUSIVE" if fam in ("copy_fixed_exit",) else "FAILED", spec=None, code=None,
                  data=[], trials=trials(fam), reason=why + " (HEIMDALL_MEMORY.md / trials ledger)"))

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
prev = json.loads(OUT.read_text()) if OUT.exists() else None
entries = []
for s in S:
    assert s["state"] in STATES, s
    entries.append({
        "strategy_id": s["strategy_id"], "family": s["family"], "state": s["state"],
        "spec_path": s["spec"], "spec_hash": sha(s["spec"]), "code_path": s["code"], "code_hash": sha(s["code"]),
        "dataset_hashes": {d: sha(d) for d in s["data"]}, "trial_ids": s["trials"],
        "last_state_transition_utc": now, "reason": s["reason"],
        "owner_approval_required_for": ["LIVE_PILOT", "SCALED", "any real order"],
        "live_enabled": False,
    })
out = {"schema": "HEIMDALL_STRATEGY_REGISTRY_V1", "built_utc": now,
       "base_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
       "rules": "exactly one state per strategy; live_enabled=false unless an owner-approved OWNER_LIVE_PILOT_REQUEST exists; "
                "no jump DEVELOPMENT->LIVE or INCONCLUSIVE->LIVE",
       "history": (prev.get("history", []) + [hashlib.sha256(OUT.read_bytes()).hexdigest()]) if prev else [],
       "strategies": entries}
OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(len(entries), {st: sum(e["state"] == st for e in entries) for st in sorted({e["state"] for e in entries})})
