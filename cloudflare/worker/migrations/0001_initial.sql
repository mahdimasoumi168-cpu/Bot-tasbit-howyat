PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id INTEGER NOT NULL UNIQUE,
  first_name TEXT,
  last_name TEXT,
  username TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS services (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  price_toman INTEGER NOT NULL DEFAULT 0,
  enabled INTEGER NOT NULL DEFAULT 1,
  description TEXT
);

CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  public_id TEXT NOT NULL UNIQUE,
  user_id INTEGER NOT NULL REFERENCES users(id),
  service_id INTEGER NOT NULL REFERENCES services(id),
  price_snapshot_toman INTEGER,
  status TEXT NOT NULL DEFAULT 'draft',
  data_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  amount_toman INTEGER NOT NULL,
  receipt_file_id TEXT,
  receipt_type TEXT NOT NULL DEFAULT 'photo',
  status TEXT NOT NULL DEFAULT 'pending',
  source_rialit_payment_id INTEGER UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Kept for historical imports only. No active Variza routes are implemented.
CREATE TABLE IF NOT EXISTS variza_payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL,
  order_id INTEGER REFERENCES orders(id),
  topup_id INTEGER,
  user_id INTEGER NOT NULL REFERENCES users(id),
  amount_toman INTEGER NOT NULL,
  pay_url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  attempt_code TEXT,
  expires_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paid_at TEXT
);

CREATE TABLE IF NOT EXISTS rialit_payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT UNIQUE,
  provider_order_id TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL,
  order_id INTEGER REFERENCES orders(id),
  topup_id INTEGER,
  user_id INTEGER NOT NULL REFERENCES users(id),
  amount_toman INTEGER NOT NULL,
  payer_amount_toman INTEGER,
  payer_fee_toman INTEGER NOT NULL DEFAULT 0,
  vpn_months INTEGER,
  vpn_gigabytes INTEGER,
  pay_url TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paid_at TEXT,
  delivered_at TEXT
);

CREATE TABLE IF NOT EXISTS wallets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
  balance_toman INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wallet_topups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  amount_toman INTEGER NOT NULL,
  receipt_file_id TEXT,
  receipt_type TEXT NOT NULL DEFAULT 'photo',
  status TEXT NOT NULL DEFAULT 'awaiting_receipt',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS wallet_transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  amount_toman INTEGER NOT NULL,
  balance_after_toman INTEGER NOT NULL,
  kind TEXT NOT NULL,
  description TEXT NOT NULL,
  order_id INTEGER REFERENCES orders(id),
  topup_id INTEGER REFERENCES wallet_topups(id),
  source_rialit_payment_id INTEGER UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discount_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL DEFAULT 'percent',
  value INTEGER NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  max_uses INTEGER,
  used_count INTEGER NOT NULL DEFAULT 0,
  expires_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  document_type TEXT NOT NULL,
  telegram_file_id TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending',
  reviewed_by_telegram_id INTEGER,
  reviewed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id),
  status TEXT NOT NULL DEFAULT 'open',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ticket_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticket_id INTEGER NOT NULL REFERENCES tickets(id),
  sender_type TEXT NOT NULL,
  sender_telegram_id INTEGER NOT NULL,
  content_type TEXT NOT NULL DEFAULT 'text',
  text TEXT,
  file_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT NOT NULL UNIQUE,
  value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_telegram_id INTEGER,
  action TEXT NOT NULL,
  order_id INTEGER REFERENCES orders(id),
  details_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  full_name TEXT NOT NULL,
  mobile TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operators (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id INTEGER NOT NULL UNIQUE,
  display_name TEXT,
  role TEXT NOT NULL DEFAULT 'operator',
  permissions_json TEXT NOT NULL DEFAULT '{}',
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS telegram_updates (
  update_id INTEGER PRIMARY KEY,
  received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rialit_webhook_events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  payment_token TEXT,
  received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at TEXT
);

CREATE TABLE IF NOT EXISTS wallet_credit_events (
  payment_id INTEGER PRIMARY KEY REFERENCES rialit_payments(id),
  credited_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vpn_provisioning_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rialit_payment_id INTEGER NOT NULL UNIQUE REFERENCES rialit_payments(id),
  telegram_user_id INTEGER NOT NULL,
  months INTEGER NOT NULL,
  gigabytes INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  provider_subscription_id TEXT,
  subscription_url TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_user_created ON orders(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status_created ON orders(status, created_at);
CREATE INDEX IF NOT EXISTS idx_documents_order ON documents(order_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket ON ticket_messages(ticket_id, created_at);
CREATE INDEX IF NOT EXISTS idx_rialit_status_created ON rialit_payments(status, created_at);
CREATE INDEX IF NOT EXISTS idx_rialit_order ON rialit_payments(order_id);
CREATE INDEX IF NOT EXISTS idx_wallet_tx_user_created ON wallet_transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_topups_status ON wallet_topups(status, created_at);
