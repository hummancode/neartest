// EXAMPLE plans. Names, prices and features are placeholders, not product decisions.
// Prices are in kuruş (integer) to avoid floating point money.

export type PlanId = "pro_monthly" | "pro_yearly";

export type Plan = { id: PlanId; label: string; price_kurus: number; interval: "month" | "year"; example: true };

export const PLANS: Record<PlanId, Plan> = {
  pro_monthly: { id: "pro_monthly", label: "Pro (aylık)", price_kurus: 9900, interval: "month", example: true },
  pro_yearly: { id: "pro_yearly", label: "Pro (yıllık)", price_kurus: 99000, interval: "year", example: true },
};

export function isPlanId(x: unknown): x is PlanId {
  return typeof x === "string" && Object.hasOwn(PLANS, x);
}
