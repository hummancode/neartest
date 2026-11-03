# Yol haritası ve fikir havuzu

Amaç: nominal rakamları reel, dolar ve altın bazına çeviren, makro göstergelerle piyasa verisini
**aynı zemin üzerinde** gösteren ve aralarındaki ilişkiyi şeffaf hesaplarla sentezleyen bir platform.
Kırmızı çizgiler değişmez (CLAUDE.md): yatırım tavsiyesi yok, siyasi yorum yok, kendi resmi enflasyon
endeksimiz yok, kullanıcı verisi sunucuda yok, doğrulanmamış rakam yok.

Durum: ✅ yapıldı · 🟡 altyapı hazır, veri/karar bekliyor · ⬜ fikir

## 1. Piyasa ve varlıklar
| | Fikir | Veri / not |
|---|---|---|
| ✅ | Reel Tablo, varlık detayları, "100 TL ne oldu?" | EVDS (kodlar doğrulanacak) |
| ✅ | Grafik: X'in Y cinsinden fiyatı (TradingView tarzı) | mevcut seriler |
| 🟡 | **Hisse takibi**: borsa sayfası (reel/USD/altın), izleme listesi, grafik aracı ve portföyde hisseler — altyapı hazır | Fiyat verisi lisanslı: Borsa İstanbul veri dağıtımı (ücretli), lisanslı veri sağlayıcılar; ücretsiz kaynakların çoğu otomatik çekmeyi yasaklıyor. Şimdilik `data/manual/stocks/<KOD>.csv` |
| ✅ | **Portföyüm** (tarayıcıda): alış tarihine göre reel / USD / altın getiri, dışa/içe aktarma | Altın, döviz, mevduat, endeks; hisseler veri girilince |
| ⬜ | Temettü ve bölünme düzeltmeli toplam getiri | KAP duyuruları + fiyat verisi |
| ⬜ | Yatırım fonları (TEFAS) reel getiri karşılaştırması | TEFAS kullanım şartları kontrol edilmeli |
| ⬜ | Eurobond / DİBS getiri eğrisi, reel getiri (TÜFE'ye endeksli tahviller) | Hazine, EVDS |

## 2. Makro
| | Fikir | Veri / not |
|---|---|---|
| ✅ | **Makro Pano** (örnek veriyle; seri kodları doğrulanacak): GSYH büyümesi, kişi başı GSYH ($), TÜFE, işsizlik, cari denge, rezervler, politika faizi, CDS, bütçe | TÜİK/TCMB/HMB via EVDS; **CDS**: resmi ücretsiz kaynak yok (lisanslı veri) → elle |
| ✅ | **İlişkiler**: iki göstergenin birlikte hareketi, kayan korelasyon | mevcut seriler; korelasyon ≠ nedensellik |
| ✅ | Olay penceresi: faiz artış/indirim ayları (politika faizi serisinden) ve elle eklenen resmi olaylar etrafında ortalama/medyan hareket | `data/manual/events.csv`; ay düzeyinde (günlük veriyle iyileştirilebilir) |
| ✅ | Ülke karşılaştırması: Türkiye ve 11 benzer ekonomi (enflasyon, büyüme, kişi başı GSYH, işsizlik, cari denge, reel faiz) | Dünya Bankası WDI (CC BY 4.0); kodlar API adıyla doğrulanır; günlük işte çekilir |
| ✅ | Reel konut fiyatları, Türkiye ve 60 ülke (BIS, gerçek veri) | GitHub kopyası, günlük |
| ✅ | Emtia: aylık altın (Dünya Bankası), Brent ve doğal gaz (EIA) — gerçek veri | GitHub kopyaları, günlük |
| ⬜ | Altının TL karşılığı ve Reel Tablo'daki "Gram Altın" satırının gerçek veriye geçmesi | USD/TRY (EVDS) gerekli |
| ✅ | Uzun dönem kişi başı gelir 1923–2018 (Maddison, gerçek veri; lisans doğrulanacak) | OWID GitHub, günlük |
| ✅ | Big Mac endeksi (gerçek veri, The Economist CC BY 4.0) | GitHub, günlük |
| ⬜ | Enflasyon beklentileri vs gerçekleşme (Piyasa Katılımcıları Anketi) | EVDS |
| ⬜ | Ex-ante reel faiz | Anket beklentisi + faiz |

| ✅ | **Türkiye profili** (factbook tarzı): göstergeler, dış ticaret (12 ay, partner, ürün), benzer ülkeler içinde sıra, öne çıkan iller | TÜİK, EVDS, Dünya Bankası; dağılımlar elle |
| 🟡 | **İller ekonomik haritası**: 81 il, 43 gösterge + sektörel GSYH/istihdam/ihracat ve ihracat pazarı dağılımları, uzmanlaşma (LQ), ihracat yoğunlaşması (HHI), ihracat geçmişi; (gelir, ihracat, çalışan, ücret, şirketler + BIST listesi, mevduat/kredi, konut fiyatı/kira/getiri/erişilebilirlik, otomobil, Gini, SEGE), il kartı, 81 il künye sayfası (`/il/…`), tablo, CSV | il verileri elle (TÜİK, SGK, TOBB, KAP, BDDK) — şu an örnek |
| 🟡 | **Tahmin/simülasyon**: il bazında hane serveti, medyan servet, servet Gini'si ve en zengin %10 payı (log-normal), yastık altı altın dağılımı — varsayımlar canlı değiştirilebilir | sonraki: senaryo motoru (faiz/kur/enflasyon şoklarının hane bütçesine etkisi), il bazında projeksiyon |

| 🟡 | **Nüfus: il ve ilçeler** — yıllara göre nüfus, artış hızları, büyüyen/küçülen il ve ilçeler, ilçe haritası, endeksli il karşılaştırması | TÜİK ADNKS il/ilçe tabloları elle (şu an örnek); ilçe sınırları gerçek (OSM/geoBoundaries) |
| ⬜ | Nüfus ayrıntısı: yaş yapısı, medyan yaş, iç göç (iller arası göç matrisi), doğurganlık | TÜİK ADNKS ve göç istatistikleri |
| ✅ | İl karşılaştırma (2–3 il yan yana) | mevcut il verisi |
| ⬜ | Diğer göstergeler için il bazında zaman serileri | il verisinin yıllık geçmişi |
| ⬜ | Senaryo motoru: faiz/kur/enflasyon şoklarının hane bütçesine, kredi taksitlerine, il servetine etkisi | varsayım tabanlı |

## 3. Hane ve kişisel karar araçları
| | Fikir | Veri / not |
|---|---|---|
| ✅ | Nominal illüzyon, kişisel enflasyon, kirala/satın al | — |
| ✅ | **Taksitli mi peşin mi?** Bugünkü değer ve taksit planının gizli faizi | — |
| ✅ | Reel maaş takibi: her zam enflasyona karşı, bugünkü TL / dolar / altın karşılığı | tarayıcıda saklanır |
| ✅ | Paranın erime hızı: yarılanma süresi ve 1.000 TL'nin alım gücü (nominal illüzyon sayfasında) | TÜFE |
| ✅ | Birikim hedefi: bugünkü parayla hedef için aylık birikim | varsayım girdileri |
| ✅ | Mevduat net/reel getirisi (stopaj, vade, yenileme) ve enflasyonu telafi eden brüt faiz | — |
| ✅ | Kredinin gerçek maliyeti: KKDF, BSMV, tahsis ücreti, sigorta → iç verim oranı, ödeme planı, reel maliyet | oranlar kullanıcıdan (mevzuat değişebilir) |
| ✅ | Kredi kartı asgari ödeme ve nakit avans maliyeti; kredi yapılandırma karşılaştırması | oranlar kullanıcıdan |
| ✅ | Varlıklarım: kişisel net servet takibi (tarayıcıda) | Pro: otomatik değerleme, şifreli eşitleme (planlı) |
| ✅ | Vergi: brüt–net maaş, kira geliri vergisi | oranlar mevzuat kaydından (2026 değerleri girilmeli) |
| ✅ | Kredi: erken kapama/ara ödeme, teklif karşılaştırma | — |
| ⬜ | Vergi: değer artış kazancı (konut satışı), MTV, emlak vergisi, serbest meslek | tarifeler mevzuat kaydına |
| ⬜ | Emeklilik / BES reel getiri ve devlet katkısı hesaplayıcısı | BES kuralları kullanıcıdan |
| ⬜ | Döviz/altın tevdiat vs TL mevduat: başabaş kur | kur + faiz |

## 4. Platform
| | Fikir | Not |
|---|---|---|
| ✅ | Mevzuat takibi: tarihli oran kaydı, kaynak/durum, haftalık kontrol issue'su, hesaplayıcı varsayılanları | resmî metin doğrulaması insan tarafından |
| ✅ | Paylaşılabilir bağlantı ve PNG kartlar | — |
| ✅ | Site içi arama (sayfa, il, ilçe, gösterge) | statik dizin |
| ✅ | Veri setlerinin CSV/JSON indirilmesi (`/indir/…`, Veri durumu sayfasında) | — |
| ⬜ | Haftalık bülten taslağının otomatik üretimi (yalnızca rakamlar) | elle onaylanır |
| ⬜ | E-posta uyarıları ("reel mevduat faizi pozitife döndü") | sunucu gerektirir — sonraki faz |
| ⬜ | Açık JSON uç noktaları (site/data zaten statik) | lisanslar uygun serilerle |

## Veri kaynağı kararları (sahibin onayı gerekli)
Ayrıntılı araştırma (erişim, lisans, öncelik, kayıt/izin listesi): **`docs/VERI-KAYNAKLARI.md`**.
Sahibin indirebileceği dosyalar ve repoya kaydedilecek adları: **`docs/ACIK-VERI-REHBERI.md`**.

1. EVDS seri kodları (anahtar + ağ izni) — TÜFE, kurlar, faizler, KFE, GSYH, işsizlik, cari denge, rezerv, politika faizi.
2. BIST 100, S&P 500, gram altın kaynağı.
3. Hisse fiyatları: lisanslı kaynak mı, elle mi?
4. CDS: lisanslı kaynak mı, elle mi?
5. 0 km otomobil sepetindeki modeller; BETAM verisinin kullanım izni.
