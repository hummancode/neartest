// Typed access to site/data/ulkeler.json (World Bank, computed in Python).
import raw from "../../data/ulkeler.json";

export interface CountryIndicator {
  id: string; label: string; unit: string; kind: string; code: string; verified: boolean; sample: boolean;
  series: Record<string, [string, number][]>; latest: Record<string, [string, number]>;
}
export interface Countries {
  generated_at: string; source: string; sample: boolean;
  countries: { iso: string; name: string }[]; indicators: CountryIndicator[];
}
export const countries = raw as unknown as Countries;
