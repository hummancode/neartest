// SKETCH ONLY — not implemented. Shows where a real iyzico adapter would go.
// iyzico has a native subscription product (plans, checkout form, webhooks):
// https://docs.iyzico.com/en/products/subscription
// Before implementing: merchant account (requires a company), sandbox keys in
// env/secrets (never in code), and the exact webhook signature scheme from the docs.

import type { BillingEvent } from "../entitlements.ts";
import type { CheckoutRequest, PaymentProvider } from "./provider.ts";

export class IyzicoProvider implements PaymentProvider {
  readonly name = "iyzico";
  constructor(_cfg: { apiKey: string; secretKey: string; baseUrl: string; pricingPlanRefs: Record<string, string> }) {}

  async createCheckout(_req: CheckoutRequest): Promise<{ url: string }> {
    // POST {baseUrl}/v2/subscription/checkoutform/initialize with the plan's pricingPlanReferenceCode
    // and customer e-mail; return the hosted checkout page URL.
    throw new Error("iyzico adapter not implemented");
  }

  async cancel(_provider_ref: string): Promise<void> {
    // POST {baseUrl}/v2/subscription/subscriptions/{ref}/cancel
    throw new Error("iyzico adapter not implemented");
  }

  async parseWebhook(_rawBody: string, _headers: Headers, _now: number): Promise<BillingEvent | null> {
    // Verify the signature as documented by iyzico, then map their event types
    // (e.g. order success / failure / cancel) to BillingEvent.
    throw new Error("iyzico adapter not implemented");
  }
}
