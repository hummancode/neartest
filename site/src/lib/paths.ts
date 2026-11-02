// Typed access to site/data/seriler.json (index paths per asset and window, computed in Python).
import raw from "../../data/seriler.json";

export interface Path { months: string[]; nominal: number[]; real: number[]; usd: number[] }
export interface AssetPaths { label: string; kind: string; series: string; sample: boolean; windows: Record<string, Path> }
export interface Paths { generated_at: string; end_month: string; sample: boolean; assets: Record<string, AssetPaths> }
export const paths = raw as unknown as Paths;

// Plain-language description of each asset row (display only).
export const ABOUT: Record<string, string> = {
  deposit: "TL vadeli mevduat. TCMB'nin yıllık ağırlıklı ortalama mevduat faizinden, her ay o ayın faiziyle yeniden yatırım varsayılarak üretilen endeks. Stopaj düşülmez.",
  credit: "TL kredi borcunun maliyeti. Ağırlıklı ortalama kredi faiziyle aynı yöntemle üretilen endeks; borçlu için reel getiri negatifse, borcun reel yükü erimiştir.",
  usd: "ABD doları. TCMB USD/TRY kurunun aylık ortalaması. USD cinsinden getirisi tanım gereği sıfırdır.",
  eur: "Euro. TCMB EUR/TRY kurunun aylık ortalaması.",
  gold: "Gram altının TL fiyatı (aylık ortalama). Saklama ve alış-satış makası dahil değildir.",
  bist100: "Borsa İstanbul BIST 100 fiyat endeksi (temettüsüz).",
  sp500: "S&P 500 fiyat endeksi (temettüsüz), her ay aynı ayın USD/TRY kuruyla TL'ye çevrilir.",
};
