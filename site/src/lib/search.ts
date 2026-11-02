// Search scoring, shared by the dialog and the tests. Turkish-aware, accent-insensitive.
export interface SearchEntry { t: string; u: string; k: string; s?: string; w?: string; r?: number }

const MAP: Record<string, string> = { ç: "c", ğ: "g", ı: "i", i̇: "i", ö: "o", ş: "s", ü: "u", â: "a", î: "i", û: "u" };
export function fold(s: string): string {
  return s.toLocaleLowerCase("tr").normalize("NFC").replace(/[çğıöşüâîû]/g, (c) => MAP[c] ?? c).normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9 ]+/g, " ").replace(/\s+/g, " ").trim();
}

/** Every query word must match the start of a word in the title, subtitle or keywords.
 *  Score: title prefix > title word start > other fields; then the entry's own rank (r, lower first). */
export function score(e: SearchEntry, words: string[]): number {
  const t = fold(e.t), rest = fold(`${e.s ?? ""} ${e.w ?? ""} ${e.k}`);
  let sc = 0;
  for (const w of words) {
    if (t.startsWith(w)) sc += 30;
    else if ((" " + t).includes(" " + w)) sc += 20;
    else if ((" " + rest).includes(" " + w)) sc += 8;
    else if (w.length >= 3 && t.includes(w)) sc += 5;
    else return 0;
  }
  if (t === words.join(" ")) sc += 25;
  return sc;
}

export function searchIndex(index: SearchEntry[], query: string, limit = 30): SearchEntry[] {
  const words = fold(query).split(" ").filter(Boolean);
  if (!words.length) return index.filter((e) => e.k === "Sayfa").slice(0, limit);
  return index.map((e) => [e, score(e, words)] as const).filter(([, s]) => s > 0)
    .sort((a, b) => b[1] - a[1] || (a[0].r ?? 9) - (b[0].r ?? 9) || a[0].t.localeCompare(b[0].t, "tr"))
    .slice(0, limit).map(([e]) => e);
}
