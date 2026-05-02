# wuwufu.com SEO/GEO Progress

## 2026-05-02

- 复测 Cloudflare LLM 爬虫放行：已通过。
- 建立全站处理计划文件。
- Phase 1 完成：站点级 SEO/GEO 模板与输出已添加。
- Phase 2 完成：运行 `node scripts/seo_enrich_content.mjs`，更新 788 个内容文件。
- Phase 3 完成：`/comments/` 与 `/posts/` 设置 `noindex, follow`，并从 sitemap 排除。
- Phase 4 完成：本地完整构建通过；1057 个内容 HTML 的 H1、description、canonical、robots、图片 alt 检查均通过；1651 段 JSON-LD 解析失败 0。
- Phase 5 完成：新增 `20260502-seo-geo-changelog.md`，README 增加 SEO/GEO 维护说明。
- 线上复测：AI bot 直接抓首页已返回 200 与完整 HTML；但 Cloudflare 线上 `robots.txt` 仍有 Managed robots 的 AI crawler `Disallow`，需在 Cloudflare 控制台处理。
