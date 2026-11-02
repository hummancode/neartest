# Elle yüklenen veri

API anahtarı olmadan gerçek veri eklemenin yolu. Buraya konan dosyalar `python -m pipeline.build`
tarafından okunur ve sitede **"Elle yüklendi"** olarak gösterilir. Öncelik sırası:
`data/raw/` (EVDS API) → `data/manual/` (bu klasör) → örnek veri.

## Dosya adı

`<seri>.csv` — seri adları `pipeline/series.py` içindedir: `cpi_tr`, `usdtry`, `eurtry`,
`deposit_rate`, `credit_rate`, `gold_gram_tl`, `bist100`, `sp500_usd`, `cpi_food`, `cpi_housing`, …,
`min_wage_net`.

## Biçim

İlk sütun tarih, ikinci sütun değer. Başlık satırı olabilir. EVDS web arayüzünden indirilen
dosyalar doğrudan çalışır (`Tarih;TP_...`, `2024-1`, ondalık virgül). Günlük veri aylık ortalamaya
çevrilir. Faiz serileri yüzde olarak girilir (`45,5` = %45,5).

    Tarih;Deger
    2024-1;2.000,50
    2024-2;2.050,25

`min_wage_net` (net asgari ücret) için yalnızca değiştiği ayları yazmak yeterlidir; sonraki aylar
bir önceki değerle doldurulur.

## Kaynak bilgisi (önerilir)

Aynı ada sahip `<seri>.meta.json` sitede gösterilecek kaynağı belirler:

    {"source": "TCMB EVDS (web arayüzü)", "code": "TP.XXX.YYY", "verified": true}

`verified: true` yalnızca seri kodunu ve içeriğini kaynağında gerçekten kontrol ettiyseniz yazılır.

## TÜFE grup ağırlıkları

`tufe_agirliklari.csv` — sütunlar `id,weight` (id'ler `pipeline/series.py` → `CPI_GROUPS`).
