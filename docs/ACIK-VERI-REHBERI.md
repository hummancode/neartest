# Açık Veri İndirme Rehberi — sahibi için uygulamalı liste

> Hazırlanma: 2 Kasım 2026. `docs/VERI-KAYNAKLARI.md`'deki genel taramanın **devamıdır**; orada
> anlatılan kurum tanıtımları ve lisans tartışmaları burada tekrarlanmadı. Bu belge şu soruyu
> yanıtlıyor: **"Hangi dosyayı nereden indirip repoda hangi ada kaydedeyim?"**
>
> **Ağ notu:** Bu oturumda yalnızca `raw.githubusercontent.com` açılabildi. Diğer bütün siteler
> (tcmb.gov.tr, tuik.gov.tr, csgb.gov.tr, worldbank.org, imf.org, bis.org, rug.nl, fao.org, ec.europa.eu,
> ilostat.ilo.org, data.ibb.gov.tr, ourworldindata.org, owid-public.owid.io …) hem `curl` hem WebFetch ile
> **reddedildi**. Bilgiler web aramasının döndürdüğü başlık/URL/özetlerden derlendi.
>
> İşaretler:
> - **[D]** = Bu oturumda dosyayı/sayfayı açıp içeriğini gördüm (yalnızca GitHub).
> - **[A]** = Resmî URL ve başlık web aramasında göründü, ama sayfa açılamadı. İndirmeden önce sayfaya bakın.
> - **[G]** = Genel bilgi; bu oturumda kontrol edilmedi.
> - **doğrulanamadı** = Arandı, teyit bulunamadı.
>
> Seri kodu yazılmadı (CLAUDE.md kuralı). Rakam örnekleri yalnızca dosya biçimini göstermek için var; gerçek değer değildir.

---

## 1. En değerli 10 dosya — hemen indirin

| # | Ad | Link | Format | Ne açar | Repoya kaydet |
|---|---|---|---|---|---|
| 1 | Aylık altın fiyatı (USD/oz), 1833–2026-09 | `https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly.csv` **[D]** | CSV | Reel Tablo'daki "Gram Altın" satırı (USD/TRY ile TL'ye çevrilir). **Bunu biz indirebiliriz** | `data/raw/gold_usd_oz.csv` (sizin bir şey yapmanız gerekmiyor) |
| 2 | ÇSGB "Yıllar İtibarıyla Net ve Brüt Asgari Ücret" (01/08/1996–31/12/2025) | https://csgb.gov.tr/poco-pages/asgari-ucret/ **[A]** | XLS | Nominal illüzyon makinesindeki "asgari ücret cinsinden" karşılık | `data/manual/min_wage_net.csv` |
| 3 | TCMB EVDS: TÜFE + 13 ana grup (2025=100) | EVDS 3 web arayüzü → Excel **[G]** | XLSX | Kişisel enflasyon hesaplayıcı, Reel Tablo | `data/manual/cpi_tr.csv`, `cpi_<grup>.csv` |
| 4 | TÜİK TÜFE ana grup ağırlıkları (2026) | TÜİK TÜFE bülteni ekleri **[A]** | XLS | Kişisel enflasyon (resmî sepetle kıyas) | `data/manual/tufe_agirliklari.csv` |
| 5 | TCMB Konut Fiyat Endeksi (Türkiye + 3 il) | EVDS 3 → "Konut ve Konut Dışı Fiyat Endeksleri" **[G]** | XLSX | Konut sayfası, reel konut fiyatı | `data/manual/house_tr.csv`, `house_ist.csv`, `house_ank.csv`, `house_izm.csv` |
| 6 | TÜİK ADNKS "İl ve İlçe Nüfusları" | TÜİK Veri Portalı → Nüfus ve Demografi **[A]** | XLS | İl haritası, ilçe nüfusu | `data/manual/iller/population.csv`, `data/manual/ilceler/nufus.csv` |
| 7 | BIS konut fiyatları (reel/nominal, Türkiye dahil, 2010-Ç1–2026-Ç2) | `https://raw.githubusercontent.com/datasets/house-prices-global/main/data/real_index.csv` **[D]** | CSV | Ülkelerarası reel konut kıyası. **Bunu biz indirebiliriz** | `data/raw/bis_house_real.csv` |
| 8 | World Bank WDI tamamı | https://databank.worldbank.org/data/download/WDI_CSV.zip **[A, üçüncü taraf kodundan]** | ZIP/CSV (~200 MB) | Ülke karşılaştırma panelleri (zaten API ile çekiliyor; toplu dosya yedek) | İndirmeyin; API yeterli. Gerekirse `data/manual/dunya/wdi_<gösterge>.csv` |
| 9 | Maddison Project Database 2023 | https://www.rug.nl/ggdc/historicaldevelopment/maddison/releases/maddison-project-database-2023 **[A]** | XLSX (`mpd2023_web.xlsx` [A, üçüncü taraf]) | Uzun dönem sayfası (şu an 2020 sürümü kullanılıyor; 2023 sürümü 2022'ye kadar) | `data/manual/dunya/mpd2023.xlsx` |
| 10 | FAO Gıda Fiyat Endeksi (nominal + reel, 1990–) | https://www.fao.org/worldfoodsituation/foodpricesindex/en/ **[A]** | XLSX / CSV | "Dünyada gıda fiyatı vs. TÜFE gıda" karşılaştırması | `data/manual/dunya/fao_ffpi.csv` |

> **Not (#2):** README'deki adı `asgari_ucret.csv` değil **`min_wage_net.csv`**'dir (`pipeline/series.py`). Yalnızca
> değişiklik aylarını yazmak yeterli.

> **Not (#3–4) — önemli [A]:** Haberlere göre TÜİK Şubat 2026'da TÜFE bazını **2003=100'den 2025=100'e** taşıdı ve ana
> grup sayısı **12'den 13'e** çıktı (COICOP 2018). `pipeline/series.py` → `CPI_GROUPS` şu an 12 grup içeriyor.
> Eski ve yeni seri **zincirlenmeden** birleştirilmemeli. Bu bir tasarım kararıdır, karar sizin.

---

## 2. Türkiye resmî kaynakları

### 2.1 Asgari ücret — ÇSGB

- **Sayfa [A]:** https://csgb.gov.tr/poco-pages/asgari-ucret/
- **Dosyalar [A, arama özetinden]:**
  - "Yıllar İtibarıyla Günlük ve Aylık Asgari Ücret (01/07/1974 – 31/12/2025)" — .XLS
  - "Yıllar İtibarıyla Net ve Brüt Asgari Ücret (01/08/1996 – 31/12/2025)" — .XLS
  - PDF sürümü: https://live.csgb.gov.tr/Media/14angt4p/netbrutasgari.pdf [A]
- **2026 satırı:** Resmî tabloda yok. Resmî Gazete'deki Asgari Ücret Tespit Komisyonu kararından **elle** ekleyin
  (ikincil kaynaklardaki rakamları kullanmayın).
- **Dikkat:** 1974–1996 arası **brüt** (ve bazı dönemlerde 16 yaş üstü/altı ayrımı) var; net tutar yok. 2005 öncesi eski TL
  (1 YTL = 1.000.000 TL) — dönüştürmek gerekir. Metodoloji sayfasına not düşülmeli.
- **Çaba:** Tek tık XLS + 2–3 dakikalık temizlik.
- **Repoya:** `data/manual/min_wage_net.csv`

      Tarih;Deger
      2025-1;<net TL>
      2026-1;<net TL>

  Brüt ve 1974'ten başlayan seri isterseniz önerilen yeni dosya: `data/manual/min_wage_gross.csv` (aynı biçim;
  **pipeline'da henüz karşılığı yok**).
- **Lisans:** Kamu belgesi; ayrı bir yeniden kullanım metni **doğrulanamadı**. Atıf: "Kaynak: ÇSGB, Yıllar İtibarıyla Asgari Ücretler".

### 2.2 TCMB EVDS — web arayüzünden Excel (API anahtarı beklenirken)

Ayrıntılar `VERI-KAYNAKLARI.md` 2.1'de. Burada yalnızca **elle indirme** listesi:

| Ne | EVDS'de aranacak başlık [G] | Repoya | Sıklık |
|---|---|---|---|
| TÜFE genel ve ana gruplar | "Fiyat Endeksleri" → "Tüketici Fiyat Endeksi" | `cpi_tr.csv`, `cpi_food.csv` … | Aylık |
| USD/TRY, EUR/TRY (döviz alış) | "Kurlar" → "Döviz Kurları" | `usdtry.csv`, `eurtry.csv` | Günlük → aylık ort. |
| Mevduat / ihtiyaç kredisi faizi (akım, ağ. ort.) | "Faiz İstatistikleri" | `deposit_rate.csv`, `credit_rate.csv` | Haftalık |
| KFE (Türkiye, İstanbul, Ankara, İzmir) | "Konut ve Konut Dışı Fiyat Endeksleri" | `house_tr.csv`, `house_ist.csv` … | Aylık |
| Politika faizi | "TCMB faiz oranları" | `policy_rate.csv` | Karar bazlı |
| Cari denge, rezervler | "Ödemeler Dengesi", "Uluslararası Rezervler" | `current_account.csv`, `reserves.csv` | Aylık |
| Piyasa Katılımcıları Anketi (12/24 ay TÜFE beklentisi) | "Anketler" → "Piyasa Katılımcıları Anketi" | yeni: `pka_cpi_12m.csv` | Aylık |

- **Çaba:** Seri başına 3–5 seçim (kategori → seri → tarih aralığı → frekans → Excel). README'ye göre EVDS çıktısı
  (`Tarih;TP_...`, `2024-1`, ondalık virgül) doğrudan okunuyor.
- Her dosyanın yanına `<seri>.meta.json` koyun; `verified: true` **yalnızca** seri kodunu EVDS ekranında gördüyseniz.
- **PKA:** TCMB sitesinde anketin aylık yayımlandığı kesin (haberlerde her ay aktarılıyor [A]); geçmiş sonuçların
  **Excel arşivi bulunamadı**, EVDS'de seri olarak bulunduğu **doğrulanamadı**. Bulursanız: `pka_cpi_12m.csv` (`Tarih;Deger`,
  yüzde). Bu, Reel faiz sayfasındaki **ex-ante reel faizi** açar. Pipeline desteği **yok**; eklenmesi gerekir.
- **Politika faizi alternatifi:** EVDS yoksa TCMB'nin PPK karar duyurularından (tcmb.gov.tr → Para Politikası → PPK
  Kararları [G]) elle tablo. Haber sitelerindeki kronolojiler çelişkili (ör. 2022 için farklı rakamlar) [A] — **kullanmayın**.

### 2.3 TÜİK — tablolar

TÜİK Veri Portalı'nda her bülten sayfasının altında "İstatistiksel Tablolar" bölümü ve XLS indirme düğmesi bulunur [G].

| Tablo | Aranacak ad [A/G] | Format | Repoya | Ne açar |
|---|---|---|---|---|
| İl ve ilçe nüfusu (ADNKS 2025, 9 Şub 2026 bülteni [A]) | "İBBS-Düzey1, İBBS-Düzey2, İl ve İlçe Nüfusları" [A] | XLS | `iller/population.csv` (`plaka;yil;deger`), `ilceler/nufus.csv` (`plaka;ilce;yil;nufus`) | İl haritası, ilçe nüfusu |
| İl nüfusu 2007– | ADNKS "Yıllara göre il nüfusları" [G] | XLS | `iller/population.csv` (çok yıl) | Nüfus büyüme hızı |
| İllere göre göç | ADNKS "İllerin aldığı ve verdiği göç" [G] | XLS | yeni: `iller/net_migration.csv` (`plaka;yil;deger`) — pipeline desteği yok | Göç katmanı |
| İl bazında GSYH (cari, kişi başı, sektör) | "İl Bazında Gayrisafi Yurt İçi Hasıla" [G] | XLS | `iller/gdp_mn_tl.csv`, `iller/gsyh_sektor.csv` | İl haritası |
| TÜFE ana grup ağırlıkları | TÜFE bülteni ekleri, "ağırlıklar" [A] | XLS | `tufe_agirliklari.csv` (`id,weight`) | Kişisel enflasyon |
| Konut satış (il) | "Konut Satış İstatistikleri" [G] | XLS | `iller/house_sales.csv` | İl haritası |
| Motorlu taşıt (il) | "Motorlu Kara Taşıtları" [G] | XLS | `iller/cars.csv` | İl haritası |
| Dış ticaret ülke/ürün | "Dış Ticaret İstatistikleri" [G] | XLS | `dis_ticaret_ulke.csv`, `dis_ticaret_urun.csv` | Dış ticaret |

- **Çaba:** Tek tık XLS, ama başlık satırları çok katlı; plaka sütunu yoksa il adından plakaya eşleme gerekir (pipeline'da
  il listesi var).
- **Lisans:** TÜİK yeniden kullanım metni **doğrulanamadı** (bkz. ana belge). Atıf: "Kaynak: TÜİK, <bülten adı>, <tarih>".

### 2.4 Elektrik tarifeleri — EPDK

- **Ne [A, haberler]:** EPDK üç ayda bir (son yıllarda bazen aylık) "Faaliyet Bazlı", "Nihai" ve "Yeşil" tarife tablolarını
  onaylıyor; tablolar Resmî Gazete'de de yayımlanıyor. Mesken, ticarethane, sanayi, tarımsal sulama ayrımı.
- **İndirme:** EPDK sitesinde "Elektrik → Tarifeler" bölümü [G]. Resmî bir **Excel arşivi bulunamadı**; Resmî Gazete
  sayıları PDF/HTML. → **PDF tablo / elle giriş** (dönem başına bir satır).
- **Repoya (yeni, pipeline desteği yok):** `data/manual/elektrik_tarife.csv`

      Tarih;Abone;TL_kWh_vergiler_haric;Kaynak
      2026-01;Mesken (tek zamanlı);<değer>;Resmî Gazete <tarih/sayı>

- **Ne açar:** "Elektrik faturasının reel ve asgari ücret saatine oranı" kartı.
- **Lisans:** Resmî Gazete metinleri kamuya açık (5846 s. FSEK m.31 kapsamında resmî metinler [G]); doğrulanamadı.

### 2.5 Doğal gaz tarifeleri — BOTAŞ

- **Ne [A]:** BOTAŞ her ay "tarife tablosu"nu kendi sitesinde yayımlıyor (mesken, sanayi, elektrik üretimi). Eski kararlarda
  fiyatlar m³ ve kWh bazında (m³ → kWh dönüşüm katsayısı kararda belirtiliyor [A]).
- **Excel arşivi bulunamadı.** Aylık PDF/HTML tablodan elle giriş.
- **Repoya (yeni):** `data/manual/dogalgaz_tarife.csv` — `Tarih;Abone;TL_m3;Kaynak`
- **Dikkat:** BOTAŞ toptan tarifesi ≠ hanenin ödediği fiyat (dağıtım bedeli ve vergiler eklenir). Sitede bu açıkça yazılmalı.

### 2.6 Akaryakıt fiyatları — EPDK

- **Bülten sorgulama [A]:** https://bildirim.epdk.gov.tr/bildirim-portal/faces/pages/tarife/petrol/yonetim/bultenSorgula.xhtml
  (il ve tarih seçilerek "Bayi Satış Fiyatı Bülteni"). Dışa aktarma (Excel) olup olmadığı **doğrulanamadı**.
- EPDK'nın fiyat farkı hesabı için **aylık ortalama** akaryakıt fiyatı yayımladığı üçüncü taraf sitelerde aktarılıyor [A];
  resmî dosya konumu doğrulanamadı.
- **Kural:** Bülten sayfasını program ile sorgulamak scraping sayılır → **elle**, ayda bir; ya da EPDK'ya Excel talebi.
- **Daha basit resmî alternatif:** TÜİK TÜFE alt kalemleri (benzin, motorin) — EVDS'den. Fiyat değil endeks.
- **Repoya (yeni):** `data/manual/akaryakit.csv` — `Tarih;Il;Urun;TL_litre`

### 2.7 Bütçe ve borç — Hazine ve Maliye Bakanlığı

- **Aylık Bütçe Bülteni [A]:** PDF, ms.hmb.gov.tr'de; ör. https://ms.hmb.gov.tr/uploads/2021/01/2020_Aralik-Aylik-Butce-Bulteni-min.pdf
  — 2006'dan itibaren merkezi yönetim bütçe büyüklükleri tabloları içeriyor [A].
- **Kamu Borç Yönetimi Raporu [A]:** aylık PDF, ör. https://ms.hmb.gov.tr/uploads/2023/06/Web_Kamu_Borc_Yonetimi_Raporu_Haziran_2023_v2.pdf
- **Borç göstergeleri [A]:** ör. https://ms.hmb.gov.tr/uploads/2020/03/BORÇ-GÖSTERGELERİ_31.03.2020.pdf
- **Excel:** Bakanlık sitesinde "İstatistikler → Kamu Finansmanı → Merkezi Yönetim Borç İstatistikleri" yolunun eski
  Hazine sitesinde bulunduğu aktarılıyor [A]; **güncel Excel bağlantısı doğrulanamadı**. Muhasebat GM "Bütçe İstatistikleri"
  Excel'leri [G].
- **Dikkat [A]:** 2006'da "konsolide bütçe"den "merkezi yönetim bütçesi"ne geçildi; 2006 öncesi ile kesintisiz birleştirmeyin.
- **Repoya:** `data/manual/budget_balance_gdp.csv` (çeyrek sonu ayı, %) — mevcut. Yeni öneri: `data/manual/borc_stoku.csv`
  (`Tarih;Deger`, milyar TL, ay sonu).
- **Çaba:** Excel bulunursa tek tık; yoksa PDF tablo.

### 2.8 İl bazında mevduat/kredi — BDDK FinTürk

- Sayfa ana belgede var. Ek bilgi: BDDK tablolarını indiren iki açık kaynak paket var: R `bddkR` (CRAN) ve Python `pybrsa`
  (PyPI) [A]; ikincisi "bddk" ve "finturk" tablolarını listeleyebiliyor, CSV/Excel'e yazıyor [A]. Paketlerde **il kırılımlı**
  tablo adı görülmedi (doğrulanamadı). Bunlar BDDK sitesini otomatik sorguladığı için kullanmadan önce BDDK'ya sorun.
- **Elle:** FinTürk → il seçimi → dönem → Excel [G]. Çeyreklik.
- **Repoya:** `iller/deposits_mn_tl.csv`, `iller/loans_mn_tl.csv` (`plaka;yil;deger`). Çeyreklik veriyi yıl sonu (Aralık)
  değeriyle girin, aksi hâlde "en son yıl" mantığı karışır.

### 2.9 SGK aylık istatistikler

- **Ne [A]:** Aylık istatistik bülteninde "4/a aktif sigortalıların illere dağılımı", cinsiyet kırılımı, 4/b ve 4/c tabloları;
  bülten **Excel** olarak indirilebiliyor (2020 ve 2021 sayılarının özetlerinde Excel bağlantısı var [A]).
- **Yol [G]:** sgk.gov.tr → İstatistikler → Aylık İstatistik Bilgileri → ilgili ay → Excel.
- **Repoya:** `iller/insured_employees.csv` (`plaka;yil;deger`), istersen `iller/istihdam_sektor.csv`.
- **Ortalama ücret:** SGK "prime esas kazanç" il tablosu → `iller/avg_wage_tl.csv` [G]. Prime esas kazanç tavan/taban
  sınırlıdır; "ortalama ücret" diye değil "prime esas günlük kazanç ortalaması" diye etiketleyin.
- **Çaba:** Tek tık Excel, sayfa başına bir tablo.

### 2.10 Turizm — Kültür ve Turizm Bakanlığı

- **Ne [A]:** Aylık "Sınır İstatistikleri" (milliyete ve sınır kapısına göre yabancı ziyaretçi). İl müdürlüğü raporlarında
  "tablonun Excel formatı ektedir" notu var; ör. İstanbul raporları
  https://istanbul.ktb.gov.tr/Eklenti/148266,mart-2026pdf.pdf [A].
- **Ulusal Excel:** Bakanlık Yatırım ve İşletmeler GM istatistik sayfası [G]; tam yol **doğrulanamadı**.
- **Turizm geliri:** TÜİK "Turizm İstatistikleri" (çeyreklik) [G]; ödemeler dengesi "seyahat" kalemi EVDS'de [G].
- **Repoya (yeni):** `data/manual/turizm_ziyaretci.csv` — `Tarih;Deger` (kişi, aylık). Reel turizm geliri için
  `data/manual/turizm_gelir.csv` (çeyrek sonu ayı, milyon $).

### 2.11 Kartlı harcama — BKM

- **Ne [A]:** Aylık basın bültenleri (PDF): toplam kartlı ödeme, internet ödemeleri; eski bültenlerde sektör tabloları var.
  Ör. https://bkm.com.tr/wp-content/uploads/2026/02/BKM-2026-Ocak-Basin-Bulteni.pdf ,
  https://bkm.com.tr/wp-content/uploads/2025/11/BKM-Ekim-2025-Basin-Bulteni.pdf
- **Kırılma [A]:** Nisan 2025'ten itibaren bazı ön ödemeli kartlar "banka kartı" kategorisine alındı → kart türü
  karşılaştırmasında seri kırılması.
- **Excel:** bkm.com.tr "İstatistikler" sayfasında olup olmadığı **doğrulanamadı**. → **PDF tablo**.
- **Repoya (yeni):** `data/manual/kart_harcama.csv` — `Tarih;Sektor;Milyon_TL`. TÜFE ile reelleştirilir.
- **Lisans:** doğrulanamadı → BKM'ye sorun.

### 2.12 Elektrik tüketimi — EPİAŞ Şeffaflık Platformu

- **Erişim [A]:** Şeffaflık verisine erişim için EPİAŞ Kayıt Platformu'ndan kullanıcı adı/şifre gerekiyor; API'de giriş
  zorunluluğu 19 Ağustos 2024'te devreye girdi. Web arayüzünde "indirilebilir veriler" bölümü var [A].
- **Ne:** Saatlik gerçek zamanlı tüketim, PTF (piyasa takas fiyatı).
- **Çaba:** Kayıt + tarih aralığı seç + Excel. Saatlik veri büyük; aylık toplama çevirin.
- **Repoya (yeni):** `data/manual/elektrik_tuketim.csv` — `Tarih;Deger` (aylık toplam GWh).
- **Kullanım şartları** doğrulanamadı. API anahtarı/şifre gerekiyorsa `.env` ve GitHub Secrets — asla koda yazmayın.

### 2.13 İBB Açık Veri Portalı

- https://data.ibb.gov.tr [A] — 2020'de açıldı; ulaşım, otopark, raylı sistem yolculuk verileri [A]. **Hal fiyatı veri setinin
  varlığı ve portal lisans metni doğrulanamadı.** (CKAN tabanlı portallarda lisans her veri setinin sayfasında yazar [G].)
- R paketi `ibb` (CRAN) portalı sorguluyor [A].
- **Ne açabilir:** İstanbul hal fiyatları (varsa) → gıda TÜFE ile kıyas; İstanbul toplu taşıma kullanımı.
- **Repoya (yeni):** `data/manual/ibb/<veri_seti>.csv`, yanına lisans adı ve indirme tarihiyle `.meta.json`.

---

## 3. Uluslararası açık kaynaklar

### 3.1 World Bank Pink Sheet (emtia fiyatları)

- **Sayfa [A]:** https://www.worldbank.org/en/research/commodity-markets → "Monthly prices" (CMO Historical Data Monthly, XLSX).
  Son Pink Sheet PDF: https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/world-bank-commodities-price-data-the-pink-sheet [A]
- **Uyarı [A, üçüncü taraf]:** İndirme URL'sinde her ay değişen bir karma var → kalıcı link yok; her ay sayfadan alın.
- **İçerik:** ~70 emtia, 1960–, aylık (altın, Brent, doğal gaz, buğday, şeker…). 2010=100 endeksler.
- **Lisans:** CC BY 4.0 olduğu ikincil kaynaklarda yazıyor [A]; World Bank sayfasında **doğrulanamadı**. Bazı alt seriler
  üçüncü taraf kaynaklı (Bloomberg, ICO) [A].
- **Kolay yol:** Altın için GitHub'daki türetilmiş dosya (bölüm 4.1) yeterli. Tüm Pink Sheet için:
  `data/manual/dunya/pink_sheet_monthly.xlsx`.

### 3.2 IMF World Economic Outlook (Ekim 2026)

- **Yeni yer [A]:** https://data.imf.org/datasets/WEO (veri seti kimliği IMF.RES:WEO). Geçiş kılavuzu (9 Ekim 2026) —
  https://data.imf.org/-/media/iData/External-Storage/Documents/DDAF479A0D474D01AA7E1B8435396BFD/en/WEO_Database_Transition_Guide.pdf
  "View Data" yanındaki mavi **Download** düğmesi son sürümün tamamını indiriyor; toplu indirmede "ek gereklilikler"
  olabileceği yazıyor (metin kesik) [A]. Eski SDMX indirmesi kaldırıldı [A].
- **Ekim 2026 eki [A]:** 197 ekonomi; eksik veri "n/a".
- **Lisans:** IMF SSS'ye göre kaynak gösterilerek yazılı çalışmalarda kullanılabilir [A]; IMF genel site şartları
  "kişisel, ticari olmayan" kullanım diyor (bkz. 4.6'daki README alıntısı [D]). → **Ticari site için IMF'ye sorun.**
- **Ne açar:** Ülke karşılaştırma (enflasyon, büyüme, cari denge, kamu borcu/GSYH). Tahminler "tavsiye değildir" notuyla.
- **Repoya:** `data/manual/dunya/weo_2026oct.csv` — gerekli sütunlar: `ulke_iso3;gosterge;yil;deger`.

### 3.3 BIS — politika faizleri ve konut fiyatları (toplu indirme)

- **Toplu indirme [A, üçüncü taraf R paketi]:** https://data.bis.org/bulkdownload ; dosyalar `data.bis.org/static/bulk/`
  altında, ör. `WS_CBPOL_csv_flat.zip` (politika faizleri), `WS_CPP_csv_flat.zip` (ticari gayrimenkul),
  `WS_DPP_csv_flat.zip` [A]. Konut fiyatı dosya kodu **doğrulanamadı**.
- **Lisans:** BIS şartları (ana belge 4.5), kaynak gösterilerek.
- **Ne açar:** "Türkiye politika faizi vs. diğer gelişmekte olan ülkeler" grafiği; ülkelerarası reel konut.
- **Repoya:** `data/manual/dunya/bis_cbpol.csv` — `ulke_iso2;tarih;deger`.
- Konut fiyatı için bölüm 4.2'deki GitHub kopyası daha kolay.

### 3.4 Penn World Table 11.0

- **Sayfa [A]:** https://www.rug.nl/ggdc/productivity/pwt/pwt-releases/pwt110 ; Dataverse DOI **10.34894/FABVLR** [A].
- **Kapsam [A]:** 185 ülke, 1950–2023; Excel dosyasında "Info", "Legend", "Data" sayfaları [A, üçüncü taraf].
- **Lisans [A]:** CC BY 4.0 (resmî sayfa özetinde). Atıf: Feenstra, Inklaar ve Timmer (2015), "The Next Generation of the
  Penn World Table", *American Economic Review* 105(10).
- **Ne açar:** SAGP'ye göre kişi başı reel GSYH, verimlilik, emek payı.
- **Repoya:** `data/manual/dunya/pwt110.xlsx` (olduğu gibi). Çaba: tek tık (Dataverse).

### 3.5 Maddison Project Database 2023

- **Sayfa [A]:** https://www.rug.nl/ggdc/historicaldevelopment/maddison/releases/maddison-project-database-2023 ;
  Dataverse DOI **10.34894/INZBF2** [A]. Dosya adı `mpd2023_web.xlsx`, sayfa "Full data" [A, üçüncü taraf].
- **Kapsam [A]:** 169 ülke, 2022'ye kadar.
- **Lisans [A]:** CC BY 4.0. Atıf: Bolt ve van Zanden (2024), "Maddison style estimates of the evolution of the world economy:
  A new 2023 update", *Journal of Economic Surveys*, DOI 10.1111/joes.12618.
- **Ne açar:** `pipeline/longrun.py` şu an **2020 sürümünü** OWID GitHub'dan çekiyor. 2023 sürümü daha yeni; geçiş için
  `longrun.py`'nin Excel okuması gerekir (küçük iş). Lisans bayrağı (`license_verified`) yine sizin teyidinizle açılmalı.
- **Repoya:** `data/manual/dunya/mpd2023_web.xlsx`.

### 3.6 FAO Gıda Fiyat Endeksi

- **Sayfa [A]:** https://www.fao.org/worldfoodsituation/foodpricesindex/en/ — "Excel: Nominal and real indices from 1990 onwards
  (monthly and annual)"; eski bir FAO yayını CSV seçeneği de listeliyor [A].
- Aylık, her ayın ilk haftası. Alt endeksler: tahıl, yağ, süt, et, şeker [G].
- **Lisans:** FAO genel olarak CC BY-NC-SA 3.0 IGO kullanır [G] → **ticari olmayan** şartı olabilir; **doğrulanamadı**.
  Reklamlı/ücretli site için FAO'ya sorun.
- **Repoya:** `data/manual/dunya/fao_ffpi.csv` — `Tarih;Deger` (nominal), ayrı `fao_ffpi_real.csv`.

### 3.7 Eurostat (HICP)

- **Lisans [A]:** Eurostat telif sayfası (https://ec.europa.eu/eurostat/help/copyright-notice): içerik CC BY 4.0, ticari dahil
  yeniden kullanım serbest, kaynak gösterilmeli; üçüncü taraf materyal hariç. Aday ülkeler (Türkiye) yeni metinde kapsanıyor
  görünüyor (çıkarım).
- **Türkiye HICP:** `prc_hicp_manr` vb. tablolarda TR var; bazı değerlerde "d — tanım farklı" bayrağı [A]. Aynı seri FRED'de
  `CP0000TRM086NEST` adıyla [A].
- **Ne açar:** "TÜFE vs. AB HICP" karşılaştırması (aynı metodoloji ailesi).
- **Repoya:** `data/manual/dunya/hicp_<ulke>.csv` — `Tarih;Deger`. Çaba: Data Browser'da 3–4 filtre + CSV.

### 3.8 ILOSTAT

- **Toplu indirme [A]:** https://ilostat.ilo.org/data/bulk/ — CSV, kod sözlükleri ve kılavuz
  (https://webapps.ilo.org/ilostat-files/Documents/ILOSTAT_BulkDownload_Guidelines.pdf).
- **Lisans:** CC BY 4.0 olduğu **doğrulanamadı**.
- **Ne açar:** Ülkelerarası asgari ücret (PPP), ortalama ücret, işsizlik. Asgari ücretin ülkelerarası kıyası için tek açık kaynak
  adayı.
- **Repoya:** `data/manual/dunya/ilostat_<gosterge>.csv`.

### 3.9 OECD, UN Data

- OECD: ana belgede (4.3). Elle: Data Explorer → tablo → "Download" → CSV [G]. Ortalama ücretler, uzun vadeli faizler.
- UN Data (data.un.org): bu oturumda araştırılmadı — doğrulanamadı.

---

## 4. GitHub'dan erişilebilenler (biz kendimiz çekebiliriz)

Hepsi bu oturumda `raw.githubusercontent.com` üzerinden **açıldı [D]**. Lisanslar `datapackage.json`/README'den okundu [D].
Bunlar **ikincil kopyalardır**: sitede hem kopyayı hem asıl kaynağı yazın.

### 4.1 `datasets/gold-prices` — aylık altın (USD/oz) ★ en değerli

- Dosya: `https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly.csv` (`Date,Price`; 1833-01 … **2026-09**) [D].
  Ayrıca `annual.csv`, `monthly-processed.csv`.
- Kaynak [D]: 1960– **World Bank Pink Sheet**; 1833–1959 Timothy Green tablosu (yıllık, aylara kopyalanmış).
- Lisans [D]: bakımcı katmanı **ODC-PDDL 1.0**; asıl kaynak World Bank (bölüm 3.1). README günlük GitHub Actions ile güncellendiğini söylüyor [D].
- **Ne açar:** `gold_gram_tl` = (USD/oz ÷ 31,1035) × USD/TRY aylık ortalama. Reel Tablo'nun "Gram Altın" satırı lisans sorunu
  olmadan dolar. Formül metodoloji sayfasına yazılmalı; Kapalıçarşı gram fiyatından farklıdır (işçilik, prim yok).
- **Atıf:** "Altın: World Bank Commodity Price Data (Pink Sheet), datahub.io/core/gold-prices üzerinden".

### 4.2 `datasets/house-prices-global` — BIS konut fiyatları

- `data/real_index.csv`, `nominal_index.csv`, `real_year.csv`, `nominal_year.csv` [D]; sütunlar `date,country_code,country,price`;
  çeyrek sonu tarihi. **Türkiye `TR`: 2010-03-31 → 2026-06-30** [D].
- Lisans [D]: "BIS Terms of Permitted Use of Statistics (Attribution Required)".
- **Atıf:** "Kaynak: Ulusal kaynaklar, BIS Residential Property Price database".

### 4.3 `datasets/oil-prices` ve `datasets/natural-gas` — EIA

- Brent/WTI günlük-haftalık-aylık-yıllık (`data/brent-monthly.csv`, son satır 2026-09 [D]); Henry Hub doğal gaz
  (`data/monthly.csv`) [D].
- Lisans [D]: EIA verisi ABD kamu malı; atıf önerisi "Source: U.S. Energy Information Administration (<tarih>)". Bakımcı katmanı PDDL.
- **Ne açar:** "Benzin pompa fiyatı vs. Brent (TL)" — TÜFE akaryakıt alt kalemiyle birlikte.

### 4.4 `datasets/gdp`, `datasets/population`, `datasets/inflation` — World Bank WDI kopyaları

- `gdp/main/data/gdp.csv` (cari $; TUR son yıl 2023 [D]) — lisans **CC BY 4.0** [D].
- `population/main/data/population.csv` (TUR son yıl 2025 [D]) — PDDL [D].
- `inflation/main/data/inflation-consumer.csv`, `inflation-gdp.csv` (TUR son yıl 2023 [D]) — PDDL [D].
- Pipeline WDI API'yi zaten kullanıyor; bunlar **API çökerse yedek**.
- **Uyarı — `datasets/cpi`:** README "2005=100 TÜFE düzeyi" diyor ama `cpi.csv`'de Türkiye satırları yıllık enflasyon
  oranına benziyor (2022: 72,3; 2024: 58,5) [D]. **Kullanmayın.**

### 4.5 `owid/co2-data`, `owid/energy-data`

- `owid/co2-data/master/owid-co2-data.csv` — Türkiye 2025'e kadar [D]; enerji sütunları da var. Asıl indirme adresi artık
  `owid-public.owid.io` (bu oturumdan erişilemedi) [D, README].
- `owid/energy-data`: README'ye göre GitHub sürümü **"legacy — artık güncellenmiyor"**; yeni veri `catalog.ourworldindata.org`'da [D].
  GitHub'daki CSV hâlâ indirilebiliyor [D].
- Lisans: OWID kendi işi için CC BY 4.0 [G]; alt kaynaklar (Energy Institute, Ember, EIA) kendi şartlarıyla [D, README listesi].
- **Ne açar:** Kişi başı enerji tüketimi, elektrik karışımı ülke kıyası.

### 4.6 Dikkatli kullanılacak GitHub kopyaları

| Repo | Sorun |
|---|---|
| `datasets/s-and-p-500` (Shiller, 1871–) | Bakımcı "lisans belirsiz, PDDL varsayıyorum" diyor [D]. Son dolu satır **2023-09**, sonrası sıfır [D]. Telif S&P DJI'da olabilir → Reel Tablo için **uygun değil**. |
| `datasets/house-prices-us` (Case-Shiller) | S&P CoreLogic telifli endeks; bakımcının PDDL'i asıl telifi kaldırmaz [G]. Kullanmayın. |
| `datasets/commodity-prices` (IMF) | README'deki IMF metni: "kişisel, ticari olmayan kullanım" [D]. Ticari site için uygun değil. |
| `datasets/exchange-rates` (Fed H.10) | **TRY yok** [D]; yalnızca EUR/USD çapraz kontrol için. |
| `owid/owid-datasets` | Arşiv niteliğinde; Maddison 2020 buradan çekiliyor (`pipeline/longrun.py`). 2023 sürümü için bölüm 3.5. |

### 4.7 Zaten kullanılanlar

- `TheEconomist/big-mac-data` (`pipeline/bigmac.py`), `owid/owid-datasets` Maddison 2020 (`pipeline/longrun.py`),
  geoBoundaries (ilçe sınırları). `big-mac-data` deposunda kök `LICENSE` dosyası **yok** (404) [D]; lisans bilgisi README'de.

---

## 5. Lisans / atıf özeti

| Kaynak | Lisans | Ticari site? | Atıf metni (öneri) | Durum |
|---|---|---|---|---|
| TCMB EVDS | Kaynak gösterilerek kullanım/yayım serbest | Genel TCMB koşullarında "ticari için yazılı izin" maddesi | "Kaynak: TCMB EVDS, <seri adı>, erişim <tarih>" | ana belgede [D] |
| TÜİK | Metin bulunamadı | Belirsiz | "Kaynak: TÜİK, <bülten>, <tarih>" | doğrulanamadı |
| ÇSGB asgari ücret | Kamu belgesi | Muhtemelen evet | "Kaynak: ÇSGB, Yıllar İtibarıyla Asgari Ücretler" | doğrulanamadı |
| Resmî Gazete (EPDK tarifeleri) | Resmî metin | Evet [G] | "Kaynak: EPDK kararı, Resmî Gazete <tarih/sayı>" | [G] |
| BOTAŞ, BKM, SGK, BDDK, KTB, EPİAŞ, İBB | — | Sorun | Kurum adı + tablo adı + tarih | doğrulanamadı |
| World Bank WDI | CC BY 4.0 | Evet | "World Bank – World Development Indicators" | [D, datasets/gdp README] |
| World Bank Pink Sheet | CC BY 4.0 (ikincil kaynaklarda) | Muhtemelen evet | "World Bank Commodity Price Data (The Pink Sheet)" | [A] |
| IMF WEO | Kaynak gösterilerek; genel şart "ticari olmayan" | **Sorun** | "IMF, World Economic Outlook Database, Ekim 2026" | [A] |
| BIS | Kaynak gösterilerek indirme/çoğaltma | Evet (atıfla) | "National sources, BIS Residential Property Price database" | [D, datapackage] |
| PWT 11.0 | CC BY 4.0 | Evet | Feenstra, Inklaar, Timmer (2015) AER | [A] |
| Maddison 2023 | CC BY 4.0 | Evet | Bolt & van Zanden (2024) JoES | [A] |
| FAO FFPI | CC BY-NC-SA 3.0 IGO olabilir | **Sorun** | "FAO Food Price Index" | [G] |
| Eurostat | CC BY 4.0 | Evet | "Kaynak: Eurostat, <tablo kodu>" | [A] |
| ILOSTAT | — | Sorun | "ILO, ILOSTAT" | doğrulanamadı |
| EIA (Brent, Henry Hub) | ABD kamu malı | Evet | "Source: U.S. EIA (<tarih>)" | [D, README alıntısı] |
| OWID | CC BY 4.0 (kendi işi); alt kaynaklar ayrı | Evet (alt kaynağa bağlı) | "Our World in Data, <alt kaynak>" | [G] |
| datahub `datasets/*` | Bakımcı katmanı PDDL / CC BY | Asıl kaynağın şartı geçerli | Hem kopya hem asıl kaynak | [D] |

---

## 6. Doğrulanamayanlar

- **Ağ:** GitHub dışındaki hiçbir siteye bu oturumdan erişilemedi. [A] işaretli bütün URL'ler arama sonuçlarından geldi;
  sayfa içerikleri, dosya adları ve düğme adları açılıp kontrol edilmedi. Daha fazlasını doğrulamak için bu oturumun ağ ayarlarında
  `www.tcmb.gov.tr`, `evds3.tcmb.gov.tr`, `data.tuik.gov.tr`, `csgb.gov.tr`, `www.worldbank.org`, `data.imf.org`,
  `data.bis.org`, `www.rug.nl`, `www.fao.org` alan adlarına izin verilmesi gerekir.
- ÇSGB XLS dosyalarının doğrudan indirme URL'si (yalnızca sayfa ve dosya başlıkları görüldü).
- TCMB Piyasa Katılımcıları Anketi geçmiş sonuçlarının Excel arşivi veya EVDS serisi.
- KFE'nin TCMB sitesindeki doğrudan Excel'i (EVDS dışında).
- TÜİK 2025=100 TÜFE'nin 13 ana grubunun adları ve ağırlık tablosunun dosya konumu; eski 2003=100 seriyle bağlama yöntemi.
- EPDK elektrik tarife ve akaryakıt bültenlerinde Excel dışa aktarma; EPDK aylık ortalama akaryakıt fiyat tablosunun resmî konumu.
- BOTAŞ tarife arşivinin Excel sürümü.
- Hazine ve Maliye Bakanlığı borç stoku ve bütçe Excel'lerinin güncel adresleri (yalnızca PDF'ler görüldü).
- BDDK FinTürk il tablosunun Excel çıktısı; `bddkR`/`pybrsa` paketlerinde il kırılımı.
- KTB ulusal sınır istatistikleri Excel'inin yolu; BKM'de Excel istatistik olup olmadığı.
- EPİAŞ Şeffaflık kullanım şartları; İBB Açık Veri lisansı ve hal fiyatı veri seti.
- World Bank Pink Sheet lisansının World Bank sayfasındaki metni; aylık dosyanın güncel URL'si (her ay değişiyor).
- WDI toplu ZIP adresi (yalnızca üçüncü taraf kodlarında görüldü; büyük/küçük harf farkı `WDI_CSV.zip` / `WDI_csv.zip`).
- IMF WEO toplu indirmedeki "ek gereklilikler"; IMF verisinin ticari sitede kullanımı.
- BIS konut fiyatı toplu dosyasının kodu; BIS bulk sayfasının güncel dosya listesi.
- PWT ve Maddison Excel dosya adları (üçüncü taraf kaynaklardan).
- FAO FFPI lisansı; CSV bağlantısının güncel olup olmadığı.
- ILOSTAT ve UN Data lisansları.
- `datasets/cpi` dosyasındaki Türkiye değerlerinin neden enflasyon oranına benzediği (README ile çelişiyor).
