# Changelog

- 2026-11-01 — Aşama 1–2: reel getiri motoru (17 test), EVDS çekme/keşif betikleri,
  JSON üretici, günlük GitHub Actions. Veri henüz ÖRNEK (sentetik); EVDS anahtarı
  gelince `pipeline.discover` ile seri kodları doğrulanacak.
- 2026-11-01 — Adım 0: kurulum doğrulandı (17 test, örnek JSON). `.gitignore` tamamlandı;
  workflow'a yazma izni, anahtar yoksa fetch'i atlama ve "değiştiyse commit" eklendi;
  içerik değişmediyse `generated_at` korunuyor (gereksiz günlük commit olmasın).
- 2026-11-01 — Adım 1 / Aşama 3: Astro sitesi (`site/`). Reel Tablo ana sayfası (1/3/5/10 yıl,
  nominal TL · USD · reel TL, kümülatif + yıllık, 5 yıllık reel trend çizgisi), örnek veri bandı,
  kaynaklar/notlar, Metodoloji sayfası; koyu/açık tema, Anton + Inter (yerel barındırılan).
  320–1280 px'te taşma yok. Workflow artık siteyi de derliyor. Cloudflare yayını henüz yok.
- 2026-11-01 — Adım 2 / Aşama 4: Nominal illüzyon makinesi (`/nominal-illuzyon`). Ay + TL tutarı →
  bugünkü karşılık TÜFE, dolar, gram altın cinsinden; hesap tarayıcıda, veri gönderilmez.
  Motor TypeScript'e taşındı (`site/src/lib/engine.ts`); Python ve TS aynı 22 vakayı
  (`tests/cases.json`) koşuyor. 1200×1500 PNG kart (örnek veriyse kartta da uyarı).
  Builder artık `site/data/seviyeler.json` da üretiyor. Asgari ücret serisi eksik.
- 2026-11-01 — Aşama 5: Kişisel enflasyon hesaplayıcı (`/kisisel-enflasyon`). Motor:
  `normalize_shares`, `inflation_contributions`, `personal_inflation` (önce test; Python + TS aynı
  30 ortak vaka). Builder `site/data/tufe_gruplari.json` üretiyor (12 TÜFE ana grubu, 12 aylık
  değişim, ağırlıklar `data/manual/tufe_agirliklari.csv`'den, yoksa ÖRNEK). 1200×1500 kart,
  "kişisel hesaptır, resmi enflasyon değildir" uyarısı sayfada ve kartta. Grup kodları/ağırlıkları doğrulanmadı.
- 2026-11-01 — Aşama 6: Reel faiz tablosu (`/reel-faiz`). Motor: `trailing_real_rates` (güncel faiz /
  son 12 ay TÜFE) ve `ex_post_real_rates` (12 ay önceki faiz / gerçekleşen TÜFE), önce test.
  Builder `site/data/reel_faiz.json` üretiyor (son 36 ay; hesap Python'da, sayfa sadece gösteriyor).
  Kredi faizi serisi ve Reel Tablo'ya "TL Kredi (borç maliyeti)" satırı eklendi (kod doğrulanmadı,
  kredi türü seçilmedi). Ex-ante (beklenti anketi) henüz yok. Trend çizgisi düz serilerde gürültüyü büyütmüyor.
- 2026-11-01 — Aşama 7: Bülten sayfası (platform seçilince `config.ts`'e form adresi yazılır; 3. taraf
  script yok) + arşiv düzeni, Yasal uyarı ve KVKK gizlilik metni (TASLAK, hukuki inceleme gerekli),
  404, `_headers`, robots.txt, alt menü. Kaynak tablosunda her serinin son veri ayı. `npm run check`
  (bağımlılıksız derleme sonrası kontrol) workflow'a eklendi. Tüm sayfalar 320/1280 px, açık/koyu
  temada konsol hatası ve taşma olmadan test edildi. README yeniden yazıldı (Cloudflare adımları).
- 2026-11-02 — MVP 1/4: Gerçek veri için API'siz yol: `data/manual/<seri>.csv` (+ `.meta.json`), EVDS web
  dışa aktarım biçimleri (`;`, `2024-1`, ondalık virgül, günlük→aylık ortalama) destekleniyor; öncelik
  raw (API) → manual → örnek. Faiz serileri yüzde→ondalık ölçekleniyor (EVDS'den gelecek veride
  100 kat hata önlendi). `/veri` sayfası (her serinin kökeni, kodu, aralığı) ve `durum.json`.
  Asgari ücret (isteğe bağlı, asla örneklenmez, değişim aylarından ileri doldurma) illüzyon
  makinesine ve karta bağlandı.
- 2026-11-02 — MVP 2/4: Varlık detay sayfaları (`/varlik/<id>`, 7 adet): "100 TL ne oldu?" etkileşimli
  grafiği (nominal / USD / reel, 1-3-5-10 yıl, log ölçek gerekirse, crosshair + ipucu, klavye ile
  gezinme, doğrudan uç etiketleri; palet doğrulayıcıdan geçti). Yollar Python'da `index_paths` ile
  hesaplanıyor (önce test; son değerler Reel Tablo ile birebir). Ana sayfa kartları detaya bağlandı.
- 2026-11-02 — MVP 3/4: Hesaplayıcılar için paylaşılabilir bağlantı ("Bağlantıyı kopyala"): girdiler URL'nin
  `#` kısmında (sunucuya gitmez); açılışta geri yüklenir, bozuk/negatif değerler güvenle yok sayılır.
- 2026-11-02 — MVP 4/4: Paylaşım önizlemesi (Open Graph + Twitter kartı, 1200×630 `og.png` ve yeniden
  üretme betiği), `SITE_URL` ile canonical ve `sitemap.xml`, theme-color. README güncellendi.
  Doğrulama: 79 Python + 33 TS testi, `npm run check` 17 sayfa, tüm sayfalar 320/1280 px açık/koyu
  temada hatasız; hesaplayıcı sonuçları JSON'dan bağımsız hesapla birebir.
- 2026-11-02 — Grafik ve Konut: `/grafik` ("X'in Y cinsinden fiyatı": otomobil, konut, altın, borsa, döviz,
  mevduat, kira; TL / reel / USD / EUR / altın / BIST / S&P / asgari ücret cinsinden; 3 seriye kadar,
  1-3-5-10 yıl/tümü, hazır kısayollar, paylaşılabilir bağlantı). `/konut`: şehir bazında konut getirisi
  (nominal/reel/USD/altın; TCMB KFE, girilmişse BETAM) ve kirala-mı-satın-al-mı hesaplayıcısı
  (taksit, masraflar, kira/ev/yatırım beklentileri, reel sonuç, başabaş, duyarlılık, yıl yıl döküm).
  Motor: `ratio_index`, `mortgage_payment`, `rent_vs_buy`, `jevons_chain_index` (önce test; TS'ye
  taşındı, 40 ortak vaka). Yeni seriler: TÜFE otomobil ve kira alt endeksleri, KFE (TR/İst/Ank/İzm);
  isteğe bağlı: 0 km bayi liste fiyatı sepeti, BETAM satılık/kiralık. Mobil menü. Sayfadaki
  hesap Python ile birebir doğrulandı (tutar ayrıştırma hatası bu sırada bulunup düzeltildi).
- 2026-11-02 — Makro ve İlişkiler: `docs/ROADMAP.md` (fikir havuzu, veri kararları). `/makro`: GSYH büyümesi,
  kişi başı GSYH, TÜFE, işsizlik, politika faizi, reel mevduat, cari denge, rezerv, CDS, bütçe/GSYH,
  USD/TRY, BIST 100 ($), altın ($) kartları (son değer, dönem, 1 yıllık değişim — Python'da), tıklanınca
  grafik. `/iliskiler`: iki göstergenin değişim korelasyonu, aynı yönde hareket oranı, kayan korelasyon,
  hizalı iki grafik; "korelasyon nedensellik değildir" uyarısı. Motor: `pearson`, `paired_changes`,
  `rolling_correlation`, `same_direction_share` (önce test, TS'ye taşındı; 46 ortak vaka). Çeyreklik /
  yıllık seriler desteklendi; makro seriler piyasa bitiş ayını geri çekmiyor. Grafik modülü: referans
  çizgisi, biçimlendirici, düzensiz aralık. Menü 1024 px altında açılır.
- 2026-11-02 — Borsa ve Portföyüm: `/borsa` (BIST 100 + elle yüklenen hisseler; reel / USD / altın / nominal,
  1-3-5-10 yıl; tarayıcıda saklanan izleme listesi; hisse verisi yokken lisans açıklaması). `/portfoy`:
  pozisyon ekle/sil (tutar, isteğe bağlı miktar, not), pozisyon ve toplam bazında nominal/reel/USD/altın
  getiri ve "enflasyona karşı" TL farkı; yerel depolama, dışa/içe aktarma; sunucuya veri gitmez.
  Motor: `holding_returns`, `portfolio_summary` (önce test; TS; 50 ortak vaka). `data/manual/stocks/`
  (kod doğrulamalı) → grafik aracı, borsa, portföy. Menü gruplandı (Piyasalar / Makro / Hesapla),
  ana sayfada araç ızgarası. Kaydırma kutularının dışına taşan erişilebilirlik etiketi hatası düzeltildi.
- 2026-11-02 — Karar araçları ve olay penceresi: `/kredi` (akdi faiz + KKDF + BSMV + peşin/aylık masraf →
  ödeme planı, gider dağılımı, iç verim oranıyla gerçek yıllık maliyet, "faiz × 12" ile fark, reel maliyet),
  `/taksit` (taksitlerin bugünkü değeri, taksit planının gizli faizi, enflasyona göre toplam), `/maas`
  (zam başına reel değişim, bugünkü TL / $ / gram altın / asgari ücret karşılığı, nominal-reel grafik;
  tarayıcıda saklanır), `/olaylar` (politika faizi artış/indirim aylarından türetilen ve elle eklenen
  olaylar etrafında ortalama/medyan yol). Motor: `irr`, `amortization`, `loan_cost`, `present_value`,
  `installment_vs_cash`, `salary_analysis`, `event_study`, `derive_rate_events` (önce test; TS; 59
  ortak vaka). Sayfa sonuçları Python ile birebir doğrulandı. Örnek politika faizi basamaklı hâle getirildi.
