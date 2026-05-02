# wuwufu.com

五福在家 自得其乐 —— 从 WordPress.com 迁移到 Hugo 的静态归档站点。

- 标语：时间不能倒流 但回忆的感觉尚有
- 原站：https://wuwufu.com（原 WordPress.com 托管）
- 785 篇文章（2005-2025），11 个分类，591 条评论

## 本地开发

```bash
# 克隆（含 PaperMod 主题 submodule）
git clone --recursive https://github.com/wulujia/wuwufu.com.git
cd wuwufu.com

# 本地预览
hugo server
# 打开 http://localhost:1313/
```

## 部署（Cloudflare Pages）

1. Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git
2. 选择 `wulujia/wuwufu.com` 仓库
3. 构建设置：
   - Framework preset: `Hugo`
   - Build command: `hugo --gc --minify`
   - Build output directory: `public`
4. 保存并部署

## 目录结构

- `content/posts/` — 785 篇文章 Markdown
- `static/wp-content/uploads/` — 图片和视频（原 WordPress 路径结构）
- `static/images/` — 站点 logo、header 背景图
- `themes/PaperMod/` — Hugo 主题（git submodule）
- `layouts/` — 主题覆盖（自定义 header、list 模板）
- `assets/css/extended/custom.css` — Twenty Seventeen 风格定制
- `scripts/` — 迁移脚本与 SEO/GEO 维护脚本

## SEO/GEO 维护

```bash
# 批量补齐文章 description / lastmod / images，以及 raw img/video 属性
node scripts/seo_enrich_content.mjs

# 本地完整构建验证
hugo --gc --minify
```

- 构建会生成 `/robots.txt`、`/sitemap.xml`、`/llms.txt`、`/llms-full.txt`。
- `/comments/` 和 `/posts/` 是低价值聚合页，保留访问，但 `noindex, follow`，且不进 sitemap。
- Cloudflare 如果启用 Managed robots.txt，会在站点 robots 前插入 AI crawler 的 `Disallow`；做 GEO 时需在 Cloudflare 里同步放行。

## 迁移记录

- 内容：wp2hugo 从 WXR XML 导出转换
- 评论：REST API 抓取，静态 HTML 嵌入到每篇文章末尾
- 视频：78 个 MP4 下载后去重 + HEVC 压缩，从 10.1GB 压到 587MB
- 风格：PaperMod 基础上覆盖布局，模仿 Twenty Seventeen 的头图版式
