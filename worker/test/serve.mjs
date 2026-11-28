// Yerel deneme sunucusu (Cloudflare hesabı gerekmez): node test/serve.mjs  → http://localhost:8787
// KV bellekte, LLM taklit (MOCK_GEMINI=1): çeviriler "[dil] " önekiyle döner.
// ADMIN_PASSWORD=... ile yönetim sayfası: http://localhost:8787/studio (node --import ./test/register.mjs test/serve.mjs)
// FAKE_PREP=1: /prepare GitHub'a gitmeden adımları zamanla taklit eder (ülke ~40 sn'de "hazır" olur).
import http from "node:http";
import worker from "../src/index.js";

class MemKV {
  constructor(){ this.m = new Map(); }
  async get(k, type){ const v = this.m.get(k); return v == null ? null : type === "json" ? JSON.parse(v) : v; }
  async put(k, v){ this.m.set(k, v); }
  async delete(k){ this.m.delete(k); }
  async list({prefix}){ return {keys: [...this.m.keys()].filter(k => k.startsWith(prefix)).map(name => ({name})), list_complete: true}; }
}
const env = {TOPICS: new MemKV(), DATA_BASE: process.env.DATA_BASE || "https://www.newsbyfocus.com/data/",
             MOCK_GEMINI: process.env.MOCK_GEMINI ?? "1", ADMIN_PATH: "studio", ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || "",
             GITHUB_REPO: "utkucinarertan/haber-masasi", GITHUB_TOKEN: process.env.GITHUB_TOKEN || "", GEMINI_API_KEY: process.env.GEMINI_API_KEY || "",
             mock: (system, user) => { const lang = (system.match(/into ([A-Za-z ]+?)\. /) || [, "xx"])[1];
               return {strings: JSON.parse(user).strings.map(s => s && `[${lang}] ${s}`)}; }};
const READY = new Set(["world", "de", "tr"]), fake = new Map();
function fakePrepare(url){
  const codes = (url.searchParams.get("c") || "").split(",").filter(Boolean);
  const out = {};
  for (const c of codes){
    if (READY.has(c)){ out[c] = {state: "ready", step: 4}; continue; }
    if (!fake.has(c) && url.searchParams.get("start") === "1") fake.set(c, Date.now());
    if (!fake.has(c)){ out[c] = {state: "missing", step: 0}; continue; }
    const sec = (Date.now() - fake.get(c)) / 1000;
    out[c] = c === "kw" && sec > 15 ? {state: "failed", step: 0} : sec > 40 ? {state: "ready", step: 4} : {state: "working", step: Math.min(4, 1 + Math.floor(sec / 10))};
  }
  return new Response(JSON.stringify({countries: out}), {headers: {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}});
}
http.createServer(async (req, res) => {
  const url = new URL("http://localhost:8787" + req.url);
  const r = process.env.FAKE_PREP === "1" && url.pathname === "/prepare" ? fakePrepare(url)
    : await worker.fetch(new Request(url, {method: req.method, headers: req.headers,
        body: ["GET", "HEAD"].includes(req.method) ? undefined : await new Promise(ok => { const b = []; req.on("data", c => b.push(c)); req.on("end", () => ok(Buffer.concat(b))); })}),
        env, {waitUntil(){}});
  res.writeHead(r.status, Object.fromEntries(r.headers));
  res.end(Buffer.from(await r.arrayBuffer()));
}).listen(8787, () => console.log("konu sunucusu: http://localhost:8787"));
