// Copies the PWA from ../docs into ./www for bundling inside the app.
// - data/ is NOT bundled: news JSON is fetched live from DATA_BASE (fresh every run).
// - admin.html and sw.js are left out (admin is for the owner; a service worker is
//   not needed when the shell ships inside the app and would keep stale copies).
// - A tiny shim is injected into www/index.html (the copy, never docs/index.html)
//   that rewrites relative "data/..." fetches to DATA_BASE and hides the admin link.
// Change the data host (e.g. after moving to Cloudflare Pages):
//   HABER_DATA_BASE=https://haber-masasi.pages.dev/ npm run sync
import { cpSync, rmSync, readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "..", "..", "docs");
const out = join(here, "..", "www");
let base = process.env.HABER_DATA_BASE || "https://utkucinarertan.github.io/haber-masasi/";
if (!base.endsWith("/")) base += "/";

const SKIP = new Set(["data", "admin.html", "sw.js"]);
// Empty www/ (keep the folder itself: on Windows it may be locked by an open shell/server).
mkdirSync(out, { recursive: true });
for (const n of readdirSync(out)) rmSync(join(out, n), { recursive: true, force: true });
cpSync(src, out, {
  recursive: true,
  filter: p => { const r = relative(src, p).split(/[\\/]/)[0]; return !SKIP.has(r); },
});

const shim = `<script>/* app shim (mobile/scripts/copy-web.mjs) */(function(){
var B=${JSON.stringify(base)};window.HABER_APP=true;window.HABER_DATA_BASE=B;
var f=window.fetch.bind(window);
window.fetch=function(i,o){if(typeof i==="string"){if(i.indexOf("./data/")===0)i=i.slice(2);if(i.indexOf("data/")===0)i=B+i;}return f(i,o);};
if(navigator.serviceWorker){try{navigator.serviceWorker.register=function(){return Promise.reject(new Error("no SW in app"));};}catch(e){}}
})();</script>
<style>#admin-link{display:none!important}</style>`;

const idx = join(out, "index.html");
if (!existsSync(idx)) throw new Error("docs/index.html not found");
let html = readFileSync(idx, "utf8");
if (!/<head[^>]*>/i.test(html)) throw new Error("no <head> in index.html");
html = html.replace(/<head[^>]*>/i, m => m + "\n" + shim);
writeFileSync(idx, html);
console.log(`www ready (data from ${base})`);
