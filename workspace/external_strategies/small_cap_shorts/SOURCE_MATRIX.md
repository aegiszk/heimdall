# Family H — Steven Dux small-cap short statistics (`52ZsDmFHqyY`)

Primary: YouTube auto-generated captions (`_source_transcripts/52ZsDmFHqyY.json`, is_generated=True, 1,975
snippets, SHA prefix `d76a654ac3813210`). Cross-check: `_source_reports/08-52ZsDmFHqyY.md`, rule sheet §§2–16.

## Source-recovery changes vs rule sheet
- **Gap-Up Short gap threshold resolved**: the transcript states it directly — "The gap up should… it has to be
  above 100%." The rule-sheet "70%–1000%" alternative is not in the transcript as a GS entry threshold → GS uses >100%.
- Market cap: GS "has to be under 100 million" (over 200M "not doable"); FRD "initial market cap… under 200 million",
  where initial cap = cap before the run (e.g. cap ÷ 10 after a 10x move) → STATED, resolves the $100M vs $200M
  conflict by setup.
- Float: "over 50 million… 99% of the time not tradeable"; buckets 1–2M / 2–5M / 5–10M. STATED.
- Pre-market volume > 50M → avoid GS; day volume ≈ 5–10× pre-market volume. STATED.
- GS entry depends on float: very low float (<~2M) wait for a clear momentum shift and short a ~50% bounce after
  heavy float rotation (>15×); 5–10M float may short against the pre-market high. STATED (new).
- FRD: ≥3 consecutive green days with equal-or-higher volume, no red/flat day inside; "spot the first red day and
  you short on the second day"; if the following day is green, stay away. STATED (resolves the FRD entry-timing conflict).
- Frequency: GS ~70/yr, win ~50/70, average fade 26%; FRD 5–10/yr. STATED (claims).
- Bounce-Short 10:1 ratio direction: still ambiguous in the auto-caption → remains MISSING.

## Setup matrix (compact)
| Setup | Universe | Trigger | Stop | Target | Key missing inputs |
|---|---|---|---|---|---|
| H-GS Gap-Up Short | cap < $100M, float < 50M, price > $3, gap > 100%, PM vol ≤ 50M, not biotech/energy/Chinese | consolidation breakdown after 11:00 (float-dependent variant) | above consolidation high | fade ~26% (descriptive) | point-in-time float & cap, PM volume, sector, country, borrow |
| H-BS Bounce Short | ≈1-yr trapped-volume resistance, ≥ $150M trapped | near resistance with volume ratio (direction MISSING) | above resistance | 50–75% fade (descriptive) | ratio definition, trapped-volume algorithm |
| H-FRD First Red Day | initial cap < $200M, ≥3 green days rising volume, 300%/3d or 1000%/2d | short day 2 after first red close; 1/4 starter then 3/4 if morning bounce fails prior high | highest consolidation of run | none fixed | daily bars + PIT cap |

## Data requirement and blocker (BLOCKED_DATA)
Faithful test needs: (1) survivorship-free US small-cap 1-minute bars incl. pre-market; (2) point-in-time
shares outstanding / float and market cap; (3) sector + country flags; (4) halts/LULD; (5) historical borrow/locate
availability and fees (hard-to-borrow is the defining execution constraint). None are owned.
Quotes obtained 2026-09-24 (Databento `metadata.get_cost`, quote only):
- XNAS.ITCH ohlcv-1d all symbols 2019-01..2026-09: **$28.00** (cheapest subset: decides FRD *price-pattern* frequency/fade
  only, without float/borrow — would be TESTED_MECHANIZED with borrow unmodelled).
- XNAS.ITCH ohlcv-1m all symbols 2019-01..2026-09: $1,428.29 (GS intraday; Nasdaq-listed only — NYSE/AMEX small caps missing).
- EQUS.MINI ohlcv-1m all symbols 2023-06..2026-09: $522.25 (consolidated).
- Point-in-time float/market cap and historical borrow availability: NOT offered by Databento; vendor not quoted
  (UNVERIFIED — candidates would need a live quote before any claim).
Deployment: Lucid (CME futures only) cannot trade equities — even a survivor could not run on the target account.
