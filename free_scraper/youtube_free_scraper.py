"""Free YouTube scraper: no API key, no headless browser, no JavaScript rendering.

YouTube server-renders its search results into a `ytInitialData` JSON blob inside
a <script> tag, so you can extract structured data from YouTube search pages with
plain HTTP + a JSON parse.

Usage:
    python free_scraper/youtube_free_scraper.py "python"

IMPORTANT, and the reason this script reports what it reports: YouTube ships
anti-bot and consent JavaScript on *successful* pages too. The strings "captcha"
and "consent.youtube" are present in the HTML of a page that returned perfectly
good data. So this script does NOT decide "blocked" by grepping the body for
scary words: it parses first, and only reports a block when the data is
genuinely absent. Getting that backwards produces a scraper that can never
report success.
"""
import json
import re
import sys

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def fetch(query):
    url = "https://www.youtube.com/results?search_query=" + requests.utils.quote(query)
    r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
                     timeout=45)
    return r


def extract_yt_initial_data(html):
    """Find `ytInitialData = {...}` and brace-match the object literal.

    Brace matching has to skip over string literals, or a `{` inside any JSON
    string value unbalances the count.
    """
    for m in re.finditer(r"ytInitialData\s*=\s*\{", html):
        start = html.index("{", m.start())
        depth, in_str, quote, i = 0, False, "", start
        while i < len(html):
            ch = html[i]
            if in_str:
                if ch == "\\":
                    i += 2
                    continue
                if ch == quote:
                    in_str = False
            elif ch in "\"'":
                in_str, quote = True, ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(html[start:i + 1])
                    except json.JSONDecodeError:
                        break
            i += 1
    return None


def read_text(node):
    """YouTube text nodes are either {simpleText} or {runs:[{text}]}."""
    if not isinstance(node, dict):
        return None
    if isinstance(node.get("simpleText"), str):
        return node["simpleText"]
    if isinstance(node.get("runs"), list):
        return "".join(r.get("text", "") for r in node["runs"]) or None
    return None


def extract_videos(data):
    """Walk the tree for every video renderer, in document order.

    YouTube serves at least two renderer shapes for the same query depending on
    which layout you get: `videoRenderer` (desktop) and `videoWithContextRenderer`
    (mobile web). Accept either.
    """
    out, seen = [], set()

    def visit(node):
        if isinstance(node, list):
            for c in node:
                visit(c)
            return
        if not isinstance(node, dict):
            return
        v = node.get("videoRenderer") or node.get("videoWithContextRenderer")
        if isinstance(v, dict) and v.get("videoId") and v["videoId"] not in seen:
            title = read_text(v.get("title")) or read_text(v.get("headline"))
            if title:
                seen.add(v["videoId"])
                out.append({
                    "position": len(out) + 1,
                    "video_id": v["videoId"],
                    "title": title,
                    "url": "https://www.youtube.com/watch?v=" + v["videoId"],
                    "channel": read_text(v.get("ownerText")) or read_text(v.get("shortBylineText")),
                    "views": read_text(v.get("viewCountText")) or read_text(v.get("shortViewCountText")),
                    "published": read_text(v.get("publishedTimeText")),
                    "length": read_text(v.get("lengthText")),
                })
        for k in node:
            visit(node[k])

    visit(data.get("contents", data))
    return out


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "python"
    r = fetch(query)
    print(f"HTTP {r.status_code}  {len(r.text):,} bytes")

    data = extract_yt_initial_data(r.text)

    # PARSE FIRST. If real videos came back, it worked, whatever anti-bot strings
    # happen to be sitting in the page's JavaScript.
    if data:
        videos = extract_videos(data)
        if videos:
            print(f"OK: parsed {len(videos)} videos for {query!r}\n")
            for v in videos[:10]:
                print(f"  {v['position']:2}. {v['title'][:58]}")
                print(f"      {v['channel']}  |  {v['views']}  |  {v['length']}  |  {v['published']}")
            print(f"\nParsed {len(videos)} videos. Note that number: re-run this and it changes,")
            print("because YouTube serves a different layout per request. See the README.")
            return 0

    # Only NOW is it fair to call it a block or a markup change.
    title = re.search(r"<title>(.*?)</title>", r.text, re.S)
    print("NO DATA: ytInitialData parsed = %s" % (data is not None))
    print(f"  <title>: {title.group(1)[:70] if title else 'n/a'}")
    print("  Either a bot/consent wall, or the JSON shape moved. Check the title above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
