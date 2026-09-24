# Family C — 50% Rebalance / PO3 (`HNuRp9Z1bMs`, Trader Kane)

Primary: creator captions (`_source_transcripts/HNuRp9Z1bMs.json`, is_generated=False, 752 snippets, SHA prefix
`690b0d25980b1c6b`). Changes vs rule sheet: the entry trigger, SMT timing, the hourly/H4 manipulation times and
the BE trigger are now transcript-sourced (rule sheet had them as "reported" from non-verbatim analysis).

Setups: C-short (bearish PO3 reversal), C-long (mirror: "just flipped", 0:12:54).

| Rule | Source evidence | Class | Mechanical definition | Ambiguity | Econ. |
|---|---|---|---|---|---|
| NQ only; ES comparison | 0:03:43 "I'm only trading NASDAQ… I look at ES for divergence" | STATED | MNQ traded, ES compared | — | HIGH |
| Daily / H4 / H1 PO3 alignment | 0:07:22–0:09:12; 0:34:50 "create a box where they all align" | STATED | H1 required; H4 in C2 | daily wick not operational | HIGH |
| 10:00 hourly candle manipulates above the 09:00 hourly high | 0:11:03 "at 10:00 a.m. it's most likely going to manipulate above the previous 9 hour high"; 0:11:59 | STATED | NQ high in [10:00,11:00) > NQ high in [09:00,10:00) | 09:30 variants also shown | HIGH |
| H4 wick above the previous H4 high | 0:10:09, 0:47:16 "previous 4-hour high… resting around EQ" | STATED | C2: NQ high in 10:00 hour > high of 06:00–10:00 H4 bin | — | MEDIUM |
| Active window 09:15–11:30 ET | 0:12:08 | STATED | entries 10:00–11:30 | — | MEDIUM |
| SMT: NQ takes the high, ES fails | 0:28:59–0:29:56; 0:48:12 "ES is trading above this high" (dotted line) | STATED | at entry, ES high since 10:00 ≤ ES 09:00-hour high | synchronization window | HIGH |
| Inversion = a prior gap that should support is traded through | 0:32:55 | STATED | most recent bullish 3-candle FVG completed 09:30→manip. high; entry at first exec-TF close below its bottom | which FVG | HIGH |
| Sell-stop or limit re-tap | 0:31:52 "limit a retap… or sell stop" | STATED | close-below entry (sell-stop proxy); re-tap NOT tested | preference MISSING | MEDIUM |
| Execution TF 3m / 5m | 1:00:08 "on the 3 minute… 5 minute" | STATED | C1 3m, C3 5m | — | MEDIUM |
| Stop above the SMT high | 0:33:55 "stop loss at divergence" | STATED | NQ high since 10:00 + 1 tick | buffer | HIGH |
| Target 50% of the range | 0:03:43, 0:33:55 | STATED | 50% of [range low, stop high] | range endpoints | HIGH |
| Range endpoints | 0:45:33 "high right here is the high" (swept high); 0:50:06 | INTERPRETED | C1 low = extreme since 18:00 ET; C4 = previous H4 bin low | endpoint choice | HIGH |
| BE when new hourly candle flips / 15m low taken | 0:50:06–0:51:01; 1:01:56 "as soon as we take out the 15-minute low I'd be break-even" | STATED | BE when low of last completed 15m candle before entry is taken | hourly-flip not coded | MEDIUM |
| Doesn't trade Mondays/Fridays | 1:13:22 "because I don't really trade Mondays and Fridays" | STATED (preference; Monday trades shown) | NOT applied; Tue–Thu reported as a pre-declared descriptive subset | contradicts examples | LOW |
| Avoid the open itself | 0:52:58 | STATED | entries start 10:00 | — | LOW |
| Flatten time | 0:18:15 "I'll come look at this at 4:00" | INTERPRETED | flat 16:00 ET | — | LOW |

Research assumptions: SMT evaluation window (10:00→entry), FVG choice (most recent), range-low choice (C1 vs C4),
16:00 flat. BTC/ETH variant (VISUAL) not tested — no owned crypto minute data with the needed pair alignment.
