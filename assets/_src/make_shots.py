"""Render developer-journey screenshots from REAL captured session output.

Follows the pattern oxylabs/amazon-scraper uses: a terminal shot of the command
actually running, then a table shot of the data it retrieved.

The text rendered here is the verbatim stdout of a real run (captured to
%TEMP%/ytqa/*.out) and the real committed JSON. The shell prompt is deliberately
generic so no local username or path is exposed.
"""
import json
import os
import re

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..")
DATA = os.path.join(OUT, "..", "youtube_scraper_api_data")
QA = os.path.expandvars(r"%TEMP%\ytqa")
F = "C:/Windows/Fonts/"

MONO = ImageFont.truetype(F + "consola.ttf", 15)
MONOB = ImageFont.truetype(F + "consolab.ttf", 15)
UI = ImageFont.truetype(F + "segoeui.ttf", 14)
UIB = ImageFont.truetype(F + "seguisb.ttf", 14)

BG, FG, DIM = (13, 15, 19), (208, 205, 200), (110, 106, 100)
GREEN, BLUE, AMBER, RED, CYAN = (126, 209, 138), (127, 178, 255), (255, 196, 138), (232, 118, 118), (120, 205, 210)

SECRET = re.compile(r"asa_live_[A-Za-z0-9_\-]+")


def sanitize(s: str) -> str:
    """Never leak a key, a local path, or a username into an image."""
    s = SECRET.sub("$CHOCODATA_API_KEY", s)
    s = re.sub(r"[A-Za-z]:\\Users\\[^\\\s]+", "~", s)
    s = re.sub(r"/c/Users/[^/\s]+", "~", s)
    s = s.replace(os.environ.get("USERNAME", "\0"), "dev")
    return s


def clip(s: str, n: int = 108) -> str:
    """Trim to width and drop characters the console font cannot draw (emoji)."""
    s = s[:n]
    return "".join(ch if ch == "\t" or 32 <= ord(ch) < 0x2190 else "?" for ch in s)


def terminal(lines, path, width=1180, title="youtube-scraper"):
    pad, lh = 18, 23
    h = 46 + pad * 2 + lh * len(lines)
    img = Image.new("RGB", (width, h), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, 38], fill=(24, 26, 31))
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse([16 + i * 20, 14, 26 + i * 20, 24], fill=c)
    d.text((width // 2 - 52, 11), title, font=UI, fill=DIM)
    y = 38 + pad
    for text, color, bold in lines:
        d.text((pad, y), text, font=MONOB if bold else MONO, fill=color)
        y += lh
    img.save(os.path.join(OUT, path))
    print("wrote assets/" + path, img.size)


def read_out(name):
    p = os.path.join(QA, name)
    return sanitize(open(p, encoding="utf-8", errors="replace").read()) if os.path.exists(p) else ""


def body_lines(src):
    return [l for l in read_out(src).strip().splitlines() if l.strip()]


def colorize(l):
    if re.search(r'"\w+":', l):
        return BLUE
    if re.search(r':\s+\d', l):
        return AMBER
    return FG


def shot_generic(src, out, cmd, keep=13, tail_color=CYAN, export=True):
    """Terminal shot of any script's real captured stdout."""
    body = body_lines(src)
    lines = []
    if export:
        lines.append(('$ export CHOCODATA_API_KEY="your_key"', GREEN, True))
    lines += [(f"$ python {cmd}", GREEN, True), ("", FG, False)]
    for l in body[:keep]:
        lines.append((clip(l), colorize(l), False))
    if len(body) > keep + 1:
        lines.append(("  ...", DIM, False))
    lines += [("", FG, False), (clip(body[-1]), tail_color, True)]
    terminal(lines, out)


def shot_free():
    """The free scraper actually running. It works, and the shot says so."""
    body = body_lines("free_run1.out")
    lines = [('$ python free_scraper/youtube_free_scraper.py "python"', GREEN, True), ("", FG, False)]
    for l in body[:13]:
        c = GREEN if l.startswith("OK:") else (DIM if l.startswith("      ") else FG)
        lines.append((clip(l), c, l.startswith("OK:")))
    lines += [("  ...", DIM, False), ("", FG, False),
              ("# No key, no browser. It worked: 4 of 4 runs.", DIM, False),
              ("# Re-run it and the count changes: 27, 25, 19, 26.", DIM, False)]
    terminal(lines, "run-free.png")


def shot_error():
    """The error UX: what a bad key actually gives you. Trust-building."""
    body = body_lines("badkey.out")
    lines = [('$ export CHOCODATA_API_KEY="wrong_key"', GREEN, True),
             ("$ python youtube_scraper_api_codes/search.py", GREEN, True), ("", FG, False)]
    for l in body[:4]:
        lines.append((clip(l), RED, True))
    lines += [("", FG, False),
              ("# no traceback, no silent empty list: every documented error", DIM, False),
              ("# maps to a message that tells you what to do next.", DIM, False)]
    terminal(lines, "run-error.png")


def shot_table():
    """Retrieved data as a table, the way oxylabs shows it."""
    s = json.load(open(os.path.join(DATA, "search.json"), encoding="utf-8"))["organic_results"][:8]
    cols = [("#", 34), ("title", 300), ("video_id", 104), ("channel", 152), ("views", 84),
            ("length", 80), ("published", 108)]
    W = sum(c[1] for c in cols) + 40
    rh, hh = 30, 34
    H = 52 + hh + rh * len(s)
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 14), "youtube_search_results", font=UIB, fill=(30, 30, 30))
    x0, y0 = 20, 46
    d.rectangle([x0, y0, W - 20, y0 + hh], fill=(238, 238, 238))
    x = x0
    for name, w in cols:
        d.text((x + 9, y0 + 9), name, font=UIB, fill=(20, 20, 20))
        x += w
    y = y0 + hh
    for i, r in enumerate(s):
        if i % 2:
            d.rectangle([x0, y, W - 20, y + rh], fill=(250, 250, 250))
        title = clip(r["title"], 40) + ("..." if len(r["title"]) > 40 else "")
        vals = [str(r["position"]), title, r["video_id"],
                clip((r["channel"]["name"] or "-"), 18),
                str(r["views"] or "-").replace(" views", ""),
                str(r["length"] or "-"), str(r["published"] or "-")]
        x = x0
        for (name, w), v in zip(cols, vals):
            d.text((x + 9, y + 7), v, font=MONO if name in ("video_id", "views", "length") else UI,
                   fill=(60, 60, 60) if name != "#" else (150, 150, 150))
            x += w
        d.line([(x0, y), (W - 20, y)], fill=(226, 226, 226))
        y += rh
    d.line([(x0, y), (W - 20, y)], fill=(226, 226, 226))
    for i in range(len(cols) + 1):
        xx = x0 + sum(c[1] for c in cols[:i])
        d.line([(xx, y0), (xx, y)], fill=(226, 226, 226))
    img.save(os.path.join(OUT, "retrieved-data.png"))
    print("wrote assets/retrieved-data.png", img.size)


if __name__ == "__main__":
    shot_generic("search.out", "run-search.png", "youtube_scraper_api_codes/search.py")
    shot_generic("video.out", "run-video.png", "youtube_scraper_api_codes/video.py", export=False)
    shot_generic("transcript.out", "run-transcript.png", "youtube_scraper_api_codes/transcript.py", export=False)
    shot_generic("comments.out", "run-comments.png", "youtube_scraper_api_codes/comments.py", export=False)
    shot_table()
    shot_free()
    shot_error()
