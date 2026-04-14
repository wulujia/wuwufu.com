# wuwufu.com

五福在家 自得其乐 —— 从 WordPress.com 迁移到 Hugo 的静态归档站点。

- 标语：时间不能倒流 但回忆的感觉尚有
- 原站：https://wuwufu.com（原 WordPress.com 托管）
- 786 篇文章（2005-2025），11 个分类，591 条评论

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
   - Environment variable: `HUGO_VERSION=0.155.1`
4. 保存并部署

## 目录结构

- `content/posts/` — 786 篇文章 Markdown
- `static/wp-content/uploads/` — 图片和视频（原 WordPress 路径结构）
- `static/images/` — 站点 logo、header 背景图
- `themes/PaperMod/` — Hugo 主题（git submodule）
- `layouts/` — 主题覆盖（自定义 header、list 模板）
- `assets/css/extended/custom.css` — Twenty Seventeen 风格定制
- `scripts/` — 迁移脚本（一次性使用，不影响站点）

## 迁移记录

- 内容：wp2hugo 从 WXR XML 导出转换
- 评论：REST API 抓取，静态 HTML 嵌入到每篇文章末尾
- 视频：78 个 MP4 下载后去重 + HEVC 压缩，从 10.1GB 压到 587MB
- 风格：PaperMod 基础上覆盖布局，模仿 Twenty Seventeen 的头图版式
