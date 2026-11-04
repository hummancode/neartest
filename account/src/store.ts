// Storage interface + in-memory implementation (dev/tests). A D1 version would
// implement the same interface with the SQL in schema.sql.

import type { Subscription } from "./entitlements.ts";

export type User = { id: string; email: string; created_at: number };
export type LoginToken = { token_hash: string; email: string; expires_at: number; used_at: number | null; created_at: number };
export type Session = { id_hash: string; user_id: string; expires_at: number; created_at: number };
export type Consent = { user_id: string; kind: string; version: string; accepted_at: number };

export interface Store {
  userByEmail(email: string): Promise<User | null>;
  userById(id: string): Promise<User | null>;
  createUser(u: User): Promise<void>;
  /** Deletes the user and everything that references it (sessions, consents, subscription). */
  deleteUser(id: string): Promise<void>;

  putLoginToken(t: LoginToken): Promise<void>;
  /** Atomically mark the token used; returns it only if it was unused. */
  consumeLoginToken(token_hash: string, now: number): Promise<LoginToken | null>;
  countLoginTokensSince(email: string, since: number): Promise<number>;

  putSession(s: Session): Promise<void>;
  sessionByHash(id_hash: string): Promise<Session | null>;
  deleteSession(id_hash: string): Promise<void>;

  subscriptionByUser(user_id: string): Promise<Subscription | null>;
  subscriptionByRef(provider: string, provider_ref: string): Promise<Subscription | null>;
  putSubscription(s: Subscription): Promise<void>;

  /** Returns false if this event was already recorded (idempotency). */
  recordWebhookEvent(provider: string, event_id: string, now: number): Promise<boolean>;

  putConsent(c: Consent): Promise<void>;
  consents(user_id: string): Promise<Consent[]>;
}

export class MemoryStore implements Store {
  users = new Map<string, User>();
  tokens = new Map<string, LoginToken>();
  sessions = new Map<string, Session>();
  subs = new Map<string, Subscription>();
  events = new Set<string>();
  consentList: Consent[] = [];

  async userByEmail(email: string) { return [...this.users.values()].find((u) => u.email === email) ?? null; }
  async userById(id: string) { return this.users.get(id) ?? null; }
  async createUser(u: User) { this.users.set(u.id, u); }
  async deleteUser(id: string) {
    this.users.delete(id);
    for (const [k, s] of this.sessions) if (s.user_id === id) this.sessions.delete(k);
    this.subs.delete(id);
    this.consentList = this.consentList.filter((c) => c.user_id !== id);
  }

  async putLoginToken(t: LoginToken) { this.tokens.set(t.token_hash, t); }
  async consumeLoginToken(h: string, now: number) {
    const t = this.tokens.get(h);
    if (!t || t.used_at != null) return null;
    t.used_at = now;
    return { ...t };
  }
  async countLoginTokensSince(email: string, since: number) {
    return [...this.tokens.values()].filter((t) => t.email === email && t.created_at >= since).length;
  }

  async putSession(s: Session) { this.sessions.set(s.id_hash, s); }
  async sessionByHash(h: string) { return this.sessions.get(h) ?? null; }
  async deleteSession(h: string) { this.sessions.delete(h); }

  async subscriptionByUser(user_id: string) { return this.subs.get(user_id) ?? null; }
  async subscriptionByRef(provider: string, ref: string) {
    return [...this.subs.values()].find((s) => s.provider === provider && s.provider_ref === ref) ?? null;
  }
  async putSubscription(s: Subscription) { this.subs.set(s.user_id, s); }

  async recordWebhookEvent(provider: string, id: string) {
    const k = `${provider}:${id}`;
    if (this.events.has(k)) return false;
    this.events.add(k);
    return true;
  }

  async putConsent(c: Consent) {
    if (!this.consentList.some((x) => x.user_id === c.user_id && x.kind === c.kind && x.version === c.version)) this.consentList.push(c);
  }
  async consents(user_id: string) { return this.consentList.filter((c) => c.user_id === user_id); }
}
