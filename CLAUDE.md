# Finans Portalı — Claude Code Başlangıç Promptu

> **Nasıl kullanılır:** Boş bir klasörde Claude Code'u aç. Bu dosyanın tamamını
> `CLAUDE.md` adıyla klasöre koy (Claude Code her oturumda otomatik okur).
> Sonra her oturumda **yalnızca bir aşama** iste: "CLAUDE.md'deki Aşama 1'i yap."
> Bir aşama bitip testler geçmeden sonrakine geçme. Bu, 250 $'lık krediyi
> korumanın en önemli kuralı.
>
> `[MARKA]` yazan yerleri seçtiğin isimle değiştir.

---

## 1. Proje özeti

`[MARKA]`, finansal okuryazar Türk beyaz yakası için **reel (enflasyon ve kurdan
arındırılmış) finans verisi** sunan bir web sitesi ve haftalık bültendir.

Temel vaat: *"Rakamların nominal hâlini herkes gösterir; biz reel hâlini,
hesabı şeffaf biçimde gösteririz."*

**Bu site yatırım tavsiyesi vermez.** Hesaplar, karşılaştırır ve varsayımlarını
gösterir; kararı kullanıcıya bırakır. Hiçbir sayfada "şunu al/sat", hedef fiyat
veya kişiye özel öneri olmayacak.

## 2. Teknik ilkeler

- **Statik site + günlük veri hattı.** Sunucu yok, veritabanı yok (ilk aşamalarda).
  - Site: Astro (veya gerekçesini açıklayarak önerdiğin eşdeğer bir statik site aracı).
  - Veri hattı: Python betikleri → JSON dosyaları → site bu JSON'ları okur.
  - Zamanlama: GitHub Actions ile günde bir kez veri çek, testleri koş, siteyi yeniden derle.
  - Yayın: Cloudflare Pages (ücretsiz katman).
- **Kod, değişken adları ve yorumlar İngilizce; site arayüzü Türkçe.**
- **Tüm hesaplar test edilmiş, deterministik Python fonksiyonlarıdır.** Arayüz
  hesap yapmaz, sadece hazır sonucu gösterir. Tarayıcı içi hesaplayıcılar için
  aynı formüller TypeScript'e taşınır ve aynı test vakalarıyla doğrulanır.
- **Önce test, sonra kod.** Her hesap fonksiyonu için önce elle doğrulanmış
  örnek değerlerle test yaz, sonra fonksiyonu.
- **Her sayının kaynağı vardır.** Her veri serisi için kaynak adı, seri kodu,
  son güncelleme tarihi JSON'da tutulur ve sitede gösterilir. Kaynağı
  doğrulanamayan veri `unverified: true` olarak işaretlenir.
- **Basit tut.** Gerekmeyen kütüphane, framework veya soyutlama ekleme.
  Emin olmadığın bir tasarım kararında dur ve bana sor.

## 3. Veri kaynakları

- **TCMB EVDS** (ana kaynak, API anahtarı gerekir; anahtarı `.env` dosyasında
  ve GitHub Secrets'ta tut, asla koda yazma): TÜFE, döviz kurları, mevduat ve
  kredi ağırlıklı ortalama faizleri, mümkünse altın fiyatı.
- **ABD TÜFE:** BLS veya FRED.
- **Altın, BIST 100, S&P 500:** Ücretsiz ve kullanım şartlarına uygun bir kaynak
  öner; seçmeden önce seçenekleri, sınırlarını ve şartlarını bana listele.
- **İTO ve diğer alternatif endeksler:** İlk aşamada elle güncellenen bir CSV.
- **Web sitelerinden otomatik veri çekme (scraping) yapma**, önce bana sor.

Seri kodlarını tahmin etme. EVDS'den gerçekten sorgulayıp doğrula, bulamazsan
bana söyle.

## 4. Sayfalar

1. **Ana sayfa — "Reel Tablo":** Mevduat, kredi, dolar, euro, altın, BIST 100,
   S&P 500 için son 1, 3, 5 ve 10 yıllık getiri; nominal TL, USD ve reel TL
   olarak. Her satırın yanında küçük bir trend çizgisi.
2. **Kişisel enflasyon hesaplayıcı:** Kullanıcı harcama dağılımını girer (kira,
   gıda, ulaşım, eğitim vb.); TÜFE alt kalemlerinin ağırlıklarıyla kişisel
   enflasyonu hesaplanır ve resmi TÜFE ile karşılaştırılır. Sonuç paylaşılabilir
   bir görsel kart olarak indirilebilir. Bu bir *kişisel hesaptır*, resmi
   enflasyon iddiası değildir; sayfada bu açıkça yazar.
3. **Nominal illüzyon makinesi:** "X yılında Y TL" girilir; bugünkü karşılığı
   TÜFE, dolar, altın ve asgari ücret cinsinden gösterilir. Paylaşılabilir kart üretir.
4. **Reel faiz tablosu:** Mevduat ve kredi faizlerinin geçmiş ve son
   enflasyonla karşılaştırması (ex-post reel faiz). Beklenti verisi varsa
   (TCMB Piyasa Katılımcıları Anketi) ex-ante reel faiz de.
5. **Metodoloji:** Her hesabın formülü, veri kaynakları, varsayımlar ve bilinen
   sınırlar. Bu sayfa güven kalkanının kendisidir; özenle yaz.
6. **Bülten:** Kayıt formu (bülten platformunun gömülü formu) ve geçmiş sayılar.
7. **Yasal uyarı ve gizlilik:** "Yatırım tavsiyesi değildir" metni, KVKK uyumlu
   gizlilik metni. Hesaplayıcılar kullanıcı verisini sunucuya göndermez,
   tarayıcıda çalışır; bunu açıkça yaz.

## 5. Tasarım

- Sade, hızlı, mobil öncelikli. Koyu ve açık tema.
- Veri ağırlıklı ama okunabilir: büyük rakamlar, az renk, net tablolar.
- Fontlar: başlıklar için Anton, metin ve veri için Inter (Türkçe karakter desteği şart).
- Paylaşılabilir kartlar 1200×1500 (4:5), Twitter akışında kırpılmayacak boyutta.
- Analytics: çerez gerektirmeyen, gizlilik dostu bir araç (ör. Cloudflare Web Analytics).

## 6. Aşamalar — her oturumda yalnızca bir tane

**Aşama 1 — İskelet ve veri hattı**
Proje yapısı, EVDS'den TÜFE ve USD/TRY çeken betik, JSON çıktısı, testler,
GitHub Actions iş akışı. Bitti sayılma ölçütü: `pytest` geçiyor, JSON üretiliyor.

**Aşama 2 — Reel getiri motoru**
Reel getiri, USD bazlı getiri ve yıllıklandırma fonksiyonları; elle hesaplanmış
en az 10 test vakası. Bitti ölçütü: tüm testler geçiyor ve sonuçlar bir tablo
olarak yazdırılabiliyor.

**Aşama 3 — Ana sayfa (Reel Tablo)**
Astro sitesi, ana sayfa, metodoloji sayfasının ilk hâli, Cloudflare Pages'a yayın.

**Aşama 4 — Nominal illüzyon makinesi + paylaşılabilir kart**

**Aşama 5 — Kişisel enflasyon hesaplayıcı**

**Aşama 6 — Reel faiz tablosu**

**Aşama 7 — Bülten entegrasyonu, yasal sayfalar, son kontroller**

Her aşamanın sonunda: ne yaptığını, nelerin test edildiğini ve bilinen
eksikleri kısaca özetle; `CHANGELOG.md` dosyasına bir satır ekle.

## 7. Kesinlikle yapma

- Yatırım tavsiyesi, hedef fiyat, "al/sat/tut" ifadesi.
- Kendi resmi enflasyon endeksini üretip yayınlamak.
- Siyasi yorum içeren metin.
- Kullanıcı finansal verisini sunucuda saklamak.
- API anahtarlarını koda veya repoya yazmak.
- Doğrulamadan veri serisi kodu veya rakam uydurmak.
