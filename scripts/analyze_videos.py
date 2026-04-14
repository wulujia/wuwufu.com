#!/usr/bin/env python3
"""
分析所有视频文件：大小、时长、分辨率、编码、比特率。
识别内容重复（相同时长+分辨率）和压缩空间。
"""

import json
import subprocess
from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def probe(filepath: Path) -> dict:
    """用 ffprobe 获取视频信息。"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(filepath)],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        video_stream = None
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                video_stream = s
                break

        duration = float(fmt.get("duration", 0))
        size = int(fmt.get("size", 0))
        bitrate = int(fmt.get("bit_rate", 0))

        width = int(video_stream.get("width", 0)) if video_stream else 0
        height = int(video_stream.get("height", 0)) if video_stream else 0
        codec = video_stream.get("codec_name", "?") if video_stream else "?"

        return {
            "duration": duration,
            "size": size,
            "bitrate": bitrate,
            "width": width,
            "height": height,
            "codec": codec,
            "size_mb": size / 1024 / 1024,
        }
    except Exception as e:
        return {"error": str(e), "size": filepath.stat().st_size, "size_mb": filepath.stat().st_size / 1024 / 1024}


def format_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def main():
    mp4_files = sorted(STATIC_DIR.rglob("*.mp4"), key=lambda f: f.stat().st_size, reverse=True)
    print(f"共 {len(mp4_files)} 个 MP4 文件\n")

    results = []
    for f in mp4_files:
        info = probe(f)
        info["path"] = str(f)
        info["name"] = f.name
        results.append(info)

    # 按大小排列输出
    print(f"{'大小':>8} {'时长':>8} {'分辨率':>12} {'编码':>6} {'比特率':>10} 文件名")
    print("-" * 90)
    for r in results:
        dur = format_duration(r.get("duration", 0))
        res = f"{r.get('width', '?')}x{r.get('height', '?')}"
        codec = r.get("codec", "?")
        br = r.get("bitrate", 0)
        br_str = f"{br/1000:.0f}kbps" if br else "?"
        print(f"{r['size_mb']:7.1f}M {dur:>8} {res:>12} {codec:>6} {br_str:>10} {r['name']}")

    # 识别内容重复（相同时长+分辨率）
    print("\n\n=== 疑似内容重复（相同时长 + 分辨率）===")
    from collections import defaultdict
    groups = defaultdict(list)
    for r in results:
        key = (round(r.get("duration", 0), 1), r.get("width", 0), r.get("height", 0))
        if key != (0, 0, 0):
            groups[key].append(r)

    dup_size = 0
    for key, items in sorted(groups.items(), key=lambda x: -sum(i["size"] for i in x[1])):
        if len(items) > 1:
            dur_str = format_duration(key[0])
            res_str = f"{key[1]}x{key[2]}"
            print(f"\n  时长={dur_str}, 分辨率={res_str}, 共 {len(items)} 个文件:")
            for i, r in enumerate(items):
                tag = " <-- 保留" if i == 0 else " <-- 可删除"
                print(f"    {r['size_mb']:7.1f}M  {r['name']}{tag}")
                if i > 0:
                    dup_size += r["size"]
    print(f"\n  可通过去重节省: {dup_size/1024/1024:.0f}MB")

    # 压缩空间分析
    print("\n\n=== 压缩潜力分析 ===")
    high_bitrate = [r for r in results if r.get("bitrate", 0) > 5_000_000]  # > 5Mbps
    large_res = [r for r in results if r.get("width", 0) > 1080 or r.get("height", 0) > 1080]
    hevc_possible = [r for r in results if r.get("codec") != "hevc" and r.get("size", 0) > 50_000_000]

    print(f"  高比特率（>5Mbps）: {len(high_bitrate)} 个文件")
    for r in high_bitrate[:10]:
        print(f"    {r['size_mb']:7.1f}M  {r.get('bitrate',0)/1000:.0f}kbps  {r['name']}")

    print(f"\n  高分辨率（>1080p）: {len(large_res)} 个文件")
    print(f"\n  可转 HEVC 压缩（>50MB 且非 HEVC）: {len(hevc_possible)} 个")
    potential_save = sum(r["size"] * 0.5 for r in hevc_possible)  # HEVC 大约省 50%
    print(f"  转 HEVC 预估可节省: {potential_save/1024/1024:.0f}MB")

    total = sum(r["size"] for r in results)
    print(f"\n总计: {total/1024/1024:.0f}MB ({total/1024/1024/1024:.1f}GB)")


if __name__ == "__main__":
    main()
