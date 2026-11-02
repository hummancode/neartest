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
| 🟡 | **Hisse takibi**: hisse sayfaları, grafik aracında hisseler | Fiyat verisi lisanslı: Borsa İstanbul veri dağıtımı (ücretli), lisanslı veri sağlayıcılar; ücretsiz kaynakların çoğu otomatik çekmeyi yasaklıyor. Şimdilik `data/manual/stocks/<KOD>.csv` |
| 🟡 | **Portföyüm** (tarayıcıda): alış tarihine göre reel / USD / altın getiri | Altın, döviz hazır; hisseler veriyle |
| ⬜ | Temettü ve bölünme düzeltmeli toplam getiri | KAP duyuruları + fiyat verisi |
| ⬜ | Yatırım fonları (TEFAS) reel getiri karşılaştırması | TEFAS kullanım şartları kontrol edilmeli |
| ⬜ | Eurobond / DİBS getiri eğrisi, reel getiri (TÜFE'ye endeksli tahviller) | Hazine, EVDS |

## 2. Makro
| | Fikir | Veri / not |
|---|---|---|
| 🟡 | **Makro Pano**: GSYH büyümesi, kişi başı GSYH ($), TÜFE, işsizlik, cari denge, rezervler, politika faizi, CDS, bütçe | TÜİK/TCMB/HMB via EVDS; **CDS**: resmi ücretsiz kaynak yok (lisanslı veri) → elle |
| 🟡 | **İlişkiler**: iki göstergenin birlikte hareketi, kayan korelasyon | mevcut seriler; korelasyon ≠ nedensellik |
| ⬜ | Olay penceresi analizi: PPK kararları gibi tarihli resmi olaylar etrafında piyasaların ortalama hareketi | olay listesi elle, yalnızca resmi olay adı ve tarih (yorum yok) |
| ⬜ | Ülke karşılaştırması: Türkiye ve benzer ekonomiler (enflasyon, büyüme, borç/GSYH) | Dünya Bankası / IMF açık verileri (lisansları uygun) |
| ⬜ | Enflasyon beklentileri vs gerçekleşme (Piyasa Katılımcıları Anketi) | EVDS |
| ⬜ | Ex-ante reel faiz | Anket beklentisi + faiz |

## 3. Hane ve kişisel karar araçları
| | Fikir | Veri / not |
|---|---|---|
| ✅ | Nominal illüzyon, kişisel enflasyon, kirala/satın al | — |
| ⬜ | **Taksitli mi peşin mi?** Taksitlerin bugünkü değeri vs peşin indirim | faiz + enflasyon beklentisi, yeni veri gerekmez |
| ⬜ | Reel maaş takibi: maaş artışın enflasyonu, doları, altını yendi mi? | TÜFE + kullanıcı girdisi (tarayıcıda) |
| ⬜ | Paranın erime hızı: TL'nin alım gücünün yarılanma süresi | TÜFE |
| ⬜ | Birikim hedefi: reel hedefe ulaşmak için aylık birikim | varsayım girdileri |
| ⬜ | Kredi kartı / ihtiyaç kredisi reel maliyeti | EVDS faizleri |

## 4. Platform
| | Fikir | Not |
|---|---|---|
| ✅ | Paylaşılabilir bağlantı ve PNG kartlar | — |
| ⬜ | Her tablo/grafik için CSV indirme | statik, kolay |
| ⬜ | Haftalık bülten taslağının otomatik üretimi (yalnızca rakamlar) | elle onaylanır |
| ⬜ | E-posta uyarıları ("reel mevduat faizi pozitife döndü") | sunucu gerektirir — sonraki faz |
| ⬜ | Açık JSON uç noktaları (site/data zaten statik) | lisanslar uygun serilerle |

## Veri kaynağı kararları (sahibin onayı gerekli)
1. EVDS seri kodları (anahtar + ağ izni) — TÜFE, kurlar, faizler, KFE, GSYH, işsizlik, cari denge, rezerv, politika faizi.
2. BIST 100, S&P 500, gram altın kaynağı.
3. Hisse fiyatları: lisanslı kaynak mı, elle mi?
4. CDS: lisanslı kaynak mı, elle mi?
5. 0 km otomobil sepetindeki modeller; BETAM verisinin kullanım izni.
