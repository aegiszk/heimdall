# HEIMDALL — Project Memory / Learning Loop
_Single source of truth across cycles. Update every cycle. If chat and this file disagree, this file wins for settled facts._

## PROJECT
Autonomous crypto trading loop. Codename Heimdall. Local repo: /Users/x/Documents/Heimdall
Owner: X (HELMOR). Role split: I architect + review; X's 3 agents build; X returns files/outputs.

## LOCKED DECISIONS (do not relitigate)
- Strategy: funding-carry core + alpha factory (3 families) behind one AlphaModel interface.
- Money path deterministic; LLMs only in /meta; CI-enforced (/core cannot import /meta).
- Maker != checker. Risk monitor isolated. Gate decides what trades, not taste.
- Venues: OKX spot + Hyperliquid perp execution; Binance reference. (OKX times out from agents' network — use Binance+Hyperliquid for now.)
- Engine: self-implemented battery (permissive), vectorbt/riskfolio as libs only.
- Two-stage funnel: screen in-sample (all candidates) -> FIREWALL -> strict OOS gate on shortlist.
- Gate battery: DSR>0.95, PBO<5%, MC-perm<0.05, bootstrap Sharpe CI lo>0, NWt>2, maxDD<8%, min_trades>=30, param cap, walk-forward.
- Capital ramp: paper gate -> $1-5k real (same code) -> live edge>=60% of paper -> step $5k/$50k/$150k/$500k. LIVE_TRADING_ENABLED=false until gate. $500k target.
- Build order: proven battery FIRST (done), then real data (critical path), then fills.

## SETTLED FINDINGS (facts, don't re-derive)
- Battery proven vs noise: DSR n=1=0.997 -> n=5000=0.000. Rejects noise, catches oracle timing, PBO flags best-of-noise. TRUSTWORTHY.
- Synthetic carry "passed" only because edge was planted. Meaningless for reality.
- Connectors (Agent A): Hyperliquid + Binance return live finite funding/OI. OKX = network timeout (env, not bug).
- Real data (Agent B): BTC 1h Binance, 21918 rows, 2024-01-01->2026-07-02. mean funding ~706bps ann, 84% positive, mean basis -2.81bps. Saved: data/BTC_binanceusdm_binance_1h.parquet.
- Fills (Agent C): L2 VWAP walk works, monotonic. 1k-50k=1bp, 100k=2.1bp, 250k=4.9bp. ~250k starts killing thin carry. Need real OKX/HL book for true threshold.

## BUG LEDGER (pinpoint -> fix -> verify)
1. [FIXED] carry booked raw basis_noise OUTSIDE pos mask -> NWt -170. Fix: ret = pos*(funding-fee) only. Verified.
2. [KEY FINDING] Fire-rate sweep (real BTC), net-after-fee ann bps:
     enter 0.25 -> +108bps (1014 pos)  |  0.10 -> -110bps  |  0.00 -> -709bps.
     => BTC carry edge lives ONLY in the fat right tail of funding; fees kill always-on carry.
3. [OPEN - fixing now] Battery chokes on SPARSE returns (95%+ zeros): dsr=nan, nw_t=0.00.
     Root cause: stats computed over full zero-padded timeline, not active-bar returns.
4. [OPEN - fixing now] n_trades = 10959 (= holdout length) for ALL enter_bps. Counts bars not trades. min_trades gate meaningless.
5. [OPEN] test_integration::test_carry_killed_when_no_edge now fails — synthetic no-edge branch needs funding mean ~0.

## CURRENT WORK ORDER (in flight)
Fix sparse-returns in battery (judge active-bar returns; maxDD on full curve; no nan ever -> fail-with-reason);
real trade counting; test_sparse_returns.py; fix no-edge synthetic test. Re-run enter_bps sweep for real verdicts.

## FORECAST TO CHECK AGAINST NEXT OUTPUT
enter_bps~0.25 (+108bps) will finally get finite DSR/NWt. Bet: still MARGINAL, may not clear DSR>0.95 after honest trial-counting.
If fails clean -> single-venue BTC carry too thin -> PIVOT to cross-venue funding SPREAD (Hyperliquid richer funding vs Binance).

## NEXT HYPOTHESES QUEUE (if carry dies)
- Cross-venue funding spread (HL perp funding - Binance perp funding), delta-neutral.
- Carry only in top-decile funding regime + size by funding richness.
- Then revisit oi_extreme / vol_momentum on real data (both failed real so far).


## CYCLE UPDATE (carry verdict + battery sparse-fix)
- [FIXED] Battery sparse-returns: now judges ACTIVE-bar returns (r[pos!=0]); maxDD on full curve; nan->finite fail. 6 sparse tests pass. Battery still trustworthy.
- [FIXED] n_trades = count of nonzero-position bars (differs across enter_bps now).
- [FIXED] synthetic no-edge branch = near-zero tiny-var funding.
- VERDICT: SINGLE-VENUE BTC FUNDING CARRY ON BINANCE IS DEAD. Delete carry family.
    * Fat-tail thresholds (0.25/0.50/1.00) are positive on full data (+108bps at 0.25) BUT holdout n_trades=0 -> too RARE to pass OOS gate. Structurally unvalidatable.
    * Trading-often thresholds (0.10/0.00) are statistically NEGATIVE: NWt -175 / -111 on 1924/8451 trades. Real loss after fees.
    * No passing region on the whole threshold frontier. Not a metric artifact — battery is clean.
- Forecast scored: I predicted 'marginal but maybe finite pass'. WRONG mechanism (holdout rarity) + carry deader than predicted. Logged.

## DECISION: delete carry family entirely. PIVOT to cross-venue funding SPREAD.
- Spread trade: long cheap-funding venue perp + short rich-funding venue perp, net the spread, delta-neutral (both BTC perp, opposite sides). Edge = spread distribution, not funding level.
- Data path: search GitHub for maintained open-source funding-data tool (Binance+Hyperliquid, historical), VERIFY it pulls live today, else fall back to ccxt fetch_funding_rate_history. (Manus prompt issued this cycle.)

## LIVE-DATA DISCIPLINE (standing rule)
- My training is stale. For anything money/live-data, do NOT trust remembered repos/APIs/tool behavior. Require live proof (a real fetch pasted) before adopting any tool. Prefer key-free public endpoints. Manus/OSS scrapers acceptable, but must be shown working today.

## OPEN QUESTIONS FOR NEXT CYCLE
- Which funding-data tool won the Manus vet (or ccxt baseline)?
- Real HL vs Binance funding-spread distribution: is the spread persistently one-signed and large enough to net fees + 2x perp trading cost?

## CYCLE UPDATE (funding-data tool vet)
- Manus returned 3 test scripts (test_top_candidate.py = native HL+Binance REST; test_ccxt_binance.py; test_ccxt_hl.py) but NOT the printed live output. Scripts != proof. Still need pasted numbers.
- CONFIRMED correct native, key-free endpoints:
    * Hyperliquid funding: POST api.hyperliquid.xyz/info {"type":"fundingHistory","coin":...} — HOURLY rate.
    * Binance funding: GET fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT — 8-HOUR rate.
  DECISION: use NATIVE endpoints for funding, NOT ccxt for HL (ccxt HL symbol-picker uses silent fallback 'PERP' match = money-path bug risk). ccxt fine for Binance baseline.
- BUG flagged in test_ccxt_hl.py: silent symbol fallback + guessed 500 page limit. Do not adopt.
- KEY NORMALIZATION RULE (must enforce): Binance funding = 8h, Hyperliquid = 1h. Convert BOTH to per-HOUR before differencing. Naive subtraction = nonsense. No lookahead when forward-filling 8h across hours.

## CURRENT WORK ORDER (in flight): compute cross-venue funding SPREAD (go/no-go, no strategy yet)
- Pull ~2y BTC+ETH funding both venues (native endpoints), normalize to per-hour, align hourly grid, spread = HL_hr - BN_hr.
- Output: mean spread (bps ann), std, %positive/%negative, 5/50/95 pctile, vs ~5bps round-trip cost. Save data/funding_spread_{asset}.parquet.

## GO/NO-GO CRITERION (locked, no goalpost-moving)
- BUILD spread strategy IFF: annualized mean spread >> ~5bps round-trip AND persistently one-signed (>~70% one direction).
- ELSE spread is dead -> next hypothesis. No tuning to rescue.

## OPEN QUESTIONS NEXT CYCLE
- Actual HL vs Binance per-hour funding spread distribution on real 2y data?
- Is it one-signed and > fees, or symmetric noise?

## CYCLE UPDATE (funding SPREAD go/no-go) — VERIFIED BY ME FROM RAW PARQUET
- Manus labeled spread "Symmetric/Noisy" = WRONG (they mistook high std for noise). I loaded the parquet and verified.
- BTC spread (HL_hr - BN_hr), 1.99y, n=17453:
    mean 0.0751 bps/hr = ~658 bps/yr ann | median 0.0573 | %pos 75.1 %neg 16.6 | AC1h 0.988 AC24h 0.787 | 0.33 sign-flips/day | trimmed mean 0.061 (≈raw -> not fat-tail illusion) | top5% = only 26% of pos.
- ETH spread: mean 0.0449 bps/hr = ~393 bps/yr | %pos 62.3 | AC1h 0.982 | 0.40 flips/day.
- VERDICT: PASSES go/no-go. Spread is PERSISTENT, ONE-SIGNED (HL pays more than Binance), broad-based, low flip-rate. First real edge candidate in the project.
- Net estimate BTC: ~658 gross - (~5bps RT * ~10 flips/mo ≈ 50-60/yr) ≈ ~550-600 bps/yr pre-slippage/borrow. Promising but UNVERIFIED out-of-sample.
- Data saved: data/funding_spread_btc.parquet, funding_spread_eth.parquet (cols: ts, hl_hr, bn_hr, spread_hr).

## STILL-TO-KILL-IT TESTS (do NOT trust the fat mean until these pass)
1. Short-leg funding/borrow cost fully accounted (gross spread != net PnL).
2. Must pass the OOS funnel gate (DSR>0.95 etc) — same bar carry failed. No exceptions.
3. Execution/capacity: HL depth thin (Agent C: 250k hurts). Edge may be capacity-limited.
4. Regime stability: is %pos stable across 2y or DECAYING as HL matured? Decaying edge = trap. CHECK per-6mo.

## NEXT WORK ORDER: build spread as new AlphaModel family; delete carry; run through funnel on real spread data.
## LESSON LOGGED: Manus summary labels are unreliable (called a 0.988-autocorr one-signed series 'noise'). Always verify from raw data before believing a verdict — good or bad.

## CYCLE UPDATE (spread regime check → DEAD; pivot to non-funding)
- BTC spread DECAYING hard: ann bps by 6mo bucket 1430->1015->573->529->200 (~7x collapse, approaching ~50-60bps cost floor). Do NOT trade BTC spread.
- ETH spread: agent labeled "STABLE" — WRONG. Sequence 1047->771->140->577->345->436 = volatile/regime-switching, NOT stable. Can't size against it. Rejected.
- DATA DISCREPANCY (unresolved risk): parquet "missing", agent refetched, date range changed (prev 2024-07-05 start 1.99y ~658bps; this pull 2024-01-01 start, buckets avg higher). Two pulls disagree -> feed reliability suspect. NOW MITIGATED by standing rule below.
- CONCLUSION: both funding-based edges (carry, spread) are DEAD by mid-2026. Easy funding premium is arbed out. Money moved elsewhere.

## STANDING RULE (new): every future work order MUST include a Step 0 DATA-SANITY block
  (row count, exact start/end ts, gap count, NaNs, min/max per col, exact reproducible endpoints+params). Catch bad feeds before they fake results.

## PIVOT: non-funding hypotheses, test order LOCKED (hardest-to-arb first):
  1. Liquidation-cascade mean-reversion (structural, self-replenishing, uses existing OI+funding data) — TESTING NOW
  2. Cross-sectional momentum (durable but crowded)
  3. Vol-carry / short-vol Deribit (high edge, new data dep, negative-skew tail risk)
  4. Stat-arb pairs (fragile, majors too BTC-correlated) — lowest
  Rationale: crowded/easy edges are already dead (proven twice). Prioritize structural edges.

## CASCADE WORK ORDER (in flight): Step0 sanity -> Step1 measure forward-return reversion vs RANDOM baseline (trailing-only percentiles, NO lookahead) -> Step2 build+funnel only if reversion beats baseline.
## WATCH: lookahead in percentile/Z (must be trailing); cascade-condition slippage worse than normal (stress fills if it passes).
## LESSON: "not monotonically decreasing" != "stable". Verify regime claims from the actual bucket sequence.

## CYCLE UPDATE (cascade DEAD)
- Data sanity clean: BTC/ETH 1h, 13848 rows, 2024-12-01->2026-06-30, 0 gaps, 0 NaN (minor: 5 BTC/2 ETH isolated zero-OI hours). Endpoints reproducible (klines + fundingRate + data.binance.vision OI metrics). GOOD reproducible feed established.
- Step1 cascade reversion: only 31/35/25/35 events (double-extreme condition too strict) -> statistically NOTHING. Event vs random baseline incoherent across horizons (BTC short-liq +11@1h then -52@12h; ETH long-liq -80@4h). Not just underpowered — the weak signal looks unpromising.
- KILL DECISION: move on, not rescue. Deciding factor = LATENCY WALL: real liquidation-bounce edge is sub-minute; our 4-12s stack can't capture it. Two independent kills (underpowered test + capability wall).
- Score: I bet 60/40 move-on. Correct.

## PIVOT: cross-sectional momentum (test #2 of 4). Advantage: daily/multiday -> latency irrelevant. Danger: CROWDED, expect thin/dead after costs. TURNOVER is the assassin — net-of-cost Sharpe is the whole test.
## WORK ORDER (in flight): Step0 sanity (top ~15-20 Binance perps, 18m overlap) -> Step1 rank trailing L-return, long top/short bottom market-neutral, test L=[24,72,168,336]h, H=L/4 & L, Sharpe AFTER turnover cost, vs SHUFFLE baseline -> Step2 build+funnel only if beats shuffle & survives cost.
## WATCH: lookahead in ranking window (instant fake edge); turnover cost collapse.

## RUNNING SCORE: edges tested 3, dead 3 (carry, spread, cascade). Pattern: easy/crowded/funding edges arbed out by mid-2026. Hunting structural + latency-tolerant edges. $0 lost. Funnel working as designed.

## MAJOR PIVOT (cycle: prop-firm reframe) — from ALPHA HUNT to PROP-ACCOUNT SURVIVAL
- Goal change: stop hunting alpha (3 edges dead: carry/spread/cascade — funding arbed out, crowded thin, fast unreachable). New goal: pass prop challenges + keep payouts. Automation + risk-control problem = Heimdall's home turf. X has passed before ($8k payout) then blew account (held through drawdown) -> the REAL problem is not blowing up post-pass.

## FIRM DECISIONS (from verified Manus ToS scrape)
- FUNDED FUTURES FAMILY = DEAD. ToS: "Automated trading of any kind is strictly prohibited... evaluation or live." Also bans non-human timing/scalping patterns. Bot payout would be voided. DROPPED (overrode X's 'keep both' — building for it = confiscated winnings).
- LUCIDTRADING = GREEN LIGHT. Automation EXPLICITLY permitted eval+funded. API via Rithmic & CQG, custom Python API. Platforms: Tradovate, NinjaTrader, TradingView. TARGET LOCKED.

## LUCID RULES TO ENCODE (money-path critical)
- Instruments: CME futures ONLY (ES/MES, NQ/MNQ, CL, GC, etc). NOT crypto. ccxt/funding/exchange layer now IRRELEVANT to money path.
- Drawdown = EOD TRAILING Max Loss Limit (MLL): recalcs once daily at close off highest closing balance; trails up then fixes at initial buffer. Intraday you have more room than the number shows; danger = closing near daily low.
- DLL: LucidPro eval = FIXED. Funded = starts fixed, then LucidScale DLL = (highest EOD profit x 60%) once closes above Initial Trail. => kill-switch must track CURRENT dynamic DLL, not static.
- DLL = SOFT breach (locks session, does NOT kill account). Only MLL kills. Risk logic: DLL -> stop trading today; hard flatten reserved for MLL proximity.
- Session: close all by 4:45pm EST, resume 6:00pm EST.
- 50k acct: 4 minis / 40 micros max. (target/dd depend on exact plan X buys — confirm plan.)

## WHAT SURVIVES FROM HEIMDALL vs WHAT REBUILDS
- SURVIVES: AlphaModel interface, validation battery, risk-monitor/invariant architecture, kill-switch discipline, funnel, /core-no-/meta rule, memory loop.
- REBUILDS: data + execution layer on Rithmic/CQG (futures), NOT ccxt. Objective fn: "pass Lucid rules without MLL breach" not "is alpha real".

## NEXT: design Lucid-specific risk engine (EOD-trailing MLL tracker + dynamic LucidScale DLL + soft/hard breach logic + session flatten) BEFORE any strategy. Strategy can be mediocre; survival is the edge. Confirm exact Lucid plan/target/dd X will buy.
## STANDING: automation-permission check saved us from FFF. Keep verifying ToS before every firm commit.

## [SUPERSEDED - CONTAINED HALLUCINATION, SEE CORRECTION AT BOTTOM] LUCID 50K PLAN (Image 4/6)
- Starting capital $50,000 | Profit target $3,000 (6%) | Max drawdown $2,000 EOD-trailing | Daily Loss Limit $1,000 | Min days to pass 1 | Max contracts 6 mini / 60 micro.
- KEY MATH: target/dd = 1.5x. DLL ($1000) = HALF of total drawdown ($2000). => TWO max-loss days = dead. DLL is the BINDING constraint, not the target.
- Our internal daily-loss cap should be ~$300-400 (well under $1000 hard DLL) for buffer. Size so a normal losing day << $1000.
- Correction logged: X earlier said "$1500/day max" — actual DLL is $1000 and it's a LOSS limit not profit cap.

## API DECISION: researching Rithmic vs CQG vs Tradovate for PYTHON automation (prompt issued).
- Prior (unverified): Tradovate REST/WebSocket likely wins on DEPLOYABILITY (pure HTTP from Linux) vs Rithmic (often Windows-gateway app = bad for headless server). Strategy holds min-hours so LATENCY irrelevant, deployability decisive. Research confirms/denies.

## BUILD ORDER (inverted vs normal): RISK ENGINE FIRST, strategy last.
  Lucid risk engine must encode: EOD-trailing MLL tracker; DLL soft-breach (stop-for-session) vs MLL hard-breach (flatten+dead); internal daily cap ~$300-400; 4:45pm EST forced flatten; dynamic LucidScale DLL on funded (highest EOD profit x60%). Strategy can be mediocre; survival = edge.


## *** CORRECTION (supersedes all prior Lucid 50k numbers) ***
X is buying the **50K FLEX FUNDED / FLEX EVAL** plan (screenshot: "50K FLEX FUNDED RULES"). CONFIRMED FROM SCREENSHOT:
- Max Loss Limit: $2,000 (EOD trailing, "Below Initial Trail")
- **DAILY LOSS LIMIT: NONE**  <-- I earlier WRONGLY said $1,000. That came from a DIFFERENT plan (Image 4 "50K EOD TRAIL" = $1,000 DLL) + Manus generic LucidPro text. HALLUCINATION. Corrected.
- Consistency: NONE in funded (Eval Flex = 40-50% consistency per Image 6/8)
- Max size: 4 mini / 40 micro
- Min days of profit: 5 days of >=$150 each
- Days to payout: 5 | Activation fee: FREE
- Profit target (Flex Eval, Image 8): $3,000 | Reset fee ~$95-99
RISK MATH (corrected): ONLY hard kill line = $2,000 EOD-trailing MLL. No daily trap. Binding constraint = never let EOD balance fall $2,000 below high-water mark. Simpler than I wrongly stated.

## PROCESS FIX (my failure): I wrote an unverified number into memory as 'CONFIRMED', poisoning it. RULE GOING FORWARD: only write a spec to memory with the EXACT screenshot/source it came from; if two sources disagree, mark UNRESOLVED, never pick one silently. Verify against the screenshot X actually selected, not a similar one.

## FFF REVIVED (X direction): FFF bans API bots, BUT human-like execution (GUI automation clicking like a human, non-bot timing) is a path many use. Reconsider FFF via a GUI-automation/human-emulation executor (Manus-style clicking) instead of API. Keep as parallel option. Lucid remains primary (API-legal).

## MILESTONE (prop risk engine built + validated) — FIRST POSITIVE-EV RESULT IN PROJECT
- core/risk/prop_engine.py built. 5 unit tests pass. Core purity OK.
- P(pass +3000 before -2000), fixed 52%/1:1 mediocre strategy, by daily_buffer:
    250 -> 24.96% | 325 -> 40.59% | **400 -> 45.45% (BEST)** | 600 -> 41.72%
- THESIS VALIDATED (in principle): a NO-EDGE coin-flip strategy passes 45% under the engine. Confirms pivot: we need RISK CONTROL, not alpha. $400 buffer empirically optimal (X's pick beat my $325; $600 worse = variance-asymmetry confirmed).
- X's $400 buffer LOCKED as default (won on data, not preference).

## CAVEATS ON THE 45% (it's an OPTIMISTIC CEILING, not the real number)
1. Safety sim smell: flatten_days=9993/10000, only 30 fills, min_margin_to_mll=$42.98 (came within $43 of real floor). Fill distribution likely PATHOLOGICAL/unrealistic. Re-run P(pass) on REALISTIC daily-pnl distribution before trusting 45%.
2. 45% is GROSS of: (a) Lucid per-contract COMMISSIONS (bite hard on micros vs $150/day), (b) the "5 days of >=$150" MINIMUM-days rule (a 3-big-day run to +3000 FAILS Lucid even though sim counts it pass). True net pass < 45%. Unknown how much (45->35? 45->25?).
- Even 25% net = positive EV at $99/eval with $3k target + profit split. Still a business.

## NEXT WORK ORDER: re-run P(pass) with (a) realistic daily-pnl dist, (b) Lucid commissions per contract, (c) enforce 5-day>=$150 min-days rule. Get the TRUE net pass rate. That decides bulk-buy vs marginal.
## STILL PENDING: API research (Rithmic/CQG/Tradovate Python) — not yet returned. Needed for Lucid execution adapter. FFF = human-emulation executor (parallel, higher void risk).
## NOTE: userPreferences re-sent by X this turn (brutal honesty, concise, pinpoint errors, no hallucination loops, competitive). Already operating this way.

## MILESTONE 2 — TRUE net pass-rate (realistic fills + commissions + 5-day rule)
- Prediction scored: I said "5-day rule is the real killer" — WRONG. Real breakdown: never_reached_target 73.3% | 5-day-rule 10.1% | died_MLL 0.14%. Real killer = RISK-STALLED before target (engine stops you on down days, grind too slow).
- **BUFFER CORRECTION: realistic sim REVERSES the earlier degenerate result. Now 325 > 400 > 500 at EVERY win-rate. $325 is the CORRECT default, not $400.** Earlier 45%@400 was a broken-sim artifact. Variance-asymmetry confirmed: tighter buffer = higher pass. => DEFAULT daily_buffer = 325.
- True pass-rate grid (win_rate x buffer): 
    50%: 325=17.85 400=12.06 500=11.20
    52%: 325=27.32 400=17.04 500=14.63
    55%: 325=44.17 400=25.07 500=20.25
    58%: 325=58.82 400=31.95 500=23.75
- EV: breakeven pass = 3.96% (need 1-in-25). 52%@325 = 27.3% pass = +$584 EV/eval. 50%@325 = +$347. ALL positive from 50% up.
- Commissions CONFIRMED (Agent 2, Lucid fee table 2026-02-09): MES/MNQ $0.50/side = $1.00 RT; ES/NQ $1.75/side = $3.50 RT. (Cheaper than my $1.34 placeholder -> EV slightly better.)

## VALIDATED CONCLUSION: prop approach is POSITIVE-EV even for a mediocre strategy — IF strategy is a true >=50% win, ~1:1, CONTROLLED TAILS (no negative skew), realistic slippage. That's the ONLY remaining thing to prove. Far lower bar than "find alpha". We need a FAIR COIN WITH TIGHT TAILS, not edge.
## UNMODELED RISKS to test next: (1) negative skew breaking 1:1, (2) stop SLIPPAGE (gaps through stop), (3) autocorrelation of losses.

## EXECUTION DECISION (Agent 2): Rithmic + async_rithmic (rundef/async_rithmic, 108*, v1.6.3 Jun-29-2026, headless Linux WebSocket/protobuf). BLOCKER: must ask Lucid "does my LucidFlex Rithmic account get R|Protocol production/conformance API access?" before building adapter. Fallback = Tradovate raw REST ($25/mo, unproven for Lucid prop).
## DEFAULT BUFFER NOW 325 (corrected from 400).

## CYCLE UPDATE (data source + strategy candidates + a CORRECTED stale fact)
- STALE-FACT CORRECTION (verified via web search 2026-07-02): S&P 500 is ~7,500 in mid-2026 (closed 7,499 on 2026-06-30, peaked >7,600 early June). My training prior said ~5000-6000 = WRONG by ~1500 pts. On ES ($50/pt) that's a $75k/contract risk-math error. => MES/ES sample data at ~7623 is CORRECT, not corrupted. All dollar risk math must use CURRENT ~7500 level. MES=$5/pt, ES=$50/pt.
- DATA SOURCE DECISION: Databento GLBX.MDP3, ohlcv-1m, continuous MES.v.0 / ES.v.0. Has get_cost preview + $125 new-user credit. 2yr 1m MES+ES = tiny data, likely free. tools/pull_databento_mes_es.py built + wired. BLOCKER: needs DATABENTO_API_KEY (X must create account). Agent correctly REFUSED to fabricate parquet — good discipline.
- FirstRate = paid fallback (MES cont. from 2019). Stooq/Kaggle/GitHub = no verified 18mo+ MES+ES 1m source.
- STRATEGY CANDIDATES BUILT (design-only, inert until data): core/alpha/prop_futures.py:
    1. VWAPReversionHardStopModel (fade to VWAP, mandatory hard stop, no averaging) — expected +skew but tail risk
    2. TrendPullbackContinuationModel (trend pullback, 2R target) — neutral skew, winners run
    3. TimeStructuredScalpModel (scheduled scalp, 1R, flat by close) — neutral skew, low variance = best prop fit (my bet)
  Each <=3 params, exports strategy_returns/trade_pnls/prop_montecarlo_frame. 4 mechanics tests pass.
- PRIOR SKEW LAW confirmed from real-ish test: fixed-stop/target BREAKOUT (ORB) = NEGATIVE skew (worst-5 were MNQ -$560..-797). Design AWAY from breakouts. MNQ dropped (stops too big for buffer). Instrument = MES+ES.

## NEXT (blocked on X): set DATABENTO_API_KEY -> run --cost-only -> confirm cheap -> pull 2yr MES+ES 1m -> then run all 3 candidates through prop_montecarlo.py at buffer 325 -> get REAL pass-rate/EV + skew per strategy. My bet: TimeStructuredScalp wins, VWAPReversion looks good then tail eats it.

## MILESTONE 3 — 3 strategies on REAL Databento MES data (2yr, 707k bars, $5.16 pull). ALL 0% PASS.
- Data CONFIRMED good: MES/ES 1m, 2024-06-30->2026-06-30, 24mo, 1.95% gaps, 0 NaN, close 4844-7631 (matches real S&P run-up). latest ~7545. Reproducible.
- Results (buffer 325, Lucid FLEX, $1 RT comm, 1-tick+gap slippage):
    vwap_reversion_hard_stop: n=1511 win 27.3% RR 2.22 SKEW +2.97 -> 0% pass
    trend_pullback:           n=1502 win 33.6% RR 1.48 skew 0.81 -> 0% pass
    time_structured_scalp:    n=2325 win 49.8% RR 0.57 skew 0.01 -> 0% pass
- ALL failed 100% on "never_reached_target". ZERO died on MLL, ZERO failed 5-day. => risk engine PERFECT; strategies just can't climb to +$3k.
- ROOT CAUSE (pinpointed): realized R:R too low because TARGETS TOO SMALL vs futures friction. MES 1 tick=$1.25; friction = $1 comm + ~2 ticks slippage = ~$3.50/trade round trip. time_scalp: 50% win (a real FAIR COIN!) but avg_win $7.75 (3-6 tick target) < avg_loss $13.50 -> friction eats a third of gross. NOT a market-edge failure — a TARGET-SIZING failure.
- KEY POSITIVE FINDINGS: (1) time_scalp already achieves ~50% win = fair coin exists. (2) vwap_reversion has SKEW +2.97 (strongly positive, what we wanted) but only 27% win -> frequency problem not tail problem (my "tail eats it" prediction WRONG — tail is its asset).
- MY PREDICTION SCORED: bet time_scalp wins — WRONG (all 0). But diagnosis salvageable: entry logic fine, EXIT/TARGET sizing wrong.

## FIX HYPOTHESIS (next): WIDEN TARGETS so friction becomes small % of trade (target 15-25 ticks not 3-8). Keep time_scalp's ~50% win with a wider target -> RR>1 after costs. Separately try to lift vwap_reversion hit-rate while keeping +skew. This is a target/exit REGIME fix, NOT re-picking strategies. Still no param-overfitting: sweep target size in a small principled grid + hold-out test.
## CAUTION: widening targets LOWERS win-rate (further to go). Real question: does win-rate*avg_win beat friction+losses at ANY target? If NO target regime clears friction on MES, index-futures scalping is structurally friction-dead and we reconsider instrument (ES bigger $/pt dilutes friction%) or approach.

## MILESTONE 4 — Filters + Swing, BOTH DEAD. Pattern identified, strategy-hunting on generic TA HALTED.
- Filters (vol/time-of-day/trend-align) on vwap_reversion+trend_pullback: best case (vwap+trend_align) EV $296.84 aggregate BUT all 4 walk-forward buckets negative (-29.55/-16.32/-4.15/-6.75). Filters cannot fix a no-edge entry, only trim noise. DEAD.
- SwingTrendModel (ES, 20d breakout, 2.5R): CATASTROPHIC sizing bug — avg risk $4,414/max $6,603 vs $2,000 MLL / $325 buffer (single ES contract = 2-3x whole account risk budget). fail_died_mll=74.82%. ROOT CAUSE PINPOINTED (not guesswork): wrong instrument size, same class of bug as MNQ-scalping error earlier. Fix = MES (1/10 $/pt) -> risk ~$440-660, in-budget.
- BUT underlying ceiling even with fix: only 16 holdout trades, win-rate swung 0%/0%/16.7%/75% by bucket = STATISTICALLY MEANINGLESS regardless of sizing. 2yr of data cannot validate a multi-day swing strategy. Would need many more years (=more paid data) to even test properly.
- UNRESOLVED FACT (flagged per memory-hygiene rule): overnight-hold permission on LucidFlex was NEVER actually confirmed — I only logged the scalper's 4:45pm flatten DEFAULT, which got misread as "overnight allowed." Blocks ANY swing/overnight strategy until verified directly with Lucid (cheap, same channel as API question).

## PATTERN FINDING (5th consecutive confirmation): funding carry, funding spread, liquidation cascade, AND now 4 generic TA entries (VWAP reversion, trend-pullback, ORB, daily breakout) on ES/MES ALL show no edge or mild NEGATIVE edge after cost. Win rates cluster 42-50%, consistently JUST UNDER fair coin, not randomly scattered -> fingerprint of a crowded/faded pattern, not neutral noise. CONCLUSION: generic textbook TA on the most efficient competed market (S&P futures) has no free edge left in 2026. STOPPING blind entry-variant hunting per no-hallucination-loop rule. Real strategic decision needed from X: pivot to (a) codifying X's OWN real discretionary edge (the one that earned $8k before blowing the account) instead of hunting generic patterns, (b) resolve overnight permission + retry swing at correct MES size as ONE last precise test (not a guess-loop), (c) accept more years of paid data needed before further swing testing, or (d) reconsider instrument/market entirely.

## CYCLE UPDATE — "Fabio Valentini IVB Model" PDF received, VERIFIED as marketing not institutional research
- Web search confirms: Fabio Valentini / "matfino" / "fabervaale" = retail trading-education personality (TikTok "Chart Fanatics", YouTube, Telegram @fabervaaleEng, "Deep Charge Boot Camp", sells indicators/courses). The PDF's "Institutional Protocol / CONFIDENTIAL / Matteo Conti independent validation" framing is marketing theater, NOT a real internal desk memo. LESSON: always verify unfamiliar entities/brands before trusting a document's self-description, exactly like the price-level check.
- TECHNICAL CRITIQUE (why we don't trust it as proof, precise): (1) self-contradiction: stamped "VALIDATED/DEPLOYABLE" while its own "Next Checks Before Capital" lists walk-forward/slippage-stress/regime-decomposition as NOT yet done. (2) Their bootstrap only tests "is THIS trade log's mean != 0", NOT parameter-selection overfitting (no PBO/CPCV disclosed, no count of configs tried before landing on DeltaThreshold=200/ORB_Dur=30). (3) "Independent validation" admits (own limitations section) NO independent re-execution on raw data was performed — trusted a vendor-supplied trade log. (4) Requires tick-level bid/ask delta data (Upticks-Downticks), not the cheap OHLCV tier we've been using. (5) Full-size NQ 1-contract doesn't fit Lucid $50k FLEX limits/buffer without rescaling to MNQ (same class of issue as ES->MES earlier).
- NOT dismissed outright: volume-delta/order-flow confirmation on ORB is a legitimate, different technique class from the vanilla ORB we already killed (that had zero confirmation filter). Worth an honest independent re-test.
- PLAN (2-phase, cost-gated, X approved both): Phase A = free/cheap approximation (candle-based delta proxy from OHLCV, standard known technique) on NEWLY cost-quoted MNQ 1m data (not full NQ), ported EXACTLY from the EasyLanguage spec, through OUR funnel (train/holdout/walk-forward/DSR-PBO-battery), no param retuning. Phase B = cost-quote ONLY (no pull) for real tick/MBO data, so if Phase A is promising we know the real price before spending further.
- STANDING RULE REINFORCED: no new data pull without a cost-quote + explicit go-ahead first (card-charge caution).

## MILESTONE 5 — NULL-ENTRY TEST: risk-engine-only thesis FALSIFIED. ROOT CAUSE ISOLATED.
- True random 50/50 coin, MES, 20-tick stop/target, real MES commission+slippage, 20 seeds, full funnel:
  median pass_rate=2.835% (WORST of 20 seeds=2.27%, BEST=7.58%) vs breakeven 3.9616%. Median EV=-$28.15.
  Gap vs earlier SYNTHETIC 52%/1:1 result (27.32% pass) = -24.49 percentage points. HUGE gap.
- ROOT CAUSE (mechanical, not entry-skill): win nets $24.00 (target fill clean, only commission drag);
  loss nets -$27.25 (commission + STOP-FILL ADVERSE SLIPPAGE + gap-through risk). At literal 50/50, this
  alone = -$1.625 EV/trade BEFORE any entry logic. This is the unifying mechanism behind ALL 6 prior dead
  strategies this session (every one showed avg_loss > avg_win at nominal ~1:1 setups) — finally isolated
  and proven in isolation, not confounded with entry quality.
- REFRAMES the risk-engine thesis correctly (not a contradiction): risk control prevents RUIN, cannot
  manufacture edge from a structurally negative fill mechanism. "Coin flip + good risk control = profit"
  is FALSE. Real edge clearing the stop-slippage tax is mandatory, not optional.
- NEXT (in flight, offline/free): sensitivity sweep on stop-slippage (0/1/2 ticks) + stop-limit vs
  stop-market order-type comparison (honest, including stop-limit's unfilled-order downside). Decides:
  is this a fixable EXECUTION problem (free lever) or a fundamental wall requiring real info-edge (Path 2,
  costs $591-1532+ for tick/MBO data per Phase B quote)?
- IF even 0-tick idealized fills still fail breakeven -> fill mechanics were never the constraint, go
  straight to Path 2 (real info edge, real budget). IF gap closes substantially at 0-1 tick -> better
  execution (stop-limit / working orders) is a free structural fix worth building first.

## SCOREBOARD: 7 tests run this session (carry, spread, cascade, 3 TA entries+filters, swing, Fabio
  ORB+delta, null-entry-mechanics). ALL confirm: no free lunch in generic retail-accessible entries on
  liquid futures in 2026, AND stop-order fill mechanics carry a real structural tax that must be cleared
  by genuine edge. $0 lost testing all of this — exactly what the funnel discipline is for.

## CYCLE UPDATE — ATAS killed (verified), Sierra Chart chosen, POC-first workflow
- ATAS DEAD: confirmed dxFeed connection explicitly does NOT support Delta/Order-Flow/Cumulative-Trades
  candle types (unsupported list, official docs). No bulk export exists (chart-by-chart CSV or custom
  C# indicator only, undocumented feed limits). Harvest-then-cancel trial plan ABANDONED correctly before
  wasting a week -- the exact signal needed isn't reliably exportable on this platform regardless of trial depth.
- DECISION: Sierra Chart Package 3, $26/month RECURRING (first ongoing cost in project, X's own time also
  spent). Confirmed (prior cycle): 18+ months history, real Bid/Ask trade volume, CSV export supported.
- DISCIPLINE APPLIED TO MANUAL LABOR (not just money): do NOT scale to 4 instruments x 18-24mo immediately.
  PROOF-OF-CONCEPT FIRST: export ONE month of NQ only, verify CSV has real separate bid_volume/ask_volume
  columns (not just total volume) and the export process is tolerable. Only then scale to full history x
  4 instruments (ES/MES/NQ/MNQ).
- BUILT: sierra_csv_loader.py -- ingests Sierra CSV into Heimdall's standard schema (ts/open/high/low/close/
  volume/bid_volume/ask_volume/delta=ask-bid), matching Databento pipeline's schema so downstream funnel/
  battery code is source-agnostic. HARD VALIDATION built in: raises if bid_volume/ask_volume columns are
  missing (POC failure = do not scale), and prints bid+ask-vs-total-volume reconciliation sanity check
  (large mismatch = export unreliable, do not trust). COLMAP in the script must be adjusted to match X's
  ACTUAL Sierra export header -- do not assume column names, verify against the real file.
- FALLBACK if Sierra POC fails or manual labor proves too costly: Databento `trades` schema, $237.26 for
  NQ 2yr (confirmed cost via get_cost), reproducible API, zero manual labor, already-proven pipeline.

## CYCLE UPDATE — ICT pivot: Dhesi Inversion Model codification (X-directed)
- X directed pivot to codifying the Dhesi Trades ICT "Inversion Model" (Chart Fanatics video UIGZtoGGPH4).
  NOTED: same Chart Fanatics ecosystem as the Fabio marketing PDF; payout claims ($2M/$900K Apex) unverifiable.
  Doesn't matter for testing — the funnel decides, not the video.
- Manus transcript extraction delivered a clean rule sheet: 4-step sequence (liquidity sweep -> HTF 4H/1H
  FVG inversion -> 15m retracement into iFVG -> LTF 5m/1m FVG inversion = entry), structure stop, TP1 at
  nearest liquidity (~1.5-2R, trim 50% + BE), runners to major pools (1:5-1:10R), no trades before 10:00 ET,
  2-loss daily stop, one entry/session, vol-expansion filter.
- KEY ADVANTAGE: pure price action — needs ONLY existing OHLCV parquets (MNQ/MES/ES). Zero new data cost.
- SIERRA CHART: PAUSED (my call, X delegated). No delta data needed for ICT. Resume only if we return to
  order-flow after this test. No $26/mo clock started.
- DISCRETION HANDLING: "cleanest timeframe" and "market expanding" feel-calls get PRE-REGISTERED mechanical
  proxies (1H fallback if no 4H FVG; ATR-vs-median filter). Testing the MECHANICAL version of his model —
  if it fails, verdict is "codifiable part has no edge," not "trader is fake." No tuning allowed.
- WORK ORDER ISSUED: InversionModel through full funnel, 3 instruments, buffer 325, standard friction,
  walk-forward + MC, discretion-gap list required. Offline, zero cost.

## CYCLE UPDATE — InversionModel v1: FAIL on FREQUENCY, not edge. Different failure species.
- Holdout n=2-6 trades/instrument vs 30 min gate; MC 0% (never_target 100% — too few trades to climb).
- BUT per-trade geometry is the BEST of all 8 tests: skew +0.53..+1.16 (positive, every split), RR 2.0-5.0,
  runner contribution 67-91% (matches Dhesi's claimed profile), MNQ holdout 50% win / RR 2.19 / +$82 mean.
  Sample far too small to trust ANY of it — but shape is right for the first time.
- DIAGNOSIS: 4 sequential AND-conditions with strict pre-registered thresholds multiply to ~7 trades/yr
  vs Dhesi trading ~weekly. Either my codification is over-strict (likely links: sweep close-back-in-3-bars;
  FULL close through HTF FVG; 5m FVG during-retracement + zone-overlap) OR the real frequency lives in his
  discretion. Cannot distinguish from n=14.
- DISCIPLINE HELD: refused threshold-loosening loop (banned tuning). Issued MEASUREMENT-ONLY work order:
  condition-funnel diagnostic counting session survival step0->4 on MNQ, incl. near-miss distribution at
  the 3->4 link. Output = named bottleneck -> X makes ONE deliberate pre-registered revision (or none).
  Not a tuning knob.
- Agent process note: one non-compliant broad pytest hit OKX timeout (no pull, no charge); rerun offline.

## CYCLE UPDATE — funnel diagnostic result + STRATEGIC REFRAME to PORTFOLIO
- Diagnostic (MNQ, 515 RTH sessions): ATR filter (MY proxy, NOT Dhesi's rule) kills 52.6% of sessions
  (515->244) before the model starts = biggest single choke. His actual chain: sweep 96% -> HTF inversion
  44% -> 15m retrace 42% -> entry 45% => 20 entries/2yr full-period (14 was train-split only).
  Near-misses at 3->4: 9 overlap-never-inverted, 8 no-zone-overlap, 6 no-5m-FVG, 1 no-stop-swing.
- ONE pre-registered revision authorized (correcting MY over-reach, not tuning HIS rules): remove
  session-ATR proxy, replace with his actual per-setup displacement filter (>=30 NQ pts). Rerun issued.
- BRUTAL MATH LOGGED: even ~40 trades/2yr (~1.7/mo) CANNOT pass a Lucid eval alone (needs 5 x $150 profit
  days). Single sparse strategy != eval-passable regardless of edge.
- X frustration addressed with facts: 8/8 "publicly working" strategies implemented + killed by funnel =
  the system working, not looping. X's "trade when strategies align" idea corrected: AND/confluence
  multiplies sparsity (the diagnosed disease); correct structure = OR-PORTFOLIO of independently
  funnel-passed strategies, risk engine managing combined book. 5 strategies x 20 tr/yr = 100 tr/yr =
  eval becomes passable. This is what the alpha-factory architecture was built for. STRATEGIC DIRECTION SET.
- 3 new YouTube strategy videos from X (EZ_L7zovyrw, 52ZsDmFHqyY, jsUTbjwpFVk): Manus extraction prompt
  issued (same Dhesi-format rule sheets). Pipeline now repeatable ~1 day/strategy: transcript -> rule sheet
  -> AlphaModel -> funnel -> portfolio if passed.

## CYCLE UPDATE — InversionModel v2 result + 3 new rule sheets triaged
- InversionModel v2 (ATR proxy removed, 30-pt displacement filter): MNQ holdout 13 trades (was 6), 38.46%
  win, RR 2.05, skew +0.79, mean +$26.31/trade, walk-forward 3/4 buckets green (+98/-28/+59/-10). Geometry
  HELD after the fix. Still min_trades fail (13<30), MC ~0% — CONFIRMED PORTFOLIO CANDIDATE #1, unvalidated,
  cannot pass eval alone. SPEC BUG noted (not chasing): 30 RAW points applied unscaled to ES/MES (~30 NQ pts
  ≈ 7-8 ES pts) -> ES/MES died to 0-4 trades. MNQ is this model's market anyway.
- 3 Chart Fanatics rule sheets triaged:
  * OKALA 80/20 (NQ): BUILD NOW. Most mechanical spec received all session — fixed 10pt stop/15pt TP1 +
    runner, 80/20 price levels, 3 patterns, NY-open session, daily-scale frequency (what the portfolio
    needs), runs on owned MNQ 1m data. Work order issued (setups A/B/C, pre-registered proxies, per-setup
    attribution; C dropped if not mechanizable without invention).
  * CRUDELE Bollinger (ES daily): PARTIAL — MR + expansion price-rules codifiable on daily bars, but his
    real edge wrapper is OPTIONS risk-definition + macro discretion + "friend Pax" targets. Queue skeleton
    test AFTER Okala. Low expectation, near-zero cost, daily-frequency sparse ceiling known.
  * DUX small-cap shorts: REJECT for Heimdall — wrong market (small-cap equities), needs unowned data
    (float/premarket/mktcap), needs shorting locates, and CANNOT trade on a CME-only Lucid account at all.
    Parked, not judged.
- PORTFOLIO STATE: candidate #1 = InversionModel-MNQ (sparse, positive). Awaiting Okala (frequency donor).
- Friction check for Okala pre-registered: 10pt MNQ stop = $20 risk; ~$3.50 RT friction = 17% of risk —
  tight but ~5x better than the dead 3-6 tick scalps. TP1 15pt = $30 gross. Watch realized RR after slippage.

## CYCLE UPDATE — Okala v1 zero-trade fail (MY encoding), data-theory addressed, 3 new sheets triaged
- X's theory "strategies fail because data isn't real/offline" = WRONG and corrected: Databento GLBX.MDP3 IS
  the real CME feed; everything died on real prices + real costs. The ONE genuinely missing data class =
  order-flow granularity (bid/ask delta/footprint). Cheapest verified source remains Sierra Chart $26/mo
  (loader already built: tools/sierra_csv_loader.py). "Pay for real data" = $26, not $591-1532 tick tier.
- OKALA v1: 0 trades. Funnel diagnostic pinpoints MY over-literal encoding: "fails to touch" = exactly
  one tick short -> only 16 qualifying candles/2yr (10,328 strong moves upstream). Same error class as the
  Dhesi ATR proxy. ONE pre-registered revision authorized: fails-to-touch = wick 1-10 ticks short; B zone
  touch = within 2 ticks. ONE run. If still ~zero or geometry garbage -> Okala edge lives in his eyes, DEAD,
  no third attempt.
- NEW SHEETS: Verma small-cap shorts REJECT (wrong market, can't trade on CME-only Lucid — 2nd small-cap
  sheet, same structural verdict; stop collecting these). Patrick Nill REJECT (Manus itself: zero codifiable
  rules). ORDER FLOW NQ (absorption/aggression) = REAL CANDIDATE: "absorption" mechanically = high aggressive
  delta at key level + low price result, then opposite initiative — computable from Sierra bid/ask volume.
  This is where the data spend lands.
- SCOREBOARD stated to X: ~$11 data spent, 10 strategies killed pre-money, machine (engine/funnel/pipeline)
  proven; weak link = YouTube source material (vibes-or-edge-free, 10/10). Live threads: Dhesi (positive,
  sparse) + order-flow (needs $26 Sierra).

## CYCLE UPDATE — OKALA DEAD (pre-committed kill, both revisions exhausted)
- Revision 2 (wick-miss 1-10 ticks, zone-touch within 2 ticks): STILL 0 trades. A: 110 wick-misses -> 0
  second-candle confirmations (chain dies one link later). B: 16 zones -> 0 touches. Verdict rule triggered
  (holdout 0 < 30). NO third run — discipline held.
- LESSON (now 2x confirmed on Okala alone): the two-candle precise sequence at exact 80/20 levels on 200s
  bars essentially NEVER occurs mechanically. If his edge is real, it lives in discretionary chart-reading,
  not in the literal words. Same terminal conclusion as Fabio: video language does not contain the system.
- SCOREBOARD: 11 strategies dead (carry, spread, cascade, vwap-rev, trend-pullback, time-scalp, swing,
  Fabio ORB+delta, null-entry, Okala v1, Okala v2). LIVE: Dhesi InversionModel-MNQ (portfolio candidate #1,
  sparse, +$26/trade holdout). IN FLIGHT: Sierra $26 POC -> absorption diagnostic (order-flow thread).
- PROCESS FIX (2nd miss): memory file must be PRESENTED to X in the same action as every update, before any
  analysis text. No exceptions.

## CYCLE UPDATE — Jev research triage integrated (Windows migration follow-up)
- VERIFIED source: TypeSafe System One docs (`https://docs.typesafe.ai/llms.txt`,
  `https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md`). Jev provides typed Choice/Score/Noul
  judgments with probabilities; code must compose results and route uncertainty.
- IMPLEMENTED: `meta/jev_strategy_triage.py` + `tools/jev_triage_strategies.py`. Local Markdown collections
  are split into individual `## Rule Sheet` candidates before Jev evaluates codifiability, target-market fit,
  and whether currently listed data can test the defining signal.
- HARD BOUNDARY: Jev is advisory research tooling in `/meta` only. It may NOT emit/approve trade signals,
  place orders, change risk limits, or count as backtest evidence. Every result requires human review followed
  by deterministic implementation and the existing holdout/walk-forward funnel.
- LIVE PROOF: Jev `jev-1.13.0` successfully answered a bounded HEIMDALL routing request. It selected the Sierra
  NQ absorption POC as the next research track (0.99 selection confidence), judged order-flow data necessary
  (noul 0.95), and rejected direct Jev execution/risk use (safe-to-execute noul 0.03).
- VERIFICATION: core purity OK; 51 non-legacy tests pass, including 4 offline Jev boundary/parser tests.
- NEXT ACTION UNCHANGED: Sierra one-month NQ bid/ask-volume CSV POC. No broker adapter and no live order path
  until a strategy clears deterministic validation.

## CYCLE UPDATE — Sierra POC PASSED, bounded archive complete, wallet replay foundation built
- PAID ACTION VERIFIED: Sierra Chart Package 3 was activated for USD 26. No upgrade, exchange package, or
  second paid data source was purchased. Official capability sources:
  `https://www.sierrachart.com/index.php?file=doc/Packages.php`,
  `https://www.sierrachart.com/index.php?page=doc/SierraChartHistoricalData.php`, and
  `https://www.sierrachart.com/index.php?l=doc/ContinuousFuturesContractCharts.html`.
- POC VERDICT: PASS. NQ 30-day continuous one-minute export produced 28,156 rows with real `BidVolume` and
  `AskVolume`; bid+ask versus total-volume mismatch over 5% was 0.00%. The Sierra order-flow roadblock is
  removed for bar-level absorption/aggression research. Package 3 does NOT provide MBO/order-book queue
  history, so MBO-dependent claims remain out of scope.
- ARCHIVE COMPLETED: validated 90-day, one-minute, volume-roll, non-back-adjusted continuous exports for
  NQ/MNQ/ES/MES/GC/MGC/CL/MCL/RTY/M2K/YM/MYM. Each normalized parquet has UTC index plus
  open/high/low/close/volume/bid_volume/ask_volume/delta, zero duplicate timestamps, zero NaNs, and 0.00%
  material bid+ask reconciliation mismatch. Exact rows, ranges, filenames, caveats, and raw SHA-256 values
  are recorded in `data/sierra/MANIFEST.md`; do not redownload or re-derive them.
- CRYPTO ARCHIVE: Deribit BTC perpetual is the canonical free Sierra comparison feed (123,241 rows through
  2026-09-21 15:23 UTC). BitMEX is comparison-only because its export ended 2026-09-16 and contains many
  missing minutes. Sierra crypto is venue trade data, NOT wallet/on-chain data.
- LOADER CORRECTED AND TESTED: `tools/sierra_csv_loader.py` now maps Sierra's observed `Last` column to
  `close`, tolerates header spaces, defaults the verified chart time zone to UTC, fails closed without real
  bid/ask fields, and emits only the eight-column normalized schema.
- WALLET COPY FOUNDATION (READ-ONLY/OFFLINE): `meta/wallet_copy/` now provides immutable validated EVM
  observations, canonical append-only JSONL recording, monotonic-time and duplicate guards, and deterministic
  replay metrics for observation latency and adverse price drift. It contains no RPC, signing, key, approval,
  or order path. Public post-trade feeds cannot guarantee copying a target in the same block; never claim they can.
- JEV VERDICT APPLIED: prioritize core index order flow; gold/energy/secondary indices and crypto are archive
  support, not simultaneous strategy launches. Jev remains advisory in `/meta` and cannot affect money paths.
- NEXT ACTION: pre-register ONE bar-level NQ/MNQ absorption detector before looking at outcome statistics,
  then implement and run untouched holdout + walk-forward validation. In parallel, the next wallet slice is a
  read-only Robinhood Chain feed adapter only after a provider cost quote and exact chain/router/wallet inputs.
  No broker adapter, signing, live order, or new paid service is authorized.

## CYCLE UPDATE — Order-flow absorption v1 DEAD on frequency; no tuning loop
- PRE-REGISTRATION FROZEN BEFORE OUTCOMES: `ORDERFLOW_ABSORPTION_PREREGISTRATION.md`, SHA-256
  `86943C07589D8A06C420FC6FD61215FC2B26D8AC86A9C994E58F4CDFEFB6B525`. Fixed rules: prior-session
  68% close-bucket value area, trailing 20-session effort baselines, 90th-percentile signed delta absorption,
  median-or-smaller range, opposite 75th-percentile aggression within 3 minutes, one MNQ contract, 2R target,
  breakeven after 1R, exact stop/entry/flatten slippage. Zero threshold sweeps.
- IMPLEMENTED: `core/alpha/orderflow_absorption.py`, unit-tested with no free strategy parameters and no
  `/meta` dependency. Validation used only `data/sierra/MNQ_continuous_1m_latest_90d.parquet`; no network.
- V1 RESULT: 0 train trades, 0 holdout trades, 0/4 positive walk-forward buckets, validation gate failed
  `min_trades`, Lucid Monte Carlo 0% pass / 100% never-target. VERDICT: v1 DEAD. This is a frequency failure,
  not evidence of negative or positive expectancy.
- EXACT CONDITION FUNNEL (44 eligible sessions): near level 12,064 events/43 sessions -> close rejection
  393/25 -> signed 90th-percentile effort 14/9 -> full low-result absorption 1/1 -> opposite 75th-percentile
  aggression within 3 bars 0. The main choke is the joint high-effort/low-result bar; the sole survivor had no
  confirmation. Do NOT loosen these thresholds or retry v1.
- INTERPRETATION: one-minute bar delta cannot faithfully reproduce the source's price-level footprint bubbles.
  A materially different v2 requires actual tick/price-level volume evidence and a new pre-registration, not a
  threshold edit. The acquired bar archive remains valid for other bar-level order-flow hypotheses.

## CYCLE UPDATE — Sierra tick archive secured; footprint absorption v2 DEAD
- SIERRA ONE-TICK DATA SECURED with no additional purchase: NQM26 34,259,267 records, NQU26 30,910,522,
  NQZ26 2,602,500 (67,772,289 total). Raw `.scid` files are copied under `data/sierra/tick_raw/`; full
  Parquets and 1-minute price-level footprints are under `data/sierra/tick/`. Exact ranges, byte counts,
  SHA-256 hashes, roll construction, and caveats are in `data/sierra/MANIFEST.md`.
- OFFICIAL FORMAT SOURCE: https://www.sierrachart.com/index.php?page=doc/IntradayDataFileFormat.html .
  `tools/sierra_scid_loader.py` validates the 56-byte header / 40-byte record layout and streams to Parquet.
  All records have `num_trades==1` and exact bid+ask volume reconciliation. NQU contains two retained,
  documented backward timestamp jumps. Never silently drop them.
- QUOTE CAVEAT: 16.34%-20.33% of records have trade price outside SCID high/low, despite those fields being
  documented as ask/bid for one-tick records. Therefore high/low quote fields are FORBIDDEN for research;
  only trade price (`close`) and exchange-classified bid/ask volumes are trusted.
- CONTINUOUS FOOTPRINT: 3,850,741 unique minute/price cells across 146 RTH sessions. Prior-session-volume
  roll switches NQM->NQU on 2026-06-16 and NQU->NQZ on 2026-09-15, never backward.
- V2 PRE-REGISTRATION frozen before outcomes: `ORDERFLOW_FOOTPRINT_PREREGISTRATION.md`, SHA-256
  `2ECBAB429D8B4D9B24C83C48F049EBE84DC50E4582C1E13B0A8F4F07DF49A1EA`. Zero threshold sweeps.
- V2 RESULT: 126 eligible sessions, 0 candidate bars, 0 trades, 0/4 positive walk-forward buckets,
  Lucid pass 0%. VERDICT: v2 DEAD on frequency; it says nothing about expectancy.
- EXACT V2 FUNNEL: level touch 36,297 -> close rejected one tick inside 1,066 -> extreme aggressor >=20
  contracts 28 -> >=3:1 imbalance 27 -> >=20% same-minute aggressor concentration 0. The fixed 20%
  concentration rule is the terminal choke. Do NOT loosen it or retry v2.
- ORDER-FLOW ABSORPTION THREAD IS CLOSED after two independent frozen failures (bar proxy and true
  price-level footprint). Move to a materially different pre-registered strategy family; no rescue tuning.

## CYCLE UPDATE — Initiative continuation v3 FAILED untouched holdout
- USER REQUESTED a profitable change to the absorption strategy. The premise is corrected: profitability
  cannot be forced by tuning. The research-supported material change tested the opposite claim—aggressive
  order flow with high price result continues briefly—rather than weakening dead absorption thresholds.
- SOURCES: local Rule Sheet 2 aggression/initiative definition; Kurov & Lasser (JFE 2007),
  https://doi.org/10.1016/j.jfineco.2006.05.010; Jin et al. (IJFE),
  https://doi.org/10.1002/ijfe.2439. Both support short-run order-flow/price linkage, not guaranteed net edge.
- PRE-REGISTRATION frozen before returns: `ORDERFLOW_INITIATIVE_PREREGISTRATION.md`, SHA-256
  `3487645460510C3C770D2E9CE27156D7605D6135A60C8F41D71C4855C91D335E`. Development ended
  2026-06-15; untouched NQU/NQZ holdout began 2026-06-16. Zero threshold sweeps.
- FUNNEL: 126 eligible sessions -> 80 initiative bars -> 64 confirmations -> 64 entries.
- DEVELOPMENT looked promising: 36 trades, 55.56% wins, +$9.50/trade, +$342 total, RR 1.143.
- UNTOUCHED HOLDOUT FAILED: 28 trades (below 30 minimum), 39.29% wins, -$12.68/trade, -$355 total,
  RR 0.962, only 1/4 walk-forward buckets positive. Lucid Monte Carlo 0% pass / 100% never-target.
- VERDICT: v3 DEAD. This is the exact overfitting/regime failure the firewall exists to catch. Do not tune,
  loosen, or retry v3. Apparent in-sample profitability is not edge.
- TECHNICAL RESEARCH SHORTLIST saved in `HEIMDALL_TECHNICAL_RESEARCH.md`. Highest-fit utilities:
  Polars/DuckDB for 67.8M-tick analytics; `orderflow-metrics` as an audited formula reference; skfolio for
  later checker-side purged CV. Sierra DTC/NautilusTrader are execution-architecture candidates only after
  broker permission. `async_rithmic` is blocked on Lucid R|Protocol confirmation and requires independent
  audit. hftbacktest is rejected with current trade-only data because queue/L2 simulation would be false precision.

## CYCLE UPDATE — 2026-09-22: LuxAlgo POC + YouTube FVG REJECTED; value-area test blocked at fidelity gate
- Consolidated report: `STRATEGY_RESEARCH_2026-09-22.md`. Artifacts: `data/strategy_research/validation_2026-09-22.json`,
  both `*_trades.csv`, `va_proxy_fidelity_2026-09-22.json`, `next_experiment_triage_2026-09-22.json`.
- LUXALGO POC SWEEP RECLAIM (prereg SHA-256 `22EF522402B15653742977C8B426A8044CE7BC4AA4B2EB3BEFB423201F9B33FE`):
  MNQ_1m, 515 sessions 60/40. Train 307 tr, 29.97% win, -$8.46/tr. Holdout 205 tr, 37.56%, -$5.20/tr, -$1,065.50,
  skew -0.53, all 4 buckets negative, gate fail (dsr/nw_t/boot_lo/wf_min), Lucid MC 0.00% pass. REJECTED. Its
  close-volume "POC" matched true Sierra footprint POC in 2.70% of 4,857 five-minute bars (median 21 ticks off);
  minute alignment 98.38% of 24,343 bars, so not a timestamp artifact. Never call that proxy a POC.
- CASPER OPENING-FVG SCALP (prereg SHA-256 `6A074F0ECEF0E8DB413F1534ADAEB590467AB4752055EFEB8792A9246197F56D`):
  Train 107 tr, 38.32%, +$26.79/tr. Holdout 67 tr, 28.36%, +$0.46/tr (+$31), 2/4 buckets positive, gate fail,
  Lucid MC 0.64% pass vs 3.96% breakeven. REJECTED. Do not tune FVG/engulf/window/stop/target.
- Other 4 videos (TradingLab, Casper day variant, JackTrades PO3, Trader Mayne, Mulham) = NOT FAITHFULLY TESTABLE
  from available rules — not "failed". JackTrades overlaps Dhesi.
- Implementation reviewed against both preregs: entry slipped once, stop +1 adverse tick, commission once, MC gets
  net PnL, stop wins same bar, chronological session split, no lookahead. No defect; results stand.
- NEXT EXPERIMENT chosen (Jev advisory: va_reacceptance 0.80 selection conf, but codifiability conf only 0.39):
  prior-session value-area re-acceptance (Dalton 80% rule). Prereg `VA_REACCEPTANCE_PREREGISTRATION.md`, SHA-256
  `5CD7D937D007D51C235E6EF48301E9E4144C06B15F797ED98CFCE84404EF1949`. Stage 1 (levels only, no outcomes):
  one-minute close-volume 70% VA vs true footprint VA, both edges within 4 ticks in only 0.68% of 146 sessions
  (median err VAH 143 / VAL 197.5 ticks; true width median 790). FAIL -> Stage 2 NOT run, per frozen rule.
  Status = BLOCKED BY MISSING DATA (needs multi-year trade-level NQ/MNQ), NOT rejected. Do not rerun Stage 1 at
  coarser buckets or run Stage 2 on the proxy — that is a new hypothesis. Shared helper `core/alpha/value_area.py`
  (+ tests/test_value_area.py, 4 tests).
- HOLDOUT REUSE: MNQ two-year holdout read by 3 experiments (Dhesi, POC, FVG); footprint holdout by 1 (v3).
- VERIFIED 2026-09-22: full pytest `2 failed, 84 passed` (only accepted OKX-timeout files); core purity OK.
  hftbacktest 2.4.4 has a cp314 win_amd64 wheel (venv is Python 3.14.3).

## CYCLE UPDATE — 2026-09-22/23: VALIDATION TRUST AUDIT (separate lane) -> TRUSTED WITH LIMITATIONS
- Full report: `VALIDATION_AUDIT_2026-09-22.md`; outputs `data/validation_audit/*.json`; tests
  `tests/test_audit_{pnl_oracle,stat_references,invariants_prop}.py` (104 new, all pass). No threshold, gate,
  simulator or strategy file changed. Full pytest 198 passed / 2 failed (known OKX-timeout files); purity OK.
- VERIFIED CLEAN: shared RTH simulator == hand oracle (14 fixtures + 40 random paths, exact); point values,
  commission-once, no MC double-charge; PSR/DSR formulas; NW t == statsmodels HAC; DST; chronological split.
- REFINES "Battery proven ... TRUSTWORTHY": it is a reliable REJECTOR (null accept <= 4.8% in every cell) and a
  WEAK DETECTOR. Conv. A power: SR0.10 (~55%/1:1) accepted 6-9% at 30-100 trades, 14% at 200; SR0.20 7-27% at
  30-100, 51% at 200; N<30 = 0%. Most binding gate N=30-200 = wf_min (all 5 sub-period Sharpes > 0).
- DEFECT D1: validate_research_candidates passes sr_trials_var=1.0 (per-trade units -> SR0 0.52/trade) ->
  ~0% acceptance at any edge/N. LuxAlgo/FVG verdicts unchanged (gross edge ~0). Conv. A (nb=1) = NO deflation
  despite ~20+ strategies reusing the MNQ holdout (false-positive side).
- DEFECT D2: prop MC is 1 contract / 80 days. "Lucid MC 0% / 100% never_target" = PROP verdict at 1 lot, NOT alpha.
  Demo: +$10/trade edge -> 0% at 1 lot, >50% at 5 lots. Lucid MLL lock level, eval time limit, and whether
  target-before-5-days ends the eval are UNRESOLVED (sim treats it as terminal fail).
- DEFECT D3: LuxAlgo POC ran on 5m bars with stop-first: 65/205 holdout stop exits ambiguous. Holdout mean
  worst -5.20 / 1m+tick-resolved -2.24 / best +2.08 -> LESS NEGATIVE, STILL REJECTED.
- DEFECT D4 (strategy): Dhesi v2 stop from last 15m swing w/o side check: 5/30 MNQ trades wrong-side stop
  (1 in holdout). v3 stop_guard already fixes. v2 needs a LABELLED rerun, do not overwrite.
- RECLASSIFIED (frozen logs, no rerun): Dhesi v2 = INCONCLUSIVE (13 tr, 95% CI [-135,+188]; "positive
  candidate" is as unsupported as "dead"). Initiative v3 = INCONCLUSIVE (28 tr, CI [-37,+12] contains dev
  +9.50). VWAP rev, time scalp, Casper FVG = UNCHANGED: every one had ~0 GROSS edge; execution tax
  $1.8-3.2/trade is not what killed them.
- Gate-level: sign-flip MC / iid bootstrap / DSR(nb=1) run 6-19% FPR standalone under neg skew or AR(1) 0.3;
  PBO never computed (no candidate matrix); spec bootstrap lo>1.0 vs code lo>0.0 = UNRESOLVED owner decision.
- NEXT (P0, V13 rules apply): 3-axis verdicts ALPHA/EXECUTION/PROP + INCONCLUSIVE when N < power-required N;
  trials ledger + empirical sr_trials_var replacing conv. A and B; prop MC pass-rate vs contract count.

## CYCLE UPDATE — 2026-09-23: Profit-discovery program (S0–S2 partial) — STATUS CHECKPOINT, WINNER NONE
Full report: `PROFIT_DISCOVERY_2026-09-23.md`. Scripts + datasets: `workspace/profit_discovery_2026-09-23/`
(`fomopulse_tape.parquet` 212,859 fills, `copy_sim_results.parquet`, `rht_*`, harness scripts). Pool logs and GeckoTerminal
candles were still downloading at session end (session scratchpad `logs/`, `ohlcv/`) — copy them in and rerun.
- RECONCILIATION: intraday momentum (INTRADAY_MOMENTUM_PREREGISTRATION.md) was run 2026-09-22 and FAILED — MNQ train
  296 tr -$15.84/tr, holdout 198 tr -$11.65/tr (NWt -1.65, 0/4 buckets >=0), fresh MNQ +$12.80/tr but ES/MES/M2K/MYM negative.
  DEAD. A "fade r_ROD" variant is CONTAMINATED (discovered from this data) and already contradicted by the fresh MNQ window.
- CORRECTIONS to HEIMDALL_WALLET_COPY_AUDIT_REPORT.md (2026-09-22): its §6 follower grid is a SYNTHETIC model, not
  verified data; its 115 ms p50 end-to-end latency was never measured; rhtrenches has NO pagination (API caps 400 closed /
  500 tape); FomoPulse PnL is AVERAGE-COST, not FIFO; FomoPulse history starts 2026-09-05, not July.
- MEASURED (this Dubai host, 2026-09-23): sequencer feed `wss://feed.mainnet.chain.robinhood.com` needs permessage-deflate;
  delivers already-sequenced blocks (feed seq = L2 block + 2), ~10 blocks/s (p50 101 ms apart). Public RPC head lags feed
  p50 455 / p90 637 ms; RPC RTT p50 231 ms; sequencer endpoint RTT p50 272 ms. Pure-python keccak decode 4.3 ms/tx (too slow
  live; rhfeed claims 4-70 us). Gas per FOMO-route swap: median $0.66, p90 $2.03 (25 receipts, ETH $2,752).
- VERIFIED (chainstacklabs/fomo-solana-rh-listeners docs/02): FOMO buys = Solana Relay deposit that does NOT name the token,
  then a solver fill on 4663 seconds later. => NO pre-execution visibility of the traded token by any public path.
  Every RH-chain FOMO trade is a solver buy or user sell via ERC-4337 (tx.from = bundler, not trader).
- SOURCE WALLETS LOSE (FomoPulse tape, 294 wallets, 2026-09-05..22, avg-cost): realized -15.3% on $75.8M sold cost;
  win 44-47%. Open bags $23.5M cost "worth" $408M at mark but $27M capped at 50% pool liquidity; 78.8% of paper MTM is one
  token (8Stock, $1,053 liquidity). Realized + liquidity-capped MTM = -8.2% on $99.3M. Persistence weak: Spearman H1->H2
  +0.19; top-quintile H1 wallets realized -9.3% in H2. Followers vs H2 return: Spearman 0.003.
- PROVISIONAL results (follower replay, candidates, cluster test, backfill) are NOT memory facts: they live in
  `PROFIT_DISCOVERY_CHECKPOINT_2026-09-23.md` and `AGENT_HANDOFF.md` until settled (owner rule 2026-09-23).
- Validation-audit supersessions of older memory lines: `MEMORY_SUPERSESSION_2026-09-23.md`.

## CYCLE UPDATE — 2026-09-23: External Alpha Intelligence (Phase 2) — CHECKPOINT, no winner
- Report: `EXTERNAL_ALPHA_INTELLIGENCE_2026-09-23.md`; scripts/raw: `workspace/external_intel_2026-09-23/`. Extends
  `PROFIT_DISCOVERY_2026-09-23.md` (PD); PD T1-T35 stand except corrections below.
- DATA ASSET [V, docs.hydromancer.xyz/reservoir/hyperliquid.md]: Hydromancer Reservoir `s3://hydromancer-reservoir`
  (REQUESTER-PAYS, Parquet, ap-northeast-1): every HL perp fill WITH wallet address, crossed(taker), realized_pnl,
  start_position, builder, twap_id, liquidation flags, from 2025-07-28; Trade[XYZ] from 2025-10-13; daily all-account
  position snapshots; 1s candles; 1m 20-level L2. Egress cost UNQUOTED. PD's "no untouched wallet history" is FALSE for HL.
- [V] HL `recentTrades` / WS `trades` include `users:[buyer,seller]` free. HL official S3 buckets `hl-mainnet-node-data`,
  `hyperliquid-archive` = requester-pays (anonymous AccessDenied, probed 2026-09-23).
- [V] HIP-3 CME analogs, 24h notional 2026-09-23: xyz:CL $360M, xyz:SP500 $222M, xyz:XYZ100 $215M, xyz:GOLD $46M. trade.xyz
  index oracle = CME futures quotes 23/5, internal 30-min EMA when closed (docs.trade.xyz oracle-price, equity-indices/us).
- [V, one day only, Tardis free sample 2026-09-01 BTC]: Binance leads HL ~500ms (corr 0.203 @+500ms, 100ms grid); HL public
  feed delivery p50 256ms/p99 735ms (Tokyo collector). Replaces PD T17 "~700ms [U]".
- [V] HL fees base: taker 4.5bps, maker 1.5bps. Zhai 2026 (arXiv 2608.04373): toxic-wallet markout 1.25-3.11bps, rank
  persistence rho 0.52, replicated Dec 2025 -> TAKER COPY OF TOXIC WALLETS KILLED (markout < fee).
- [V] Indexers disagree per wallet: RHTrenches vs FomoPulse 30d realized, 121 common wallets, SIGN DISAGREES on 21, median
  |diff| $41,259 -> never select wallets from indexer PnL. Aggregates agree: RHT 30d realized -$17.47M (15 win/111 lose),
  FomoPulse -$11.60M. RHTrenches history starts 2026-08-27 only.
- [V] fomo.family copy = notification + manual (official page 2026-02-01). docs.onfomo.com is a DIFFERENT product. Fomo
  leaderboard PnL formula UNRESOLVED (sources conflict: realized / realized+unrealized avg-cost / net cash flow).
- MONEY-PATH CONFLICT: only H2 (HIP-3 index wallet flow -> MES/MNQ minutes) is Lucid-reachable; H1/H3/H4/H5 need a crypto
  account (Track B/C). Owner decision.
- SURVIVING (untested): H2, H1 (identity, maker-side/longer horizon), H3 post-visible-TWAP decay (arXiv 2606.15715),
  H4 HL liquidation-fill recovery path (reopened on NEW data; cascade latency kill was ASSUMED, never measured), H5
  Binance-lead execution filter. Next: E1 Reservoir cost QUOTE (needs owner AWS account) -> bounded pull; E3 $0 Tardis replication.

## CYCLE UPDATE — 2026-09-23 (checkpoint 2): free work complete; AWS cost discovery prepared, NOT run
- Report: `EXTERNAL_ALPHA_INTELLIGENCE_CHECKPOINT2_2026-09-23.md`. No paid object downloaded, no AWS call made.
- [V] HOST CLOCK IS ~15 s FAST and drifting (SNTP: -14.97 s, later -15.95 s, ~140 ms/h). Any raw-wall-clock latency
  measured on this machine is wrong by ~15 s; RTT-based ones are fine. Owner fix: enable Windows time sync (admin).
- [V] Host latency (65 min, SNTP-corrected): Binance USD-M aggTrade event->receipt p50 79 / p90 85 / p99 222 ms;
  HL trades block->receipt p50 315 / p90 485-610 / p99 ~750 ms. Binance futures aggTrade now ONLY on
  `wss://fstream.binance.com/market/...` (legacy /ws path connects but sends nothing).
- [V] Tardis free first-of-month, 23 days 2024-11-01..2026-09-01 (HL starts 2024-11), BTC/ETH/SOL: Binance leads HL
  in EVENT time on 69/69 cells (Hayashi-Yoshida median 600/550/700 ms; 2026 ~500/500/700); receive time adds
  ~250-300 ms = transport. Grid estimates overstate by ~300 ms (sparse-trade bias); HL quote-based lags worse (snapshot cadence).
  Capturable HL catch-up +300..+1500 ms after top-0.5% Binance 200 ms moves: ~1.95-2.37 bps mean vs 9 bps taker
  round trip -> BINANCE->HL LEAD-LAG TRADING KILLED; keep only as execution filter (H5).
- [V] H1 maker use KILLED analytically: Gatto 2026 HL touch quoter 10 s pre-fee capture +0.560 / adverse -1.017 /
  net -0.458 bp; best reachable HL maker fee 0.9 bp (1.5 base, -40% max staking) -> even a perfect filter nets
  -0.34 bp/fill. H1 survives only as a directional minute-horizon test (needs >~10 bp).
- H3 downgraded: fair-pricing evidence -> post-metaorder reversion ~1/3 of peak impact; Naviglio 2025 limited reversion.
- [V] Recorder RUNNING (read-only): `tools/hl_trade_recorder.py` -> `data/hl_tape/` (BTC, ETH, SOL, xyz:SP500,
  xyz:XYZ100, xyz:CL, xyz:GOLD; buyer+seller; SNTP offset logged every 10 min). Audit vs HL 1m candle n: 0.9992-1.0000.
  Not reboot-persistent. Audit with `tools/hl_tape_audit.py` at least every 3 days (candles cover ~3.5 days).
- [V] Artemis `s3://artemis-hyperliquid-data/raw/` = requester-pays too (fills, order statuses ~54 GB/day, TWAP
  statuses, balances; from 2025-08-17). DuckDB lacks requester-pays support (discussion #17770) -> use boto3.
- [V] AWS ap-northeast-1 prices (price list 2026-09-16/18): egress $0.114/GB, LIST $0.0047/1k, GET $0.0037/10k.
  Discovery (~978 LIST + footer GETs) ~ $0.01. Inferred pulls: H2 xyz $0.3-0.8 if coin-selectable, $6-15 full files;
  all four ~$1.3-7 selectable / ~$9-25 full. H2 causal pre-reg draft (M0 controls, cohorts, Holm 12 tests, >=+1 tick net) in report §5.

## CYCLE UPDATE — 2026-09-24: External 8-strategy program (rule sheet + owner report zip) — COMPLETE, 0 SURVIVORS
Report: `EXTERNAL_8_STRATEGIES_STATE.md`; source recovery `EXTERNAL_8_STRATEGIES_SOURCE_RECOVERY.md`; code/logs
`workspace/external_strategies/`; prereg aggregate SHA-256 067f073c…2bcc (frozen before PnL); artefact hashes
`workspace/external_strategies/_program/ARTEFACT_HASHES.json`.
- [V] All 8 primary transcripts retrieved 2026-09-24 (youtube-transcript-api). coBMd1vk2Lo (Trader Mayne) IS fully
  specified (rule sheet said inaccessible). SQEtBHOJW6I = Jay Ortani stock/options Level-2 + tape strategy; the rule
  sheet's IPP / 2 PM Silver Bullet / ICT-FX reconstructions and five "examples" are NOT in the video — retired.
- [V] New free data: HistData 1m BID FX/XAU (EURUSD GBPUSD USDJPY USDCAD NZDUSD XAUUSD) 2022-01..2026-08 in
  `data/fx_histdata/` (EST-no-DST -> UTC). 2025-01..2026-08 is SEALED (unread) as a fresh window.
- RESULTS (DEV only; futures windows REUSED): 62 valid trials + 4 invalid looks registered (`EXT8-*`). Holm/BH all
  1.0; White RC CME p=0.43, FX/XAU p=0.97; max DSR (n>=30) 0.08. Liquidity-trap (Marco) ≈0R over ~1,000 MNQ
  trades even before costs (NO_SIGNAL); Mayne H4 variants ROBUSTLY_REJECTED; PO3, Trident, MMXM TOO_SPARSE;
  Rizzy uptrend-long MNQ +0.15R is FRAGILE (drop top-5 -> +0.014R; bear days -0.05R; negative on ES/XAU).
  Trident's claimed ~90% win rate vs 3/22 mechanized. G (Ortani) and H (Dux) BLOCKED_DATA; neither tradable on Lucid.
- BUG caught by diagnosis: Family A first run used sell-stop semantics (98.8% wrong-side fills) -> invalidated,
  fixed, rerun as `_fix1` (`workspace/external_strategies/_program/BUGFIX_A_ENTRY.md`).
- Databento quotes 2026-09-24 (get_cost, nothing bought): XNAS MBO NVDA/TSLA/AMD 1 month $26.72; XNAS ohlcv-1d all
  symbols 2019..2026-09 $28.00; XNAS ohlcv-1m all $1,428.29; EQUS.MINI ohlcv-1m 2023-06..2026-09 $522.25.
- OPEN (owner): `tests/test_gates_split.py::test_ledger_integrity_and_reference_numbers` now fails because the new
  CME trials raised the MNQ-holdout empirical SR variance 0.00345 -> 0.0172 (ledger working as designed; test not edited).
