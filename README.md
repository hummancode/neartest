# [MARKA] — reel finans verisi

    pip install -r requirements.txt
    pytest -q                              # motor testleri
    python -m pipeline.build --sample      # örnek (sentetik) veriyle JSON üret
    EVDS_API_KEY=... python -m pipeline.discover "Tüketici Fiyat" "Mevduat"
    EVDS_API_KEY=... python -m pipeline.fetch && python -m pipeline.build

Plan ve kurallar: CLAUDE.md. Değişiklikler: CHANGELOG.md.
