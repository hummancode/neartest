# [MARKA] — reel finans verisi

    pip install -r requirements.txt
    pytest -q                              # motor testleri
    python -m pipeline.build --sample      # örnek (sentetik) veriyle JSON üret
    EVDS_API_KEY=... python -m pipeline.discover "Tüketici Fiyat" "Mevduat"
    EVDS_API_KEY=... python -m pipeline.fetch && python -m pipeline.build

Plan ve kurallar: CLAUDE.md. Değişiklikler: CHANGELOG.md.

## Site (Astro)

    cd site
    npm install
    npm run build      # çıktı: site/dist (Cloudflare Pages: build komutu `npm run build`, kök `site`, çıktı `dist`)
    npm run preview    # http://localhost:4321
