# TRIDENT_V2 — SOURCE SPEC (one canonical long model)

Source: `ADnslyKOwFE` creator captions (`workspace/external_strategies/_source_transcripts/ADnslyKOwFE.json`, SHA prefix
`1272f03ba35728f0`). BASE_SHA `a1486c4738bb96babaed396fe9163a86a679506b`. Code: `trident_v2/strategy.py`.
Adjudication record: Agent 1 decision + Agent 2 verbatim review (AGREE on the EMA rulings, 2026-09-24); Jev advisory
(`JEV_V2_ADJUDICATION.json`) — per work-order addendum §C Jev did not decide anything here.

Classes: STATED (verbatim), INTERPRETED (joins stated parts), ASSUMPTION (needed to run, not in source), OMITTED (stated
but not reproducible; disclosed).

## CORE ENTRY CONDITIONS (all required)
| # | Rule | Verbatim basis | Class | Mechanical definition |
|---|---|---|---|---|
| C1 | London kill zone 03:00–06:30 NY | 0:02:47 "only be trading London from the hours of 3:00 a.m. … stop looking for entries at around 6:30 a.m." | STATED | the doji bar and the confirmation bar both start inside [03:00, 06:30) ET |
| C2 | 30-minute chart only | 0:02:47 "we're only going to be trading the 30 minute time frame" | STATED | 30m bars on the ET wall clock |
| C3 | FVG formed in the window | 0:06:24 "fair value gap … printing on the 3 a.m. candle … 2:30 or 3:30 … highly probable"; 0:33:54 "not worried about this fair value gap … printed outside of our kill zone" | STATED + INTERPRETED | bullish 3-candle gap (low of candle 3 > high of candle 1), third candle starts inside [03:00, 06:30); three consecutive 30m bars |
| C4 | Doji whose wick passes through the FVG 50% | 0:07:19 "If I get a doji candle here, especially a wick that wicks through it" (CE / 50%) | STATED | low < (FVG bottom + FVG top)/2 |
| C5 | Doji body not inside the FVG | 0:09:06–0:10:01 "Say this wasn't a doji and the body of this candle was in here … this would be an invalidation" | STATED | min(open, close) ≥ FVG top |
| C6 | Doji threshold | not given | ASSUMPTION | \|close − open\| ≤ 0.25 × (high − low) |
| C7 | (removed) | Agent 2 audit 2026-09-24: no fill / close-below-gap invalidation anywhere in the transcript; V1 carried it as a generic ICT import | — | no gap-failure rule; the doji search window is bounded only by the kill zone (≤ 7 bars after the gap) |
| C8 | Next candle closes below the doji high | 0:07:19 "the next candle after this doji candle closes below this high … If it closes above the high, I'll invalidate" | STATED | confirmation close < doji high, else the setup is dead |
| C9 | EMA 5/9/13/21 stacked bullishly | 0:05:31 "they're all stacking … strong bullish structure … If they were intertwining … I wouldn't be interested in any price action" | STATED (exclusion) | at the confirmation close EMA5 > EMA9 > EMA13 > EMA21 (30m, EMA 13 per 0:05:31; "13 or 15" at 0:32:57 unresolved → 13) |

## CONTEXTUAL / PREFERRED (recorded per trade, NEVER gate)
| Item | Verbatim basis | Recorded as |
|---|---|---|
| Above 200 EMA = bias | 0:33:54 "if we're above the 200 EMA, that's my bias"; 0:41:08 takes a long when the 4H/daily is below the 200 EMA and "cut it earlier" | `ctx_above_ema200` |

## OMITTED (declared; owner + Agent 2 acceptance required before any sealed run)
- "Bull trading" TradingView indicator colour (daily candles). 0:44:48 "if these candles weren't green … invalidated setup";
  0:19:39 "I don't rely on indicators … confluence"; 0:45:39 "green and black … highly probable". Formula unknown, legend
  inconsistent → not reproducible. Fidelity status: **PASS_WITH_DECLARED_OMISSION**.
- Daily-chart TP target selection and the "minimum 1:20 R:R" (0:00:56, 0:12:41, 0:38:29): the target is read from the daily
  chart by discretion; no mechanical daily target is given → not implemented as an entry filter.
- "Large bearish candle" exit (0:19:39): no size given → not implemented.

## ENTRY / STOP / EXIT
| Item | Basis | Class | Definition |
|---|---|---|---|
| Entry | 0:43:00 "you could even enter here … it closed inside the range" | STATED | market at the confirmation bar close (+ modelled spread/slippage) |
| Stop FX | 0:07:19 "my stop loss would be below this candle low"; ~10 pip (0:12:41) | STATED + ASSUMPTION (buffer) | doji low − 1 pip |
| Stop gold | 0:12:41–0:13:34 "with gold, I don't use a hard stop loss. I will wait for a close below" | STATED + ASSUMPTION (catastrophic) | exit on a 30m close below the doji low; catastrophic hard stop = doji low − 3 × doji range; R measured vs the doji low |
| Exit | 0:19:39 "usually I'll just ride the trend until like the EMAs cross over" | STATED | first 30m close with EMA5 < EMA21 after entry |
| Max hold | not given | ASSUMPTION | 10 calendar days, then market exit |
| Direction | 0:03:42 long-biased; shorts not described | STATED | long only |
| Instruments | 0:08:11 USDCAD, NZDUSD, EURUSD, GBPUSD, USDJPY (not AUDUSD) + gold | STATED | the six |
| Re-entry | not given | ASSUMPTION | one setup per FVG; one open position per instrument |

## Declared untested alternatives
- C3 with the gap's THIRD candle at 02:30 (i.e. whole FVG before 03:00) eligible — not tested.
- C7 abort-on-gap-failure (V1 behaviour) — not tested; pre-PnL counts with and without it in `FIDELITY_V2_DEV_COUNTS.json`.

## Frequency vs source claim (pre-PnL counts, DEV 2022–2024, `FIDELITY_V2_DEV_COUNTS.json`)
EURUSD 4.7/yr, GBPUSD 5.4, USDJPY 8.7, USDCAD 4.7, NZDUSD 4.0, XAUUSD 7.0 (103 setups pooled) vs the creator's 6–8/yr/pair
(gold 10–15). With the removed, unsourced C7 abort the draft had 36 setups (1.3–3.0/yr): that import, not source
discretion, was the main frequency choke. No stated rule was loosened.

## Line against V1
V1 (E1–E4) applied EMA200 as a hard gate and used a middle-candle FVG window; E1/E3 used a fixed 20R exit. Those runs read
the same DEV window, so V2 DEV results are **not blind** to V1 outcomes; V2 rule choices above are justified by source text
only, and the sealed window 2025-01..2026-08 remains unread.
