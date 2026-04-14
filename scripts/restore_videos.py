#!/usr/bin/env python3
"""
从 WordPress XML 导出文件中提取视频嵌入信息，
恢复到 wp2hugo 转换后丢失视频的 Markdown 文件中。

视频来源：
1. wp-block-video: <figure><video src="videos.files.wordpress.com/...">
2. videopress: https://videopress.com/v/...
3. hana-flv-player: [hana-flv-player video="..."]

策略：从 XML 中匹配 post_id，提取视频 URL，
建立 videos.files.wordpress.com -> 本地 wp-content/uploads 的映射，
将 <video> 标签插入对应的 Markdown 文件。
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

EXPORT_DIR = Path(__file__).parent.parent / "export"
CONTENT_DIR = Path(__file__).parent.parent / "content" / "posts"
STATIC_DIR = Path(__file__).parent.parent / "static"

NS = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'wp': 'http://wordpress.org/export/1.2/',
}


def find_xml_file() -> Path:
    """找到导出的 XML 文件。"""
    for f in EXPORT_DIR.rglob("*.xml"):
        return f
    raise FileNotFoundError("找不到 XML 导出文件")


def extract_videos_from_html(html_content: str) -> list[dict]:
    """从 HTML 内容中提取所有视频引用。"""
    videos = []

    # wp-block-video 中的 <video> 标签
    for match in re.finditer(
        r'<figure[^>]*class="[^"]*wp-block-video[^"]*"[^>]*>.*?'
        r'<video[^>]*src="([^"]+)"[^>]*/?>.*?</figure>',
        html_content, re.DOTALL
    ):
        videos.append({"type": "wp-block-video", "url": match.group(1)})

    # 单独的 <video> 标签（不在 figure 中）
    for match in re.finditer(
        r'<video[^>]*src="([^"]+)"[^>]*/?>',
        html_content
    ):
        url = match.group(1)
        # 避免重复
        if not any(v["url"] == url for v in videos):
            videos.append({"type": "video-tag", "url": url})

    # videopress 嵌入
    for match in re.finditer(
        r'https://videopress\.com/v/(\w+)',
        html_content
    ):
        videos.append({"type": "videopress", "url": match.group(0)})

    # hana-flv-player
    for match in re.finditer(
        r'\[hana-flv-player\s+video="([^"]+)"',
        html_content
    ):
        videos.append({"type": "hana-flv", "url": match.group(1)})

    return videos


def build_video_url_map(xml_path: Path) -> dict:
    """
    建立 videos.files.wordpress.com URL -> 本地 wp-content 路径的映射。
    通过匹配文件名来关联。
    """
    url_map = {}

    # 从 XML 中提取所有 attachment 的 URL
    tree = ET.parse(xml_path)
    root = tree.getroot()
    channel = root.find("channel")

    local_mp4s = {}
    for item in channel.findall("item"):
        post_type = item.find("wp:post_type", NS)
        if post_type is not None and post_type.text == "attachment":
            att_url_el = item.find("wp:attachment_url", NS)
            if att_url_el is not None and att_url_el.text:
                att_url = att_url_el.text
                if att_url.endswith(".mp4"):
                    filename = att_url.rsplit("/", 1)[-1]
                    local_path = att_url.replace("https://wuwufu.com/", "")
                    local_mp4s[filename] = local_path

    # 扫描 videos.files.wordpress.com URL 的文件名，匹配到本地路径
    # videos.files.wordpress.com URL 格式: .../hash/filename.mp4
    # wp-content/uploads URL 格式: .../YYYY/MM/filename.mp4
    # 文件名通常是一样的

    return local_mp4s


def find_local_path_for_video(video_url: str, local_mp4s: dict) -> str | None:
    """将视频 URL 映射到本地路径。"""
    filename = video_url.rsplit("/", 1)[-1]
    # 去掉查询参数
    filename = filename.split("?")[0]

    if filename in local_mp4s:
        return "/" + local_mp4s[filename]

    # 尝试不带后缀数字匹配
    # 例如 copy_xxx-1.mp4 可能对应 copy_xxx.mp4
    return None


def build_post_index() -> dict:
    """建立 post_id -> 文件路径 的索引。"""
    index = {}
    for filepath in CONTENT_DIR.glob("*.md"):
        content = filepath.read_text(encoding="utf-8")
        match = re.search(r'^post_id:\s*(\d+)', content, re.MULTILINE)
        if match:
            index[match.group(1)] = filepath
    return index


def generate_video_html(local_path: str) -> str:
    """生成本地视频的 HTML 标签。"""
    return f'\n<video controls width="100%"><source src="{local_path}" type="video/mp4"></video>\n'


def main():
    dry_run = "--dry-run" in sys.argv

    xml_path = find_xml_file()
    print(f"XML 文件: {xml_path}")

    # 建立索引
    print("建立文章索引...")
    post_index = build_post_index()
    print(f"  索引了 {len(post_index)} 篇文章")

    print("建立视频 URL 映射...")
    local_mp4s = build_video_url_map(xml_path)
    print(f"  找到 {len(local_mp4s)} 个本地 MP4")

    # 解析 XML，逐篇处理
    print("扫描 XML 中的视频...")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    channel = root.find("channel")

    total_posts = 0
    total_videos = 0
    restored = 0
    not_found = 0
    no_local = 0

    for item in channel.findall("item"):
        post_type = item.find("wp:post_type", NS)
        if post_type is None or post_type.text != "post":
            continue

        content_el = item.find("content:encoded", NS)
        if content_el is None or not content_el.text:
            continue

        videos = extract_videos_from_html(content_el.text)
        if not videos:
            continue

        post_id_el = item.find("wp:post_id", NS)
        title_el = item.find("title")
        post_id = post_id_el.text if post_id_el is not None else "?"
        title = title_el.text if title_el is not None else "?"

        total_posts += 1
        total_videos += len(videos)

        md_file = post_index.get(post_id)
        if not md_file:
            not_found += 1
            print(f"  未找到文章: post_id={post_id}, title={title}")
            continue

        # 检查文章是否已有视频标签（避免重复）
        md_content = md_file.read_text(encoding="utf-8")
        if "<video" in md_content:
            continue

        # 生成视频 HTML 并追加
        video_html_parts = []
        for v in videos:
            if v["type"] in ("wp-block-video", "video-tag"):
                local_path = find_local_path_for_video(v["url"], local_mp4s)
                if local_path:
                    video_html_parts.append(generate_video_html(local_path))
                else:
                    # 保留原始 URL 作为降级
                    video_html_parts.append(generate_video_html(v["url"]))
                    no_local += 1
            elif v["type"] == "videopress":
                video_html_parts.append(f'\n[VideoPress: {v["url"]}]({v["url"]})\n')
            elif v["type"] == "hana-flv":
                local_path = find_local_path_for_video(v["url"], local_mp4s)
                if local_path:
                    video_html_parts.append(generate_video_html(local_path))
                else:
                    video_html_parts.append(generate_video_html(v["url"]))

        if video_html_parts and not dry_run:
            # 在正文末尾（评论区之前）插入视频
            if "\n---\n\n## 评论" in md_content:
                insert_point = md_content.index("\n---\n\n## 评论")
                new_content = md_content[:insert_point] + "\n".join(video_html_parts) + md_content[insert_point:]
            else:
                new_content = md_content + "\n".join(video_html_parts)
            md_file.write_text(new_content, encoding="utf-8")

        restored += 1
        print(f"  恢复: {title} ({len(videos)} 个视频)")

    print(f"\n完成:")
    print(f"  含视频的文章: {total_posts} 篇，共 {total_videos} 个视频")
    print(f"  已恢复: {restored} 篇")
    print(f"  未找到对应文章: {not_found} 篇")
    print(f"  无本地路径（保留远程 URL）: {no_local} 个")
    if dry_run:
        print("（dry-run 模式）")


if __name__ == "__main__":
    main()
