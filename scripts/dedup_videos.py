#!/usr/bin/env python3
"""
视频去重和清理：
1. 将未被文章引用的 MP4 移到 quarantine_unreferenced/
2. 在被引用的文件中，识别内容重复（相同时长+分辨率），保留被引用的那个，
   将多余的移到 quarantine_duplicates/
3. 生成清单文件说明每个被移动文件的情况
"""

import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"
EXPORT_DIR = Path(__file__).parent.parent / "export"
CONTENT_DIR = Path(__file__).parent.parent / "content" / "posts"
Q_UNREF = EXPORT_DIR / "quarantine_unreferenced"
Q_DUP = EXPORT_DIR / "quarantine_duplicates"
XML_PATH = next(EXPORT_DIR.rglob("*.xml"))

NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp": "http://wordpress.org/export/1.2/",
}


def probe_duration_res(filepath: Path) -> tuple:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(filepath)],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(r.stdout)
        dur = round(float(data.get("format", {}).get("duration", 0)), 1)
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                return (dur, int(s.get("width", 0)), int(s.get("height", 0)))
        return (dur, 0, 0)
    except Exception:
        return (0, 0, 0)


def get_referenced_filenames() -> set:
    """从 XML 文章正文中提取所有被引用的视频文件名。"""
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    channel = root.find("channel")

    post_contents = []
    for item in channel.findall("item"):
        pt = item.find("wp:post_type", NS)
        if pt is not None and pt.text == "post":
            ce = item.find("content:encoded", NS)
            if ce is not None and ce.text:
                post_contents.append(ce.text)

    all_text = " ".join(post_contents)

    referenced = set()
    # 直接文件名引用
    for m in re.finditer(r'[\w\-]+\.mp4', all_text):
        referenced.add(m.group(0))
    # CDN URL 引用
    for m in re.finditer(r'videos\.files\.wordpress\.com/\w+/([\w\-\.]+\.mp4)', all_text):
        referenced.add(m.group(1))

    return referenced


def main():
    local_mp4s = {f.name: f for f in STATIC_DIR.rglob("*.mp4")}
    referenced = get_referenced_filenames()

    print(f"本地 MP4: {len(local_mp4s)} 个")
    print(f"被文章引用: {len(referenced & set(local_mp4s.keys()))} 个")

    manifest_unref = []
    manifest_dup = []

    # === 步骤 1：移走未引用的文件 ===
    print("\n=== 步骤 1：移走未被文章引用的文件 ===")
    unreferenced = set(local_mp4s.keys()) - referenced
    unref_size = 0
    for name in sorted(unreferenced):
        src = local_mp4s[name]
        dst = Q_UNREF / name
        size_mb = src.stat().st_size / 1024 / 1024
        unref_size += size_mb
        print(f"  移走: {name} ({size_mb:.1f}MB)")
        shutil.move(str(src), str(dst))
        manifest_unref.append(f"{name}\t{size_mb:.1f}MB\t未被任何文章正文引用，仅存在于 WordPress 附件库")

    print(f"  共移走 {len(unreferenced)} 个，{unref_size:.0f}MB")

    # 写清单
    (Q_UNREF / "MANIFEST.txt").write_text(
        "# 未被引用的视频文件\n"
        "# 这些文件存在于 WordPress 附件库但未被任何文章正文引用\n"
        "# 如果确认不需要，可以安全删除此文件夹\n\n"
        + "\n".join(manifest_unref),
        encoding="utf-8",
    )

    # === 步骤 2：在剩余文件中去重 ===
    print("\n=== 步骤 2：在被引用的文件中去重 ===")
    remaining = {f.name: f for f in STATIC_DIR.rglob("*.mp4")}

    # 获取每个文件的时长和分辨率
    file_info = {}
    for name, path in remaining.items():
        info = probe_duration_res(path)
        file_info[name] = info

    # 按 (时长, 分辨率) 分组
    groups = defaultdict(list)
    for name, info in file_info.items():
        if info != (0, 0, 0):
            groups[info].append(name)

    dup_size = 0
    for key, names in sorted(groups.items(), key=lambda x: -len(x[1])):
        if len(names) <= 1:
            continue

        # 保留被引用的那个；如果都被引用，保留第一个
        keep = None
        for n in names:
            if n in referenced:
                keep = n
                break
        if not keep:
            keep = names[0]

        dur_str = f"{int(key[0]//60)}:{int(key[0]%60):02d}"
        res_str = f"{key[1]}x{key[2]}"
        print(f"\n  重复组: 时长={dur_str}, 分辨率={res_str}")
        print(f"    保留: {keep}")

        for name in names:
            if name == keep:
                continue
            src = remaining[name]
            dst = Q_DUP / name
            size_mb = src.stat().st_size / 1024 / 1024
            dup_size += size_mb
            print(f"    移走: {name} ({size_mb:.1f}MB) - 与 {keep} 内容重复")
            shutil.move(str(src), str(dst))
            manifest_dup.append(f"{name}\t{size_mb:.1f}MB\t与 {keep} 内容重复（时长={dur_str}, 分辨率={res_str}）")

    print(f"\n  共移走 {len(manifest_dup)} 个重复文件，{dup_size:.0f}MB")

    # 写清单
    (Q_DUP / "MANIFEST.txt").write_text(
        "# 重复的视频文件\n"
        "# 这些文件与保留的文件具有相同的时长和分辨率，属于重复上传\n"
        "# 如果确认不需要，可以安全删除此文件夹\n\n"
        + "\n".join(manifest_dup),
        encoding="utf-8",
    )

    # === 汇总 ===
    final = list(STATIC_DIR.rglob("*.mp4"))
    final_size = sum(f.stat().st_size for f in final) / 1024 / 1024
    print(f"\n=== 汇总 ===")
    print(f"  移走未引用: {len(unreferenced)} 个, {unref_size:.0f}MB")
    print(f"  移走重复: {len(manifest_dup)} 个, {dup_size:.0f}MB")
    print(f"  剩余视频: {len(final)} 个, {final_size:.0f}MB")


if __name__ == "__main__":
    main()
