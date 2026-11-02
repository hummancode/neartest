// "İstanbul" -> "istanbul", "Kahramanmaraş" -> "kahramanmaras"; URL: /il/34-istanbul
export function slugify(s: string): string {
  return s.replace(/İ/g, "i").replace(/I/g, "ı").toLocaleLowerCase("tr-TR")
    .replace(/ç/g, "c").replace(/ğ/g, "g").replace(/ı/g, "i").replace(/ö/g, "o").replace(/ş/g, "s").replace(/ü/g, "u")
    .replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}
export const provinceUrl = (plaka: number, name: string) => `/il/${String(plaka).padStart(2, "0")}-${slugify(name)}`;
