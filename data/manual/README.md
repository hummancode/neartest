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

## Hisseler

`stocks/<KOD>.csv` — tarih; kapanış fiyatı (TL). Günlük veri aylık ortalamaya çevrilir. İsteğe bağlı
`stocks/<KOD>.meta.json`: `{"name": "Şirket adı", "source": "...", "verified": true}`. Dosya adı yalnızca
büyük harf ve rakamdan oluşan hisse kodu olmalıdır (2–8 karakter). Grafik aracında görünmesi için
verinin ortak bitiş ayına kadar uzanması gerekir. Borsa fiyat verisi lisanslıdır; kaynağın kullanım
şartlarına uyun.

## Makro göstergeler ve CDS

`gdp_growth`, `gdp_usd_pc`, `unemployment`, `current_account`, `reserves`, `policy_rate`, `cds_5y`,
`budget_balance_gdp` — değerler **gösterim biriminde** girilir (`4,5` = %4,5; CDS baz puan; cari denge
ve rezerv milyar $). Çeyreklik seriler çeyrek sonu ayına (`2026-03`, `2026-06` …), yıllık seriler
Aralık'a (`2025-12`) yazılır. CDS için ücretsiz resmî kaynak yoktur.

## İller (`iller/<gösterge>.csv`)

Sütunlar `plaka;yil;deger` (plaka 1–81). Göstergeler: `population`, `household_size`, `gdp_mn_tl`,
`exports_mn_usd`, `insured_employees`, `companies_active`, `companies_new`, `listed_companies`,
`deposits_mn_tl`, `loans_mn_tl`, `m2_price_tl`, `rent_m2_tl`, `house_sales`, `avg_wage_tl`, `income_gini`,
`cars`, `sege_score` (ayrıntı: `pipeline/provinces.py`). Gelir Gini'si bölge değeridir; bölgedeki her ile aynı yazılır.

Dağılımlar (sütunlar `plaka;yil;kategori;deger`, her il için en son yıl kullanılır):
`iller/gsyh_sektor.csv` (TÜİK il bazında GSYH, iktisadi faaliyet kolu, milyon TL), `iller/istihdam_sektor.csv`
(SGK 4/a, ekonomik faaliyet, kişi), `iller/ihracat_sektor.csv` (TİM/TÜİK sektör, milyon $), `iller/ihracat_ulke.csv`
(ülke, milyon $). İhracatın yıllık geçmişi için `iller/exports_mn_usd.csv` dosyasına birden çok yıl yazılabilir.
Kategori adları serbesttir; sanayi/tarım/inşaat payları için "Tarım, ormancılık ve balıkçılık", "Sanayi", "İnşaat" adları kullanılmalıdır.

Borsa şirketleri listesi: `iller/bist_sirketler.csv` — `plaka;kod;unvan;sektor` (KAP'taki merkez adresine göre).
Liste varsa il bazında şirket sayısı bu listeden sayılır.
Aynı il için birden çok yıl varsa en son yıl kullanılır.

## Nüfus: il ve ilçe (TÜİK ADNKS)

- **İl nüfusu, yıllara göre:** `iller/population.csv` — `plaka;yil;deger`, her il için birden çok yıl
  (ADNKS 2007–). En son yıl gösterge olarak, tüm yıllar grafik ve büyüme hızları için kullanılır.
- **İlçe nüfusu:** `ilceler/nufus.csv` — `plaka;ilce;yil;nufus` (başlık satırı isteğe bağlı), ör.
  `6;Çankaya;2024;950.000`. TÜİK "il ve ilçe nüfusları" tablosundan. Merkez ilçesi büyükşehir olmayan
  illerde `Merkez` yazılır. Adlar sınır dosyasıyla Türkçe karakterlere duyarlı biçimde eşleşir
  (`KEÇİÖREN` = `Keçiören`); eşleşmeyenler Veri durumu sayfasında listelenir.
- **İlçe sınırları** (`site/data/tr_ilceler.json`, depoda hazır): geoBoundaries gbOpen TUR ADM2/ADM1
  (OpenStreetMap tabanlı, ODbL 1.0). Yenilemek için: `python -m pipeline.geo_districts ADM2.geojson ADM1.geojson`.

## Dış ticaret dağılımı

`dis_ticaret_ulke.csv`: `yil;ulke;ihracat_milyon_usd;ithalat_milyon_usd` ·
`dis_ticaret_urun.csv`: `yil;urun;ihracat_milyon_usd` (kaynak: TÜİK). En son yıl gösterilir.
