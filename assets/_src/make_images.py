"""Generate the repo's hero + evidence graphics with Pillow.

Every value rendered here is REAL: the JSON card fields come from
youtube_scraper_api_data/video.json, the free-vs-API numbers come from measured
runs of both scripts in this repo, and the search-drift panel is five real,
consecutive calls to /youtube/search recorded on 2026-07-16.

Nothing here is a mocked-up screenshot of a page we could not reach.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(OUT, "..", "youtube_scraper_api_data")
F = "C:/Windows/Fonts/"


def font(name, size):
    for cand in (name, "segoeui.ttf"):
        try:
            return ImageFont.truetype(F + cand, size)
        except OSError:
            continue
    return ImageFont.load_default()


BOLD, SEMI, REG, MONO = "segoeuib.ttf", "seguisb.ttf", "segoeui.ttf", "consola.ttf"
INK = (245, 243, 240)
MUTE = (169, 162, 154)
DIM = (111, 106, 100)
ACC = (255, 143, 90)
ACC2 = (255, 196, 138)


def vgrad(w, h, top, bot):
    """Vertical gradient base."""
    img = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.point((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return img.resize((w, h))


def glow(img, cx, cy, rx, ry, color, strength):
    """Soft radial glow, composited additively."""
    layer = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 44
    for i in range(steps, 0, -1):
        t = i / steps
        a = int(strength * (1 - t) ** 2.2)
        d.ellipse([cx - rx * t, cy - ry * t, cx + rx * t, cy + ry * t],
                  fill=tuple(int(c * a / 255) for c in color))
    return Image.fromarray(
        np.clip(np.asarray(img, dtype=int) + np.asarray(layer, dtype=int), 0, 255).astype("uint8"))


def pill(d, x, y, text, f, hot=False):
    w = d.textlength(text, font=f)
    h = 30
    d.rounded_rectangle([x, y, x + w + 28, y + h], radius=15,
                        fill=(28, 20, 17) if hot else (25, 26, 30),
                        outline=(120, 66, 44) if hot else (52, 54, 60))
    d.text((x + 14, y + 6), text, font=f, fill=ACC2 if hot else (221, 214, 207))
    return w + 28 + 9


def hero():
    W, H = 1280, 540
    img = vgrad(W, H, (15, 17, 21), (26, 18, 16))
    img = glow(img, 1000, 100, 520, 300, (255, 143, 90), 46)
    img = glow(img, 150, 470, 420, 260, (120, 84, 60), 40)
    d = ImageDraw.Draw(img)

    # faint grid
    for x in range(0, W, 64):
        d.line([(x, 0), (x, H)], fill=(24, 26, 31))
    for y in range(0, H, 64):
        d.line([(0, y), (W, y)], fill=(24, 26, 31))

    # brand
    d.ellipse([64, 60, 75, 71], fill=ACC)
    d.text((88, 57), "C H O C O D A T A", font=font(SEMI, 15), fill=(185, 178, 170))

    # headline
    d.text((64, 108), "YouTube", font=font(BOLD, 76), fill=INK)
    d.text((64, 192), "Scraper", font=font(BOLD, 76), fill=ACC)

    d.text((64, 300), "Extract video titles, views, likes, transcripts, comments", font=font(REG, 23), fill=MUTE)
    d.text((64, 334), "and channel data from YouTube.com as structured JSON.", font=font(REG, 23), fill=MUTE)

    els = [("titles", 1), ("views", 1), ("likes", 1), ("transcripts", 1), ("comments", 1),
           ("subscribers", 1), ("descriptions", 0), ("keywords", 0), ("search results", 0),
           ("playlists", 0), ("Shorts", 0), ("channels", 0)]
    f = font(REG, 15)
    x, y = 64, 410
    for t, hot in els:
        w = d.textlength(t, font=f) + 37
        if x + w > 700:
            x, y = 64, y + 39
        x += pill(d, x, y, t, f, hot=bool(hot))

    # real JSON card, straight from the committed sample
    cx, cy, cw = 828, 150, 388
    d.rounded_rectangle([cx, cy, cx + cw, cy + 268], radius=14, fill=(11, 13, 17), outline=(45, 47, 53))
    d.rounded_rectangle([cx, cy, cx + cw, cy + 38], radius=14, fill=(21, 23, 28))
    d.rectangle([cx, cy + 24, cx + cw, cy + 38], fill=(21, 23, 28))
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse([cx + 14 + i * 18, cy + 14, cx + 24 + i * 18, cy + 24], fill=c)
    d.line([(cx, cy + 38), (cx + cw, cy + 38)], fill=(38, 40, 46))

    v = json.load(open(os.path.join(DATA, "video.json"), encoding="utf-8"))
    rows = [("{", None, None),
            ('  "title"', f'"{v["title"]}"', "s"),
            ('  "view_count"', f'{v["view_count"]}', "n"),
            ('  "like_count"', f'{v["like_count"]}', "n"),
            ('  "channel_name"', f'"{v["channel_name"]}"', "s"),
            ('  "duration_seconds"', str(v["duration_seconds"]), "n"),
            ('  "category"', f'"{v["category"]}"', "s"),
            ('  "related_count"', str(v["related_count"]), "n"),
            ("}", None, None)]
    fm = font(MONO, 13)
    yy = cy + 54
    for k, val, kind in rows:
        if val is None:
            d.text((cx + 18, yy), k, font=fm, fill=DIM)
        else:
            d.text((cx + 18, yy), k, font=fm, fill=(127, 178, 255))
            kw = d.textlength(k, font=fm)
            d.text((cx + 18 + kw, yy), ": ", font=fm, fill=DIM)
            d.text((cx + 18 + kw + d.textlength(": ", font=fm), yy), val, font=fm,
                   fill=(154, 230, 160) if kind == "s" else ACC2)
        yy += 24

    d.text((828, 468), "9 endpoints  ·  real JSON  ·  no headless browser", font=font(REG, 14), fill=DIM)
    img.save(os.path.join(OUT, "hero.png"))
    print("wrote assets/hero.png", img.size)


def evidence():
    """The honest side-by-side. On YouTube the free script WORKS, so this is not
    'blocked vs parsed'. It is what each path actually costs you."""
    W, H = 1280, 440
    img = vgrad(W, H, (15, 17, 21), (22, 16, 15))
    d = ImageDraw.Draw(img)
    d.text((64, 40), "The free script works. Here is what each path costs.", font=font(BOLD, 27), fill=INK)
    d.text((64, 80), "Measured 2026-07-16 from a clean residential IP, 4 runs of each. Reproduce both with the scripts in this repo.",
           font=font(REG, 15), fill=DIM)

    fm = font(MONO, 13)

    # left: the free path (works, but you pay in bytes and in parsers)
    d.rounded_rectangle([64, 124, 624, 392], radius=13, fill=(22, 19, 13), outline=(104, 84, 44))
    d.text((88, 144), "free_scraper/youtube_free_scraper.py", font=font(MONO, 13), fill=(220, 186, 120))
    for i, ln in enumerate([
        "HTTP status ........ 200   (4 of 4 runs)",
        "downloaded ......... ~2.0 MB of HTML per query",
        "videos parsed ...... 27, 25, 19, 26   (same query)",
        "fields per video ... 8    (ones you parse yourself)",
        "renderer shapes .... 2    (desktop + mobile web)",
        "transcripts ........ not from this page",
    ]):
        d.text((88, 182 + i * 24), ln, font=fm, fill=(178, 168, 162))
    d.text((88, 350), "Works. You own the parser.", font=font(BOLD, 16), fill=(226, 176, 92))

    # right: the API
    s = json.load(open(os.path.join(DATA, "search.json"), encoding="utf-8"))
    t = json.load(open(os.path.join(DATA, "transcript.json"), encoding="utf-8"))
    d.rounded_rectangle([656, 124, 1216, 392], radius=13, fill=(12, 20, 14), outline=(46, 96, 54))
    d.text((680, 144), "youtube_scraper_api_codes/search.py", font=font(MONO, 13), fill=(130, 210, 140))
    for i, ln in enumerate([
        "HTTP status ........ 200   (4 of 5 runs, 1 retryable 502)",
        "downloaded ......... ~17 KB of parsed JSON",
        f"videos parsed ...... {s['results_count']}   (results_count)",
        f"fields per video ... {len(s['organic_results'][0])}   (parsed for you)",
        "renderer shapes .... somebody else's problem",
        f"transcripts ........ 1 call -> {t['segment_count']} segments",
    ]):
        d.text((680, 182 + i * 24), ln, font=fm, fill=(178, 168, 162))
    d.text((680, 350), "Works. We own the parser.", font=font(BOLD, 16), fill=(110, 210, 130))

    img.save(os.path.join(OUT, "free-vs-api.png"))
    print("wrote assets/free-vs-api.png", img.size)


def drift():
    """Five identical calls to /youtube/search, recorded 2026-07-16. This is the
    single most useful thing to know before you build on YouTube search."""
    W, H = 1280, 486
    img = vgrad(W, H, (15, 17, 21), (20, 17, 22))
    d = ImageDraw.Draw(img)
    d.text((64, 40), "Five identical calls. 53 different videos.", font=font(BOLD, 27), fill=INK)
    d.text((64, 80), "GET /api/v1/youtube/search?search_query=python  ·  five times in a row  ·  2026-07-16",
           font=font(MONO, 13), fill=DIM)

    fm = font(MONO, 14)
    fb = font(MONO, 14)
    # measured: (call, results_count, #1 title)
    calls = [(1, 22, "Python Tutorial Deutsch | Komplettkurs"),
             (2, 20, "Python Tutorial For Beginners in Hindi"),
             (3, 20, "GOT7 'PYTHON' MV"),
             (4, 19, "GOT7 'PYTHON' MV"),
             (5, 23, "GOT7 'PYTHON' MV")]
    y = 132
    d.text((88, y), "call", font=font(SEMI, 13), fill=DIM)
    d.text((150, y), "results_count", font=font(SEMI, 13), fill=DIM)
    d.text((290, y), "position 1", font=font(SEMI, 13), fill=DIM)
    y += 26
    for n, cnt, title in calls:
        d.rounded_rectangle([80, y - 4, 1200, y + 24], radius=6, fill=(23, 21, 28) if n % 2 else (19, 18, 24))
        d.text((88, y), f" {n}", font=fm, fill=MUTE)
        d.text((150, y), f"{cnt}", font=fb, fill=ACC2)
        d.text((290, y), title, font=fm, fill=(200, 195, 190))
        y += 30

    y += 18
    d.rounded_rectangle([80, y, 1200, y + 86], radius=10, fill=(18, 20, 26), outline=(58, 60, 70))
    d.text((104, y + 16), "53", font=font(BOLD, 30), fill=ACC)
    d.text((104, y + 54), "distinct video_ids across the five calls", font=font(REG, 14), fill=MUTE)
    d.text((520, y + 16), "3", font=font(BOLD, 30), fill=ACC)
    d.text((520, y + 54), "of them appeared in every call", font=font(REG, 14), fill=MUTE)
    d.text((900, y + 16), "19-23", font=font(BOLD, 30), fill=ACC)
    d.text((900, y + 54), "results per call, same query", font=font(REG, 14), fill=MUTE)

    d.text((64, H - 34), "That is YouTube, not the API. The free script in this repo drifts the same way (27/25/19/26). Plan for it.",
           font=font(REG, 14), fill=DIM)
    img.save(os.path.join(OUT, "search-drift.png"))
    print("wrote assets/search-drift.png", img.size)


if __name__ == "__main__":
    hero()
    evidence()
    drift()
