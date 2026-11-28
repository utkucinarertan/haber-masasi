/* Günlük baskı ve son dakika, yayın dillerinde (config.languages) olmayan bir dile istek üzerine çevrilir.
   Her ülke bölümü ayrı çevrilir ve KV'de saklanır: aynı içerik + dil herkes için tek kez çevrilir. */
import {LANGS, translateStrings} from "./llm.js";

export function hash(s){   // FNV-1a 32 bit: içerik değişince çeviri yenilenir
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); }
  return (h >>> 0).toString(36);
}

const base = env => env.DATA_BASE.replace(/\/?$/, "/");
async function fetchJSON(env, path, ttl = 60){
  const r = await fetch(base(env) + path, {cf: {cacheTtl: ttl, cacheEverything: true}});
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

async function translateCountry(env, date, c, lang){
  const key = `trn:e:${date}:${c.code}:${lang}:${hash(JSON.stringify(c))}`;
  const hit = await env.TOPICS.get(key, "json");
  if (hit) return hit;
  const strings = [c.overview || ""];
  for (const it of c.items || []) strings.push(it.title || "", it.summary || "", it.category || "");
  const out = await translateStrings(env, strings, lang);
  const res = {...c, overview: out[0], items: (c.items || []).map((it, i) => ({...it,
    title: out[1 + i * 3] || it.title, summary: out[2 + i * 3] || it.summary, category: out[3 + i * 3] || it.category}))};
  await env.TOPICS.put(key, JSON.stringify(res), {expirationTtl: 3 * 86400});
  return res;
}

async function translateFlash(env, code, list, lang){
  const texts = list.map(x => (x.text && (x.text.tr || x.text.en || Object.values(x.text)[0])) || "");
  const key = `trn:f:${code}:${lang}:${hash(texts.join("\n"))}`;
  let out = await env.TOPICS.get(key, "json");
  if (!out){
    out = await translateStrings(env, texts, lang);
    await env.TOPICS.put(key, JSON.stringify(out), {expirationTtl: 2 * 86400});
  }
  return list.map((x, i) => ({...x, text: {...x.text, [lang]: out[i] || texts[i]}}));
}

export async function handleTranslate(request, env){
  const url = new URL(request.url);
  const kind = url.searchParams.get("kind");
  const lang = (url.searchParams.get("lang") || "").toLowerCase();
  const codes = (url.searchParams.get("c") || "").toLowerCase().split(",").filter(c => /^([a-z]{2}|world)$/.test(c)).slice(0, 12);
  const json = (d, s = 200) => new Response(JSON.stringify(d), {status: s, headers: {"Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=300"}});
  if (!LANGS[lang] || !codes.length) return json({error: "bad-request"}, 400);
  if (kind === "edition"){
    const date = url.searchParams.get("date") || "";
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return json({error: "bad-request"}, 400);
    const idx = await fetchJSON(env, "index.json");
    const entry = (idx.editions || []).find(e => e.date === date);
    if (!entry) return json({error: "not-found"}, 404);
    const src = entry.langs.includes(lang) ? lang : entry.langs.includes("tr") ? "tr" : entry.langs[0];
    const doc = await fetchJSON(env, `editions/${date}/${src}.json`, 120);
    if (src === lang) return json(doc);
    const failed = [];
    const countries = await Promise.all((doc.countries || []).filter(c => codes.includes(c.code)).map(c =>
      translateCountry(env, date, c, lang).catch(e => { failed.push(c.code); console.log("çeviri", c.code, e.message); return {...c, untranslated: true}; })));
    return json({...doc, lang, source: src, countries, failed});
  }
  if (kind === "flash"){
    const fl = await fetchJSON(env, "flash.json", 60);
    const countries = {};
    await Promise.all(codes.filter(c => (fl.countries || {})[c]?.length).map(async c => {
      try { countries[c] = await translateFlash(env, c, fl.countries[c], lang); }
      catch (e){ console.log("son dakika çevirisi", c, e.message); countries[c] = fl.countries[c]; }
    }));
    return json({since: fl.since, updatedAt: fl.updatedAt, countries});
  }
  return json({error: "bad-request"}, 400);
}
