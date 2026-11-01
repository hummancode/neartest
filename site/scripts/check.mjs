// Post-build checks on site/dist. No dependencies; run with `npm run check` after `npm run build`.
// Fails (exit 1) on: broken internal links/anchors, missing <title>/lang, missing disclaimer,
// missing sample banner while data is sample, or unexpected third-party scripts.
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, relative, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");
const ALLOWED_SCRIPT_HOSTS = ["static.cloudflareinsights.com"];
const errors = [];

function walk(dir) {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}

const pages = walk(dist).filter((p) => p.endsWith(".html"));
const html = Object.fromEntries(pages.map((p) => [p, readFileSync(p, "utf8")]));
const ids = (s) => new Set([...s.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]));

function resolvePage(urlPath) {
  const clean = urlPath.replace(/\/$/, "");
  const candidates = [join(dist, clean, "index.html"), join(dist, clean), join(dist, `${clean}.html`)];
  return candidates.find((c) => existsSync(c) && statSync(c).isFile());
}

const sample = JSON.parse(readFileSync(join(root, "data", "reel_tablo.json"), "utf8")).sample;

for (const [file, s] of Object.entries(html)) {
  const name = relative(dist, file);
  if (!/<html lang="tr"/.test(s)) errors.push(`${name}: <html lang="tr"> yok`);
  if (!/<title>[^<]+<\/title>/.test(s)) errors.push(`${name}: <title> yok`);
  if (!s.includes("Yatırım tavsiyesi değildir")) errors.push(`${name}: "Yatırım tavsiyesi değildir" yok`);

  for (const [, href] of s.matchAll(/\s(?:href|src)="([^"]+)"/g)) {
    if (/^(https?:|mailto:|data:)/.test(href)) {
      continue;
    }
    if (href.startsWith("#")) {
      if (href.length > 1 && !ids(s).has(href.slice(1))) errors.push(`${name}: çapa bulunamadı ${href}`);
      continue;
    }
    const [path, anchor] = href.split("#");
    const target = resolvePage(path);
    if (!target) {
      errors.push(`${name}: kırık bağlantı ${href}`);
      continue;
    }
    if (anchor && target.endsWith(".html") && !ids(html[target] ?? readFileSync(target, "utf8")).has(anchor)) {
      errors.push(`${name}: çapa bulunamadı ${href}`);
    }
  }

  for (const [, src] of s.matchAll(/<script[^>]*\ssrc="(https?:[^"]+)"/g)) {
    const host = new URL(src).host;
    if (!ALLOWED_SCRIPT_HOSTS.includes(host)) errors.push(`${name}: izin verilmeyen dış script ${src}`);
  }
}

const index = html[join(dist, "index.html")];
if (sample && !index.includes("ÖRNEK VERİ")) errors.push("index.html: veri örnek ama ÖRNEK VERİ bandı yok");
if (!sample && index.includes("ÖRNEK VERİ — gerçek değildir")) errors.push("index.html: veri gerçek ama örnek bandı görünüyor");

if (errors.length) {
  console.error(`✗ ${errors.length} sorun:\n` + errors.map((e) => `  - ${e}`).join("\n"));
  process.exit(1);
}
console.log(`✓ ${pages.length} sayfa kontrol edildi (bağlantılar, çapalar, başlık, uyarı, dış script).`);
