// Single source for the site map: header menu, home page directory and search index.
export interface NavItem { href: string; label: string; desc: string; keywords?: string; real?: boolean }   // real: page runs on real (non-sample) data
export interface NavGroup { label: string; items: NavItem[] }

export const NAV: NavGroup[] = [
  { label: "Piyasalar", items: [
    { href: "/", label: "Reel Tablo", desc: "Mevduat, kredi, döviz, altın ve borsanın 1–10 yıllık nominal, dolar ve reel getirisi.", keywords: "getiri enflasyon" },
    { href: "/grafik", label: "Grafik: X'in Y cinsinden fiyatı", desc: "Otomobili gram altınla, konutu dolarla, altını borsayla ölçün.", keywords: "araba otomobil altın dolar" },
    { href: "/emtia", label: "Emtia: altın, petrol, doğal gaz", desc: "Dünya fiyatları, dolar cinsinden: 1–20 yıllık değişim, altın/petrol oranı.", keywords: "altın ons gram petrol brent doğalgaz emtia", real: true },
    { href: "/borsa", label: "Borsa", desc: "Endeks ve hisselerin reel, dolar ve altın bazında getirisi; izleme listesi.", keywords: "bist hisse" },
  ] },
  { label: "Makro", items: [
    { href: "/turkiye", label: "Türkiye profili", desc: "Ekonominin künyesi: göstergeler, dış ticaret, benzer ülkeler, iller.", keywords: "factbook ihracat ithalat" },
    { href: "/makro", label: "Makro Pano", desc: "Büyüme, enflasyon, işsizlik, cari denge, rezerv, faiz, CDS — tek sayfada.", keywords: "gsyh cds işsizlik" },
    { href: "/iliskiler", label: "İlişkiler", desc: "CDS ile borsa, faiz ile kur: göstergeler birlikte nasıl hareket etti?", keywords: "korelasyon" },
    { href: "/reel-faiz", label: "Reel Faiz", desc: "Mevduat ve kredi faizi enflasyonun üstünde mi?" },
    { href: "/olaylar", label: "Olay penceresi", desc: "Faiz kararları etrafında piyasalar ortalama ne yaptı?", keywords: "ppk karar" },
    { href: "/uzun-donem", label: "Uzun dönem: 100 yılda gelir", desc: "1923'ten bugüne reel kişi başı gelir; on yıllara göre büyüme, zengin ülkelere yakınsama.", keywords: "maddison tarih gsyh büyüme", real: true },
    { href: "/big-mac", label: "Big Mac endeksi", desc: "Aynı hamburger her ülkede kaç dolar? TL'nin satın alma gücüne kaba bir bakış.", keywords: "satın alma gücü ppp kur hamburger", real: true },
    { href: "/ulkeler", label: "Ülke karşılaştırması", desc: "Türkiye ve benzer ekonomiler: enflasyon, büyüme, gelir, işsizlik.", keywords: "dünya bankası" },
  ] },
  { label: "İller", items: [
    { href: "/iller", label: "İller: ekonomik harita", desc: "81 il: gelir, ihracat, çalışan, şirketler, mevduat, konut, tahmini servet.", keywords: "harita şehir" },
    { href: "/karsilastir", label: "İlleri karşılaştır", desc: "İki veya üç il yan yana: tüm göstergeler, sıralar, nüfus seyri, sektör yapısı.", keywords: "karşılaştırma kıyas" },
    { href: "/nufus", label: "Nüfus: il ve ilçeler", desc: "Hangi il ve ilçe büyüyor, hangisi küçülüyor? Yıllara göre nüfus.", keywords: "nüfus ilçe göç" },
  ] },
  { label: "Borç", items: [
    { href: "/kredi", label: "Kredinin gerçek maliyeti", desc: "KKDF, BSMV ve masraflarla gerçek yıllık maliyet.", keywords: "kkdf bsmv faiz" },
    { href: "/kredi-karsilastir", label: "Kredi tekliflerini karşılaştır", desc: "Faiz, masraf ve vergilerle tekliflerin gerçek yıllık maliyeti yan yana.", keywords: "kredi teklif banka karşılaştırma" },
    { href: "/erken-kapama", label: "Erken kapama ve ara ödeme", desc: "Krediye ara ödeme ya da erken kapama ne kazandırır? Taksit mi düşsün, vade mi kısalsın?", keywords: "erken ödeme kapama ara ödeme kredi" },
    { href: "/kart", label: "Kredi kartı: asgari ödeme, nakit avans", desc: "Yalnızca asgari ödeme yaparsanız borç kaç ayda biter?" },
    { href: "/yapilandirma", label: "Kredi yapılandırma", desc: "Krediyi kapatıp yenisine geçmek gerçekten kârlı mı?" },
    { href: "/taksit", label: "Taksitli mi, peşin mi?", desc: "“Faizsiz taksit”in gizli faizi ve bugünkü değeri." },
  ] },
  { label: "Hesapla", items: [
    { href: "/vergi", label: "Vergi hesaplayıcıları", desc: "Brüt–net maaş, kira geliri vergisi, mevduat stopajı, kredi vergileri; oranlar mevzuat kaydından.", keywords: "vergi maaş brüt net kira gelir vergisi bordro sgk" },
    { href: "/bes", label: "BES: reel getiri ve devlet katkısı", desc: "Katkı, devlet katkısı, kesinti, hak ediş ve stopajla çıkışta ne kalır?", keywords: "bes bireysel emeklilik devlet katkısı fon" },
    { href: "/varliklarim", label: "Varlıklarım: net servet", desc: "Ev, araba, altın, birikim ve borçların; zaman içinde net servetin nominal, reel, dolar ve altın cinsinden.", keywords: "servet varlık borç mal portföy net değer" },
    { href: "/portfoy", label: "Portföyüm", desc: "Kendi alımlarınızın gerçek getirisi. Veriler tarayıcınızda kalır." },
    { href: "/mevduat", label: "Mevduat: net ve reel getiri", desc: "Stopaj sonrası net ve reel getiri; enflasyonu yeniyor mu?", keywords: "faiz stopaj" },
    { href: "/birikim", label: "Birikim hedefi", desc: "Bugünkü parayla hedefe ulaşmak için ayda ne biriktirmeli?" },
    { href: "/maas", label: "Reel maaş takibi", desc: "Zamlarınız enflasyonu, doları, altını yendi mi?", keywords: "zam ücret" },
    { href: "/konut-fiyatlari", label: "Reel konut fiyatları: Türkiye ve dünya", desc: "Enflasyondan arındırılmış konut fiyatı; Türkiye ve 60 ülke, BIS verisi.", keywords: "ev konut fiyat bis kfe", real: true },
    { href: "/konut", label: "Konut: kirala mı, satın al mı?", desc: "Şehirlerde konutun reel getirisi; kira ile satın almanın karşılaştırması.", keywords: "ev kira" },
    { href: "/nominal-illuzyon", label: "Nominal illüzyon ve erime hızı", desc: "Geçmişteki bir tutar bugün neye denk geliyor?" },
    { href: "/kisisel-enflasyon", label: "Kişisel enflasyon", desc: "Kendi harcama sepetinizle son 12 ayın enflasyonu.", keywords: "tüfe" },
  ] },
];

/** Pages outside the menu groups (footer, reference). */
export const OTHER_PAGES: NavItem[] = [
  { href: "/metodoloji", label: "Metodoloji", desc: "Her hesabın formülü, veri kaynakları, varsayımlar ve sınırlar." },
  { href: "/veri", label: "Veri durumu", desc: "Her serinin kaynağı, kodu, güncelliği; veri indirme.", keywords: "csv indir kaynak" },
  { href: "/mevzuat", label: "Mevzuat takibi", desc: "Hesaplarda kullanılan vergi ve oranların tarihli kaydı.", keywords: "kkdf bsmv stopaj" },
  { href: "/bulten", label: "Bülten", desc: "Haftalık bülten ve geçmiş sayılar." },
  { href: "/yasal-uyari", label: "Yasal uyarı", desc: "Yatırım tavsiyesi değildir." },
  { href: "/gizlilik", label: "Gizlilik ve KVKK", desc: "Hangi veriler işlenir, hangileri işlenmez." },
];
