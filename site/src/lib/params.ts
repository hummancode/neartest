// Regulated-rate registry (site/data/mevzuat.json, built by pipeline/params.py).
import raw from "../../data/mevzuat.json";

export interface ParamEntry {
  value: number; effective_from: string | null; status: "verified" | "candidate" | "example";
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
  if (!p || !p.current) return null;
  const c = p.current;
  const note = c.status === "verified" ? `kaynak: ${c.source.title}` : c.status === "candidate" ? "mevzuattan alındı, resmî metinden doğrulanmadı" : "örnek değer";
  return { value: c.value, note: `${note} — bkz. Mevzuat sayfası` };
}
