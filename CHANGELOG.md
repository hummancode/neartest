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
