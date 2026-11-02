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
