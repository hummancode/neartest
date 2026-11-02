# [MARKA] — reel finans verisi

Plan ve kurallar: `CLAUDE.md`. Değişiklikler: `CHANGELOG.md`.

## Veri hattı (Python)

    pip install -r requirements.txt
    pytest -q                              # motor + builder testleri
    python -m pipeline.build --sample      # eksik serileri ÖRNEK (sentetik) veriyle doldurarak JSON üret
    EVDS_API_KEY=... python -m pipeline.discover "Tüketici Fiyat" "Mevduat" "Altın"
    EVDS_API_KEY=... python -m pipeline.fetch && python -m pipeline.build

Çıktılar `site/data/`: `reel_tablo.json`, `seviyeler.json`, `tufe_gruplari.json`, `reel_faiz.json`,
`seriler.json` (grafikler), `durum.json` (veri durumu). Seri kodları `pipeline/series.py`'de; doğrulanmadan
`verified=True` yapılmaz.

**İsteğe bağlı elle yüklenen kaynaklar** (asla örneklenmez): 0 km otomobil fiyat sepeti
(`car_new_basket.csv` → zincirleme Jevons endeksi), BETAM satılık/kiralık konut endeksleri, net asgari ücret.

**API anahtarı olmadan gerçek veri:** EVDS web arayüzünden (veya başka resmî kaynaktan) indirilen CSV'yi
`data/manual/<seri>.csv` olarak koyun — ayrıntılar `data/manual/README.md`. Öncelik: `data/raw/` (API)
→ `data/manual/` → örnek veri. Sitedeki `/veri` sayfası her serinin nereden geldiğini gösterir.

TÜFE grup ağırlıkları elle girilir: `data/manual/tufe_agirliklari.csv`

    id,weight
    food,...
    housing,...
    (pipeline/series.py içindeki CPI_GROUPS id'lerinin hepsi)

## Site (Astro)

    cd site
    npm install
    npm test           # TS motoru, Python ile aynı vakalar (tests/cases.json)
    npm run build      # çıktı: site/dist
    npm run check      # derleme sonrası: kırık bağlantı, çapa, uyarı metni, örnek bandı
    npm run preview    # http://localhost:4321

Sahibin karar vermesi gereken ayarlar tek dosyada: `site/src/config.ts`
(marka adı, site adresi `SITE_URL` → canonical/OG/sitemap, KVKK iletişim/veri sorumlusu, bülten form
adresi, Cloudflare Web Analytics token'ı, yasal metinlerin taslak uyarısı). Marka adı değişince paylaşım
görselini yenileyin: `node scripts/make-og.cjs` (yerelde Playwright gerekir).

## Cloudflare Pages'a yayın

1. Cloudflare → Workers & Pages → Create → Pages → Connect to Git → bu repo.
2. Production branch: `main`. Build command: `npm run build`. Build output: `dist`. Root directory: `site`.
3. Environment variable: `NODE_VERSION` = `22`.
4. `site/public/_headers` güvenlik başlıklarını ve önbellek ayarını içerir.

Günlük veri işi (`.github/workflows/daily.yml`) yalnızca varsayılan dalda zamanlanır ve
`EVDS_API_KEY` repo secret'ı gerektirir; yoksa yalnızca örnek veriyle derler.
