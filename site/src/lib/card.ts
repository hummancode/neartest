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

const INK = "#f2f2f2";
const MUTED = "#a3a3a3";
const RED = "#c8102e";
const MAX_W = W - 2 * PAD;

interface Frame { c: HTMLCanvasElement; ctx: CanvasRenderingContext2D; y: number }

/** Dark canvas, optional red sample band and a small kicker line. */
async function frame(sample: boolean, kicker: string): Promise<Frame> {
  await ensureFonts();
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const ctx = c.getContext("2d")!;
  ctx.fillStyle = "#111214";
  ctx.fillRect(0, 0, W, H);
  ctx.textBaseline = "alphabetic";
  let y = 0;
  if (sample) {
    ctx.fillStyle = RED;
    ctx.fillRect(0, 0, W, 96);
    ctx.fillStyle = "#fff";
    ctx.font = `700 40px ${BODY}`;
    ctx.textAlign = "center";
    ctx.fillText("ÖRNEK VERİ — gerçek değildir", W / 2, 62);
    ctx.textAlign = "left";
    y = 96;
  }
  y += 100;
  ctx.fillStyle = MUTED;
  ctx.font = `600 34px ${BODY}`;
  ctx.fillText(up(kicker), PAD, y);
  return { c, ctx, y };
}

/** Bottom strip: sources, data end, disclaimer, site name. Returns the strip's top y. */
function footer(ctx: CanvasRenderingContext2D, sample: boolean, sources: string[], endLabel: string, disclaimer: string, siteName: string): number {
  const stripH = 200;
  const top = H - stripH;
  ctx.fillStyle = "#1c1d21";
  ctx.fillRect(0, top, W, stripH);
  ctx.fillStyle = MUTED;
  ctx.font = `400 24px ${BODY}`;
  let sy = top + 48;
  for (const line of wrap(ctx, `Kaynak: ${sources.join(" · ")}`, MAX_W).slice(0, 3)) {
    ctx.fillText(line, PAD, sy);
    sy += 32;
  }
  ctx.font = `400 34px ${HEAD}`;
  const nameW = ctx.measureText(up(siteName)).width;
  ctx.textAlign = "right";
  ctx.fillStyle = INK;
  ctx.fillText(up(siteName), W - PAD, H - 44);
  ctx.textAlign = "left";
  const foot = `Son veri: ${endLabel} (aylık ortalama) · ${disclaimer}`;
  const fs = fitFont(ctx, foot, BODY, 26, MAX_W - nameW - 32, "600");
  ctx.font = `600 ${fs}px ${BODY}`;
  ctx.fillText(foot, PAD, H - 44);
  if (sample) {
    ctx.fillStyle = RED;
    ctx.fillRect(0, top - 8, W, 8);
  }
  return top;
}

function bigLine(ctx: CanvasRenderingContext2D, text: string, y: number, max: number, color = INK): number {
  const size = fitFont(ctx, text, HEAD, max, MAX_W);
  const ny = y + size * 0.98;
  ctx.fillStyle = color;
  ctx.font = `400 ${size}px ${HEAD}`;
  ctx.fillText(text, PAD, ny);
  return ny;
}

function rule(ctx: CanvasRenderingContext2D, y: number) {
  ctx.strokeStyle = "#2c2d31";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(PAD, y);
  ctx.lineTo(W - PAD, y);
  ctx.stroke();
}

export async function drawCard(d: CardData): Promise<HTMLCanvasElement> {
  const { c, ctx, y: y0 } = await frame(d.sample, "Nominal illüzyon");
  let y = y0 + 10;
  y = bigLine(ctx, up(d.thenLabel), y, 100);
  y = bigLine(ctx, up(d.amount), y, d.rows.length > 3 ? 170 : 220);

  y += d.rows.length > 3 ? 64 : 80;
  ctx.fillStyle = MUTED;
  ctx.font = `400 38px ${BODY}`;
  ctx.fillText(`bugün (${d.endLabel}) şuna denk geliyor:`, PAD, y);

  y += 40;
  const many = d.rows.length > 3;
  for (const row of d.rows) {
    rule(ctx, y + 20);
    y += many ? 70 : 82;
    ctx.fillStyle = MUTED;
    ctx.font = `600 ${many ? 30 : 34}px ${BODY}`;
    ctx.fillText(row.label, PAD, y);
    y = bigLine(ctx, up(row.value), y, many ? 84 : 110);
  }
  footer(ctx, d.sample, d.sources, d.endLabel, d.disclaimer, d.siteName);
  return c;
}

export interface PersonalCardData {
  siteName: string;
  disclaimer: string;
  sample: boolean;
  period: string;          // "Eylül 2025 → Eylül 2026"
  endLabel: string;
  personal: string;        // "%38,2"
  official: string;        // "%33,0"
  diff: string;            // "+5,2 puan"
  topGroups: { label: string; value: string }[];
  sources: string[];
}

export async function drawPersonalCard(d: PersonalCardData): Promise<HTMLCanvasElement> {
  const { c, ctx, y: y0 } = await frame(d.sample, "Kişisel enflasyonum · tahmini");
  let y = y0 + 20;
  ctx.fillStyle = MUTED;
  ctx.font = `400 34px ${BODY}`;
  ctx.fillText(`Son 12 ay: ${d.period}`, PAD, y + 20);
  y += 30;
  y = bigLine(ctx, d.personal, y, 300);

  y += 70;
  ctx.fillStyle = MUTED;
  ctx.font = `600 34px ${BODY}`;
  ctx.fillText("Resmi TÜFE (aynı dönem)", PAD, y);
  y = bigLine(ctx, d.official, y, 120);
  y += 56;
  ctx.fillStyle = INK;
  ctx.font = `600 38px ${BODY}`;
  ctx.fillText(`Fark: ${d.diff}`, PAD, y);

  y += 40;
  rule(ctx, y);
  y += 56;
  ctx.fillStyle = MUTED;
  ctx.font = `600 30px ${BODY}`;
  ctx.fillText("En çok katkı yapan harcamalarım", PAD, y);
  ctx.font = `400 32px ${BODY}`;
  for (const g of d.topGroups.slice(0, 3)) {
    y += 52;
    ctx.fillStyle = INK;
    ctx.fillText(g.label, PAD, y);
    ctx.textAlign = "right";
    ctx.fillText(g.value, W - PAD, y);
    ctx.textAlign = "left";
  }

  y += 64;
  ctx.fillStyle = MUTED;
  ctx.font = `400 26px ${BODY}`;
  ctx.fillText("Bu kişisel bir hesaptır; resmi enflasyon değildir.", PAD, y);
  footer(ctx, d.sample, d.sources, d.endLabel, d.disclaimer, d.siteName);
  return c;
}

/** Trigger a PNG download of a canvas. */
export async function downloadCanvas(canvas: HTMLCanvasElement, filename: string): Promise<void> {
  const blob: Blob | null = await new Promise((r) => canvas.toBlob(r, "image/png"));
  if (!blob) throw new Error("PNG üretilemedi");
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
