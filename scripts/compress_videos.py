#!/usr/bin/env python3
"""
批量压缩视频：h264 -> HEVC (h265)，目标比特率 2Mbps。
原始文件备份到 export/originals/，压缩后替换原位置。
"""

import json
import subprocess
import sys
from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"
BACKUP_DIR = Path(__file__).parent.parent / "export" / "originals_before_compress"

TARGET_BITRATE = "2M"
MAX_BITRATE = "3M"


def probe(filepath: Path) -> dict:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(filepath)],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(r.stdout)
        fmt = data.get("format", {})
        bitrate = int(fmt.get("bit_rate", 0))
        size = int(fmt.get("size", 0))
        codec = "?"
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                codec = s.get("codec_name", "?")
                break
        return {"bitrate": bitrate, "size": size, "codec": codec}
    except Exception:
        return {"bitrate": 0, "size": 0, "codec": "?"}


def compress(src: Path, dst: Path) -> bool:
    """用 ffmpeg 压缩视频到 HEVC。"""
    try:
        r = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(src),
                "-c:v", "libx265",
                "-preset", "medium",
                "-b:v", TARGET_BITRATE,
                "-maxrate", MAX_BITRATE,
                "-bufsize", "4M",
                "-c:a", "aac", "-b:a", "128k",
                "-tag:v", "hvc1",  # 兼容 Safari
                "-movflags", "+faststart",
                str(dst),
            ],
            capture_output=True, text=True, timeout=600,
        )
        return r.returncode == 0
    except Exception as e:
        print(f"    错误: {e}")
        return False


def main():
    skip_small = "--skip-small" in sys.argv  # 跳过已经很小的文件

    mp4_files = sorted(STATIC_DIR.rglob("*.mp4"), key=lambda f: f.stat().st_size, reverse=True)
    print(f"共 {len(mp4_files)} 个视频待压缩\n")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    total_before = 0
    total_after = 0
    compressed = 0
    skipped = 0

    for i, filepath in enumerate(mp4_files, 1):
        info = probe(filepath)
        size_mb = info["size"] / 1024 / 1024
        bitrate_kbps = info["bitrate"] / 1000
        total_before += info["size"]

        # 跳过已经是 HEVC 或比特率已经很低的文件
        if info["codec"] == "hevc":
            print(f"[{i}/{len(mp4_files)}] 跳过（已是 HEVC）: {filepath.name}")
            total_after += info["size"]
            skipped += 1
            continue

        if skip_small and info["bitrate"] < 3_000_000 and info["size"] < 30_000_000:
            print(f"[{i}/{len(mp4_files)}] 跳过（已较小）: {filepath.name} ({size_mb:.1f}MB, {bitrate_kbps:.0f}kbps)")
            total_after += info["size"]
            skipped += 1
            continue

        print(f"[{i}/{len(mp4_files)}] 压缩: {filepath.name} ({size_mb:.1f}MB, {bitrate_kbps:.0f}kbps)...", end=" ", flush=True)

        # 备份原文件
        backup_path = BACKUP_DIR / filepath.name
        if not backup_path.exists():
            import shutil
            shutil.copy2(str(filepath), str(backup_path))

        # 压缩到临时文件
        tmp_path = filepath.with_suffix(".tmp.mp4")
        if compress(filepath, tmp_path):
            new_size = tmp_path.stat().st_size
            new_mb = new_size / 1024 / 1024
            ratio = new_size / info["size"] * 100 if info["size"] > 0 else 0

            if new_size < info["size"]:
                # 压缩有效，替换原文件
                tmp_path.replace(filepath)
                total_after += new_size
                compressed += 1
                print(f"{new_mb:.1f}MB ({ratio:.0f}%)")
            else:
                # 压缩后更大，保留原文件
                tmp_path.unlink()
                total_after += info["size"]
                skipped += 1
                print(f"跳过（压缩后更大: {new_mb:.1f}MB）")
        else:
            if tmp_path.exists():
                tmp_path.unlink()
            total_after += info["size"]
            print("失败")

    print(f"\n=== 完成 ===")
    print(f"  压缩: {compressed} 个")
    print(f"  跳过: {skipped} 个")
    print(f"  压缩前: {total_before/1024/1024:.0f}MB ({total_before/1024/1024/1024:.1f}GB)")
    print(f"  压缩后: {total_after/1024/1024:.0f}MB ({total_after/1024/1024/1024:.1f}GB)")
    print(f"  节省: {(total_before-total_after)/1024/1024:.0f}MB ({(1-total_after/total_before)*100:.0f}%)")
    print(f"\n  原始文件已备份到: {BACKUP_DIR}")


if __name__ == "__main__":
    main()
