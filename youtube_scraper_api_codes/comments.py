"""
YouTube Comments - Chocodata YouTube Scraper API

Runnable example. It calls the LIVE API and prints the real JSON response.

    pip install requests
    export CHOCODATA_API_KEY="your_key"      # free: 1,000 requests, one-time
    python youtube_scraper_api_codes/comments.py

Docs: https://chocodata.com/docs
"""
import json
import os
import sys

import requests

API = "https://api.chocodata.com/api/v1/youtube/comments"
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
        # Also what you get when a video has comments turned off: the page carries
        # no comments continuation, so there is nothing to parse.
        sys.exit("502: YouTube refused every attempt, or this video has comments disabled. "
                 "You were not charged.")
    r.raise_for_status()


def comments(video_id: str, sort: str = "top") -> dict:
    """One page of comments (20 rows) plus a cursor for the next page."""
    params = {"api_key": KEY, "video_id": video_id, "sort": sort}
    r = requests.get(API, params=params, timeout=90)
    _check(r)
    return r.json()


def next_page(page_token: str) -> dict:
    """Fetch exactly one more page using the cursor from a previous response."""
    r = requests.get(API, params={"api_key": KEY, "page_token": page_token}, timeout=90)
    _check(r)
    return r.json()


if __name__ == "__main__":
    data = comments("x7X9w_GIm1s")
    print(json.dumps(data["comments"][0], indent=2, ensure_ascii=False))
    print()
    for c in data["comments"][:5]:
        print(f"  {str(c['like_count_text']):>6} likes | {c['author'][:20]:20} | {c['text'][:52]}")
    print(f"\n{data['results_count']} comments this page | sort={data['sort_applied']} | "
          f"has_more={data['has_more']}")
