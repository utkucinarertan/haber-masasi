# Konu sunucusu (Cloudflare Worker)

Kişinin uygulamada eklediği kendi konuları (ör. "Beşiktaş") için o ülkenin bağımsız kaynaklarından
en önemli **5 tekil haberi** Gemini ile seçer ve kişinin **diline çevirir**.

- İlk eklemede özet hemen üretilir (5-10 sn); sonra her sabah Almanya saatiyle 05:00'ten itibaren yenilenir.
- Aynı konu + ülke + dil herkes için tek özettir: maliyet kullanıcı değil konu sayısıyla artar.
- Kişisel bilgi tutulmaz: yalnızca konu, ülke, dil ve son istenme günü. 14 gün kimse istemeyen konu silinir.
- Haberler uygulamanın yayınladığı havuzdan gelir (`data/pool/<ülke>.json`, yönetim sayfasındaki kaynaklar).
- Sunucu kurulana kadar uygulama eskisi gibi havuzda anahtar kelime eşleşmesi gösterir.

## Kurulum (bir kez, ~10 dakika)

1. **Cloudflare hesabı** açın: https://dash.cloudflare.com/sign-up (ücretsiz, kart istemez).
2. Bu klasörde terminal açın ve sırayla çalıştırın:

```bash
npm install
```

```bash
npx wrangler login
```
   Tarayıcı açılır, **Allow** deyin.

```bash
npx wrangler kv namespace create TOPICS
```
   Çıkan `id = "..."` değerini `wrangler.toml` içindeki `BURAYA_KV_ID` yerine yazın.

```bash
npx wrangler secret put GEMINI_API_KEY
```
   Gemini anahtarınızı (yönetim sayfasında kaydettiğiniz anahtar) yapıştırıp Enter'a basın.

```bash
npx wrangler deploy
```
   Sonunda `https://haber-masasi-konular.<hesabınız>.workers.dev` adresi çıkar.

3. Bu adresi `docs/data/config.json` dosyasına `"topicApi": "https://..."` olarak ekleyin (Claude'a söyleyin, o ekler).

## Sınırlar (ücretsiz plan)

- Günde 100.000 istek, 1.000 KV yazma: yaklaşık **400 farklı konu/dil** günde yenilenebilir.
- Sabah yenilemesi 10 dakikada bir en fazla 15 özet; 05:00-06:59 arası ~180 özet. Fazlası ilk istendiğinde üretilir.
- Daha fazlası için Workers Paid (aylık 5 $) yeterli; kod değişmez.

## Yerel deneme (hesap gerekmez)

```bash
npm test
```

```bash
node test/serve.mjs
```
   `http://localhost:8787/topic?country=tr&q=Beşiktaş&lang=de` (Gemini taklit; gerçek için `MOCK_GEMINI=0 GEMINI_API_KEY=...`).
