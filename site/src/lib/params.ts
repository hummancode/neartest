// Regulated-rate registry (site/data/mevzuat.json, built by pipeline/params.py).
import raw from "../../data/mevzuat.json";

export type Tariff = [number | null, number][];
export interface ParamEntry {
  value: number | Tariff; effective_from: string | null; status: "verified" | "candidate" | "example";
  checked_at: string | null; checked_by: string; source: { title: string; url: string }; note: string;
}
export interface Param {
  id: string; label: string; unit: string; group: string; used_by: string[];
  official_sources: { title: string; url: string }[]; note: string | null;
  current: ParamEntry | null; upcoming: ParamEntry | null; history: ParamEntry[];
  last_checked: string | null; stale: boolean; check_every_days: number;
}
export const mevzuat = raw as unknown as { as_of: string; params: Param[] };
export const STATUS_LABEL = { verified: "doğrulandı", candidate: "doğrulanmadı", example: "örnek" } as const;

/** Default value for a calculator field plus a short provenance note. */
export function paramDefault(id: string): { value: number; note: string } | null {
  const p = mevzuat.params.find((x) => x.id === id);
  if (!p || !p.current || typeof p.current.value !== "number") return null;
  const c = p.current;
  const note = c.status === "verified" ? `kaynak: ${c.source.title}` : c.status === "candidate" ? "mevzuattan alındı, resmî metinden doğrulanmadı" : "örnek değer";
  return { value: c.value as number, note: `${note} — bkz. Mevzuat sayfası` };
}

/** Registry entry for a calculator, with year and status for display (numbers or tariffs). */
export function paramInfo(id: string) {
  const p = mevzuat.params.find((x) => x.id === id);
  if (!p || !p.current) return null;
  const c = p.current;
  return { id, label: p.label, unit: p.unit, value: c.value, year: c.effective_from ? c.effective_from.slice(0, 4) : null,
    status: c.status, statusLabel: STATUS_LABEL[c.status], note: c.note };
}

/** "158.000 TL'ye kadar %15 · … · üzeri %40" */
export function formatTariff(t: Tariff): string {
  const n = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
  const pc = (r: number) => `%${new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 1 }).format(r * 100)}`;
  return t.map(([u, r], i) => (u === null ? `${n.format(t[i - 1]?.[0] ?? 0)} TL üzeri ${pc(r)}` : `${n.format(u)} TL'ye kadar ${pc(r)}`)).join(" · ");
}
