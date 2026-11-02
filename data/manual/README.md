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

## 0 km otomobil fiyat endeksi (resmi bayi fiyat listeleri)

`car_new_basket.csv` — her ay, seçilen modellerin markaların resmi fiyat listelerindeki fiyatı:

    Ay;Model;Fiyat
    2026-01;<Marka Model Motor Paket>;1.850.000
    2026-01;<Marka Model Motor Paket>;2.400.000
    2026-02;<Marka Model Motor Paket>;1.900.000

Endeks Python'da **zincirleme Jevons** yöntemiyle hesaplanır: her ay, iki ayda da fiyatı olan
modellerin fiyat oranlarının geometrik ortalaması kadar değişir. Modeller sepete girip çıkabilir;
ay atlanmamalıdır. Aynı model adını aylar boyunca birebir aynı yazın. Kaynak bilgisi için
`car_new_basket.meta.json` (`{"source": "..."}`). Hazır bir endeks varsa doğrudan `car_new.csv`
olarak da verilebilir. Fiyat listeleri **elle** girilir; sitelerden otomatik çekme yapılmaz.

## BETAM konut endeksleri

`betam_sale_<şehir>.csv` (satılık) ve `betam_rent_<şehir>.csv` (kiralık); şehir: `tr`, `ist`, `ank`, `izm`.
BETAM'ın aylık raporlarındaki endeks veya TL/m² değerleri girilir. Varsa konut sayfasında TCMB
endeksinin yanında kaynak seçeneği ve kira artışı referansı olarak, grafik aracında ayrı seri olarak görünür.
Yayımlarken BETAM'ı kaynak olarak belirtin ve kullanım şartlarını kontrol edin.
