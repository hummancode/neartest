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
- 2026-11-01 — Adım 2 / Aşama 4: Nominal illüzyon makinesi (`/nominal-illuzyon`). Ay + TL tutarı →
  bugünkü karşılık TÜFE, dolar, gram altın cinsinden; hesap tarayıcıda, veri gönderilmez.
  Motor TypeScript'e taşındı (`site/src/lib/engine.ts`); Python ve TS aynı 22 vakayı
  (`tests/cases.json`) koşuyor. 1200×1500 PNG kart (örnek veriyse kartta da uyarı).
  Builder artık `site/data/seviyeler.json` da üretiyor. Asgari ücret serisi eksik.
- 2026-11-01 — Aşama 5: Kişisel enflasyon hesaplayıcı (`/kisisel-enflasyon`). Motor:
  `normalize_shares`, `inflation_contributions`, `personal_inflation` (önce test; Python + TS aynı
  30 ortak vaka). Builder `site/data/tufe_gruplari.json` üretiyor (12 TÜFE ana grubu, 12 aylık
  değişim, ağırlıklar `data/manual/tufe_agirliklari.csv`'den, yoksa ÖRNEK). 1200×1500 kart,
  "kişisel hesaptır, resmi enflasyon değildir" uyarısı sayfada ve kartta. Grup kodları/ağırlıkları doğrulanmadı.
- 2026-11-01 — Aşama 6: Reel faiz tablosu (`/reel-faiz`). Motor: `trailing_real_rates` (güncel faiz /
  son 12 ay TÜFE) ve `ex_post_real_rates` (12 ay önceki faiz / gerçekleşen TÜFE), önce test.
  Builder `site/data/reel_faiz.json` üretiyor (son 36 ay; hesap Python'da, sayfa sadece gösteriyor).
  Kredi faizi serisi ve Reel Tablo'ya "TL Kredi (borç maliyeti)" satırı eklendi (kod doğrulanmadı,
  kredi türü seçilmedi). Ex-ante (beklenti anketi) henüz yok. Trend çizgisi düz serilerde gürültüyü büyütmüyor.
- 2026-11-01 — Aşama 7: Bülten sayfası (platform seçilince `config.ts`'e form adresi yazılır; 3. taraf
  script yok) + arşiv düzeni, Yasal uyarı ve KVKK gizlilik metni (TASLAK, hukuki inceleme gerekli),
  404, `_headers`, robots.txt, alt menü. Kaynak tablosunda her serinin son veri ayı. `npm run check`
  (bağımlılıksız derleme sonrası kontrol) workflow'a eklendi. Tüm sayfalar 320/1280 px, açık/koyu
  temada konsol hatası ve taşma olmadan test edildi. README yeniden yazıldı (Cloudflare adımları).
- 2026-11-02 — MVP 1/4: Gerçek veri için API'siz yol: `data/manual/<seri>.csv` (+ `.meta.json`), EVDS web
  dışa aktarım biçimleri (`;`, `2024-1`, ondalık virgül, günlük→aylık ortalama) destekleniyor; öncelik
  raw (API) → manual → örnek. Faiz serileri yüzde→ondalık ölçekleniyor (EVDS'den gelecek veride
  100 kat hata önlendi). `/veri` sayfası (her serinin kökeni, kodu, aralığı) ve `durum.json`.
  Asgari ücret (isteğe bağlı, asla örneklenmez, değişim aylarından ileri doldurma) illüzyon
  makinesine ve karta bağlandı.
- 2026-11-02 — MVP 2/4: Varlık detay sayfaları (`/varlik/<id>`, 7 adet): "100 TL ne oldu?" etkileşimli
  grafiği (nominal / USD / reel, 1-3-5-10 yıl, log ölçek gerekirse, crosshair + ipucu, klavye ile
  gezinme, doğrudan uç etiketleri; palet doğrulayıcıdan geçti). Yollar Python'da `index_paths` ile
  hesaplanıyor (önce test; son değerler Reel Tablo ile birebir). Ana sayfa kartları detaya bağlandı.
- 2026-11-02 — MVP 3/4: Hesaplayıcılar için paylaşılabilir bağlantı ("Bağlantıyı kopyala"): girdiler URL'nin
  `#` kısmında (sunucuya gitmez); açılışta geri yüklenir, bozuk/negatif değerler güvenle yok sayılır.
- 2026-11-02 — MVP 4/4: Paylaşım önizlemesi (Open Graph + Twitter kartı, 1200×630 `og.png` ve yeniden
  üretme betiği), `SITE_URL` ile canonical ve `sitemap.xml`, theme-color. README güncellendi.
  Doğrulama: 79 Python + 33 TS testi, `npm run check` 17 sayfa, tüm sayfalar 320/1280 px açık/koyu
  temada hatasız; hesaplayıcı sonuçları JSON'dan bağımsız hesapla birebir.
- 2026-11-02 — Grafik ve Konut: `/grafik` ("X'in Y cinsinden fiyatı": otomobil, konut, altın, borsa, döviz,
  mevduat, kira; TL / reel / USD / EUR / altın / BIST / S&P / asgari ücret cinsinden; 3 seriye kadar,
  1-3-5-10 yıl/tümü, hazır kısayollar, paylaşılabilir bağlantı). `/konut`: şehir bazında konut getirisi
  (nominal/reel/USD/altın; TCMB KFE, girilmişse BETAM) ve kirala-mı-satın-al-mı hesaplayıcısı
  (taksit, masraflar, kira/ev/yatırım beklentileri, reel sonuç, başabaş, duyarlılık, yıl yıl döküm).
  Motor: `ratio_index`, `mortgage_payment`, `rent_vs_buy`, `jevons_chain_index` (önce test; TS'ye
  taşındı, 40 ortak vaka). Yeni seriler: TÜFE otomobil ve kira alt endeksleri, KFE (TR/İst/Ank/İzm);
  isteğe bağlı: 0 km bayi liste fiyatı sepeti, BETAM satılık/kiralık. Mobil menü. Sayfadaki
  hesap Python ile birebir doğrulandı (tutar ayrıştırma hatası bu sırada bulunup düzeltildi).
- 2026-11-02 — Makro ve İlişkiler: `docs/ROADMAP.md` (fikir havuzu, veri kararları). `/makro`: GSYH büyümesi,
  kişi başı GSYH, TÜFE, işsizlik, politika faizi, reel mevduat, cari denge, rezerv, CDS, bütçe/GSYH,
  USD/TRY, BIST 100 ($), altın ($) kartları (son değer, dönem, 1 yıllık değişim — Python'da), tıklanınca
  grafik. `/iliskiler`: iki göstergenin değişim korelasyonu, aynı yönde hareket oranı, kayan korelasyon,
  hizalı iki grafik; "korelasyon nedensellik değildir" uyarısı. Motor: `pearson`, `paired_changes`,
  `rolling_correlation`, `same_direction_share` (önce test, TS'ye taşındı; 46 ortak vaka). Çeyreklik /
  yıllık seriler desteklendi; makro seriler piyasa bitiş ayını geri çekmiyor. Grafik modülü: referans
  çizgisi, biçimlendirici, düzensiz aralık. Menü 1024 px altında açılır.
- 2026-11-02 — Borsa ve Portföyüm: `/borsa` (BIST 100 + elle yüklenen hisseler; reel / USD / altın / nominal,
  1-3-5-10 yıl; tarayıcıda saklanan izleme listesi; hisse verisi yokken lisans açıklaması). `/portfoy`:
  pozisyon ekle/sil (tutar, isteğe bağlı miktar, not), pozisyon ve toplam bazında nominal/reel/USD/altın
  getiri ve "enflasyona karşı" TL farkı; yerel depolama, dışa/içe aktarma; sunucuya veri gitmez.
  Motor: `holding_returns`, `portfolio_summary` (önce test; TS; 50 ortak vaka). `data/manual/stocks/`
  (kod doğrulamalı) → grafik aracı, borsa, portföy. Menü gruplandı (Piyasalar / Makro / Hesapla),
  ana sayfada araç ızgarası. Kaydırma kutularının dışına taşan erişilebilirlik etiketi hatası düzeltildi.
- 2026-11-02 — Karar araçları ve olay penceresi: `/kredi` (akdi faiz + KKDF + BSMV + peşin/aylık masraf →
  ödeme planı, gider dağılımı, iç verim oranıyla gerçek yıllık maliyet, "faiz × 12" ile fark, reel maliyet),
  `/taksit` (taksitlerin bugünkü değeri, taksit planının gizli faizi, enflasyona göre toplam), `/maas`
  (zam başına reel değişim, bugünkü TL / $ / gram altın / asgari ücret karşılığı, nominal-reel grafik;
  tarayıcıda saklanır), `/olaylar` (politika faizi artış/indirim aylarından türetilen ve elle eklenen
  olaylar etrafında ortalama/medyan yol). Motor: `irr`, `amortization`, `loan_cost`, `present_value`,
  `installment_vs_cash`, `salary_analysis`, `event_study`, `derive_rate_events` (önce test; TS; 59
  ortak vaka). Sayfa sonuçları Python ile birebir doğrulandı. Örnek politika faizi basamaklı hâle getirildi.
- 2026-11-02 — Borç araçları, ülkeler, birikim: `/kart` (yalnızca asgari ödemeyle borcun seyri, toplam faiz+vergi,
  bitmeyen borç uyarısı; nakit avansın gerçek yıllık maliyeti), `/yapilandirma` (erken kapama ücreti ve
  masraflarla mevcut vs yeni kredi: taksit, toplam, bugünkü değer), `/mevduat` (stopaj sonrası net ve
  reel yıllık getiri, enflasyonu telafi eden brüt faiz), `/birikim` (bugünkü parayla hedef için aylık
  birikim), paranın erime hızı (nominal illüzyon sayfasında), `/ulkeler` (Dünya Bankası WDI; 12 ülke,
  6 gösterge; `pipeline/worldbank.py` kodları API adıyla doğrular, günlük işte çalışır; şimdilik örnek
  veri). `/indir/*.csv|json` veri indirme. Motor: `card_minimum_payoff`, `refinance_compare`,
  `deposit_net`, `breakeven_gross_rate`, `required_saving`, `half_life_years` (önce test; TS; 71 ortak
  vaka). Menüye "Borç" grubu. Hata düzeltmesi: JS ile üretilen öğelere sayfa stilleri uygulanmıyordu
  (Astro kapsamlı stil) → sayfa stilleri genel yapıldı; ülke sıralama çubukları, kredi gider işaretleri vb. düzeldi.
- 2026-11-02 — EVDS hazırlığı: `pipeline/fetch.py` artık kaynağında "EVDS" geçen 28 seriyi çekiyor (önce yalnızca
  "TCMB EVDS" yazanlar), çeyreklik/yıllık serileri kendi sıklığında istiyor, EVDS'nin çeyrek/yarıyıl/yıl
  tarih biçimlerini ayrıştırıyor (test), tek seri hatası diğerlerini durdurmuyor. `docs/EVDS.md` kontrol listesi.
- 2026-11-02 — Mevzuat takibi: `data/params/parametreler.json` (KKDF, BSMV, stopaj, kart azami faizleri, asgari ödeme;
  tarihli geçmiş, kaynak, kontrol eden, durum: verified/candidate/example), `pipeline/params.py` (doğrulama:
  "verified" resmî kaynak + kontrol eden ister; yürürlükteki/yaklaşan değer; kontrol süresi), `/mevzuat` sayfası,
  haftalık `mevzuat-check` workflow'u (doğrulanmamış/süresi geçen oranlar için tek issue). Hesaplayıcılar
  varsayılanları kayıttan alıyor ve durumunu gösteriyor. Oranlar web aramasından "aday" olarak girildi; resmî
  sayfalar (TCMB, GİB, Resmî Gazete) bu ortamdan açılamadığı için doğrulanmadı. Kredi faizi serisi: ihtiyaç kredisi.
- 2026-11-02 — İller haritası ve Türkiye profili: `/iller` (Natural Earth il sınırları → `pipeline/geo.py` ile 55 KB
  SVG yolları; 81 il, 20 gösterge: gözlenen/türetilen/model tahmini; kantil renkli harita, il kartı (sıra, Türkiye
  payı, yıl), bölge filtresi, tablo, CSV; **hane serveti simülasyonu** — ev sahipliği, konut m², mevduat payı,
  hane büyüklüğü canlı değiştirilebilir; motor `province_wealth`, önce test, TS). `/turkiye` (bir bakışta,
  ekonomi, dış ticaret 12 aylık + partner/ürün, benzer ülkeler içinde sıra, öne çıkan iller). Yeni seriler:
  ihracat/ithalat 12 aylık (EVDS), Dünya Bankası nüfus, ihracat/ithalat/GSYH, kentli nüfus. İl ve dış ticaret
  verisi elle yüklenir (`data/manual/iller/`, `dis_ticaret_*.csv`); şu an örnek.
- 2026-11-02 — İller derinleşti: 36 gösterge — konut m² satış ve kira, konut satışı, brüt kira getirisi, amortisman,
  "100 m² ev kaç yıllık maaş", kira/maaş, SGK ortalama kazanç, gelir Gini'si (bölge), otomobil ve 1.000 kişiye
  otomobil, borsa şirketleri listesi (`iller/bist_sirketler.csv`). Model tahminleri: medyan hane serveti, servet
  Gini'si ve en zengin %10 payı (gelir Gini'sinden log-normal), yastık altı altın (Türkiye toplamı varsayımı
  illere hane × servet^β ile dağıtılır; TL değeri). Haritada eşitsizlik ve altın kaydırıcıları. 81 il künye
  sayfası (`/il/34-istanbul`…): değer, sıra, bölge ortalaması, il medyanı, şirketler. Motor: `normal_cdf`/`normal_ppf`
  (iki dilde aynı algoritma), `gini_from_sigma`, `sigma_from_gini`, `top_share_lognormal`, `wealth_inequality`,
  `gold_allocation`, `housing_affordability` (önce test; 82 ortak vaka). Sonuçlar Python ile birebir doğrulandı.
- 2026-11-02 — İllerde ekonomik yapı ve ihracat: il bazında GSYH'nin ve sigortalı istihdamın sektörlere dağılımı
  (uzmanlaşma katsayısı LQ), ihracatın sektörlere ve pazarlara dağılımı, ihracat yoğunlaşması (HHI), en büyük
  pazarın payı, ihracatın yıllık seyri ve 5 yıllık değişimi. Haritada tarım/sanayi/hizmet payları ve yoğunlaşma
  göstergeleri; il kartında özet (uzmanlaşılan sektörler, öne çıkan ihracat sektörleri, ana pazarlar); il künye
  sayfasında dağılım çubukları ve ihracat grafiği; Türkiye profilinde illerin toplamından ulusal yapı ve her
  sektörde öne çıkan iller. Motor: `shares`, `location_quotients`, `hhi` (önce test). Veri elle
  (`iller/gsyh_sektor.csv`, `istihdam_sektor.csv`, `ihracat_sektor.csv`, `ihracat_ulke.csv`); şu an örnek.
- 2026-11-02 — Grafik iyileştirmeleri ve Ar-Ge (`docs/GRAFIK-ARGE.md`): yeni bağımlılıksız grafik modülü
  `charts2.ts` — halka (ilk 5 + Diğer, dilim üstü %, değerli lejant), ağaç haritası (squarified), %100 yığılmış
  çubuk, dağılım grafiği (log eksen, seçili il vurgusu, korelasyon), Lorenz eğrisi. İl künyesinde her dağılım için
  Halka/Ağaç/Çubuk seçimi, bölgedeki illerle sektör yapısı karşılaştırması, gelir ve tahmini servet Lorenz eğrisi;
  harita kartında küçük halka; haritada iki göstergeli dağılım grafiği; Türkiye profilinde ulusal halka ve ağaç
  haritası. 6 renkli kategorik palet doğrulayıcıdan geçti. Motor: `lorenz_lognormal` (önce test). Düzeltmeler:
  `[hidden]` CSS ile ezilmesin (genel kural), grafik eksen stilleri yeni grafiklere uygulanıyor, mobilde lejant
  ve segment etiketleri taşmıyor/çakışmıyor.
- 2026-11-02 — Nüfus: il ve ilçeler. İl nüfusunun yıllık geçmişi (ADNKS, 2007–) ve türetilen göstergeler (son yıl
  artış, 5/10 yıllık yıllık ortalama artış, 10 yıllık değişim, nüfus yoğunluğu). 973 ilçenin sınırları
  (geoBoundaries/OSM, ODbL; illere nokta-çokgen testiyle atanır, adlar TÜİK biçimine çevrilir) ve ilçe nüfusu
  (`data/manual/ilceler/nufus.csv`; yoksa ilçe adları gerçek, rakamlar ÖRNEK). Yeni `/nufus` sayfası: Türkiye
  toplamı, büyüme haritası (sabit eşikli sapma paleti, iki kol doğrulandı), en hızlı büyüyen/küçülen il ve
  ilçeler, endeksli il karşılaştırması, ilçe arama. İl künyesinde nüfus grafiği, ilçe haritası, sıralanabilir
  ilçe tablosu ve seçilen ilçenin grafiği. İller haritasında nüfus göstergeleri sapma renkleriyle. CSV indirme
  (`ilceler.csv`, `nufus_iller.csv`). Motor: `growth_windows` (önce test). Grafiklerde büyük eksen
  değerleri kısaltıldı (15 mn, 250 bin).
- 2026-11-02 — Arayüz: site içi arama (Ctrl/⌘ K veya "/"; sayfalar, 81 il, 973 ilçe, göstergeler; Türkçe karakter
  duyarsız; dizin yalnızca açılınca yüklenir), menü/ana sayfa/alt bilgi tek kaynaktan (`site/src/lib/nav.ts`),
  ana sayfada kategorili dizin, alt bilgide site haritası. Yeni `/karsilastir`: 2–3 il yan yana (tüm göstergeler,
  81 il içindeki sıra, nüfus seyri endeks/kişi, GSYH sektör yapısı), il künyesinden bağlantı. Düzeltmeler:
  `.scroll-x` artık her sayfada yatay kayar, "örnek/tahmin" etiketlerine ortak stil.
- 2026-11-02 — `docs/VERI-KAYNAKLARI.md`: Türkiye ve dünya veri kaynakları araştırması (TCMB EVDS 3, TÜİK, BDDK,
  SGK, TOBB, SEGE, BETAM, BIS, OECD, IMF, FRED, Dünya Bankası…; erişim, lisans, öncelik, doğrulanamayanlar).
  `docs/EVDS.md`'ye EVDS 3 geçişi uyarısı eklendi.
- 2026-11-02 — **Big Mac endeksi (gerçek veri)**: The Economist, CC BY 4.0, GitHub'dan günlük iş akışında indirilir
  (`pipeline/bigmac.py`). 2.056 ölçümün ham endeksi `big_mac` motor fonksiyonuyla (önce test) yeniden hesaplanıp
  yayımlanan değerle karşılaştırıldı: 0 uyuşmazlık. 2005 öncesi eski TL yeni TL'ye çevrildi. Yeni `/big-mac`
  sayfası: Türkiye fiyatı, ima edilen kur, Big Mac TL fiyatı ve doların endeksli seyri, dolar fiyatı (TR/ABD/Euro),
  TL'nin yıllar içindeki konumu, 54 ülke sıralaması (ham/gelire göre düzeltilmiş), CSV indirme, metodoloji.
- 2026-11-02 — **Uzun dönem kişi başı gelir (gerçek veri)**: Maddison Project 2020, Our World in Data deposundan
  (`pipeline/longrun.py`, günlük iş akışında). Yeni `/uzun-donem`: Türkiye 1923–2018 (×19, yıllık %3,2), on yıllara
  göre büyüme, 1950'den beri 20 ülkeyle karşılaştırma, ABD ve Batı Avrupa'ya yakınsama. Lisans (CC BY 4.0 beyanı)
  doğrulanana kadar sayfada "lisans doğrulanacak" etiketi.
- 2026-11-02 — Arayüz: genel "bilgi kartı" (1200×1500 PNG, `drawFactCard`) ve tek satırlık `ShareCard` bileşeni;
  Big Mac ve Uzun dönem sayfalarında paylaşılabilir kart. Menüde ve ana sayfada **gerçek veri** işaretleri
  (renk + metin açıklaması); ana sayfada "Gerçek veriyle" öne çıkanlar şeridi.
- 2026-11-02 — **Reel konut fiyatları (gerçek veri)**: BIS seçilmiş konut fiyatı endeksleri (Türkiye için TCMB KFE),
  GitHub kopyasından günlük (`pipeline/houseprices.py`). Motor: `change_over`, `drawdown` (önce test). Yeni
  `/konut-fiyatlari`: Türkiye reel/nominal, 60 ülke/bölgeyle karşılaştırma, 1/5 yıl ve 2010'dan beri sıralama,
  paylaşılabilir kart. `docs/ACIK-VERI-REHBERI.md`: sahibin indirebileceği açık veri dosyaları (bağlantı, biçim,
  repoda dosya adı, lisans).
- 2026-11-02 — **Emtia (gerçek veri)**: altın (Dünya Bankası Pink Sheet), Brent ve Henry Hub doğal gaz (ABD EIA),
  aylık, Datahub'ın GitHub kopyalarından (ODC-PDDL) günlük (`pipeline/commodities.py`, önce test). Yeni `/emtia`:
  dönem seçmeli endeksli karşılaştırma, tek seri fiyat grafiği, altın/petrol oranı (medyan çizgisiyle), 1–20 yıllık
  değişim ve zirveye uzaklık tablosu, paylaşılabilir kart. Ana sayfa "Gerçek veriyle" şeridi 5 kutuya çıktı.
- 2026-11-03 — **Varlıklarım** (`/varliklarim`): kişisel varlık ve borç kaydı, tarihli değer güncellemeleri, net servet
  grafiği (nominal / bugünün TL'si / dolar / gram altın), varlık ve borç dağılımı, toplu "değerleri güncelle",
  satıldı/kapandı, JSON yedek + CSV, örnek kayıt. Konut için BIS/TCMB nominal endeksiyle tahmini güncel değer.
  Veriler yalnızca tarayıcıda. Motor: `net_worth_timeline` (Python + TS, ortak vakalar, önce test). "Pro (yakında)"
  bölümü: otomatik değerleme, uçtan uca şifreli eşitleme, PDF rapor — ödeme/kayıt yok.
- 2026-11-03 — **Vergi hesaplayıcıları** (`/vergi`, `/vergi/maas`, `/vergi/kira`): brüt–net maaş (SGK/işsizlik tavanı,
  kümülatif gelir vergisi, damga, asgari ücret istisnası, yıl içi zam, netten brüte, dilim geçişi uyarısı, 12 aylık tablo)
  ve konut kira geliri vergisi (istisna, götürü/gerçek gider, adım adım hesap). Motor: `progressive_tax`, `payroll_year`,
  `gross_for_net`, `rental_income_tax` (Python + TS, ortak vakalar, önce test). Mevzuat kaydı artan oranlı tarifeleri
  kabul ediyor; 9 yeni parametre (2025 değerleri, durum "doğrulanmadı" — 2026 değerleri resmî metinden girilmeli).
- 2026-11-03 — **Kredi**: `/erken-kapama` (ara ödeme veya tam kapama; "vade kısalsın" / "taksit düşsün"; erken ödeme
  ücreti; kazanç = kurtulunan faiz + KKDF + BSMV; konut kredisi seçeneği) ve `/kredi-karsilastir` (3 teklif; faiz,
  tahsis ücreti, sigorta, aylık masraf; gerçek ve reel yıllık maliyet; "en düşük faiz ≠ en ucuz" uyarısı).
  Motor: `prepayment` (Python + TS, ortak vakalar, önce test).
- 2026-11-03 — **Vergi ve BES**: `/vergi/deger-artis` (konut satışında değer artış kazancı: Yİ-ÜFE endekslemesi, istisna,
  elde tutma muafiyeti seçimi, adım adım hesap), `/vergi/emlak` (konut/işyeri/arsa/arazi, büyükşehir çarpanı, hisse
  payı, taksit), `/bes` (aylık katkı + yıllık artış, devlet katkısı, fon getirisi ve kesintisi, 5 çıkış senaryosu —
  hak ediş ve stopaj, bugünün parasıyla çıkış tutarı, reel iç verim, devlet katkısının etkisi, yıllara göre grafik).
  Motor: `capital_gain_tax`, `property_tax`, `bes_projection` (Python + TS, ortak vakalar, önce test). 14 yeni
  mevzuat parametresi (2025 değerleri, "doğrulanmadı"). Ortak tarife düzenleyici (`site/src/lib/tariff-ui.ts`).
  MTV ertelendi: resmî tarife tabloları (motor hacmi × yaş × değer) doğrulanmadan girilemez.
- 2026-11-03 — **Ekonomik Nabız** (`/ekonomik-nabiz`): 16 gösterge (büyüme, kişi başı gelir, işsizlik, enflasyon, politika
  ve reel faiz, cari denge, rezerv, CDS, bütçe, kur, borsa + gerçek veriyle reel konut, altın, Brent, Big Mac). Her biri
  için son değer, 1 yıllık değişim, son 10 yıllık aralık (en düşük/medyan/en yüksek) ve yüzdelik konum, benzer
  ekonomiler içinde sıra; "bir bakışta" 10 yılın en yüksek/en düşük bölgesindekiler. İyi/kötü puanı yok (nötr dil).
  Veri hattı: `pipeline/nabiz.py` (önce test), motor: `percentile_rank`, `window_stats`.
- 2026-11-03 — **Finansal sağlık kontrolü** (`/saglik-kontrolu`): tasarruf oranı, borç taksiti/gelir, acil durum fonu
  (ay), borç/yıllık gelir, net servet, varlık dağılımı (kripto dahil); yaygın referans aralıkları nötr bantla;
  Varlıklarım'dan aktarma; isteğe bağlı tarayıcıda hatırlama. **Dövizle borçlanmanın gerçek maliyeti** (`/doviz-borc`):
  TL eşdeğer maliyet, başabaş kur artışı, kur senaryoları, teminatlı (kripto) kredide tasfiye eşiği; platform/ürün
  önermez, hukuki uyarı (SPK izni, döviz kredisi kısıtı). Motor: `financial_health`, `fx_borrowing`,
  `collateral_liquidation` (Python + TS, ortak vakalar, önce test).

- 2026-11-04 — Son kontrol: 134 sayfa 375/1280 px, koyu/açık temada tarandı (JS hatası,
  yatay taşma, NaN/undefined yok). Arama kutusuna erişilebilir etiket; ana sayfa, bülten,
  yasal uyarı ve gizlilik sayfalarına tam açıklama (SEO/paylaşım önizlemesi).
- 2026-11-04 — Üyelik/abonelik/ödeme araştırması (`docs/UYELIK-ODEME.md`: iyzico, PayTR, Paddle,
  Lemon Squeezy, Stripe; KVKK, mesafeli satış, cayma, SPK riskleri) ve yayında olmayan prototip
  `account/`: şifresiz e-posta girişi, abonelik durum makinesi, sağlayıcı arayüzü + sahte
  sağlayıcı, imzalı/idempotent webhook, yasal onay kaydı, hesap silme. 25 test; CI'a eklendi.
  Sunucuda finansal kullanıcı verisi yok.
