"""Per-wallet realized-PnL reconciliation: RHTrenches vs FomoPulse (same window).
Reads raw/tr_{host}_{window}.json captured 2026-09-23 via /api/traders?window=..&limit=500."""
import json, statistics as st
def load(h, w):
    d = json.load(open(f"raw/tr_{h}_{w}.json", encoding="utf-8"))
    rows = d if isinstance(d, list) else next(v for v in d.values() if isinstance(v, list))
    return {(r.get("address") or "").lower(): r for r in rows}
for w in ("24h", "7d", "30d"):
    for h in ("rhtrenches.com", "fomopulse.app"):
        rows = load(h, w).values()
        rp = [float(r.get("realized_pnl") or r.get("realized") or 0) for r in rows]
        print(h, w, "n", len(rp), "realized", round(sum(rp)), "win", sum(x > 0 for x in rp), "lose", sum(x < 0 for x in rp))
a, b = load("rhtrenches.com", "30d"), load("fomopulse.app", "30d")
common = [k for k in a if k and k in b]
pairs = [(float(a[k].get("realized_pnl") or 0), float(b[k].get("realized") or 0), a[k].get("handle")) for k in common]
print("common", len(pairs), "sign agree", sum((x > 0) == (y > 0) for x, y, _ in pairs),
      "median |diff|", round(st.median(abs(x - y) for x, y, _ in pairs)))
