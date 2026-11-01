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
