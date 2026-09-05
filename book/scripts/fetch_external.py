#!/usr/bin/env python3
"""Download every image the posts still reference on 55fu.wordpress.com into book/images/external/.
The ?w= size parameter is dropped so the original upload (up to 2000 px) is fetched.
File name = upload path with slashes turned into underscores, e.g. 2025_07_img_1604.jpg."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "book/images/external"
OUT.mkdir(parents=True, exist_ok=True)
PREFIX = "https://55fu.wordpress.com/wp-content/uploads/"

urls = set()
for p in (ROOT / "content/posts").glob("*.md"):
    urls.update(re.findall(r'https://55fu\.wordpress\.com/wp-content/uploads/[^ )"?]+', p.read_text(encoding="utf-8")))
(OUT / "urls.txt").write_text("\n".join(sorted(urls)) + "\n")
missing = [u for u in sorted(urls) if not (OUT / u[len(PREFIX):].replace("/", "_")).exists()]
print(f"{len(urls)} urls, {len(missing)} to fetch")
for u in missing:
    dest = OUT / u[len(PREFIX):].replace("/", "_")
    subprocess.run(["curl", "-sL", "--max-time", "60", u, "-o", str(dest)], check=False)
    print("fetched", dest.name, dest.stat().st_size if dest.exists() else "FAILED")
