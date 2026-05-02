#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const postsDir = path.join(root, "content", "posts");

function parseFrontMatter(text) {
  if (!text.startsWith("---\n")) return null;
  const end = text.indexOf("\n---", 4);
  if (end === -1) return null;
  return {
    frontMatter: text.slice(4, end),
    body: text.slice(end + 4),
  };
}

function getScalar(frontMatter, key) {
  const match = frontMatter.match(new RegExp(`^${key}:\\s*(.*)$`, "m"));
  if (!match) return "";
  return stripQuotes(match[1].trim());
}

function hasKey(frontMatter, key) {
  return new RegExp(`^${key}:`, "m").test(frontMatter);
}

function stripQuotes(value) {
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
}

function yamlString(value) {
  return `"${value.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

function getCategories(frontMatter) {
  const lines = frontMatter.split("\n");
  const categories = [];
  let inCategories = false;
  for (const line of lines) {
    if (/^categories:\s*$/.test(line)) {
      inCategories = true;
      continue;
    }
    if (inCategories) {
      const item = line.match(/^\s*-\s*(.+)\s*$/);
      if (item) {
        categories.push(stripQuotes(item[1].trim()));
        continue;
      }
      if (/^[A-Za-z_][A-Za-z0-9_-]*:/.test(line) || /^---/.test(line)) break;
    }
  }
  return categories;
}

function firstImage(body) {
  const markdown = body.match(/!\[[^\]]*]\(([^)]+)\)/);
  if (markdown) return markdown[1].trim();
  const linkedMarkdown = body.match(/\[!\[[^\]]*]\(([^)]+)\)]\([^)]+\)/);
  if (linkedMarkdown) return linkedMarkdown[1].trim();
  const figure = body.match(/{{<\s*figure[^>]*\bsrc="([^"]+)"/);
  if (figure) return figure[1].trim();
  const html = body.match(/<img\b[^>]*\bsrc="([^"]+)"/i);
  if (html) return html[1].trim();
  return "";
}

function plainText(body) {
  const main = body.split('<div class="static-comments">')[0];
  return main
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/{{<[^>]+>}}/g, " ")
    .replace(/<video\b[\s\S]*?<\/video>/gi, " ")
    .replace(/!\[[^\]]*]\([^)]+\)/g, " ")
    .replace(/\[!\[[^\]]*]\([^)]+\)]\([^)]+\)/g, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\[([^\]]+)]\([^)]+\)/g, "$1")
    .replace(/[#>*_`~\\-]+/g, " ")
    .replace(/&nbsp;|&#160;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function sentenceFor(frontMatter, body) {
  const title = getScalar(frontMatter, "title") || "未命名文章";
  const date = getScalar(frontMatter, "date").slice(0, 10);
  const categories = getCategories(frontMatter);
  const text = plainText(body);
  if (text.length >= 35) return text.slice(0, 155);
  const categoryText = categories.length ? `，分类为${categories.join("、")}` : "";
  const dateText = date ? `，发布于${date}` : "";
  return `《${title}》是五福在家 自得其乐的一篇归档文章${dateText}${categoryText}。`;
}

function insertAfter(lines, anchorKey, newLines) {
  const index = lines.findIndex((line) => line.startsWith(`${anchorKey}:`));
  if (index >= 0) {
    lines.splice(index + 1, 0, ...newLines);
  } else {
    lines.push(...newLines);
  }
}

function enrichFrontMatter(frontMatter, body) {
  const lines = frontMatter.split("\n");
  let changed = false;

  if (!hasKey(frontMatter, "description")) {
    insertAfter(lines, "title", [`description: ${yamlString(sentenceFor(frontMatter, body))}`]);
    changed = true;
  }

  if (!hasKey(frontMatter, "lastmod")) {
    const date = getScalar(frontMatter, "date");
    if (date) {
      insertAfter(lines, "date", [`lastmod: ${yamlString(date)}`]);
      changed = true;
    }
  }

  if (!hasKey(frontMatter, "images")) {
    const image = firstImage(body);
    if (image) {
      const categoriesIndex = lines.findIndex((line) => line.startsWith("categories:"));
      const imageLines = ["images:", `  - ${yamlString(image)}`];
      if (categoriesIndex >= 0) {
        let insertAt = categoriesIndex + 1;
        while (insertAt < lines.length && /^\s+-\s+/.test(lines[insertAt])) insertAt += 1;
        lines.splice(insertAt, 0, ...imageLines);
      } else {
        lines.push(...imageLines);
      }
      changed = true;
    }
  }

  return { frontMatter: lines.join("\n"), changed };
}

function enrichRawMedia(text, title) {
  let changed = false;
  let next = text.replace(/<video\b(?![^>]*\bpreload=)([^>]*)>/gi, (_match, attrs) => {
    changed = true;
    const hasPlaysInline = /\bplaysinline\b/i.test(attrs);
    return `<video preload="none"${hasPlaysInline ? "" : " playsinline"}${attrs}>`;
  });

  next = next.replace(/<img\b([^>]*?)>/gi, (match, attrs) => {
    if (/\balt\s*=/.test(attrs)) return match;
    changed = true;
    return `<img alt="${title.replace(/"/g, "&quot;")}"${attrs}>`;
  });

  return { text: next, changed };
}

let changedFiles = 0;

for (const file of fs.readdirSync(postsDir).filter((name) => name.endsWith(".md"))) {
  const fullPath = path.join(postsDir, file);
  const original = fs.readFileSync(fullPath, "utf8");
  const parsed = parseFrontMatter(original);
  if (!parsed) continue;

  const title = getScalar(parsed.frontMatter, "title") || path.basename(file, ".md");
  const enriched = enrichFrontMatter(parsed.frontMatter, parsed.body);
  const media = enrichRawMedia(parsed.body, title);
  if (!enriched.changed && !media.changed) continue;

  fs.writeFileSync(fullPath, `---\n${enriched.frontMatter}\n---${media.text}`, "utf8");
  changedFiles += 1;
}

const pageUpdates = new Map([
  [
    path.join(root, "content", "_index.md"),
    {
      description: "五福在家 自得其乐是吴五福的个人作品、书法、签名设计、诗文与家庭记忆归档。",
    },
  ],
  [
    path.join(root, "content", "archives.md"),
    {
      description: "五福在家 自得其乐的文章归档，按年份浏览吴五福的作品、诗文、回忆与家庭记录。",
    },
  ],
  [
    path.join(root, "content", "comments.md"),
    {
      description: "五福在家 自得其乐的历史评论归档页面。",
      robotsNoIndex: true,
    },
  ],
]);

for (const [file, fields] of pageUpdates) {
  const original = fs.readFileSync(file, "utf8");
  const parsed = parseFrontMatter(original);
  if (!parsed) continue;
  const lines = parsed.frontMatter.split("\n");
  let changed = false;
  if (fields.description && !hasKey(parsed.frontMatter, "description")) {
    insertAfter(lines, "title", [`description: ${yamlString(fields.description)}`]);
    changed = true;
  }
  if (fields.robotsNoIndex && !hasKey(parsed.frontMatter, "robotsNoIndex")) {
    lines.push("robotsNoIndex: true");
    changed = true;
  }
  const media = enrichRawMedia(parsed.body, getScalar(parsed.frontMatter, "title"));
  if (changed || media.changed) {
    fs.writeFileSync(file, `---\n${lines.join("\n")}\n---${media.text}`, "utf8");
    changedFiles += 1;
  }
}

console.log(`SEO enrichment updated ${changedFiles} files.`);
