# 2026-05-02 SEO description wording 更新记录

## 已处理

- 调整文章 SEO description 的生成措辞，改为“发表的文章”。
- 调整 Hugo 运行时兜底 description，保持与生成脚本一致。
- 批量修正已生成的文章 description。

## 验证

- `node scripts/seo_enrich_content.mjs` 首次更新 195 个文章文件。
- `node scripts/seo_enrich_content.mjs` 二次运行更新 0 个文件，脚本幂等。
- 全站搜索旧措辞无匹配。
- `hugo --destination /tmp/wuwufu-public --cleanDestinationDir --minify` 构建成功，输出 820 pages。
