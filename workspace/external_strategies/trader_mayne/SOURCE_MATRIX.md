# Family B — Trader Mayne HTF-range / OB / LTF-breaker (`coBMd1vk2Lo`)

**Source-recovery change vs rule sheet:** the rule sheet (§1, §5 "Strategy C") marked this video *inaccessible,
all rules MISSING*. The creator-uploaded captions were retrieved on 2026-09-24
(`_source_transcripts/coBMd1vk2Lo.json`, is_generated=False, 628 snippets, SHA prefix `07dd377895668e5b`).
They contain a near-complete mechanical framework. The rule sheet's "Strategy C: all MISSING" is **superseded**.

Setups: B-long (bullish range, buy in discount OB), B-short (bearish range mirror; short examples 0:47:18–0:52:45).

| Rule | Source evidence | Class | Mechanical definition | Ambiguity | Econ. importance |
|---|---|---|---|---|---|
| Two timeframes, HTF analysis / LTF execution | 0:05:29 "at least two time frames"; pairs weekly→daily/H12, daily/H12→H1, H4→M15, scalp H1→M5 | STATED | B1 H4→M15, B2 H1→M5, B3 D→H1 | which pair is primary | HIGH |
| 3-candle swings | 0:07:20 "three candle swing system" | STATED | pivots k=1 | — | HIGH |
| MSB = candle close through the swing | 0:07:20 "we need to see a candle close through this high" | STATED | HTF close > last confirmed untaken swing high | — | HIGH |
| Range = immediate swing low → swing high formed after MSB | 0:18:58; 0:53:36 "take the most immediate low… exact swing low before the most swing high" | STATED | low = lowest low between broken swing and MSB bar; high = next confirmed pivot high after MSB | "immediate" swing low vs leg low | HIGH |
| OB = down candle(s) before the move up that broke structure | 0:19:49–0:21:33 "the selling that occurred before the buying… three down candles… or just the last" | STATED | consecutive bearish candles ending at the leg low (≤3) | 1 vs up to 3 candles | MEDIUM |
| Buy in discount of the range | 0:16:15–0:17:16, 0:23:19 "we're now in a discount" | STATED | entry ≤ 50% of range | — | MEDIUM |
| Target = external (range high) | 0:26:57, 0:33:08 | STATED | limit at range high | — | HIGH |
| LTF breaker: swing low forms, is taken, then the generating high is broken | 0:29:35–0:31:22 | STATED | LTF k=1 swing low after OB touch; later bar trades below it; entry at first LTF close above the swing high that preceded it | "broken" = close (per MSB definition) | HIGH |
| Stop below the stop-run low | 0:33:08 "if this low gets taken out I'm wrong anyways" | STATED | sweep extreme − 1 tick | buffer | MEDIUM |
| Min 2:1 R:R else no trade | 0:34:52–0:35:47 | STATED | reject if (target−entry) < 2×risk | — | HIGH |
| At 2R de-risk: half off or BE | 0:33:08 "I'm 2R, I de-risk… take half off or move my stop to break even" | STATED (either) | move stop to BE at +2R | half vs BE | MEDIUM |
| Direct HTF entry at OB top, stop at its bottom | 0:26:57 | STATED | B4 limit at OB top, stop OB low − 1 tick, target range high, 2R rule | — | MEDIUM |
| Multiple shots allowed after stop-outs | 0:36:40 | STATED | NOT implemented: one attempt per HTF setup (declared) | — | MEDIUM |
| Setup expiry | — | MISSING → RESEARCH_ASSUMPTION | 30 HTF bars, or HTF close beyond range low, or target hit before entry | — | MEDIUM |
| Instruments: any; crypto, FX, futures, commodities | 0:41:10 | STATED | MNQ (dev) | crypto-origin | — |
| Session | none (crypto trader; 0:37:33) | MISSING → RESEARCH_ASSUMPTION | 24h, positions may be held overnight (max 12 days) | prop-deployability differs | MEDIUM |

Research assumptions: (1) OB construction ≤3 candles; (2) range low = leg low; (3) one attempt per setup;
(4) 30-bar expiry; (5) BE (not half) at +2R; (6) entry at LTF close of the break bar. Each is a single choice,
not tuned; sensitivity is examined only through the pre-declared B1–B4 lattice.
