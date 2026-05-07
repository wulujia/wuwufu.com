#!/usr/bin/env node
// Add WordPress.com flat-slug aliases to each post's frontmatter.
//
// For every content/posts/*.md, take the filename (without .md) as the WP
// slug and inject `aliases: ["/<slug>/"]` into frontmatter. Hugo then emits
// /<slug>/index.html as a meta-refresh redirect to the canonical permalink.
//
// Why: Cloudflare Pages caps _redirects at 100 rules on the free tier, but
// we have 785 posts. Aliases bypass the cap because each is a real static
// HTML file, not a redirect rule.
//
// Idempotent — re-running won't duplicate the alias.

import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, dirname, basename, extname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const POSTS_DIR = resolve(__dirname, "..", "content", "posts");

function extractUrl(yamlBlock) {
  const m = yamlBlock.match(/^url:\s*"?([^"\n]+?)"?\s*$/m);
  return m ? m[1].trim() : null;
}

function processFile(filePath, filename) {
  const slug = basename(filename, extname(filename));
  const wpAlias = `/${slug}/`;
  const text = readFileSync(filePath, "utf8");

  if (!text.startsWith("---\n")) return { skipped: "no frontmatter" };
  const end = text.indexOf("\n---\n", 4);
  if (end === -1) return { skipped: "malformed frontmatter" };
  const fm = text.slice(4, end);
  const body = text.slice(end + 5);

  const url = extractUrl(fm);
  if (!url) return { skipped: "no url field" };

  // Skip if Hugo URL == WP slug (would create a redirect loop).
  if (url === wpAlias || url === wpAlias.replace(/\/$/, "")) {
    return { skipped: "url matches slug" };
  }

  // Skip if alias is already present (idempotent).
  if (
    fm.includes(`"${wpAlias}"`) ||
    fm.includes(`'${wpAlias}'`) ||
    new RegExp(`^\\s*-\\s*['"]?${wpAlias.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}['"]?\\s*$`, "m").test(fm)
  ) {
    return { skipped: "alias already present" };
  }

  // Reject files that already have `aliases:` — needs manual merge.
  if (/^aliases:/m.test(fm)) {
    return { skipped: "existing aliases (manual merge)" };
  }

  // Insert single-line aliases before the closing fence to keep diff minimal.
  const newFm = fm.replace(/\n*$/, "") + `\naliases: ["${wpAlias}"]`;
  writeFileSync(filePath, `---\n${newFm}\n---\n` + body, "utf8");
  return { wrote: true };
}

const files = readdirSync(POSTS_DIR).filter(
  (f) => f.endsWith(".md") && !f.startsWith("_"),
);

let wrote = 0;
const reasons = {};
for (const f of files) {
  const r = processFile(join(POSTS_DIR, f), f);
  if (r.wrote) wrote++;
  else reasons[r.skipped] = (reasons[r.skipped] || 0) + 1;
}
console.log(`Wrote aliases into ${wrote} files`);
const skipped = Object.values(reasons).reduce((a, b) => a + b, 0);
if (skipped) {
  console.log(`Skipped ${skipped}:`);
  for (const [reason, n] of Object.entries(reasons)) {
    console.log(`  ${reason}: ${n}`);
  }
}
