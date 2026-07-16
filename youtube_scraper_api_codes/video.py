"""
YouTube Video - Chocodata YouTube Scraper API

Runnable example. It calls the LIVE API and prints the real JSON response.

    pip install requests
    export CHOCODATA_API_KEY="your_key"      # free: 1,000 requests, one-time
    python youtube_scraper_api_codes/video.py

Docs: https://chocodata.com/docs
"""
import json
import os
import sys

import requests

API = "https://api.chocodata.com/api/v1/youtube/video"
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


def video(video_id: str) -> dict:
    """Full data for one video: title, views, likes, description, keywords, related."""
    params = {"api_key": KEY, "video_id": video_id}
    r = requests.get(API, params=params, timeout=90)
    _check(r)
    return r.json()


if __name__ == "__main__":
    data = video("x7X9w_GIm1s")
    # related[] is 12 rows; trim it here so the printed object stays readable.
    preview = {k: v for k, v in data.items() if k not in ("related", "thumbnails")}
    print(json.dumps(preview, indent=2)[:1800])
    print()
    print(f"{data['title']} | {data['view_count']:,} views | {data['like_count']:,} likes | "
          f"{data['channel_name']} | {data['related_count']} related")
