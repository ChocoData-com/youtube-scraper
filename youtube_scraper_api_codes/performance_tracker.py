"""
YouTube performance tracker - a real, runnable use case on the Chocodata YouTube Scraper API.

Polls a channel's uploads, stores every observation as a local dataset in SQLite,
and prints how many views each video gained since the previous run. Tracking video
and channel performance over time is the main reason people scrape YouTube, so it
is here end to end rather than as a snippet.

YouTube gives you a *cumulative* view count and nothing else: there is no public
"views this week" field anywhere, on any surface, official API included. The only
way to get velocity is to sample the counter yourself and diff it. That is the
whole idea here.

    pip install requests
    export CHOCODATA_API_KEY="your_key"     # free key (1,000 requests, one-time): https://chocodata.com
    python youtube_scraper_api_codes/performance_tracker.py "@MrBeast"
    # ... run it again tomorrow to see views/day per video

Cost: 1 request (5 credits) per run per channel.
Docs: https://chocodata.com/docs
"""
import os
import re
import sqlite3
import sys
import time

import requests

API = "https://api.chocodata.com/api/v1/youtube/channel"
KEY = os.environ.get("CHOCODATA_API_KEY")
DB = "youtube_performance.db"

if not KEY:
    sys.exit("Set CHOCODATA_API_KEY first. Free key: https://chocodata.com")


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


def fetch(handle: str) -> dict:
    """One API call -> channel metadata + the most recent ~30 uploads."""
    r = requests.get(API, params={"api_key": KEY, "channel": handle}, timeout=90)
    _check(r)
    return r.json()


def parse_views(text) -> int | None:
    """'4,012,271 views' -> 4012271.

    The channel grid ships views as display text, not a number. Older rows can
    also arrive compact ('1.2M views'), so handle both rather than assuming.
    """
    if not isinstance(text, str):
        return None
    m = re.search(r"([\d,.]+)\s*([KMB])?", text.replace(",", ""))
    if not m:
        return None
    try:
        n = float(m.group(1))
    except ValueError:
        return None
    n *= {"K": 1e3, "M": 1e6, "B": 1e9}.get((m.group(2) or "").upper(), 1)
    return int(n)


def setup(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS observations (
               video_id TEXT, channel TEXT, title TEXT, views INTEGER,
               published TEXT, ts INTEGER,
               PRIMARY KEY (video_id, ts)
           )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS channel_stats (
               channel TEXT, subscribers INTEGER, video_count INTEGER, ts INTEGER,
               PRIMARY KEY (channel, ts)
           )"""
    )


def previous(conn: sqlite3.Connection, video_id: str) -> tuple | None:
    return conn.execute(
        "SELECT views, ts FROM observations WHERE video_id = ? ORDER BY ts DESC LIMIT 1",
        (video_id,),
    ).fetchone()


def main(handle: str) -> None:
    conn = sqlite3.connect(DB)
    setup(conn)
    now = int(time.time())
    data = fetch(handle)
    videos = data.get("videos", [])

    print(f"{data['channel_name']} | {data['subscriber_count_text']} | "
          f"{data['video_count_text']} | {len(videos)} recent uploads\n")

    moved = 0
    for v in videos:
        vid, views = v.get("id"), parse_views(v.get("views"))
        if not vid or views is None:
            continue

        before = previous(conn, vid)
        if before and before[0] != views:
            delta = views - before[0]
            hours = max((now - before[1]) / 3600, 1e-9)
            arrow = "UP  " if delta > 0 else "DOWN"
            print(f"{arrow} {v['title'][:50]:50} {before[0]:>11,} -> {views:>11,} "
                  f"({delta:+,} / {delta / hours * 24:+,.0f} per day)")
            moved += 1

        conn.execute(
            "INSERT OR REPLACE INTO observations VALUES (?,?,?,?,?,?)",
            (vid, data["channel_name"], v.get("title"), views, v.get("published"), now),
        )

    conn.execute(
        "INSERT OR REPLACE INTO channel_stats VALUES (?,?,?,?)",
        (data["channel_name"], data.get("subscriber_count"), data.get("video_count"), now),
    )
    conn.commit()
    tracked = conn.execute("SELECT COUNT(DISTINCT video_id) FROM observations").fetchone()[0]
    conn.close()

    print(f"\n{len(videos)} videos this run | {moved} with view changes | "
          f"{tracked} videos tracked in {DB}")
    if moved == 0:
        print("No changes yet. Run it again in a few hours, or schedule it (cron / GitHub Actions).")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "@MrBeast")
