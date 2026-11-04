// Mock provider for development and tests. Signs webhooks with HMAC-SHA256 like
// real providers do, so the verification path is exercised end to end.

import { hmacSha256Hex, safeEqual } from "../crypto.ts";
import type { BillingEvent } from "../entitlements.ts";
import type { CheckoutRequest, PaymentProvider } from "./provider.ts";

/** Reject webhooks whose timestamp is further than this from now (replay protection). */
export const WEBHOOK_TOLERANCE_MS = 5 * 60_000;

export class MockProvider implements PaymentProvider {
  readonly name = "mock";
  readonly canceled: string[] = [];
  readonly secret: string;
  constructor(secret: string) {
    this.secret = secret;
  }

  async createCheckout(req: CheckoutRequest): Promise<{ url: string }> {
    const q = new URLSearchParams({ user: req.user_id, plan: req.plan, ok: req.success_url });
    return { url: `https://mock-pay.invalid/checkout?${q}` };
  }

  async cancel(provider_ref: string): Promise<void> {
    this.canceled.push(provider_ref);
  }

  /** Test helper: produce the headers a real sender would attach. */
  async sign(body: string, timestamp: number): Promise<Headers> {
    const sig = await hmacSha256Hex(this.secret, `${timestamp}.${body}`);
    return new Headers({ "x-mock-timestamp": String(timestamp), "x-mock-signature": sig });
  }

  async parseWebhook(rawBody: string, headers: Headers, now: number): Promise<BillingEvent | null> {
    const ts = Number(headers.get("x-mock-timestamp"));
    const sig = headers.get("x-mock-signature") ?? "";
    if (!Number.isFinite(ts) || Math.abs(now - ts) > WEBHOOK_TOLERANCE_MS) return null;
    const expected = await hmacSha256Hex(this.secret, `${ts}.${rawBody}`);
    if (!safeEqual(sig, expected)) return null;
    try {
      const ev = JSON.parse(rawBody) as BillingEvent;
      return typeof ev?.id === "string" && typeof ev?.type === "string" ? ev : null;
    } catch {
      return null;
    }
  }
}
