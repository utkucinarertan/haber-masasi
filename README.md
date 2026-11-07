# Haber Masası: Almanya & Türkiye

Her sabah Almanya ve Türkiye'den 5-10'ar önemli haberi Türkçe özetleyen, günün kısa değerlendirmesini yazan kişisel haber uygulaması. Claude uygulamasından bağımsız çalışır:

- **Haberler:** Her sabah 08:00'de Claude masaüstü uygulamasındaki "Günlük Almanya–Türkiye haber baskısı" görevi tagesschau, DW Türkçe ve BBC Türkçe'den haberleri toplar (`build_news.py --collect`), Türkçe özetler ve `build_news.py --publish` ile GitHub'a gönderir. API anahtarı gerekmez; o saatte bilgisayarın açık ve Claude'un çalışıyor olması yeterli.
  - İleride bilgisayardan bağımsız çalıştırmak isterseniz: aşağıdaki API anahtarı adımlarını yapın ve `.github/workflows/daily-news.yml` içindeki `schedule` satırlarını açın.
- **Uygulama:** `docs/` klasörü GitHub Pages'te yayınlanan, kurulabilir bir web uygulamasıdır (PWA). Bilgisayarda görev çubuğuna, telefonda ana ekrana eklenir. Son 30 günün baskıları saklanır, son açılan baskı internetsiz de görünür.

## Kurulum (bir kez)

### 1. Claude API anahtarı (isteğe bağlı, yalnızca GitHub'da otomatik üretim için)
1. https://console.anthropic.com adresinde hesap açın, **Billing** bölümünden en az 5 dolar kredi yükleyin.
2. **API Keys** → **Create Key**. Anahtarı bir kenara kopyalayın (`sk-ant-...`).

Günde tek çağrı yapılır; maliyet ayda yaklaşık 2-4 dolardır.

### 2. GitHub deposu
1. https://github.com adresinde ücretsiz hesap açın.
2. **New repository** → ad: `haber-masasi`, **Public** seçin (GitHub Pages ücretsiz planda public depo ister), README eklemeden oluşturun.
3. Bu klasörü depoya gönderin:
   ```
   git remote add origin https://github.com/KULLANICI/haber-masasi.git
   git push -u origin main
   ```
4. Depoda **Settings → Secrets and variables → Actions → New repository secret**: ad `ANTHROPIC_API_KEY`, değer API anahtarınız.
5. **Settings → Pages**: Source **Deploy from a branch**, Branch **main**, klasör **/docs** → Save.
6. **Actions** sekmesi → **Günlük haber baskısı** → **Run workflow** ile ilk baskıyı hemen üretin.

Birkaç dakika sonra uygulama `https://KULLANICI.github.io/haber-masasi/` adresinde açılır.

## Bilgisayara kurulum (görev çubuğu)

**Önerilen, Microsoft Edge ile:** adresi Edge'de açın → adres çubuğundaki **Uygulamayı yükle** simgesi (ya da **⋯ → Uygulamalar → Bu siteyi uygulama olarak yükle**) → **Yükle**. Çıkan pencerede **Görev çubuğuna sabitle**'yi işaretleyin. Chrome'da da adres çubuğundaki yükle simgesi aynı işi yapar.

**Alternatif:** bu klasörde PowerShell açıp çalıştırın, sonra Başlat menüsünde **Haber Masası** → sağ tık → **Görev çubuğuna sabitle**:
```
powershell -ExecutionPolicy Bypass -File masaustu-kisayolu.ps1 -Url https://KULLANICI.github.io/haber-masasi/
```

## Telefona kurulum

**Android (Chrome):** adresi açın → sağ üstte **⋮** → **Ana ekrana ekle** → **Yükle**. Uygulama çekmecesinde kendi simgesiyle görünür.

**iPhone (Safari):** adresi Safari'de açın → alttaki **Paylaş** düğmesi → **Ana Ekrana Ekle** → **Ekle**.

Uygulama tam ekran, adres çubuğu olmadan açılır. Yeni baskı her sabah kendiliğinden gelir; uygulamayı açtığınızda ya da **Yenile**'ye bastığınızda yüklenir.

## Yerelde deneme

```
python -m http.server 8765 -d docs
```
Sonra http://localhost:8765 adresini açın. Yeni baskıyı yerelde üretmek için:
```
pip install -r requirements.txt
set ANTHROPIC_API_KEY=sk-ant-...
python scripts/build_news.py
```

## Dosyalar

| Yol | İşlevi |
|---|---|
| `scripts/build_news.py` | Haberleri çeker, Claude ile özetler, baskıyı yazar |
| `.github/workflows/daily-news.yml` | Her sabah 08:00'de betiği çalıştırır ve sonucu kaydeder |
| `docs/index.html` | Uygulamanın kendisi |
| `docs/manifest.webmanifest`, `docs/sw.js` | Kurulabilirlik ve internetsiz açılış |
| `docs/data/` | Günlük baskılar (`editions/YYYY-MM-DD.json`) ve liste (`index.json`) |
| `masaustu-kisayolu.ps1` | Windows için Başlat menüsü / masaüstü kısayolu |

Saati değiştirmek için workflow dosyasındaki `cron` satırını düzenleyin (UTC'dir; Türkiye saati = UTC+3).
