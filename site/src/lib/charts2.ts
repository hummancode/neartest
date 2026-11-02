// Part-to-whole and comparison charts: donut, treemap, 100 % stacked bars, scatter, Lorenz curve.
// Plain SVG, no dependencies. Labels via textContent. Colors are CSS custom properties.
// Display only: shares/positions are derived from the values handed in; no financial calculation.

const SVG = "http://www.w3.org/2000/svg";
export const CAT = ["var(--cat-1)", "var(--cat-2)", "var(--cat-3)", "var(--cat-4)", "var(--cat-5)", "var(--cat-6)"];
export const OTHER = "var(--cat-other)";
const pct = (x: number, d = 1) => `%${new Intl.NumberFormat("tr-TR", { maximumFractionDigits: d }).format(100 * x)}`;

function el<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number>, parent?: Element) {
  const n = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v));
  parent?.appendChild(n);
  return n;
}
export function tipBox(root: HTMLElement) {
  root.style.position = "relative";
  const tip = document.createElement("div");
  tip.className = "chart-tip";
  tip.hidden = true;
  root.appendChild(tip);
  return {
    show(lines: string[], x: number, y: number) {
      tip.replaceChildren(...lines.map((l, i) => { const d = document.createElement(i ? "div" : "strong"); d.textContent = l; return d; }));
      tip.hidden = false;
      const w = root.clientWidth;
      tip.style.left = `${Math.max(0, Math.min(w - tip.offsetWidth, x + 12))}px`;
      tip.style.top = `${Math.max(0, y - tip.offsetHeight - 8)}px`;
    },
    hide() { tip.hidden = true; },
  };
}
export const localXY = (root: HTMLElement, ev: PointerEvent) => { const r = root.getBoundingClientRect(); return [ev.clientX - r.left, ev.clientY - r.top]; };

export interface Part { name: string; value: number }

/** Top (max-1) parts plus "Diğer" for the rest, keeping order by size. */
export function foldParts(items: Part[], max = 6): Part[] {
  const s = [...items].filter((x) => x.value > 0).sort((a, b) => b.value - a.value);
  if (s.length <= max) return s;
  const head = s.slice(0, max - 1);
  return [...head, { name: "Diğer", value: s.slice(max - 1).reduce((a, x) => a + x.value, 0) }];
}

export function renderDonut(root: HTMLElement, items: Part[], opts: { format: (v: number) => string; size?: number; legend?: boolean; legendValues?: boolean; label?: string }) {
  root.replaceChildren();
  const parts = foldParts(items);
  const total = parts.reduce((a, x) => a + x.value, 0);
  const size = opts.size ?? 220, r = size / 2 - 4, r0 = r * 0.58, cx = size / 2, cy = size / 2;
  const wrap = document.createElement("div");
  wrap.className = "donut-wrap";
  root.appendChild(wrap);
  const svg = el("svg", { width: size, height: size, viewBox: `0 0 ${size} ${size}`, role: "img" }, wrap);
  svg.setAttribute("aria-label", `${opts.label ?? "Dağılım"}: ` + parts.map((p) => `${p.name} ${pct(p.value / total)}`).join(", "));
  const tip = tipBox(root);
  let a0 = -Math.PI / 2;
  parts.forEach((p, k) => {
    const frac = p.value / total, a1 = a0 + frac * 2 * Math.PI;
    const large = a1 - a0 > Math.PI ? 1 : 0;
    const pt = (a: number, rr: number) => `${cx + rr * Math.cos(a)},${cy + rr * Math.sin(a)}`;
    const d = frac >= 0.9999
      ? `M${cx - r},${cy}a${r},${r} 0 1,0 ${2 * r},0a${r},${r} 0 1,0 ${-2 * r},0M${cx - r0},${cy}a${r0},${r0} 0 1,1 ${2 * r0},0a${r0},${r0} 0 1,1 ${-2 * r0},0`
      : `M${pt(a0, r)}A${r},${r} 0 ${large} 1 ${pt(a1, r)}L${pt(a1, r0)}A${r0},${r0} 0 ${large} 0 ${pt(a0, r0)}Z`;
    const color = p.name === "Diğer" ? OTHER : CAT[k % CAT.length];
    const path = el("path", { d, fill: color, stroke: "var(--surface)", "stroke-width": 2, tabindex: 0, class: "slice" }, svg);
    path.setAttribute("aria-label", `${p.name}: ${opts.format(p.value)}, ${pct(frac)}`);
    const show = (ev?: PointerEvent) => {
      const [x, y] = ev ? localXY(root, ev) : [cx, cy];
      tip.show([p.name, `${opts.format(p.value)} · ${pct(frac)}`], x, y);
    };
    path.addEventListener("pointermove", show);
    path.addEventListener("focus", () => show());
    path.addEventListener("pointerleave", () => tip.hide());
    path.addEventListener("blur", () => tip.hide());
    if (frac >= 0.06) {                                   // direct label where the slice is big enough
      const am = (a0 + a1) / 2, rm = (r + r0) / 2;
      const t = el("text", { x: cx + rm * Math.cos(am), y: cy + rm * Math.sin(am) + 4, "text-anchor": "middle", class: "slice-label" }, svg);
      t.textContent = pct(frac, 0);
    }
    a0 = a1;
  });
  const center = el("text", { x: cx, y: cy + 5, "text-anchor": "middle", class: "donut-center" }, svg);
  center.textContent = opts.format(total);
  if (opts.legend !== false) {
    const ul = document.createElement("ul");
    ul.className = "donut-legend";
    parts.forEach((p, k) => {
      const li = document.createElement("li");
      const sw = document.createElement("span"); sw.className = "sw"; sw.style.background = p.name === "Diğer" ? OTHER : CAT[k % CAT.length];
      const nm = document.createElement("span"); nm.className = "lg-name"; nm.textContent = p.name;
      const v = document.createElement("span"); v.className = "lg-val";
      v.textContent = opts.legendValues === false ? pct(p.value / total) : `${pct(p.value / total)} · ${opts.format(p.value)}`;
      li.append(sw, nm, v);
      ul.appendChild(li);
    });
    wrap.appendChild(ul);
  }
}

/** Squarified treemap layout (Bruls, Huizing & van Wijk 2000). Returns rectangles in input order of the sorted list. */
export function squarify(values: number[], x: number, y: number, w: number, h: number): { x: number; y: number; w: number; h: number }[] {
  const total = values.reduce((a, b) => a + b, 0);
  if (!(total > 0) || w <= 0 || h <= 0) return values.map(() => ({ x, y, w: 0, h: 0 }));
  const scale = (w * h) / total;
  const areas = values.map((v) => v * scale);
  const out: { x: number; y: number; w: number; h: number }[] = [];
  let i = 0, X = x, Y = y, W = w, H = h;
  const worst = (row: number[], side: number) => {
    const s = row.reduce((a, b) => a + b, 0), mx = Math.max(...row), mn = Math.min(...row);
    return Math.max((side * side * mx) / (s * s), (s * s) / (side * side * mn));
  };
  while (i < areas.length) {
    const side = Math.min(W, H);
    const row = [areas[i]];
    let j = i + 1;
    while (j < areas.length && worst([...row, areas[j]], side) <= worst(row, side)) { row.push(areas[j]); j++; }
    const s = row.reduce((a, b) => a + b, 0);
    if (W >= H) {                      // lay the row out as a column on the left
      const cw = s / H;
      let yy = Y;
      for (const a of row) { out.push({ x: X, y: yy, w: cw, h: a / cw }); yy += a / cw; }
      X += cw; W -= cw;
    } else {                           // lay the row out along the top
      const rh = s / W;
      let xx = X;
      for (const a of row) { out.push({ x: xx, y: Y, w: a / rh, h: rh }); xx += a / rh; }
      Y += rh; H -= rh;
    }
    i = j;
  }
  return out;
}

export function renderTreemap(root: HTMLElement, items: Part[], opts: { format: (v: number) => string; height?: number; label?: string }) {
  root.replaceChildren();
  root.classList.add("chart");
  const s = [...items].filter((x) => x.value > 0).sort((a, b) => b.value - a.value);
  const total = s.reduce((a, x) => a + x.value, 0);
  const W = Math.max(240, root.clientWidth), H = opts.height ?? (W < 520 ? 260 : 320);
  const svg = el("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: "img" }, root);
  svg.setAttribute("aria-label", `${opts.label ?? "Dağılım"}: ` + s.map((p) => `${p.name} ${pct(p.value / total)}`).join(", "));
  const tip = tipBox(root);
  const rects = squarify(s.map((x) => x.value), 0, 0, W, H);
  s.forEach((p, k) => {
    const r = rects[k];
    // one hue; larger parts darker so rank reads without a rainbow
    const t = Math.min(1, (p.value / s[0].value) ** 0.5);
    const g = el("g", { tabindex: 0, class: "tm-cell" }, svg);
    g.setAttribute("aria-label", `${p.name}: ${opts.format(p.value)}, ${pct(p.value / total)}`);
    el("rect", { x: r.x + 1, y: r.y + 1, width: Math.max(0, r.w - 2), height: Math.max(0, r.h - 2), rx: 3,
      fill: `color-mix(in srgb, var(--cat-1) ${Math.round(35 + 65 * t)}%, var(--surface))` }, g);
    if (r.w > 70 && r.h > 34) {
      const name = el("text", { x: r.x + 8, y: r.y + 18, class: "tm-name" }, g);
      const maxChars = Math.floor((r.w - 14) / 6.6);
      name.textContent = p.name.length > maxChars ? p.name.slice(0, Math.max(3, maxChars - 1)) + "…" : p.name;
      const val = el("text", { x: r.x + 8, y: r.y + 34, class: "tm-val" }, g);
      val.textContent = pct(p.value / total);
      if (t > 0.55) { name.classList.add("on-dark"); val.classList.add("on-dark"); }
    }
    const show = (ev?: PointerEvent) => {
      const [x, y] = ev ? localXY(root, ev) : [r.x + r.w / 2, r.y + 10];
      tip.show([p.name, `${opts.format(p.value)} · ${pct(p.value / total)}`], x, y);
    };
    g.addEventListener("pointermove", show);
    g.addEventListener("focus", () => show());
    g.addEventListener("pointerleave", () => tip.hide());
    g.addEventListener("blur", () => tip.hide());
  });
}

/** 100 % stacked horizontal bars: one row per whole, same category colors across rows. */
export function renderStacked100(root: HTMLElement, rows: { label: string; parts: Record<string, number>; emphasis?: boolean }[], categories: string[]) {
  root.replaceChildren();
  const tip = tipBox(root);
  const color = (c: string) => (c === "Diğer" ? OTHER : CAT[categories.indexOf(c) % CAT.length]);
  const legend = document.createElement("ul");
  legend.className = "donut-legend inline";
  for (const c of categories) {
    const li = document.createElement("li");
    const sw = document.createElement("span"); sw.className = "sw"; sw.style.background = color(c);
    const nm = document.createElement("span"); nm.textContent = c;
    li.append(sw, nm); legend.appendChild(li);
  }
  root.appendChild(legend);
  for (const row of rows) {
    const tot = Object.values(row.parts).reduce((a, b) => a + b, 0);
    const line = document.createElement("div");
    line.className = "st-row" + (row.emphasis ? " emph" : "");
    const lab = document.createElement("span"); lab.className = "st-label"; lab.textContent = row.label;
    const bar = document.createElement("span"); bar.className = "st-bar";
    for (const c of categories) {
      const v = row.parts[c] ?? 0;
      if (!(v > 0) || !(tot > 0)) continue;
      const seg = document.createElement("span");
      seg.className = "st-seg";
      seg.style.width = `${(100 * v) / tot}%`;
      seg.style.background = color(c);
      seg.tabIndex = 0;
      seg.setAttribute("aria-label", `${row.label}, ${c}: ${pct(v / tot)}`);
      seg.dataset.label = pct(v / tot, 0);
      const show = (ev?: PointerEvent) => {
        const r = root.getBoundingClientRect(), sr = seg.getBoundingClientRect();
        tip.show([`${row.label} — ${c}`, pct(v / tot)], ev ? ev.clientX - r.left : sr.left - r.left + sr.width / 2, sr.top - r.top);
      };
      seg.addEventListener("pointermove", show);
      seg.addEventListener("focus", () => show());
      seg.addEventListener("pointerleave", () => tip.hide());
      seg.addEventListener("blur", () => tip.hide());
      bar.appendChild(seg);
    }
    line.append(lab, bar);
    root.appendChild(line);
  }
  // Print a share only where it actually fits (measured after layout).
  requestAnimationFrame(() => root.querySelectorAll<HTMLElement>(".st-seg").forEach((seg) => {
    seg.textContent = seg.offsetWidth >= 34 ? seg.dataset.label ?? "" : "";
  }));
}

export interface ScatterPoint { id: number; label: string; x: number; y: number }

/** Scatter of provinces; the selected one is emphasised, the rest stay neutral. */
export function renderScatter(root: HTMLElement, pts: ScatterPoint[], opts: {
  xLabel: string; yLabel: string; fx: (v: number) => string; fy: (v: number) => string;
  logX?: boolean; logY?: boolean; selected?: number | null; onSelect?: (id: number) => void;
}) {
  root.replaceChildren();
  root.classList.add("chart");
  const W = Math.max(260, root.clientWidth), H = W < 520 ? 300 : 380;
  const M = { l: 58, r: 14, t: 10, b: 44 };
  const svg = el("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: "img" }, root);
  svg.setAttribute("aria-label", `${opts.yLabel} ile ${opts.xLabel}: ${pts.length} il`);
  const tip = tipBox(root);
  const usable = pts.filter((p) => (!opts.logX || p.x > 0) && (!opts.logY || p.y > 0));
  const tx = (v: number) => (opts.logX ? Math.log10(v) : v), ty = (v: number) => (opts.logY ? Math.log10(v) : v);
  const xs = usable.map((p) => tx(p.x)), ys = usable.map((p) => ty(p.y));
  const [x0, x1] = [Math.min(...xs), Math.max(...xs)], [y0, y1] = [Math.min(...ys), Math.max(...ys)];
  const px = (v: number) => M.l + ((tx(v) - x0) / (x1 - x0 || 1)) * (W - M.l - M.r);
  const py = (v: number) => H - M.b - ((ty(v) - y0) / (y1 - y0 || 1)) * (H - M.t - M.b);
  const ticks = (lo: number, hi: number, log: boolean) => {
    const n = 4, out: number[] = [];
    for (let k = 0; k <= n; k++) { const t = lo + ((hi - lo) * k) / n; out.push(log ? 10 ** t : t); }
    return out;
  };
  const grid = el("g", { class: "grid" }, svg);
  for (const v of ticks(y0, y1, !!opts.logY)) {
    const yy = py(v);
    el("line", { x1: M.l, x2: W - M.r, y1: yy, y2: yy }, grid);
    const t = el("text", { x: M.l - 6, y: yy + 4, "text-anchor": "end", class: "tick" }, grid); t.textContent = opts.fy(v);
  }
  ticks(x0, x1, !!opts.logX).forEach((v, k, arr) => {
    const xx = px(v);
    const anchor = k === 0 ? "start" : k === arr.length - 1 ? "end" : "middle";
    const t = el("text", { x: xx, y: H - M.b + 16, "text-anchor": anchor, class: "tick" }, grid); t.textContent = opts.fx(v);
  });
  const xl = el("text", { x: (M.l + W - M.r) / 2, y: H - 6, "text-anchor": "middle", class: "axis-label" }, svg); xl.textContent = opts.xLabel + (opts.logX ? " (log)" : "");
  const yl = el("text", { x: 12, y: (M.t + H - M.b) / 2, "text-anchor": "middle", class: "axis-label", transform: `rotate(-90 12 ${(M.t + H - M.b) / 2})` }, svg); yl.textContent = opts.yLabel + (opts.logY ? " (log)" : "");
  const sorted = [...usable].sort((a, b) => (a.id === opts.selected ? 1 : 0) - (b.id === opts.selected ? 1 : 0));
  for (const p of sorted) {
    const sel = p.id === opts.selected;
    const c = el("circle", { cx: px(p.x), cy: py(p.y), r: sel ? 7 : 5, class: sel ? "pt sel" : "pt", tabindex: 0 }, svg);
    c.setAttribute("aria-label", `${p.label}: ${opts.fx(p.x)}, ${opts.fy(p.y)}`);
    // invisible larger hit target
    const hit = el("circle", { cx: px(p.x), cy: py(p.y), r: 12, fill: "transparent" }, svg);
    const show = () => tip.show([p.label, `${opts.xLabel}: ${opts.fx(p.x)}`, `${opts.yLabel}: ${opts.fy(p.y)}`], px(p.x), py(p.y));
    for (const n of [c, hit]) {
      n.addEventListener("pointerenter", show);
      n.addEventListener("pointerleave", () => tip.hide());
      n.addEventListener("click", () => opts.onSelect?.(p.id));
    }
    c.addEventListener("focus", show);
    c.addEventListener("blur", () => tip.hide());
    c.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); opts.onSelect?.(p.id); } });
    if (sel) {
      const right = px(p.x) > W - 110;
      const t = el("text", { x: px(p.x) + (right ? -10 : 10), y: py(p.y) - 8, class: "pt-label", "text-anchor": right ? "end" : "start" }, svg);
      t.textContent = p.label;
    }
  }
}

/** Lorenz curves (share of population -> share of total), with the equality diagonal. */
export function renderLorenz(root: HTMLElement, curves: { label: string; color: string; f: (p: number) => number }[]) {
  root.replaceChildren();
  root.classList.add("chart");
  const S = Math.min(360, Math.max(240, root.clientWidth || 300)), M = 40;
  const svg = el("svg", { width: S, height: S, viewBox: `0 0 ${S} ${S}`, role: "img" }, root);
  svg.setAttribute("aria-label", "Lorenz eğrisi: " + curves.map((c) => `${c.label}, en yoksul yarının payı ${pct(c.f(0.5))}`).join("; "));
  const x = (p: number) => M + p * (S - 2 * M), y = (q: number) => S - M - q * (S - 2 * M);
  const grid = el("g", { class: "grid" }, svg);
  for (const v of [0, 0.25, 0.5, 0.75, 1]) {
    el("line", { x1: x(0), x2: x(1), y1: y(v), y2: y(v) }, grid);
    const t1 = el("text", { x: x(0) - 6, y: y(v) + 4, "text-anchor": "end", class: "tick" }, grid); t1.textContent = pct(v, 0);
    const t2 = el("text", { x: x(v), y: S - M + 16, "text-anchor": "middle", class: "tick" }, grid); t2.textContent = pct(v, 0);
  }
  el("line", { x1: x(0), y1: y(0), x2: x(1), y2: y(1), class: "base" }, grid);
  const eq = el("text", { x: x(0.45), y: y(0.45) - 6, class: "tick", transform: `rotate(-45 ${x(0.45)} ${y(0.45) - 6})`, "text-anchor": "middle" }, svg); eq.textContent = "tam eşitlik";
  // legend in the empty top-left corner instead of labels on crowded curves
  curves.forEach((c, k) => {
    const n = 60, d = Array.from({ length: n + 1 }, (_, i) => { const p = i / n; return `${i ? "L" : "M"}${x(p).toFixed(1)},${y(c.f(p)).toFixed(1)}`; }).join("");
    el("path", { d, fill: "none", stroke: c.color, "stroke-width": 2.2 }, svg);
    const ly = M + 8 + 18 * k;
    el("line", { x1: x(0) + 6, x2: x(0) + 22, y1: ly, y2: ly, stroke: c.color, "stroke-width": 3 }, svg);
    const lbl = el("text", { x: x(0) + 28, y: ly + 4, class: "end-label" }, svg); lbl.textContent = c.label;
  });
  const xl = el("text", { x: S / 2, y: S - 4, "text-anchor": "middle", class: "axis-label" }, svg); xl.textContent = "hanelerin payı (en yoksuldan)";
  const yl = el("text", { x: 10, y: S / 2, "text-anchor": "middle", class: "axis-label", transform: `rotate(-90 10 ${S / 2})` }, svg); yl.textContent = "toplamın payı";
}
