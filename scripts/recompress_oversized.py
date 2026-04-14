#!/usr/bin/env python3
"""
针对超过 Cloudflare Pages 25MB 单文件上限的视频做精确码率控制。
目标输出 < 22MB（留 3MB buffer）。
"""

import json
import subprocess
import sys
from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"
TARGET_SIZE_MB = 22  # 留 buffer
AUDIO_BITRATE_KBPS = 96  # 降低音频码率给视频让空间

# 超过 25MB 的 5 个文件
OVERSIZED = [
    "copy_5dc12165-b49e-4473-abb0-cc6bb564083c.mp4",
    "copy_62fbcba5-170b-4d17-a59a-c9fa8a48b89b-1.mp4",
    "copy_dc8f7703-b38e-4bd0-8851-510a54c3373b-21.mp4",
    "copy_32fe9577-b80d-4ce7-b141-f66f3ba26cb2-2.mp4",
    "copy_3d7212e6-1f59-4452-afd8-19d984cbafad.mp4",
]


def probe_duration(filepath: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(filepath)],
        capture_output=True, text=True, timeout=30,
    )
    return float(r.stdout.strip())


def compress(src: Path, target_video_kbps: int) -> bool:
    """单遍压缩到指定视频码率。"""
    tmp = src.with_suffix(".recompress.mp4")
    r = subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-c:v", "libx265",
            "-preset", "slow",   # 慢一点但压缩率更高
            "-b:v", f"{target_video_kbps}k",
            "-maxrate", f"{int(target_video_kbps * 1.3)}k",
            "-bufsize", f"{target_video_kbps * 2}k",
            "-c:a", "aac", "-b:a", f"{AUDIO_BITRATE_KBPS}k",
            "-tag:v", "hvc1",
            "-movflags", "+faststart",
            str(tmp),
        ],
        capture_output=True, text=True, timeout=900,
    )
    if r.returncode != 0:
        if tmp.exists():
            tmp.unlink()
        print(f"    ffmpeg 错误: {r.stderr[-500:]}")
        return False

    tmp.replace(src)
    return True


def main():
    # 收集文件信息
    files = []
    for name in OVERSIZED:
        matches = list(STATIC_DIR.rglob(name))
        if not matches:
            print(f"找不到: {name}")
            continue
        f = matches[0]
        dur = probe_duration(f)
        size_mb = f.stat().st_size / 1024 / 1024
        files.append({"path": f, "name": name, "duration": dur, "size_mb": size_mb})

    # 逐个压缩
    print(f"目标输出: < {TARGET_SIZE_MB}MB\n")
    for i, info in enumerate(files, 1):
        dur = info["duration"]
        # 计算目标视频码率（总码率 - 音频码率）
        target_total_kbps = TARGET_SIZE_MB * 8 * 1024 / dur
        target_video_kbps = int(target_total_kbps - AUDIO_BITRATE_KBPS)

        print(f"[{i}/{len(files)}] {info['name']}")
        print(f"  原始: {info['size_mb']:.1f}MB, 时长 {int(dur//60)}:{int(dur%60):02d}")
        print(f"  目标视频码率: {target_video_kbps}kbps", end=" ... ", flush=True)

        if compress(info["path"], target_video_kbps):
            new_size = info["path"].stat().st_size / 1024 / 1024
            print(f"完成: {new_size:.1f}MB")
        else:
            print("失败")

    # 汇总
    print(f"\n=== 最终结果 ===")
    for info in files:
        new_size = info["path"].stat().st_size / 1024 / 1024
        status = "OK" if new_size < 25 else "仍超限"
        print(f"  [{status}] {info['name']}: {info['size_mb']:.1f}MB -> {new_size:.1f}MB")


if __name__ == "__main__":
    main()
