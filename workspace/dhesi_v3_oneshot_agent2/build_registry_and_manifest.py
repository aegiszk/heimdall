"""Builds STRATEGY_REGISTRY.json (addendum D) and SIERRA_ASSET_MANIFEST_V2.json (addendum P / phase 10 plan).
Agent 2, 2026-09-24. Metadata only. Active entries owned by Agent 1 are marked owner_agent=agent1; Agent 1 updates them.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import trials_ledger as tl  # noqa: E402

TODAY = "2026-09-24"
STATES = ["SOURCE_RESEARCH", "DEVELOPMENT", "PREREGISTERED", "VALIDATION_READY", "VALIDATING", "VALIDATED_ALPHA", "SHADOW",
          "LIVE_PILOT_READY", "LIVE_PILOT", "SCALED", "FAILED", "INCONCLUSIVE", "BLOCKED_DATA", "BLOCKED_EXECUTION"]


def entry(sid, fam, state, reason, owner, spec=None, code=None, data=None, trials=(), approval="owner approval for any transition beyond VALIDATED_ALPHA"):
    assert state in STATES
    return {"strategy_id": sid, "family": fam, "spec_hash": spec, "code_hash": code, "dataset_hashes": data or {},
            "trial_ids": list(trials), "state": state, "last_state_transition": TODAY, "reason": reason,
            "owner_approval_requirement": approval, "owner_agent": owner, "live_enabled": False}


def main():
    led = tl.load_ledger()
    voided = tl.voided_ids(led)
    fam_trials: dict = {}
    for e in led["entries"]:
        fam_trials.setdefault(e["family"], []).append((e["id"], tl.effective_verdict(e, led, voided)))
    reg = [
        entry("DHESI_V3", "dhesi_inversion", "PREREGISTERED",
              "Canonical spec + protocol V1 + amendment 1 frozen; PR #1 merged a1486c4; binding V2 (see VALIDATION_BINDING_V2.json); awaiting owner Sierra harvest, then integrity -> VALIDATION_READY",
              "agent2", spec="8f330ae21a7537586cf769b20b4727fddc4f4eee7aea9d94e36bd29aeb9c6059",
              code="0ab7a5156e506c629110efe5253a6b93315072cd3f544490d80c2a746922bf85",
              data={"dev_MNQ_1m": "91670f3f43d3a3e5eb99608d9c335fef2a0e215cb365543cb0126aac9e2b5774", "untouched_NQ": "PENDING_HARVEST"},
              trials=[t for t, _ in fam_trials.get("dhesi_inversion", [])]),
        entry("TRIDENT_V2", "ext8_trident", "PREREGISTERED",
              "Re-frozen after Agent 2 audit (C7 unsourced gate removed); source audit PASS (64cc3fa) bound to manifest 37fcf7a3; DEV run pending; sealed FX/XAU 2025-01..2026-08 unread",
              "agent1", spec="V2_PREREG_MANIFEST aggregate 37fcf7a3b06b3c1e0f51432e423621104ce51e4a2ce0123498719ed18dfc0b91",
              code="b765cae07a4e27236205aedfe9a4b891727ae6073bc29748b9c063296c2ee3c2"),
        entry("MMXM_V2", "ext8_mmxm_ote", "PREREGISTERED",
              "V2 source audit PASS (Agent 2, 64cc3fa) bound to manifest 37fcf7a3; DEV run pending; sealed FX/XAU 2025-01..2026-08 unread",
              "agent1", spec="V2_PREREG_MANIFEST aggregate 37fcf7a3b06b3c1e0f51432e423621104ce51e4a2ce0123498719ed18dfc0b91",
              code="4a899501e1f438a62e1c5a3838668026a05a2bcf8b64d5852bbbd1f17b870251"),
        entry("FOMO_PROSPECTIVE", "fomo", "VALIDATING",
              "Prospective recorder; evaluate once at >=3,500 eligible trades and >=14 days, or 45 days (FOMO_PROSPECTIVE_PREREGISTRATION.md 902263424c170fb7...). Recorder DOWN 24.1 h (last event 2026-09-23 10:25 local, not reboot-persistent); restarted unchanged code (sha db2f0f36...) as run 4 at epoch 1790231366 (Agent 1); outage = feed gap per run-1/2/3 precedent; eligible so far 2",
              "agent1"),
        entry("CL_EIA_TICK", "cl_eia", "BLOCKED_DATA",
              "Pre-declared tick-window event study (SIERRA_LIVE_EDGE_LAB.md); needs 24 months CL ticks from Sierra; fallback lane per addendum Q", "agent2"),
    ]
    ext8 = {"A_liquidity_trap": ("INCONCLUSIVE", "NO_SIGNAL ~0R gross over ~1,000 trades; A2 ROBUSTLY_REJECTED"),
            "B_trader_mayne": ("FAILED", "REJECTED_IMPLEMENTATION_NOT_FAMILY: H4 variants robustly negative; entries worse than random placebo"),
            "C_po3_50": ("INCONCLUSIVE", "TOO_SPARSE; SMT-gated frequency ceiling 24.5/yr"),
            "D_little_rizzy": ("INCONCLUSIVE", "D4 FRAGILE / regime- / tail-dependent; XAU F-short rejected; H BLOCKED_DATA"),
            "E_trident_v1": ("INCONCLUSIVE", "TOO_SPARSE + EXECUTION_SENSITIVE; superseded by TRIDENT_V2"),
            "F_mmxm_v1": ("INCONCLUSIVE", "TOO_SPARSE + undisclosed KZ veto; superseded by MMXM_V2"),
            "G_ortani_orderflow": ("BLOCKED_DATA", "needs full-depth US equity book + tape; not tradable on Lucid; DO_NOT_BUY"),
            "H_smallcap_shorts": ("BLOCKED_DATA", "needs PIT float/cap/borrow/halts; not tradable on Lucid; DO_NOT_BUY")}
    for k, (s, r) in ext8.items():
        reg.append(entry(f"EXT8_{k}", "ext8", s, r + " (Agent 2 certification 45672b9)", "agent1"))
    skip = {"dhesi_inversion", "null_control"}
    for fam, ts in sorted(fam_trials.items()):
        if fam in skip or fam.startswith("ext8_"):
            continue
        vs = [v for _, v in ts]
        up = " ".join(vs).upper()
        state = "INCONCLUSIVE" if "INCONCLUSIVE" in up and not all(("DEAD" in x.upper() or "FAIL" in x.upper()) for x in vs) else "FAILED"
        reg.append(entry(f"HIST_{fam}", fam, state, "ledger effective verdicts: " + "; ".join(sorted(set(vs))), "agent1",
                         trials=[t for t, _ in ts]))
    out = {"registry": "STRATEGY_REGISTRY", "schema": "addendum D", "states": STATES, "as_of": TODAY,
           "rules": ["exactly one state per strategy", "live_enabled=false by default", "no DEVELOPMENT->LIVE or INCONCLUSIVE->LIVE",
                     "Jev/LLM output never authorizes a transition (addendum C)"],
           "strategies": reg}
    (ROOT / "STRATEGY_REGISTRY.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")

    plan = {"manifest": "SIERRA_ASSET_MANIFEST_V2", "status": "PLAN (metadata only; nothing harvested yet)", "as_of": TODAY,
            "symbol_availability": "UNVERIFIED until Sierra is running: on-disk naming is ROOT+month+YY-EXCHANGE (e.g. NQZ26-CME, GCZ26-COMEX, CLZ26-NYMEX); confirm CME FX roots in the Sierra symbol search.",
            "record_fields_filled_after_harvest": ["exact start/end", "row count", "disk size", "SHA-256"],
            "assets": [
                {"priority": 1, "instrument": "NQ continuous (volume roll, no back-adjust)", "resolution": "1 minute",
                 "range": "2011-09-01 (protocol V1 2.3) -> 2024-10-31", "est_disk": "0.3-0.7 GB",
                 "purpose": "Dhesi v3 one-shot (RESERVED: metadata only before authorization)", "checklist": "SIERRA_OWNER_CHECKLIST.md"},
                {"priority": 2, "instrument": "CME FX futures 6E, 6B, 6J, 6C, 6N (continuous, volume roll, no back-adjust)", "resolution": "1 minute",
                 "range": "2022-01-01 -> harvest date", "est_disk": "~0.25 GB each",
                 "purpose": "futures translation of a VALIDATED Trident/MMXM result only; overlaps the SEALED FX window 2025-01..2026-08 -> no inspection"},
                {"priority": 3, "instrument": "GC continuous (volume roll, no back-adjust)", "resolution": "1 minute", "range": "2022-01-01 -> harvest date",
                 "est_disk": "~0.3 GB", "purpose": "gold translation (Trident XAU); same sealed-overlap rule"},
                {"priority": 4, "instrument": "CL contracts (tick storage)", "resolution": "1 tick", "range": "last 24 months",
                 "est_disk": "3-8 GB (estimate, UNVERIFIED)", "purpose": "frozen CL/EIA tick event study (fallback lane, addendum Q); needs storage unit = 1 Tick"}],
            "no_paid_upgrade": True, "license_note": "Sierra/CME data for internal research use; keep in private repo release assets only"}
    (ROOT / "workspace" / "dhesi_v3_oneshot_agent2" / "SIERRA_ASSET_MANIFEST_V2.json").write_text(json.dumps(plan, indent=1) + "\n", encoding="utf-8")
    print(len(reg), "registry entries")


if __name__ == "__main__":
    main()
