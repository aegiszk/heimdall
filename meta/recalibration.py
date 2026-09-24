"""Verification-debt auditor (S7, off money path). Reads STATE.md outcomes weekly, reports gate
precision/recall drift. LLM-assisted narration is optional; recalibration edits require admin action."""
def audit_gate(*a, **k): raise NotImplementedError("S7: wire to STATE outcomes log + admin config")
