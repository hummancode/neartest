// Build-time access to district data (site/data/ilceler.json, tr_ilceler.json).
// Import ONLY in page frontmatter; pass the slice a page needs to the client via data attributes.
import districtsRaw from "../../data/ilceler.json";
import geoRaw from "../../data/tr_ilceler.json";
import type { District, ProvinceShapes } from "./popviz.ts";

export const districts = districtsRaw as unknown as { generated_at: string; sample: boolean; source: string; has_data: boolean; unmatched: string[]; provinces: Record<string, District[]> };
export const districtGeo = geoRaw as unknown as { scale: number; source: string; license: string; provinces: Record<string, ProvinceShapes> };
