# MMXM_V2 — SOURCE SPEC (one canonical model, sell + mirrored buy)

Source: `IB-fyWI5j8w` creator captions (`workspace/external_strategies/_source_transcripts/IB-fyWI5j8w.json`, SHA prefix
`0e56b9491707afd8`). BASE_SHA `a1486c4738bb96babaed396fe9163a86a679506b`. Code: `mmxm_v2/strategy.py`.
Adjudications: Agent 1 decision with Agent 2 review (outside-KZ veto, lookback, zero anchor, KZ gate); Jev advisory only.

## Framework conditions (all required)
| # | Rule | Verbatim basis | Class | Mechanical definition |
|---|---|---|---|---|
| M1 | Predetermined bias | 0:05:32 "You need a predetermined expectation on the day. So, you'll only favor this when you're bearish"; 0:29:02 "If I'm bearish on the week…" | STATED + ASSUMPTION (method) | bias = previous completed week (FX days, W-FRI) close vs open; sells only if bearish, buys only if bullish |
| M2 | Key levels | 0:03:41–0:04:39 "previous days highs and previous days lows … previous week high and previous week low" | STATED | PDH/PWH for sells, PDL/PWL for buys (HTF FVG/OB/breaker levels NOT coded — no construction given) |
| M3 | Only days opening near a key level | 0:06:27 "I'm only considering days where we open closer to these one of these key levels. I'm not going in every day trying to find this" | STATED + INTERPRETED | a level is eligible only if the FX-day open is closer to it than to its opposite (PDH vs PDL, PWH vs PWL) |
| M4 | Run of the level | 0:12:06 "you have a low, a high, and then you run that high" | STATED | first 15m bar of the FX day trading beyond an eligible level; **no kill-zone requirement and no day veto** (V1's outside-KZ veto had no basis) |
| M5 | SMR extreme | 0:12:06 "high, low, a high, low, higher high, lower low" | STATED | running extreme from the run bar until the break |
| M6 | Structure break by BODY close | 0:12:58 "bodied close 15 minute" | STATED | first 15m close through the most recent confirmed k=1 swing (opposite side) formed before the SMR extreme — no lookback cap (V1's 60-bar cap had no basis) |
| M7 | Displacement | 0:16:35 "bodied candles, engulfing candles … momentum"; 0:17:27 wicky close → let a retracement go | STATED + ASSUMPTION (threshold) | breaking candle body ≥ 50% of its range and coloured with the break; otherwise no first-leg trade that day (second leg / Silver Bullet NOT implemented) |
| M8 | Fib 1 / fib 0 | 0:37:21 "you'll have some sort of swing made … This is your distribution side"; 0:40:07 "from this high to this low 60% of the range"; 0:50:40 "your stop loss is a swing … anchor your fib from there" | STATED + INTERPRETED | 1 = SMR extreme; 0 = extreme of the displacement leg, fixed when the first confirmed k=1 swing at/after the break bar exists (order placed at that confirmation) |
| M9 | Entry / stop / target | 0:55:52 "at the 62 level with a 90% stop loss and the zero TP is like 2.2R"; 0:56:43 "705 90% stop-loss shave" | STATED (two plans; 0.62 chosen: it is the first OTE level reached, so every 0.705 fill also passes 0.62) | limit at 0.62, stop 0.9, TP at 0 |
| M10 | Break-even | 0:45:20–0:46:15 "go break even 0.2, and you're closing there. Not wicking there" | STATED | 15m CLOSE beyond the 0.2 level → stop to entry |

## Context (recorded, never gates)
- Kill zones NY 02–05 / 07–10 / 10–12 (0:29:52) → `ctx_disp_in_kz`. The source describes when the framework tends to
  appear, not a mandatory gate (Agent 2 review: a gate needs verbatim basis; none).

## Assumptions (declared)
FX day = 17:00 NY roll (source gives no day definition); weekly bias method (M1); displacement 50% body (M7); unfilled order
expires at 17:00 NY at the end of the FX day of the displacement; max hold 3 days then market exit; one setup per side per
day; pairs EURUSD, GBPUSD, USDJPY (examples UJ, EU, "pound", 1:00:13+).

## Not implemented (declared)
Second-leg / Silver-Bullet entry (0:17:27–0:18:19), scaling in after BE (0:18:19), ADR room check (0:31:40, "eyeball"),
HTF PDA levels, -0.28/-0.62 extensions, discretionary TP removal (0:46:15).

## Frequency vs source (pre-PnL, DEV 2022–2024 orders): EURUSD 68/yr, GBPUSD 70/yr, USDJPY 70/yr (placed limit orders; not all
fill). Source: "fewer than 10 a month is preferable" (rule sheet, 0:18:28–0:22:42). Consistent in order of magnitude.

## Line against V1
V1 (F1–F3) read the same DEV window; V2 DEV is not blind. V2 choices rest on the verbatim basis above; sealed window unread.
