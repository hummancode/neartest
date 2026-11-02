// Static search index: pages, assets, provinces, districts, province indicators.
import { NAV, OTHER_PAGES } from "../lib/nav.ts";
import { provinces } from "../lib/provinces.ts";
import { districts } from "../lib/districts.ts";
import { paths } from "../lib/paths.ts";
import { provinceUrl } from "../lib/slug.ts";
import type { SearchEntry } from "../lib/search.ts";

export function GET() {
  const out: SearchEntry[] = [];
  for (const g of NAV) for (const i of g.items) out.push({ t: i.label, u: i.href, k: "Sayfa", s: `${g.label} · ${i.desc}`, w: i.keywords, r: 0 });
  for (const i of OTHER_PAGES) out.push({ t: i.label, u: i.href, k: "Sayfa", s: i.desc, w: i.keywords, r: 1 });
  for (const [id, a] of Object.entries(paths.assets) as [string, { label: string }][]) out.push({ t: a.label, u: `/varlik/${id}`, k: "Varlık", s: "nominal, dolar ve reel getiri", r: 1 });
  for (const p of provinces.provinces) out.push({ t: p.name, u: provinceUrl(p.plaka, p.name), k: "İl", s: `${p.region} · plaka ${String(p.plaka).padStart(2, "0")}`, w: String(p.plaka), r: 2 });
  for (const ind of provinces.indicators) out.push({ t: ind.label, u: `/iller#g=${ind.id}`, k: "Gösterge", s: `81 il haritası · ${ind.group}`, r: 3 });
  for (const [pl, ds] of Object.entries(districts.provinces)) {
    const p = provinces.provinces[Number(pl) - 1];
    for (const d of ds) out.push({ t: d.name === "Merkez" ? `Merkez (${p.name})` : d.name, u: `${provinceUrl(p.plaka, p.name)}#ilce=${encodeURIComponent(d.name)}`, k: "İlçe", s: p.name, r: 4 });
  }
  return new Response(JSON.stringify(out), { headers: { "Content-Type": "application/json; charset=utf-8" } });
}
