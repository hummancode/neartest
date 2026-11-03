// sitemap.xml from the known routes. Needs SITE_URL (config.ts); empty sitemap otherwise.
import { SITE_URL } from "../config.ts";
import { paths } from "../lib/paths.ts";
import { provinces } from "../lib/provinces.ts";
import { provinceUrl } from "../lib/slug.ts";

const ROUTES = ["/", "/turkiye/", "/ekonomik-nabiz/", "/iller/", "/nufus/", "/karsilastir/", "/mevzuat/", "/kart/", "/yapilandirma/", "/mevduat/", "/birikim/", "/ulkeler/", "/big-mac/", "/uzun-donem/", "/kredi/", "/kredi-karsilastir/", "/erken-kapama/", "/taksit/", "/maas/", "/olaylar/", "/borsa/", "/emtia/", "/portfoy/", "/varliklarim/", "/vergi/", "/vergi/maas/", "/vergi/kira/", "/vergi/deger-artis/", "/vergi/emlak/", "/bes/", "/makro/", "/iliskiler/", "/grafik/", "/konut/", "/konut-fiyatlari/", "/nominal-illuzyon/", "/kisisel-enflasyon/", "/reel-faiz/", "/metodoloji/", "/veri/", "/bulten/", "/yasal-uyari/", "/gizlilik/"];

export function GET() {
  const urls = SITE_URL
    ? [...ROUTES, ...Object.keys(paths.assets).map((id) => `/varlik/${id}/`), ...provinces.provinces.map((p) => `${provinceUrl(p.plaka, p.name)}/`)].map((r) => `  <url><loc>${SITE_URL}${r}</loc></url>`)
    : [];
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join("\n")}\n</urlset>\n`;
  return new Response(body, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
}
