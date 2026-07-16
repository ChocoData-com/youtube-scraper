"""
YouTube Suggest - Chocodata YouTube Scraper API

Runnable example. It calls the LIVE API and prints the real JSON response.

    pip install requests
    export CHOCODATA_API_KEY="your_key"      # free: 1,000 requests, one-time
    python youtube_scraper_api_codes/suggest.py

Docs: https://chocodata.com/docs
"""
import json
import os
import string
import sys

import requests

API = "https://api.chocodata.com/api/v1/youtube/suggest"
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


def suggest(query: str, language: str = "en", country: str = "us") -> dict:
    """YouTube's own autocomplete suggestions for a seed keyword."""
    params = {"api_key": KEY, "query": query, "language": language, "country": country}
    r = requests.get(API, params=params, timeout=90)
    _check(r)
    return r.json()


def expand(seed: str) -> list:
    """A-Z expansion: the standard trick for turning one seed into a keyword list.

    Costs 27 requests (1 seed + 26 letters), so mind your credits.
    """
    found = list(suggest(seed)["related_searches"])
    for ch in string.ascii_lowercase:
        found += suggest(f"{seed} {ch}")["related_searches"]
    return sorted(set(found))


if __name__ == "__main__":
    data = suggest("python")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()
    print(f"{data['related_count']} suggestions for {data['query']!r}")
    # Uncomment for the full A-Z expansion (27 requests):
    # print("\n".join(expand("python")))
