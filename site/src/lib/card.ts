// Input parsing and the shareable PNG card (1200×1500) for the nominal illusion page.
// Drawing happens on a local <canvas>; nothing is uploaded anywhere.

/**
 * Parse a Turkish-formatted TL amount. Accepts "1.000", "1000", "2.500,50", "2500,5", "1 000".
 * Returns null for empty, non-numeric, non-positive or absurdly large input.
 */
export function parseAmount(input: string): number | null {
  let s = input.trim().replace(/\s|TL|₺/gi, "");
  if (s === "") return null;
  if (s.includes(",")) {
    // Comma is the decimal separator; dots are thousands separators.
    if ((s.match(/,/g) || []).length > 1) return null;
    s = s.replace(/\./g, "").replace(",", ".");
  } else if (/^\d{1,3}(\.\d{3})+$/.test(s)) {
    s = s.replace(/\./g, ""); // "1.000" / "1.000.000"
  }
  if (!/^\d+(\.\d+)?$/.test(s)) return null;
  const x = Number(s);
  if (!Number.isFinite(x) || x <= 0 || x > 1e15) return null;
  return x;
}

export interface CardData {
  siteName: string;
  disclaimer: string;
  sample: boolean;
  thenLabel: string;   // "Eylül 2016"
  endLabel: string;    // "Eylül 2026"
  amount: string;      // "1.000 TL"
  rows: { label: string; value: string }[];
  sources: string[];
}

const W = 1200;
const H = 1500;
const PAD = 80;
const HEAD = '"Anton", Impact, sans-serif';
const BODY = '"Inter", system-ui, sans-serif';

const up = (s: string) => s.toLocaleUpperCase("tr-TR");

/** Largest font size (<= max) at which `text` fits `maxWidth`. */
function fitFont(ctx: CanvasRenderingContext2D, text: string, family: string, max: number, maxWidth: number, weight = "400"): number {
  let size = max;
  while (size > 20) {
    ctx.font = `${weight} ${size}px ${family}`;
    if (ctx.measureText(text).width <= maxWidth) break;
    size -= 4;
  }
  return size;
}

function wrap(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let line = "";
  for (const w of words) {
    const test = line ? `${line} ${w}` : w;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = w;
    } else {
      line = test;
    }
  }
  if (line) lines.push(line);
  return lines;
}

async function ensureFonts() {
  if (!("fonts" in document)) return;
  const sample = "İŞĞÜÖÇışğüöç0123456789.,%";
  await Promise.all([
    document.fonts.load(`400 120px ${HEAD}`, sample),
    document.fonts.load(`400 32px ${BODY}`, sample),
    document.fonts.load(`600 32px ${BODY}`, sample),
    document.fonts.load(`700 32px ${BODY}`, sample),
  ]);
}

export async function drawCard(d: CardData): Promise<HTMLCanvasElement> {
  await ensureFonts();
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const ctx = c.getContext("2d")!;
  const ink = "#f2f2f2";
  const muted = "#a3a3a3";
  const red = "#c8102e";
  const maxW = W - 2 * PAD;

  ctx.fillStyle = "#111214";
  ctx.fillRect(0, 0, W, H);
  ctx.textBaseline = "alphabetic";

  let y = 0;
  if (d.sample) {
    ctx.fillStyle = red;
    ctx.fillRect(0, 0, W, 96);
    ctx.fillStyle = "#fff";
    ctx.font = `700 40px ${BODY}`;
    ctx.textAlign = "center";
    ctx.fillText("ÖRNEK VERİ — gerçek değildir", W / 2, 62);
    ctx.textAlign = "left";
    y = 96;
  }

  // Kicker
  y += 100;
  ctx.fillStyle = muted;
  ctx.font = `600 34px ${BODY}`;
  ctx.fillText(up("Nominal illüzyon"), PAD, y);

  // Headline: "<month year>" then the amount, big.
  y += 110;
  ctx.fillStyle = ink;
  let size = fitFont(ctx, up(d.thenLabel), HEAD, 100, maxW);
  ctx.font = `400 ${size}px ${HEAD}`;
  ctx.fillText(up(d.thenLabel), PAD, y);

  size = fitFont(ctx, up(d.amount), HEAD, 220, maxW);
  y += size * 0.98;
  ctx.font = `400 ${size}px ${HEAD}`;
  ctx.fillText(up(d.amount), PAD, y);

  y += 80;
  ctx.fillStyle = muted;
  ctx.font = `400 38px ${BODY}`;
  ctx.fillText(`bugün (${d.endLabel}) şuna denk geliyor:`, PAD, y);

  // Result rows
  y += 40;
  for (const row of d.rows) {
    ctx.strokeStyle = "#2c2d31";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(PAD, y + 20);
    ctx.lineTo(W - PAD, y + 20);
    ctx.stroke();

    y += 82;
    ctx.fillStyle = muted;
    ctx.font = `600 34px ${BODY}`;
    ctx.fillText(row.label, PAD, y);

    const vs = fitFont(ctx, up(row.value), HEAD, 110, maxW);
    y += vs * 0.98;
    ctx.fillStyle = ink;
    ctx.font = `400 ${vs}px ${HEAD}`;
    ctx.fillText(up(row.value), PAD, y);
  }

  // Bottom strip: sources, data end, disclaimer, site name.
  const stripH = 200;
  const top = H - stripH;
  ctx.fillStyle = "#1c1d21";
  ctx.fillRect(0, top, W, stripH);
  ctx.fillStyle = muted;
  ctx.font = `400 24px ${BODY}`;
  const srcLines = wrap(ctx, `Kaynak: ${d.sources.join(" · ")}`, maxW).slice(0, 3);
  let sy = top + 48;
  for (const line of srcLines) {
    ctx.fillText(line, PAD, sy);
    sy += 32;
  }
  ctx.font = `400 34px ${HEAD}`;
  const nameW = ctx.measureText(up(d.siteName)).width;
  ctx.textAlign = "right";
  ctx.fillStyle = ink;
  ctx.fillText(up(d.siteName), W - PAD, H - 44);
  ctx.textAlign = "left";
  const foot = `Son veri: ${d.endLabel} (aylık ortalama) · ${d.disclaimer}`;
  const fs = fitFont(ctx, foot, BODY, 26, maxW - nameW - 32, "600");
  ctx.font = `600 ${fs}px ${BODY}`;
  ctx.fillText(foot, PAD, H - 44);

  if (d.sample) {
    ctx.fillStyle = red;
    ctx.fillRect(0, top - 8, W, 8);
  }
  return c;
}
