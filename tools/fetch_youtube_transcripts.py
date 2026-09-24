"""Fetch timestamped YouTube transcripts for a fixed research set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video_ids", nargs="+")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    api = YouTubeTranscriptApi()
    for video_id in args.video_ids:
        transcript = api.fetch(video_id)
        payload = {
            "video_id": video_id,
            "language": transcript.language,
            "language_code": transcript.language_code,
            "is_generated": transcript.is_generated,
            "snippets": [
                {
                    "text": snippet.text,
                    "start": snippet.start,
                    "duration": snippet.duration,
                }
                for snippet in transcript
            ],
        }
        output_path = args.output_dir / f"{video_id}.json"
        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(
            f"{video_id}: {len(transcript)} snippets, "
            f"language={transcript.language!r}, generated={transcript.is_generated}, "
            f"output={output_path}"
        )


if __name__ == "__main__":
    main()
