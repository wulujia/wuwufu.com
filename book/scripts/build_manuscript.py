#!/usr/bin/env python3
"""
Build the book manuscript (book/src/manuscript.json) from book/manifest.yaml
and content/posts/*.md.

The author's text is kept verbatim. Only three kinds of edits are made:
  1. WordPress leftovers are removed (HTML tags, entities, [gallery], backslash escapes)
  2. ASCII punctuation between Chinese characters is widened to full-width
  3. Typos listed in manifest `fixes` are applied

Usage:
  python3 book/scripts/build_manuscript.py            # tiers A and B
  python3 book/scripts/build_manuscript.py --tier A   # tier A only
"""

import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
POSTS = ROOT / "content" / "posts"
BOOK = ROOT / "book"
MANIFEST = BOOK / "manifest.yaml"
OUT = BOOK / "src" / "manuscript.json"

CJK = r"\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"
FIG = "\x00FIG:"
DROPPED = []


# ---------- front matter ----------

def parse_front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    fields = {}
    key = None
    for line in m.group(1).split("\n"):
        if line.startswith("  - ") and key:
            fields.setdefault(key, [])
            if isinstance(fields[key], list):
                fields[key].append(line[4:].strip().strip('"'))
            continue
        kv = re.match(r"^(\w+):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            fields[key] = val.strip('"') if val else []
    return fields, text[m.end():]


def fmt_date(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return ""
    y, mo, d = (int(x) for x in m.groups())
    return f"{y} 年 {mo} 月 {d} 日"


# ---------- images ----------

def resolve_image(src):
    """Map an image reference to a path relative to the repo root, or None."""
    src = html.unescape(src.strip())
    src = re.sub(r"[?#].*$", "", src)
    if src.startswith("/wp-content/"):
        src = unquote(src)
    if src.startswith("/wp-content/"):
        rel = "/static" + src
    elif src.startswith("https://55fu.wordpress.com/wp-content/uploads/"):
        tail = src[len("https://55fu.wordpress.com/wp-content/uploads/"):]
        rel = "/book/images/external/" + tail.replace("/", "_")
    elif src.startswith("/book/"):
        rel = src
    else:
        return None
    if not (ROOT / rel.lstrip("/")).exists():
        return None
    return rel


def image_info(rel):
    with Image.open(ROOT / rel.lstrip("/")) as im:
        w, h = im.size
    return {"t": "fig", "src": rel, "w": w, "h": h}


# ---------- text cleaning ----------

WECHAT_STAMPS = [
    re.compile(r"^\**\s*微信\s*(\d{6}|\d{8})\s*[:：]\s*\**\s*"),
    re.compile(r"^\**\s*(\d{8})\s*\**\s*\**\s*微信\s*[:：]?\s*\**\s*"),
    re.compile(r"^\**\s*(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\s*微信\s*[:：]\s*\**\s*"),
    re.compile(r"^\**\s*(\d{2})\s*\**\s*\**\s*(\d{6})\s*\**\s*\**\s*微信\s*[:：]\s*\**\s*"),
]


def strip_wechat_stamp(body):
    """Remove the WeChat date stamp from the first text line; return (body, date string)."""
    lines = body.split("\n")
    idx = next((i for i, l in enumerate(lines) if l.strip() and not l.startswith(FIG)), None)
    if idx is None:
        return body, None
    lead = lines[idx].lstrip()
    if re.search(r"微信\s*[:：]", lead[:40]) or re.match(r"^\**\s*微信\s*\d", lead):
        lead = lead.replace("**", "")
    for i, rx in enumerate(WECHAT_STAMPS):
        m = rx.match(lead)
        if not m:
            continue
        g = m.groups()
        if i == 0:
            s = g[0]
            if len(s) == 6:
                y, mo, d = 2000 + int(s[:2]), int(s[2:4]), int(s[4:])
            else:
                y, mo, d = int(s[:4]), int(s[4:6]), int(s[6:])
        elif i == 1:
            s = g[0]
            y, mo, d = int(s[:4]), int(s[4:6]), int(s[6:])
        elif i == 2:
            y, mo, d = (int(x) for x in g)
        else:
            s = g[0] + g[1]
            y, mo, d = int(s[:4]), int(s[4:6]), int(s[6:])
        lines[idx] = lead[m.end():]
        return "\n".join(lines), f"{y} 年 {mo} 月 {d} 日"
    return body, None


def widen_punct(s):
    """ASCII punctuation touching Chinese text becomes full-width."""
    pairs = {",": "，", ".": "。", "?": "？", "!": "！", ":": "：", ";": "；"}
    for a, f in pairs.items():
        s = re.sub(rf"(?<=[{CJK}])\{a}(?=[{CJK}\s]|$)", f, s)
    if re.search(rf"[{CJK}]", s):
        s = re.sub(r"\(\s*", "（", s)
        s = re.sub(r"\s*\)", "）", s)
    return s


def clean_body(raw, piece):
    body = raw
    # cut comments
    body = re.split(r"\n-{3,}\s*\n## 评论|\n## 评论|<div class=\"static-comments\">", body)[0]
    # video
    body = re.sub(r"<video.*?</video>", "", body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"<source[^>]*>", "", body)
    # images -> placeholders
    def fig(m):
        rel = resolve_image(m.group(1))
        if not rel:
            DROPPED.append((piece.get("file") or piece.get("gallery"), m.group(1)[:80]))
        return f"\n\n{FIG}{rel}\n\n" if rel else "\n\n"
    body = re.sub(r'\{\{<\s*figure\s+src="([^"]+)"[^>]*>\}\}', fig, body)
    body = re.sub(r"\[!\[[^\]]*\]\(([^)\s]+)[^)]*\)\]\([^)]*\)", fig, body)
    body = re.sub(r"!\[[^\]]*\]\(([^)\s]+)[^)]*\)", fig, body)
    body = re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', fig, body)
    # html structure
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.IGNORECASE)
    body = re.sub(r"</?(p|div|pre|blockquote)[^>]*>", "\n\n", body, flags=re.IGNORECASE)
    body = re.sub(r"<a\s[^>]*>(.*?)</a>", r"\1", body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"</?[a-zA-Z][^>]*>", "", body)
    body = html.unescape(body)
    # markdown links: keep text, drop bare urls
    body = re.sub(r"\[([^\]]*)\]\([^)]*\)", lambda m: "" if re.match(r"^\s*(https?://|/)", m.group(1)) else m.group(1), body)
    body = re.sub(r"https?://\S+", "", body)
    # wordpress shortcodes and escapes
    body = re.sub(r"\\\[/?(gallery|caption)[^\]]*\\\]", "", body)
    body = re.sub(r"\[/?(gallery|caption)[^\]]*\]", "", body)
    body = body.replace("\\\\", "\\")
    body = re.sub(r"\\([.\[\]*_#()!\-+>])", r"\1", body)
    body = re.sub(r"^\s*\*\s+", "", body, flags=re.MULTILINE)
    body = body.replace("\u00a0", " ")
    # typo fixes from manifest
    for old, new in (piece.get("fixes") or {}).items():
        body = body.replace(old, new)
    return body


# ---------- runs and blocks ----------

def to_runs(line):
    runs = []
    parts = re.split(r"\*\*", line)
    for i, seg in enumerate(parts):
        if seg == "":
            continue
        runs.append({"s": seg, "b": bool(i % 2)})
    # drop bold if the whole line is bold (WeChat export artifact)
    if runs and all(r["b"] for r in runs):
        for r in runs:
            r["b"] = False
    return runs


def norm_line(s):
    s = re.sub(r"[ \t\u3000]+", " ", s).strip()
    return widen_punct(s)


def looks_like_verse(lines):
    if len(lines) < 3:
        return False
    short = sum(1 for l in lines if len(l) <= 22)
    return short / len(lines) >= 0.8


def split_joined_verse(line):
    """A poem pasted on one line has spaces between Chinese verse lines."""
    parts = re.split(rf"(?<=[{CJK}*]) +(?=[{CJK}*])", line)
    return parts if len(parts) >= 4 else None


def build_blocks(body, mode):
    blocks = []
    groups = re.split(r"\n\s*\n", body.strip())
    for g in groups:
        lines = [l for l in g.split("\n") if l.strip()]
        if not lines:
            continue
        if lines[0].startswith(FIG):
            for l in lines:
                if l.startswith(FIG):
                    blocks.append(image_info(l[len(FIG):].strip()))
            continue
        lines = [norm_line(l) for l in lines]
        lines = [l for l in lines if l]
        if not lines:
            continue
        if mode == "verse" or looks_like_verse(lines):
            blocks.append({"t": "verse", "lines": [to_runs(l) for l in lines]})
            continue
        for l in lines:
            joined = split_joined_verse(l)
            if joined:
                blocks.append({"t": "verse", "lines": [to_runs(x.strip()) for x in joined]})
            else:
                blocks.append({"t": "p", "runs": to_runs(l)})
    return blocks


# ---------- pieces ----------

def find_written(blocks):
    """Look for the author's own trailing date mark such as （1961/10） or 写于1970-10-10."""
    tail = []
    for b in blocks[-3:]:
        if b["t"] == "p":
            tail.append("".join(r["s"] for r in b["runs"]))
        elif b["t"] == "verse":
            tail.append("".join(r["s"] for l in b["lines"][-2:] for r in l))
    for t in reversed(tail):
        m = re.search(r"(?:写于|作于)?\s*[（(]?\s*(19\d{2}|20\d{2})\s*[./年-]\s*(\d{1,2})(?:\s*[./月-]\s*(\d{1,2}))?\s*[日）)]?", t)
        if m:
            y, mo = m.group(1), int(m.group(2))
            return f"{y} 年 {mo} 月"
        m = re.search(r"[（(]\s*(19\d{2}|20\d{2})\s*[）)]", t)
        if m:
            return f"{m.group(1)} 年"
    return None


def load_post(name):
    text = (POSTS / f"{name}.md").read_text(encoding="utf-8")
    fm, body = parse_front_matter(text)
    return fm, body


def build_piece(spec):
    name = spec["file"]
    fm, body = load_post(name)
    cats = fm.get("categories") or []
    cat = cats[0] if cats else ""
    mode = spec.get("mode") or ("verse" if cat == "我的诗" else "auto")
    body = clean_body(body, spec)
    body, wechat_date = strip_wechat_stamp(body)
    blocks = build_blocks(body, mode)
    if spec.get("images") is not None:
        blocks = [b for b in blocks if b["t"] != "fig"]
        blocks += [image_info(p) for p in spec["images"]]
    for p in spec.get("extra_images") or []:
        blocks.append(image_info(p))
    date = wechat_date or fmt_date(fm.get("date", ""))
    if wechat_date:
        cat = "微信"
    if spec.get("written"):
        date = f"写于 {spec['written']}"
    elif (fm.get("date", "") or "").startswith("2005-07-0"):
        w = find_written(blocks)
        date = f"写于 {w}" if w else ""
    return {
        "title": spec.get("title") or html.unescape(fm.get("title", name)),
        "date": date,
        "category": cat,
        "tier": spec.get("tier", "A"),
        "source": name,
        "blocks": blocks,
    }


def build_gallery(spec):
    imgs = []
    for name in spec["files"]:
        fm, body = load_post(name)
        body = clean_body(body, spec)
        for l in body.split("\n"):
            if l.startswith(FIG):
                imgs.append(image_info(l[len(FIG):].strip()))
                break
    return {
        "title": spec.get("title") or spec["gallery"],
        "date": spec.get("date", ""),
        "category": spec.get("category", ""),
        "tier": spec.get("tier", "A"),
        "source": spec["gallery"],
        "blocks": [{"t": "grid", "cols": spec.get("columns", 3), "imgs": imgs}],
    }


def main():
    tier = "B"
    if "--tier" in sys.argv:
        tier = sys.argv[sys.argv.index("--tier") + 1]
    m = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    out = {"book": m["book"], "front": [], "parts": []}
    for spec in m.get("front", []):
        out["front"].append(build_piece(spec))
    chars = 0
    figs = 0
    for part in m["parts"]:
        pieces = []
        for spec in part["pieces"]:
            if spec.get("tier", "A") > tier:
                continue
            piece = build_gallery(spec) if "gallery" in spec else build_piece(spec)
            for b in piece["blocks"]:
                if b["t"] == "p":
                    chars += sum(len(r["s"]) for r in b["runs"])
                elif b["t"] == "verse":
                    chars += sum(len(r["s"]) for l in b["lines"] for r in l)
                elif b["t"] == "fig":
                    figs += 1
                elif b["t"] == "grid":
                    figs += len(b["imgs"])
            pieces.append(piece)
        out["parts"].append({"title": part["title"], "subtitle": part.get("subtitle", ""), "pieces": pieces})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(p["pieces"]) for p in out["parts"])
    for name, src in DROPPED:
        print(f"  dropped image in {name}: {src}")
    print(f"wrote {OUT.relative_to(ROOT)}: {n} pieces, {chars} chars, {figs} images (tier <= {tier})")


if __name__ == "__main__":
    main()
