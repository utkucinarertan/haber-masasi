/* Gizli yönetim sayfası: uygulamada bağlantısı yoktur; şifreyle açılır.
   GitHub anahtarı tarayıcıya hiç gitmez: sayfa GitHub'a bu Worker üzerinden, yalnızca uygulamanın deposu için erişir.

   GET  /<ADMIN_PATH>            yönetim sayfası
   POST /adm/login {password}    → {token} (12 saat geçerli)
   *    /adm/gh/<github yolu>    GitHub API (yalnızca repos/<GITHUB_REPO>/...)
   POST /adm/llm-key {key}       LLM anahtarını konu sunucusu için de kaydeder (GitHub'a sayfa kaydeder)
*/
import {resetSettings} from "./llm.js";
import PAGE from "./admin.html";

const SESSION_MS = 12 * 3600e3;
const enc = new TextEncoder();
const b64url = buf => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

async function hmacKey(env){
  const raw = await crypto.subtle.digest("SHA-256", enc.encode("news-admin|" + env.ADMIN_PASSWORD));
  return crypto.subtle.importKey("raw", raw, {name: "HMAC", hash: "SHA-256"}, false, ["sign", "verify"]);
}
async function sign(env, payload){ return b64url(await crypto.subtle.sign("HMAC", await hmacKey(env), enc.encode(payload))); }
async function makeToken(env){ const exp = String(Date.now() + SESSION_MS); return exp + "." + await sign(env, exp); }
async function validToken(env, token){
  const [exp, sig] = String(token || "").split(".");
  if (!exp || !sig || !(+exp > Date.now())) return false;
  return timingSafeEqual(sig, await sign(env, exp));
}
function timingSafeEqual(a, b){
  if (a.length !== b.length) return false;
  let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}
async function samePassword(env, given){   // iki tarafın özeti karşılaştırılır: uzunluk ya da zamanlama bilgi vermez
  const [x, y] = await Promise.all([given, env.ADMIN_PASSWORD].map(s => crypto.subtle.digest("SHA-256", enc.encode(String(s)))));
  return timingSafeEqual(b64url(x), b64url(y));
}

/* Deneme sınırı: aynı adresten 5 yanlış şifre → 15 dakika kilit (Worker örneği başına). */
const fails = new Map();
const json = (d, s = 200) => new Response(JSON.stringify(d), {status: s, headers: {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}});
const notFound = () => new Response(JSON.stringify({error: "not-found"}), {status: 404, headers: {"Content-Type": "application/json"}});

export function isAdminPath(env, path){
  return !!env.ADMIN_PASSWORD && !!env.ADMIN_PATH && (path === "/" + env.ADMIN_PATH || path.startsWith("/adm/"));
}

export async function handleAdmin(request, env){
  const url = new URL(request.url);
  const path = url.pathname;
  if (path === "/" + env.ADMIN_PATH && request.method === "GET")
    return new Response(PAGE, {headers: {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex, nofollow", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer"}});
  if (path === "/adm/login" && request.method === "POST"){
    const ip = request.headers.get("CF-Connecting-IP") || "?";
    const f = fails.get(ip);
    if (f && f.n >= 5 && Date.now() < f.until) return json({error: "locked"}, 429);
    const body = await request.json().catch(() => ({}));
    if (await samePassword(env, body.password || "")){
      fails.delete(ip);
      return json({token: await makeToken(env)});
    }
    const n = (f && Date.now() < f.until ? f.n : 0) + 1;
    fails.set(ip, {n, until: Date.now() + 15 * 60e3});
    await new Promise(r => setTimeout(r, 700));
    return json({error: "wrong"}, 401);
  }
  const auth = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (!await validToken(env, auth)) return json({error: "auth"}, 401);
  if (path === "/adm/llm-key" && request.method === "POST"){
    const body = await request.json().catch(() => ({}));
    const key = String(body.key || "").trim();
    if (!/^[\w\-]{20,200}$/.test(key)) return json({error: "bad-key"}, 400);
    await env.TOPICS.put("cfg:geminiKey", key);
    resetSettings();
    return json({ok: true});
  }
  if (path.startsWith("/adm/gh/")){
    if (!env.GITHUB_TOKEN) return json({error: "not-configured", message: "Sunucuda GitHub anahtarı tanımlı değil."}, 503);
    const ghPath = path.slice("/adm/gh/".length);
    if (!ghPath.startsWith(`repos/${env.GITHUB_REPO}`) || ghPath.includes("..")) return json({error: "forbidden"}, 403);
    if (!["GET", "PUT", "POST", "DELETE"].includes(request.method)) return json({error: "method"}, 405);
    const r = await fetch("https://api.github.com/" + ghPath + url.search, {method: request.method,
      headers: {"Authorization": "Bearer " + env.GITHUB_TOKEN, "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "news-admin",
        ...(request.method !== "GET" ? {"Content-Type": "application/json"} : {})},
      body: request.method === "GET" || request.method === "DELETE" && !request.headers.get("Content-Length") ? undefined : await request.text()});
    return new Response(r.body, {status: r.status, headers: {"Content-Type": r.headers.get("Content-Type") || "application/json", "Cache-Control": "no-store"}});
  }
  return notFound();
}
