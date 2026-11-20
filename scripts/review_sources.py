"""Haber Masası - haftalık kaynak denetimi.

Her ülkenin haber kaynaklarını Gemini'ye (Google aramasıyla, güncel bilgiyle) denetletir:
- bağımsızlığını yitiren kaynakları (kayyum atanan, devlet ya da hükümet denetimine geçen,
  kapanan) çıkarır,
- yerine bağımsız haber sitelerinin RSS akışlarını önerir; her adres gerçekten denenir,
- sonucu docs/data/config.json'a yazar, değişiklikleri docs/data/source-review.json'a kaydeder.

Yöneticinin "kullanılmayacak siteler" listesi (config.json → blocked) her zaman uygulanır;
bu listedeki alan adları hiçbir zaman eklenmez.

Çalıştırma:
  GEMINI_API_KEY=... python scripts/review_sources.py          # son denetimden 6 gün geçtiyse
  GEMINI_API_KEY=... python scripts/review_sources.py --force  # hemen
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_news as bn  # noqa: E402

# denetim raporu her profilin klasöründe: <profil>/source-review.json
EVERY = timedelta(days=6, hours=12)
MAX_FEEDS = 16          # ülke başına en fazla kaynak
MIN_DAILY = 3           # günlük baskıya en az bu kadar çalışan kaynak (yoksa eski liste korunur)
MIN_FLASH = 2           # son dakikaya en az bu kadar
MIN_ITEMS = 3           # son 3 günde en az bu kadar haber çıkaran akış "çalışıyor" sayılır

SCHEMA = {"type": "object", "properties": {
    "current": {"type": "array", "items": {"type": "object", "properties": {
        "url": {"type": "string"}, "keep": {"type": "boolean"}, "reason": {"type": "string"}},
        "required": ["url", "keep", "reason"]}},
    "suggestions": {"type": "array", "items": {"type": "object", "properties": {
        "name": {"type": "string"}, "url": {"type": "string"}, "language": {"type": "string"},
        "use": {"type": "string", "enum": ["daily", "flash", "both"]}, "reason": {"type": "string"},
        "topic": {"type": "string", "enum": ["general", "ekonomi", "teknoloji", "spor"]},},
        "required": ["name", "url", "use", "reason"]}},
    "avoid": {"type": "array", "items": {"type": "object", "properties": {
        "domain": {"type": "string"}, "reason": {"type": "string"}}, "required": ["domain", "reason"]}}},
    "required": ["current", "suggestions", "avoid"]}

SYSTEM = """You are a careful media researcher who audits the news sources of a news-summary app. \
Search the web for up-to-date information before answering: ownership changes, court-appointed \
trustees (kayyum), state takeovers, closures and bans happen often. Output only what you can support."""


def prompt(country, feeds, blocked, today, topics="ekonomi, teknoloji, spor"):
    return f"""Today is {today}. Audit the RSS news sources used for {country}.

Goal: the app must only use editorially independent, reputable news outlets. An outlet is NOT acceptable if, as of today, it is state-controlled or government-aligned media, has had a court- or government-appointed trustee/administrator (e.g. "kayyum") placed over it, has been taken over by owners who turned it into a government mouthpiece, or has closed. Public service broadcasters with independent governance (e.g. ARD/tagesschau, ZDF, BBC, DW) are acceptable; state broadcasters and agencies under government control (e.g. TRT, Anadolu Ajansı) are not. Prefer outlets across the independent spectrum, not one political camp.

1. current: for each feed below decide keep=true/false with a short reason (in Turkish).
2. suggestions: up to 10 additional feeds from independent outlets covering {country} (prefer the country's own language; dedicated Turkish/German/English services of independent international broadcasters are welcome). Give exact, real https RSS/Atom URLs you are confident exist. use: "flash" for fast latest/breaking feeds, "daily" for curated top-story feeds, "both" for main feeds. topic: "general" for main news feeds, or "ekonomi", "teknoloji", "spor" for feeds dedicated to economy, technology/science or sport (use "daily" for those). The app needs at least two working dedicated feeds per enabled topic ({topics}); fill missing topics first. reason in Turkish.
3. avoid: domains (e.g. example.com) of well-known outlets for {country} that must not be used because they are not independent as of today, with a short Turkish reason.

Never suggest these blocked domains: {", ".join(blocked) or "-"}

Current feeds (JSON):
{json.dumps(feeds, ensure_ascii=False)}"""


def domain(url):
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def is_blocked(url, blocked):
    d = domain(url)
    return any(d == b or d.endswith("." + b) for b in blocked)


def works(name, url, since, min_items=MIN_ITEMS):
    try:
        n = len(bn.read_feed(name, url, since))
    except Exception as e:  # noqa: BLE001
        bn.log(f"  ✗ {name} {url} ({type(e).__name__})")
        return 0
    bn.log(f"  {'✓' if n >= min_items else '✗'} {name} {url} ({n} haber)")
    return n if n >= min_items else 0


def review_country(country, blocked, today, since):
    name = country.get("name") or country["code"].upper()
    bn.log(f"{name}:")
    old = country.get("feeds", [])
    result = bn.gemini(SYSTEM, prompt(f"{name} (ISO {country['code'].upper()})",
                                      [{"name": f.get("name"), "url": f["url"], "use": bn.feed_use(f),
                                        "topic": bn.feed_topic(f) or "general"} for f in old],
                                      blocked, today,
                                      ", ".join(t for t in bn.country_topics(country) if t != "gundem") or "-"),
                       SCHEMA, search=True)
    verdict = {str(c.get("url", "")).strip(): c for c in result.get("current") or []}
    avoid = [{"domain": domain("https://" + str(a.get("domain", "")).strip().removeprefix("https://").removeprefix("http://")),
              "reason": str(a.get("reason", ""))[:200]} for a in result.get("avoid") or []]
    avoid = [a for a in avoid if "." in a["domain"]]
    all_blocked = blocked + [a["domain"] for a in avoid]

    kept, removed, added = [], [], []
    for f in old:
        v = verdict.get(f["url"], {})
        if is_blocked(f["url"], all_blocked):
            removed.append({**f, "reason": v.get("reason") or "kullanılmayacak siteler listesinde"})
        elif v.get("keep") is False:
            removed.append({**f, "reason": str(v.get("reason", ""))[:200]})
        elif not works(f.get("name", ""), f["url"], since - timedelta(days=4), 1):   # seyrek "Eilmeldung" akışları
            removed.append({**f, "reason": "akış çalışmıyor ya da son bir haftada haber yok"})
        else:
            kept.append(f)
    have = {f["url"] for f in kept}
    for s in result.get("suggestions") or []:
        if len(kept) >= MAX_FEEDS:
            break
        url = str(s.get("url", "")).strip()
        if not url.startswith("https://") or url in have or is_blocked(url, all_blocked):
            continue
        have.add(url)
        f = {"name": str(s.get("name") or domain(url))[:60], "url": url,
             "use": s.get("use") if s.get("use") in ("daily", "flash", "both") else "both"}
        if s.get("topic") in ("ekonomi", "teknoloji", "spor"):
            f["topic"] = s["topic"]
        if works(f["name"], url, since):
            kept.append(f)
            added.append({**f, "reason": str(s.get("reason", ""))[:200]})

    daily = sum(bn.feed_use(f) in ("daily", "both") for f in kept)
    flash = sum(bn.feed_use(f) in ("flash", "both") for f in kept)
    if daily < MIN_DAILY or flash < MIN_FLASH:
        # yeterli bağımsız ve çalışan kaynak bulunamadı: listeyi boşaltma, yalnız engellileri çıkar
        bn.log(f"  Yeterli kaynak yok (günlük {daily}, son dakika {flash}); yalnızca engelli siteler çıkarıldı.")
        kept = [f for f in old if not is_blocked(f["url"], blocked)]
        removed = [r for r in removed if is_blocked(r["url"], blocked)]
        added = []
    return kept, {"code": country["code"], "added": added, "removed": removed, "avoid": avoid}


def main():
    """Her profil kendi kaynaklarını ve engelli listesini taşır; hepsi sırayla denetlenir.
    --profile <id> verilirse yalnız o profil (yönetim sayfasındaki düğme)."""
    sys.stdout.reconfigure(encoding="utf-8")
    only = sys.argv[sys.argv.index("--profile") + 1].strip() if "--profile" in sys.argv else ""
    for pid in bn.list_profiles():
        if only and pid != only:
            continue
        bn.use_profile(pid)
        bn.log(f"=== Profil: {pid}")
        review_profile()


def review_profile():
    cfg = json.loads(bn.CONFIG.read_text(encoding="utf-8"))
    review_file = bn.DATA / "source-review.json"
    now = datetime.now(bn.zone(cfg))
    last = cfg.get("sourcesReviewedAt")
    forced = "--force" in sys.argv or os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
    if last and not forced and now - datetime.fromisoformat(last) < EVERY:
        bn.log(f"Son denetim {last}; bir hafta dolmadı.")
        return
    blocked = [domain("https://" + b["domain"]) for b in cfg.get("blocked", []) if b.get("domain")]
    since = datetime.now(timezone.utc) - timedelta(days=3)
    report = []
    for i, country in enumerate(cfg.get("countries", [])):
        if i:
            time.sleep(30)   # dakikalık kota
        try:
            feeds, r = review_country(country, blocked, now.date().isoformat(), since)
        except RuntimeError as e:
            bn.log(f"  denetlenemedi: {e}")
            report.append({"code": country["code"], "error": str(e)[:200]})
            continue
        country["feeds"] = feeds
        report.append(r)
    if all(not r.get("error") for r in report):   # hata varsa bir sonraki zamanlanmış çalıştırmada yeniden denenir
        cfg["sourcesReviewedAt"] = now.isoformat(timespec="minutes")
    bn.CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    review_file.write_text(json.dumps({"reviewedAt": now.isoformat(timespec="minutes"), "countries": report},
                                 ensure_ascii=False, indent=1), encoding="utf-8")
    for r in report:
        bn.log(f"{r['code']}: +{len(r.get('added', []))} / -{len(r.get('removed', []))}"
               + (f" HATA {r['error']}" if r.get("error") else ""))


if __name__ == "__main__":
    main()
