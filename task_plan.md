# wuwufu.com SEO/GEO 全站处理计划

## Goal

把 wuwufu.com 从“可访问的 Hugo 归档站”处理成“全站可爬、可索引、可被 LLM 读取、元数据完整、媒体更友好”的静态站。

## Phases

- [x] Phase 0: 复测 Cloudflare 爬虫放行状态
- [x] Phase 1: 建立站点级 SEO/GEO 模板兜底
- [x] Phase 2: 批量补齐 785 篇文章的 metadata 与媒体属性
- [x] Phase 3: 控制索引与 sitemap，只提交规范、可索引 URL
- [x] Phase 4: 构建验证、爬虫验证、SEO 结果统计
- [x] Phase 5: 记录 changelog/log

## Decisions

- 不只挑精选页；所有文章都要有可用 description、lastmod、图片 alt fallback、视频 preload 策略。
- `/comments/` 和 `/posts/` 是聚合/重复页面，保留给用户访问，但应 `noindex, follow`，并从 sitemap 排除。
- GEO 入口覆盖全站：生成 `/llms.txt` 和 `/llms-full.txt`，但排除 noindex 页面与评论归档。
- 用 `layouts/` 覆盖 PaperMod，不改 theme submodule。
- 内容批处理脚本保留在 `scripts/seo_enrich_content.mjs`，后续可重复运行。

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
| PageSpeed API quota exceeded | 尝试跑 PSI | 改用本地构建、curl、HTML 检查；CWV 需 GSC 后续确认 |
| Cloudflare robots 仍显示 AI crawler Disallow | 复测线上 `/robots.txt` | 仓库已生成允许版 robots；Cloudflare Managed robots.txt 会前置管理内容，需在 Cloudflare 关闭或调整 |
