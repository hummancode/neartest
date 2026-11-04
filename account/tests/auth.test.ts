import { test } from "node:test";
import assert from "node:assert/strict";
import { ConsoleEmail, LOGIN_TOKEN_TTL_MS, MAX_LINKS_PER_WINDOW, normalizeEmail, readCookie, requestLoginLink, userFromSession, verifyLoginLink } from "../src/auth.ts";
import { MemoryStore } from "../src/store.ts";

const T0 = Date.UTC(2026, 0, 1);
const tokenFrom = (m: ConsoleEmail) => decodeURIComponent(/t=([^\s]+)/.exec(m.sent.at(-1)!.text)![1]);

test("normalizeEmail", () => {
  assert.equal(normalizeEmail("  Ayse@Example.COM "), "ayse@example.com");
  for (const bad of ["", "no-at", "a@b", "a b@c.d", 42, null]) assert.equal(normalizeEmail(bad), null);
});

test("login link: single use, creates user, stores only hashes", async () => {
  const store = new MemoryStore(), mail = new ConsoleEmail();
  assert.equal(await requestLoginLink(store, mail, "ayse@example.com", "https://x.test", T0), "sent");
  const token = tokenFrom(mail);
  assert.ok(![...store.tokens.keys()].includes(token), "raw token must not be stored");
  const r = await verifyLoginLink(store, token, T0 + 1000);
  assert.ok(r && r.isNew && r.user.email === "ayse@example.com");
  assert.ok(![...store.sessions.keys()].includes(r.sessionToken), "raw session id must not be stored");
  assert.equal((await userFromSession(store, r.sessionToken, T0 + 2000))?.id, r.user.id);
  assert.equal(await verifyLoginLink(store, token, T0 + 2000), null, "second use fails");
});

test("login link expires", async () => {
  const store = new MemoryStore(), mail = new ConsoleEmail();
  await requestLoginLink(store, mail, "a@b.co", "https://x.test", T0);
  assert.equal(await verifyLoginLink(store, tokenFrom(mail), T0 + LOGIN_TOKEN_TTL_MS), null);
});

test("second login reuses the same user", async () => {
  const store = new MemoryStore(), mail = new ConsoleEmail();
  await requestLoginLink(store, mail, "a@b.co", "https://x.test", T0);
  const a = await verifyLoginLink(store, tokenFrom(mail), T0);
  await requestLoginLink(store, mail, "A@B.co", "https://x.test", T0 + 1);
  const b = await verifyLoginLink(store, tokenFrom(mail), T0 + 1);
  assert.equal(a!.user.id, b!.user.id);
  assert.equal(b!.isNew, false);
});

test("rate limit per e-mail", async () => {
  const store = new MemoryStore(), mail = new ConsoleEmail();
  for (let i = 0; i < MAX_LINKS_PER_WINDOW; i++) assert.equal(await requestLoginLink(store, mail, "a@b.co", "https://x.test", T0 + i), "sent");
  assert.equal(await requestLoginLink(store, mail, "a@b.co", "https://x.test", T0 + 10), "rate_limited");
  assert.equal(await requestLoginLink(store, mail, "a@b.co", "https://x.test", T0 + LOGIN_TOKEN_TTL_MS + 10), "sent");
});

test("garbage tokens and expired sessions are rejected", async () => {
  const store = new MemoryStore();
  for (const t of [undefined, "", "short", "x".repeat(500)]) assert.equal(await verifyLoginLink(store, t, T0), null);
  assert.equal(await userFromSession(store, "nope", T0), null);
  assert.equal(await userFromSession(store, null, T0), null);
});

test("readCookie", () => {
  assert.equal(readCookie("a=1; sid=abc; b=2"), "abc");
  assert.equal(readCookie("a=1"), null);
  assert.equal(readCookie(null), null);
});
