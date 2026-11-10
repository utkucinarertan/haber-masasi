"""Haber Masası - bir ülke için haber kaynaklarını (RSS) Gemini ile bulur.

Yönetim sayfasındaki "LLM ile ekle" düğmesi bu betiği GitHub Actions'ta çalıştırır.
Gemini ülkenin önemli haber sitelerinin RSS adreslerini önerir; her adres gerçekten
indirilip denenir, yalnızca güncel haber içerenler suggest/<ülke>.json dosyasına yazılır.
Yönetim sayfası bu dosyayı okuyup kaynakları forma ekler; kaydetmek yöneticiye kalır.

Çalıştırma:
  GEMINI_API_KEY=... python scripts/suggest_feeds.py <ülke kodu> [istek kimliği] [ülke adı]
"""
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_news as bn  # noqa: E402

OUT = bn.ROOT / "suggest"
MAX_FEEDS = 8
MIN_ITEMS = 3

SCHEMA = {"type": "object", "properties": {"feeds": {"type": "array", "items": {
    "type": "object", "properties": {
        "name": {"type": "string"}, "url": {"type": "string"},
        "language": {"type": "string"}, "use": {"type": "string", "enum": ["daily", "flash", "both"]},
        "why": {"type": "string"}},
    "required": ["name", "url", "language", "use"]}}}, "required": ["feeds"]}


def prompt(country, exclude):
    avoid = ("\nThese URLs did not work, do not suggest them again:\n" + "\n".join(exclude)) if exclude else ""
    return f"""You help configure a news app. List RSS or Atom feed URLs for news about {country}.

Requirements:
- Suggest 12 feeds from well-known, reputable outlets that cover {country}: the public broadcaster, major national newspapers and news sites across the political spectrum, and a news agency if it offers RSS. Prefer feeds in the country's own language; add Turkish, English or German services of international broadcasters (BBC, DW, Euronews, France 24, VOA, etc.) if they have a dedicated feed for {country} or its region.
- Give exact, real feed URLs (https) that you are confident exist, e.g. the outlet's main "top stories" or "latest news" feed. Do not invent paths.
- use: "flash" for fast "latest / breaking / son dakika / Eilmeldungen" style feeds that update many times per hour, "daily" for curated top-story or politics/economy feeds, "both" for main feeds that serve both purposes.
- language: ISO 639-1 code of the feed's language.
- why: a few words on what the feed covers.{avoid}"""


def try_feed(f, since):
    try:
        items = bn.read_feed(f["name"], f["url"], since)
    except Exception as e:  # noqa: BLE001
        bn.log(f"  ✗ {f['name']} {f['url']} ({type(e).__name__})")
        return None
    if len(items) < MIN_ITEMS:
        bn.log(f"  ✗ {f['name']} {f['url']} (son 3 günde {len(items)} haber)")
        return None
    bn.log(f"  ✓ {f['name']} {f['url']} ({len(items)} haber)")
    return len(items)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    code = sys.argv[1].strip().lower()
    if not (len(code) == 2 and code.isascii() and code.isalpha()):
        raise SystemExit(f"Geçersiz ülke kodu: {code!r}")
    request = sys.argv[2] if len(sys.argv) > 2 else ""
    country = (sys.argv[3] if len(sys.argv) > 3 else "").strip() or code.upper()
    since = datetime.now(timezone.utc) - timedelta(days=3)
    kept, tried, failed = [], set(), []
    for round_no in range(2):
        result = bn.gemini("You are a careful news-media researcher. Output only what you are confident about.",
                           prompt(f"{country} (ISO code {code.upper()})", failed), SCHEMA)
        for f in result.get("feeds") or []:
            url = str(f.get("url", "")).strip()
            if not url.startswith("https://") or url in tried:
                continue
            tried.add(url)
            f = {"name": str(f.get("name") or "").strip()[:60] or url, "url": url,
                 "use": f.get("use") if f.get("use") in ("daily", "flash", "both") else "both",
                 "language": str(f.get("language", ""))[:5], "why": str(f.get("why", ""))[:120]}
            n = try_feed(f, since)
            if n:
                kept.append({**f, "items": n})
            else:
                failed.append(url)
            if len(kept) >= MAX_FEEDS:
                break
        if len(kept) >= 4 or len(kept) >= MAX_FEEDS:
            break
        time.sleep(5)
    OUT.mkdir(exist_ok=True)
    (OUT / f"{code}.json").write_text(json.dumps({
        "code": code, "country": country, "request": request,
        "createdAt": datetime.now(bn.TR_TZ).isoformat(timespec="seconds"),
        "feeds": kept, "rejected": failed}, ensure_ascii=False, indent=1), encoding="utf-8")
    bn.log(f"{country}: {len(kept)} çalışan kaynak bulundu, {len(failed)} adres çalışmadı.")


if __name__ == "__main__":
    main()
