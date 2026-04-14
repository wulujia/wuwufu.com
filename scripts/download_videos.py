#!/usr/bin/env python3
"""
从 WordPress 下载所有 MP4 视频和 doc 文件到本地 static/ 目录。
"""

import os
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

STATIC_DIR = Path(__file__).parent.parent / "static"
URLS_FILE = "/tmp/video_urls.txt"


def download(url: str, dest: Path) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = Request(url, headers={"User-Agent": "wuwufu-migration/1.0"})
        with urlopen(req, timeout=120) as resp:
            data = resp.read()
            dest.write_bytes(data)
        return True
    except (HTTPError, URLError, OSError) as e:
        return False


def main():
    urls = Path(URLS_FILE).read_text().strip().split("\n")
    print(f"共 {len(urls)} 个文件待下载\n")

    success = 0
    failed = 0
    skipped = 0
    total_size = 0

    for i, url in enumerate(urls, 1):
        url = url.strip()
        if not url:
            continue

        rel_path = url.replace("https://wuwufu.com/", "")
        dest = STATIC_DIR / rel_path
        filename = dest.name

        if dest.exists() and dest.stat().st_size > 0:
            size = dest.stat().st_size
            total_size += size
            skipped += 1
            print(f"[{i}/{len(urls)}] 已存在: {filename} ({size/1024/1024:.1f}MB)")
            continue

        print(f"[{i}/{len(urls)}] 下载: {filename}...", end=" ", flush=True)

        if download(url, dest):
            size = dest.stat().st_size
            total_size += size
            success += 1
            print(f"{size/1024/1024:.1f}MB")
        else:
            # 备用 URL
            alt_url = url.replace("wuwufu.com", "55fu.wordpress.com")
            if download(alt_url, dest):
                size = dest.stat().st_size
                total_size += size
                success += 1
                print(f"{size/1024/1024:.1f}MB (备用)")
            else:
                failed += 1
                print("失败")

        time.sleep(0.3)

    print(f"\n完成:")
    print(f"  下载成功: {success}")
    print(f"  已存在: {skipped}")
    print(f"  失败: {failed}")
    print(f"  总大小: {total_size/1024/1024:.1f}MB")


if __name__ == "__main__":
    main()
