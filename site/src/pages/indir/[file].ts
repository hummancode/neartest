// Static downloads: every data file as JSON, plus tidy CSVs of the main datasets.
// Built at build time; served as plain files (no server).
import { tablo } from "../../lib/data.ts";
import { prices } from "../../lib/prices.ts";
import { macro } from "../../lib/macro.ts";
import { countries } from "../../lib/countries.ts";
import { realRates } from "../../lib/rates.ts";
import { levels } from "../../lib/levels.ts";
import { housing } from "../../lib/housing.ts";
import { status } from "../../lib/status.ts";
import { provinces } from "../../lib/provinces.ts";
import { shiftMonth } from "../../lib/engine.ts";
import { districts } from "../../lib/districts.ts";
import bigmac from "../../../data/bigmac.json";

const JSON_FILES: Record<string, unknown> = {
  reel_tablo: tablo, fiyatlar: prices, makro: macro, ulkeler: countries, reel_faiz: realRates,
  seviyeler: levels, konut: housing, durum: status, iller: provinces, ilceler: districts, bigmac,
};

const esc = (v: unknown) => {
  const s = v === null || v === undefined ? "" : String(v);
  return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
const toCsv = (rows: unknown[][]) => "﻿" + rows.map((r) => r.map(esc).join(",")).join("\n") + "\n";

function csvPrices() {
  const ids = prices.instruments.map((i) => i.id);
  const all = new Set<string>();
  const maps: Record<string, Record<string, number>> = {};
  for (const id of ids) {
    const s = prices.series[id];
    maps[id] = {};
    s.values.forEach((v, k) => { const m = shiftMonth(s.start, k); maps[id][m] = v; all.add(m); });
  }
  const months = [...all].sort();
  return toCsv([["ay", ...ids], ...months.map((m) => [m, ...ids.map((id) => maps[id][m] ?? "")])]);
}
const csvMacro = () => toCsv([["gosterge", "birim", "donem", "deger", "ornek_veri"],
  ...macro.indicators.flatMap((i) => i.points.map(([m, v]) => [i.id, i.unit, m, v, i.sample]))]);
const csvCountries = () => toCsv([["gosterge", "kod", "ulke", "yil", "deger", "ornek_veri"],
  ...countries.indicators.flatMap((i) => Object.entries(i.series).flatMap(([iso, pts]) => pts.map(([y, v]) => [i.id, i.code, iso, y, v, i.sample])))]);
const csvTablo = () => toCsv([["varlik", "yil", "nominal_tl", "usd", "reel_tl", "nominal_tl_yillik", "usd_yillik", "reel_tl_yillik", "ornek_veri"],
  ...tablo.rows.flatMap((r) => r.windows.map((w) => [r.id, w.years, w.nominal_tl, w.usd, w.real_tl, w.nominal_tl_annual, w.usd_annual, w.real_tl_annual, r.sample]))]);
const csvRates = () => toCsv([["ay", "mevduat_faizi", "kredi_faizi", "tufe_12ay", "reel_mevduat_son", "reel_kredi_son", "reel_mevduat_expost", "reel_kredi_expost"],
  ...realRates.rows.map((r) => [r.month, r.deposit_rate, r.credit_rate, r.cpi_12m, r.deposit_real_trailing, r.credit_real_trailing, r.deposit_real_ex_post, r.credit_real_ex_post])]);

const csvProvinces = () => {
  const ids = provinces.indicators.map((i) => i.id);
  return toCsv([["plaka", "il", "bolge", ...ids, "ornek_veri"],
    ...provinces.provinces.map((p) => [p.plaka, p.name, p.region, ...ids.map((id) => p.values[id]?.value ?? ""),
      Object.values(p.values).some((v) => v.sample)])]);
};

// Long format: one row per province/district and year.
const csvDistricts = () => toCsv([["plaka", "il", "ilce", "yil", "nufus", "ornek_veri"],
  ...Object.entries(districts.provinces).flatMap(([pl, ds]) => ds.flatMap((d) => d.points.map(([y, v]) =>
    [pl, provinces.provinces[Number(pl) - 1].name, d.name, y, v, districts.sample])))]);
const csvPopulation = () => toCsv([["plaka", "il", "yil", "nufus", "ornek_veri"],
  ...provinces.provinces.flatMap((p) => (p.history.population?.points ?? []).map(([y, v]) => [p.plaka, p.name, y, v, p.history.population.sample]))]);

const csvBigMac = () => toCsv([["tarih", "ulke_kodu", "ulke", "yerel_fiyat", "kur_dolar", "dolar_fiyati", "ham_endeks", "duzeltilmis_endeks"],
  ...Object.entries((bigmac as any).history).flatMap(([iso, h]: [string, any]) => h.points.map((p: any[]) => [p[0], iso, h.name, p[1], p[2], p[3], p[4], p[5]]))]);

const CSV_FILES: Record<string, () => string> = {
  bigmac: csvBigMac,
  iller: csvProvinces, ilceler: csvDistricts, nufus_iller: csvPopulation,
  fiyatlar: csvPrices, makro: csvMacro, ulkeler: csvCountries, reel_tablo: csvTablo, reel_faiz: csvRates,
};

export function getStaticPaths() {
  return [
    ...Object.keys(JSON_FILES).map((n) => ({ params: { file: `${n}.json` } })),
    ...Object.keys(CSV_FILES).map((n) => ({ params: { file: `${n}.csv` } })),
  ];
}

export function GET({ params }: { params: { file: string } }) {
  const [name, ext] = params.file.split(".");
  if (ext === "json") {
    return new Response(JSON.stringify(JSON_FILES[name]), { headers: { "Content-Type": "application/json; charset=utf-8" } });
  }
  return new Response(CSV_FILES[name](), { headers: { "Content-Type": "text/csv; charset=utf-8" } });
}
