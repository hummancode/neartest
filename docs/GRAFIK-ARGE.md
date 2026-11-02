# Grafik Ar-Ge: neyi, neden seçtik

## 1. Araştırma özeti

- **Algı sırası (Cleveland & McGill, 1984; Heer & Bostock, 2010).** İnsanlar nicelikleri en iyi ortak bir
  eksen üzerindeki konumla, sonra uzunlukla, daha kötü açıyla ve alanla karşılaştırır. Pasta/halka grafikler
  açı ve alan kullanır; yakın değerleri ayırt etmek ve 6'dan fazla parçayı okumak zorlaşır.
- **Pasta/halka ne zaman iyi?** Tek bir bütünün "kabaca nasıl bölündüğünü" bir bakışta görmek için, az parçayla
  (≤ 6) ve yüzdeler doğrudan yazılıysa. Kesin karşılaştırma için sıralı çubuk daha doğrudur.
- **Çok parçalı dağılım (15–20 sektör):** ağaç haritası (treemap) alanı kullanır ama dikdörtgenler sıralı ve
  etiketli olduğunda pastadan çok daha fazla parçayı okunur kılar (Bruls, Huizing & van Wijk, 2000 — squarified).
- **Birden çok bütünü karşılaştırmak** (illerin sektör yapısı): %100 yığılmış çubuk; her satır aynı uzunlukta,
  aynı renk aynı sektör.
- **İki gösterge arasındaki ilişki:** dağılım grafiği; büyüklük farkı çoksa logaritmik eksen. Korelasyon
  nedensellik değildir — grafiğin altında yazar.
- **Eşitsizlik:** Lorenz eğrisi Gini katsayısının görsel karşılığıdır (köşegen ile eğri arasındaki alanın iki katı).
- **Renk:** kategorik palet sabit sırada, renk körlüğü ayrımı doğrulayıcıyla ölçülür (komşu çiftlerde ΔE ≥ 8);
  açık temada kontrastı düşük renkler için doğrudan etiket ve değerli lejant zorunlu. Sıralı (tek tonlu) renk
  haritada; gökkuşağı yok.

## 2. Uygulananlar

| Yer | Grafik | Neden |
|---|---|---|
| İl künyesi — GSYH, istihdam, pazarlar | **Halka** (ilk 5 + Diğer), dilim üstünde %, değerli lejant; **Halka / Ağaç / Çubuk** seçimi | Bir bakış + kesin okuma seçeneği |
| İl künyesi — ihracat sektörleri | **Ağaç haritası** (varsayılan) | 15–18 sektör pastada okunmaz |
| İl künyesi — bölgedeki illerle sektör yapısı | **%100 yığılmış çubuk**, il vurgulu, Türkiye satırı | Birkaç bütünü karşılaştırmanın doğru biçimi |
| İl künyesi — eşitsizlik | **Lorenz eğrisi** (gelir vs tahmini servet) | Gini'nin görsel karşılığı, "en yoksul %50'nin payı" |
| Harita — il kartı | **Küçük halka** (GSYH sektörleri) | Kartta bir bakışta yapı |
| Harita — dağılım grafiği | **Dağılım grafiği**, log eksen, seçili il vurgulu, korelasyon | 81 ili iki boyutta konumlamak |
| Türkiye profili | Ulusal **halka** (GSYH) ve **ağaç haritası** (sektörel ihracat) | Ulusal yapı |

Tümü bağımlılıksız SVG; ipucu kutusu, klavye odağı, ekran okuyucu etiketi; 320 px'te taşmasız.

## 3. Sıradaki öneriler (öncelik sırasıyla)

1. **"81 il içinde nerede?" nokta şeridi:** il künyesindeki her göstergenin yanında 81 ilin tek eksende
   dağılımı, seçili il vurgulu (sıra numarasından daha bilgilendirici).
2. **Zaman kaydırıcılı harita:** il verisi yıllara göre girildiğinde haritayı yıl yıl oynatma.
3. **Altıgen kartogram:** 81 il eşit büyüklükte altıgen; küçük iller (Yalova, Kilis) büyük illerin gölgesinde kalmaz.
4. **İki değişkenli harita (bivariate):** iki gösterge aynı haritada 3×3 renk matrisiyle (ör. gelir × eşitsizlik).
5. **Sankey (akış) grafiği:** il → sektör → ihracat pazarı.
6. **Şelale (waterfall) grafiği:** kredi maliyeti dökümü (anapara → faiz → KKDF → BSMV → masraf).
7. **Eğim grafiği (slope chart):** iki yıl arasında illerin sıralama değişimi.
8. **Isı haritası:** il × sektör uzmanlaşma (LQ) matrisi.
9. **Belirsizlik yelpazesi (fan chart):** senaryo motoru geldiğinde tahmin aralıkları.
10. **Her grafiği PNG olarak indirme** ve grafiklerde olay işaretleri (ör. faiz kararları).
