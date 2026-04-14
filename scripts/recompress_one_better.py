#!/usr/bin/env python3
"""
单独对 8 分钟视频做更好的压缩：
- 从 826MB 原始 h264 直接编码（避免多次转码损失）
- 降分辨率到短边 720（1080 -> 720，像素数减少 55%）
- 2-pass HEVC 编码精确控制大小到 23MB
- slow preset 追求压缩效率
"""

import subprocess
from pathlib import Path

ORIGINAL = Path(__file__).parent.parent / "export/originals_before_compress/copy_dc8f7703-b38e-4bd0-8851-510a54c3373b-21.mp4"
TARGET = Path(__file__).parent.parent / "static/wp-content/uploads/2025/03/copy_dc8f7703-b38e-4bd0-8851-510a54c3373b-21.mp4"
LOG_PREFIX = "/tmp/ffmpeg2pass"

TARGET_SIZE_MB = 23
AUDIO_KBPS = 96
DURATION_S = 533  # 8:53


def main():
    target_total_kbps = TARGET_SIZE_MB * 8 * 1024 / DURATION_S
    target_video_kbps = int(target_total_kbps - AUDIO_KBPS)
    print(f"从: {ORIGINAL}")
    print(f"到: {TARGET}")
    print(f"目标大小: {TARGET_SIZE_MB}MB")
    print(f"视频码率: {target_video_kbps}kbps (audio {AUDIO_KBPS}kbps)")
    print()

    # scale='min(720,iw)':'min(720,ih)':force_original_aspect_ratio=decrease
    # 保持比例缩放到短边 <= 720
    scale = "scale='if(gt(iw,ih),-2,720)':'if(gt(iw,ih),720,-2)'"

    # Pass 1
    print("Pass 1: 分析...", flush=True)
    r = subprocess.run([
        "ffmpeg", "-y", "-i", str(ORIGINAL),
        "-vf", scale,
        "-c:v", "libx265",
        "-preset", "slow",
        "-b:v", f"{target_video_kbps}k",
        "-x265-params", f"pass=1:log-level=error",
        "-an",
        "-f", "null", "/dev/null",
    ], capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        print(f"  失败: {r.stderr[-500:]}")
        return

    # Pass 2
    print("Pass 2: 编码...", flush=True)
    r = subprocess.run([
        "ffmpeg", "-y", "-i", str(ORIGINAL),
        "-vf", scale,
        "-c:v", "libx265",
        "-preset", "slow",
        "-b:v", f"{target_video_kbps}k",
        "-x265-params", f"pass=2:log-level=error",
        "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k",
        "-tag:v", "hvc1",
        "-movflags", "+faststart",
        str(TARGET),
    ], capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        print(f"  失败: {r.stderr[-500:]}")
        return

    new_size = TARGET.stat().st_size / 1024 / 1024
    print(f"\n完成: {new_size:.1f}MB")

    # 检查分辨率
    r = subprocess.run([
        "ffprobe", "-v", "quiet", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,bit_rate",
        "-of", "csv=p=0", str(TARGET),
    ], capture_output=True, text=True)
    print(f"输出信息: {r.stdout.strip()}")


if __name__ == "__main__":
    main()
