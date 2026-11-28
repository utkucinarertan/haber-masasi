"""News - uygulamada seçilen yeni bir ülkeyi hazırlar (konu sunucusu GitHub Actions'ta başlatır).

Adımlar ayrı ayrı çalışır; iş akışındaki adım adları uygulamada ilerleme olarak görünür:

  sources <kod> <ad>   1 Haber kaynaklarını belirle: Gemini ülkenin bağımsız kaynaklarını önerir, her akış denenir
  review  <kod>        2 Kaynakları değerlendir: Google aramalı denetim (devlet/kayyum/kapanma), çalışmayanlar çıkar
  build   <kod>        3 Haberleri oluştur: her konuda en önemli 5 haber, günün değerlendirmesi
  publish <kod>        4 Yayınla: ülke ayarlara, haberler baskıya, başlıklar konu havuzuna yazılır ve gönderilir

Ara sonuçlar .prep/<kod>.json dosyasında tutulur. Ülke ayarlarda zaten varsa 1. ve 2. adım atlanır.
Yayın, haber döngüsünün aynı anda yaptığı değişikliklerle çakışırsa en güncel hâle yeniden uygulanır.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_news as bn  # noqa: E402

STATE_DIR = bn.ROOT / ".prep"
MIN_FEEDS = 3


def valid(code):
    return (len(code) == 2 and code.isascii() and code.isalpha()) or code == "world"


def state_path(code):
    return STATE_DIR / f"{code}.json"


def load_state(code):
    try:
        return json.loads(state_path(code).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"code": code}


def save_state(code, st):
    STATE_DIR.mkdir(exist_ok=True)
    state_path(code).write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def read_cfg():
    cfg = json.loads(bn.CONFIG.read_text(encoding="utf-8"))
    bn.apply_settings(cfg)
    return cfg


def existing(cfg, code):
    return next((c for c in cfg.get("countries", []) if c["code"] == code), None)


def step_sources(code, name):
    cfg = read_cfg()
    have = existing(cfg, code)
    if have and len(have.get("feeds", [])) >= MIN_FEEDS:
        bn.log(f"{code}: ülke ayarlarda zaten var ({len(have['feeds'])} kaynak); kaynak araması atlandı.")
        save_state(code, {"code": code, "name": have.get("name") or name, "existing": True})
        return
    import suggest_feeds as sf
    kept, failed = sf.find(code, f"{name} (ISO code {code.upper()})" if code != "world" else "World")
    bn.log(f"{name}: {len(kept)} çalışan kaynak, {len(failed)} çalışmayan adres.")
    if len(kept) < MIN_FEEDS:
        raise SystemExit(f"{name}: yeterli çalışan kaynak bulunamadı ({len(kept)}).")
    feeds = [{"name": f["name"], "url": f["url"], "use": f["use"], **({"topic": f["topic"]} if f.get("topic") else {})}
             for f in kept]
    save_state(code, {"code": code, "name": name, "feeds": feeds})


def step_review(code):
    st = load_state(code)
    if st.get("existing"):
        bn.log("Ülke ayarlarda zaten var; değerlendirme atlandı.")
        return
    cfg = read_cfg()
    blocked = [str(b.get("domain", "")).lower().removeprefix("www.") for b in cfg.get("blocked", []) if b.get("domain")]
    country = {"code": code, "name": st["name"], "topics": list(bn.TOPICS), "feeds": st["feeds"]}
    import review_sources as rs
    today = datetime.now(bn.zone(cfg)).date().isoformat()
    since = datetime.now(timezone.utc) - timedelta(days=3)
    try:
        feeds, report = rs.review_country(country, blocked, today, since)
        bn.log(f"Değerlendirme: +{len(report['added'])} / -{len(report['removed'])}")
        for r in report["removed"]:
            bn.log(f"  çıkarıldı: {r.get('name')} ({r.get('reason')})")
    except (RuntimeError, SystemExit) as e:   # denetim yapılamazsa denenmiş öneriler kullanılır
        bn.log(f"Uyarı: denetim yapılamadı ({e}); önerilen ve denenmiş kaynaklar kullanılıyor.")
        feeds = st["feeds"]
    feeds = [f for f in feeds if not rs.is_blocked(f["url"], blocked)]
    if len(feeds) < MIN_FEEDS:
        raise SystemExit(f"{st['name']}: değerlendirmeden sonra yeterli kaynak kalmadı ({len(feeds)}).")
    st["feeds"] = feeds
    save_state(code, st)


def country_entry(cfg, code, st):
    have = existing(cfg, code)
    if have:
        return have
    return {"code": code, "name": st["name"], "topics": list(bn.TOPICS), "feeds": st["feeds"],
            "addedBy": "app", "addedAt": datetime.now(timezone.utc).date().isoformat()}


def edition_date(cfg):
    """Bugünün baskısı varsa ona, yoksa en son baskıya eklenir (gece eklenen ülke sabah baskısında da olur)."""
    now = datetime.now(bn.zone(cfg))
    today = now.date().isoformat()
    if (bn.EDITIONS / today).is_dir():
        return today
    days = sorted((p.name for p in bn.EDITIONS.iterdir() if p.is_dir()), reverse=True) if bn.EDITIONS.is_dir() else []
    return days[0] if days else today


def step_build(code):
    st = load_state(code)
    cfg = bn.without_blocked(read_cfg())
    entry = country_entry(cfg, code, st)
    langs = [l for l in cfg.get("languages", []) if l in bn.LANGS] or ["tr"]
    now = datetime.now(bn.zone(cfg))
    items, failed = bn.collect(entry, {}, now - timedelta(hours=30))
    if failed:
        bn.log(f"Alınamayan kaynak: {', '.join(failed)}")
    if len(items) < bn.MIN_ITEMS:
        items, _ = bn.collect(entry, {}, now - timedelta(hours=72))   # sakin bir gün: üç güne genişlet
    if len(items) < bn.MIN_ITEMS:
        raise SystemExit(f"{entry['name']}: yeterli haber yok ({len(items)}).")
    r = None
    for attempt in range(3):
        try:
            r = bn.summarize(entry, items, langs)
            break
        except RuntimeError as e:
            bn.log(f"Özet alınamadı ({attempt + 1}. deneme): {e}")
            time.sleep(30)
    if not r:
        raise SystemExit("Haberler oluşturulamadı.")
    r["key"] = bn.desk_key(entry, langs, edition_date(cfg))
    bn.log(f"{len(items)} haberden {len(r['stories'])} seçildi.")
    st.update({"entry": entry, "result": r, "langs": langs})
    save_state(code, st)


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=bn.ROOT, check=check, capture_output=True, text=True)


def apply(code, st):
    cfg = read_cfg()
    if not existing(cfg, code):
        cfg.setdefault("countries", []).append(st["entry"])
        bn.CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    date = edition_date(cfg)
    langs = [l for l in st["langs"] if l in bn.LANGS]
    bn.write_editions(date, datetime.now(bn.zone(cfg)).isoformat(timespec="minutes"), langs,
                      [(code, st["result"])], order=[c["code"] for c in cfg["countries"]])
    bn.write_pool(bn.without_blocked(cfg), only={code})
    bn.log(f"{code}: {date} baskısına eklendi.")


def step_publish(code):
    st = load_state(code)
    if not st.get("result"):
        raise SystemExit("Yayınlanacak sonuç yok.")
    if os.environ.get("GITHUB_ACTIONS") != "true":
        apply(code, st)
        return
    for attempt in range(6):
        git("fetch", "-q", "origin", "main")
        git("reset", "-q", "--hard", "origin/main")
        apply(code, st)
        git("add", "-A", "docs/data")
        if git("diff", "--cached", "--quiet", check=False).returncode == 0:
            bn.log("Değişiklik yok.")
            return
        git("commit", "-q", "-m", f"Yeni ülke hazırlandı: {st.get('name') or code}")
        if git("push", "-q", "origin", "HEAD:main", check=False).returncode == 0:
            bn.log("Yayına gönderildi.")
            return
        bn.log(f"Gönderim çakıştı ({attempt + 1}); en güncel hâle yeniden uygulanıyor.")
        time.sleep(5 + 5 * attempt)
    raise SystemExit("Yayına gönderilemedi.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    step, code = sys.argv[1], sys.argv[2].strip().lower()
    if not valid(code):
        raise SystemExit(f"Geçersiz ülke kodu: {code!r}")
    name = (sys.argv[3] if len(sys.argv) > 3 else "").strip()[:60] or code.upper()
    if step == "sources":
        step_sources(code, name)
    elif step == "review":
        step_review(code)
    elif step == "build":
        step_build(code)
    elif step == "publish":
        step_publish(code)
    else:
        raise SystemExit(f"Bilinmeyen adım: {step}")


if __name__ == "__main__":
    main()
