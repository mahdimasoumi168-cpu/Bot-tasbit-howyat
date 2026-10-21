-- Migration 0002: bridge fields needed by the existing Python bot's business features.
-- Run once after schema.sql. This migration is intentionally versioned; do not run twice.
ALTER TABLE payments ADD COLUMN receipt_file_id TEXT;
ALTER TABLE payments ADD COLUMN receipt_type TEXT NOT NULL DEFAULT 'photo';
ALTER TABLE payments ADD COLUMN provider_metadata_json TEXT NOT NULL DEFAULT '{}';

ALTER TABLE wallet_topups ADD COLUMN receipt_type TEXT NOT NULL DEFAULT 'photo';
ALTER TABLE wallet_transactions ADD COLUMN order_id INTEGER REFERENCES orders(id);
ALTER TABLE wallet_transactions ADD COLUMN topup_id INTEGER REFERENCES wallet_topups(id);

ALTER TABLE documents ADD COLUMN document_type TEXT NOT NULL DEFAULT 'attachment';
ALTER TABLE documents ADD COLUMN review_status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE documents ADD COLUMN reviewed_by_telegram_id TEXT;
ALTER TABLE documents ADD COLUMN reviewed_at TEXT;

ALTER TABLE tickets ADD COLUMN order_id INTEGER REFERENCES orders(id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tickets_order_unique ON tickets(order_id) WHERE order_id IS NOT NULL;

ALTER TABLE ticket_messages ADD COLUMN sender_type TEXT NOT NULL DEFAULT 'user';
ALTER TABLE ticket_messages ADD COLUMN content_type TEXT NOT NULL DEFAULT 'text';
ALTER TABLE ticket_messages ADD COLUMN text TEXT;
ALTER TABLE ticket_messages ADD COLUMN file_id TEXT;

ALTER TABLE orders ADD COLUMN price_snapshot_toman INTEGER;
ALTER TABLE audit_logs ADD COLUMN order_id INTEGER REFERENCES orders(id);

CREATE TABLE IF NOT EXISTS companions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  full_name TEXT NOT NULL,
  mobile TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_companions_order ON companions(order_id);

CREATE TABLE IF NOT EXISTS operators (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id TEXT NOT NULL UNIQUE,
  display_name TEXT,
  role TEXT NOT NULL DEFAULT 'operator',
  permissions_json TEXT NOT NULL DEFAULT '{}',
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_operators_active ON operators(active);

CREATE TABLE IF NOT EXISTS discount_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL DEFAULT 'percent',
  value INTEGER NOT NULL CHECK(value >= 0),
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  max_uses INTEGER,
  used_count INTEGER NOT NULL DEFAULT 0,
  expires_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_discount_codes_active ON discount_codes(active);

CREATE TABLE IF NOT EXISTS variza_payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL,
  order_id INTEGER REFERENCES orders(id),
  topup_id INTEGER REFERENCES wallet_topups(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  amount_toman INTEGER NOT NULL CHECK(amount_toman > 0),
  pay_url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  attempt_code TEXT,
  expires_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paid_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_variza_payments_status ON variza_payments(status);

CREATE TABLE IF NOT EXISTS rialit_payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL,
  order_id INTEGER REFERENCES orders(id),
  topup_id INTEGER REFERENCES wallet_topups(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  amount_toman INTEGER NOT NULL CHECK(amount_toman > 0),
  vpn_months INTEGER,
  vpn_gigabytes INTEGER,
  pay_url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paid_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_rialit_payments_status ON rialit_payments(status);
