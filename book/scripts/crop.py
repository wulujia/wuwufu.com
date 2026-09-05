#!/usr/bin/env python3
"""Crop single pictures out of the 2025 phone collages. Boxes are (left, top, right, bottom) in px."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / "book/images/external"
OUT = ROOT / "book/images/crops"

CROPS = {
    # 1953 self-portrait, from 《少年自画像》(2025-07-12) collage
    "self-portrait-1953.jpg": ("2025_07_img_1604.jpg", (355, 630, 970, 1355)),
}
LOCAL_CROPS = {
    # 吴鲁加's signature, right third of 签名设计（35）second image
    "signature-wulujia.jpg": ("static/wp-content/uploads/2024/05/11652-q-m2.jpg", (427, 0, 640, 267)),
}

OUT.mkdir(parents=True, exist_ok=True)
for name, (src, box) in CROPS.items():
    with Image.open(EXT / src) as im:
        im.crop(box).save(OUT / name, quality=95)
        print(name, im.crop(box).size)
for name, (src, box) in LOCAL_CROPS.items():
    with Image.open(ROOT / src) as im:
        im.crop(box).save(OUT / name, quality=95)
        print(name, im.crop(box).size)
