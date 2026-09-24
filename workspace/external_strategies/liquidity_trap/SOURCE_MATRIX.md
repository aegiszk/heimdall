# Family A — Liquidity-Trap Reversal (`DAnXM7C16h0`, "Marco")

Primary source: creator-uploaded English captions retrieved 2026-09-24 via `youtube-transcript-api`
(`_source_transcripts/DAnXM7C16h0.json`, is_generated=False, 1,190 snippets, SHA-256 prefix `57cf810a5fb1e86e`).
Secondary: `_source_reports/01-DAnXM7C16h0.md` (zip SHA `ecd90a4d…`), rule sheet §§2–16. Primary wins on conflict.

Evidence classes: STATED (spoken in the primary transcript) · VISUAL (described on chart, not a rule) ·
INTERPRETED (conservative joining of stated parts) · RESEARCH_ASSUMPTION (needed to run; not in source) · MISSING.

## Setups
- A-short: bearish sweep short. A-long: bullish sweep long (exact mirror, STATED "buy below lows, sell above highs" 0:12:20).

## Rule matrix (short; long mirrors)

| Rule | Source evidence | Class | Mechanical definition | Ambiguity | Economic importance |
|---|---|---|---|---|---|
| Liquidity = resting stops at a respected high/low that price moved away from | 0:03:34 "high respected previous highs… there's now liquidity above this high"; 0:13:13 "high taken, low respected, move away" | STATED | confirmed 5m pivot (k each side) not yet traded through | swing algorithm unstated | HIGH — defines every level |
| A swept extreme holds no liquidity | 0:29:48 "there should not be any liquidity above this high"; 0:44:49 "spiked out a high… shouldn't be any liquidity above" | STATED | **anchor** = pivot whose own bars [p−k,p] took an older confirmed untaken pivot | "spike" size unstated | HIGH — sets the stop |
| Enter off internal liquidity below the anchor | 0:28:05 "taking entries off internal liquidity… targeting external"; 1:08:19 "as soon as this high is taken out, my stop covers this high on the left" | STATED | internal = pivot formed after anchor, below it, untaken | which internal if several | HIGH |
| Trigger = breach, market execution | 0:46:33 "I just market execute… as soon as the high is spiked out" | STATED | buy-stop/sell-stop 1 tick beyond internal (A1–A3) | tick vs close (see A4) | HIGH |
| Alternative: 5m close confirmation | 1:26:32 "if we can get a nice five-minute close above, I will add" (used for ADDS) | STATED (for adds) → INTERPRETED as entry variant | A4: first 5m bar that spikes the level must close back inside; enter at close | source uses it for scaling, not initial entry | MEDIUM |
| Stop 1–2 ticks beyond the anchor high (futures) | 1:09:12 "a tick or two above the high"; 0:31:19 | STATED | anchor ± 2 ticks | 1 vs 2 ticks | MEDIUM |
| Target opposing liquidity | 0:31:34 "I need to make sure I'm targeting liquidity"; 0:32:29 | STATED | nearest untaken confirmed swing low beyond the trigger | internal vs external | HIGH |
| Partials at internal target, rest external; BE only after partial | 0:32:29–0:33:20 "not the biggest fan of BE unless I've partialed"; 0:47:21 "partial here usually 50%" | STATED | A3: 50% at nearest, 50% at 2nd-nearest, BE after first | 50 vs 70% | MEDIUM |
| Trail below newly protected swing | 0:32:29 "I'll trail my stop below this low" | STATED | NOT implemented (declared) | trailing distance unstated | MEDIUM |
| Time: NY, entries after 09:30 open | 0:42:16 "stock open is 9:30"; 0:43:02 "looking for entries after the open" | STATED | entries 09:30–11:30 ET | window end unstated | HIGH |
| Out before NY lunch | 1:46:46 "I do want to be out of this before this lunch hour" | STATED | flatten 12:00 ET | lunch start unstated | MEDIUM |
| Specific time window, outside irrelevant | 0:49:03 | STATED | same window | exact bounds MISSING | MEDIUM |
| No entry before news; wait 2–4 min | 1:07:24 | STATED | NOT implemented: no calendar on disk | tiers MISSING | LOW–MEDIUM (10:00 releases fall in window) |
| HTF logic: target must exist | 0:11:27, 0:31:34 | STATED | order only if an opposing untaken swing exists | HTF TF unstated | MEDIUM |
| Strict rule: no longs until the low is taken | 0:24:33 | STATED | structural (longs only below lows) | — | HIGH |
| Instruments: "whatever chart"; YM, NQ, EURUSD examples | 1:03:42, 0:41:11 | STATED | MNQ (NQ price) dev; YM replication | — | — |
| Timeframe: 5m normal, 1m more stops | 0:42:32, 1:06:30 | STATED | 5m signal bars, 1m fills | — | — |
| Swing algorithm | — | MISSING → RESEARCH_ASSUMPTION | k=1 (3-candle) or k=2 pivots | both defensible | HIGH |
| Lookback of levels | Asia/London/prior-day NY levels used in examples (0:43:51, 1:15:32) | VISUAL → RESEARCH_ASSUMPTION | current + previous session day | older levels excluded | MEDIUM |

## Research assumptions (material)
1. **Pivot width k** — needed to define "respected". Alternatives: k=1, k=2 (both tested: A1 vs A2). Sensitivity: HIGH (changes which levels exist).
2. **Anchor = pivot that took an older pivot within its own bars** — the operational meaning of "spiked out". Alternative: any higher high in the prior leg. Sensitivity: MEDIUM.
3. **Window 09:30–11:30, flat 12:00** — source gives "after the open" and "before lunch". Alternative 09:30–12:00. Sensitivity: MEDIUM.
4. **No news filter** — no event calendar on disk; declared as an unimplemented source rule. Direction of bias: unknown.
5. **Level lookback = current + previous session day.** Sensitivity: MEDIUM.

## Contradictions preserved
- Trigger: breach (0:46:33) vs close-add (1:26:32) → separate interpretations A1 vs A4.
- Partials: "not the biggest fan" (0:32:29) vs "usually 50%/70%" (0:47:21) → A1 (none) vs A3 (50/50).
