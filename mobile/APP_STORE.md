# NewsByFocus: App Store'a çıkış rehberi

Son güncelleme: 28.11.2026. Karar: **önce ücretsiz**, **bireysel Apple hesabı**, derleme **GitHub Actions'ta (Mac gerekmez)**,
mağaza adı **NewsByFocus**.

## Hazır olanlar

| Konu | Durum |
|---|---|
| Uygulama kimliği (Bundle ID) | `com.newsbyfocus.app` (ilk yüklemeden sonra değiştirilemez) |
| Ad | NewsByFocus (ana ekranda, uygulamada ve mağazada) |
| Cihaz | Yalnızca iPhone (iPad ekran görüntüsü gerekmez) |
| Diller | 12 arayüz dili; `Info.plist` → `CFBundleLocalizations` |
| Şifreleme beyanı | `ITSAppUsesNonExemptEncryption = NO` (yalnızca HTTPS) |
| Yerel özellikler (Apple 4.2 için) | Paylaş menüsü, kaynağı uygulama içinde açma (Safari görünümü), internetsiz açılış, gece/gündüz modu |
| Gizlilik politikası | https://www.newsbyfocus.com/privacy.html (EN/TR/DE) |
| Destek + künye | https://www.newsbyfocus.com/support.html (EN/TR/DE) |
| Bulut derleme | `.github/workflows/ios-release.yml` (TestFlight'a yükler), `ios-check.yml` (imzasız deneme; **başarılı**) |
| Ekran görüntüleri | `mobile/store/screenshots/en` ve `/tr`: 5'er adet, 1290×2796 (6,9" iPhone) |

## Senin yapacakların (sırayla)

### 1. Künye bilgilerini ver (5 dk)
`docs/legal.js` içindeki üç alan doldurulmalı: **ad soyad**, **destek e-postası**, **açık adres**. Bireysel hesapta mağazada
satıcı olarak zaten gerçek adın görünür. Almanya'ya hitap eden haber hizmetinde künye (Impressum) ve adres zorunludur. Bilgileri
bana yazman yeterli, ben yerleştiririm. Adresini yayınlamak istemezsen bir "c/o" künye adresi hizmeti kullanılabilir.

### 2. Apple Developer Program'a kaydol (99 $/yıl, 1-2 gün)
1. https://developer.apple.com/programs/enroll/ → Apple ID ile giriş (iki adımlı doğrulama açık olmalı).
2. **Individual / Sole Proprietor** seç, kimlik doğrulamasını tamamla, ücreti öde.
3. Onay e-postası gelince **Membership details** sayfasındaki **Team ID**'yi (10 karakter) not et.
4. App Store Connect → **Business**: ücretsiz uygulama için yalnızca "Free Apps Agreement" yeterli (otomatik). Banka/vergi
   bilgisi ücretli sürüme geçince gerekir.

### 3. App Store Connect'te uygulama kaydını aç (10 dk)
1. https://appstoreconnect.apple.com → **Apps** → **+** → **New App**.
2. Platform: iOS · Name: **NewsByFocus** · Primary language: **English (U.S.)** (Türkçe ve Almanca sonra yerelleştirme olarak eklenir)
   · Bundle ID: listede `com.newsbyfocus.app` yoksa önce https://developer.apple.com/account/resources/identifiers → **+** →
   App IDs → Explicit: `com.newsbyfocus.app`, Description: NewsByFocus · SKU: `newsbyfocus-ios` · User access: Full.

### 4. App Store Connect API anahtarı oluştur (5 dk)
1. App Store Connect → **Users and Access** → **Integrations** → **App Store Connect API** → **Team Keys** → **+**.
2. Name: `github-actions`, Access: **Admin** (bulutta imza sertifikası oluşturabilmek için gerekli).
3. **Issuer ID**'yi ve anahtarın **Key ID**'sini not et, **Download** ile `AuthKey_XXXXXXXXXX.p8` dosyasını indir (yalnızca bir kez
   indirilebilir; güvenli bir yerde sakla).

### 5. Dört bilgiyi GitHub'a gizli olarak gir (5 dk)
https://github.com/utkucinarertan/haber-masasi/settings/secrets/actions → **New repository secret**:

| Ad | Değer |
|---|---|
| `APPLE_TEAM_ID` | 2. adımdaki Team ID |
| `ASC_KEY_ID` | 4. adımdaki Key ID |
| `ASC_ISSUER_ID` | 4. adımdaki Issuer ID |
| `ASC_KEY_P8` | `.p8` dosyasını Not Defteri ile aç, `-----BEGIN PRIVATE KEY-----` dahil tamamını yapıştır |

### 6. İlk derlemeyi gönder (otomatik, ~20 dk)
GitHub → **Actions** → **iOS yayını (TestFlight)** → **Run workflow** → Sürüm: `1.0.0`. Bitince derleme App Store Connect →
**TestFlight**'ta 5-30 dakika içinde görünür. Kendi iPhone'una **TestFlight** uygulamasını kurup kendini "Internal Tester"
olarak ekle ve dene.

### 7. Mağaza sayfasını doldur ve incelemeye gönder (30-60 dk)
Aşağıdaki metinleri ve `mobile/store/screenshots` görüntülerini gir; **App Privacy**, **Age Rating** ve **App Review Information**
bölümlerini doldur; TestFlight'taki derlemeyi seç → **Add for Review** → **Submit**. İnceleme genelde 1-3 gün sürer.

## Mağaza bilgileri

- **Kategori:** News (birincil) · Magazines & Newspapers değil, News
- **Fiyat:** Ücretsiz · **Ülkeler:** Tümü (Çin anakarası hariç tutulmalı: haber uygulamaları orada ayrı lisans ister)
- **Destek URL:** https://www.newsbyfocus.com/support.html
- **Pazarlama URL:** https://www.newsbyfocus.com
- **Gizlilik URL:** https://www.newsbyfocus.com/privacy.html
- **Telif (Copyright):** `2026 [Ad Soyad]`

### English (U.S.)
- **Name:** NewsByFocus
- **Subtitle (≤30):** `The day's key news, your way`
- **Promotional text (≤170):** `Pick your countries and topics. Every morning NewsByFocus selects the 5 most important stories per topic from independent sources and writes them in your language.`
- **Description:**
```
NewsByFocus gives you the day's most important news from the countries you follow, written in your language.

• Your countries: choose from more than 50 of the world's largest economies, Türkiye and World news.
• Your topics: headlines, economy, technology, sport and culture – plus any topic you add yourself, such as inflation, climate or artificial intelligence.
• Only what matters: for every topic the app selects the 5 most important distinct stories of the day, with a short summary and a link to the original source.
• Breaking news: short updates during the day; important ones stay at the top.
• Your language: 12 languages, including English, Spanish, French, Arabic, Hindi, Chinese, Portuguese, Russian, Bengali, Indonesian, German and Turkish. News from any country is translated for you.
• Independent sources: each country's editorially independent outlets plus international broadcasters such as BBC and DW. State-controlled media are not used; sources are reviewed regularly.
• Private by design: no account, no ads, no tracking. Your profile stays on your phone.
• Day and night mode, sharing, and reading without a connection.

Summaries and translations are written by AI based only on the facts in the sources. Always follow the link to read the full article.
```
- **Keywords (≤100):** `news,headlines,breaking,daily,summary,world,economy,technology,sport,translate,briefing,ai`
- **What's New:** `First release.`

### Türkçe
- **Ad:** NewsByFocus
- **Altyazı (≤30):** `Günün önemli haberleri, size göre`
- **Tanıtım metni (≤170):** `Ülkelerinizi ve konularınızı seçin. NewsByFocus her sabah bağımsız kaynaklardan her konuda en önemli 5 haberi seçer ve sizin dilinizde yazar.`
- **Açıklama:**
```
NewsByFocus, takip ettiğiniz ülkelerden günün en önemli haberlerini sizin dilinizde sunar.

• Ülkeleriniz: dünyanın en büyük 50'yi aşkın ekonomisi, Türkiye ve Dünya haberleri arasından seçin.
• Konularınız: Gündem, Ekonomi, Teknoloji, Spor ve Kültür-Sanat; ayrıca enflasyon, iklim, yapay zekâ gibi kendi eklediğiniz konular.
• Yalnızca önemli olan: her konuda günün en önemli 5 tekil haberi, kısa özet ve özgün kaynağa bağlantıyla.
• Son dakika: gün içinde kısa güncellemeler; önemli olanlar üstte kalır.
• Sizin diliniz: Türkçe, İngilizce, Almanca, İspanyolca, Fransızca, Arapça, Hintçe, Çince, Portekizce, Rusça, Bengalce ve Endonezce. Her ülkenin haberleri sizin için çevrilir.
• Bağımsız kaynaklar: her ülkenin editoryal olarak bağımsız yayın organları ile BBC, DW gibi uluslararası yayıncılar. Devlet denetimindeki medya kullanılmaz; kaynaklar düzenli olarak gözden geçirilir.
• Gizlilik: hesap yok, reklam yok, takip yok. Profiliniz telefonunuzda kalır.
• Gece ve gündüz modu, paylaşma ve internetsiz okuma.

Özetler ve çeviriler yalnızca kaynaklardaki bilgilere dayanarak yapay zekâ tarafından yazılır. Haberin tamamı için her zaman kaynağa gidin.
```
- **Anahtar kelimeler (≤100):** `haber,gündem,son dakika,manşet,özet,dünya,ekonomi,teknoloji,spor,çeviri,bülten,yapay zeka`

### Deutsch
- **Untertitel (≤30):** `Die wichtigsten News, für dich`
- **Werbetext (≤170):** `Wähle Länder und Themen. Jeden Morgen wählt NewsByFocus aus unabhängigen Quellen die 5 wichtigsten Meldungen pro Thema – in deiner Sprache.`
- **Beschreibung:** englischen Text sinngemäß übernehmen (oder mich um eine fertige Fassung bitten).
- **Schlüsselwörter:** `nachrichten,schlagzeilen,eilmeldung,täglich,zusammenfassung,welt,wirtschaft,technik,sport,ki`

## App Privacy (gizlilik etiketi)

"Do you or your third-party partners collect data from this app?" → **Yes**, yalnızca:

| Veri türü | Kullanım | Kimliğe bağlı mı? | Takip? |
|---|---|---|---|
| **User Content → Other User Content** (kullanıcının yazdığı konu, örn. "inflation") | App Functionality | **No** | **No** |

Gerekçe: kendi konuları ve çeviri istekleri sunucuya gider ve konu 14 gün saklanır (gizlilik politikası madde 3). Ad, profil,
ülke seçimleri cihazda kalır; reklam, analiz, takip yok. Sonuç etiketi: *Data Not Linked to You → User Content*.

## Age Rating (yaş sınırı)

Haber uygulaması: savaş, şiddet ve suç haberleri içerebilir.
- Violence (Realistic/Cartoon): **Infrequent/Mild** · Mature/Suggestive Themes: **Infrequent/Mild**
- Unrestricted Web Access: **No** (yalnızca haber kaynaklarına bağlantı, Safari görünümünde)
- User-generated content: **No** (kullanıcıların yazdığı konular başkalarına gösterilmez)
- Beklenen sonuç: **13+**. Kategori sorusunda "News" seçildiği için Apple haber içeriğini bu yaşta kabul eder.

## App Review Information (inceleme notu)

- Sign-in required: **No**
- Notes:
```
NewsByFocus needs no account. On first launch choose a language, enter any name, pick one or more countries (e.g. Germany, Türkiye or World are ready instantly) and tap Save.
Countries that nobody has chosen before are prepared on our server the first time (sources are found, checked and summarised); this can take a few minutes and the app shows the progress.
Content: the app selects and summarises stories from public RSS feeds of editorially independent news outlets with AI and always links to the original article (opened in an in-app Safari view). Users can share stories via the iOS share sheet; the latest edition is cached for offline reading.
Contact: [e-posta]
```

## Bilinmesi gereken riskler

1. **Apple 4.2 (asgari işlevsellik) ve 4.2.2 (içerik toplayıcı):** Apple, web sitesini kabuğa saran ya da yalnızca bağlantı toplayan
   uygulamaları reddedebilir. Elimizdeki güçlü yanlar: kişiye özel seçim ve özet, 12 dile çeviri, paylaş menüsü, uygulama içi
   tarayıcı, internetsiz açılış. Ret gelirse ilk eklenecek özellik **son dakika bildirimleri** (push) olmalı.
2. **5.2 (fikri mülkiyet) ve telif:** Başka yayıncıların başlıkları ve bunlardan yapılmış yapay zekâ özetleri gösteriliyor. Ücretsiz
   sürümde bile Apple izin sorabilir; ücretli sürüme geçmeden önce mutlaka bir avukata danışılmalı (AB'de basın yayıncısı yan
   hakkı, Türkiye'de FSEK).
3. **Barındırma:** GitHub Pages ticari kullanıma uygun değil. Ücretsiz sürüm sorun değil; ücretli sürümden önce Cloudflare
   Pages'e taşınmalı.
4. **Gemini:** Kullanıcı sayısı artınca ücretsiz kota yetmez ve ücretsiz katmanın şartları ticari ürün için uygun değil. Mağazaya
   çıkmadan önce Google AI Studio'da faturalandırmayı açıp aylık bütçe sınırı koy.
5. **Çin:** Çin anakarası App Store'unda haber uygulamaları ayrı izin ister; o ülkeyi dağıtımdan çıkar.
