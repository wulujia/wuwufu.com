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

# 给每篇文章 frontmatter 加 WP 老 slug 的 aliases（一次性，幂等）
node scripts/add_wp_aliases.mjs

# 生成 _redirects（处理 aliases 覆盖不到的老链接：feed/category/archive 等）
node scripts/generate_redirects.mjs

# 本地完整构建验证
hugo --gc --minify
```

- 构建会生成 `/robots.txt`、`/sitemap.xml`、`/llms.txt`、`/llms-full.txt`。
- `/comments/` 和 `/posts/` 是低价值聚合页，保留访问，但 `noindex, follow`，且不进 sitemap。
- Cloudflare 如果启用 Managed robots.txt，会在站点 robots 前插入 AI crawler 的 `Disallow`；做 GEO 时需在 Cloudflare 里同步放行。
- **WP 老链接接管分两层**（CF Pages 免费版 `_redirects` 限 100 条规则，785 篇文章超额）：
  1. **每篇文章 frontmatter 的 `aliases:`** 接 `/<old-slug>/` → 文章 permalink。Hugo 把每条 alias 渲染成独立的 `<old-slug>/index.html`（meta-refresh），不占 `_redirects` 配额。重新导入或 slug 结构变化后跑一次 `add_wp_aliases.mjs`。
  2. **`static/_redirects`** 处理 alias 覆盖不到的：`/feed/`、`/category/X/`、`/2018/10/` 月度归档、`/钢光纪念相册-3/` WP 重复后缀。共 ~16 条规则，远低于 100 上限。GSC 又报新的归档或重复后缀时，编辑 `scripts/generate_redirects.mjs` 的 BODY 加一行重跑。

## 迁移记录

- 内容：wp2hugo 从 WXR XML 导出转换
- 评论：REST API 抓取，静态 HTML 嵌入到每篇文章末尾
- 视频：78 个 MP4 下载后去重 + HEVC 压缩，从 10.1GB 压到 587MB
- 风格：PaperMod 基础上覆盖布局，模仿 Twenty Seventeen 的头图版式
