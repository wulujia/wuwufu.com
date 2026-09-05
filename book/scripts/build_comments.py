#!/usr/bin/env python3
"""Turn book/comments_select.yaml + comments_all.json into book/src/comments.json, sorted by date."""
import json
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
ALL = {c["id"]: c for c in json.loads((ROOT / "book/src/comments_all.json").read_text(encoding="utf-8"))}
SEL = yaml.safe_load((ROOT / "book/comments_select.yaml").read_text(encoding="utf-8"))

ALIAS = {"wlj": "吴鲁加", "wulujia": "吴鲁加", "wuyisi": "吴五福", "lilongyang": "李龙洋", "淡如雏菊": "卢晓华（淡如雏菊）", "littlesky": "黄天赠（littlesky）"}


def fmt_date(d):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(d))
    return f"{int(m.group(1))} 年 {int(m.group(2))} 月 {int(m.group(3))} 日" if m else str(d)


out = []
for s in SEL:
    c = ALL[s["id"]]
    text = c["text"]
    if s.get("from"):
        i = text.find(s["from"])
        text = text[i:] if i >= 0 else text
    if s.get("to"):
        i = text.find(s["to"])
        text = text[:i] if i >= 0 else text
    text = re.sub(r"\s*\|\s*回复\s*\|\s*删除\s*\|\s*举报", "", text)
    text = re.sub(r"https?://\S+", "", text).strip()
    name = s.get("name") or c["name"]
    name = ALIAS.get(name, name)
    date = str(s.get("date") or c["date"])
    out.append({"name": name, "date": fmt_date(date), "sort": date, "post": c["post"], "text": text})
out.sort(key=lambda x: x["sort"])
(ROOT / "book/src/comments.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "comments selected")
