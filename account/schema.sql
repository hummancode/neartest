-- PROTOTYPE schema for Cloudflare D1 (SQLite). Not applied anywhere yet.
-- Principle: the server stores identity, subscription state and legal consents only.
-- NO user financial data (portfolio, salary, budget...) is ever stored here.

CREATE TABLE users (
  id          TEXT PRIMARY KEY,           -- random id, not derived from email
  email       TEXT NOT NULL UNIQUE,       -- lower-cased
  created_at  INTEGER NOT NULL            -- unix ms
);

-- One-time login links. Only the SHA-256 hash of the token is stored.
CREATE TABLE login_tokens (
  token_hash  TEXT PRIMARY KEY,
  email       TEXT NOT NULL,
  expires_at  INTEGER NOT NULL,
  used_at     INTEGER,
  created_at  INTEGER NOT NULL
);
CREATE INDEX login_tokens_email ON login_tokens(email, created_at);

-- Sessions. Only the hash of the cookie value is stored.
CREATE TABLE sessions (
  id_hash     TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at  INTEGER NOT NULL,
  created_at  INTEGER NOT NULL
);

CREATE TABLE subscriptions (
  user_id             TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  provider            TEXT NOT NULL,      -- 'mock' | 'iyzico' | 'paddle' | ...
  provider_ref        TEXT,               -- provider's subscription id
  plan                TEXT NOT NULL,
  status              TEXT NOT NULL,      -- see src/entitlements.ts
  current_period_end  INTEGER,
  cancel_at_period_end INTEGER NOT NULL DEFAULT 0,
  updated_at          INTEGER NOT NULL
);

-- Webhook idempotency: each provider event is applied at most once.
CREATE TABLE webhook_events (
  provider    TEXT NOT NULL,
  event_id    TEXT NOT NULL,
  received_at INTEGER NOT NULL,
  PRIMARY KEY (provider, event_id)
);

-- Which legal texts (by version) the user saw/accepted and when.
-- e.g. 'kvkk_aydinlatma', 'mesafeli_satis', 'on_bilgilendirme', 'cayma_istisnasi'
CREATE TABLE consents (
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind        TEXT NOT NULL,
  version     TEXT NOT NULL,
  accepted_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, kind, version)
);
