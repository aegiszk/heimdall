# Family G — `SQEtBHOJW6I` ("conflicting live-order-flow / ICT episode")

## Source-recovery result (overturns the rule sheet)
The YouTube auto-generated captions were retrieved on 2026-09-24 (`_source_transcripts/SQEtBHOJW6I.json`,
is_generated=True, 5,217 snippets, ~2h52m, SHA prefix `cb8b6b966352b0c3`). The episode is **Jay Ortani's
"Market DNA" order-flow strategy on single US stocks and options** (Tesla, Nvidia, AMD, ARM), with live trading.

None of the three reconstructions in the rule sheet / `_source_reports/07-SQEtBHOJW6I.md` describes this video:
- Pass A "Internal Pivot Point (IPP)" — not in the transcript.
- Pass B "T-Rex / 2 PM Silver Bullet, ES/NQ 14:00–15:00" — not in the transcript.
- Pass C "generic ICT on EURUSD/NAS100/XAU/GBPUSD/USDJPY with five examples" — not in the transcript (the
  transcript explicitly disparages FX: "there's no edge in forex" discussion, ~0:18).
The five "alleged examples" (EURUSD 1.08455 etc.) are **fabrications of the AI analysis passes**. They are
retired: NOT_SOURCE. Only the secondary-metadata "live Nvidia trade > $50k" matches (the transcript: "$49,000 on
the NVDA trade… overall $44,000 on this day").

## Recovered strategy (as far as the transcript is mechanical)

| Rule | Source evidence (auto-caption) | Class | Mechanical definition | Ambiguity | Econ. |
|---|---|---|---|---|---|
| Universe: liquid single stocks (TSLA ~700–800K of his P&L, NVDA, AMD, ARM), traded via options | 0:00:48; examples throughout | STATED | — | options vs shares | HIGH |
| Pre-market "level of significance" (daily levels, prior ATH, Camarilla R3/R6/S4) | "192 zone on the daily"; "S4 camera levels"; "squeeze above R six" | STATED | daily levels + Camarilla pivots (formula standard) | which levels | HIGH |
| Bias 50/50 (NVDA) or 70/30 (TSLA) into the open; direction chosen by tape at the level | "heading into the market open I'm 50/50… if I see strength on the tape around this level…" | STATED | — | discretionary | HIGH |
| Entry trigger = order-book/tape: big resting orders (Bookmap, filter ≥1,000 shares), absorption, bid refill, "ladder support/resistance", aggressive prints on bid/ask | "big seller 140k shares at 143"; "bid refill… 37,000 shares… I'm going to enter"; "action from the sellers but no reaction on the price" | STATED | requires full-depth order book (MBO/MBP-10) + time & sales | "anomalies" thresholds are relative to each stock's "personality" (100K TSLA vs 2M NVDA) | HIGH |
| Stop = break of the level / the defending big order ("stop loss was a break above 143") | 0:~50 | STATED | level ± tick | — | HIGH |
| Exits by tape (new sellers, orders stepping down), partials | live segment | STATED | discretionary | HIGH | HIGH |
| Dynamic sizing $500 → $50,000 risk by conviction | "dynamic risk" | STATED | — | — | MEDIUM |

## Terminal assessment
- Setup G-MarketDNA: **BLOCKED_DATA** (historical full-depth US equity order book + trades required; not owned)
  and **largely BLOCKED_SOURCE** (entry = "anomalies" judged relative to each stock's personality; no thresholds).
- Setups G-PassA / G-PassB / G-PassC: **NOT_TESTABLE_SOURCE — retired as not present in the video.**
- Cheapest decisive data subset (quote only, 2026-09-24, Databento `metadata.get_cost`, nothing bought):
  XNAS.ITCH MBO for NVDA,TSLA,AMD one month (2024-01) = **$26.72**; MBP-10 = $18.65; three years of trades
  (2023-01..2026-09) = $174.50. Even with this data a faithful test needs a pre-registered absorption/refill
  detector; Heimdall's two prior absorption detectors (bar-proxy and true footprint, NQ) died on frequency —
  prior probability of a faithful mechanization is low. NO PURCHASE without owner approval.
- Also: Lucid 50K FLEX trades CME futures only — this family cannot be deployed on the target account.
