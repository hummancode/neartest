// Population views: diverging classes (shrinking ← 0 → growing), ranked bars around zero,
// district choropleth. Display only — growth rates are computed in the Python pipeline.
import { tipBox, localXY } from "./charts2";

const SVG = "http://www.w3.org/2000/svg";

export interface District {
  name: string; points: [string, number][]; year: string; pop: number; share: number | null;
  g1?: number; g5?: number; g10?: number; c10?: number; area_km2?: number; density?: number;
}
export interface DistrictShape { name: string; d: string; area_km2: number; cx: number; cy: number }
export interface ProvinceShapes { bbox: number[]; districts: DistrictShape[] }

/** Fixed class edges for annual growth in % — the same on every map so colors are comparable. */
export const GROWTH_EDGES = [0.1, 0.5, 1.5];
export const SIGNED = new Set(["population_growth_1y", "population_cagr_5y", "population_cagr_10y", "population_change_10y"]);

/** -3..3: sign gives direction, magnitude the class; |v| below the first edge is neutral (0). */
export function divClass(v: number, edges: number[] = GROWTH_EDGES): number {
  const k = edges.filter((e) => Math.abs(v) >= e).length;
  return v < 0 ? -k : k;
}
export const divCss = (k: number) => (k < 0 ? `dn${-k}` : k > 0 ? `dp${k}` : "d0");

/** Edges for a signed absolute quantity (e.g. people): terciles of |v| among the nonzero values. */
export function absEdges(xs: number[]): number[] {
  const s = xs.map(Math.abs).filter((x) => x > 0).sort((a, b) => a - b);
  if (!s.length) return [1, 2, 3];
  const q = (f: number) => s[Math.min(s.length - 1, Math.floor(f * s.length))];
  return [q(0.1), q(0.45), q(0.8)];
}

const nf = (d: number) => new Intl.NumberFormat("tr-TR", { maximumFractionDigits: d, minimumFractionDigits: d });
export const fmtPct = (v: number, d = 1) => {
  const r = Math.round(v * 10 ** d) / 10 ** d;          // no "−%0,0"
  return `${r > 0 ? "+" : r < 0 ? "−" : ""}%${nf(d).format(Math.abs(r))}`;
};
export const fmtInt = (v: number) => new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 }).format(v);
export const fmtSigned = (v: number) => { const r = Math.round(v); return `${r > 0 ? "+" : r < 0 ? "−" : ""}${fmtInt(Math.abs(r))}`; };

export function legendItems(edges: number[], fmt: (v: number) => string): { cls: string; label: string }[] {
  const [a, b, c] = edges;
  return [
    { cls: "dn3", label: `≤ ${fmt(-c)}` }, { cls: "dn2", label: `${fmt(-c)} … ${fmt(-b)}` }, { cls: "dn1", label: `${fmt(-b)} … ${fmt(-a)}` },
    { cls: "d0", label: `yaklaşık sabit (±${fmt(a).replace(/^[+−]/, "")})` },
    { cls: "dp1", label: `${fmt(a)} … ${fmt(b)}` }, { cls: "dp2", label: `${fmt(b)} … ${fmt(c)}` }, { cls: "dp3", label: `≥ ${fmt(c)}` },
  ];
}
export function renderLegend(root: HTMLElement, edges: number[], fmt: (v: number) => string) {
  root.replaceChildren(...legendItems(edges, fmt).map(({ cls, label }) => {
    const it = document.createElement("span"); it.className = "lg-item";
    const sw = document.createElement("span"); sw.className = `sw ${cls}`;
    const t = document.createElement("span"); t.textContent = label;
    it.append(sw, t); return it;
  }));
}

/** Ranked horizontal bars growing left (negative) or right (positive) from a zero line. */
export function renderDivBars(root: HTMLElement, rows: { label: string; sub?: string; value: number; href?: string; emphasis?: boolean }[],
                              opts: { format: (v: number) => string; edges?: number[]; label: string }) {
  root.replaceChildren();
  const max = Math.max(...rows.map((r) => Math.abs(r.value)), 1e-9);
  const hasNeg = rows.some((r) => r.value < 0), hasPos = rows.some((r) => r.value > 0);
  const zero = hasNeg && hasPos ? 50 : hasNeg ? 100 : 0;
  const span = hasNeg && hasPos ? 50 : 100;
  const list = document.createElement("ol"); list.className = "dbars"; list.setAttribute("aria-label", opts.label);
  for (const r of rows) {
    const li = document.createElement("li");
    if (r.emphasis) li.className = "em";
    const name = document.createElement(r.href ? "a" : "span"); name.className = "db-name"; name.textContent = r.label;
    if (r.href) (name as HTMLAnchorElement).href = r.href;
    if (r.sub) { const s = document.createElement("small"); s.textContent = r.sub; name.appendChild(s); }
    const track = document.createElement("span"); track.className = "db-track";
    const bar = document.createElement("span"); bar.className = `db-bar ${divCss(divClass(r.value, opts.edges))}`;
    const w = (span * Math.abs(r.value)) / max;
    bar.style.width = `${w}%`;
    bar.style.left = `${r.value < 0 ? zero - w : zero}%`;
    if (hasNeg && hasPos) { const z = document.createElement("span"); z.className = "db-zero"; z.style.left = `${zero}%`; track.appendChild(z); }
    track.appendChild(bar);
    const val = document.createElement("span"); val.className = "db-val"; val.textContent = opts.format(r.value);
    li.append(name, track, val);
    list.appendChild(li);
  }
  root.appendChild(list);
}

/** District choropleth for one province (zoomed to its bounding box). */
export function renderDistrictMap(root: HTMLElement, g: ProvinceShapes | undefined, valueOf: (name: string) => number | null | undefined,
                                  opts: { edges: number[]; tip: (name: string) => string[]; onSelect?: (name: string) => void; selected?: string | null; label: string }) {
  root.replaceChildren();
  if (!g) return;
  const [x0, y0, x1, y1] = g.bbox, pad = (x1 - x0 + y1 - y0) * 0.02;
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("viewBox", `${x0 - pad} ${y0 - pad} ${x1 - x0 + 2 * pad} ${y1 - y0 + 2 * pad}`);
  svg.setAttribute("class", "dmap");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", opts.label);
  const tip = tipBox(root);
  for (const d of g.districts) {
    const v = valueOf(d.name);
    const path = document.createElementNS(SVG, "path");
    path.setAttribute("d", d.d);
    path.setAttribute("class", "dist " + (v == null ? "nodata" : divCss(divClass(v, opts.edges))) + (opts.selected === d.name ? " sel" : ""));
    path.setAttribute("tabindex", "0");
    path.setAttribute("aria-label", opts.tip(d.name).join(", "));
    path.addEventListener("pointermove", (ev) => { const [x, y] = localXY(root, ev as PointerEvent); tip.show(opts.tip(d.name), x, y); });
    path.addEventListener("pointerleave", () => tip.hide());
    path.addEventListener("focus", () => { const r = path.getBoundingClientRect(), o = root.getBoundingClientRect(); tip.show(opts.tip(d.name), r.left - o.left + r.width / 2, r.top - o.top); });
    path.addEventListener("blur", () => tip.hide());
    if (opts.onSelect) {
      path.addEventListener("click", () => opts.onSelect!(d.name));
      path.addEventListener("keydown", (ev) => { if ((ev as KeyboardEvent).key === "Enter") opts.onSelect!(d.name); });
    }
    svg.appendChild(path);
  }
  root.insertBefore(svg, root.firstChild);
}
