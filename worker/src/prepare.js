/* Yeni ülke hazırlığı: uygulamada henüz haberi olmayan bir ülke seçilince GitHub Actions'taki
   "Ülke hazırla" işini başlatır ve adımlarını (kaynak bulma → değerlendirme → haberler → yayın) bildirir.

   GET /prepare?c=jp,kr[&start=1]  →  {countries: {jp: {state: "ready"|"working"|"failed", step: 0-4}}}
*/

/* Uygulamanın sunduğu ülkeler: dünyanın en büyük ekonomileri + Türkiye (+ Dünya). Uygulamadaki liste ile aynı. */
export const COUNTRIES = ["world", "us", "cn", "de", "jp", "in", "gb", "fr", "it", "ca", "br", "ru", "kr", "au", "mx", "es",
  "id", "nl", "sa", "tr", "ch", "pl", "tw", "be", "se", "ie", "ar", "ae", "sg", "il", "at", "no", "th", "ph", "vn", "bd",
  "my", "dk", "ng", "eg", "za", "co", "cl", "fi", "cz", "pt", "ro", "nz", "gr", "pk", "qa", "hu", "kz", "kw", "pe"];
const MAX_STARTS_PER_DAY = 30;     // kötüye kullanıma karşı: günde en fazla bu kadar yeni ülke hazırlığı
const RETRY_AFTER = 20 * 60e3;     // başarısız hazırlık bu kadar sonra yeniden başlatılabilir
const STEP_RE = /^([1-4]) /;

const enName = code => { if (code === "world") return "World"; try { return new Intl.DisplayNames(["en"], {type: "region"}).of(code.toUpperCase()); } catch { return code.toUpperCase(); } };

export async function github(env, path, opts = {}){
  const r = await fetch("https://api.github.com/" + path, {...opts, headers: {
    "Authorization": "Bearer " + env.GITHUB_TOKEN, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "news-worker", ...(opts.body ? {"Content-Type": "application/json"} : {}), ...(opts.headers || {})}});
  return r;
}

/* Kısa süreli bellek önbelleği (aynı Worker örneğinde art arda gelen yoklamalar GitHub'ı yormasın). */
const memo = new Map();
async function cached(key, ttl, fn){
  const hit = memo.get(key);
  if (hit && Date.now() - hit.at < ttl) return hit.value;
  const value = await fn();
  memo.set(key, {at: Date.now(), value});
  return value;
}

async function readyCodes(env){
  return cached("ready", 15e3, async () => {
    const base = env.DATA_BASE.replace(/\/?$/, "/");
    const t = "?t=" + Date.now();   // Pages önbelleğini atla: yayın biter bitmez görülsün
    const [cfg, idx] = await Promise.all([fetch(base + "config.json" + t).then(r => r.json()), fetch(base + "index.json" + t).then(r => r.json())]);
    const configured = new Set((cfg.countries || []).map(c => c.code));
    const latest = (idx.editions || [])[0];
    let inEdition = new Set();
    if (latest){
      const doc = await fetch(`${base}editions/${latest.date}/${latest.langs[0]}.json${t}`).then(r => r.json()).catch(() => ({}));
      inEdition = new Set((doc.countries || []).filter(c => c.topics).map(c => c.code));
    }
    return new Set([...configured].filter(c => inEdition.has(c)));
  });
}

async function findRun(env, code, since){
  const runs = await cached("runs", 8e3, async () => {
    const r = await github(env, `repos/${env.GITHUB_REPO}/actions/workflows/prepare-country.yml/runs?per_page=40`);
    return r.ok ? (await r.json()).workflow_runs || [] : [];
  });
  return runs.find(x => x.display_title === `Hazırla ${code}` && Date.parse(x.created_at) >= since - 120e3) || null;
}

async function runStep(env, run){
  if (run.status === "completed") return run.conclusion === "success" ? 4 : -1;
  if (run.status !== "in_progress") return 0;
  const jobs = await cached("jobs:" + run.id, 8e3, async () => {
    const r = await github(env, `repos/${env.GITHUB_REPO}/actions/runs/${run.id}/jobs`);
    return r.ok ? (await r.json()).jobs || [] : [];
  });
  const steps = (jobs[0]?.steps || []).filter(s => STEP_RE.test(s.name));
  if (steps.some(s => s.conclusion === "failure")) return -1;
  const cur = steps.find(s => s.status !== "completed");
  return cur ? +cur.name.match(STEP_RE)[1] : steps.length ? 4 : 1;
}

async function start(env, code){
  const day = new Date().toISOString().slice(0, 10);
  const n = +(await env.TOPICS.get("prepday:" + day) || 0);
  if (n >= MAX_STARTS_PER_DAY) return false;
  const r = await github(env, `repos/${env.GITHUB_REPO}/actions/workflows/prepare-country.yml/dispatches`, {method: "POST",
    body: JSON.stringify({ref: "main", inputs: {country: code, name: enName(code)}})});
  if (!r.ok){ console.log("hazırlık başlatılamadı", code, r.status, await r.text()); return false; }
  await env.TOPICS.put("prep:" + code, JSON.stringify({at: Date.now()}), {expirationTtl: 86400});
  await env.TOPICS.put("prepday:" + day, String(n + 1), {expirationTtl: 2 * 86400});
  memo.delete("runs");
  return true;
}

export async function handlePrepare(request, env){
  const url = new URL(request.url);
  const json = (d, s = 200) => new Response(JSON.stringify(d), {status: s, headers: {"Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*", "Cache-Control": "no-store"}});
  const codes = [...new Set((url.searchParams.get("c") || "").toLowerCase().split(","))].filter(c => COUNTRIES.includes(c)).slice(0, 12);
  if (!codes.length) return json({error: "bad-request"}, 400);
  if (!env.GITHUB_TOKEN) return json({error: "not-configured"}, 503);
  const wantStart = url.searchParams.get("start") === "1";
  let ready;
  try { ready = await readyCodes(env); } catch (e){ return json({error: "data", message: e.message}, 502); }
  const out = {};
  for (const code of codes){
    if (ready.has(code)){ out[code] = {state: "ready", step: 4}; continue; }
    let prep = await env.TOPICS.get("prep:" + code, "json");
    let run = prep ? await findRun(env, code, prep.at) : null;
    let step = run ? await runStep(env, run) : 0;
    const stale = prep && !run && Date.now() - prep.at > 5 * 60e3;              // başlatıldı ama iş hiç görünmedi
    const retry = prep && step === -1 && Date.now() - prep.at > RETRY_AFTER;   // başarısız oldu, süre doldu
    if (wantStart && (!prep || stale || retry)){
      if (await start(env, code)){ out[code] = {state: "working", step: 0}; continue; }
      out[code] = {state: "failed", step: 0, reason: "limit"}; continue;
    }
    if (!prep){ out[code] = {state: "missing", step: 0}; continue; }
    out[code] = step === -1 ? {state: "failed", step: 0} : {state: "working", step};
  }
  return json({countries: out});
}
