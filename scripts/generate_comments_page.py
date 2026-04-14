#!/usr/bin/env python3
"""
扫描所有文章里已嵌入的评论，生成独立的评论汇总页 content/comments.md。
每条评论附上原文标题链接，按时间倒序排列。
"""

import re
from pathlib import Path
from html import unescape

POSTS = Path(__file__).parent.parent / "content" / "posts"
OUTPUT = Path(__file__).parent.parent / "content" / "comments.md"


def parse_front_matter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).split("\n"):
        kv = re.match(r'^(\w+):\s*(.*)', line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return fm, text[m.end():]


def extract_comments(body: str) -> list[dict]:
    """从文章 body 中提取所有 static-comment。"""
    comments = []
    # 每个 comment div
    for m in re.finditer(
        r'<div class="static-comment"(?:\s+style="[^"]*")?\s+id="comment-(\d+)">\s*'
        r'<div class="comment-author">(.*?)</div>\s*'
        r'<div class="comment-date">(.*?)</div>\s*'
        r'<div class="comment-body">(.*?)</div>\s*'
        r'</div>',
        body, re.DOTALL
    ):
        cid, author, date, content = m.groups()
        comments.append({
            "id": cid,
            "author": author.strip(),
            "date": date.strip(),
            "content": content.strip(),
        })
    return comments


def clean_html(html: str) -> str:
    """移除 HTML 标签，保留纯文本。"""
    text = unescape(html)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>\s*<p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?p[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    # 压缩空白
    text = re.sub(r'\n\n+', '\n\n', text)
    return text.strip()


def main():
    all_comments = []
    for md in POSTS.glob("*.md"):
        text = md.read_text("utf-8")
        fm, body = parse_front_matter(text)
        if 'static-comment' not in body:
            continue
        post_title = fm.get("title", "").strip() or "(无标题)"
        post_url = fm.get("url", "").strip()
        for c in extract_comments(body):
            c["post_title"] = post_title
            c["post_url"] = post_url
            all_comments.append(c)

    # 按日期倒序
    all_comments.sort(key=lambda x: x["date"], reverse=True)
    print(f"共收集 {len(all_comments)} 条评论，涉及 {len(set(c['post_url'] for c in all_comments))} 篇文章")

    # 生成 Markdown 页面
    lines = [
        "---",
        'title: "评论"',
        'url: "/comments/"',
        "---",
        "",
        f"共 {len(all_comments)} 条评论。",
        "",
        '<div class="comments-archive">',
        "",
    ]

    for c in all_comments:
        content_html = c["content"]  # 保留 HTML 以便渲染富文本
        lines.append(f'<div class="comment-item">')
        lines.append(f'  <div class="comment-item-head">')
        lines.append(f'    <span class="comment-item-author">{c["author"]}</span>')
        lines.append(f'    <span class="comment-item-date">{c["date"]}</span>')
        lines.append(f'    <span class="comment-item-on">评论了 <a href="{c["post_url"]}">《{c["post_title"]}》</a></span>')
        lines.append(f'  </div>')
        lines.append(f'  <div class="comment-item-body">{content_html}</div>')
        lines.append(f'</div>')
        lines.append('')

    lines.append('</div>')
    lines.append('')

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"已写入: {OUTPUT}")


if __name__ == "__main__":
    main()
