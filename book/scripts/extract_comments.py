#!/usr/bin/env python3
"""
Parse content/comments.md into book/src/comments_all.json.

The outer author/date fields are unreliable: 555 comments were pasted by the
author in May and August 2011 when the blog moved, so the real commenter and
date sit inside the body in one of several formats. This script pulls them out.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "content" / "comments.md"
OUT = ROOT / "book" / "src" / "comments_all.json"

ITEM = re.compile(
    r'<div class="comment-item">\s*<div class="comment-item-head">\s*'
    r'<span class="comment-item-author">(.*?)</span>\s*'
    r'<span class="comment-item-date">(.*?)</span>\s*'
    r'<span class="comment-item-on">.*?<a href="([^"]*)">(.*?)</a>.*?</span>\s*</div>\s*'
    r'<div class="comment-item-body">(.*?)</div>\s*</div>', re.DOTALL)

# body formats for pasted comments
PASTED = [
    # [引用这个评论]   Jabeck  2009-04-14 评论 text
    re.compile(r"^\[引用这个评论\]\s*(\S+)\s+(\d{4}-\d{2}-\d{2})\s*评论\s*[:：]?\s*(.*)$", re.DOTALL),
    # （百度） 林慕理     2010-11-06 20:33 评论： text   /  (i170) name 于 08-13 07:10 评论 : text
    re.compile(r"^[（(]\s*(?:百度|i170)\s*[)）]\s*(\S+)\s+(?:于\s*)?([\d-]+(?:\s+[\d:]+)?)\s*评论\s*[:：]?\s*(.*)$", re.DOTALL),
    # text 评论者: name   2010-11-25 09:50
    re.compile(r"^(.*?)\s*评论者\s*[:：]\s*(\S+)\s+(\d{4}-\d{2}-\d{2})(?:\s+[\d:]+)?\s*$", re.DOTALL),
]


def clean(s):
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</?p[^>]*>", "\n", s)
    s = re.sub(r"</?[a-zA-Z][^>]*>", "", s)
    s = html.unescape(s)
    s = s.replace(" ", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def split_pasted(author, date, body):
    if author != "wuwufu":
        return author, date, body, False
    b = body.strip()
    m = PASTED[0].match(b)
    if m:
        return m.group(1), m.group(2), m.group(3).strip(), True
    m = PASTED[1].match(b)
    if m:
        return m.group(1), m.group(2), m.group(3).strip(), True
    m = PASTED[2].match(b)
    if m:
        return m.group(2), m.group(3), m.group(1).strip(), True
    # otherwise it is the author's own reply, pasted with the batch
    return "吴五福", date, b, True


def main():
    text = SRC.read_text(encoding="utf-8")
    out = []
    for m in ITEM.finditer(text):
        author, date, url, title, body = (html.unescape(x.strip()) for x in m.groups())
        body = clean(body)
        name, real_date, body, pasted = split_pasted(author, date, body)
        out.append({
            "id": len(out) + 1,
            "name": name,
            "date": real_date[:10],
            "post": title.strip("《》"),
            "url": url,
            "text": body,
            "pasted": pasted,
        })
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    c = Counter(x["name"] for x in out)
    print(f"{len(out)} comments -> {OUT.relative_to(ROOT)}")
    print("top names:", c.most_common(15))


if __name__ == "__main__":
    main()
