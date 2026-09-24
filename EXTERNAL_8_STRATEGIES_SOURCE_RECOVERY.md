# External 8-Strategy Program — Source Recovery (2026-09-24)

## What was recovered
All eight primary transcripts were retrieved on 2026-09-24 with the project's existing tool
(`tools/fetch_youtube_transcripts.py`, `youtube-transcript-api` 1.2.4) into
`workspace/external_strategies/_source_transcripts/` (JSON + 45-second-block TXT). The owner also supplied
`trading_strategy_video_reports.zip` (SHA-256 `ecd90a4d002056bfdf796b27a199b9b235de97fcc853191e2c2553e735376742`),
the eight secondary reports the rule sheet was built from, extracted to `_source_reports/`.

Authority order used: **primary transcript > creator's own material > secondary report > rule sheet**.

| Video | Family | Caption type | Snippets | JSON SHA-256 prefix | Rule-sheet status before | Status after |
|---|---|---|---|---|---|---|
| DAnXM7C16h0 | A Liquidity trap | creator (manual) | 1,190 | 57cf810a5fb1e86e | strongest; swing/sweep/session MISSING | stop anchor + trigger structure recovered |
| coBMd1vk2Lo | B Trader Mayne | creator (manual) | 628 | 07dd377895668e5b | **inaccessible, all MISSING** | **near-complete mechanical framework recovered** |
| HNuRp9Z1bMs | C PO3 / 50% | creator (manual) | 752 | 690b0d25980b1c6b | non-verbatim; entry/SMT semantics MISSING | 10:00-hour PO3, SMT, inversion entry, BE trigger recovered |
| AVVM-FyewLg | D Little Rizzy | auto-generated | 2,152 | 52c9b1a05e185f7c | third-party mirror | confirmed; BB = 2 std; close-exit confirmed |
| ADnslyKOwFE | E Trident | creator (manual) | 555 | 1272f03ba35728f0 | non-verbatim | 30m-only, FVG-inside-KZ, 200-EMA bias, entry mechanics recovered |
| IB-fyWI5j8w | F MMXM / OTE | creator (manual) | 863 | 0e56b9491707afd8 | non-verbatim | displacement, wicky→2nd leg, 0.9-stop rationale, weekly bias recovered |
| SQEtBHOJW6I | G "conflicting" | auto-generated | 5,217 | cb8b6b966352b0c3 | **no transcript; 3 incompatible AI passes** | **identity resolved: Jay Ortani stock order-flow; all 3 passes are not the video** |
| 52ZsDmFHqyY | H Small-cap shorts | auto-generated | 1,975 | d76a654ac3813210 | non-verbatim | GS >100% gap, caps by setup, FRD day-2 entry resolved |

## Material corrections to `Trading-Strategy Rule Sheet.md`
1. **coBMd1vk2Lo (Strategy C "all MISSING") is superseded**: 3-candle swings; MSB = close through swing; range =
   immediate swing low → post-MSB swing high; OB = down candle(s) before the break; buy in discount; LTF breaker =
   swing low → sweep → close through the generating high; stop below the stop-run; min 2:1; de-risk at 2R;
   timeframe pairs W→D/H12, D→H1, H4→M15, H1→M5 (0:05:29–0:35:47).
2. **SQEtBHOJW6I**: Pass A (IPP), Pass B (T-Rex/2 PM Silver Bullet), Pass C (generic ICT FX) and all five
   "alleged examples" (EURUSD 1.08455 …) are **not in the video** — retired as NOT_SOURCE. The real content is an
   equities/options Level-2 + tape strategy (Bookmap big orders, absorption, bid refills, Camarilla levels).
3. **HNuRp9Z1bMs**: the 10:00 ET hourly candle sweeping the 09:00-hour high is stated (0:11:03); SMT is NQ-vs-ES
   at that sweep (0:48:12); entry = close/sell-stop through an inversion (0:31:52–0:32:55); BE when the 15-minute
   low is taken (1:01:56); "I don't really trade Mondays and Fridays" (1:13:22) — a new, conflicting preference.
4. **ADnslyKOwFE**: "only trading on one time frame… the 30 minute" (0:02:47); FVG printed outside the kill zone is
   ignored (0:33:54) — conflicts with the 02:30 example (kept as E1 vs E3); "13 or 15, I don't really remember" (0:32:57).
5. **IB-fyWI5j8w**: Silver Bullet is the *second retracement leg* after a wicky break or an opposing 15m PDA
   (0:17:27–0:18:19), not a separate clock window; 0.9 stop: "<10%… one in 15 trades" touch 0.9 but not 1.0 (0:41:50).
6. **52ZsDmFHqyY**: GS "has to be above 100%" (resolves 70–1000% vs >100%); GS cap < $100M, FRD initial cap < $200M;
   FRD entry = short the day after the first red day (resolves the starter-timing conflict). BS ratio direction still MISSING.
7. **DAnXM7C16h0**: entries key off an anchor high that itself swept liquidity; the stop covers that anchor; the
   trigger is taking the newer internal high beneath it (1:08:19); the 5-minute close is used for ADDS (1:26:32).

No generic ICT/SMC definition was imported where a creator did not define a term; such gaps are listed as
RESEARCH_ASSUMPTION in each family's SOURCE_MATRIX.md with alternatives and sensitivity.
