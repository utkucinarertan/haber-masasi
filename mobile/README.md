# Haber Masası: telefon uygulaması (Google Play + App Store)

Bu klasör, `docs/` altındaki web uygulamasını (PWA) Android ve iOS uygulamasına çeviren
**Capacitor 8** projesidir.

- Uygulama kimliği (paket adı / Bundle ID): `app.habermasasi`
- Uygulama adı: **Haber Masası**
- Arayüz (HTML/CSS/JS) uygulamanın içine gömülür. Haberler (`data/*.json`) ise her açılışta
  canlı sunucudan çekilir; varsayılan adres `https://utkucinarertan.github.io/haber-masasi/`.
- `admin.html` ve `sw.js` uygulamaya konmaz. Footer'daki "Yönetim" bağlantısı uygulamada gizlenir.
- Profil, dil ve konu seçimleri, web sürümünde olduğu gibi yalnızca telefonda (localStorage) tutulur.

## Klasör yapısı

| Yol | Ne işe yarar |
|---|---|
| `capacitor.config.json` | Uygulama kimliği, adı, açılış ekranı ve durum çubuğu ayarları |
| `scripts/copy-web.mjs` | `docs/` klasörünü `www/` içine kopyalar (`data/`, `admin.html` ve `sw.js` hariç), kopyadaki `index.html`'e veri adresini ekleyen küçük bir betik yerleştirir. `docs/index.html` dosyasına dokunmaz. |
| `scripts/make-icon-source.mjs` | `docs/icons/favicon.svg` dosyasından 1024 px ikon ve 2732 px açılış ekranı kaynaklarını (`assets/`) üretir |
| `android/` | Android Studio projesi |
| `ios/` | Xcode projesi (Swift Package Manager ile) |
| `keystore.properties.example` | Android imza anahtarı ayarlarının örneği |
| `www/` | Üretilen kopya. Git'e girmez, her `npm run sync` ile yeniden oluşur. |

## Bu bilgisayarda olanlar ve eksikler (27.11.2026'da kontrol edildi)

| Araç | Durum |
|---|---|
| Node.js 22 / npm 10 | Kurulu |
| JDK 21 (Temurin) | Kurulu, `JAVA_HOME` ayarlı |
| **Android SDK / Android Studio** | **Yok.** Bu yüzden APK henüz derlenmedi. |
| Xcode (iOS) | Windows'ta çalışmaz, **Mac gerekir** |

### Android Studio'yu kur (bir kez)

1. https://developer.android.com/studio adresinden Android Studio'yu indirip kur.
2. İlk açılışta "Standard" kurulumu seç. Android SDK, Platform 36 ve Build-Tools kendiliğinden gelir.
3. Kurulum bitince SDK genelde `C:\Users\Utku\AppData\Local\Android\Sdk` klasöründe olur.
   `mobile/android/local.properties` dosyasını oluşturup içine şunu yaz (Git'e girmez):
   ```
   sdk.dir=C\:\\Users\\Utku\\AppData\\Local\\Android\\Sdk
   ```
   Android Studio bu dosyayı projeyi ilk açışta kendisi de yazar.

## Günlük kullanım

Tüm komutlar `mobile/` klasöründe çalıştırılır:

```powershell
cd C:\Users\Utku\Downloads\haber-masasi-app\mobile
```

```powershell
npm install
```

Web tarafında `docs/` değiştiyse uygulamaya aktarmak için:

```powershell
npm run sync
```

Haber verisi başka bir adrese taşındığında (ör. Cloudflare Pages):

```powershell
$env:HABER_DATA_BASE = "https://haber-masasi.pages.dev/"; npm run sync
```

İkon veya açılış ekranı değişince (kaynak `docs/icons/favicon.svg`; daha iyi bir tasarım için `assets/icon-only.png` dosyasını 1024×1024 bir PNG ile değiştirebilirsin):

```powershell
npm run assets
```

### Test için APK (Android Studio kurulduktan sonra)

```powershell
npm run android:debug
```

Çıkan dosya: `android\app\build\outputs\apk\debug\app-debug.apk`. Telefona USB ile atıp kurabilirsin
(telefonda "Bilinmeyen kaynaklar"a izin vermek gerekir). İstersen `npm run open:android` ile projeyi
Android Studio'da açıp ▶ ile emülatörde de çalıştırabilirsin.

> **Canlı adres yedeği:** Gömülü sürümde bir sorun çıkarsa `capacitor.config.json` dosyasına
> `"server": { "url": "https://utkucinarertan.github.io/haber-masasi/" }` ekleyip `npx cap sync`
> çalıştırırsan uygulama doğrudan web sitesini açar. Apple bu tür "sadece web sitesi" uygulamaları
> sık reddettiği için (Kural 4.2) gömülü sürüm önerilir.

---

## 1. Hesaplar (bunları senin açman gerekiyor)

### Google Play Console: 25 $, tek seferlik
1. https://play.google.com/console adresinden bir Google hesabıyla kaydol.
2. Hesap türünü seç: **Kişisel** ya da **Kuruluş**. Satış yapacaksan ve şirketin varsa "Kuruluş"
   seçmek daha iyi. Bu durumda D-U-N-S numarası gerekir; ücretsiz alınır ama birkaç gün sürebilir.
3. Kimlik doğrulaması ve 25 $ ödeme.
4. **Kişisel hesap uyarısı:** 13.11.2023'ten sonra açılan kişisel hesaplar, uygulamayı herkese açmadan
   önce **en az 12 test kullanıcısıyla 14 gün boyunca kapalı test** yapmak zorunda. Kuruluş
   hesaplarında bu şart yok.
5. Ücretli uygulama ya da uygulama içi satın alma için Play Console'da **Ödemeler profili** açılır
   (banka hesabı ve vergi bilgisi).

### Apple Developer Program: 99 $/yıl
1. Bir Apple ID ile https://developer.apple.com/programs/enroll/ adresinden kaydol. İki adımlı
   doğrulama açık olmalı.
2. Bireysel ya da kuruluş üyeliği seçilir. Kuruluş üyeliği için D-U-N-S numarası gerekir.
3. Ücretli uygulama ya da abonelik satacaksan App Store Connect'te **Agreements, Tax and Banking**
   bölümünde "Paid Apps" sözleşmesini imzala, banka ve vergi bilgilerini (W-8BEN) gir.
4. **Mac gerekir.** Xcode yalnızca macOS'ta çalışır. Seçenekler: kendi Mac'in, kiralık bulut Mac
   (MacinCloud, AWS EC2 Mac) ya da Codemagic / GitHub Actions macOS gibi bir CI servisi.

## 2. İmza anahtarları

### Android
Play Store, yükleme anahtarıyla imzalanmış bir **AAB** ister. Anahtarı bir kez oluştur ve **asla
kaybetme**. Yedeğini şifre yöneticisinde ve ayrı bir diskte tut.

```powershell
cd C:\Users\Utku\Downloads\haber-masasi-app\mobile
```

```powershell
keytool -genkeypair -v -keystore haber-masasi-upload.jks -alias upload -keyalg RSA -keysize 2048 -validity 10000
```

(`keytool`, kurulu JDK 21 ile gelir. Şifreleri komut sorduğunda sen yaz.)

Sonra `keystore.properties.example` dosyasını `keystore.properties` adıyla kopyala ve şifreleri doldur.
Bu dosya ve `.jks` Git'e girmez (`.gitignore`). Play Console'da **Play App Signing** açık kalsın:
Google son imzayı kendisi atar, sen yalnızca yükleme anahtarını kullanırsın. Yükleme anahtarını
kaybedersen Play Console'dan sıfırlatabilirsin.

### iOS
Xcode → proje → **Signing & Capabilities** → Team olarak Apple Developer hesabını seç ve
"Automatically manage signing" kutusunu işaretle. Sertifika ve profilleri Xcode kendisi oluşturur.

## 3. Sürüm derleme

### Android: yayın AAB'si
1. Her yeni sürümde `android/app/build.gradle` içinde `versionCode` değerini 1 artır
   (`versionName` ise kullanıcının gördüğü sürüm, ör. "1.0.1").
2. Derle:
   ```powershell
   npm run android:release
   ```
3. Çıkan dosya: `android\app\build\outputs\bundle\release\app-release.aab`
4. Play Console → Uygulama oluştur → **Test → Kapalı test** (kişisel hesapta zorunlu) → AAB'yi yükle.
   14 gün sonra **Üretim**'e geçir.

### iOS: IPA (Mac üzerinde)
1. Projeyi Mac'e al (`git clone`), `mobile/` klasöründe sırayla:
   ```
   npm install
   npm run sync
   npx cap open ios
   ```
2. Xcode'da hedef cihaz olarak **Any iOS Device (arm64)** seç. App → General bölümünde Version
   (ör. 1.0.0) ve Build (her yüklemede artır) değerlerini ayarla.
3. **Product → Archive** → Organizer açılır → **Distribute App → App Store Connect → Upload**.
4. App Store Connect'te uygulamayı oluştur (Bundle ID `app.habermasasi`), yüklenen derlemeyi önce
   TestFlight'ta dene, sonra "Submit for Review".
5. Şifreleme sorusu: `Info.plist` dosyasında `ITSAppUsesNonExemptEncryption = NO` ayarlı. Uygulama
   yalnızca standart HTTPS kullandığı için muaf.

## 4. Mağaza metinleri

Kategori: **Haberler / News** (iki mağazada da). Yaş sınırı anketinde şiddet ve benzeri sorulara
"haber içeriği, ara sıra" seçeneği uygun. Sonuç genelde Play'de 12+, App Store'da 12+ ya da 17+ olur;
anket cevaplarına göre değişir.

> Uzunluk sınırları: Play'de kısa açıklama en fazla 80, uzun açıklama en fazla 4000 karakter.
> App Store'da altyazı (subtitle) 30, anahtar kelimeler 100 karakter (virgülle, boşluksuz).

### Türkçe
- **Kısa açıklama (Play) / Altyazı (App Store):**
  - Play: `Almanya, Türkiye ve dünyadan günün önemli haberleri, kısa özetlerle.`
  - App Store altyazısı: `Günün haberleri, kısa özetle`
- **Uzun açıklama:**
  ```
  Haber Masası, günün önemli gelişmelerini tek ekranda toplar.

  • Almanya, Türkiye ve dünyadan seçilmiş haberler
  • Her haber için kısa, anlaşılır bir özet ve değerlendirme
  • Son dakika sekmesiyle gün içindeki gelişmeler
  • Gündem, ekonomi, teknoloji, spor, kültür-sanat gibi konuları siz seçin
  • Türkçe, İngilizce ve Almanca okuyun
  • Kendi profilinizi oluşturun: ülkeler, konular ve dil tercihiniz

  Hesap açmanız gerekmez. Tercihleriniz yalnızca telefonunuzda saklanır;
  kişisel veri toplamıyor, sizi takip etmiyoruz.

  Haber özetleri yapay zekâ yardımıyla hazırlanır; her haberin altında
  orijinal kaynağa bağlantı bulunur.
  ```
- **Anahtar kelimeler (App Store):** `haber,son dakika,almanya,türkiye,gündem,özet,ekonomi,spor,dünya,manşet`

### English
- **Short description (Play):** `Today's key news from Germany, Türkiye and the world, briefly summarised.`
- **Subtitle (App Store):** `Today's news, in brief`
- **Full description:**
  ```
  Haber Masası brings the day's most important stories together on one screen.

  • Hand-picked news from Germany, Türkiye and around the world
  • A short, clear summary and context for every story
  • Breaking news tab for developments throughout the day
  • Choose your topics: top stories, economy, tech, sports, culture
  • Read in English, Turkish or German
  • Create your own profile: countries, topics and language

  No account needed. Your preferences are stored only on your phone;
  we collect no personal data and do not track you.

  Summaries are prepared with the help of AI; every story links to
  the original source.
  ```
- **Keywords (App Store):** `news,breaking,germany,turkey,headlines,summary,world,economy,sports,daily`

### Deutsch
- **Kurzbeschreibung (Play):** `Die wichtigsten Nachrichten aus Deutschland, der Türkei und der Welt – kurz.`
- **Untertitel (App Store):** `Nachrichten des Tages, kurz`
- **Ausführliche Beschreibung:**
  ```
  Haber Masası bündelt die wichtigsten Meldungen des Tages auf einem Bildschirm.

  • Ausgewählte Nachrichten aus Deutschland, der Türkei und der Welt
  • Zu jeder Meldung eine kurze, verständliche Zusammenfassung mit Einordnung
  • „Eilmeldungen“-Tab für Entwicklungen im Tagesverlauf
  • Themen selbst wählen: Aktuelles, Wirtschaft, Technik, Sport, Kultur
  • Auf Deutsch, Türkisch oder Englisch lesen
  • Eigenes Profil anlegen: Länder, Themen und Sprache

  Kein Konto nötig. Ihre Einstellungen werden nur auf Ihrem Telefon
  gespeichert; wir erheben keine personenbezogenen Daten und tracken nicht.

  Die Zusammenfassungen entstehen mit Unterstützung von KI; jede Meldung
  verlinkt auf die Originalquelle.
  ```
- **Schlüsselwörter (App Store):** `nachrichten,eilmeldung,türkei,deutschland,schlagzeilen,news,welt,wirtschaft,sport`

## 5. Gizlilik politikası

İki mağaza da herkese açık bir **gizlilik politikası URL'si** ister. Aşağıdaki metni web sitesinde
ayrı bir sayfa olarak yayınla (ör. `privacy.html`). Bu sayfayı `docs/` içine diğer oturum ya da sen
eklemelisin; bu klasörün kapsamı dışında. Ardından adresi iki mağazaya da gir. `[...]` yerlerini doldur.

```
Haber Masası – Gizlilik Politikası
Son güncelleme: [tarih]

Haber Masası ("uygulama") [ad soyad / şirket adı, adres] tarafından sunulur.
İletişim: [e-posta]

1. Hesap yok. Uygulamayı kullanmak için kayıt olmanız veya giriş yapmanız gerekmez.

2. Cihazda saklanan veriler. Seçtiğiniz dil, ülkeler, konular ve isteğe bağlı
   olarak girdiğiniz profil adı yalnızca cihazınızda (uygulamanın yerel
   depolama alanında) saklanır. Bu bilgiler bize veya üçüncü kişilere
   gönderilmez. Uygulamayı silerek veya uygulama verilerini temizleyerek
   tamamen kaldırabilirsiniz.

3. Takip ve reklam yok. Uygulama analiz, reklam veya izleme araçları içermez;
   reklam kimliğinize erişmez, konum, kişiler, fotoğraf gibi izinler istemez.

4. Haber içeriğinin yüklenmesi. Uygulama, haber listelerini [sunucu adresi]
   adresinden indirir. Yazı tipleri Google Fonts üzerinden yüklenir. Bu
   sunucular, her internet bağlantısında olduğu gibi IP adresinizi ve teknik
   bağlantı bilgilerini (tarayıcı türü, zaman) kısa süreli olarak işleyebilir.
   Bu bilgiler bizim tarafımızdan kimliğinizle eşleştirilmez veya saklanmaz.

5. Dış bağlantılar. Bir habere dokunduğunuzda ilgili yayıncının sitesi açılır;
   o sitenin kendi gizlilik politikası geçerlidir.

6. Yapay zekâ. Haber özetleri sunucuda, yapay zekâ hizmeti (Google Gemini)
   kullanılarak hazırlanır. Bu süreçte sizin hiçbir verinizi işlemeyiz.

7. Çocuklar. Uygulama 13 yaşından küçük çocuklara yönelik değildir ve
   bilerek çocuklardan veri toplamaz.

8. Haklarınız (KVKK / GDPR). Sizinle ilgili sunucuda kişisel veri tutmadığımız
   için silinecek veya aktarılacak bir kayıt yoktur. Sorularınız için
   [e-posta] adresine yazabilirsiniz.

9. Değişiklikler. Bu politika değişirse güncel hali bu sayfada yayınlanır.
```

> Diğer oturumda tasarlanan **kullanıcının eklediği konular** sunucuya gönderilmeye başlarsa bu metin
> ve aşağıdaki veri güvenliği cevapları **güncellenmek zorunda**.

## 6. Play "Veri güvenliği" formu ve Apple "Gizlilik etiketleri"

Bugünkü sürüm için (veri yalnızca cihazda kalıyor, sunucuya kullanıcı verisi gitmiyor):

**Google Play → Uygulama içeriği → Veri güvenliği**
| Soru | Cevap |
|---|---|
| Uygulamanız, zorunlu kullanıcı veri türlerinden herhangi birini topluyor veya paylaşıyor mu? | **Hayır** |
| (Bu nedenle tür listesi boş kalır.) | |
| Aktarılan tüm veriler şifreleniyor mu? | Evet (yalnızca HTTPS) |
| Kullanıcılar veri silme isteğinde bulunabilir mi? | Veri toplanmadığı için uygulanmaz |

Not: Google'ın tanımına göre yalnızca cihazda işlenip cihazdan çıkmayan veriler "toplanan veri"
sayılmaz.

**Play → Uygulama içeriği'ndeki diğer sorular:** Reklam içeriyor mu: *Hayır*. Hedef kitle: *18+*
(ya da 13+; çocuklara yönelik seçme, ek kurallar getirir). Haber uygulaması mı: *Evet*. Bu durumda
Play, "Haber ve Dergiler" politikası gereği yayıncı ve iletişim bilgisini (künye) uygulamada ya da
web sitesinde ister. Hükümet uygulaması: *Hayır*. Finans ya da sağlık özelliği: *Yok*.

**App Store Connect → App Privacy**
- "Do you or your third-party partners collect data from this app?" → **No**
- Sonuç etiketi: **Data Not Collected**

## 7. Ekran görüntüleri

Telefonda (ya da emülatörde) uygulamayı açıp şunları çek:

1. **Ana ekran, Türkçe**: Almanya masası açık, birkaç manşet ve özet görünüyor
2. **Son dakika** sekmesi
3. Bir haberin **özeti ve değerlendirmesi** açık
4. **Profilim** ekranı: ülke ve konu seçimi
5. **Dil seçimi**: aynı ekran İngilizce ve Almanca (her dilin mağaza sayfasına o dilin görüntüleri)
6. Türkiye ve Dünya masaları

Gerekli boyutlar:
| Mağaza | Boyut | Adet |
|---|---|---|
| Google Play telefon | En az 1080 px kenar, 16:9 veya 9:16 (ör. 1080×1920) | 2–8 |
| Google Play öne çıkan görsel | **1024×500** (zorunlu) | 1 |
| Google Play ikon | 512×512 PNG (`assets/icon-only.png` küçültülerek) | 1 |
| App Store iPhone 6.9" | 1320×2868 (ya da 1290×2796) | 1–10 |
| App Store iPad 13" | 2064×2752. Yalnızca iPad desteği açık kalırsa gerekir. iPad'i kapatmak için Xcode → General → Supported Destinations bölümünden iPad'i kaldır. | 1–10 |

İpucu: Android Studio emülatöründe "Pixel 8 Pro", Xcode Simulator'da "iPhone 16 Pro Max" seçip
kamera simgesiyle çekmek en kolayı.

---

## Satış öncesi yapılacaklar

- [ ] **Barındırmayı GitHub Pages'ten taşı.** GitHub Pages kuralları ticari kullanıma (SaaS, gelir
      amaçlı site) izin vermiyor. Öneri: **Cloudflare Pages** (ücretsiz katman, ticari kullanıma açık,
      GitHub deposuna bağlanıp `docs/` klasörünü yayınlar). Taşıdıktan sonra
      `$env:HABER_DATA_BASE = "https://<yeni-adres>/"; npm run sync` çalıştır ve yeni sürüm yayınla.
      CORS için `Access-Control-Allow-Origin: *` başlığı gerekli. Cloudflare'de `docs/_headers`
      dosyasıyla `/data/*` yoluna eklenir.
- [ ] **Gemini'yi ücretli katmana geçir.** Ücretsiz katmanın kullanım şartları ticari ürün için
      uygun değil (ücretsiz katmanda Google, girdileri ürün geliştirmede kullanabiliyor). Google AI
      Studio / Cloud'da faturalandırmayı aç ve aylık bütçe uyarısı koy.
- [ ] **Hukuki inceleme: yayıncı içeriği.** Başka yayıncıların başlıklarını ve bunlardan üretilmiş
      yapay zekâ özetlerini **ücretli** bir üründe göstermek telif ve yan haklar açısından riskli.
      AB'de (Almanya dahil) basın yayıncılarının yan hakkı (DSM Direktifi md. 15, Alman UrhG
      §87f vd.) var. Türkiye'de FSEK geçerli. Bir avukata şunları sor: başlık ve kısa alıntı sınırı,
      kaynak gösterme ve bağlantı biçimi, özetlerin "türev eser" sayılıp sayılmadığı, gerekirse
      lisans (ör. haber ajansı API'leri). Mağazalar da Play "Haberler" politikası ve App Store 5.2
      (fikri mülkiyet) kapsamında künye ve izin sorabilir.
- [ ] **Künye ve iletişim (Impressum).** Almanya'da yayın yapan haber uygulamasında
      Impressum zorunlu (DDG §5, MStV §18). Uygulamaya ve siteye bir "Künye / Impressum" sayfası ekle.
- [ ] **Kullanıcının eklediği konular için backend.** Diğer oturumda tasarlanıyor. Kullanıcıların
      kendi konuları sunucuda haber üretimini tetikleyecekse bir API (kimlik doğrulama ya da
      anonim cihaz kimliği, kötüye kullanım ve maliyet sınırı) gerekir. Bu geldiğinde gizlilik
      politikası, Play veri güvenliği formu ve App Store gizlilik etiketi güncellenmeli.
- [ ] **Gelir modeli.** Ücretli indirme mi, abonelik mi? Abonelik ya da uygulama içi satın alma
      seçilirse Android'de **Google Play Billing**, iOS'ta **StoreKit** zorunlu (harici ödeme bağlantısı
      kurallara aykırı). Capacitor için RevenueCat gibi bir eklenti kullanılabilir; ayrıca iş gerekir.
- [ ] **Apple 4.2 (asgari işlevsellik) riski.** Apple, web sitesini kabuğa saran uygulamaları
      reddedebiliyor. Şansı artırmak için: çevrimdışı açılış (arayüz zaten gömülü), bildirimler
      (ör. son dakika push bildirimi, `@capacitor/push-notifications`), paylaş menüsü
      (`@capacitor/share`) gibi yerel özellikler eklenebilir.
- [ ] **Kişisel Play hesabıysa:** 12 test kullanıcısı bul, 14 günlük kapalı testi planla.
- [ ] Destek e-postası ve web sitesi adresini belirle (iki mağaza da istiyor).
