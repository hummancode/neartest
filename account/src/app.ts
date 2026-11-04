// HTTP layer. `handle` is framework-free (Request -> Response) so the same code runs
// in a Cloudflare Worker / Pages Function and in tests with an in-memory store.

import { logout, readCookie, requestLoginLink, sessionCookie, userFromSession, verifyLoginLink, type EmailSender } from "./auth.ts";
import type { PaymentProvider } from "./billing/provider.ts";
import { applyEvent, entitlement } from "./entitlements.ts";
import { isPlanId, PLANS } from "./plans.ts";
import type { Store, User } from "./store.ts";

/** Versions of the legal texts currently shown on the site. Bump when a text changes. */
export type LegalVersions = { kvkk_aydinlatma: string; mesafeli_satis: string; on_bilgilendirme: string; cayma_istisnasi: string };

export type Deps = {
  store: Store;
  mail: EmailSender;
  provider: PaymentProvider;
  baseUrl: string; // e.g. https://example.com — also the only allowed Origin
  legal: LegalVersions;
  now?: () => number;
};

const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...headers } });

const CHECKOUT_TEXTS = ["mesafeli_satis", "on_bilgilendirme", "cayma_istisnasi"] as const;

async function readJson(req: Request): Promise<Record<string, unknown> | null> {
  if (!(req.headers.get("content-type") ?? "").startsWith("application/json")) return null;
  try {
    const v = await req.json();
    return v && typeof v === "object" ? (v as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

export async function handle(req: Request, d: Deps): Promise<Response> {
  const now = (d.now ?? Date.now)();
  const url = new URL(req.url);
  const route = `${req.method} ${url.pathname}`;

  // Webhooks come from the provider, authenticated by signature, not by Origin/cookie.
  if (route === "POST /api/billing/webhook") return webhook(req, d, now);

  // CSRF: state-changing requests must come from our own site.
  if (req.method !== "GET" && req.headers.get("origin") !== new URL(d.baseUrl).origin) return json({ error: "bad_origin" }, 403);

  const sid = readCookie(req.headers.get("cookie"));

  switch (route) {
    case "POST /api/auth/link": {
      const body = await readJson(req);
      const r = await requestLoginLink(d.store, d.mail, body?.email, d.baseUrl, now);
      if (r === "invalid_email") return json({ error: "invalid_email" }, 400);
      if (r === "rate_limited") return json({ error: "rate_limited" }, 429);
      return json({ ok: true }, 202);
    }
    case "POST /api/auth/verify": {
      const body = await readJson(req);
      const r = await verifyLoginLink(d.store, body?.token, now);
      if (!r) return json({ error: "invalid_or_expired" }, 400);
      // The privacy notice (aydınlatma metni) was shown on the sign-in form; record which version.
      await d.store.putConsent({ user_id: r.user.id, kind: "kvkk_aydinlatma", version: d.legal.kvkk_aydinlatma, accepted_at: now });
      return json({ email: r.user.email, new: r.isNew }, 200, { "set-cookie": sessionCookie(r.sessionToken) });
    }
    case "POST /api/auth/logout":
      await logout(d.store, sid);
      return json({ ok: true }, 200, { "set-cookie": sessionCookie("", 0) });
  }

  const user = await userFromSession(d.store, sid, now);
  if (!user) return json({ error: "unauthorized" }, 401);

  switch (route) {
    case "GET /api/me": {
      const sub = await d.store.subscriptionByUser(user.id);
      return json({
        email: user.email,
        entitlement: entitlement(sub, now),
        subscription: sub && { plan: sub.plan, status: sub.status, current_period_end: sub.current_period_end, cancel_at_period_end: sub.cancel_at_period_end },
      });
    }
    case "DELETE /api/me":
      return deleteAccount(user, d);
    case "POST /api/billing/checkout":
      return checkout(req, user, d, now);
    case "POST /api/billing/cancel": {
      const sub = await d.store.subscriptionByUser(user.id);
      if (!sub?.provider_ref || sub.status === "expired") return json({ error: "no_active_subscription" }, 400);
      await d.provider.cancel(sub.provider_ref);
      return json({ ok: true, note: "İptal talebi alındı; erişim dönem sonuna kadar sürer." }, 202);
    }
  }
  return json({ error: "not_found" }, 404);
}

async function checkout(req: Request, user: User, d: Deps, now: number): Promise<Response> {
  const body = await readJson(req);
  const plan = body?.plan;
  if (!isPlanId(plan)) return json({ error: "unknown_plan" }, 400);
  const accept = (body?.accept ?? {}) as Record<string, unknown>;
  // Distance-sale contract, pre-information form and the explicit acknowledgement that
  // digital service starts immediately must all be accepted before payment.
  const missing = CHECKOUT_TEXTS.filter((k) => accept[k] !== true);
  if (missing.length) return json({ error: "consent_required", missing }, 400);
  const ent = entitlement(await d.store.subscriptionByUser(user.id), now);
  if (ent.tier === "pro") return json({ error: "already_subscribed" }, 409);
  for (const k of CHECKOUT_TEXTS) await d.store.putConsent({ user_id: user.id, kind: k, version: d.legal[k], accepted_at: now });
  const { url } = await d.provider.createCheckout({
    user_id: user.id, email: user.email, plan: PLANS[plan].id,
    success_url: `${d.baseUrl}/hesap?odeme=tamam`, cancel_url: `${d.baseUrl}/hesap?odeme=iptal`,
  });
  return json({ url });
}

async function webhook(req: Request, d: Deps, now: number): Promise<Response> {
  const raw = await req.text();
  const ev = await d.provider.parseWebhook(raw, req.headers, now);
  if (!ev) return json({ error: "bad_signature" }, 400);
  // Idempotency: providers retry webhooks; apply each event id once.
  if (!(await d.store.recordWebhookEvent(d.provider.name, ev.id, now))) return json({ ok: true, duplicate: true });
  if (ev.type === "subscription.started") {
    if (!(await d.store.userById(ev.user_id))) return json({ ok: true, ignored: "unknown_user" });
    const prev = await d.store.subscriptionByUser(ev.user_id);
    await d.store.putSubscription(applyEvent(prev, ev, d.provider.name)!);
    return json({ ok: true });
  }
  const sub = await d.store.subscriptionByRef(d.provider.name, ev.provider_ref);
  const next = applyEvent(sub, ev, d.provider.name);
  if (next && next !== sub) await d.store.putSubscription(next);
  return json({ ok: true });
}

async function deleteAccount(user: User, d: Deps): Promise<Response> {
  const sub = await d.store.subscriptionByUser(user.id);
  if (sub?.provider_ref && (sub.status === "active" || sub.status === "trialing" || sub.status === "past_due")) await d.provider.cancel(sub.provider_ref);
  await d.store.deleteUser(user.id);
  // NOTE: invoices are kept by the payment provider / accounting system for the legally
  // required period; this database keeps nothing about the deleted user.
  return json({ ok: true }, 200, { "set-cookie": sessionCookie("", 0) });
}
