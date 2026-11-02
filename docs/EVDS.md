# EVDS erişimi geldiğinde: kontrol listesi

Kural (CLAUDE.md): seri kodu **tahmin edilmez**. Her kod EVDS'de sorgulanır, adı/birimi/sıklığı
kontrol edilir, sahibin onayından sonra `pipeline/series.py`'ye yazılır ve `verified=True` yapılır.

## 1. Ortam
- `EVDS_API_KEY`: cloud ortamının gizli değişkenleri **ve** GitHub → Settings → Secrets → Actions.
- Ağ: cloud ortamında `evds2.tcmb.gov.tr` izinli alan olmalı (GitHub Actions'ta gerekmez).

## 2. Keşif
    python -m pipeline.discover "Tüketici Fiyat" "Döviz" "Mevduat" "Kredi" "Konut Fiyat" "Altın" \
        "Gayri Safi" "İşgücü" "Ödemeler Dengesi" "Rezerv" "Politika Faizi"

## 3. Bulunacak seriler (28)
| Seri adı (`series.py`) | Aranan | Kontrol |
|---|---|---|
| `usdtry`, `eurtry` | Döviz kurları, gösterge niteliğinde alış | Kod örneklerde `TP.DK.USD.A.YTL` / `TP.DK.EUR.A.YTL` geçiyor; yine de doğrula |
| `cpi_tr` | TÜFE genel endeks (2003=100) | Baz yılı değişikliği varsa not al |
| `cpi_food` … `cpi_misc` (12) | TÜFE ana harcama grupları | Grup yapısı 12 mi 13 mü (COICOP 2018)? |
| `rent_cpi`, `car_cpi` | TÜFE gerçek kira, otomobil alt endeksleri | Alt kalem kodları |
| `deposit_rate` | TL mevduat ağırlıklı ortalama faiz (akım) | Hangi vade? yüzde birim (ölçek 0,01 otomatik) |
| `credit_rate` | TL **ihtiyaç (tüketici) kredisi** ağırlıklı ortalama faiz | Karar: ihtiyaç kredisi (hane halkı odaklı) |
| `house_tr/ist/ank/izm` | Konut Fiyat Endeksi (KFE) | Türkiye ve 3 il |
| `gdp_growth` | GSYH, zincirlenmiş hacim, yıllık % değişim | Çeyreklik (frekans otomatik) |
| `unemployment` | İşsizlik oranı (mevsimsellikten arındırılmış?) | Hangisi? |
| `current_account` | Cari işlemler hesabı, 12 aylık toplam (milyar $) | Birim: milyon $ ise build'de ölçek ekle |
| `reserves` | TCMB brüt rezervleri | Haftalık ise aylık ortalama |
| `policy_rate` | Politika faizi (bir hafta vadeli repo) | Aylık ortalama |

EVDS dışı (elle veya başka kaynak): gram altın, BIST 100, S&P 500, CDS, kişi başı GSYH ($),
bütçe dengesi/GSYH, asgari ücret, TÜFE ağırlıkları, BETAM, 0 km fiyat sepeti, hisseler.

## 4. Onaydan sonra
    # series.py'ye kodları yaz, verified=True
    python -m pipeline.fetch && python -m pipeline.build --sample
    cd site && npm run build && npm run check

Kontrol: `/veri` sayfasında kaynak "TCMB EVDS API" görünmeli; Reel Tablo'da anormal değer (ör.
mevduat getirisinde 100 kat sapma, eksik aylar) olmamalı. Tüm seriler gerçek olunca `--sample`
bayrağı workflow'dan kaldırılabilir; örnek veri bandı kendiliğinden kalkar.
