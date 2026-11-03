// Editable progressive tariff (rows: upper limit TL + rate %), shared by the tax calculators.
import type { Brackets } from "./engine.ts";
import { parseAmount } from "./card.ts";

const nf0 = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 1 });
const num = (s: string) => { const t = s.trim().replace(/\./g, "").replace(",", "."); const x = Number(t); return t !== "" && Number.isFinite(x) ? x : null; };

export function renderTariffEditor(root: HTMLElement, t: Brackets, onInput: () => void) {
  root.replaceChildren(...t.map(([u, r], i) => {
    const row = document.createElement("div"); row.className = "t-row";
    const up = document.createElement("input"); up.inputMode = "decimal"; up.className = "t-up";
    up.value = u === null ? "" : nf0.format(u); up.disabled = u === null; up.placeholder = u === null ? "üzeri" : "";
    up.setAttribute("aria-label", `${i + 1}. dilim üst sınırı (TL)`);
    const rt = document.createElement("input"); rt.inputMode = "decimal"; rt.className = "t-rate"; rt.value = nf1.format(r * 100);
    rt.setAttribute("aria-label", `${i + 1}. dilim oranı (%)`);
    const l1 = document.createElement("span"); l1.textContent = u === null ? "Kalan matrah:" : `${i + 1}. dilim: TL'ye kadar`;
    const l2 = document.createElement("span"); l2.textContent = "%";
    row.append(l1, up, rt, l2);
    return row;
  }));
  root.querySelectorAll("input").forEach((x) => x.addEventListener("input", onInput));
}

export function readTariff(root: HTMLElement): Brackets | null {
  const out: Brackets = [];
  for (const r of root.querySelectorAll<HTMLDivElement>(".t-row")) {
    const up = r.querySelector<HTMLInputElement>(".t-up")!, rt = num(r.querySelector<HTMLInputElement>(".t-rate")!.value);
    if (rt == null) return null;
    if (up.disabled) out.push([null, rt / 100]);
    else { const u = parseAmount(up.value); if (u == null) return null; out.push([u, rt / 100]); }
  }
  return out;
}
