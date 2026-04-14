#!/usr/bin/env python3
"""
清理 wp2hugo 转换后的 Markdown 文件。
- 移除 WP 专用元数据，只保留必要字段
- 修复分类中的 HTML 实体
- 清理 WordPress 专用 HTML
- 重命名文件为可读的中文名

用法:
  python3 cleanup_posts.py              # 正常运行
  python3 cleanup_posts.py --dry-run    # 只打印统计
"""

import os
import re
import sys
import html
from pathlib import Path
from urllib.parse import unquote

CONTENT_DIR = Path(__file__).parent.parent / "content" / "posts"

# 需要保留的 front matter 字段
KEEP_FIELDS = {"title", "date", "categories", "url", "post_id", "author"}


def parse_front_matter(content: str) -> tuple[dict, str]:
    """解析 YAML front matter，返回 (字段字典, body)。"""
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return {}, content

    fm_text = match.group(1)
    body = content[match.end():]

    # 简单的 YAML 解析（不引入 pyyaml 依赖）
    fields = {}
    current_key = None
    current_list = None

    for line in fm_text.split("\n"):
        # 列表项
        if line.startswith("  - "):
            if current_list is not None:
                current_list.append(line.strip("  - ").strip())
            continue

        # 键值对
        kv_match = re.match(r'^(\w[\w_]*)\s*:\s*(.*)', line)
        if kv_match:
            if current_list is not None and current_key:
                fields[current_key] = current_list
                current_list = None

            key = kv_match.group(1)
            value = kv_match.group(2).strip()

            if value == "":
                # 可能是列表的开始
                current_key = key
                current_list = []
            else:
                # 去掉引号
                value = value.strip('"').strip("'")
                fields[key] = value
                current_key = key
                current_list = None

    # 处理最后一个列表
    if current_list is not None and current_key:
        fields[current_key] = current_list

    return fields, body


def build_front_matter(fields: dict) -> str:
    """将字段字典转回 YAML front matter 字符串。"""
    lines = ["---"]

    # 按固定顺序输出
    order = ["title", "date", "url", "categories", "author", "post_id"]
    for key in order:
        if key not in fields:
            continue
        value = fields[key]
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            # 标题和 URL 需要引号（可能含特殊字符）
            if key in ("title", "url", "date"):
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f"{key}: {value}")

    lines.append("---")
    return "\n".join(lines) + "\n"


def fix_categories(categories: list) -> list:
    """修复分类中的 HTML 实体。"""
    return [html.unescape(c) for c in categories]


def clean_wp_html(body: str) -> str:
    """清理 WordPress 专用 HTML 标记。"""
    # 去掉 WordPress block 注释
    body = re.sub(r'<!-- /?wp:.*?-->', '', body)
    # 去掉空的 wp-block div 包裹
    body = re.sub(
        r'<div class="wp-block-[^"]*"[^>]*>(.*?)</div>',
        r'\1',
        body,
        flags=re.DOTALL
    )
    # 去掉多余连续空行
    body = re.sub(r'\n{4,}', '\n\n\n', body)
    return body


def process_file(filepath: Path, dry_run: bool = False) -> dict:
    """处理单个文件，返回统计。"""
    stats = {"cleaned": False, "categories_fixed": False, "renamed": False}

    content = filepath.read_text(encoding="utf-8")
    fields, body = parse_front_matter(content)

    if not fields:
        return stats

    # 只保留需要的字段
    cleaned_fields = {k: v for k, v in fields.items() if k in KEEP_FIELDS}

    # 修复分类 HTML 实体
    if "categories" in cleaned_fields and isinstance(cleaned_fields["categories"], list):
        original_cats = cleaned_fields["categories"]
        cleaned_fields["categories"] = fix_categories(original_cats)
        if cleaned_fields["categories"] != original_cats:
            stats["categories_fixed"] = True

    # 修复标题中的 HTML 实体
    if "title" in cleaned_fields:
        cleaned_fields["title"] = html.unescape(cleaned_fields["title"])

    # 清理正文
    body = clean_wp_html(body)

    # 重建文件内容
    new_content = build_front_matter(cleaned_fields) + body

    if new_content != content:
        stats["cleaned"] = True
        if not dry_run:
            filepath.write_text(new_content, encoding="utf-8")

    # 重命名文件（URL 编码 -> 中文）
    decoded_name = unquote(filepath.name, encoding="utf-8")
    if decoded_name != filepath.name:
        new_path = filepath.parent / decoded_name
        stats["renamed"] = True
        if not dry_run:
            if new_path.exists():
                # 避免冲突，加后缀
                new_path = filepath.parent / (new_path.stem + "-2" + new_path.suffix)
            filepath.rename(new_path)

    return stats


def main():
    dry_run = "--dry-run" in sys.argv

    if not CONTENT_DIR.exists():
        print(f"目录不存在: {CONTENT_DIR}")
        sys.exit(1)

    md_files = list(CONTENT_DIR.glob("*.md"))
    if not md_files:
        print("没有找到 Markdown 文件")
        sys.exit(1)

    print(f"处理 {len(md_files)} 个文件...")
    if dry_run:
        print("（dry-run 模式）")

    total = {"cleaned": 0, "categories_fixed": 0, "renamed": 0}

    for filepath in md_files:
        stats = process_file(filepath, dry_run)
        for key in total:
            if stats[key]:
                total[key] += 1

    print(f"\n完成:")
    print(f"  front matter 清理: {total['cleaned']} 个文件")
    print(f"  分类修复: {total['categories_fixed']} 个文件")
    print(f"  文件重命名: {total['renamed']} 个文件")


if __name__ == "__main__":
    main()
