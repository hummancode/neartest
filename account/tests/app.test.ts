import { test } from "node:test";
import assert from "node:assert/strict";
import { handle, type Deps } from "../src/app.ts";
import { ConsoleEmail } from "../src/auth.ts";
import { MockProvider, WEBHOOK_TOLERANCE_MS } from "../src/billing/mock.ts";
import { MemoryStore } from "../src/store.ts";

const BASE = "https://site.test";
const DAY = 86_400_000;
const T0 = Date.UTC(2026, 0, 1);
const LEGAL = { kvkk_aydinlatma: "k1", mesafeli_satis: "m1", on_bilgilendirme: "o1", cayma_istisnasi: "c1" };
const ALL_ACCEPTED = { mesafeli_satis: true, on_bilgilendirme: true, cayma_istisnasi: true };

function setup() {
  let now = T0;
  const store = new MemoryStore(), mail = new ConsoleEmail(), provider = new MockProvider("whsec_test");
  const d: Deps = { store, mail, provider, baseUrl: BASE, legal: LEGAL, now: () => now };
  let cookie = "";
  const call = async (method: string, path: string, body?: unknown, extra: Record<string, string> = {}) => {
    const headers: Record<string, string> = { origin: BASE, ...extra };
    if (cookie) headers.cookie = cookie;
    if (body !== undefined) headers["content-type"] = "application/json";
    const res = await handle(new Request(BASE + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) }), d);
    const sc = res.headers.get("set-cookie");
    if (sc) cookie = sc.split(";")[0].endsWith("=") ? "" : sc.split(";")[0];
    return { status: res.status, body: await res.json() };
  };
  const login = async (email = "ayse@example.com") => {
    await call("POST", "/api/auth/link", { email });
    const token = decodeURIComponent(/t=([^\s]+)/.exec(mail.sent.at(-1)!.text)![1]);
    return call("POST", "/api/auth/verify", { token });
  };
  const webhook = async (ev: unknown, ts = now) => {
    const raw = JSON.stringify(ev);
    const res = await handle(new Request(BASE + "/api/billing/webhook", { method: "POST", headers: await provider.sign(raw, ts), body: raw }), d);
    return { status: res.status, body: await res.json() };
  };
  return { d, store, mail, provider, call, login, webhook, setNow: (t: number) => (now = t) };
}

test("full flow: login → checkout → webhook → pro → cancel → free", async () => {
  const s = setup();
  const v = await s.login();
  assert.equal(v.status, 200);
  assert.equal(v.body.new, true);
  const uid = [...s.store.users.values()][0].id;

  let me = await s.call("GET", "/api/me");
  assert.equal(me.body.entitlement.tier, "free");

  const co = await s.call("POST", "/api/billing/checkout", { plan: "pro_monthly", accept: ALL_ACCEPTED });
  assert.equal(co.status, 200);
  assert.match(co.body.url, /^https:\/\/mock-pay\.invalid\/checkout\?/);
  assert.deepEqual((await s.store.consents(uid)).map((c) => `${c.kind}@${c.version}`).sort(),
    ["cayma_istisnasi@c1", "kvkk_aydinlatma@k1", "mesafeli_satis@m1", "on_bilgilendirme@o1"]);

  const wh = await s.webhook({ type: "subscription.started", id: "ev1", user_id: uid, provider_ref: "sub_1", plan: "pro_monthly", period_end: T0 + 20 * DAY, trial: false, at: T0 });
  assert.equal(wh.status, 200);
  me = await s.call("GET", "/api/me");
  assert.equal(me.body.entitlement.tier, "pro");
  assert.equal(me.body.subscription.status, "active");

  assert.equal((await s.call("POST", "/api/billing/checkout", { plan: "pro_monthly", accept: ALL_ACCEPTED })).status, 409);

  const c = await s.call("POST", "/api/billing/cancel");
  assert.equal(c.status, 202);
  assert.deepEqual(s.provider.canceled, ["sub_1"]);
  await s.webhook({ type: "subscription.canceled", id: "ev2", provider_ref: "sub_1", immediate: false, at: T0 + DAY });
  me = await s.call("GET", "/api/me");
  assert.equal(me.body.entitlement.tier, "pro"); // paid until period end
  s.setNow(T0 + 21 * DAY); // after period end, session (30 days) still valid
  me = await s.call("GET", "/api/me");
  assert.equal(me.body.entitlement.tier, "free");
});

test("checkout requires every legal acceptance and a known plan", async () => {
  const s = setup();
  await s.login();
  const r = await s.call("POST", "/api/billing/checkout", { plan: "pro_monthly", accept: { mesafeli_satis: true } });
  assert.equal(r.status, 400);
  assert.deepEqual(r.body.missing, ["on_bilgilendirme", "cayma_istisnasi"]);
  assert.equal((await s.call("POST", "/api/billing/checkout", { plan: "gold", accept: ALL_ACCEPTED })).body.error, "unknown_plan");
});

test("webhooks: bad signature, replayed timestamp and duplicates", async () => {
  const s = setup();
  await s.login();
  const uid = [...s.store.users.values()][0].id;
  const ev = { type: "subscription.started", id: "ev1", user_id: uid, provider_ref: "sub_1", plan: "pro_monthly", period_end: T0 + 30 * DAY, trial: false, at: T0 };

  const raw = JSON.stringify(ev);
  const forged = await handle(new Request(BASE + "/api/billing/webhook", { method: "POST", headers: { "x-mock-timestamp": String(T0), "x-mock-signature": "0".repeat(64) }, body: raw }), s.d);
  assert.equal(forged.status, 400);
  assert.equal((await s.webhook(ev, T0 - WEBHOOK_TOLERANCE_MS - 1)).status, 400, "old timestamp rejected");
  assert.equal(s.store.subs.size, 0);

  assert.equal((await s.webhook(ev)).body.ok, true);
  assert.equal((await s.webhook(ev)).body.duplicate, true);
});

test("webhook for unknown user is acknowledged but ignored", async () => {
  const s = setup();
  const r = await s.webhook({ type: "subscription.started", id: "ev1", user_id: "ghost", provider_ref: "sub_1", plan: "pro_monthly", period_end: T0 + DAY, trial: false, at: T0 });
  assert.equal(r.body.ignored, "unknown_user");
  assert.equal(s.store.subs.size, 0);
});

test("CSRF: foreign origin is rejected; unauthenticated calls get 401", async () => {
  const s = setup();
  assert.equal((await s.call("POST", "/api/auth/link", { email: "a@b.co" }, { origin: "https://evil.test" })).status, 403);
  assert.equal((await s.call("GET", "/api/me")).status, 401);
  assert.equal((await s.call("POST", "/api/billing/checkout", { plan: "pro_monthly", accept: ALL_ACCEPTED })).status, 401);
});

test("login link endpoint: invalid email and rate limit", async () => {
  const s = setup();
  assert.equal((await s.call("POST", "/api/auth/link", { email: "nope" })).status, 400);
  for (let i = 0; i < 3; i++) assert.equal((await s.call("POST", "/api/auth/link", { email: "a@b.co" })).status, 202);
  assert.equal((await s.call("POST", "/api/auth/link", { email: "a@b.co" })).status, 429);
});

test("logout ends the session", async () => {
  const s = setup();
  await s.login();
  assert.equal((await s.call("GET", "/api/me")).status, 200);
  await s.call("POST", "/api/auth/logout");
  assert.equal((await s.call("GET", "/api/me")).status, 401);
});

test("account deletion cancels billing and removes all user data", async () => {
  const s = setup();
  await s.login();
  const uid = [...s.store.users.values()][0].id;
  await s.webhook({ type: "subscription.started", id: "ev1", user_id: uid, provider_ref: "sub_1", plan: "pro_yearly", period_end: T0 + 365 * DAY, trial: false, at: T0 });
  const r = await s.call("DELETE", "/api/me");
  assert.equal(r.status, 200);
  assert.deepEqual(s.provider.canceled, ["sub_1"]);
  assert.equal(s.store.users.size, 0);
  assert.equal(s.store.sessions.size, 0);
  assert.equal(s.store.subs.size, 0);
  assert.equal((await s.store.consents(uid)).length, 0);
});
