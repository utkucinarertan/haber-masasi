"""Almanya & Türkiye Haber Masası - günlük baskı üretici.

RSS kaynaklarından haberleri çeker, Claude API ile Türkçe özetleyip
değerlendirir ve docs/data altına JSON olarak yazar.

Çalıştırma:
  ANTHROPIC_API_KEY=... python scripts/build_news.py   # topla + özetle + yaz (GitHub Actions)
  python scripts/build_news.py --collect haberler.json  # yalnızca haberleri topla
  python scripts/build_news.py --publish baski.json     # hazır baskıyı yaz, commit et, gönder
                                                         # (Claude masaüstü sabah görevi bu ikisini kullanır)
"""
import html
import json
import os
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "data"
EDITIONS = DATA / "editions"
KEEP_DAYS = 30
TR_TZ = timezone(timedelta(hours=3))

FEEDS = [
    ("tagesschau", "https://www.tagesschau.de/xml/rss2"),
    ("tagesschau Inland", "https://www.tagesschau.de/inland/index~rss2.xml"),
    ("DW Türkçe", "https://rss.dw.com/rdf/rss-tur-all"),
    ("BBC Türkçe", "https://feeds.bbci.co.uk/turkce/rss.xml"),
]

MODEL = "claude-opus-5-5"

ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "category": {"type": "string"},
        "importance": {"type": "integer", "enum": [1, 2, 3]},
        "source": {"type": "string"},
        "url": {"type": "string"},
        "time": {"type": "string"},
    },
    "required": ["title", "summary", "category", "importance", "source", "url", "time"],
    "additionalProperties": False,
}
DESK_SCHEMA = {
    "type": "object",
    "properties": {
        "overview": {"type": "string"},
        "items": {"type": "array", "items": ITEM_SCHEMA},
    },
    "required": ["overview", "items"],
    "additionalProperties": False,
}
EDITION_SCHEMA = {
    "type": "object",
    "properties": {"germany": DESK_SCHEMA, "turkey": DESK_SCHEMA},
    "required": ["germany", "turkey"],
    "additionalProperties": False,
}

SYSTEM = """Sen Türkçe yayın yapan bir haber masasının editörüsün. Okuyucu Türkiye'de yaşıyor ve hem Almanya'yı hem Türkiye'yi yakından takip ediyor.

Sana Almanca ve Türkçe RSS kaynaklarından son haberler verilecek. Görevin:
- Doğrudan Almanya'yı ilgilendiren 5-10 haber ve doğrudan Türkiye'yi ilgilendiren 5-10 haber seç. ABD, Ukrayna gibi başka ülkelerin haberleri ancak Almanya'yı ya da Türkiye'yi doğrudan etkiliyorsa girer.
- Siyaset, ekonomi, güvenlik ve toplum haberlerine öncelik ver. Aynı olayı birden fazla kaynak veriyorsa tek habere birleştir.
- Her haber için kısa, net bir Türkçe başlık ve 2-3 cümlelik Türkçe özet yaz. Yalnızca kaynakta yazanları kullan; bilgi uydurma.
- category: tek ya da iki kelimelik Türkçe kategori (Siyaset, Ekonomi, Güvenlik, Toplum, Teknoloji, Yargı, Çevre, Kültür gibi).
- importance: 3 çok önemli, 2 önemli, 1 gündem. Her ülkede en fazla 3 haber 3 alabilir. Listeyi önem sırasına göre diz.
- source: haberin geldiği kaynağın adı; url ve time: verilen haberin bağlantısı ve yayın zamanı, değiştirmeden.
- overview: her ülke için günün genel tablosunu değerlendiren 3-4 cümlelik Türkçe paragraf. Haberler arasındaki bağlantıyı ve neden önemli olduklarını anlat.
Doğal, akıcı, gazete Türkçesi kullan; çeviri kokan cümlelerden kaçın."""


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "HaberMasasi/1.0 (+github pages)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def clean(text):
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return " ".join(text.split())


def strip_tracking(url):
    return re.sub(r"\?(at_medium|maca)=.*$", "", url or "")


def parse_time(raw):
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def collect(since):
    items, failed = [], []
    for source, url in FEEDS:
        try:
            root = ET.fromstring(fetch(url))
        except Exception as e:  # noqa: BLE001 - one bad feed must not stop the edition
            print(f"Kaynak alınamadı: {source} ({e})", file=sys.stderr)
            failed.append(source)
            continue
        for it in (e for e in root.iter() if e.tag.split("}")[-1] == "item"):
            f = {c.tag.split("}")[-1]: (c.text or "") for c in it}
            when = parse_time(f.get("pubDate") or f.get("date"))
            link = strip_tracking(f.get("link", "").strip())
            if not when or when < since or not link.startswith("https://") or "whatsapp.com" in link:
                continue
            items.append({
                "source": source.replace(" Inland", ""),
                "title": clean(f.get("title")),
                "description": clean(f.get("description"))[:600],
                "url": link,
                "time": when.isoformat(),
            })
    seen, unique = set(), []
    for it in items:
        if it["url"] not in seen:
            seen.add(it["url"])
            unique.append(it)
    return unique, failed


def summarize(items):
    import anthropic  # yalnızca API ile özetlerken gerekir

    client = anthropic.Anthropic()
    request = dict(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM,
        output_config={
            "effort": "low",
            "format": {"type": "json_schema", "schema": EDITION_SCHEMA},
        },
        messages=[{
            "role": "user",
            "content": "Son haberler (JSON):\n" + json.dumps(items, ensure_ascii=False),
        }],
    )
    try:
        # Server-side fallback: a safety decline is retried on another model in the same call.
        response = client.beta.messages.create(
            betas=["server-side-fallback-2026-07-01"], fallbacks="default", **request
        )
    except anthropic.BadRequestError as e:
        print(f"Fallback olmadan yeniden deneniyor: {e}", file=sys.stderr)
        response = client.messages.create(**request)
    if response.stop_reason == "refusal":
        raise SystemExit("Model isteği reddetti; bugünkü baskı üretilmedi.")
    if response.stop_reason == "max_tokens":
        raise SystemExit("Yanıt yarıda kesildi (max_tokens); bugünkü baskı üretilmedi.")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def write_edition(edition):
    EDITIONS.mkdir(parents=True, exist_ok=True)
    (EDITIONS / f"{edition['date']}.json").write_text(
        json.dumps(edition, ensure_ascii=False, indent=1), encoding="utf-8")
    dates = sorted((p.stem for p in EDITIONS.glob("*.json")), reverse=True)
    for old in dates[KEEP_DAYS:]:
        (EDITIONS / f"{old}.json").unlink()
    (DATA / "index.json").write_text(
        json.dumps({"editions": dates[:KEEP_DAYS]}, ensure_ascii=False), encoding="utf-8")


def check_edition(edition):
    for desk in ("germany", "turkey"):
        d = edition.get(desk) or {}
        if not isinstance(d.get("overview"), str) or not d["overview"].strip():
            raise SystemExit(f"{desk}.overview eksik")
        items = d.get("items")
        if not isinstance(items, list) or not 3 <= len(items) <= 12:
            raise SystemExit(f"{desk}.items 3-12 haber olmalı")
        for it in items:
            missing = [k for k in ITEM_SCHEMA["required"] if k not in it]
            if missing:
                raise SystemExit(f"{desk} haberinde eksik alan: {', '.join(missing)}")
            if it["importance"] not in (1, 2, 3):
                raise SystemExit(f"{desk}: importance 1, 2 ya da 3 olmalı")
            it["url"] = strip_tracking(it["url"])


def git(*args):
    subprocess.run(["git", "-C", str(ROOT), *args], check=True)


def publish(path):
    now = datetime.now(TR_TZ)
    edition = json.loads(Path(path).read_text(encoding="utf-8"))
    check_edition(edition)
    edition = {"date": edition.get("date") or now.date().isoformat(),
               "updatedAt": now.isoformat(timespec="minutes"),
               "germany": edition["germany"], "turkey": edition["turkey"]}
    git("pull", "--rebase", "--autostash", "-q")
    write_edition(edition)
    git("add", "-A", "docs/data")
    if subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--quiet"]).returncode:
        git("commit", "-q", "-m", f"Günlük baskı {edition['date']}")
    git("push", "-q")
    print(f"{edition['date']} yayında: Almanya {len(edition['germany']['items'])}, "
          f"Türkiye {len(edition['turkey']['items'])} haber")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) == 3 and sys.argv[1] == "--collect":
        items, failed = collect(since=datetime.now(TR_TZ) - timedelta(hours=30))
        Path(sys.argv[2]).write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        note = f", alınamayan kaynak: {', '.join(failed)}" if failed else ""
        print(f"{len(items)} haber toplandı{note}")
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--publish":
        publish(sys.argv[2])
        return
    now = datetime.now(TR_TZ)
    items, failed = collect(since=now - timedelta(hours=30))
    if len(items) < 5:
        raise SystemExit(f"Yeterli haber alınamadı ({len(items)}); bugünkü baskı üretilmedi.")
    result = summarize(items)
    edition = {"date": now.date().isoformat(), "updatedAt": now.isoformat(timespec="minutes"), **result}
    write_edition(edition)
    note = f", alınamayan kaynak: {', '.join(failed)}" if failed else ""
    print(f"{edition['date']}: Almanya {len(result['germany']['items'])}, "
          f"Türkiye {len(result['turkey']['items'])} haber{note}")


if __name__ == "__main__":
    main()
