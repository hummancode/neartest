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
import { shiftMonth } from "../../lib/engine.ts";

const JSON_FILES: Record<string, unknown> = {
  reel_tablo: tablo, fiyatlar: prices, makro: macro, ulkeler: countries, reel_faiz: realRates,
  seviyeler: levels, konut: housing, durum: status,
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

const CSV_FILES: Record<string, () => string> = {
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
