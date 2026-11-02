interface Env {
  DB: D1Database;
  ASSETS: Fetcher;
  BOT_TOKEN: string;
  RIALIT_API_KEY: string;
  API_VPN?: string;
  RIALIT_API_BASE_URL?: string;
  RIALIT_WEBHOOK_IPS?: string;
  PAYMENT_FEE_PERCENT?: string;
  APP_NAME?: string;
  ADMIN_IDS?: string;
}

type TelegramUser = {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
};

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

const text = (value: string, status = 200) =>
  new Response(value, { status, headers: { "content-type": "text/plain; charset=utf-8" } });

function toHex(bytes: ArrayBuffer): string {
  return [...new Uint8Array(bytes)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function verifyTelegramInitData(initData: string, botToken: string): Promise<TelegramUser | null> {
  if (!initData || !botToken) return null;
  const params = new URLSearchParams(initData);
  const receivedHash = params.get("hash");
  const authDate = Number(params.get("auth_date") || 0);
  if (!receivedHash || !authDate || Math.abs(Date.now() / 1000 - authDate) > 86_400) return null;

  const checkString = [...params.entries()]
    .filter(([key]) => key !== "hash")
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}=${value}`)
    .join("\n");

  const encoder = new TextEncoder();
  const initialKey = await crypto.subtle.importKey(
    "raw", encoder.encode(botToken), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const secret = await crypto.subtle.sign("HMAC", initialKey, encoder.encode("WebAppData"));
  const validationKey = await crypto.subtle.importKey(
    "raw", secret, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const calculated = toHex(await crypto.subtle.sign("HMAC", validationKey, encoder.encode(checkString)));
  if (calculated.length !== receivedHash.length) return null;
  let mismatch = 0;
  for (let i = 0; i < calculated.length; i++) mismatch |= calculated.charCodeAt(i) ^ receivedHash.charCodeAt(i);
  if (mismatch !== 0) return null;

  try {
    return JSON.parse(params.get("user") || "null") as TelegramUser | null;
  } catch {
    return null;
  }
}

async function miniAppUser(request: Request, env: Env): Promise<TelegramUser | null> {
  return verifyTelegramInitData(
    request.headers.get("x-telegram-init-data") || "",
    env.BOT_TOKEN
  );
}

async function ensureUser(db: D1Database, user: TelegramUser): Promise<number> {
  await db.prepare(`
    INSERT INTO users (telegram_id, first_name, last_name, username)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(telegram_id) DO UPDATE SET
      first_name = excluded.first_name,
      last_name = excluded.last_name,
      username = excluded.username,
      updated_at = CURRENT_TIMESTAMP
  `).bind(user.id, user.first_name || null, user.last_name || null, user.username || null).run();

  const row = await db.prepare("SELECT id FROM users WHERE telegram_id = ?")
    .bind(user.id).first<{ id: number }>();
  if (!row) throw new Error("user_upsert_failed");
  return row.id;
}

async function telegram(env: Env, method: string, payload: Record<string, unknown>): Promise<any> {
  const response = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || !(body as any)?.ok) {
    console.error("Telegram API failure", method, response.status);
    throw new Error("telegram_api_failed");
  }
  return (body as any).result;
}

function homeKeyboard(appUrl: string) {
  return {
    inline_keyboard: [
      [{ text: "🚀 ورود به مینی‌اپ کمک‌یار مهاجر", web_app: { url: appUrl } }],
      [
        { text: "🧾 خدمات دفتر نت‌یار مهاجر", callback_data: "menu:services" },
        { text: "💰 اعتبار من", callback_data: "menu:wallet" },
      ],
      [
        { text: "📂 پرونده‌های من", callback_data: "menu:orders" },
        { text: "🎧 پشتیبانی", callback_data: "menu:support" },
      ],
    ],
  };
}

async function handleTelegram(request: Request, env: Env): Promise<Response> {
  const expected = env.TELEGRAM_WEBHOOK_SECRET;
  const supplied = request.headers.get("x-telegram-bot-api-secret-token");
  if (!expected || supplied !== expected) return text("forbidden", 403);

  const update = await request.json<any>().catch(() => null);
  if (!update || !Number.isInteger(update.update_id)) return json({ ok: false }, 400);

  const inserted = await env.DB.prepare(
    "INSERT OR IGNORE INTO telegram_updates(update_id) VALUES (?)"
  ).bind(update.update_id).run();
  if ((inserted.meta?.changes || 0) === 0) return json({ ok: true, duplicate: true });

  const message = update.message;
  if (message?.from?.id) {
    const user = message.from as TelegramUser;
    await ensureUser(env.DB, user);
    const appUrl = new URL("/app/", request.url).toString();
    const greeting = user.first_name ? `سلام ${user.first_name} عزیز 🌷\n\n` : "سلام و خوش آمدید 🌷\n\n";
    await telegram(env, "sendMessage", {
      chat_id: message.chat.id,
      text: greeting +
        "به «کمک‌یار مهاجر» خوش آمدید.\n" +
        "از اینجا می‌توانید خدمات دفتر، پرونده‌ها و اعتبار خود را مدیریت کنید.",
      reply_markup: homeKeyboard(appUrl),
    });
  }

  const callback = update.callback_query;
  if (callback?.id && callback?.from?.id) {
    await telegram(env, "answerCallbackQuery", { callback_query_id: callback.id });
    const chatId = callback.message?.chat?.id;
    if (chatId) {
      const appUrl = new URL("/app/", request.url).toString();
      const label: Record<string, string> = {
        "menu:home": "صفحه اصلی کمک‌یار مهاجر",
        "menu:services": "برای ثبت درخواست خدمت، مینی‌اپ را باز کنید.",
        "menu:wallet": "برای مشاهده موجودی و افزایش اعتبار، مینی‌اپ را باز کنید.",
        "menu:orders": "برای مشاهده و پیگیری پرونده‌ها، مینی‌اپ را باز کنید.",
        "menu:support": "برای ارتباط با پشتیبانی، درخواست خود را در همین گفتگو ارسال کنید.",
      };
      await telegram(env, "sendMessage", {
        chat_id: chatId,
        text: label[String(callback.data)] || "برای ادامه، مینی‌اپ را باز کنید.",
        reply_markup: homeKeyboard(appUrl),
      });
    }
  }
  return json({ ok: true });
}

async function bootstrap(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const userId = await ensureUser(env.DB, user);
  const [services, wallet, orders, settings] = await Promise.all([
    env.DB.prepare("SELECT id, code, name, price_toman, description FROM services WHERE enabled = 1 ORDER BY id").all(),
    env.DB.prepare("SELECT balance_toman FROM wallets WHERE user_id = ?").bind(userId).first<{ balance_toman: number }>(),
    env.DB.prepare(`
      SELECT o.id, o.public_id, o.status, o.price_snapshot_toman, o.created_at, s.name AS service_name
      FROM orders o JOIN services s ON s.id = o.service_id
      WHERE o.user_id = ? ORDER BY o.id DESC LIMIT 20
    `).bind(userId).all(),
    env.DB.prepare("SELECT key, value FROM settings WHERE key IN ('card_number','card_holder','card_bank','support_username')").all(),
  ]);
  return json({
    ok: true,
    user: { id: user.id, first_name: user.first_name, last_name: user.last_name },
    services: services.results || [],
    wallet: wallet || { balance_toman: 0 },
    orders: orders.results || [],
    settings: Object.fromEntries((settings.results || []).map((x: any) => [x.key, x.value])),
    payment: { rialit_fee_percent: Number(env.PAYMENT_FEE_PERCENT || "12"), min_toman: 50_000, max_toman: 10_000_000 },
  });
}

async function createOrder(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json<any>().catch(() => null);
  const serviceCode = String(body?.service_code || "");
  const formData = body?.form_data;
  if (!serviceCode || !formData || typeof formData !== "object" || Array.isArray(formData)) {
    return json({ ok: false, error: "invalid_request" }, 400);
  }
  const userId = await ensureUser(env.DB, user);
  const service = await env.DB.prepare(
    "SELECT id, price_toman FROM services WHERE code = ? AND enabled = 1"
  ).bind(serviceCode).first<{ id: number; price_toman: number }>();
  if (!service) return json({ ok: false, error: "service_unavailable" }, 404);

  const created = await env.DB.prepare(`
    INSERT INTO orders (public_id, user_id, service_id, price_snapshot_toman, status, data_json)
    VALUES ('', ?, ?, ?, 'waiting_payment', ?)
    RETURNING id
  `).bind(userId, service.id, service.price_toman, JSON.stringify(formData)).first<{ id: number }>();
  if (!created) return json({ ok: false, error: "order_create_failed" }, 500);
  const publicId = `YM-${String(created.id).padStart(7, "0")}`;
  await env.DB.prepare("UPDATE orders SET public_id = ? WHERE id = ?")
    .bind(publicId, created.id).run();
  return json({ ok: true, order_id: created.id, public_id: publicId, amount_toman: service.price_toman });
}

async function createRialitPayment(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json<any>().catch(() => null);
  const orderId = Number(body?.order_id);
  if (!Number.isSafeInteger(orderId) || orderId < 1) return json({ ok: false, error: "invalid_order" }, 400);
  const userId = await ensureUser(env.DB, user);
  const order = await env.DB.prepare(`
    SELECT o.id, o.public_id, o.price_snapshot_toman, o.status
    FROM orders o WHERE o.id = ? AND o.user_id = ?
  `).bind(orderId, userId).first<any>();
  if (!order) return json({ ok: false, error: "order_not_found" }, 404);
  if (order.status !== "waiting_payment") return json({ ok: false, error: "order_not_payable" }, 409);

  const amount = Number(order.price_snapshot_toman || 0);
  if (amount < 50_000 || amount > 10_000_000) {
    return json({ ok: false, error: "rialit_amount_out_of_range", card_transfer_available: true }, 400);
  }
  if (!env.RIALIT_API_KEY) return json({ ok: false, error: "rialit_not_configured" }, 503);

  const providerOrderId = `mohajer-order-${order.id}`;
  const existing = await env.DB.prepare(
    "SELECT token, pay_url, payer_amount_toman, payer_fee_toman FROM rialit_payments WHERE provider_order_id = ? AND status = 'pending'"
  ).bind(providerOrderId).first<any>();
  if (existing?.pay_url) {
    return json({ ok: true, pay_url: existing.pay_url, payer_amount_toman: existing.payer_amount_toman, payer_fee_toman: existing.payer_fee_toman });
  }

  await env.DB.prepare(`
    INSERT OR IGNORE INTO rialit_payments
      (provider_order_id, kind, order_id, user_id, amount_toman, status)
    VALUES (?, 'order', ?, ?, ?, 'pending')
  `).bind(providerOrderId, order.id, userId, amount).run();

  const apiBase = (env.RIALIT_API_BASE_URL || "https://api.rialit.io/api/v1").replace(/\/$/, "");
  const payload = { amount, order_id: providerOrderId, payer_id: user.id };
  let response: Response;
  try {
    response = await fetch(`${apiBase}/send`, {
      method: "POST",
      headers: { authorization: `Bearer ${env.RIALIT_API_KEY}`, "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(25_000),
    });
  } catch {
    return json({ ok: false, error: "rialit_network_error", retry_same_order: true }, 502);
  }
  const result = await response.json<any>().catch(() => ({}));
  if (![200, 201].includes(response.status)) {
    const error = String(result?.error || "");
    if (response.status === 401) return json({ ok: false, error: "rialit_key_invalid" }, 502);
    if (response.status === 403 && error === "IP not allowed") return json({ ok: false, error: "rialit_outbound_ip_not_allowed" }, 502);
    if (response.status === 403) return json({ ok: false, error: "rialit_merchant_inactive" }, 502);
    if (response.status === 409) return json({ ok: false, error: "rialit_order_id_conflict" }, 409);
    if (response.status === 429 || response.status >= 500) return json({ ok: false, error: "rialit_retry_later", retry_same_order: true }, 503);
    return json({ ok: false, error: "rialit_request_invalid", detail: error }, 400);
  }

  const token = String(result?.token || "");
  const payerAmount = Number(result?.payer_amount);
  const payerFee = Number(result?.payer_fee);
  if (!/^[A-Za-z0-9]{1,64}$/.test(token) || !Number.isSafeInteger(payerAmount) || !Number.isSafeInteger(payerFee) || Number(result?.amount) !== amount) {
    return json({ ok: false, error: "rialit_invalid_response" }, 502);
  }
  const payUrl = `https://pay.rialit.io/v1/${token}`;
  await env.DB.prepare(`
    UPDATE rialit_payments
    SET token = ?, pay_url = ?, payer_amount_toman = ?, payer_fee_toman = ?
    WHERE provider_order_id = ? AND status = 'pending'
  `).bind(token, payUrl, payerAmount, payerFee, providerOrderId).run();

  const expectedPayerAmount = Math.ceil((amount * 100 / 88) / 50) * 50;
  const feeMatchesTwelvePercent = payerAmount === expectedPayerAmount;
  return json({
    ok: true,
    pay_url: payUrl,
    amount_toman: amount,
    payer_amount_toman: payerAmount,
    payer_fee_toman: payerFee,
    fee_percent: 12,
    fee_configuration_matches: feeMatchesTwelvePercent,
  });
}

async function handleRialitWebhook(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
  const allowed = new Set((env.RIALIT_WEBHOOK_IPS || "").split(",").map((x) => x.trim()).filter(Boolean));
  const sourceIp = request.headers.get("cf-connecting-ip") || "";
  if (!sourceIp || !allowed.has(sourceIp)) return json({ ok: false, error: "source_ip_not_allowed" }, 403);

  const eventHeader = request.headers.get("x-rialit-event") || "";
  const deliveryHeader = request.headers.get("x-rialit-delivery") || "";
  const payload = await request.json<any>().catch(() => null);
  if (!payload || typeof payload !== "object") return json({ ok: false, error: "invalid_payload" }, 400);
  const eventId = String(payload.event_id || "");
  const eventType = String(payload.type || "");
  if (!eventId || eventId !== deliveryHeader || eventType !== eventHeader) {
    return json({ ok: false, error: "invalid_event_headers" }, 400);
  }
  if (eventType === "webhook.test") return json({ ok: true });
  if (!["payment.paid", "payment.expired", "payment.cancelled"].includes(eventType)) {
    return json({ ok: false, error: "unsupported_event" }, 400);
  }

  const token = String(payload.data?.id || "");
  if (!/^[A-Za-z0-9]{1,64}$/.test(token)) return json({ ok: false, error: "invalid_payment_token" }, 400);
  const duplicate = await env.DB.prepare("SELECT event_id FROM rialit_webhook_events WHERE event_id = ?")
    .bind(eventId).first();
  if (duplicate) return json({ ok: true, duplicate: true });

  const payment = await env.DB.prepare(
    "SELECT * FROM rialit_payments WHERE token = ?"
  ).bind(token).first<any>();
  if (!payment) return json({ ok: true, ignored: true });

  let verifiedResponse: Response;
  try {
    verifiedResponse = await fetch(
      `${(env.RIALIT_API_BASE_URL || "https://api.rialit.io/api/v1").replace(/\/$/, "")}/status/${token}`,
      {
        headers: { authorization: `Bearer ${env.RIALIT_API_KEY}`, accept: "application/json" },
        signal: AbortSignal.timeout(8_000),
      }
    );
  } catch {
    return json({ ok: false, error: "rialit_verification_unavailable" }, 503);
  }
  if (!verifiedResponse.ok) return json({ ok: false, error: "rialit_verification_unavailable" }, 503);
  const verified = await verifiedResponse.json<any>().catch(() => ({}));
  const status = String(verified?.status || verified?.data?.status || "");
  const verifiedAmount = Number(verified?.amount ?? verified?.data?.amount);
  const verifiedPayer = Number(verified?.payer_id ?? verified?.data?.payer_id);
  const verifiedOrderId = String(verified?.order_id ?? verified?.data?.order_id ?? "");
  if (status === "paid" && (
    verifiedAmount !== Number(payment.amount_toman) ||
    verifiedPayer !== Number(payment.user_id ? payload.data?.payer_id : 0) ||
    verifiedOrderId !== payment.provider_order_id
  )) {
    await env.DB.prepare(
      "INSERT OR IGNORE INTO rialit_webhook_events(event_id,event_type,payment_token,processed_at) VALUES(?,?,?,CURRENT_TIMESTAMP)"
    ).bind(eventId, eventType, token).run();
    return json({ ok: true, rejected: "payment_details_mismatch" });
  }

  if (!["pending", "paid", "expired", "cancelled"].includes(status)) {
    return json({ ok: false, error: "unknown_verified_status" }, 503);
  }

  const statements: D1PreparedStatement[] = [
    env.DB.prepare("INSERT OR IGNORE INTO rialit_webhook_events(event_id,event_type,payment_token,processed_at) VALUES(?,?,?,CURRENT_TIMESTAMP)")
      .bind(eventId, eventType, token),
    env.DB.prepare("UPDATE rialit_payments SET status = ?, paid_at = CASE WHEN ? = 'paid' THEN CURRENT_TIMESTAMP ELSE paid_at END WHERE id = ? AND changes() = 1 AND status != 'paid'")
      .bind(status, status, payment.id),
  ];

  if (status === "paid" && payment.kind === "order" && payment.order_id) {
    statements.push(
      env.DB.prepare("UPDATE orders SET status = 'payment_approved', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status IN ('waiting_payment','waiting_receipt_review') AND changes() = 1")
        .bind(payment.order_id),
      env.DB.prepare("INSERT OR IGNORE INTO payments(order_id,amount_toman,receipt_file_id,receipt_type,status,source_rialit_payment_id) SELECT ?,?,NULL,'rialit','approved',? WHERE changes() = 1")
        .bind(payment.order_id, payment.amount_toman, payment.id)
    );
  }

  if (status === "paid" && payment.kind === "topup" && payment.topup_id) {
    statements.push(
      env.DB.prepare("UPDATE wallet_topups SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP WHERE id = ? AND status IN ('awaiting_receipt','waiting_receipt_review') AND changes() = 1")
        .bind(payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO wallets(user_id,balance_toman) SELECT user_id,0 FROM wallet_topups WHERE id = ? AND status = 'approved'")
        .bind(payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO wallet_credit_events(payment_id) SELECT ? WHERE changes() = 1")
        .bind(payment.id),
      env.DB.prepare("UPDATE wallets SET balance_toman = balance_toman + ? WHERE user_id = (SELECT user_id FROM wallet_topups WHERE id = ?) AND changes() = 1")
        .bind(payment.amount_toman, payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO wallet_transactions(user_id,amount_toman,balance_after_toman,kind,description,topup_id,source_rialit_payment_id) SELECT w.user_id,?,w.balance_toman,'topup',?, ?, ? FROM wallets w JOIN wallet_topups t ON t.user_id = w.user_id WHERE t.id = ? AND changes() = 1")
        .bind(payment.amount_toman, `افزایش اعتبار ریالت #${payment.topup_id}`, payment.topup_id, payment.id, payment.topup_id),
    );
  }

  await env.DB.batch(statements);
  if (status === "paid" && payment.kind === "vpn") {
    // Provider request payload must be validated against the authenticated Gozarban OpenAPI schema before activation is enabled.
    await env.DB.prepare(`
      INSERT OR IGNORE INTO vpn_provisioning_jobs
        (rialit_payment_id, telegram_user_id, months, gigabytes, status)
      VALUES (?, ?, ?, ?, 'blocked_waiting_api_schema')
    `).bind(payment.id, Number(payload.data?.payer_id || 0), Number(payment.vpn_months || 0), Number(payment.vpn_gigabytes || 0)).run();
  }
  if (status === "paid") {
    ctx.waitUntil(telegram(env, "sendMessage", {
      chat_id: payment.user_telegram_id || payload.data?.payer_id,
      text: "✅ پرداخت شما توسط ریالت‌پی تأیید شد. برای مشاهده وضعیت پرونده، مینی‌اپ را باز کنید.",
    }).catch(() => undefined));
  }
  return json({ ok: true, action: status });
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/health") return json({ ok: true, service: "help-yar-mohajer", platform: "cloudflare-workers" });
    if (url.pathname === "/webhooks/telegram" && request.method === "POST") return handleTelegram(request, env);
    if (url.pathname === "/webhooks/rialit" && request.method === "POST") return handleRialitWebhook(request, env, ctx);
    if (url.pathname === "/api/miniapp/bootstrap" && request.method === "GET") return bootstrap(request, env);
    if (url.pathname === "/api/miniapp/orders" && request.method === "POST") return createOrder(request, env);
    if (url.pathname === "/api/miniapp/payments/rialit" && request.method === "POST") return createRialitPayment(request, env);
    if (url.pathname === "/app" || url.pathname === "/app/") {
      const assetUrl = new URL("/index.html", request.url);
      return env.ASSETS.fetch(new Request(assetUrl, request));
    }
    if (url.pathname.startsWith("/api/")) return json({ ok: false, error: "not_found" }, 404);
    return env.ASSETS.fetch(request);
  },
};
