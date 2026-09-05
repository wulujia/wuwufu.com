# 2026-09-05 成书工程启动

把博客印成一本书送给父亲。计划见 `~/.claude/plans/blog-eager-reddy.md`。今天做了：

- 读完全站 785 篇，定下书型：他自己的话，按人生阶段分六部，一卷精装约 300 页，全程保密，尽快印。
- 新建 `book/` 目录，Hugo 不构建它。`manifest.yaml` 列出 157 篇选篇（含必选、备选）、标题覆盖、创作年份、错字修正。
- `scripts/build_manuscript.py`：把选篇转成 `src/manuscript.json`。只做三件事：清 WordPress 残留、半角标点换全角、按 manifest 改错字。诗按行排，散文里粘成一行的诗按空格拆行。朋友圈回填帖的日期从正文戳里取。
- `scripts/extract_comments.py` 和 `build_comments.py`：从 589 条评论里抽出真名和日期（2011 年搬家时粘贴的评论外层作者全是 wuwufu），按 `comments_select.yaml` 选 59 条进附录。
- `scripts/crop.py`：从 2025 年翻拍的拼图里裁出 1953 年自画像。
- 外链图片：55fu.wordpress.com 上的 185 张全部下载到 `book/images/external/`，长边中位数 1706 px。
- Typst 0.15 装在 `~/.local/bin`。版式在 `src/template.typ`，16 开，Noto Serif CJK 13 pt。
- 附录做好：签名墙（44 幅签名拼图加吴鲁加的签名单放）、留言选 59 条按时间排、博客大事记。
- 第一版 PDF `book/out/book.pdf` 编译通过，281 页（含全部备选），15 MB。
- 序和编后记各留一个文件：`book/src/preface.typ`、`book/src/afterword.typ`，红字占位。

重新生成的命令：

```bash
python3 book/scripts/fetch_external.py     # 外链图（已下载，幂等）
python3 book/scripts/crop.py               # 自画像、儿子签名裁图
python3 book/scripts/build_manuscript.py   # 选篇 -> src/manuscript.json
python3 book/scripts/extract_comments.py && python3 book/scripts/build_comments.py
typst compile --root . book/src/main.typ book/out/book.pdf
```

待办：儿子的序和编后记；样书；备选取舍。
