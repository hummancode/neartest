// Small dependency-free line chart for the asset detail pages.
// Draws precomputed index paths (100 = window start); it does not calculate returns.
// Hover / keyboard crosshair with one tooltip listing every series. Labels via textContent only.

export interface ChartSeries {
  key: string;
  label: string;
  color: string;      // CSS color, usually var(--series-n)
  values: number[];
}
export interface ChartData {
  months: string[];   // "YYYY-MM"
  series: ChartSeries[];
}

const SVG = "http://www.w3.org/2000/svg";
const MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
const MONTHS_SHORT = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];
const fmt1 = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 1, minimumFractionDigits: 1 });
const fmt0 = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
const pctFmt = new Intl.NumberFormat("tr-TR", { style: "percent", maximumFractionDigits: 1, minimumFractionDigits: 1, signDisplay: "exceptZero" });

function el<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number>, parent?: Element) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, String(v));
  parent?.appendChild(node);
  return node;
}

function niceStep(raw: number): number {
  const p = 10 ** Math.floor(Math.log10(raw));
  const f = raw / p;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
}

/** Y ticks; log scale when the data spans more than 2.5x. */
export function yScale(min: number, max: number, allowLog = true) {
  const log = allowLog && min > 0 && max / min > 2.5;
  let ticks: number[] = [];
  if (log) {
    for (const mult of [[1, 2, 5], [1, 1.5, 2, 3, 5, 7]]) {
      ticks = [];
      for (let k = Math.floor(Math.log10(min)) - 1; k <= Math.ceil(Math.log10(max)) + 1; k++) {
        for (const m of mult) {
          const v = m * 10 ** k;
          if (v >= min * 0.98 && v <= max * 1.02) ticks.push(v);
        }
      }
      if (ticks.length >= 3) break;
    }
  } else {
    const step = niceStep((max - min) / 4 || 1);
    for (let v = Math.ceil(min / step) * step; v <= max + 1e-9; v += step) ticks.push(+v.toFixed(10));
  }
  const lo = log ? Math.log(min) : min;
  const hi = log ? Math.log(max) : max;
  const pad = (hi - lo) * 0.06 || 1;
  return {
    log,
    ticks,
    map: (v: number, top: number, bottom: number) => {
      const t = ((log ? Math.log(v) : v) - (lo - pad)) / (hi - lo + 2 * pad);
      return bottom - t * (bottom - top);
    },
  };
}

export interface ChartOptions {
  onScale?: (log: boolean) => void;
  baseline?: number | null;          // dashed reference line; 100 for index charts (default), 0 for changes, null for none
  format?: (v: number) => string;    // value formatter for end labels and tooltip
  allowLog?: boolean;
  xLabels?: string[];                // custom x labels (e.g. event offsets "−3", "0", "+6") instead of months
  tickEvery?: number;                // with xLabels: label every n-th point
}

export function renderChart(root: HTMLElement, data: ChartData, opts: ChartOptions = {}) {
  const baseline = opts.baseline === undefined ? 100 : opts.baseline;
  const isIndex = baseline === 100;
  const fmtVal = opts.format ?? ((v: number) => fmt1.format(v));
  root.replaceChildren();
  root.classList.add("chart");
  const W = Math.max(240, root.clientWidth);
  const H = W < 520 ? 280 : 380;
  const M = { left: 44, right: W < 520 ? 92 : 104, top: 14, bottom: 30 };
  const n = data.months.length;
  const all = data.series.flatMap((s) => s.values).concat(baseline === null ? [] : [baseline]);
  const ys = yScale(Math.min(...all), Math.max(...all), opts.allowLog ?? isIndex);
  opts.onScale?.(ys.log);
  const x = (i: number) => M.left + (n === 1 ? 0 : (i / (n - 1)) * (W - M.left - M.right));
  const y = (v: number) => ys.map(v, M.top, H - M.bottom);

  const svg = el("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: "img", tabindex: 0 }, root);
  svg.setAttribute("aria-label", `${data.series.map((s) => s.label).join(", ")}: ${data.months.length} noktalık seyir${isIndex ? ", 100 = başlangıç" : ""}. Ok tuşlarıyla noktalar arasında gezinin.`);
  const tickFmt = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 2 });

  // Grid + y ticks
  const grid = el("g", { class: "grid" }, svg);
  for (const t of ys.ticks) {
    const yy = y(t);
    el("line", { x1: M.left, x2: W - M.right, y1: yy, y2: yy, class: t === baseline ? "base" : "" }, grid);
    const label = el("text", { x: M.left - 6, y: yy + 4, "text-anchor": "end", class: "tick" }, grid);
    label.textContent = tickFmt.format(t);
  }
  if (baseline !== null && !ys.ticks.includes(baseline)) {
    el("line", { x1: M.left, x2: W - M.right, y1: y(baseline), y2: y(baseline), class: "base" }, grid);
  }
  // X ticks: first point of each year (thinned to fit); for windows up to 1.5 years, quarters.
  const idx = (m: string) => Number(m.slice(0, 4)) * 12 + Number(m.slice(5)) - 1;
  const yearsSpan = opts.xLabels ? 0 : (idx(data.months[n - 1]) - idx(data.months[0])) / 12;
  const everyYears = Math.max(1, Math.ceil((yearsSpan * 60) / (W - M.left - M.right)));
  if (opts.xLabels) {
    const every = opts.tickEvery ?? Math.max(1, Math.ceil(n / 8));
    opts.xLabels.forEach((lab, i) => {
      if (i % every !== 0 && i !== n - 1) return;
      el("line", { x1: x(i), x2: x(i), y1: H - M.bottom, y2: H - M.bottom + 4, class: "xtick" }, grid);
      const t = el("text", { x: x(i), y: H - M.bottom + 18, "text-anchor": "middle", class: "tick" }, grid);
      t.textContent = lab;
    });
  }
  if (!opts.xLabels) data.months.forEach((m, i) => {
    const mo = Number(m.slice(5));
    const yr = Number(m.slice(0, 4));
    const show = yearsSpan <= 1.5
      ? (mo - 1) % 3 === 0
      : i > 0 && yr !== Number(data.months[i - 1].slice(0, 4)) && yr % everyYears === 0;
    if (!show) return;
    el("line", { x1: x(i), x2: x(i), y1: H - M.bottom, y2: H - M.bottom + 4, class: "xtick" }, grid);
    const t = el("text", { x: x(i), y: H - M.bottom + 18, "text-anchor": "middle", class: "tick" }, grid);
    t.textContent = yearsSpan <= 1.5 ? `${MONTHS_SHORT[mo - 1]} ${m.slice(2, 4)}` : String(yr);
  });

  // Lines
  for (const s of data.series) {
    const d = s.values.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(" ");
    el("path", { d, fill: "none", stroke: s.color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
  }

  // Direct end labels, nudged apart so they never collide.
  const ends = data.series
    .map((s) => ({ s, y: y(s.values[n - 1]) }))
    .sort((a, b) => a.y - b.y);
  const gap = 30;
  for (let k = 1; k < ends.length; k++) if (ends[k].y - ends[k - 1].y < gap) ends[k].y = ends[k - 1].y + gap;
  const overflow = ends.length ? ends[ends.length - 1].y - (H - M.bottom) : 0;
  if (overflow > 0) for (const e of ends) e.y -= overflow;
  for (const e of ends) {
    el("circle", { cx: x(n - 1), cy: y(e.s.values[n - 1]), r: 3.5, fill: e.s.color }, svg);
    const g = el("g", {}, svg);
    const t1 = el("text", { x: W - M.right + 8, y: e.y - 2, class: "end-value" }, g);
    t1.textContent = isIndex ? fmt0.format(e.s.values[n - 1]) : fmtVal(e.s.values[n - 1]);
    const t2 = el("text", { x: W - M.right + 8, y: e.y + 12, class: "end-label" }, g);
    t2.textContent = e.s.label;
    el("rect", { x: W - M.right + 1, y: e.y - 6, width: 4, height: 2, fill: e.s.color }, g);
  }

  // Crosshair + tooltip
  const hair = el("line", { y1: M.top, y2: H - M.bottom, class: "hair", visibility: "hidden" }, svg);
  const dots = data.series.map((s) => el("circle", { r: 4.5, fill: s.color, class: "dot", visibility: "hidden" }, svg));
  const hit = el("rect", { x: M.left, y: M.top, width: W - M.left - M.right, height: H - M.top - M.bottom, fill: "transparent" }, svg);
  const tip = document.createElement("div");
  tip.className = "chart-tip";
  tip.hidden = true;
  root.appendChild(tip);

  let current = n - 1;
  function show(i: number) {
    current = Math.max(0, Math.min(n - 1, i));
    const cx = x(current);
    hair.setAttribute("x1", String(cx));
    hair.setAttribute("x2", String(cx));
    hair.setAttribute("visibility", "visible");
    data.series.forEach((s, k) => {
      dots[k].setAttribute("cx", String(cx));
      dots[k].setAttribute("cy", String(y(s.values[current])));
      dots[k].setAttribute("visibility", "visible");
    });
    const m = data.months[current];
    tip.replaceChildren();
    const head = document.createElement("div");
    head.className = "tip-head";
    head.textContent = opts.xLabels ? opts.xLabels[current] : `${MONTHS[Number(m.slice(5)) - 1]} ${m.slice(0, 4)}`;
    tip.appendChild(head);
    for (const s of [...data.series].sort((a, b) => b.values[current] - a.values[current])) {
      const row = document.createElement("div");
      row.className = "tip-row";
      const key = document.createElement("span");
      key.className = "tip-key";
      key.style.background = s.color;
      const val = document.createElement("strong");
      val.textContent = fmtVal(s.values[current]);
      const lab = document.createElement("span");
      lab.className = "tip-label";
      lab.textContent = isIndex ? `${s.label} (${pctFmt.format(s.values[current] / 100 - 1)})` : s.label;
      row.append(key, val, lab);
      tip.appendChild(row);
    }
    tip.hidden = false;
    const tw = tip.offsetWidth;
    const preferred = cx + 12 + tw > W ? cx - 12 - tw : cx + 12;
    tip.style.left = `${Math.max(0, Math.min(W - tw, preferred))}px`;
    tip.style.top = `${M.top}px`;
  }
  function hide() {
    hair.setAttribute("visibility", "hidden");
    dots.forEach((d) => d.setAttribute("visibility", "hidden"));
    tip.hidden = true;
  }
  const indexAt = (clientX: number) => {
    const r = svg.getBoundingClientRect();
    return Math.round(((clientX - r.left - M.left) / (W - M.left - M.right)) * (n - 1));
  };
  hit.addEventListener("pointermove", (ev) => show(indexAt(ev.clientX)));
  hit.addEventListener("pointerdown", (ev) => show(indexAt(ev.clientX)));
  svg.addEventListener("pointerleave", hide);
  svg.addEventListener("focus", () => show(current));
  svg.addEventListener("blur", hide);
  svg.addEventListener("keydown", (ev) => {
    const step = { ArrowLeft: -1, ArrowRight: 1, PageUp: -12, PageDown: 12 }[ev.key];
    if (step) { show(current + step); ev.preventDefault(); }
    else if (ev.key === "Home") { show(0); ev.preventDefault(); }
    else if (ev.key === "End") { show(n - 1); ev.preventDefault(); }
    else if (ev.key === "Escape") hide();
  });
}
