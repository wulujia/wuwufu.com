# 2026-05-02 SEO/GEO 全站处理记录

## 范围

按 `/Users/lucawu/Library/CloudStorage/Dropbox/marketing/seo/20260502-technical-seo-checklist.md` 与 `/Users/lucawu/Library/CloudStorage/Dropbox/marketing/seo/20260502-geo-best-practices.md`，对 wuwufu.com 做全站级处理，不只处理少数页面。

## 已处理

- 全站 head 覆盖：唯一 title、description、canonical、robots、OG、Twitter Card、JSON-LD。
- 首页、文章、分类、归档、404 保持唯一 H1；正文 Markdown 一级标题渲染为 H2。
- 首页和列表页改为摘要列表，不再把全文、视频、图片批量塞进列表页。
- 新增 `/robots.txt`，显式允许 Googlebot、Bingbot、GPTBot、ClaudeBot、anthropic-ai、PerplexityBot、Google-Extended、Bytespider、CCBot。
- 新增 `/sitemap.xml`，只输出规范、可索引页面，排除 `/comments/` 和 `/posts/`。
- 新增 `/llms.txt` 与 `/llms-full.txt`，提供 LLM 友好的全站入口。
- 批量补齐 785 篇文章的 `description`、`lastmod`，有图文章补 `images`。
- Markdown 图片、figure shortcode、raw img 均补 alt fallback；正文首图 eager + `fetchpriority="high"`，其余 lazy。
- raw video 增加 `preload="none"` 与 `playsinline`。
- `/comments/` 和 `/posts/` 设置 `noindex, follow`。
- 新增可重复运行脚本：`scripts/seo_enrich_content.mjs`。

## 验证

```bash
hugo --destination /tmp/wuwufu-public --cleanDestinationDir --minify
node scripts/seo_enrich_content.mjs
```

- Hugo 构建成功：819 pages，256 paginator pages，12 aliases。
- 内容 HTML：1057 个；自动重定向 HTML：12 个。
- 内容 HTML 检查：H1 异常 0，description 缺失 0，canonical 缺失 0，robots meta 缺失 0，图片 alt 缺失 0。
- JSON-LD：1651 段，解析失败 0。
- sitemap：798 个 URL，未包含 `/comments/` 或 `/posts/`。
- `/llms.txt`：811 行。
- `/llms-full.txt`：1,371,078 bytes。
- `node scripts/seo_enrich_content.mjs` 二次运行更新 0 个文件，脚本幂等。

## 线上复测

- `GPTBot/1.0`、`ClaudeBot`、`anthropic-ai`、`PerplexityBot`、`Google-Extended`、`Bytespider`、`CCBot` 请求 `https://wuwufu.com/` 均返回 200，且返回完整 HTML。
- 当前线上 `/llms.txt` 与 `/llms-full.txt` 仍是 404，需部署本次改动后生效。
- 当前线上 `robots.txt` 仍由 Cloudflare Managed robots.txt 插入 AI crawler `Disallow` 与 `Content-Signal: search=yes,ai-train=no`。Cloudflare 官方说明：开启 Managed robots.txt 时会把 Cloudflare 管理内容插到源站 robots 前面。参考：https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/

## 外部待处理

- Cloudflare：关闭或调整 Managed robots.txt / Instruct AI bot traffic with robots.txt，确认线上 `robots.txt` 不再出现 GPTBot、ClaudeBot、Bytespider、CCBot 等 `Disallow: /`。
- Cloudflare：把 `https://www.wuwufu.com/` 301 到 `https://wuwufu.com/`；当前线上是 200 + canonical，不如 301 干净。
- Search Console / Bing Webmaster：部署后提交新的 `/sitemap.xml`。
