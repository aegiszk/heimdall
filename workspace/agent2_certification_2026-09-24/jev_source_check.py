"""Part B second judge: Jev (TypeSafe System One, jev-latest) citation check of Agent 1's recovered source rules.
Pattern: docs.typesafe.ai/cookbooks/citation_check (fetched 2026-09-24). Step 1 (code): pull the verbatim
transcript block(s) at the cited timestamp and string-check the key phrase. Step 2 (Jev): one Choice on how the
section relates to the claim. AUTO_ACCEPT 0.8; below -> Agent 2 manual reading decides (recorded).
"""
import json
import os
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TR = HERE.parents[0] / "external_strategies" / "_source_transcripts"
AUTO_ACCEPT = 0.8

CLAIMS = [
    ("B", "coBMd1vk2Lo", "0:07:20", "three candle", "Swings are 3-candle swing points and a market structure break requires a candle CLOSE through the swing."),
    ("B", "coBMd1vk2Lo", "0:34:52", "two to one", "The creator requires a minimum 2:1 reward-to-risk; a setup below 2:1 is not taken."),
    ("B", "coBMd1vk2Lo", "0:29:35", "swing low get taken out", "Lower-timeframe entry: a swing low forms, that swing low is taken out, then the high that generated it is broken, giving the breaker entry."),
    ("G", "SQEtBHOJW6I", "0:00:00", "orderflow strategy", "The video presents a US-stock order-flow (buyers and sellers / tape) trading strategy rather than an ICT forex strategy."),
    ("G", "SQEtBHOJW6I", "1:17:26", "bookmap", "The creator reads the Bookmap order-book display to see actual resting orders at a level."),
    ("G", "SQEtBHOJW6I", "1:55:57", "S3", "The creator's key levels are Camarilla pivot levels."),
    ("C", "HNuRp9Z1bMs", "0:11:03", "9h hour high", "At 10:00 a.m. ET price typically manipulates above the previous 09:00-hour high, then reverses."),
    ("C", "HNuRp9Z1bMs", "0:48:12", None, "SMT divergence between NQ and ES is checked at the 10:00 sweep of the 09:00-hour extreme."),
    ("C", "HNuRp9Z1bMs", "1:01:56", "15minute low", "The stop is moved to break-even as soon as the 15-minute low is taken."),
    ("H", "52ZsDmFHqyY", "0:18:32", "above 100%", "For the gap-up short the gap up has to be above 100%."),
    ("E", "ADnslyKOwFE", "0:02:47", "one time frame", "The Trident setup is traded on a single timeframe, the 30-minute chart."),
    ("E", "ADnslyKOwFE", "0:33:54", "outside of our kill zone", "A fair value gap printed outside the kill zone is ignored."),
    ("E", "ADnslyKOwFE", "0:32:08", "13 or 15", "The creator is unsure whether the third EMA is 13 or 15."),
]

QUESTION = {
    "relation": {
        "type": "choice",
        "instructions": "How does `section` (a verbatim transcript excerpt from the source video) relate to `claim` (a rule attributed to that video)?",
        "criteria": {
            "supports": "The section states the whole claim or directly implies that all of it is true",
            "partially_supports": "The section supports part of the claim, but another part of the claim (a detail, a name, a condition or a link between two things) is not stated in the section",
            "contradicts": "The section states the opposite of the claim or implies it is false",
            "says_nothing": "The section does not address what the claim asserts, either way",
        },
    }
}
VERDICT = {"supports": "VERIFIED", "partially_supports": "PARTIALLY_VERIFIED", "contradicts": "CONTRADICTED", "says_nothing": "UNSUPPORTED"}


def section(video: str, ts: str) -> str:
    txt = (TR / f"{video}.txt").read_text(encoding="utf-8")
    blocks = re.split(r"(?=\[\d+:\d{2}:\d{2}\])", txt)
    for i, b in enumerate(blocks):
        if b.startswith(f"[{ts}]"):
            return re.sub(r"\s+", " ", " ".join(blocks[i:i + 2]))
    raise KeyError(f"{video} {ts}")


def jev(claim: str, sec: str) -> dict:
    body = json.dumps({"state": {"claim": claim, "section": sec}, "model": "jev-latest", "questions": QUESTION}).encode()
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=body, headers={
        "Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}", "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    a = r["answers"]["relation"]
    return {"choice": a["choice"], "confidence": a["confidence"], "probabilities": a["probabilities"], "model": r["model"]}


if __name__ == "__main__":
    out = []
    for fam, vid, ts, phrase, claim in CLAIMS:
        sec = section(vid, ts)
        found = None if phrase is None else (phrase.lower() in sec.lower())
        a = jev(claim, sec)
        v = VERDICT[a["choice"]]
        out.append(dict(family=fam, video=vid, ts=ts, claim=claim, phrase_found=found, jev_choice=a["choice"],
                        jev_confidence=round(a["confidence"], 3), jev_verdict=v,
                        auto_accept=a["confidence"] >= AUTO_ACCEPT, model=a["model"]))
        print(f"{fam} {vid} {ts:8s} phrase={found!s:5s} {a['choice']:18s} conf={a['confidence']:.2f} -> {v}{'' if a['confidence'] >= AUTO_ACCEPT else '  [REVIEW]'}")
    (HERE / "jev_source_check_result.json").write_text(json.dumps(out, indent=1))
