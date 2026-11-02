# Veri Kaynakları Araştırması — Reel Finans Portalı

> Hazırlanma: 2 Kasım 2026. Bu bir **masa başı web araştırmasıdır**. Bazı kaynak
> sitelere (ör. sahibinden.com, teknoblog.com) bu oturumun ağ kısıtı yüzünden doğrudan
> erişilemedi; bilgiler arama sonuçlarından ve resmî belgelerin aktarımlarından derlendi.
>
> İşaretler:
> - **[D]** = Bu araştırmada bir resmî sayfa/belge ya da birden çok bağımsız kaynakla doğrulandı.
> - **[G]** = Genel bilgiye dayanıyor; bu oturumda açılıp kontrol edilmedi. Kullanmadan önce sahibinin bakması gerekir.
> - **doğrulanamadı** = Arandı ama teyit bulunamadı.
>
> Seri kodları **bilerek yazılmadı**. CLAUDE.md kuralı gereği her kod EVDS/TÜİK'ten
> sorgulanarak doğrulanacak.

---

## 1. Özet tablo

| Kaynak | Ne sağlar (bizim için) | Erişim | Lisans / şartlar | Öncelik |
|---|---|---|---|---|
| TCMB EVDS 3 | TÜFE, kurlar, mevduat/kredi faizleri, KFE, PKA beklentileri, ödemeler dengesi, rezervler, politika faizi | API (ücretsiz anahtar) + Excel | Kaynak göstererek kullanım ve yayım serbest [D]; ticari kullanım için yazılı izin maddesi genel TCMB sitesinde var [D] | **Yüksek** |
| TÜİK (Veri Portalı, MEDAS) | ADNKS il/ilçe nüfusu, il GSYH, TÜFE alt kalemleri ve ağırlıkları, konut satış, taşıt, dış ticaret (il), işgücü, gelir | İndirme (Excel/CSV), JSON-stat uç noktası (resmî dokümante API yok) | Resmî yeniden kullanım metni bulunamadı (**doğrulanamadı**) | **Yüksek** |
| BDDK FinTürk | İl bazında mevduat/kredi (çeyreklik) | Web arayüzü + indirme | Şartlar doğrulanamadı | **Yüksek** (il haritası) |
| SGK İstatistik Yıllıkları | İl bazında sigortalı sayısı, prime esas kazanç | Excel (yıllık/aylık) | doğrulanamadı | Orta |
| TOBB | Kurulan/kapanan şirket (il bazında, aylık) | PDF/web tablo | doğrulanamadı | Orta |
| Hazine ve Maliye Bak. | Bütçe dengesi, kamu borç stoku | Excel | doğrulanamadı | Orta |
| TİM / Ticaret Bak. / TÜİK | İl ve sektör bazında ihracat | Excel/web | doğrulanamadı | Orta |
| SEGE (Sanayi ve Teknoloji Bak.) | İl/ilçe sosyo-ekonomik gelişmişlik skoru | PDF (2022, 973 ilçe) [D] | Kamu yayını; şart doğrulanamadı | Orta |
| ODMD / OSD | Otomobil satışı, üretim, ihracat | PDF/bülten | doğrulanamadı | Düşük–Orta |
| Borsa İstanbul Datastore | BIST 100 tarihsel veri | Ücretli/lisanslı indirme | Telif BİST'te; lisans gerekir | Yüksek ama **lisans** |
| BETAM–sahibinden "sahibindex" | Kiralık/satılık ilan fiyatları, reel kira | Aylık PDF rapor [D] | Kullanım şartı doğrulanamadı → izin sor | Orta |
| Endeksa / REIDIN | Konut değer endeksleri | Ücretli / rapor | REIDIN: yazılı izinsiz alıntı/çoğaltma yasak [D] | Düşük |
| World Bank WDI + Pink Sheet | Ülke karşılaştırma; aylık altın fiyatı | API (anahtarsız) | CC BY 4.0 [G] | **Yüksek** |
| IMF (data.imf.org) | WEO tahminleri, emtia fiyatları | SDMX 2.1/3.0 API [D] | IMF şartları; doğrulanamadı | Orta |
| OECD Data Explorer | Karşılaştırmalı makro, fiyatlar | SDMX API, hız sınırlı [D] | Açık lisans (1 Tem 2024'ten itibaren) [D, kapsam notlu] | Orta |
| BIS | Konut fiyatları, politika faizleri, kredi | SDMX API [D] | Kaynak göstererek indirme/çoğaltma [D] | Orta |
| FRED | ABD TÜFE, S&P 500 (10 yıl günlük), faizler | API (ücretsiz anahtar) | Seri sahibinin telifi geçerli [D] | **Yüksek** |
| BLS | ABD TÜFE (birincil kaynak) | API (v2 için kayıt) | ABD kamu verisi [G] | Orta |
| Eurostat / ECB | AB HICP, EUR kurları | API | Eurostat: kaynak göstererek yeniden kullanım [G] | Düşük–Orta |
| UN Comtrade | Ülkelerarası ticaret | API (anahtar, ücretsiz kota) | Şartlı [G] | Düşük |
| OWID / PWT / Maddison | Uzun dönem GSYH, yaşam standardı | CSV/GitHub | CC BY 4.0 [G] | Orta |
| WID | Gelir/servet eşitsizliği | Toplu indirme | Lisans **doğrulanamadı** | Düşük |
| Numbeo | Yaşam maliyeti | Ücretli lisans/API | Ticari kullanım ücretli, scraping yasak [D] | Düşük (kullanma) |
| LBMA Gold Price | Altın referans fiyatı | ICE IBA lisansı | Gecikmeli bile olsa yeniden dağıtım lisans ister [D] | Kullanma |
| Big Mac Index | Satın alma gücü örneği | GitHub CSV | Veri CC BY 4.0 [D, README aktarımı] | Düşük–Orta |
| CDS (5 yıl) | Ülke risk primi | Bloomberg/Refinitiv/IHS — lisanslı | Ücretsiz resmî kaynak bulunamadı | Düşük |

---

## 2. Türkiye resmî kaynaklar

### 2.1 TCMB EVDS (Elektronik Veri Dağıtım Sistemi) — Öncelik: Yüksek

- **Güncel durum [D]:** TCMB, Ocak 2026'da EVDS 3'ü (beta) devreye aldı; geçiş sürecinde EVDS 2 bir süre açık tutuldu. Ekim 2026'da yapay zekâ araçları için **EVDS-MCP** hizmeti duyuruldu ve "yenilenen kullanım şartları ve kılavuzun EVDS 3 platformunda" olduğu bildirildi.
  - Adres: https://evds3.tcmb.gov.tr
  - Eski kılavuz (EVDS 2, Nisan 2024): https://evds2.tcmb.gov.tr/help/videos/EVDS_Web_Service_Usage_Guide.pdf
  - Basın duyurusu aktarımı (Ocak 2026): https://www.alomaliye.com/2026/01/26/tcmb-elektronik-veri-dagitim-sisteminin-yenilenmesine-iliskin-basin-duyurusu/
  - EVDS-MCP duyurusu aktarımı (Ekim 2026): https://www.alomaliye.com/2026/10/26/evds-mcpnin-devreye-alinmasina-iliskin-basin-duyurusu/
- **Uyarı:** Bir üçüncü taraf kütüphane notu (borsapy v0.10.0) eski `evds2` REST API'nin 2025 sonunda kapandığını ve PyPI'daki `evds` paketlerinin bozulduğunu söylüyor. **Resmî kaynaktan doğrulanamadı.** Pratik sonuç: veri hattını doğrudan EVDS 3 dokümantasyonuna göre yazın; `evds` gibi eski paketlere güvenmeyin.
- **API anahtarı [D, haber aktarımı]:** EVDS 3'e üye ol → giriş → "Benim Sayfam / Profilim" → "API KEY KOPYALA". Anahtar her istekle gönderilir; yoksa 403 döner (eski kılavuz). EVDS 3'te anahtarın başlıkta mı parametrede mi gittiği **doğrulanamadı**.
- **Kullanım şartları [D]:** EVDS şartlar belgesi: "EVDS uygulamasında sunulan veriler kaynak gösterilmek koşuluyla üçüncü kişiler tarafından kullanılabilir ve yayımlanabilir." TCMB veriyi önceden bildirmeden değiştirme/kaldırma hakkını saklı tutar; dış kaynaklı verilerin sorumluluğu ilgili kurumdadır.
  - Belge: https://evds3.tcmb.gov.tr/igmevdsms-dis/documents/showDocument?docId=18
  - Genel TCMB site koşulları (2018 tarihli metin): "ticari amaçlarla kullanımı TCMB'nin yazılı iznine tabidir" — https://www.tcmb.gov.tr/wps/wcm/connect/ekonomi/hie/diger/kullanim+kosullari . Bunun EVDS verisine uygulanıp uygulanmadığı belirsiz. Site reklam/ücretli üyelik alacaksa TCMB'ye yazılı soru sorulması önerilir.
- **Bizim için önemli veri grupları** (seri kodları EVDS 3'ten sorgulanacak):
  - TÜFE (genel + ana harcama grupları), ÜFE → Reel Tablo, kişisel enflasyon, nominal illüzyon
  - Döviz kurları (USD, EUR alış/satış, günlük) → Reel Tablo
  - Mevduat ve kredi ağırlıklı ortalama faizleri (akım, haftalık) → Reel Tablo, Reel faiz
  - Konut Fiyat Endeksi (KFE) ve Yeni/Yeni Olmayan Konut endeksleri, il/bölge kırılımı → Konut sayfası
  - Piyasa Katılımcıları Anketi (12 ay / 24 ay sonrası TÜFE beklentisi, yıl sonu kur beklentisi) → Ex-ante reel faiz. Anketin EVDS'de seri olarak bulunduğu **doğrulanamadı** (anketin kendisi aylık yayımlanıyor [D]).
  - Ödemeler dengesi (cari işlemler), uluslararası rezervler, politika faizi (1 hafta repo) → Makro pano
  - Altın fiyatları: EVDS'de altın serisi olup olmadığı **doğrulanamadı**; "Kıymetli maden" başlığı altında aranmalı.
  - BIST endeksleri: EVDS'de bulunup bulunmadığı **doğrulanamadı** (bulunursa BİST lisans meselesini çözebilir; ama veri üçüncü taraf olduğundan BİST şartları yine de geçerli olabilir).
- **Otomasyon:** API ile günlük çekim uygun. GitHub Actions'ta anahtar Secrets'ta.

### 2.2 TÜİK — Öncelik: Yüksek

- **Erişim noktaları:**
  - Veri Portalı: https://data.tuik.gov.tr [G]
  - MEDAS (Merkezi Dağıtım Sistemi): https://biruni.tuik.gov.tr/medas [G]
  - Üçüncü taraf bir MCP projesine göre veri akışları `databrowser2.tuik.gov.tr` üzerindeki JSON-stat 2.0 uç noktasından okunabiliyor; eski SDMX servisi (`nsiws.tuik.gov.tr`) Ağustos 2026'dan beri erişilemiyor. **Tek kaynak, doğrulanamadı.**
  - TÜİK'in **dokümante edilmiş resmî bir REST API'si yok** (üçüncü taraf beyanı; ters kanıt bulunamadı).
- **Lisans:** TÜİK'in genel bir "yeniden kullanım" lisans metni **bulunamadı**. Mikro veri yönergesi kaynak gösterilmesini şart koşuyor. Pratik öneri: her tabloda "Kaynak: TÜİK, [bülten adı], [tarih]" yazın ve TÜİK'e yazılı olarak "kaynak göstererek web sitesinde yayımlama" teyidi isteyin.
- **Bizim için seriler:**
  | Veri | İçerik | Sıklık | Sayfa |
  |---|---|---|---|
  | ADNKS | İl/ilçe nüfus, yaş, medyan yaş, cinsiyet; il içi/ili arası göç matrisi | Yıllık (Şubat) | İl haritası, ilçe nüfus |
  | İl bazında GSYH | Cari fiyatlarla il GSYH, kişi başı, sektör payları | Yıllık (gecikmeli, ~1 yıl) | İl haritası |
  | TÜFE alt kalemleri + ağırlıklar | COICOP ana grup ve alt grup endeksleri, yıllık ağırlıklar (Hanehalkı Bütçe Anketi ve ulusal hesaplar tabanlı) | Aylık / ağırlık yıllık | Kişisel enflasyon |
  | Konut satış istatistikleri | İl/ilçe bazında satış, ilk el/ikinci el, yabancıya satış | Aylık | Konut, il haritası |
  | Motorlu kara taşıtları | İl bazında taşıt sayısı, trafiğe kaydı yapılan | Aylık/yıllık | İl haritası, otomobil |
  | Dış ticaret (il bazında) | İl bazında ihracat/ithalat (firma merkezine göre — yorumlarken dikkat) | Aylık | İl haritası |
  | Gelir ve Yaşam Koşulları | Gini, yoksulluk, eşdeğer gelir | Yıllık | Makro / ülke |
  | İşgücü | İşsizlik, istihdam (bölge düzeyinde, Düzey 2) | Aylık/yıllık | Makro |
- **Otomasyon:** Çoğunlukla manuel indirme + depoya CSV koyma. JSON-stat uç noktası çalışıyorsa yarı otomatik olabilir ama dokümante değil — kırılgan.

### 2.3 BDDK — Öncelik: Yüksek (il haritası için)

- **FinTürk — "İl Bazında Türk Bankacılık Sektörünün Temel Göstergeleri" [D]:** İl bazında nakdi kredi (türlerine göre: konut, taşıt, ihtiyaç, kredi kartı, ticari), mevduat (TL/YP), şube ve personel sayısı. **Çeyreklik.** Son bülten: 30.07.2026 (2026-6 dönemi).
  - https://www.bddk.org.tr/BultenFinturk/tr/Home/HaberBulteni
- **Aylık Bülten / Haftalık Bülten:** sektör toplamları. https://www.bddk.org.tr/BultenAylik [G]
- **Lisans:** doğrulanamadı. Kamu kurumu verisi; kaynak gösterimi şart kabul edilmeli.
- **Otomasyon:** Web arayüzünden Excel indirme; çeyrekte bir manuel güncelleme yeterli.

### 2.4 SGK İstatistik Yıllıkları — Öncelik: Orta

- İl bazında 4/a, 4/b, 4/c sigortalı sayıları, işyeri sayısı, prime esas günlük kazanç ortalamaları.
- Adres: https://www.sgk.gov.tr (İstatistikler → Aylık İstatistik Bilgileri / İstatistik Yıllıkları) [G]
- Excel, aylık ve yıllık. Lisans doğrulanamadı. Manuel.
- Sayfa: İl haritası (istihdam yoğunluğu, ortalama kazanç).

### 2.5 TOBB Kurulan/Kapanan Şirket İstatistikleri — Öncelik: Orta

- Aylık rapor; il bazında kurulan, kapanan, tasfiyeye giren şirket ve gerçek kişi ticari işletme sayıları [D, PDF içeriği].
- Raporlar KOSGEB sitesinde de barındırılıyor (ör. Temmuz 2026): https://webdosya.kosgeb.gov.tr/Content/Upload/Dosya/Kurumsal/2026/
- Asıl kaynak: https://www.tobb.org.tr (İstatistikler bölümü) [G]
- Format: PDF; Excel bulunduğu **doğrulanamadı**. PDF'ten tablo çıkarma gerekebilir (bu scraping değil, yayımlanmış belgeyi işleme; yine de TOBB'a sormak iyi olur).

### 2.6 Hazine ve Maliye Bakanlığı — Öncelik: Orta

- Merkezi yönetim bütçe dengesi (aylık): Muhasebat GM — https://muhasebat.hmb.gov.tr [G]
- Kamu borç stoku, borçlanma istatistikleri: https://www.hmb.gov.tr (Kamu Finansmanı İstatistikleri) [G]
- Excel; manuel. Bir kısmı EVDS'de de var olabilir (doğrulanamadı).
- Sayfa: Makro pano.

### 2.7 İhracat (il ve sektör) — Öncelik: Orta

- **TİM:** Aylık ihracat rakamları, il ve sektör kırılımı. https://www.tim.org.tr [G]. TİM verisi firmaların kayıtlı olduğu ile göre (İstanbul şişkinliği). Şartlar doğrulanamadı.
- **Ticaret Bakanlığı:** Aylık dış ticaret açıklamaları. https://www.ticaret.gov.tr [G]
- **TÜİK:** İl bazında dış ticaret (resmî istatistik) — TİM'e göre tercih edilmeli.

### 2.8 KAP, Borsa İstanbul, SPK, TEFAS

- **KAP** (https://www.kap.org.tr [G]): Borsada işlem gören şirket listesi, merkez adresleri. İl haritasında "borsa şirketi merkezi" katmanı için. API/şart doğrulanamadı; KAP'ın ticari veri dağıtımı lisanslı olabilir. Öncelik: Düşük.
- **Borsa İstanbul** — bkz. Bölüm 5.
- **SPK** (https://www.spk.gov.tr [G]): Sektör istatistikleri, yatırımcı sayıları. Düşük.
- **TEFAS** (https://www.tefas.gov.tr [G]): Fon fiyatları/getirileri. Resmî kullanım şartları **bulunamadı**. Fon getirisi sergilemek "tavsiye" algısı yaratabilir → bizim kurallarla uyumsuzluk riski. Öncelik: Düşük; kullanılacaksa Takasbank'a yazılı soru.

### 2.9 SEGE — Sanayi ve Teknoloji Bakanlığı — Öncelik: Orta

- **SEGE-2022 [D]:** 973 ilçenin tamamı için skor ve kademe; 56 değişken (bir kaynağa göre). Yayın: Kalkınma Ajansları GM, Nisan 2022 duyurusu. İl düzeyi SEGE'nin en son baskısı (SEGE-2017) [G].
  - PDF: https://www.geka.gov.tr/uploads/news_v/sege-2022.pdf
- Format PDF → tek seferlik elle CSV'ye aktarım. Sayfa: İl/ilçe haritası.

### 2.10 Eğitim ve sağlık

- **YÖK Yükseköğretim İstatistikleri:** https://istatistik.yok.gov.tr [G] — il bazında öğrenci, öğretim elemanı.
- **ÖSYM:** sınav istatistikleri (il bazında başarı) — https://www.osym.gov.tr [G]. Şartlar doğrulanamadı.
- **Sağlık Bakanlığı Sağlık İstatistikleri Yıllığı:** il bazında hekim/yatak sayısı — https://www.saglik.gov.tr [G].
- Öncelik: Düşük (il haritası ek katman).

### 2.11 Otomobil — ODMD / OSD — Öncelik: Düşük–Orta

- **ODMD** (https://www.odmd.org.tr [G]): Aylık otomobil + hafif ticari pazar (marka bazında adet).
- **OSD** (https://www.osd.org.tr [D, rapor PDF'leri var]): Üretim, ihracat.
- **0 km fiyat endeksi:** ODMD/OSD **liste fiyatı yayımlamıyor** (bulunamadı). Liste fiyatları markaların kendi sitelerinde; bunları otomatik toplamak scraping olur → **izin gerekir**. Alternatif: TÜFE "otomobil" alt kalemi (TÜİK) — resmî ve izinsiz kullanılabilir proxy.

### 2.12 Alternatif enflasyon ölçümleri

- **İTO İstanbul Enflasyonu** (https://www.ito.org.tr [G]): Aylık İstanbul perakende ve toptan fiyat endeksleri. CLAUDE.md'ye göre ilk aşamada elle CSV. Şart doğrulanamadı; kaynak göstererek.
- **ENAG** (Enflasyon Araştırma Grubu, https://enagrup.org [G]): Bağımsız akademisyen grubu, aylık alternatif endeks. TÜİK'in ENAG hakkında suç duyurusunda bulunduğu haberlere yansıdı. Öneri: **sitede yayımlamayın** veya yalnızca metodoloji sayfasında "alternatif ölçümler mevcuttur" düzeyinde, tarafsız biçimde anın. "Kendi resmî endeksini üretme / siyasi yorum yapma" yasağıyla çakışma riski var.
- **TÜRK-İŞ açlık/yoksulluk sınırı** (aylık) — Fikirler bölümüne bkz.

### 2.13 Diğer kurumlar

- **TBB (Türkiye Bankalar Birliği):** "İllere ve Bölgelere Göre Bilgiler" — il bazında mevduat/kredi/şube (yıllık). https://www.tbb.org.tr (İstatistiki Raporlar) [G]. BDDK'yı tamamlar, uzun geçmiş için faydalı. Orta.
- **Kredi Kayıt Bürosu (KKB):** Kamuya açık veri çok sınırlı (basın açıklamaları, "Kredi Notu" vb. ürünler ticari). https://www.kkb.com.tr [G]. Düşük.
- **Gelir İdaresi Başkanlığı:** Vergi istatistikleri, il bazında tahakkuk/tahsilat, mükellef sayısı. https://www.gib.gov.tr (İstatistikler) [G]. Orta — il haritası için ilginç katman.
- **ÇSGB (Asgari ücret):** Asgari ücret tarihçesi (net/brüt). https://www.csgb.gov.tr [G]. **Yüksek** (nominal illüzyon makinesi "asgari ücret cinsinden" için zorunlu).
- **EPDK:** Elektrik tarife tabloları (ulusal, Resmî Gazete'de) ve 81 il için akaryakıt fiyat farkı tabloları [D]. https://www.epdk.gov.tr [G]. Pompa fiyatları dağıtıcı sitelerinde → scraping, izin gerekir.

---

## 3. Türkiye özel / akademik kaynaklar

### 3.1 BETAM – sahibinden.com "sahibindex Konut Piyasası Görünümü" — Öncelik: Orta

- **Ne [D]:** Bahçeşehir Üniversitesi BETAM ile sahibinden.com iş birliği; **Ocak 2021'den beri aylık** rapor. sahibinden Emlak kategorisindeki ilanlardan: kiralık ve satılık ilan fiyatlarının cari ve reel seyri, ilan stoku, ilanların yayında kalma süresi (talep göstergesi), büyükşehirler kırılımı. Son haberlere göre 2025 verileri de yayımlanıyor.
  - Örnek rapor PDF: https://betam.bahcesehir.edu.tr/wp-content/uploads/2021/11/sahibindex-Konut-Piyasasi-Gorunumu-Kasim-2021.pdf
  - Arşiv: https://betam.bahcesehir.edu.tr [D]
- **Metodolojik not [D]:** Endeks yeni kiraya verilecek ilanların **talep (ilan) fiyatıdır**; TÜFE kira kalemiyle doğrudan karşılaştırılamaz. Sitede bu açıkça yazılmalı.
- **Format:** PDF; ham zaman serisi indirme olduğu **doğrulanamadı**.
- **Lisans:** doğrulanamadı. Rakamları grafikleştirip yayımlamak için **BETAM'dan yazılı izin** istenmeli (ve mümkünse ham seriyi Excel olarak talep edin).
- Sayfa: Konut (kira vs. satın alma, kira getiri oranı).

### 3.2 sahibinden.com

- Kamuya açık resmî **API veya veri lisansı bulunamadı**.
- Kullanım koşulları sayfasına bu oturumdan erişilemedi (ağ kısıtı); **scraping yasağı metni doğrulanamadı**. Ancak üçüncü taraf scraper satıcıları sitenin "agresif bot koruması" kullandığını, kullanıcı şikâyetlerinde "otomatik erişim uyarısı" ile hesap kısıtlaması olduğunu belirtiyor. Rekabet Kurumu'nun ilan verisinin kullanımına ilişkin bir kararı da var.
- **Sonuç:** Kesinlikle scraping yapılmamalı. Veri gerekiyorsa sahibinden.com kurumsal iletişim/basın birimine yazılı başvuru; pratikte BETAM raporları yeterli.

### 3.3 Endeksa — Öncelik: Düşük

- Konut m² değer tahminleri, il/ilçe/mahalle bazında; basında aylık özet rakamlar. Uygulamada ücretli değerleme raporları var [D].
- Resmî API veya açık lisans **bulunamadı**; kullanım koşulları doğrulanamadı. İletişim: support@endeksa.com (App Store profilinde) [D].

### 3.4 REIDIN — Öncelik: Düşük

- REIDIN-GYODER konut fiyat endeksleri, aylık PDF. Rapor metninde **yazılı izin olmadan çoğaltma/alıntı yasağı** var [D].
  - Örnek: https://reidin.com/wp-content/uploads/2024/08/REIDIN-EMLAK-ENDEKS_202407.pdf
- Lisans olmadan kullanmayın.

### 3.5 Hepsiemlak / Emlakjet

- Periyodik pazar raporları basın bülteni olarak yayımlanıyor [G]. Resmî API veya veri lisansı **doğrulanamadı**. Kullanılacaksa izin + yalnızca rapordaki özet rakamlar.

### 3.6 BKM (Bankalararası Kart Merkezi) — Öncelik: Orta

- Aylık kartlı ödeme tutarları, işyeri sektörüne göre dağılım (market-gıda, giyim, akaryakıt, vb.), internet ödemeleri; bayram dönemi bültenleri [D].
- https://bkm.com.tr (İstatistikler / bültenler) [D, PDF'ler var]. **İl bazında kırılım bulunamadı.**
- Format PDF/web tablo; lisans doğrulanamadı.

---

## 4. Dünya kaynakları

### 4.1 World Bank — Öncelik: Yüksek

- **WDI API (zaten kullanılıyor):** https://api.worldbank.org/v2/ [G], anahtar gerekmez. Lisans: büyük çoğunluğu **CC BY 4.0** [G] (bazı seriler üçüncü taraf; seri bazında kontrol).
- **Commodity Price Data ("Pink Sheet"):** aylık altın (USD/oz), petrol, gıda emtia fiyatları, 1960'tan bugüne, Excel [G]. **Ücretsiz ve açık altın fiyatı için en iyi aday** (aylık; günlük değil). Lisans CC BY 4.0 olduğu varsayılıyor — **doğrulanamadı**, Pink Sheet sayfasındaki notu kontrol edin.
  - https://www.worldbank.org/en/research/commodity-markets [G]

### 4.2 IMF — Öncelik: Orta

- **Yeni portal [D]:** https://data.imf.org — SDMX 2.1 ve SDMX 3.0 API, Swagger sayfası (oturum açmak için beta portal hesabı gerekebilir). API sayfası: https://data.imf.org/en/Resource-Pages/IMF-API
- **IFS bölündü (üçüncü taraf R paketi beyanı, doğrulanamadı):** eski seri kodları çalışmıyor, resmî eşleme tablosu yok.
- **WEO:** Nisan/Ekim; vintage bazında çekilebiliyor; anahtar gerekmiyor (üçüncü taraf beyanı).
- **Primary Commodity Prices:** aylık altın fiyatı da içerir [G].
- Lisans: IMF Copyright and Usage sayfası kontrol edilmeli — **doğrulanamadı**.
- Sayfa: Ülke karşılaştırma (WEO tahminleri — "tahmin"in tavsiye olmadığı not edilmeli).

### 4.3 OECD — Öncelik: Orta

- **Data Explorer:** https://data-explorer.oecd.org [G]; SDMX API ücretsiz, OECD Şartları'na tabi, **hız sınırlaması var** [D].
  - API açıklaması: https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html
- **Lisans [D, kapsam notlu]:** 1 Temmuz 2024'ten itibaren OECD verileri ve yayınları açık lisansla. Basın bülteni dipnotu CC BY 4.0'ı açıkça "1 Temmuz 2024'ten itibaren yayımlanan OECD yazılı içeriği" ile sınırlıyor; veri setleri için kesin lisans metni Şartlar sayfasından kontrol edilmeli.
  - https://www.oecd.org/en/about/news/press-releases/2024/07/oecd-data-publications-and-analysis-become-freely-accessible.html
- Türkiye OECD üyesi → TÜFE, faiz, konut fiyatı, ücret karşılaştırmaları.

### 4.4 Eurostat ve ECB — Öncelik: Düşük–Orta

- **Eurostat:** HICP (Türkiye aday ülke olarak bazı serilerde var), API: https://ec.europa.eu/eurostat [G]. Yeniden kullanım: kaynak göstererek serbest (Komisyon yeniden kullanım kararı) [G].
- **ECB Data Portal:** https://data.ecb.europa.eu [G], API anahtarsız; EUR referans kurları, euro bölgesi faizleri. ECB referans kurları TRY'yi içeriyor olabilir — doğrulanamadı.

### 4.5 BIS — Öncelik: Orta

- **Data Portal:** https://data.bis.org [D]; API: https://stats.bis.org/api-doc/v2 [D] (SDMX REST; üçüncü tarafa göre anahtarsız).
- **İçerik:** Konut fiyatları (Türkiye dahil, reel ve nominal), politika faizleri, özel sektör kredisi, efektif döviz kurları.
- **Şartlar [D]:** Konut fiyatı dokümantasyonu (31 Tem 2026) seçili serilerin indirilebileceğini, çoğaltılabileceğini ve dağıtılabileceğini, portalın verdiği atıf biçimiyle kaynak gösterilmesi gerektiğini söylüyor. Genel şartlar: https://www.bis.org/terms_statistics.htm — "yatırım tavsiyesi değildir" ve "bunun dışındaki kullanım izinli değil" ifadeleri var; iki metin birlikte okunmalı.
- Sayfa: Konut (ülkelerarası reel konut fiyatı), ülke karşılaştırma.

### 4.6 FRED — Öncelik: Yüksek

- https://fred.stlouisfed.org ; API anahtarı ücretsiz (hesap → API Keys) [G].
- **Şartlar [D]:** https://fred.stlouisfed.org/docs/api/terms_of_use.html — Serilerin telifi üçüncü taraflarda olabilir; FRED API'ye erişim bu telifleri geçersiz kılmaz. Telifli serilerin notlarında "Copyright" yazar.
- **S&P 500 [D]:** 2014'te S&P DJI serileri kaldırıldı, sonra yeni anlaşmayla **son 10 yıl günlük** veri geri geldi. Telifli → kullanım koşulları S&P DJI'ya tabi. Wilshire endeksleri Haziran 2024'te kaldırıldı.
- **Altın:** FRED'deki LBMA altın serilerinin kaldırıldığı biliniyor [G, doğrulanamadı].
- Bizim için: ABD TÜFE (CPIAUCSL — kodu FRED'de doğrulayın), ABD faizleri, S&P 500 (lisans notuyla).

### 4.7 BLS — Öncelik: Orta

- ABD TÜFE'nin birincil kaynağı. API v2 için ücretsiz kayıt anahtarı [G]: https://www.bls.gov/developers/
- ABD federal verisi, genelde kamu malı [G].

### 4.8 UN Comtrade — Öncelik: Düşük

- https://comtradeplus.un.org [G]; ücretsiz anahtar, günlük kota; toplu indirme premium. Türkiye'nin ülke/ürün bazında ticareti. Şartlar: Comtrade kullanım şartları kontrol edilmeli (doğrulanamadı).

### 4.9 Our World in Data, Penn World Table, Maddison — Öncelik: Orta

- **OWID** (https://ourworldindata.org [G]): Kendi ürettiği içerik CC BY 4.0; üçüncü taraf verilerde orijinal lisans geçerli. GitHub/CSV.
- **Penn World Table** (https://www.rug.nl/ggdc/productivity/pwt/ [G]): Ülkelerin reel GSYH, SAGP, verimlilik; CC BY 4.0 [G].
- **Maddison Project** (https://www.rug.nl/ggdc/historicaldevelopment/maddison/ [G]): 1820'lerden beri kişi başı GSYH; CC BY 4.0 [G].
- Sayfa: Ülke karşılaştırma ("Türkiye 100 yılda reel olarak ne kadar zenginleşti?").

### 4.10 WID (World Inequality Database) — Öncelik: Düşük

- https://wid.world [D]; tüm veritabanı toplu indirilebilir; R paketi `wid` (kod MIT). **Veri lisansı doğrulanamadı** → info@wid.world'e sorun.

### 4.11 Global Property Guide — Öncelik: Düşük

- https://www.globalpropertyguide.com [G]; kira getirisi, fiyat/kira oranları. Ticari site; yeniden yayım şartı **doğrulanamadı**. Kullanmayın ya da izin isteyin.

### 4.12 Numbeo — Kullanmayın

- **Şartlar [D]:** Kişisel kullanım ücretsiz (atıfla); kurumsal/ticari kullanım ücretli abonelik veya API; kamuya açık veri akışlarıyla yeniden dağıtım izne tabi; **scraping/crawling yazılı izin olmadan kesinlikle yasak**. Sırbistan hukuku.
  - https://www.numbeo.com/common/terms_of_use.jsp
  - https://www.numbeo.com/premium/commercial-license
- Kitle kaynaklı, istatistiki güvenilirliği sınırlı. Bizim "her sayının doğrulanabilir kaynağı" ilkesine uymuyor.

### 4.13 Big Mac Index — Öncelik: Düşük–Orta

- https://github.com/TheEconomist/big-mac-data [D]; README'ye göre The Economist'in ürettiği veri **CC BY 4.0**; kod MIT (ikincil kaynak). Yılda iki kez (Ocak/Temmuz).
- Sayfa: Ülke karşılaştırma / eğlenceli kart. Atıf: "Kaynak: The Economist Big Mac Endeksi".

---

## 5. Fiyat verisi seçenekleri (altın, endeksler, CDS)

### 5.1 Altın

| Seçenek | Sıklık | Lisans | Değerlendirme |
|---|---|---|---|
| **LBMA Gold Price** (ICE IBA) | Günlük | Yeniden dağıtım (gecikmeli dahi) **lisans ister**; ücretsiz gösterim Londra gece yarısından sonra LBMA'nın kendi sitesinde [D]. World Gold Council, IBA talebiyle Mart 2025'te tarihsel veriyi sitesinden kaldırdı [D] | **Kullanmayın** (lisanssız) |
| World Bank Pink Sheet | Aylık | CC BY 4.0 (doğrulanmalı) | **Önerilen** — Reel Tablo'nun 1/3/5/10 yıllık getirisi için aylık yeterli |
| IMF Primary Commodity Prices | Aylık | IMF şartları (doğrulanamadı) | Yedek |
| TCMB EVDS altın serisi | Günlük? | EVDS şartları | **Varsa en iyisi** (TL bazlı) — doğrulanamadı, EVDS 3'te arayın |
| Borsa İstanbul Kıymetli Madenler | Günlük | BİST lisansı | Lisans gerekir |
| Kapalıçarşı/Bigpara vb. | Günlük | Ticari, scraping | Kullanmayın |

Not: Aylık USD/oz × aylık ortalama USD/TRY (EVDS) ile TL bazlı altın getirisi türetilebilir; metodoloji sayfasında belirtin.

Kaynaklar: https://www.lbma.org.uk/prices-and-data/lbma-gold-price/lbma-gold-price , https://www.ice.com/iba/licensing , https://www.gold.org/goldhub/data/gold-prices

### 5.2 BIST 100

- **Borsa İstanbul Datastore:** https://datastore.borsaistanbul.com [D, BİST sayfası yönlendiriyor]; 2015'ten beri bazı dosyalar yalnızca burada. Ücret/lisans koşulları **doğrulanamadı**. Endeks Verileri sayfası: https://borsaistanbul.com/endeksler/endeks-verileri [D]
- BİST verisinin telifi Borsa İstanbul'da; isim ve logosu tescilli [D, ikincil].
- **Öneri:** Borsa İstanbul Veri Satış birimine yazılı başvuru: "aylık kapanış BIST 100 değerlerini (gecikmeli, tarihsel) kâr amacı gütmeyen/küçük bir eğitim sitesinde göstermek" için koşul ve ücret sorun. Yanıt gelene kadar BIST 100 satırını "veri lisansı bekleniyor" olarak bırakın.
- EVDS'de BIST endeksi bulunursa (doğrulanamadı) kaynak göstererek kullanım mümkün olabilir; yine de BİST'e sorun.
- Yahoo Finance, Investing.com, Stooq gibi sitelerin kullanım şartları genellikle yeniden yayıma izin vermez ve otomatik indirme scraping sayılır → **kullanmayın** (şartlar bu oturumda tek tek doğrulanmadı).

### 5.3 S&P 500

- **FRED SP500:** son 10 yıl günlük; telif S&P DJI'da [D]. 10 yıllık getiri için yeterli ama tam 10 yılın sınırda kalabileceğine dikkat.
- **Robert Shiller "U.S. Stock Markets 1871–Present" (Yale):** aylık S&P Composite, temettü, CPI [G]. Akademik veri; lisansı açık değil — **doğrulanamadı**.
- **S&P DJI resmî site:** https://www.spglobal.com/spdji/ [G] — endeks sayfalarında geçmiş veri indirilebiliyor olabilir; şartlar kontrol edilmeli.
- **Öneri:** FRED + atıf ("S&P 500, S&P Dow Jones Indices LLC; FRED üzerinden"), aylık örnekleme. Ticari kullanım ihtimali varsa S&P DJI'ya sorun.

### 5.4 CDS (Türkiye 5 yıllık)

- Kaynaklar Bloomberg, LSEG/Refinitiv, S&P Global (IHS Markit) — **tamamı lisanslı**. Haberlerdeki günlük değerler kaynak gösterilerek tek tük alıntılanabilir ama zaman serisi kurmak için uygun değil.
- **Ücretsiz resmî kaynak bulunamadı.** TCMB Finansal İstikrar Raporu ve Enflasyon Raporu grafiklerinde CDS yer alıyor [G], ancak bunlar Bloomberg kaynaklı ve indirilebilir seri değil.
- **Resmî proxy önerileri:**
  - Türkiye ve ABD 10 yıllık devlet tahvili faiz farkı (Türkiye: EVDS'de gösterge tahvil faizi olup olmadığı doğrulanamadı; ABD: FRED DGS10). TL tahvil kur riskini içerir, CDS ile aynı şey değildir — metodolojide açıklanmalı.
  - Hazine'nin Eurobond ihraç faizleri (Hazine ve Maliye Bak. borçlanma istatistikleri) [G] — seyrek.
- Öncelik: Düşük. Makro panoda "CDS" yerine "uzun vadeli faiz" göstergesi kullanmak daha güvenli.

---

## 6. Fikirler: siteye yeni değer katabilecek veri setleri

1. **Asgari ücretin reel ve USD karşılığı (1970'lerden bugüne)** — ÇSGB asgari ücret tarihçesi + EVDS TÜFE/USD. Nominal illüzyon makinesinin çekirdeği. https://www.csgb.gov.tr [G]
2. **Elektrik ve doğalgaz faturası reel seyri** — EPDK tarife tabloları (ulusal, Resmî Gazete) [D]; BOTAŞ tarifeleri https://www.botas.gov.tr [G]. "Ortalama hane faturası kaç asgari ücret saatine denk?"
3. **Akaryakıt fiyatı reel ve USD** — TÜİK TÜFE "benzin/motorin" alt kalemleri (resmî) veya EPDK piyasa raporları. Pompa fiyatlarını dağıtıcı sitelerinden çekmek scraping → izin.
4. **Gıda fiyatları: TÜFE gıda alt kalemleri + İBB hal fiyatları** — İBB Açık Veri Portalı https://data.ibb.gov.tr [G] (lisans portalda belirtilir; çoğu açık lisans — doğrulanamadı).
5. **TÜRK-İŞ açlık ve yoksulluk sınırı** (aylık, Ankara 4 kişilik aile) — https://www.turkis.org.tr [G]. Alternatif gösterge; "resmî değil, sendika hesabı" notuyla. Siyasi algı riskine dikkat.
6. **Kartlı harcama, sektör bazında (reel)** — BKM aylık bültenleri [D]. "Market harcaması reel olarak arttı mı?"
7. **Turizm geliri ve yabancı ziyaretçi** — Kültür ve Turizm Bakanlığı sınır istatistikleri https://yigm.ktb.gov.tr [G]; TÜİK turizm geliri.
8. **Kira getirisi / amortisman süresi (il bazında)** — TCMB KFE + TÜİK TÜFE kira + BETAM ilan kiraları (izinle). "Ev kaç yıllık kirayla ödenir?" Konut sayfasının yıldızı olur.
9. **Konut kredisi taksitinin ortalama ücrete oranı (erişilebilirlik endeksi)** — EVDS konut kredisi faizi + KFE + SGK ortalama kazanç. Tamamen resmî verilerle türetilir.
10. **Ülkelerarası reel konut fiyatı ve reel ücret** — BIS konut fiyatları [D] + OECD ortalama ücretler [G].
11. **Altın/ev, ev/otomobil gibi "takas oranları"** — EVDS + TÜİK; görsel kart için çok paylaşılabilir.
12. **Vergi yükü: il bazında vergi tahsilatının bütçeden geri dönüşü** — GİB il bazında tahsilat + Hazine il bazında harcama (Muhasebat il bazında bütçe gerçekleşmeleri yayımlıyor — doğrulanamadı). Siyasi yoruma kaymamaya dikkat.
13. **Elektrik tüketimi (gerçek zamanlı ekonomik aktivite göstergesi)** — EPİAŞ Şeffaflık Platformu https://seffaflik.epias.com.tr [G]; API var, kayıt gerekebilir (doğrulanamadı).
14. **Emeklilik (BES) ve OKS istatistikleri** — Emeklilik Gözetim Merkezi https://www.egm.org.tr [G]; fon getirisi değil, katılımcı sayısı/birikim (tavsiye riskinden uzak).

---

## 7. Sahibinin yapması gerekenler

### 7.1 Kayıt olunacak yerler / API anahtarları

| Kurum | Ne yapılacak | Not |
|---|---|---|
| TCMB EVDS 3 | https://evds3.tcmb.gov.tr üye ol → Profilim → API anahtarını kopyala → `.env` ve GitHub Secrets | EVDS 3 kullanım şartları ve kılavuzunu indirip depoya **kopyasını değil, bağlantısını** koyun; eski `evds2` API'ye güvenmeyin |
| FRED | fred.stlouisfed.org hesap → API Keys | Kullanılacak her serinin notlarında "Copyright" var mı kontrol |
| BLS | API v2 kaydı | FRED yeterliyse isteğe bağlı |
| UN Comtrade | Ücretsiz hesap + anahtar | İsteğe bağlı |
| IMF Data Portal | Beta portal hesabı (Swagger için) | İsteğe bağlı |
| Cloudflare | Pages + Web Analytics | — |

### 7.2 İzin / teyit istenecek kurumlar (yazılı, e-posta ile)

1. **TCMB** — Sitede reklam veya ücretli bülten olacaksa: "EVDS verilerinin kaynak gösterilerek ticari nitelikli bir sitede yayımlanması" sorusu (genel site koşullarındaki "ticari kullanım yazılı izne tabidir" maddesi nedeniyle).
2. **TÜİK** — Kaynak göstererek yeniden yayım teyidi; ayrıca MEDAS/JSON-stat uç noktalarının otomatik sorgulanmasının uygun olup olmadığı.
3. **Borsa İstanbul (Veri Satış)** — BIST 100 tarihsel aylık kapanış verisinin sitede gösterimi için lisans koşulları ve ücret.
4. **S&P Dow Jones Indices** — S&P 500 tarihsel verisinin gösterimi (FRED üzerinden gelse bile telif S&P'de).
5. **BETAM (Bahçeşehir Üniv.)** — sahibindex raporlarındaki serilerin grafiklenip yayımlanması için izin; mümkünse ham aylık seri (Excel) talebi.
6. **sahibinden.com** — Yalnızca BETAM dışı ham veri isteniyorsa kurumsal başvuru. **Scraping yok.**
7. **BDDK, SGK, TOBB, TİM** — Kaynak göstererek kullanım teyidi (büyük ihtimalle sorun yok ama yazılı teyit "güven kalkanı"na eklenir).
8. **Takasbank/TEFAS** — Fon verisi kullanılacaksa (önerilmez).
9. **WID** — Veri lisansı (info@wid.world).
10. **Endeksa / REIDIN / Global Property Guide** — Yalnızca kullanılmak istenirse; büyük ihtimalle ücretli.

### 7.3 Uygulama notları

- Her JSON'da: `source`, `source_url`, `series_code`, `retrieved_at`, `license_note`, `unverified` alanları.
- Elle güncellenen CSV'ler (İTO, SEGE, TOBB, SGK, BETAM) için `data/manual/` altında, her dosyanın yanında kaynak PDF bağlantısı ve indirme tarihi.
- Lisanslı veri (BIST, S&P, CDS, LBMA) gelene kadar satırları "veri lisansı bekleniyor" diye işaretleyin; tahminî/uydurma değer koymayın.

---

## 8. Doğrulanamayanlar

- EVDS 3 API'nin uç nokta biçimi ve anahtarın nasıl gönderildiği (resmî EVDS 3 web servis kılavuzu bulunamadı).
- Eski `evds2` REST API'nin 2025 sonunda kapandığı iddiası (yalnızca bir üçüncü taraf kaynak).
- EVDS'de altın, BIST 100, gösterge tahvil faizi ve Piyasa Katılımcıları Anketi serilerinin bulunup bulunmadığı ve kodları.
- TCMB genel site koşullarındaki "ticari kullanım yazılı izne tabidir" maddesinin EVDS verisine uygulanıp uygulanmadığı.
- TÜİK'in yeniden kullanım/lisans metni; `data.tuik.gov.tr`, `biruni.tuik.gov.tr/medas` adreslerinin güncel durumu; JSON-stat uç noktası (`databrowser2.tuik.gov.tr`) ve SDMX servisinin kapandığı bilgisi.
- BDDK, SGK, TOBB, TİM, KAP, TEFAS, ODMD, OSD, İTO, BKM kullanım şartları.
- TOBB il bazında verilerinin Excel olarak sunulup sunulmadığı.
- sahibinden.com kullanım koşullarındaki otomatik erişim/scraping maddesinin tam metni (siteye bu oturumdan erişilemedi; `www.sahibinden.com` ve `www.teknoblog.com` alan adlarının oturum ağ ayarlarında izinli olması gerekir).
- BETAM raporlarının kullanım şartları ve ham seri sunulup sunulmadığı.
- Endeksa, Hepsiemlak, Emlakjet, Global Property Guide şartları ve API varlığı.
- Borsa İstanbul Datastore ücretleri ve gecikmeli/tarihsel endeks verisi kullanım koşulları.
- World Bank Pink Sheet ve IMF emtia fiyatlarının lisansı (CC BY 4.0 varsayımı).
- OECD veri setlerinin kesin lisans metni (CC BY 4.0'ın yazılı içerikle sınırlı olduğu dipnotu nedeniyle).
- IMF IFS'in bölündüğü ve eski kodların çalışmadığı bilgisi (üçüncü taraf R paketi).
- WID veri lisansı; Shiller veri setinin lisansı; Yahoo/Investing/Stooq şartları.
- FRED'deki LBMA altın serilerinin kaldırılma tarihi.
- Big Mac verisinin MIT (kod) lisansı (CC BY 4.0 veri lisansı README aktarımıyla doğrulandı; LICENSE dosyası açılmadı).
- Türkiye CDS'i için ücretsiz resmî bir zaman serisi (bulunamadı).
- Bölüm 2.4–2.13 ve 4. bölümdeki [G] işaretli URL'ler bu oturumda açılmadı.

---

### Başvurulan kaynaklar (seçme)

- EVDS kullanım şartları: https://evds3.tcmb.gov.tr/igmevdsms-dis/documents/showDocument?docId=18
- TCMB site koşulları: https://www.tcmb.gov.tr/wps/wcm/connect/ekonomi/hie/diger/kullanim+kosullari
- EVDS 2 kılavuzu: https://evds2.tcmb.gov.tr/help/videos/EVDS_Web_Service_Usage_Guide.pdf
- borsapy sürüm notu (evds2 kapanış iddiası): https://github.com/saidsurucu/borsapy/releases/tag/v0.10.0
- BDDK FinTürk: https://www.bddk.org.tr/BultenFinturk/tr/Home/HaberBulteni
- SEGE-2022: https://www.geka.gov.tr/uploads/news_v/sege-2022.pdf
- BETAM örnek rapor: https://betam.bahcesehir.edu.tr/wp-content/uploads/2021/11/sahibindex-Konut-Piyasasi-Gorunumu-Kasim-2021.pdf
- REIDIN örnek rapor: https://reidin.com/wp-content/uploads/2024/08/REIDIN-EMLAK-ENDEKS_202407.pdf
- FRED API şartları: https://fred.stlouisfed.org/docs/api/terms_of_use.html
- BIS şartları: https://www.bis.org/terms_statistics.htm , API: https://stats.bis.org/api-doc/v2
- OECD açık erişim duyurusu: https://www.oecd.org/en/about/news/press-releases/2024/07/oecd-data-publications-and-analysis-become-freely-accessible.html
- IMF API: https://data.imf.org/en/Resource-Pages/IMF-API
- Numbeo: https://www.numbeo.com/common/terms_of_use.jsp , https://www.numbeo.com/premium/commercial-license
- LBMA / IBA: https://www.lbma.org.uk/prices-and-data/lbma-gold-price/lbma-gold-price , https://www.ice.com/iba/licensing
- Big Mac: https://github.com/TheEconomist/big-mac-data
- Borsa İstanbul endeks verileri: https://borsaistanbul.com/endeksler/endeks-verileri
