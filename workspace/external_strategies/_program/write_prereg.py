"""Writes per-family PREREGISTRATION.md and the hash manifest. Run once, before any PnL."""
import datetime
import glob
import hashlib
import json
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COMMON = """
## Common protocol (all interpretations in this family)
- Cost model (`common/harness.py` SPECS): futures trade prices; market/stop fills +1 tick adverse; stop exits +1 tick
  adverse (gap-through fills at the worse open); limits need a 1-tick trade-through; commission MNQ $1.00 RT, ES
  $3.50 RT, YM $3.50 RT (YM = ASSUMPTION). FX/XAU: HistData BID bars; ask = bid + modelled spread (EURUSD 0.3,
  GBPUSD 0.6, USDJPY 0.4, USDCAD 0.6, NZDUSD 0.7 pips; XAU $0.20); +0.2 pip ($0.05 XAU) slippage on market/stop
  fills; $7 per lot RT commission. ALL FX costs are RESEARCH ASSUMPTIONS; x1.25/x1.5/x2 re-simulated.
- Same-bar semantics: stop beats target in the same minute; no target credit in the entry minute; an entry minute
  that also touches the stop is a stop-out; pending entries cancel if the stop level trades first.
- Rolls: Databento continuous MNQ/ES Panama back-adjusted at instrument_id changes (gap = first open of the new
  contract minus last close of the old; error <= one minute's move); YM Sierra roll 2026-09-14 00:00 UTC.
- Sequencing: every order resolved independently; one position at a time per interpretation+instrument; first FILL wins.
- Windows: MNQ/ES DEV 2024-07-01..2026-06-30 (REUSED, diagnostic only); YM Sierra 2026-06-24..2026-09-21 (REUSED);
  FX/XAU DEV 2022-01-01..2024-12-31; FX/XAU FRESH 2025-01-01..2026-08-31 SEALED (not read).
  DHESI firewall: no NQ/MNQ/ES/MES data before 2024-07-01 is read (`load_futures` asserts).
- Role: every result here is DEVELOPMENT evidence. Nothing here validates.
- Metrics: net R per trade (R = net / |fill - initial stop|; XAU close-stop designs vs the declared invalidation),
  NW t, date-clustered bootstrap 95% CI, and the work-order section 10 list.
- Falsification (fixed now, per interpretation): ROBUSTLY_REJECTED if n >= 30 and mean net R <= 0 with the 95%
  cluster-bootstrap upper bound < +0.05R; INCONCLUSIVE if n < 30 or the CI straddles 0 without positive evidence;
  CANDIDATE only if mean net R > 0, NW t > 2, cost x1.5 still > 0, drop-top-5 still > 0 and >= 2/3 of calendar
  years positive; candidates then face the section-14 adversarial battery before any SURVIVING label.
- No parameter may change after PnL is seen. A changed rule = a new hypothesis ID.
"""

FAM = {
    "liquidity_trap": ("A", "DAnXM7C16h0 liquidity-trap reversal", """
| ID | Instr./TF | Session | Dir | Entry | Stop | Target | Mgmt | Params |
|---|---|---|---|---|---|---|---|---|
| A1_k1_spike_nearest | MNQ 5m signal / 1m fill | entries 09:30-11:30 ET, flat 12:00 | both | stop order 1 tick beyond internal swing | anchor +/- 2 ticks | nearest untaken opposing swing | none; pending expires 11:30 | k=1 |
| A2_k2_spike_nearest | same | same | both | same | same | same | same | k=2 |
| A3_k1_spike_split | same | same | both | same | same | 50% nearest, 50% 2nd | BE after first partial | k=1 |
| A4_k1_close_nearest | same | same | both | close of the first 5m bar that spikes the level and closes back | same | nearest | same | k=1 |
| A1 YM replication | YM Sierra 90d, tick 1.0 | same | both | as A1 | as A1 | as A1 | as A1 | k=1 |

Mechanism: stops rest beyond respected swings; an extreme that swept an older swing holds none. Re-entry allowed when flat. 5 trials.
""", "pivot width k; anchor = pivot whose own bars took an older confirmed swing; lookback current+previous session day; window 09:30-11:30 / flat 12:00; no news filter (no calendar on disk)."),
    "trader_mayne": ("B", "coBMd1vk2Lo Trader Mayne HTF range / OB / LTF breaker", """
| ID | HTF->LTF | Entry | Stop | Target | Mgmt | Expiry |
|---|---|---|---|---|---|---|
| B1_H4_M15_breaker | 4h->15m | LTF close above the swing high that generated a swept LTF swing low (after OB touch); entry <= 50% of range; min 2R | sweep extreme -1 tick | HTF range high | stop to BE at +2R | 30 HTF bars / HTF close beyond range low / target first |
| B2_H1_M5_breaker | 1h->5m | same | same | same | same | same |
| B3_D_H1_breaker | 1D->1h | same | same | same | same | same |
| B4_H4_OB_limit | 4h | limit at OB top (long) / bottom (short); min 2R; in discount | OB far edge -1 tick | range high | BE at +2R | same |

MNQ 24h, holds across sessions allowed (max 12 days). Both directions. 4 trials.
""", "OB = <=3 consecutive opposite candles ending at the leg extreme; range low = leg extreme between broken swing and MSB; one attempt per setup; BE (not half) at 2R."),
    "po3_50": ("C", "HNuRp9Z1bMs 50% rebalance / PO3", """
| ID | Exec TF | Range low | H4 PO3 required | Stop | Target | BE | Flat |
|---|---|---|---|---|---|---|---|
| C1_3m_overnight | 3m | extreme since 18:00 ET | no | NQ extreme since 10:00 +/- 1 tick | 50% of [range low, extreme] | last completed 15m candle extreme taken | 16:00 ET |
| C2_3m_overnight_H4 | 3m | since 18:00 | yes | same | same | same | same |
| C3_5m_overnight | 5m | since 18:00 | no | same | same | same | same |
| C4_3m_h4range | 3m | previous H4 bin 06:00-10:00 | no | same | same | same | same |

Entry (all): first exec-TF close through the inversion-FVG edge, 10:00-11:30, after NQ swept its 09:00-hour extreme
during the 10:00 hour while ES had NOT swept its own 09:00-hour extreme (checked through entry). One setup per side
per day. MNQ traded, ES for SMT. 4 trials. Tue-Thu subset is descriptive only.
Frequency-fidelity note (pre-PnL): ~20 setups/yr vs the creator's "most days".
""", "manipulation hour 10:00-11:00; SMT window 10:00 to entry; inversion FVG = most recent same-direction 3-candle FVG after 09:30 ending by the manipulation extreme; flat 16:00."),
    "little_rizzy": ("D", "AVVM-FyewLg Little Rizzy measured move", """
| ID | Setup | TF | Entry | Max-loss stop | Loss exit | Target |
|---|---|---|---|---|---|---|
| D1_F_short_1h_pivot | F downtrend short | 1h | market at P2 confirmation close if below TL and above low(L) | P2 high + 1 tick | first close above TL | low(L) - D |
| D2_F_short_4h_pivot | F | 4h | same | same | same | same |
| D3_F_short_1h_bb | F | 1h | first close below BB(20,2) mid within 5 bars after P2 | same | same | same |
| D4_G_long_1h_pivot | G uptrend long (mirror) | 1h | mirror of D1 | P2 low - 1 tick | close below TL | high(H) + D |

Pivots k=2; chain count <= 2. Each ID on MNQ, ES (dev 2024-07..2026-06) and XAUUSD (dev 2022-2024) = 12 trials.
Setup H (crash-bottom) NOT tested: needs multi-decade monthly index data, < 10 events (TOO_SPARSE).
""", "k=2 pivots; TL through two consecutive pivots; max-loss stop at P2; chain count; BB period 20."),
    "trident": ("E", "ADnslyKOwFE Trident", """
| ID | FVG window (middle candle open, ET) | Exit | Side |
|---|---|---|---|
| E1_long_kz0300_20R | 03:00-06:30 | fixed 20R target | long |
| E2_long_kz0300_emacross | 03:00-06:30 | 30m close with EMA5 < EMA21 | long |
| E3_long_fvg0230_20R | 02:30-06:30 | 20R | long |
| E4_short_mirror_20R | 03:00-06:30 | 20R | short (mirror; weak source) |

All: 30m ET bars; doji body <= 25% of range, low < FVG 50%, open & close >= FVG top; doji and confirmation inside
03:00-06:30; confirmation close < doji high; EMA 5>9>13>21 and close > EMA200 (30m) at confirmation; entry at the
confirmation close; FX stop = doji low - 1 pip; XAU = exit on 30m close below the doji low (+ catastrophic stop 3x
the doji range; R measured vs the doji low); max hold 10 days. Six instruments -> 24 trials.
Frequency-fidelity note (pre-PnL funnel): ~1 setup/yr/pair vs the creator's claimed 6-8 -> expected TOO_SPARSE.
""", "doji threshold 0.25; 'body not inside the FVG' read as body above the gap; EMA200 on 30m; XAU catastrophic stop."),
    "mmxm_ote": ("F", "IB-fyWI5j8w MMXM + OTE", """
| ID | OTE entry | Stop | Levels | Target | BE |
|---|---|---|---|---|---|
| F1_ote62_sl100_PD | limit 0.62 | 1.0 | PDH/PDL | 0 | 15m close beyond 0.2 |
| F2_ote705_sl90_PD | limit 0.705 | 0.9 | PDH/PDL | 0 | same |
| F3_ote62_sl90_PDPW | limit 0.62 | 0.9 | PDH/PDL + PWH/PWL | 0 | same |

All: 15m ET bars; bias = previous week close vs open (trade only with it); level run inside NY 02-05 / 07-10 / 10-12;
displacement = first 15m body close through the latest confirmed k=1 swing before the SMR extreme, body >= 50% of
range and correct colour, else no first-leg trade; fib anchors fixed at the displacement close; order expires
12:00 NY; max hold 3 days. EURUSD GBPUSD USDJPY -> 9 trials. Silver-Bullet second leg NOT tested.
""", "weekly-candle bias; body >= 50% displacement; fixed fib anchors; noon expiry; 3-day max hold."),
}

for d, (L, title, table, assump) in FAM.items():
    txt = (f"# PREREGISTRATION - Family {L}: {title}\n\nFrozen 2026-09-24 BEFORE any PnL was computed in this program. "
           f"Code: `{d}/strategy.py` + `common/harness.py` (hashes in `_program/PREREG_MANIFEST.json`). "
           f"Source evidence: `{d}/SOURCE_MATRIX.md`.\n\n## Interpretations\n{table}\n"
           f"## Research assumptions (not source rules)\n{assump}\n{COMMON}")
    open(f"{d}/PREREGISTRATION.md", "w", encoding="utf-8").write(txt)

files = sorted(glob.glob("*/PREREGISTRATION.md") + glob.glob("*/strategy.py")
               + ["common/harness.py", "common/registry.py", "common/stats.py"])
man = {f: hashlib.sha256(open(f, "rb").read()).hexdigest() for f in files}
agg = hashlib.sha256(json.dumps(man, sort_keys=True).encode()).hexdigest()
json.dump({"frozen_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "note": "frozen before any PnL",
           "files": man, "aggregate_sha256": agg}, open("_program/PREREG_MANIFEST.json", "w"), indent=1)
print(agg)
