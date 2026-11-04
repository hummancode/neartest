// Subscription state machine and entitlement check. Pure functions, no I/O.

import type { PlanId } from "./plans.ts";

export type SubStatus = "active" | "trialing" | "past_due" | "canceled" | "expired";

export type Subscription = {
  user_id: string;
  provider: string;
  provider_ref: string | null;
  plan: PlanId;
  status: SubStatus;
  current_period_end: number | null; // unix ms
  cancel_at_period_end: boolean;
  updated_at: number;
};

/** Provider-independent billing events. Each provider adapter maps its webhooks to these. */
export type BillingEvent =
  | { type: "subscription.started"; id: string; user_id: string; provider_ref: string; plan: PlanId; period_end: number; trial: boolean; at: number }
  | { type: "subscription.renewed"; id: string; provider_ref: string; period_end: number; at: number }
  | { type: "payment.failed"; id: string; provider_ref: string; at: number }
  | { type: "subscription.canceled"; id: string; provider_ref: string; immediate: boolean; at: number }
  | { type: "subscription.refunded"; id: string; provider_ref: string; at: number };

/** Days of access kept after a failed renewal while the provider retries the card. */
export const GRACE_DAYS = 3;
const DAY = 86_400_000;

/**
 * Apply one event to the current subscription (or null). Returns the new state.
 * Events older than the last update are ignored, so out-of-order webhooks cannot
 * resurrect a canceled subscription.
 */
export function applyEvent(sub: Subscription | null, ev: BillingEvent, provider: string): Subscription | null {
  if (ev.type === "subscription.started") {
    return {
      user_id: ev.user_id, provider, provider_ref: ev.provider_ref, plan: ev.plan,
      status: ev.trial ? "trialing" : "active", current_period_end: ev.period_end,
      cancel_at_period_end: false, updated_at: ev.at,
    };
  }
  if (!sub || sub.provider_ref !== ev.provider_ref) return sub; // unknown subscription: ignore
  if (ev.at < sub.updated_at) return sub; // stale event
  switch (ev.type) {
    case "subscription.renewed":
      return { ...sub, status: "active", current_period_end: Math.max(ev.period_end, sub.current_period_end ?? 0), updated_at: ev.at };
    case "payment.failed":
      return sub.status === "expired" ? sub : { ...sub, status: "past_due", updated_at: ev.at };
    case "subscription.canceled":
      return ev.immediate
        ? { ...sub, status: "expired", current_period_end: ev.at, cancel_at_period_end: false, updated_at: ev.at }
        : { ...sub, status: "canceled", cancel_at_period_end: true, updated_at: ev.at };
    case "subscription.refunded":
      return { ...sub, status: "expired", current_period_end: ev.at, updated_at: ev.at };
  }
}

export type Entitlement = { tier: "free" | "pro"; until: number | null; reason: string };

/** What the user may use right now. */
export function entitlement(sub: Subscription | null, now: number): Entitlement {
  if (!sub || sub.current_period_end == null) return { tier: "free", until: null, reason: "no_subscription" };
  const end = sub.current_period_end;
  switch (sub.status) {
    case "active":
    case "trialing":
    case "canceled": // paid until the end of the period
      return now < end ? { tier: "pro", until: end, reason: sub.status } : { tier: "free", until: null, reason: "period_ended" };
    case "past_due": {
      const graceEnd = end + GRACE_DAYS * DAY;
      return now < graceEnd ? { tier: "pro", until: graceEnd, reason: "grace" } : { tier: "free", until: null, reason: "payment_failed" };
    }
    case "expired":
      return { tier: "free", until: null, reason: "expired" };
  }
}
