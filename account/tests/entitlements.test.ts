import { test } from "node:test";
import assert from "node:assert/strict";
import { applyEvent, entitlement, GRACE_DAYS, type BillingEvent, type Subscription } from "../src/entitlements.ts";

const DAY = 86_400_000;
const T0 = Date.UTC(2026, 0, 1);
const start = (o: Partial<Extract<BillingEvent, { type: "subscription.started" }>> = {}): BillingEvent =>
  ({ type: "subscription.started", id: "e1", user_id: "u1", provider_ref: "s1", plan: "pro_monthly", period_end: T0 + 30 * DAY, trial: false, at: T0, ...o });
const started = () => applyEvent(null, start(), "mock") as Subscription;

test("no subscription is free", () => {
  assert.deepEqual(entitlement(null, T0), { tier: "free", until: null, reason: "no_subscription" });
});

test("started subscription is pro until period end, free after", () => {
  const s = started();
  assert.equal(s.status, "active");
  assert.equal(entitlement(s, T0 + DAY).tier, "pro");
  assert.equal(entitlement(s, T0 + 30 * DAY).tier, "free"); // end is exclusive
});

test("trial is marked trialing and grants pro", () => {
  const s = applyEvent(null, start({ trial: true }), "mock")!;
  assert.equal(s.status, "trialing");
  assert.equal(entitlement(s, T0 + DAY).tier, "pro");
});

test("renewal extends the period", () => {
  const s = applyEvent(started(), { type: "subscription.renewed", id: "e2", provider_ref: "s1", period_end: T0 + 60 * DAY, at: T0 + 30 * DAY }, "mock")!;
  assert.equal(s.current_period_end, T0 + 60 * DAY);
  assert.equal(entitlement(s, T0 + 45 * DAY).tier, "pro");
});

test("renewal never shortens the period", () => {
  const s = applyEvent(started(), { type: "subscription.renewed", id: "e2", provider_ref: "s1", period_end: T0 + 10 * DAY, at: T0 + DAY }, "mock")!;
  assert.equal(s.current_period_end, T0 + 30 * DAY);
});

test("failed payment keeps access for the grace period only", () => {
  const s = applyEvent(started(), { type: "payment.failed", id: "e2", provider_ref: "s1", at: T0 + 30 * DAY }, "mock")!;
  assert.equal(s.status, "past_due");
  assert.deepEqual(entitlement(s, T0 + 31 * DAY), { tier: "pro", until: T0 + (30 + GRACE_DAYS) * DAY, reason: "grace" });
  assert.equal(entitlement(s, T0 + (30 + GRACE_DAYS) * DAY).tier, "free");
});

test("cancel at period end keeps access until the end", () => {
  const s = applyEvent(started(), { type: "subscription.canceled", id: "e2", provider_ref: "s1", immediate: false, at: T0 + 5 * DAY }, "mock")!;
  assert.equal(s.status, "canceled");
  assert.equal(s.cancel_at_period_end, true);
  assert.equal(entitlement(s, T0 + 29 * DAY).tier, "pro");
  assert.equal(entitlement(s, T0 + 30 * DAY).tier, "free");
});

test("immediate cancel and refund end access now", () => {
  for (const type of ["subscription.canceled", "subscription.refunded"] as const) {
    const ev = (type === "subscription.canceled"
      ? { type, id: "e2", provider_ref: "s1", immediate: true, at: T0 + 5 * DAY }
      : { type, id: "e2", provider_ref: "s1", at: T0 + 5 * DAY }) as BillingEvent;
    const s = applyEvent(started(), ev, "mock")!;
    assert.equal(s.status, "expired");
    assert.equal(entitlement(s, T0 + 5 * DAY).tier, "free");
  }
});

test("stale (out-of-order) events are ignored", () => {
  const canceled = applyEvent(started(), { type: "subscription.canceled", id: "e3", provider_ref: "s1", immediate: true, at: T0 + 10 * DAY }, "mock")!;
  const after = applyEvent(canceled, { type: "subscription.renewed", id: "e2", provider_ref: "s1", period_end: T0 + 60 * DAY, at: T0 + 9 * DAY }, "mock");
  assert.equal(after, canceled);
});

test("events for another subscription are ignored", () => {
  const s = started();
  assert.equal(applyEvent(s, { type: "payment.failed", id: "e2", provider_ref: "other", at: T0 + DAY }, "mock"), s);
  assert.equal(applyEvent(null, { type: "payment.failed", id: "e2", provider_ref: "s1", at: T0 + DAY }, "mock"), null);
});
