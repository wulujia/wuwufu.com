# wuwufu.com SEO/GEO Findings

## 2026-05-02

- Cloudflare 页面抓取放行已生效：`GPTBot/1.0`、`ClaudeBot`、`anthropic-ai`、`PerplexityBot`、`Google-Extended`、`CCBot`、`Bytespider` 访问首页均返回 200 和完整 HTML。
- 但线上 `robots.txt` 仍有 Cloudflare Managed robots.txt 插入的 AI crawler `Disallow`，包括 GPTBot、ClaudeBot、Bytespider、CCBot 等；这会让遵守 robots 的 LLM 爬虫不抓站点。
- 当前仓库构建不会生成 `robots.txt`，因为 `hugo.toml` 的 `outputs.home` 只包含 `HTML/RSS/JSON`。
- 线上 `/llms.txt` 和 `/llms-full.txt` 目前是 404。
- 线上 `https://www.wuwufu.com/` 返回 200，canonical 指向 apex，但没有 301 归一。
- 内容规模：`content/posts` 下 785 篇文章；所有文章都有 categories；没有文章自带 `description` 或 `summary`。
- 媒体规模：空 alt Markdown 图片约 1073 个，空 alt figure shortcode 约 31 个，raw video 标签约 54 个，WordPress 外链图片约 185 个。
- 构建产物里存在约 78 个 `wordCount=0` 页面，主要是纯图片/视频文章；模板需要 description fallback。
- `/comments/` 页面约 533KB，是评论聚合页；SEO 价值低，应 noindex。
- 已新增模板兜底：`seo_description.html`、`seo_robots.html`、自定义 head、OG、Twitter Card、Schema、sitemap、robots、llms。
- 内容批处理更新 788 个文件：785 篇 posts + 3 个顶层内容页，补 description、lastmod、images，并给 raw video/img 加爬虫/性能属性。
- 最终本地验证：Hugo 构建成功；1057 个内容 HTML 中 H1 异常 0、description 缺失 0、canonical 缺失 0、robots meta 缺失 0、图片 alt 缺失 0；JSON-LD 1651 段，解析失败 0。
- 本地 `/sitemap.xml` 输出 798 个 URL，已排除 `/comments/` 与 `/posts/`；`/llms.txt` 811 行，`/llms-full.txt` 1,371,078 bytes。
