#!/usr/bin/env python3
"""
用 CRF 质量模式迭代压缩：从质量好开始，不断提高 CRF 直到文件 < 23MB。
保持较高分辨率（900p 短边）。
"""

import subprocess
from pathlib import Path

ORIGINAL = Path(__file__).parent.parent / "export/originals_before_compress/copy_dc8f7703-b38e-4bd0-8851-510a54c3373b-21.mp4"
TARGET = Path(__file__).parent.parent / "static/wp-content/uploads/2025/03/copy_dc8f7703-b38e-4bd0-8851-510a54c3373b-21.mp4"
TMP = TARGET.with_suffix(".tmp.mp4")

MAX_SIZE_MB = 23
SHORT_EDGE = 900   # 短边最大 900（1080 -> 900，降约 17%）


def try_crf(crf: int) -> float:
    """返回压缩后大小 MB。"""
    scale = f"scale='if(gt(iw,ih),-2,{SHORT_EDGE})':'if(gt(iw,ih),{SHORT_EDGE},-2)'"
    r = subprocess.run([
        "ffmpeg", "-y", "-i", str(ORIGINAL),
        "-vf", scale,
        "-c:v", "libx265",
        "-preset", "slow",
        "-crf", str(crf),
        "-c:a", "aac", "-b:a", "96k",
        "-tag:v", "hvc1",
        "-movflags", "+faststart",
        str(TMP),
    ], capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        print(f"    ffmpeg 失败: {r.stderr[-400:]}")
        return 0
    return TMP.stat().st_size / 1024 / 1024


def main():
    print(f"短边目标: {SHORT_EDGE}px")
    print(f"最大输出: {MAX_SIZE_MB}MB\n")

    # 从 CRF 26 开始，如果太大就升高
    # HEVC CRF 参考：20=视觉无损, 24=高质量, 28=一般, 32=偏差
    crf = 26
    attempts = []
    while crf <= 36:
        print(f"尝试 CRF {crf}...", end=" ", flush=True)
        size_mb = try_crf(crf)
        print(f"{size_mb:.1f}MB")
        attempts.append((crf, size_mb))
        if size_mb <= MAX_SIZE_MB and size_mb > 0:
            break
        crf += 2

    # 取最接近但不超过 23MB 的最低 CRF（画质最好）
    valid = [(c, s) for c, s in attempts if s <= MAX_SIZE_MB and s > 0]
    if not valid:
        print("\n所有尝试都超过大小限制")
        return

    # 选最小 CRF（质量最好）的方案
    best_crf, best_size = min(valid, key=lambda x: x[0])
    print(f"\n最佳: CRF={best_crf}, 大小={best_size:.1f}MB")

    # 如果当前 tmp 不是最佳方案，重新生成
    if attempts[-1][0] != best_crf:
        print(f"重新生成最佳方案...")
        try_crf(best_crf)

    # 替换原文件
    TMP.replace(TARGET)
    print(f"\n输出: {TARGET}")
    print(f"大小: {TARGET.stat().st_size/1024/1024:.1f}MB")

    # 显示最终参数
    r = subprocess.run([
        "ffprobe", "-v", "quiet", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,bit_rate",
        "-of", "csv=p=0", str(TARGET),
    ], capture_output=True, text=True)
    print(f"视频流: {r.stdout.strip()}  (宽x高, 码率bps)")


if __name__ == "__main__":
    main()
