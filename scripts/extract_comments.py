#!/usr/bin/env python3
"""
从 WordPress.com REST API 提取评论，嵌入到对应的 Hugo Markdown 文件中。
评论以静态 HTML 形式追加到文章末尾。

用法:
  python3 extract_comments.py              # 正常运行
  python3 extract_comments.py --dry-run    # 只打印统计，不修改文件
"""

import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
from urllib.request import urlopen, Request

SITE = "55fu.wordpress.com"
API_BASE = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE}"
CONTENT_DIR = Path(__file__).parent.parent / "content" / "posts"
PAGE_SIZE = 100


def api_get(endpoint: str) -> dict:
    """调用 WordPress.com REST API。"""
    url = f"{API_BASE}{endpoint}"
    req = Request(url, headers={"User-Agent": "wuwufu-migration/1.0"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all_comments() -> list:
    """分页获取所有评论。"""
    all_comments = []
    offset = 0
    while True:
        print(f"  获取评论 offset={offset}...")
        data = api_get(f"/comments/?number={PAGE_SIZE}&offset={offset}&status=approved")
        comments = data.get("comments", [])
        if not comments:
            break
        all_comments.extend(comments)
        if len(all_comments) >= data.get("found", 0):
            break
        offset += len(comments)
        time.sleep(0.5)  # 避免请求过快
    return all_comments


def fetch_post_slugs(post_ids: set) -> dict:
    """批量获取 post ID 到 slug 的映射。"""
    id_to_slug = {}
    for post_id in post_ids:
        try:
            data = api_get(f"/posts/{post_id}?fields=ID,slug,date")
            slug = unquote(data.get("slug", ""), encoding="utf-8")
            date_str = data.get("date", "")
            id_to_slug[post_id] = {"slug": slug, "date": date_str}
            time.sleep(0.3)
        except Exception as e:
            print(f"  警告: 无法获取 post {post_id} 的信息: {e}")
    return id_to_slug


def build_file_index() -> dict:
    """建立 slug -> 文件路径 的索引。"""
    index = {}
    for filepath in CONTENT_DIR.glob("*.md"):
        content = filepath.read_text(encoding="utf-8")
        # 从 front matter 提取 slug
        slug_match = re.search(r'^slug:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
        if slug_match:
            slug = slug_match.group(1).lower().strip()
            index[slug] = filepath
        # 也用文件名作为备选 key
        stem = filepath.stem.lower()
        if stem not in index:
            index[stem] = filepath
    return index


def format_date(date_str: str) -> str:
    """格式化日期显示。"""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return date_str


def build_comment_tree(comments: list) -> list:
    """将评论列表转为树结构（处理嵌套回复）。"""
    by_id = {c["ID"]: c for c in comments}
    roots = []
    children = defaultdict(list)

    for c in comments:
        parent = c.get("parent")
        if parent and isinstance(parent, dict):
            parent_id = parent.get("ID")
        elif parent and isinstance(parent, (int, str)):
            parent_id = int(parent)
        else:
            parent_id = None

        if parent_id and parent_id in by_id:
            children[parent_id].append(c)
        else:
            roots.append(c)

    return roots, children


def render_comment(comment: dict, children: dict, depth: int = 0) -> str:
    """渲染单条评论及其回复为 HTML。"""
    indent_class = f' style="margin-left: {depth * 2}em;"' if depth > 0 else ""
    author = comment.get("author", {}).get("name", "匿名")
    date = format_date(comment.get("date", ""))
    content = comment.get("content", "")
    comment_id = comment.get("ID", 0)

    html = f"""<div class="static-comment"{indent_class} id="comment-{comment_id}">
<div class="comment-author">{author}</div>
<div class="comment-date">{date}</div>
<div class="comment-body">{content}</div>
</div>"""

    # 递归渲染子评论
    for child in children.get(comment_id, []):
        html += "\n" + render_comment(child, children, depth + 1)

    return html


def render_comments_section(comments: list) -> str:
    """渲染完整的评论区 HTML。"""
    if not comments:
        return ""

    # 按日期排序
    comments.sort(key=lambda c: c.get("date", ""))

    roots, children = build_comment_tree(comments)

    parts = [
        "\n\n---\n",
        "\n## 评论\n",
        '<div class="static-comments">\n',
    ]
    for root in roots:
        parts.append(render_comment(root, children))
        parts.append("")
    parts.append("</div>")

    return "\n".join(parts)


def find_md_file(post_info: dict, file_index: dict) -> Path | None:
    """根据 post 信息找到对应的 Markdown 文件。"""
    slug = post_info.get("slug", "").lower().strip()
    if slug in file_index:
        return file_index[slug]

    # 尝试 URL 解码后的 slug
    decoded = unquote(slug, encoding="utf-8").lower()
    if decoded in file_index:
        return file_index[decoded]

    # 模糊匹配：slug 包含在文件名中
    for key, path in file_index.items():
        if slug and slug in key:
            return path

    return None


def main():
    dry_run = "--dry-run" in sys.argv

    if not CONTENT_DIR.exists():
        print(f"目录不存在: {CONTENT_DIR}")
        print("请先运行 wp2hugo 转换内容，再运行此脚本。")
        sys.exit(1)

    # 1. 获取所有评论
    print("步骤 1: 获取评论...")
    comments = fetch_all_comments()
    print(f"  共获取 {len(comments)} 条评论")

    if not comments:
        print("没有评论，退出。")
        return

    # 2. 按 post ID 分组
    print("\n步骤 2: 按文章分组...")
    by_post = defaultdict(list)
    post_ids = set()
    for c in comments:
        post = c.get("post", {})
        post_id = post.get("ID") if isinstance(post, dict) else post
        if post_id:
            by_post[post_id].append(c)
            post_ids.add(post_id)
    print(f"  涉及 {len(by_post)} 篇文章")

    # 3. 获取 post slug 映射
    print(f"\n步骤 3: 获取文章 slug 映射（{len(post_ids)} 篇）...")
    post_slugs = fetch_post_slugs(post_ids)

    # 4. 建立文件索引
    print("\n步骤 4: 建立本地文件索引...")
    file_index = build_file_index()
    print(f"  索引了 {len(file_index)} 个文件")

    # 5. 嵌入评论
    print("\n步骤 5: 嵌入评论...")
    matched = 0
    unmatched = 0
    unmatched_posts = []
    total_comments_embedded = 0

    for post_id, post_comments in by_post.items():
        post_info = post_slugs.get(post_id, {})
        md_file = find_md_file(post_info, file_index)

        if md_file:
            comments_html = render_comments_section(post_comments)
            if comments_html and not dry_run:
                content = md_file.read_text(encoding="utf-8")
                # 移除已有的评论区（如果重复运行）
                content = re.sub(r'\n\n---\n\n## 评论\n.*', '', content, flags=re.DOTALL)
                content += comments_html
                md_file.write_text(content, encoding="utf-8")
            matched += 1
            total_comments_embedded += len(post_comments)
        else:
            unmatched += 1
            slug = post_info.get("slug", "unknown")
            unmatched_posts.append(f"  post_id={post_id}, slug={slug}, 评论数={len(post_comments)}")

    print(f"\n完成:")
    print(f"  匹配成功: {matched} 篇文章，嵌入 {total_comments_embedded} 条评论")
    print(f"  未匹配: {unmatched} 篇文章")
    if unmatched_posts:
        print("\n未匹配的文章:")
        for info in unmatched_posts:
            print(info)
    if dry_run:
        print("\n（dry-run 模式，未修改任何文件）")


if __name__ == "__main__":
    main()
