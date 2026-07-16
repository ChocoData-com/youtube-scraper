"""
YouTube Channel - Chocodata YouTube Scraper API

Runnable example. It calls the LIVE API and prints the real JSON response.

    pip install requests
    export CHOCODATA_API_KEY="your_key"      # free: 1,000 requests, one-time
    python youtube_scraper_api_codes/channel.py

Docs: https://chocodata.com/docs
"""
import json
import os
import sys

import requests

API = "https://api.chocodata.com/api/v1/youtube/channel"
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


def channel(handle: str, tab: str = "videos") -> dict:
    """Channel metadata + subscriber count + the first page of the tab's videos."""
    params = {"api_key": KEY, "channel": handle, "tab": tab}
    r = requests.get(API, params=params, timeout=90)
    _check(r)
    return r.json()


def next_page(page_token: str) -> dict:
    """Fetch exactly one more page using the cursor from a previous response."""
    r = requests.get(API, params={"api_key": KEY, "page_token": page_token}, timeout=90)
    _check(r)
    return r.json()


if __name__ == "__main__":
    data = channel("@MrBeast")
    preview = {k: v for k, v in data.items() if k not in ("videos", "next_page_token", "next_page_url")}
    print(json.dumps(preview, indent=2)[:1400])
    print()
    print(f"{data['channel_name']} | {data['subscriber_count_text']} | {data['video_count_text']}")
    print(f"Page 1: {data['videos_count']} videos, has_more={data['has_more']}\n")
    for v in data["videos"][:5]:
        print(f"  {v['position']:2}. {v['title'][:50]:50} {str(v['views']):>18}  {v['published']}")
