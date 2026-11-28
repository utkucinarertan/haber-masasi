// Yerel test: Cloudflare hesabı gerekmez. Canlı havuzu okur, KV'yi bellekte taklit eder, Gemini'yi taklit eder.
import assert from "node:assert/strict";
import worker, {norm, matcher, editionDay, cleanQuery, refresh} from "../src/index.js";

class MemKV {
  constructor(){ this.m = new Map(); this.writes = 0; }
  async get(k, type){ const v = this.m.get(k); return v == null ? null : type === "json" ? JSON.parse(v) : v; }
  async put(k, v){ this.writes++; this.m.set(k, v); }
  async delete(k){ this.m.delete(k); }
  async list({prefix, cursor}){ return {keys: [...this.m.keys()].filter(k => k.startsWith(prefix)).map(name => ({name})), list_complete: true}; }
}
const env = {TOPICS: new MemKV(), DATA_BASE: "https://www.newsbyfocus.com/data/", MOCK_GEMINI: "1",
  mock: (system, user) => ({strings: JSON.parse(user).strings.map(s => s && "[ç] " + s)})};
const waits = [];
const ctx = {waitUntil: p => waits.push(p)};
const call = async qs => { const r = await worker.fetch(new Request("https://x/topic?" + qs), env, ctx); await Promise.all(waits); return [r.status, await r.json()]; };

// eşleştirme
assert.ok(matcher("Beşiktaş")(norm("Beşiktaş'ın yeni transferi")));
assert.ok(matcher("besiktas")(norm("BEŞİKTAŞ kazandı")));
assert.ok(!matcher("Bayern")(norm("Bayernmünchen")) === false);   // önek eşleşmesi bilinçli
assert.ok(!matcher("AYM")(norm("kaymakam")));                       // kelime başı
assert.equal(cleanQuery("  #Beşiktaş   JK "), "Beşiktaş JK");
assert.match(editionDay(new Date("2026-11-27T03:30:00Z")), /^2026-11-26$/);   // Almanya 04:30 → önceki gün
assert.match(editionDay(new Date("2026-11-27T05:30:00Z")), /^2026-11-27$/);

// istek
let [st, d] = await call("country=tr&q=Beşiktaş&lang=tr");
assert.equal(st, 200); console.log("Beşiktaş:", d.matched, "eşleşme,", d.items.length, "haber, gün", d.day);
assert.ok(d.items.length > 0 && d.items.length <= 5);
const writes1 = env.TOPICS.writes;
[st, d] = await call("country=tr&q=beşiktaş&lang=tr");   // aynı konu (büyük/küçük harf): önbellekten, yeni yazma yok
assert.equal(st, 200); assert.equal(env.TOPICS.writes, writes1, "ikinci istek yazmamalı");
[st, d] = await call("country=tr&q=Beşiktaş&lang=de");    // başka dil: ayrı özet
assert.equal(st, 200);
[st, d] = await call("country=tr&q=zzqqxx&lang=tr");      // eşleşme yok: Gemini'ye gitmeden boş
assert.equal(st, 200); assert.equal(d.items.length, 0);
[st, d] = await call("country=xx1&q=a&lang=tr"); assert.equal(st, 400);
[st, d] = await call("country=fr&q=Macron&lang=tr"); assert.equal(st, 404);   // havuzu olmayan ülke
const reg = await env.TOPICS.get("reg:default:tr:besiktas", "json");
console.log("kayıt:", reg);
assert.deepEqual(reg.langs.sort(), ["de", "tr"]);

// dil denetimi
import {wrongLanguageText} from "../src/llm.js";
assert.ok(wrongLanguageText("Gözaltına alınan taraftarlar serbest bırakıldı ve UEFA soruşturma açtı", "de"));
assert.ok(!wrongLanguageText("Festgenommene Fans wurden freigelassen, und die UEFA hat eine Untersuchung eingeleitet", "de"));
assert.ok(wrongLanguageText("UEFA opens an investigation into the match after the incidents", "zh"));
assert.ok(!wrongLanguageText("欧足联对比赛中发生的事件展开调查，十六名球迷获释", "zh"));
assert.ok(!wrongLanguageText("الاتحاد الأوروبي لكرة القدم يفتح تحقيقا في أحداث المباراة", "ar"));
assert.ok(!wrongLanguageText("La UEFA abre una investigación por los incidentes del partido con los aficionados", "es"));

// çeviri (taklit LLM): baskı ve son dakika
const tr1 = await worker.fetch(new Request("https://x/translate?kind=edition&lang=es&c=tr&date=" + (await (await fetch(env.DATA_BASE + "index.json")).json()).editions[0].date), env, ctx);
const ed = await tr1.json(); assert.equal(tr1.status, 200);
assert.equal(ed.lang, "es"); assert.ok(ed.countries[0].items[0].title.startsWith("[ç] ")); console.log("çeviri:", ed.countries[0].items[0].title.slice(0, 60));
const fl = await (await worker.fetch(new Request("https://x/translate?kind=flash&lang=fr&c=tr,de"), env, ctx)).json();
console.log("son dakika çevirisi:", Object.keys(fl.countries), (Object.values(fl.countries)[0] || [])[0]?.text?.fr?.slice(0, 50));
const wr = env.TOPICS.writes;
await worker.fetch(new Request("https://x/translate?kind=flash&lang=fr&c=tr,de"), env, ctx);
assert.equal(env.TOPICS.writes, wr, "aynı son dakika ikinci kez çevrilmemeli");
// hazırlık: GitHub anahtarı yoksa 503, geçersiz ülke 400
assert.equal((await worker.fetch(new Request("https://x/prepare?c=jp"), env, ctx)).status, 503);
assert.equal((await worker.fetch(new Request("https://x/prepare?c=xx"), env, ctx)).status, 400);

// sabah yenilemesi: bugünkü özetler varken bir şey yapmaz; eskiyince yeniler
let n = await refresh(env); assert.equal(n, 0);
const dk = "dig:default:tr:besiktas:tr";
const old = await env.TOPICS.get(dk, "json"); old.day = "2000-01-01"; await env.TOPICS.put(dk, JSON.stringify(old));
n = await refresh(env); assert.equal(n, 1); assert.equal((await env.TOPICS.get(dk, "json")).day, editionDay());
console.log("tüm testler geçti; KV yazma:", env.TOPICS.writes);
