"""
YouTube Shorts - Chocodata YouTube Scraper API

Runnable example. It calls the LIVE API and prints the real JSON response.

    pip install requests
    export CHOCODATA_API_KEY="your_key"      # free: 1,000 requests, one-time
    python youtube_scraper_api_codes/shorts.py

Docs: https://chocodata.com/docs
"""
import json
import os
import sys

import requests

API = "https://api.chocodata.com/api/v1/youtube/shorts"
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


def short(video_id: str) -> dict:
    """Data for one Short. Accepts a bare id or any /shorts/<id> URL."""
    params = {"api_key": KEY, "video_id": video_id}
    r = requests.get(API, params=params, timeout=90)
    _check(r)
    return r.json()


if __name__ == "__main__":
    data = short("egvLKQe6I4I")
    preview = {k: v for k, v in data.items() if k not in ("related", "thumbnails")}
    print(json.dumps(preview, indent=2, ensure_ascii=False)[:1500])
    print()
    print(f"{data['title']} | {data['view_count']:,} views | {data['like_count']:,} likes | "
          f"{data['duration_seconds']}s | is_short={data['is_short']}")
