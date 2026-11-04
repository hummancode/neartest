// Passwordless e-mail login ("magic link"). No passwords are stored.
// Tokens and session ids are random; only their SHA-256 hashes are persisted.

import { randomToken, sha256Hex } from "./crypto.ts";
import type { Store, User } from "./store.ts";

export const LOGIN_TOKEN_TTL_MS = 15 * 60_000;
export const SESSION_TTL_MS = 30 * 86_400_000;
export const MAX_LINKS_PER_WINDOW = 3; // per e-mail per TTL window
export const SESSION_COOKIE = "sid";

export interface EmailSender {
  send(to: string, subject: string, text: string): Promise<void>;
}

/** Collects mails instead of sending them (dev/tests). */
export class ConsoleEmail implements EmailSender {
  readonly sent: { to: string; subject: string; text: string }[] = [];
  async send(to: string, subject: string, text: string) {
    this.sent.push({ to, subject, text });
  }
}

export function normalizeEmail(raw: unknown): string | null {
  if (typeof raw !== "string") return null;
  const e = raw.trim().toLowerCase();
  // Deliberately simple: the link itself proves the address works.
  return e.length <= 254 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e) ? e : null;
}

export type LinkResult = "sent" | "rate_limited" | "invalid_email";

export async function requestLoginLink(
  store: Store, mail: EmailSender, rawEmail: unknown, baseUrl: string, now: number,
): Promise<LinkResult> {
  const email = normalizeEmail(rawEmail);
  if (!email) return "invalid_email";
  if ((await store.countLoginTokensSince(email, now - LOGIN_TOKEN_TTL_MS)) >= MAX_LINKS_PER_WINDOW) return "rate_limited";
  const token = randomToken();
  await store.putLoginToken({ token_hash: await sha256Hex(token), email, expires_at: now + LOGIN_TOKEN_TTL_MS, used_at: null, created_at: now });
  const link = `${baseUrl}/hesap/giris?t=${encodeURIComponent(token)}`;
  await mail.send(email, "Giriş bağlantınız",
    `Giriş yapmak için bu bağlantıyı 15 dakika içinde açın:\n${link}\n\nBu isteği siz yapmadıysanız bu e-postayı yok sayabilirsiniz.`);
  return "sent";
}

export type VerifyResult = { user: User; sessionToken: string; isNew: boolean } | null;

/** Consume a login token; creates the user on first login. Returns a new session. */
export async function verifyLoginLink(store: Store, token: unknown, now: number): Promise<VerifyResult> {
  if (typeof token !== "string" || token.length < 20 || token.length > 100) return null;
  const t = await store.consumeLoginToken(await sha256Hex(token), now);
  if (!t || t.expires_at <= now) return null;
  let user = await store.userByEmail(t.email);
  const isNew = !user;
  if (!user) {
    user = { id: randomToken(16), email: t.email, created_at: now };
    await store.createUser(user);
  }
  const sessionToken = randomToken();
  await store.putSession({ id_hash: await sha256Hex(sessionToken), user_id: user.id, expires_at: now + SESSION_TTL_MS, created_at: now });
  return { user, sessionToken, isNew };
}

export async function userFromSession(store: Store, sessionToken: string | null, now: number): Promise<User | null> {
  if (!sessionToken) return null;
  const s = await store.sessionByHash(await sha256Hex(sessionToken));
  if (!s || s.expires_at <= now) return null;
  return store.userById(s.user_id);
}

export async function logout(store: Store, sessionToken: string | null): Promise<void> {
  if (sessionToken) await store.deleteSession(await sha256Hex(sessionToken));
}

export function sessionCookie(token: string, maxAgeMs = SESSION_TTL_MS): string {
  return `${SESSION_COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${Math.floor(maxAgeMs / 1000)}`;
}

export function readCookie(header: string | null, name = SESSION_COOKIE): string | null {
  for (const part of (header ?? "").split(";")) {
    const [k, ...v] = part.trim().split("=");
    if (k === name) return v.join("=") || null;
  }
  return null;
}
