"""Jev (TypeSafe System One) DECIDES the source-fidelity adjudications for TRIDENT_V2 and MMXM_V2 (owner instruction:
Jev takes decisions). State = verbatim primary-transcript quotes with timestamps (creator-uploaded captions, retrieved
2026-09-24, hashes in EXTERNAL_8_PROGRAM_HANDOFF_TO_CHECKER.md). Code applies a decision only at confidence >= 0.80;
otherwise the item is ESCALATED and the spec may not be frozen on it. Jev never sees PnL or results.
Output: workspace/revenue_sprint_2026-09-24/JEV_V2_ADJUDICATION.json
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "workspace" / "revenue_sprint_2026-09-24" / "JEV_V2_ADJUDICATION.json"
MIN_CONF = 0.80

TRIDENT = {
    "video": "ADnslyKOwFE (TG Capital, 'Trident'), creator captions",
    "quotes": {
        "05:31": "you see how all these EMAs here, the five, the 9, the 13, and the 21, they're all stacking. So, it's showing "
                 "strong bullish structure already. If they were intertwining like this, if the EMAs were crossing like here, I "
                 "wouldn't be interested in any price action that has to do with that because it's a low probability condition.",
        "33:04-33:54": "if we're above the 200 EMA, that's my bias. If we're below, we're looking for shorts. So I keep that as "
                       "like a neutral bias. So, if we're above the 200 structure is bullish.",
        "40:14-41:59": "if my daily chart is below the 200 EMA, I'm not looking for longs. I'll be short biased. So, if I do take a "
                       "trade, and say my higher time frame, the 4 hour and the daily is below the 200 EMA, and I get a long "
                       "setup, I'll cut it earlier because I know that the higher time frame is bearish. So maybe I'll do like on "
                       "those trades like 10 to 15 R",
        "45:39": "See, this one was below the 200 EMA. But notice ... all of the EMAs are stacking. You're just riding.",
        "44:48-45:39": "definitely utilize the indicator ... if these candles weren't green like this and they were red and blue, it "
                       "would be an invalidated setup. You don't take it because the market conditions aren't there.",
        "33:04 indicator": "It's called bull trading on TradingView. Bull trading one minute easy scalping. You change the first "
                           "time frame to daily time frame ... if these candles are closing green, it's showing strong bullish price action.",
        "19:39": "usually I'll just ride the trend until like the EMAs cross over or if I get like a large bearish candle, then I'll cut it",
        "00:56 / 12:41 / 38:29": "The risk-to-reward minimum that I'm taking on that trades is a 1 to 20 ... the smallest amount of RR "
                                 "that I've taken on a trade is 1 to 20. That's like my minimum.",
        "34:54": "If you want to just solely utilize a 1 to 20 you can. But ... you could take my model and use it in a different way.",
        "06:24-07:19": "I see a fair value gap here, printing on the 3 a.m. candle ... It doesn't have to be at 3:00 a.m., but based on my "
                       "data, when the candle is at 3:00 a.m. or 2:30 or 3:30, it's normally really highly probable",
        "33:54 FVG": "Here's the FG printed at 2:30. Like I told you, 2:30 and 3:00, those fair value gaps are extremely strong ... "
                     "We're not worried about this fair value gap. You know why? Because it's printed outside of our kill zone.",
        "02:47": "we're strictly going to be trading in the London kill zone ... from the hours of 3:00 a.m. ... I'll usually stop "
                 "looking for entries at around 6:30 a.m.",
    },
    "note": "The 'bull trading' indicator is a third-party TradingView script whose formula is not given in the source and is not "
            "available offline; it cannot be reproduced faithfully.",
}

MMXM = {
    "video": "IB-fyWI5j8w (MBB Trader / Omar), creator captions",
    "quotes": {
        "03:41-04:39": "previous days highs and previous days lows and you can even say previous week high and previous week low ... "
                       "these areas are our key levels. From these key levels, we have the expectation of a market maker model to form",
        "05:32": "You need a predetermined expectation on the day. So, you'll only favor this when you're bearish.",
        "12:06": "break a block is literally when you have a low, a high, right? And then you run that high. So, you have a high, "
                 "low, a high, low, higher high, lower low ... This is a reference point for the first entry",
        "12:58": "there's always a conversation about body close or is it a wick close? bodied close 15 minute.",
        "29:02-29:52": "If I'm bearish on the week and Monday trades higher, Tuesday I'm favoring this run and reversal ... if you're a "
                       "London open trader, you might get that even in London. And you'll try position that if you're in there in "
                       "London, hold the trade through the day",
        "29:52": "London open is 2 to 5 [New York time] and then 7 to 10 is New York and then 10 to 12 is London close.",
        "30:49": "this can be London ... and then New York is what I like to call the London to New York optimal trade entry ... "
                 "8:00 a.m. New York time, you might get that in New York that break a block ... if there's still time in New "
                 "York or it's a London close kind of day",
        "37:21": "This is your entry. So you'll have some sort of swing made, right? You'll have some sort of swing made right in "
                 "the market. This is your distribution side of the curve.",
        "36:21-40:07": "if we draw a fib ... This is your one level. This is one. This is zero ... So from this high to this low 60% of "
                       "the range ... sell at this level with your stop loss at the one TP at the zero",
        "50:40": "this is your first swing point. Optimal trade entries need to have graded swing points ... your stop loss is a "
                 "swing. How good is the swing? If the swing you think should remain intact, anchor your fib from there.",
        "40:58-42:42": "the chances of your trade hitting 90% and keeping the one in between is less than 10% ... maybe this is the "
                       "90%. And you can put your stop loss there.",
        "55:52": "at the 62 level with a 90% stop loss and the zero TP is like 2.2R",
        "56:43": "if you get that 705 90% stop-loss shave and you get that TP just an original TP, two trades back to back ... "
                 "you're passing a challenge",
        "45:20-46:15": "we get here at 0.2 ... eliminate risk, go break even 0.2, and you're closing there. Not wicking there.",
        "Agent 1 V1 implementation (not source)": "V1 discarded the whole day if the key level was first run outside a kill zone; "
                                                   "searched the broken swing only within the last 60 fifteen-minute bars; set fib 0 "
                                                   "to the lowest low from the SMR high through the displacement bar close.",
    },
}

Q = {
    "trident_ema_stack": {"type": "choice",
        "instructions": "Using only `trident.quotes`, what role does the 5/9/13/21 EMA stack play for a LONG Trident setup?",
        "criteria": {"hard_requirement_bullish_stack": "a long setup is only taken when the EMAs are stacked bullishly; "
                                                        "otherwise the source says he is not interested",
                     "disqualifier_intertwining_only": "only intertwined/crossing EMAs disqualify; any non-crossing order is acceptable",
                     "preferred_context_only": "stacking is preferred but setups are still taken without it"}},
    "trident_ema200": {"type": "choice",
        "instructions": "Using only `trident.quotes`, what role does price relative to the 200 EMA play for a LONG setup?",
        "criteria": {"hard_filter": "longs are never taken below the 200 EMA",
                     "bias_context_not_gate": "it sets bias and management (e.g. smaller target) but longs below it are still taken"}},
    "trident_indicator_blocks_fidelity": {"type": "noul",
        "instructions": ("Using `trident.quotes` and `trident.note`: the source states a setup is invalidated if the 'bull trading' "
                         "indicator candles are not green, and that indicator cannot be reproduced. Does this make a mechanical "
                         "model without it NOT source-faithful (a fidelity failure), rather than a disclosed limitation?"),
        "criteria": {"true": "the omitted rule is an explicit invalidation condition, so fidelity fails",
                     "false": "the omission is a disclosed limitation and fidelity can still pass"}},
    "trident_exit": {"type": "choice",
        "instructions": "Using only `trident.quotes`, which single exit rule best represents how the creator manages a winning long?",
        "criteria": {"fixed_20R_target": "close the whole position at 20R",
                     "ride_until_ema_cross": "hold until the EMAs cross over (or a large bearish candle), no fixed target",
                     "not_determinable": "the source does not support choosing one"}},
    "trident_fvg_window": {"type": "choice",
        "instructions": ("Using only `trident.quotes`, which FVG timing rule is most consistent with ALL the FVG and kill-zone "
                         "statements (3:00-6:30 window, 2:30/3:00/3:30 FVGs strongest, FVG printed outside the kill zone ignored)?"),
        "criteria": {"fvg_completed_inside_kz": "the FVG's third candle must form inside 03:00-06:30 (so a 02:30-03:30 gap counts)",
                     "fvg_middle_candle_inside_kz": "the FVG's middle candle must open at or after 03:00",
                     "any_time_before_or_during_kz": "any FVG formed before or during the window counts"}},
    "mmxm_outside_kz_veto": {"type": "noul",
        "instructions": ("Using `mmxm.quotes`: does the source say that if the key level is first run OUTSIDE a kill zone, a later "
                         "setup that forms inside a kill zone on the same day must be skipped?"),
        "criteria": {"true": "the source states or clearly implies this veto",
                     "false": "the source does not state this veto; it was an implementation choice"}},
    "mmxm_kz_role": {"type": "choice",
        "instructions": "Using `mmxm.quotes`, which event must fall inside a kill zone (NY 02-05, 07-10, 10-12)?",
        "criteria": {"displacement_break_in_kz": "the breaker / displacement close that confirms the setup forms inside a kill zone",
                     "level_run_in_kz": "the run of the key level must happen inside a kill zone",
                     "not_determinable": "the source does not tie any specific event to the kill zones"}},
    "mmxm_swing_break": {"type": "choice",
        "instructions": "Using `mmxm.quotes`, which swing must the displacement close through?",
        "criteria": {"most_recent_swing_before_smr_uncapped": "the most recent swing low before the run high, however far back",
                     "swing_within_fixed_lookback": "a swing low within a fixed recent window (e.g. 60 bars)",
                     "not_determinable": "the source does not specify"}},
    "mmxm_fib_zero": {"type": "choice",
        "instructions": "Using `mmxm.quotes`, where is fib 0 anchored for the OTE entry of a sell?",
        "criteria": {"completed_swing_low_of_displacement_leg": "at the low of the displacement leg once a swing low has formed",
                     "lowest_low_at_break_close": "at the lowest low reached by the close of the candle that broke structure",
                     "not_determinable": "the source does not specify"}},
    "mmxm_entry_stop": {"type": "choice",
        "instructions": "Using `mmxm.quotes`, which single OTE entry / stop combination is the creator's stated plan?",
        "criteria": {"ote62_stop100": "limit at 0.62, stop at 1.0", "ote705_stop90": "limit at 0.705, stop at 0.9",
                     "ote62_stop90": "limit at 0.62, stop at 0.9", "not_determinable": "no single plan is stated"}},
}


def _key() -> str:
    k = os.environ.get("TYPESAFE_API_KEY")
    if not k and (ROOT / ".env").exists():
        m = re.search(r"^TYPESAFE_API_KEY\s*=\s*['\"]?([^'\"\r\n]+)", (ROOT / ".env").read_text(encoding="utf-8"), re.M)
        k = m.group(1).strip() if m else None
    if not k:
        raise SystemExit("TYPESAFE_API_KEY not available")
    return k


def main() -> int:
    body = json.dumps({"model": "jev-latest", "state": {"trident": TRIDENT, "mmxm": MMXM}, "questions": Q}).encode()
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
    dec, esc = {}, []
    for k, a in resp["answers"].items():
        if a["type"] == "noul":
            p = a["noul"]
            ok = p >= MIN_CONF or p <= 1 - MIN_CONF
            dec[k] = {"decision": (p >= 0.5) if ok else "ESCALATED", "noul": p}
        else:
            ok = a["confidence"] >= MIN_CONF and a["choice"] != "not_determinable"
            dec[k] = {"decision": a["choice"] if ok else "ESCALATED", "jev_choice": a["choice"],
                      "confidence": a["confidence"], "probabilities": a.get("probabilities")}
        if not ok:
            esc.append(k)
    out = {"decider": "Jev", "model": resp.get("model"), "min_confidence": MIN_CONF, "decisions": dec, "escalated": esc,
           "state": {"trident": TRIDENT, "mmxm": MMXM}, "questions": Q, "usage": resp.get("usage")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"decisions": dec, "escalated": esc}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
