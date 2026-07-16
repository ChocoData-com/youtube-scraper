"""
YouTube Transcript - Chocodata YouTube Scraper API

Runnable example. It calls the LIVE API and prints the real JSON response.

Transcripts are the endpoint people most often come to YouTube scraping for, and
the one the official YouTube Data API does not give you for videos you do not own
(captions.download "requires the user to have permission to edit the video").

    pip install requests
    export CHOCODATA_API_KEY="your_key"      # free: 1,000 requests, one-time
    python youtube_scraper_api_codes/transcript.py

Docs: https://chocodata.com/docs
"""
import json
import os
import sys

import requests

API = "https://api.chocodata.com/api/v1/youtube/transcript"
KEY = os.environ.get("CHOCODATA_API_KEY")

if not KEY:
    sys.exit("Set CHOCODATA_API_KEY first. Free key (1,000 requests, one-time): https://chocodata.com")


def _check(r) -> None:
    """Map the API's documented errors onto actionable messages instead of a traceback."""
    if r.status_code == 400:
        sys.exit(f"400 invalid_params: {r.text[:200]}")
    if r.status_code == 401:
        sys.exit("401 INVALID_API_KEY: key missing or not recognised. Get one: https://chocodata.com")
    if r.status_code == 402:
        sys.exit("402 INSUFFICIENT_CREDITS: balance exhausted. Top up or upgrade: https://chocodata.com/pricing")
    if r.status_code == 429:
        sys.exit("429 RATE_LIMITED: over your plan's concurrency. Back off and retry.")
    if r.status_code == 502:
        sys.exit("502 target_unreachable: YouTube refused every attempt for this request. "
                 "Retryable, and you were not charged.")
    r.raise_for_status()


def transcript(video_id: str, lang: str = "en", fmt: str = "both") -> dict:
    """Captions for one video, as timed segments and/or one plain-text blob."""
    params = {"api_key": KEY, "video_id": video_id, "lang": lang, "format": fmt}
    r = requests.get(API, params=params, timeout=90)
    _check(r)
    return r.json()


if __name__ == "__main__":
    data = transcript("x7X9w_GIm1s")

    # A reachable video with no captions is a SUCCESS with transcript_available:false,
    # not an error. Handle that case rather than KeyError-ing on `segments`.
    if not data.get("transcript_available"):
        sys.exit(f"No transcript for {data['video_id']}: reason={data.get('reason')}")

    preview = {k: v for k, v in data.items() if k not in ("segments", "text")}
    print(json.dumps(preview, indent=2))
    print()
    for s in data["segments"][:5]:
        print(f"  [{s['start']:>7.2f}s +{s['duration']:.2f}s] {s['text']}")
    print(f"\n{data['segment_count']} segments | {data['word_count']} words | "
          f"{data['language_name']} | source={data['source']}")
