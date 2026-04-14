#!/usr/bin/env python3
"""
验证所有 Markdown 文件中引用的媒体文件是否存在于本地。
缺失的文件会尝试从 WordPress.com 下载。

用法:
  python3 verify_media.py              # 扫描并下载缺失文件
  python3 verify_media.py --scan-only  # 只扫描，不下载
"""

import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

CONTENT_DIR = Path(__file__).parent.parent / "content" / "posts"
STATIC_DIR = Path(__file__).parent.parent / "static"

# WordPress.com 图片 URL 模式
WP_IMAGE_PATTERNS = [
    r'https?://55fu\.wordpress\.com/(wp-content/uploads/[^\s"\'<>]+)',
    r'https?://wuwufu\.com/(wp-content/uploads/[^\s"\'<>]+)',
    r'https?://i\d\.wp\.com/55fu\.wordpress\.com/(wp-content/uploads/[^\s"\'<>]+)',
]

# 本地图片引用模式
LOCAL_IMAGE_PATTERN = r'(?:src="|!\[.*?\]\()/(wp-content/uploads/[^\s"\'<>\)]+)'

# 视频 URL 模式
VIDEO_PATTERNS = [
    r'(https?://videos\.files\.wordpress\.com/[^\s"\'<>]+)',
]


def scan_markdown_files() -> tuple[set, set, set]:
    """扫描所有 Markdown 文件，提取媒体引用。"""
    local_refs = set()
    remote_refs = set()
    video_refs = set()

    for filepath in CONTENT_DIR.glob("*.md"):
        content = filepath.read_text(encoding="utf-8")

        # 本地引用
        for match in re.finditer(LOCAL_IMAGE_PATTERN, content):
            local_refs.add(match.group(1))

        # 远程 WordPress 引用（还未替换为本地路径的）
        for pattern in WP_IMAGE_PATTERNS:
            for match in re.finditer(pattern, content):
                remote_refs.add(match.group(1))

        # 视频引用
        for pattern in VIDEO_PATTERNS:
            for match in re.finditer(pattern, content):
                video_refs.add(match.group(1))

    return local_refs, remote_refs, video_refs


def check_local_files(refs: set) -> tuple[set, set]:
    """检查本地引用的文件是否存在。"""
    existing = set()
    missing = set()
    for ref in refs:
        local_path = STATIC_DIR / ref
        if local_path.exists():
            existing.add(ref)
        else:
            missing.add(ref)
    return existing, missing


def download_file(url: str, local_path: Path) -> bool:
    """下载文件到本地。"""
    try:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        req = Request(url, headers={"User-Agent": "wuwufu-migration/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
            local_path.write_bytes(data)
        return True
    except (HTTPError, URLError, OSError) as e:
        print(f"    下载失败: {url} -> {e}")
        return False


def download_missing(missing: set, source_base: str = "https://55fu.wordpress.com/") -> tuple[int, int]:
    """下载缺失的文件。"""
    success = 0
    failed = 0
    for ref in sorted(missing):
        url = source_base + ref
        local_path = STATIC_DIR / ref
        print(f"  下载: {ref}...")
        if download_file(url, local_path):
            success += 1
        else:
            # 尝试 wuwufu.com 作为备选
            alt_url = "https://wuwufu.com/" + ref
            if download_file(alt_url, local_path):
                success += 1
            else:
                failed += 1
        time.sleep(0.3)
    return success, failed


def main():
    scan_only = "--scan-only" in sys.argv

    if not CONTENT_DIR.exists():
        print(f"目录不存在: {CONTENT_DIR}")
        sys.exit(1)

    md_count = len(list(CONTENT_DIR.glob("*.md")))
    print(f"扫描 {md_count} 个 Markdown 文件...\n")

    local_refs, remote_refs, video_refs = scan_markdown_files()

    print(f"媒体引用统计:")
    print(f"  本地图片引用: {len(local_refs)}")
    print(f"  远程图片引用（未替换）: {len(remote_refs)}")
    print(f"  视频引用: {len(video_refs)}")

    # 检查本地文件
    if local_refs:
        print(f"\n检查本地文件...")
        existing, missing = check_local_files(local_refs)
        print(f"  存在: {len(existing)}")
        print(f"  缺失: {len(missing)}")

        if missing and not scan_only:
            print(f"\n下载缺失的本地引用文件...")
            success, failed = download_missing(missing)
            print(f"  成功: {success}, 失败: {failed}")
        elif missing:
            print("\n缺失文件列表:")
            for ref in sorted(missing):
                print(f"  {ref}")

    # 处理远程引用
    if remote_refs:
        print(f"\n远程引用（应该由 cleanup_posts.py 替换为本地路径）:")
        all_refs = local_refs | remote_refs
        _, missing_remote = check_local_files(remote_refs)
        print(f"  已存在本地: {len(remote_refs) - len(missing_remote)}")
        print(f"  需要下载: {len(missing_remote)}")

        if missing_remote and not scan_only:
            print(f"\n下载远程引用文件...")
            success, failed = download_missing(missing_remote)
            print(f"  成功: {success}, 失败: {failed}")

    # 视频统计
    if video_refs:
        print(f"\n视频引用（{len(video_refs)} 个）:")
        for ref in sorted(video_refs):
            print(f"  {ref}")
        print("提示: 视频文件可能较大，建议手动处理或保留原始链接。")

    # 统计总体积
    total_size = 0
    if STATIC_DIR.exists():
        for f in STATIC_DIR.rglob("*"):
            if f.is_file():
                total_size += f.stat().st_size
    print(f"\nstatic/ 目录总大小: {total_size / 1024 / 1024:.1f} MB")

    if scan_only:
        print("\n（scan-only 模式，未下载任何文件）")


if __name__ == "__main__":
    main()
