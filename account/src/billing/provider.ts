// Payment provider abstraction. The app only talks to this interface, so switching
// between iyzico, PayTR, Paddle, Lemon Squeezy... means writing one adapter.

import type { BillingEvent } from "../entitlements.ts";
import type { PlanId } from "../plans.ts";

export type CheckoutRequest = {
  user_id: string;
  email: string;
  plan: PlanId;
  success_url: string;
  cancel_url: string;
};

export interface PaymentProvider {
  readonly name: string;
  /** Returns the provider-hosted payment page URL. Card data never touches our server. */
  createCheckout(req: CheckoutRequest): Promise<{ url: string }>;
  /** Ask the provider to stop renewing. The final state arrives later as a webhook. */
  cancel(provider_ref: string): Promise<void>;
  /** Verify the webhook signature and map the payload to a BillingEvent. Null = reject. */
  parseWebhook(rawBody: string, headers: Headers, now: number): Promise<BillingEvent | null>;
}
