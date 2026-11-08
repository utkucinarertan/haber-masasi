# Haber Masası: Almanya & Türkiye

Her sabah Almanya ve Türkiye'den 5-10'ar önemli haberi Türkçe özetleyen, günün kısa değerlendirmesini yazan haber uygulaması. Kullananların hiçbir hesap ya da anahtar girmesi gerekmez.

- **Baskı:** GitHub Actions her sabah 07:00'de (Türkiye) tagesschau, DW Türkçe ve BBC Türkçe'den haberleri çeker, ücretsiz Google Gemini ile Türkçe özetler ve `docs/data` altına kaydeder. Bilgisayarın açık olması gerekmez.
- **Uygulama:** `docs/` klasörü https://utkucinarertan.github.io/haber-masasi/ adresinde yayınlanır. Bilgisayarda görev çubuğuna, telefonda ana ekrana eklenir. **Yenile** en son baskıyı getirir. Son 30 günün baskıları saklanır.

## Yönetici kurulumu (bir kez, yalnızca depo sahibi)

1. https://aistudio.google.com/app/apikey → Google hesabıyla giriş → **Create API key** → kopyala. Ücretsizdir, kart istemez. (Ücretsiz katmanda Google gönderilen metni ürün geliştirmek için kullanabilir; gönderilen yalnızca herkese açık haber metinleridir.)
2. https://github.com/utkucinarertan/haber-masasi/settings/secrets/actions/new → Name: `GEMINI_API_KEY`, Secret: anahtar → **Add secret**.
3. **Actions → Günlük haber baskısı → Run workflow** ile ilk baskıyı hemen üretin.

## Kullanıcılar için kurulum

**Bilgisayar (Edge ya da Chrome):** adresi açın → adres çubuğundaki **Uygulamayı yükle** simgesi → **Yükle** → çıkan pencerede **Görev çubuğuna sabitle**.
Alternatif (Windows): `powershell -ExecutionPolicy Bypass -File masaustu-kisayolu.ps1 -Url https://utkucinarertan.github.io/haber-masasi/`

**iPhone (Safari):** adresi Safari'de açın → **Paylaş** → **Ana Ekrana Ekle** → **Ekle**.

**Android (Chrome):** adresi açın → **⋮** → **Ana ekrana ekle** → **Yükle**.

## Yerelde deneme

```
python -m http.server 8765 -d docs
GEMINI_API_KEY=... python scripts/build_news.py
```

## Dosyalar

| Yol | İşlevi |
|---|---|
| `scripts/build_news.py` | Haberleri çeker, Gemini (yoksa Claude) ile özetler, baskıyı yazar; `--collect` / `--publish` ile elle baskı da hazırlanabilir |
| `.github/workflows/daily-news.yml` | Her sabah 07:00'de betiği çalıştırır ve sonucu kaydeder |
| `docs/index.html` | Uygulamanın kendisi |
| `docs/manifest.webmanifest`, `docs/sw.js` | Kurulabilirlik ve internetsiz açılış |
| `docs/data/` | Günlük baskılar (`editions/YYYY-MM-DD.json`) ve liste (`index.json`) |
| `masaustu-kisayolu.ps1` | Windows için Başlat menüsü / masaüstü kısayolu |

Saati değiştirmek için workflow dosyasındaki `cron` satırını düzenleyin (UTC'dir; Türkiye saati = UTC+3).
