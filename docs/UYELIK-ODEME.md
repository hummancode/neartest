# Üyelik, abonelik ve ödeme: altyapı araştırması

> Durum: **araştırma + çalışan prototip** (`account/`). Yayında hiçbir şey yok; site
> tamamen statik kalmaya devam ediyor. Aşağıdaki hukuki noktalar ikincil kaynaklardan
> derlenmiştir ve **bir hukukçu ile mali müşavire doğrulatılmalıdır.** Fiyat ve limitler
> 2026-11 itibarıyla aranmış, resmî sayfalardan kontrol edilmelidir.

## 0. Önce ürün kararı: Pro ne satacak?

Ücretli katman, sitenin temel kurallarını değiştirmez: **yatırım tavsiyesi yok, kullanıcının
finansal verisi sunucuda yok.** Bu iki kural, satılabilecek şeyi belirler.

| Pro adayı | Sunucu verisi | Uygun mu? |
|---|---|---|
| Reklamsız kullanım, tüm grafiklerde uzun dönem / gelişmiş karşılaştırma | yok | ✅ |
| Hesaplayıcı sonuçlarının PDF raporu (tarayıcıda üretilir) | yok | ✅ |
| Veri uyarıları: "TÜFE açıklandı", "reel mevduat faizi pozitife döndü" (herkes için aynı olay) | yalnızca e-posta + seçilen uyarı türleri | ✅ |
| Veri setlerini toplu indirme / API | yok | ⚠️ Her kaynağın **ticari kullanım** lisansı ayrıca kontrol edilmeli (EVDS şartları, OWID/Maddison CC BY, BIS, Big Mac vb.) |
| Varlıklarım'ı cihazlar arası eşitleme | şifreli blob | ⚠️ **Sahibin kararı.** Uçtan uca şifreleme ile sunucu içeriği okuyamaz, ama CLAUDE.md "finansal veriyi sunucuda saklama" diyor. Önerim: ilk sürümde yok; yerine dosyaya dışa/içe aktarma. |
| Kişiye özel portföy önerisi, "sinyal", model portföy | — | ❌ SPK izni gerektirir (bkz. §4) |

## 1. Mimari

```
Tarayıcı ──(statik sayfalar, hesaplayıcılar: veri tarayıcıda kalır)──► Cloudflare Pages
   │
   └─ /api/*  ─► Pages Functions / Worker ─► D1 (SQLite)
                     │                        kullanıcı e-postası, oturum özeti,
                     │                        abonelik durumu, yasal onay sürümleri
                     ├─► Ödeme sağlayıcısının barındırdığı ödeme sayfası (kart bilgisi bize gelmez)
                     │◄── imzalı webhook (abonelik başladı / yenilendi / başarısız / iptal)
                     └─► İşlemsel e-posta servisi (giriş bağlantısı)
```

- Statik site aynen kalır; yalnızca `/api/*` için küçük bir Worker eklenir. Aynı Cloudflare hesabı, ayrı sunucu yok.
- Sunucu yalnızca **kimlik, abonelik durumu ve yasal onayları** tutar (`account/schema.sql`).
- Kart bilgisi sağlayıcının sayfasında girilir; bu, kart güvenliği (PCI DSS) yükünü en aza indirir.
- Pro özellikleri sayfada `GET /api/me` → `entitlement.tier === "pro"` ile açılır. Sunucuya veri gönderen bir hesaplayıcı yine olmayacak.

**Maliyet (doğrulanmalı):** D1 ücretsiz katmanı için üçüncü taraf kaynaklar günde 5 milyon satır
okuma, 100 bin satır yazma ve 5 GB depolama bildiriyor; Workers Paid planı aylık 5 $ civarı.
Bu ölçekte bir üyelik sistemi ücretsiz katmanda rahat çalışır.

## 2. Kimlik doğrulama

| Seçenek | Artı | Eksi |
|---|---|---|
| **Kendi şifresiz e-posta girişimiz** (prototipte bu) | Bağımlılık yok, şifre saklanmaz, veri yurt dışında üçüncü bir kimlik servisine gitmez | E-posta teslimi bize ait; passkey / Google girişi yok |
| Better Auth (açık kaynak, kendi veritabanımızda) | Passkey, sihirli bağlantı, sosyal giriş eklentileri; D1 ile Drizzle/Kysely üzerinden çalıştığı bildiriliyor | Sık sürüm değişikliği, ek bağımlılık |
| Clerk / Auth0 / Firebase gibi barındırılan servisler | Hızlı kurulum, hazır arayüz | Kullanıcı verisi yurt dışı bir işleyende (KVKK yurt dışı aktarım), aylık ücret, bağımlılık |

**Önerim:** başlangıçta şifresiz e-posta girişi (prototip hazır). Passkey veya sosyal giriş
gerekirse Better Auth'a geçmek kolay, çünkü uygulama yalnızca `Store` ve `userFromSession` arayüzünü kullanıyor.

## 3. Ödeme sağlayıcısı

| Sağlayıcı | Model | Artı | Eksi / dikkat |
|---|---|---|---|
| **iyzico** | Yerli ödeme kuruluşu; kendi **Abonelik** ürünü var (plan, ödeme formu, webhook, iptal, kart güncelleme) | TL, yerli kartlar, Türk kullanıcıya tanıdık ödeme ekranı | Şirket (en az şahıs şirketi) ve sanal POS başvurusu gerekir; faturayı biz keseriz. Belgelere göre abonelik modülü ilk 3 ay ücretsiz, sonra aylık 199 TL (+ işlem komisyonu; güncel tarifeyi doğrulayın) |
| **PayTR** | Yerli; kart saklama + "tekrarlayan ödeme" servisi | TL, yerli kartlar | Yenileme zamanlamasını biz yönetiriz; Direkt API için PayTR onayı gerekir ve güvenlik sorumluluğu mağazadadır |
| **Paddle** / **Lemon Squeezy** | Yurt dışı "Merchant of Record": satışı onlar yapar, vergiyi ve faturayı onlar yönetir | Şirket kurmadan başlanabilir; Lemon Squeezy resmî listesinde Türkiye'ye banka ödemesi var | Fiyat genelde USD; Türk kullanıcı yurt dışı işlem olarak öder (kur, banka ek ücreti); komisyon daha yüksek (~%5 + 0,50 $ bildiriliyor); Türkiye'deki gelir yine beyan edilir. Lemon Squeezy'nin Stripe altyapısına taşındığı bildiriliyor, doğrulanmalı |
| Stripe | — | — | Kaynakların çoğuna göre Türkiye'de kurulu işletmeler doğrudan hesap açamıyor (yurt dışı şirket gerekir). Önermiyorum |

**Önerim:** hedef kitle Türkiye'deki kullanıcılar olduğu için **iyzico Abonelik**. Şirket kurulana kadar
denemek istenirse Lemon Squeezy / Paddle. Karar senin; prototip sağlayıcıdan bağımsız
(`PaymentProvider` arayüzü), seçim yapılınca yalnızca bir adaptör yazılır.

## 4. Yasal yükümlülükler (hukukçu ve mali müşavir kontrol listesi)

**Vergi ve şirket**
- Ücret almak için vergi mükellefiyeti gerekir (şahıs şirketi yeterli olabilir); e-Arşiv fatura ve KDV.
  Yerli ödeme kuruluşları şirket ister. Merchant of Record kullanılsa da gelir Türkiye'de beyan edilir.

**Tüketici hukuku (6502 sayılı Kanun)**
- Mesafeli Sözleşmeler Yönetmeliği: ödeme öncesi **ön bilgilendirme formu** ve **mesafeli satış sözleşmesi**.
- 14 günlük **cayma hakkı**. Anında ifa edilen dijital hizmet için istisna, kaynaklara göre ancak tüketici
  önceden bilgilendirilip açık onay verdiyse geçerli. Prototip, ödeme başlatmadan önce bu üç onayı
  (`mesafeli_satis`, `on_bilgilendirme`, `cayma_istisnasi`) **sürüm numarası ve zaman damgasıyla** kaydediyor.
- Abonelik Sözleşmeleri Yönetmeliği: sözleşmenin bir kopyası verilmeli; iptal, abone olmak kadar kolay
  olmalı. Prototipte tek uç noktayla iptal var. Otomatik yenileme öncesi bildirim yükümlülüğü doğrulanmalı.

**KVKK**
- Giriş formunda aydınlatma metni (prototip gösterilen sürümü kaydediyor).
- Yurt dışına aktarım: Cloudflare, e-posta servisi, ödeme sağlayıcısı. 2024 değişikliğinden sonra
  standart sözleşme ve Kurum'a bildirim gibi şartlar var; hukukçuya doğrulatın.
- VERBİS kayıt yükümlülüğü eşiğe bağlı; kontrol edilmeli. Saklama ve imha politikası.
- Silme hakkı: `DELETE /api/me` hesabı ve tüm kayıtları siliyor. Faturalar yasal süre boyunca muhasebede kalır.

**SPK — en kritik nokta**
- Taranan kaynaklar, ücret karşılığı **kişiye özel** al/sat yönlendirmesinin izinsiz yatırım
  danışmanlığı sayıldığını ve idari ve cezai yaptırım riski taşıdığını aktarıyor (ücretli "sinyal grupları" örnekleri).
- Bu yüzden Pro hiçbir zaman öneri, sinyal veya model portföy içermemeli. Pazarlama dili de
  "kazandırır", "en iyi yatırım" gibi ifadelerden uzak durmalı. Hesaplayıcılar, kullanıcının kendi
  girdisiyle mekanik hesap yapar. Ücretli olmalarının bu değerlendirmeyi değiştirip değiştirmediğini hukukçuya sorun.

**Ticari elektronik ileti**
- Pro tanıtımı içeren e-postalar ticari iletidir: açık onay ve İYS (İleti Yönetim Sistemi) kaydı.
  Giriş bağlantısı gibi işlemsel e-postalar bu kapsamda değil; bülten ve tanıtım e-postaları ayrı tutulmalı.

## 5. Prototipte uygulanan güvenlik önlemleri
- Şifre yok. Tek kullanımlık giriş bağlantısı 15 dakika geçerli, e-posta başına 15 dakikada en fazla 3 bağlantı.
- Token ve oturum kimlikleri rastgele; veritabanında yalnızca SHA-256 özetleri var (veritabanı sızsa bile oturum çalınamaz).
- Çerez `HttpOnly; Secure; SameSite=Lax`. Durum değiştiren isteklerde Origin kontrolü (CSRF).
- Webhook: HMAC imza ve sabit zamanlı karşılaştırma, ±5 dakika zaman damgası (tekrar saldırısı), olay kimliğiyle idempotency, sıra dışı eski olayların yok sayılması.
- Ödeme başarısız olursa 3 günlük ek süre, sonra ücretsiz katmana dönüş. Dönem sonunda iptal edilen abonelik, dönem bitene kadar Pro kalır.

## 6. Sahibin kararları
1. Pro'da ne olacak (§0)? Özellikle şifreli eşitleme evet/hayır.
2. Ödeme sağlayıcısı: iyzico (şirket gerekir) mi, Merchant of Record mı?
3. Şirket yapısı ve fiyat (prototipteki 99 TL / 990 TL **örnek**).
4. Hukukçu: sözleşme metinleri, KVKK, SPK değerlendirmesi. Mali müşavir: fatura ve KDV.

## Kaynaklar (2026-11 araması)
- iyzico Abonelik belgeleri: <https://docs.iyzico.com/en/products/subscription>, <https://docs.iyzico.com/v/en/products/subscription/subscription-implementation/subscription-transactions>
- PayTR kayıtlı kartla tekrarlayan ödeme: <https://dev.paytr.com/direkt-api/kart-saklama-api/kayitli-kart-tekrarlayan-odeme>
- Lemon Squeezy desteklenen ülkeler: <https://docs.lemonsqueezy.com/help/getting-started/supported-countries>
- Paddle, Türkiye: <https://www.paddle.com/billing/turkey>
- Stripe ve Türkiye (ikincil): <https://dodopayments.com/blogs/stripe-supported-countries-alternatives>, <https://community.shopify.com/t/can-i-connect-stripe-to-a-turkish-bank-account-for-my-shopify-site/281164>
- Cloudflare D1 limitleri (ikincil): <https://freetier.co/articles/cloudflare-d1-free-tier-limits-pricing-and-alternatives>
- İzinsiz yatırım danışmanlığı ve sinyal grupları (avukat yazısı): <https://bilalalyar.av.tr/yatirim-danismanligi-izinsiz-faaliyet-2026/>
- Mesafeli Sözleşmeler Yönetmeliği: <https://www.lexpera.com.tr/mevzuat/yonetmelikler/mesafeli-sozlesmeler-yonetmeligi>; dijital içerik ve cayma: <https://hukukcularevi.com/dijital-icerik-hizmet-tuketici-haklari-cayma-abonelik-iade-6502/>
- Better Auth + D1 (ikincil): <https://danielmschmidt.github.io/cfast/guides/auth/>
