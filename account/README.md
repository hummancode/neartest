# account/ — üyelik ve ödeme PROTOTİPİ

> **Yayında değil.** Site hâlâ tamamen statik. Bu klasör, ileride bir "Pro" katmanı
> açılırsa kullanılacak altyapının çalışan bir taslağıdır. Hiçbir sayfa buraya bağlı
> değil, gerçek ödeme sağlayıcısı yok, hiçbir anahtar yok.
> Araştırma ve kararlar: [`docs/UYELIK-ODEME.md`](../docs/UYELIK-ODEME.md).

## Ne var?
| Dosya | İş |
|---|---|
| `schema.sql` | D1 (SQLite) tabloları: kullanıcı, giriş bağlantısı, oturum, abonelik, webhook kaydı, yasal onaylar. **Finansal kullanıcı verisi için tablo yok.** |
| `src/auth.ts` | Şifresiz e-posta girişi (tek kullanımlık bağlantı, 15 dk). Token ve oturum kimliklerinin yalnızca SHA-256 özeti saklanır. E-posta başına hız sınırı. |
| `src/entitlements.ts` | Abonelik durum makinesi (active, trialing, past_due, canceled, expired) ve "şu an Pro mu?" kararı; ödeme başarısızsa 3 günlük ek süre. Saf fonksiyonlar. |
| `src/billing/provider.ts` | Ödeme sağlayıcısı arayüzü. Uygulama yalnızca bunu tanır; sağlayıcı değişirse tek dosya yazılır. |
| `src/billing/mock.ts` | Sahte sağlayıcı: webhook'ları gerçekleri gibi HMAC-SHA256 ile imzalar, zaman damgası kontrolü yapar. |
| `src/billing/iyzico.ts` | Gerçek adaptörün iskeleti (uygulanmadı). |
| `src/app.ts` | HTTP katmanı (`Request → Response`): giriş, çıkış, `/api/me`, ödeme başlatma, iptal, webhook, hesap silme. Origin kontrolü (CSRF), webhook tekrarına karşı idempotency. |
| `src/worker.ts` | Cloudflare Workers giriş noktası taslağı (bellek içi depo, yalnızca geliştirme). |
| `src/plans.ts` | ÖRNEK planlar ve fiyatlar (karar değil). |

## Uç noktalar
| Yöntem ve yol | Açıklama |
|---|---|
| `POST /api/auth/link` `{email}` | Giriş bağlantısı gönderir (202). Geçersiz e-posta 400, sınır aşımı 429. |
| `POST /api/auth/verify` `{token}` | Bağlantıyı doğrular, oturum çerezi verir (HttpOnly, Secure, SameSite=Lax). İlk girişte hesap açılır. |
| `POST /api/auth/logout` | Oturumu siler. |
| `GET /api/me` | E-posta, Pro hakkı ve abonelik durumu. |
| `DELETE /api/me` | Hesabı ve ona bağlı tüm kayıtları siler; aktif abonelik varsa önce iptal eder (KVKK silme hakkı). |
| `POST /api/billing/checkout` `{plan, accept}` | Mesafeli satış sözleşmesi, ön bilgilendirme ve cayma istisnası onayları **üçü birden** yoksa 400. Onayların sürümünü kaydeder, sağlayıcının ödeme sayfası adresini döner. Kart bilgisi sunucumuza hiç gelmez. |
| `POST /api/billing/cancel` | Yenilemeyi durdurur; erişim dönem sonuna kadar sürer. |
| `POST /api/billing/webhook` | Sağlayıcıdan gelen olay. İmza ve zaman damgası doğrulanır, her olay bir kez uygulanır, sıra dışı gelen eski olaylar yok sayılır. |

## Test
```bash
cd account && npm test
```
25 test: durum makinesi (10), giriş (7), uçtan uca API akışı (8). Bağımlılık yok, Node 22+.

## Yayına almak için eksikler
1. Sağlayıcı seçimi ve gerçek adaptör (bkz. `docs/UYELIK-ODEME.md`), sandbox ile uçtan uca deneme.
2. D1 deposu (`Store` arayüzünün SQL hâli) ve `wrangler.toml`; sırlar `wrangler secret put` ile.
3. E-posta gönderimi (işlemsel e-posta servisi) ve SPF/DKIM.
4. Sitede `/hesap` sayfaları: giriş formu (aydınlatma metniyle), plan seçimi, abonelik yönetimi, iptal (en az kaydolmak kadar kolay).
5. Hukukçu tarafından hazırlanmış metinler: mesafeli satış sözleşmesi, ön bilgilendirme formu, abonelik koşulları, KVKK aydınlatma metni, çerez metni.
6. IP bazlı hız sınırı (Cloudflare Rate Limiting) ve hata izleme.
