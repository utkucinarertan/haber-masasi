// Yerel deneme sunucusu (Cloudflare hesabı gerekmez): node test/serve.mjs  → http://localhost:8787
// KV bellekte, Gemini taklit (MOCK_GEMINI=1). Gerçek Gemini ile denemek için GEMINI_API_KEY ortam
// değişkenini verip MOCK_GEMINI=0 ile başlatın.
import http from "node:http";
import worker from "../src/index.js";

class MemKV {
  constructor(){ this.m = new Map(); }
  async get(k, type){ const v = this.m.get(k); return v == null ? null : type === "json" ? JSON.parse(v) : v; }
  async put(k, v){ this.m.set(k, v); }
  async delete(k){ this.m.delete(k); }
  async list({prefix}){ return {keys: [...this.m.keys()].filter(k => k.startsWith(prefix)).map(name => ({name})), list_complete: true}; }
}
const env = {TOPICS: new MemKV(), DATA_BASE: process.env.DATA_BASE || "https://utkucinarertan.github.io/haber-masasi/data/",
             MOCK_GEMINI: process.env.MOCK_GEMINI ?? "1", GEMINI_API_KEY: process.env.GEMINI_API_KEY || ""};
http.createServer(async (req, res) => {
  const r = await worker.fetch(new Request("http://localhost:8787" + req.url, {method: req.method}), env, {waitUntil(){}});
  res.writeHead(r.status, Object.fromEntries(r.headers));
  res.end(Buffer.from(await r.arrayBuffer()));
}).listen(8787, () => console.log("konu sunucusu: http://localhost:8787"));
