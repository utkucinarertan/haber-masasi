# Haber Masası

Seçilen ülkelerin günün önemli haberlerini her sabah Türkçe, İngilizce ve Almanca özetleyen haber uygulaması.

- **Kullanıcılar** hiçbir hesap ya da anahtar girmez. Uygulamayı açar, bir dil ve istediği ülkeleri (birden fazla) seçer. **Yenile** en son baskıyı getirir.
- **Yönetici** `admin.html` sayfasından bir kez GitHub'a bağlanır ve Gemini anahtarını, yayın saatini, dilleri, ülkeleri ve her ülkenin haber kaynaklarını (RSS) belirler.
- **Baskı** GitHub Actions'ta hazırlanır. Ayarlanan saatte (varsayılan 07:00, Türkiye) kaynaklardan son 30 saatin haberleri çekilir. Ücretsiz Google Gemini her ülke için 5-10 önemli haberi seçer ve seçili dillerin hepsinde başlık, özet ve günün değerlendirmesini yazar. Bilgisayarın açık olması gerekmez.

Uygulama: https://utkucinarertan.github.io/haber-masasi/
Yönetim: https://utkucinarertan.github.io/haber-masasi/admin.html

## Yönetici kurulumu (bir kez)

Yönetim sayfası her adımı kendisi anlatır:
1. **GitHub bağlantısı.** https://github.com/settings/personal-access-tokens/new adresinde yalnızca `haber-masasi` deposu için anahtar oluşturun. **Contents**, **Actions** ve **Secrets** izinleri **Read and write** olmalı. Anahtarı yapıştırıp **Bağlan** deyin. Anahtar yalnızca o cihazın tarayıcısında saklanır.
2. **Gemini anahtarı.** https://aistudio.google.com/app/apikey adresinden ücretsiz anahtar alın (kart istemez). Yapıştırıp **Kaydet** deyin. Anahtar GitHub'a şifrelenerek `GEMINI_API_KEY` adıyla kaydedilir.
3. **Yayın saati ve diller.**
4. **Ülkeler ve kaynaklar.**
5. **Ayarları kaydet**, ardından ilk baskı için **Şimdi hazırla**.

Ücretsiz katmanda Google, gönderilen metni ürün geliştirmek için kullanabilir. Buraya gönderilen yalnızca herkese açık haber metinleridir. Her baskı ülke başına tek Gemini çağrısı yapar; kullanıcı sayısı maliyeti ve kotayı etkilemez.

## Kullanıcılar için kurulum

- **Bilgisayar (Edge ya da Chrome):** Adresi açın, adres çubuğundaki **Uygulamayı yükle** simgesine ve ardından **Yükle**'ye tıklayın. Çıkan pencerede **Görev çubuğuna sabitle**'yi seçin.
- **iPhone (Safari):** Adresi Safari'de açın, sonra **Paylaş → Ana Ekrana Ekle → Ekle**.
- **Android (Chrome):** Adresi açın, sonra **⋮ → Ana ekrana ekle → Yükle**.

## Yapı

| Yol | İşlevi |
|---|---|
| `docs/index.html` | Kullanıcı uygulaması (dil ve ülke seçimi, baskılar) |
| `docs/admin.html` | Yönetim sayfası |
| `docs/data/config.json` | Yayın saati, diller, ülkeler ve kaynaklar (yönetim sayfası yazar) |
| `docs/data/editions/YYYY-MM-DD/<dil>.json` | Günlük baskılar; `docs/data/index.json` listesi, son 30 gün |
| `scripts/build_news.py` | Haberleri çeker, Gemini ile özetler, baskıları yazar (`--force`: saate bakmadan) |
| `.github/workflows/daily-news.yml` | Saatte bir kontrol eder; ayarlanan saatten sonra o günün baskısı yoksa üretir |
| `docs/manifest.webmanifest`, `docs/sw.js` | Kurulabilirlik ve internetsiz açılış |
| `masaustu-kisayolu.ps1` | Windows için Başlat menüsü / masaüstü kısayolu |

Yerelde deneme:
```
python -m http.server 8765 -d docs
GEMINI_API_KEY=... python scripts/build_news.py --force
```
