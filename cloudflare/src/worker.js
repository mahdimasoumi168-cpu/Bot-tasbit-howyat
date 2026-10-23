import { MINIAPP_HTML } from "./miniapp.js";


const MINIAPP_SERVICE_FALLBACK = [
  { code: "identity", name: "تثبیت هویت", description: "بررسی مدارک و درخواست تثبیت هویت" },
  { code: "khodnevis", name: "کد رهگیری خودنویس", description: "ثبت درخواست دریافت کد رهگیری" },
  { code: "fida", name: "ثبت‌نام کد فیدا غیرحضوری", description: "ثبت اطلاعات برای دریافت کد فیدا" },
  { code: "dolatman_login", name: "رفع مشکل ورود به درگاه دولت من", description: "بررسی مشکل ورود و دسترسی" },
  { code: "student_screening", name: "آزمون غربالگری دانش‌آموزان", description: "ثبت اطلاعات دانش‌آموز" },
  { code: "other_service", name: "درخواست خدمات دیگر", description: "شرح خدمت موردنیاز" }
];

function bytesToHex(bytes) {
  return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, "0")).join("");
}

async function hmacSha256(keyBytes, messageBytes) {
  const key = await crypto.subtle.importKey("raw", keyBytes, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return new Uint8Array(await crypto.subtle.sign("HMAC", key, messageBytes));
}

async function verifyTelegramInitData(initData, botToken) {
  botToken = String(botToken || "").trim();
  if (!initData) return { user: null, reason: "init_data_missing" };
  if (!botToken) return { user: null, reason: "bot_token_missing" };
  if (initData.length > 8192) return { user: null, reason: "init_data_too_long" };
  const params = new URLSearchParams(initData);
  const receivedHash = params.get("hash");
  if (!receivedHash || !/^[a-f0-9]{64}$/i.test(receivedHash)) return { user: null, reason: "hash_missing_or_invalid" };
  params.delete("hash");
  const pairs = Array.from(params.entries()).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  const checkString = pairs.map(([k, v]) => k + "=" + v).join("\n");
  // Telegram Mini Apps: secret_key = HMAC_SHA256(key=bot_token, message="WebAppData").
  // The bot token is the HMAC key; reversing these inputs rejects valid initData.
  const secret = await hmacSha256(new TextEncoder().encode("WebAppData"), new TextEncoder().encode(botToken));
  const expectedHash = bytesToHex(await hmacSha256(secret, new TextEncoder().encode(checkString)));
  if (expectedHash.length !== receivedHash.length) return { user: null, reason: "hash_mismatch" };
  let diff = 0;
  for (let i = 0; i < expectedHash.length; i++) diff |= expectedHash.charCodeAt(i) ^ receivedHash.toLowerCase().charCodeAt(i);
  if (diff !== 0) return { user: null, reason: "hash_mismatch" };
  const authDate = Number(params.get("auth_date"));
  const now = Math.floor(Date.now() / 1000);
  if (!Number.isFinite(authDate) || authDate > now + 60) return { user: null, reason: "auth_date_invalid" };
  if (now - authDate > 86400) return { user: null, reason: "init_data_expired" };
  let user;
  try { user = JSON.parse(params.get("user") || "null"); } catch { return { user: null, reason: "user_invalid" }; }
  if (!user || !Number.isSafeInteger(user.id)) return { user: null, reason: "user_invalid" };
  return { user, reason: null };
}

async function authorizeMiniApp(request, env) {
  let body;
  try { body = await request.json(); } catch { return { error: "invalid_json" }; }
  const verified = await verifyTelegramInitData(body?.initData, env.BOT_TOKEN);
  if (!verified.user) return { error: verified.reason || "invalid_telegram_session" };
  const user = verified.user;
  const adminIds = String(env.ADMIN_IDS || "").split(",").map(v => v.trim()).filter(Boolean);
  return { user, isAdmin: adminIds.includes(String(user.id)), body };
}

async function miniAppApi(request, env, path) {
  const auth = await authorizeMiniApp(request, env);
  if (auth.error) return json({ ok: false, error: auth.error }, 401);
  if (path === "/api/miniapp/me") {
    if (env.DB) {
      try { await ensureUser(env, auth.user); }
      catch (error) { console.error("miniapp_user_sync_failed", error?.message || "unknown_error"); return json({ ok: false, error: "database_not_ready" }, 503); }
    }
    return json({ ok: true, user: { id: auth.user.id, first_name: auth.user.first_name || "", last_name: auth.user.last_name || "", username: auth.user.username || "" }, isAdmin: auth.isAdmin, database_bound: Boolean(env.DB) });
  }
  if (path === "/api/miniapp/services") {
    if (env.DB) {
      try {
        const rows = await env.DB.prepare("SELECT code,name,description,enabled FROM services ORDER BY rowid").all();
        if (rows.results?.length) return json({ ok: true, services: rows.results.filter(s => s.enabled).map(s => ({ code: s.code, name: s.name, description: s.description || "" })) });
      } catch (error) { console.error("miniapp_services_query_failed", error?.message || "unknown_error"); }
    }
    return json({ ok: true, services: MINIAPP_SERVICE_FALLBACK, mode: "preview" });
  }
  if (path === "/api/miniapp/select-service") {
    const code = auth.body?.code;
    if (typeof code !== "string" || !Object.hasOwn(SERVICE_LABELS, code)) return json({ ok: false, error: "invalid_service" }, 400);
    if (!env.DB) return json({ ok: false, error: "database_not_ready" }, 503);
    const service = await env.DB.prepare("SELECT code,enabled,price_toman FROM services WHERE code=?").bind(code).first();
    if (!service || !service.enabled || !Number.isSafeInteger(service.price_toman) || service.price_toman <= 0) {
      return json({ ok: false, error: "service_not_ready" }, 409);
    }
    await showRules(env, auth.user.id, code, auth.user.id);
    return json({ ok: true });
  }
  if (path === "/api/miniapp/orders") {
    if (!env.DB) return json({ ok: false, error: "database_not_ready" }, 503);
    try {
      const u = await env.DB.prepare("SELECT id FROM users WHERE telegram_id=?").bind(String(auth.user.id)).first();
      if (!u) return json({ ok: true, orders: [] });
      const result = await env.DB.prepare("SELECT public_id,service_code,status,created_at FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 30").bind(u.id).all();
      return json({ ok: true, orders: result.results || [] });
    } catch (error) { console.error("miniapp_orders_query_failed", error?.message || "unknown_error"); return json({ ok: false, error: "database_not_ready" }, 503); }
  }
  return json({ ok: false, error: "not_found" }, 404);
}

const SERVICE_LABELS = {
  identity: "🪪 تثبیت هویت",
  khodnevis: "📝 کد رهگیری خودنویس",
  fida: "🪪 ثبت‌نام کد فیدا غیرحضوری",
  dolatman_login: "🔐 رفع مشکل ورود به درگاه دولت من",
  student_screening: "🎒 آزمون غربالگری دانش‌آموزان",
  other_service: "🧾 درخواست خدمات دیگر",
};

const HOME_KEYBOARD = {
  inline_keyboard: [
    [{ text: "🚀 باز کردن مینی‌اپ", web_app: { url: "https://bot-tasbit-howyat.mahdi-masoumi168.workers.dev/app" } }],
    [{ text: "🧾 خدمات دفتر نت‌یار مهاجر", callback_data: "menu:services" }],
    [{ text: "🔐 خرید VPN / فیلترشکن", callback_data: "vpn:start" }],
    [{ text: "💰 اعتبار من", callback_data: "menu:wallet" }, { text: "👤 حساب من", callback_data: "menu:account" }],
    [{ text: "📋 پیگیری درخواست‌ها", callback_data: "menu:tracking" }],
    [{ text: "🔄 شروع مجدد", callback_data: "menu:restart" }, { text: "📞 پشتیبانی", callback_data: "menu:support" }],
  ],
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

async function telegram(env, method, payload) {
  const botToken = String(env.BOT_TOKEN || "").trim();
  if (!botToken) throw new Error("BOT_TOKEN_missing");
  const response = await fetch(`https://api.telegram.org/bot${botToken}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || body.ok !== true) {
    // Never log the token or full request URL: Telegram API URLs contain the token.
    console.error("telegram_api_error", method, response.status, body.description || "unknown_error");
    throw new Error(`telegram_api_error_${method}`);
  }
  return body.result;
}

async function sendMessage(env, chatId, text, replyMarkup) {
  const payload = { chat_id: chatId, text };
  if (replyMarkup) payload.reply_markup = replyMarkup;
  return telegram(env, "sendMessage", payload);
}

async function answerCallback(env, callbackId, text) {
  try { await telegram(env, "answerCallbackQuery", { callback_query_id: callbackId, text }); }
  catch (error) { console.error("callback_answer_failed", error.message); }
}

async function ensureUser(env, from) {
  if (!env.DB) return null;
  await env.DB.prepare(`
    INSERT INTO users(telegram_id, username, first_name, last_name)
    VALUES(?, ?, ?, ?)
    ON CONFLICT(telegram_id) DO UPDATE SET
      username=excluded.username, first_name=excluded.first_name,
      last_name=excluded.last_name, updated_at=CURRENT_TIMESTAMP
  `).bind(String(from.id), from.username || null, from.first_name || null, from.last_name || null).run();
  return env.DB.prepare("SELECT * FROM users WHERE telegram_id=?").bind(String(from.id)).first();
}

async function saveState(env, telegramId, state, data = {}) {
  if (!env.DB) return;
  await env.DB.prepare("UPDATE users SET state=?, state_json=?, updated_at=CURRENT_TIMESTAMP WHERE telegram_id=?")
    .bind(state, JSON.stringify(data), String(telegramId)).run();
}

async function getState(env, telegramId) {
  if (!env.DB) return { state: "idle", data: {} };
  const user = await env.DB.prepare("SELECT state,state_json FROM users WHERE telegram_id=?").bind(String(telegramId)).first();
  let data = {};
  try { data = JSON.parse(user?.state_json || "{}"); } catch {}
  return { state: user?.state || "idle", data };
}

async function showServices(env, chatId) {
  // Keep every known service visible even while prices/activation are being migrated.
  // A disabled service is shown but its rules handler prevents order/payment creation.
  let services = Object.entries(SERVICE_LABELS).map(([code, name]) => ({ code, name, enabled: false }));
  if (env.DB) {
    try {
      const rows = await env.DB.prepare("SELECT code,name,enabled FROM services ORDER BY rowid").all();
      const byCode = new Map((rows.results || []).map(row => [row.code, row]));
      services = services.map(item => {
        const row = byCode.get(item.code);
        return row ? { code: row.code, name: row.name || item.name, enabled: Boolean(row.enabled) } : item;
      });
    } catch (error) {
      console.error("services_menu_load_failed", error?.message || "unknown_error");
    }
  }
  const rows = services.map(({code,name,enabled}) => [{
    text: (enabled ? "" : "⏳ ") + name,
    callback_data: `service:rules:${code}`
  }]);
  rows.push([{ text: "🔙 بازگشت به منوی اصلی", callback_data: "menu:home" }]);
  return sendMessage(env, chatId, "🧾 خدمات دفتر نت‌یار مهاجر\n\n⏳ خدماتی که کنارشان این علامت است هنوز تعرفه و فعال‌سازی نهایی‌شان تأیید نشده است.\n\nلطفاً خدمت موردنظر را انتخاب کنید:", { inline_keyboard: rows });
}

async function showRules(env, chatId, code, userId) {
  const label = SERVICE_LABELS[code];
  if (!label) return sendMessage(env, chatId, "این خدمت شناخته نشد.", HOME_KEYBOARD);
  let rules = "";
  if (env.DB) {
    const row = await env.DB.prepare("SELECT name,rules_text FROM services WHERE code=? AND enabled=1").bind(code).first();
    if (!row) return sendMessage(env, chatId, "این خدمت در حال حاضر فعال نیست.", HOME_KEYBOARD);
    rules = row.rules_text || "";
  }
  await saveState(env, userId, "awaiting_rules", { service_code: code });
  return sendMessage(env, chatId, `📋 قوانین و شرایط خدمت «${label}»\n\n${rules || "لطفاً اطلاعات را دقیق وارد کنید. نتیجه و زمان انجام خدمت به بررسی کارشناس بستگی دارد."}\n\nآیا قوانین را می‌پذیرید؟`, {
    inline_keyboard: [
      [{ text: "✅ تأیید و ادامه", callback_data: `service:accept:${code}` }],
      [{ text: "❌ رد قوانین", callback_data: "service:reject" }],
      [{ text: "❌ انصراف", callback_data: "flow:cancel" }],
    ],
  });
}

function formSteps(code) {
  const common = [{ key: "phone", label: "شماره موبایل در دسترس را وارد کنید:" }];
  const forms = {
    identity: [
      ...common,
      { key: "full_name", label: "نام و نام خانوادگی را وارد کنید:" },
      { key: "birth_date", label: "تاریخ تولد را وارد کنید:" },
      { key: "return_date", label: "تاریخ مراجعه/بازگشت موردنظر را وارد کنید:" },
      { key: "consulate", label: "کنسولگری موردنظر را بنویسید (زاهدان یا مشهد):" },
      { key: "document_type", label: "نوع مدرک شناسایی را وارد کنید (آمایش، پاسپورت، سایر یا ندارم):" },
      { key: "document_id", label: "شماره شناسه مدرک شناسایی را وارد کنید؛ اگر ندارید بنویسید «ندارم»:" },
      { key: "document_photo", label: "در صورت امکان تصویر مدرک شناسایی را ارسال کنید؛ اگر ندارید بنویسید «ندارم»:" },
      { key: "tazkira", label: "وضعیت تذکره اقارب نزدیک را توضیح دهید:" },
      { key: "description", label: "توضیحات تکمیلی را بنویسید یا «رد» ارسال کنید:" },
    ],
    khodnevis: [
      ...common,
      { key: "full_name", label: "نام و نام خانوادگی را وارد کنید:" },
      { key: "document_type", label: "نوع مدرک را انتخاب کنید (کارت آمایش یا پاسپورت):" },
      { key: "document_number", label: "شماره مدرک شناسایی را وارد کنید:" },
      { key: "tenant_login", label: "آیا مستأجر می‌تواند وارد درگاه دولت من شود؟ (بله/خیر)" },
      { key: "description", label: "توضیحات تکمیلی را بنویسید یا «رد» ارسال کنید:" },
    ],
    fida: [
      ...common,
      { key: "full_name", label: "نام و نام خانوادگی را وارد کنید:" },
      { key: "father_name", label: "نام پدر را وارد کنید:" },
      { key: "birth_date", label: "تاریخ تولد را وارد کنید:" },
      { key: "province", label: "استان محل سکونت:" },
      { key: "city", label: "شهر محل سکونت:" },
      { key: "neighborhood", label: "محله محل سکونت:" },
      { key: "street", label: "خیابان محل سکونت:" },
      { key: "alley", label: "کوچه محل سکونت:" },
      { key: "plate", label: "پلاک:" },
      { key: "document_photo", label: "تصویر مدرک شناسایی را ارسال کنید یا «رد» بنویسید:" },
      { key: "description", label: "توضیحات تکمیلی را بنویسید یا «رد» ارسال کنید:" },
    ],
    dolatman_login: [
      ...common,
      { key: "own_name_phone", label: "آیا سیم‌کارت به نام خودتان است؟ (بله/خیر)" },
      { key: "sim_photo", label: "در صورت نیاز تصویر مدرک سیم‌کارت را ارسال کنید یا «رد» بنویسید:" },
      { key: "document_photo", label: "تصویر مدرک شناسایی را ارسال کنید یا «رد» بنویسید:" },
      { key: "description", label: "توضیحات تکمیلی را بنویسید یا «رد» ارسال کنید:" },
    ],
    student_screening: [
      ...common,
      { key: "parent_own_name_phone", label: "آیا شماره موبایل به نام والد/سرپرست است؟ (بله/خیر)" },
      { key: "parent_id_photo", label: "تصویر مدرک شناسایی صاحب شماره را ارسال کنید یا «رد» بنویسید:" },
      { key: "child_id_photo", label: "تصویر مدرک شناسایی دانش‌آموز را ارسال کنید یا «رد» بنویسید:" },
      { key: "student_count", label: "تعداد دانش‌آموزان را وارد کنید:" },
      { key: "description", label: "توضیحات تکمیلی را بنویسید یا «رد» ارسال کنید:" },
    ],
    other_service: [
      ...common,
      { key: "requested_service", label: "خدمت موردنیاز را شرح دهید:" },
      { key: "description", label: "توضیحات تکمیلی را بنویسید یا «رد» ارسال کنید:" },
    ],
  };
  return forms[code] || [];
}

async function acceptService(env, chatId, userId, code) {
  const steps = formSteps(code);
  if (!steps.length) return sendMessage(env, chatId, "فرم این خدمت هنوز منتقل نشده است.", HOME_KEYBOARD);
  await saveState(env, userId, "form", { service_code: code, step: 0, answers: {} });
  return sendMessage(env, chatId, `فرم «${SERVICE_LABELS[code]}» آغاز شد.\n\n${steps[0].label}\n\nبرای لغو، دکمه انصراف را بزنید.`, {
    inline_keyboard: [[{ text: "❌ انصراف", callback_data: "flow:cancel" }]],
  });
}

function normalizeDigits(value) {
  return String(value || "").replace(/[۰-۹]/g, d => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d)))
    .replace(/[٠-٩]/g, d => String("٠١٢٣٤٥٦٧٨٩".indexOf(d)));
}

async function startRialitTopup(env, chatId, telegramId, amount) {
  if (!Number.isSafeInteger(amount) || amount < 10000 || amount > 5000000 || amount % 1000 !== 0) {
    return sendMessage(env, chatId, "مبلغ معتبر نیست. حداقل ۱۰٬۰۰۰ و حداکثر ۵٬۰۰۰٬۰۰۰ تومان وارد کنید؛ مبلغ باید مضرب ۱٬۰۰۰ باشد.", {
      inline_keyboard: [[{text:"🔙 انتخاب مبلغ",callback_data:"wallet:add"}]]
    });
  }
  if (!env.DB) return sendMessage(env, chatId, "پایگاه داده اعتبار متصل نیست؛ پرداخت ساخته نشد.", HOME_KEYBOARD);
  if (!env.RIALIT_API_KEY) return sendMessage(env, chatId, "درگاه ریالت‌پی هنوز روی نسخه Cloudflare تنظیم نشده است. مدیر باید Secret با نام RIALIT_API_KEY را روی همین Worker اضافه کند. هیچ مبلغی از حساب شما کسر نشده است.", {
    inline_keyboard: [[{text:"🔄 تلاش دوباره",callback_data:"wallet:add"}],[{text:"🔙 منوی اصلی",callback_data:"menu:home"}]]
  });
  const user = await env.DB.prepare("SELECT id FROM users WHERE telegram_id=?").bind(String(telegramId)).first();
  if (!user) return sendMessage(env, chatId, "حساب مشترک پیدا نشد؛ لطفاً /start را بزنید.", HOME_KEYBOARD);
  await env.DB.prepare("INSERT INTO wallets(user_id,balance_toman) VALUES(?,0) ON CONFLICT(user_id) DO NOTHING").bind(user.id).run();
  const topupResult = await env.DB.prepare("INSERT INTO wallet_topups(user_id,amount_toman,status) VALUES(?,?,'awaiting_payment')").bind(user.id, amount).run();
  const topupId = topupResult.meta?.last_row_id;
  if (!topupId) throw new Error("wallet_topup_insert_failed");
  try {
    const response = await fetch("https://api.rialit.org/api/v1/send", {
      method: "POST",
      headers: { "Authorization": "Bearer " + env.RIALIT_API_KEY, "Accept": "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        amount,
        callback_url: "https://bot-tasbit-howyat-migration.mahdi-masoumi168.workers.dev/webhooks/rialit",
        order_id: "topup-" + topupId + "-" + Date.now(),
        user_id: Number(user.id)
      })
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || !body || typeof body !== "object") {
      console.error("rialit_link_create_failed", response.status);
      throw new Error("rialit_link_create_http_" + response.status);
    }
    const token = String(body.token || body.data?.token || "").trim();
    if (!token || token.length > 512 || /[/?#]/.test(token)) throw new Error("rialit_token_missing");
    const payUrl = "https://api.rialit.org/api/v1/redirect/" + token;
    await env.DB.prepare("INSERT INTO rialit_payments(token,kind,topup_id,user_id,amount_toman,pay_url,status) VALUES(?,'topup',?,?,?,?,'pending')")
      .bind(token, topupId, user.id, amount, payUrl).run();
    return sendMessage(env, chatId, `🧾 درخواست افزایش اعتبار شماره ${topupId}\n\nمبلغ: ${amount.toLocaleString("fa-IR")} تومان\nدرگاه: ریالت‌پی\n\nپس از پرداخت، ریالت‌پی تراکنش را به‌صورت خودکار بررسی می‌کند. اعتبار تنها پس از تأیید سمت سرور افزوده می‌شود؛ از ارسال رسید یا پرداخت دوباره خودداری کنید.`, {
      inline_keyboard: [
        [{text:"💳 پرداخت امن ریالت‌پی",url:payUrl}],
        [{text:"🔄 بررسی موجودی",callback_data:"menu:wallet"}],
        [{text:"🏠 منوی اصلی",callback_data:"menu:home"}]
      ]
    });
  } catch (error) {
    await env.DB.prepare("UPDATE wallet_topups SET status='payment_link_failed' WHERE id=? AND status='awaiting_payment'").bind(topupId).run();
    console.error("rialit_topup_start_failed", error?.message || "unknown_error");
    return sendMessage(env, chatId, "ساخت لینک پرداخت ناموفق بود. هیچ اعتباری اضافه نشده و از پرداخت با لینک نامعتبر خودداری کنید. کمی بعد دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.", {
      inline_keyboard: [[{text:"🔄 تلاش دوباره",callback_data:"wallet:add"}],[{text:"📞 پشتیبانی",url:"https://t.me/NetYar_esf"}]]
    });
  }
}

async function handleCallback(env, callback) {
  const data = callback.data || "";
  const chatId = callback.message?.chat?.id;
  const userId = callback.from?.id;
  if (!chatId || !userId) return;
  await ensureUser(env, callback.from);
  await answerCallback(env, callback.id, "انجام شد");
  if (data === "menu:home" || data === "menu:restart") {
    await saveState(env, userId, "idle", {});
    return sendMessage(env, chatId, "🌟 سلام و خوش آمدید به کمک‌یار مهاجر\n\nهمراه شما برای استفاده از خدمات دفتر نت‌یار مهاجر.\n\nاز منوی زیر می‌توانید خدمت موردنیاز را انتخاب کنید، درخواست‌هایتان را پیگیری کنید، اعتبار حساب را ببینید یا با پشتیبانی در ارتباط باشید.", HOME_KEYBOARD);
  }
  if (data === "menu:services") return showServices(env, chatId);
  if (data === "vpn:start") {
    return sendMessage(env, chatId, "🔐 خرید VPN / فیلترشکن\n\nمدت اشتراک را انتخاب کنید:", {
      inline_keyboard: [
        [{text:"۱ ماه",callback_data:"vpn:months:1"},{text:"۲ ماه",callback_data:"vpn:months:2"}],
        [{text:"۳ ماه",callback_data:"vpn:months:3"},{text:"۴ ماه",callback_data:"vpn:months:4"}],
        [{text:"🔙 بازگشت به منوی اصلی",callback_data:"menu:home"}]
      ]
    });
  }
  if (data.startsWith("vpn:months:")) {
    const months = Number(data.split(":")[2]);
    if (![1,2,3,4].includes(months)) return sendMessage(env, chatId, "مدت انتخابی معتبر نیست.", HOME_KEYBOARD);
    const rows = [];
    for (let gb=10; gb<=100; gb+=10) {
      if (gb%20===10) rows.push([]);
      rows[rows.length-1].push({text:`${gb} گیگابایت — ${(gb*10000).toLocaleString("fa-IR")} تومان`,callback_data:`vpn:gb:${months}:${gb}`});
    }
    rows.push([{text:"🔙 انتخاب مدت",callback_data:"vpn:start"}],[{text:"🔙 منوی اصلی",callback_data:"menu:home"}]);
    return sendMessage(env, chatId, `🔐 مدت انتخابی: ${months} ماه\n\nحجم موردنیاز را انتخاب کنید. قیمت فعلی منطبق با کد اصلی: هر گیگابایت ۱۰٬۰۰۰ تومان است.\n\n`,{inline_keyboard:rows});
  }
  if (data.startsWith("vpn:gb:")) {
    const parts=data.split(":"); const months=Number(parts[2]); const gb=Number(parts[3]);
    if (![1,2,3,4].includes(months) || !Number.isInteger(gb) || gb<10 || gb>100 || gb%10!==0) return sendMessage(env,chatId,"مدت یا حجم انتخابی معتبر نیست.",HOME_KEYBOARD);
    const amount=gb*10000;
    return sendMessage(env,chatId,`🧾 خلاصه سفارش VPN\n\n⏳ مدت اشتراک: ${months} ماه\n📦 حجم: ${gb} گیگابایت\n💰 قیمت هر گیگابایت: ۱۰٬۰۰۰ تومان\n💵 مبلغ کل: ${amount.toLocaleString("fa-IR")} تومان\n\n⚠️ پرداخت ریالت‌پی هنوز به Worker مهاجرتی متصل نشده است؛ فعلاً پرداختی انجام ندهید. این صفحه فقط انتخاب سفارش را نشان می‌دهد.\n\nپس از انتقال کامل درگاه، امکان پرداخت امن فعال می‌شود.`,{inline_keyboard:[[ {text:"🔄 انتخاب دوباره",callback_data:"vpn:start"} ],[ {text:"🔙 بازگشت به منوی اصلی",callback_data:"menu:home"} ]]});
  }
  if (data === "menu:account") return sendMessage(env, chatId, `👤 حساب شما\nشناسه تلگرام: ${userId}`, HOME_KEYBOARD);
  if (data === "menu:wallet") {
    if (!env.DB) return sendMessage(env, chatId, "پایگاه داده اعتبار در دسترس نیست؛ لطفاً بعداً تلاش کنید.", HOME_KEYBOARD);
    const u = await env.DB.prepare("SELECT id FROM users WHERE telegram_id=?").bind(String(userId)).first();
    if (!u) return sendMessage(env, chatId, "حساب مشترک پیدا نشد. لطفاً /start را بزنید.", HOME_KEYBOARD);
    await env.DB.prepare("INSERT INTO wallets(user_id,balance_toman) VALUES(?,0) ON CONFLICT(user_id) DO NOTHING").bind(u.id).run();
    const w = await env.DB.prepare("SELECT balance_toman FROM wallets WHERE user_id=?").bind(u.id).first();
    return sendMessage(env, chatId, `💰 اعتبار من\n\nموجودی فعلی: ${Number(w?.balance_toman || 0).toLocaleString("fa-IR")} تومان\n\nبرای افزایش اعتبار، مبلغ را انتخاب کنید. اعتبار فقط پس از تأیید پرداخت توسط ریالت‌پی اضافه می‌شود.`, {
      inline_keyboard: [
        [{text:"➕ افزایش اعتبار",callback_data:"wallet:add"}],
        [{text:"📜 سوابق اعتبار",callback_data:"wallet:history"}],
        [{text:"🔙 بازگشت به منوی اصلی",callback_data:"menu:home"}]
      ]
    });
  }
  if (data === "wallet:add") {
    return sendMessage(env, chatId, "💳 مبلغ افزایش اعتبار را انتخاب کنید:", {
      inline_keyboard: [
        [{text:"۵۰٬۰۰۰ تومان",callback_data:"wallet:topup:amount:50000"},{text:"۱۰۰٬۰۰۰ تومان",callback_data:"wallet:topup:amount:100000"}],
        [{text:"۲۰۰٬۰۰۰ تومان",callback_data:"wallet:topup:amount:200000"},{text:"۵۰۰٬۰۰۰ تومان",callback_data:"wallet:topup:amount:500000"}],
        [{text:"✍️ مبلغ دلخواه",callback_data:"wallet:topup:custom"}],
        [{text:"🔙 بازگشت به اعتبار من",callback_data:"menu:wallet"}]
      ]
    });
  }
  if (data === "wallet:topup:custom") {
    await saveState(env, userId, "wallet_amount", {});
    return sendMessage(env, chatId, "مبلغ موردنظر را به تومان و فقط با عدد بفرستید. حداقل ۱۰٬۰۰۰ و حداکثر ۵٬۰۰۰٬۰۰۰ تومان است. مثال: ۱۵۰۰۰۰", {
      inline_keyboard: [[{text:"❌ انصراف",callback_data:"flow:cancel"}]]
    });
  }
  if (data.startsWith("wallet:topup:amount:")) {
    const amount = Number(data.split(":")[3]);
    return startRialitTopup(env, chatId, userId, amount);
  }
  if (data === "wallet:history") {
    if (!env.DB) return sendMessage(env, chatId, "پایگاه داده در دسترس نیست.", HOME_KEYBOARD);
    const u = await env.DB.prepare("SELECT id FROM users WHERE telegram_id=?").bind(String(userId)).first();
    const rows = u ? await env.DB.prepare("SELECT amount_toman,balance_after_toman,kind,description,created_at FROM wallet_transactions WHERE user_id=? ORDER BY id DESC LIMIT 10").bind(u.id).all() : {results:[]};
    const lines = (rows.results || []).map(t => `• ${String(t.created_at || "").slice(0,16)} — ${Number(t.amount_toman).toLocaleString("fa-IR")} تومان — موجودی: ${Number(t.balance_after_toman).toLocaleString("fa-IR")} تومان\n  ${t.description || t.kind}`);
    return sendMessage(env, chatId, lines.length ? "📜 ده گردش اخیر اعتبار شما:\n\n" + lines.join("\n\n") : "هنوز گردش اعتباری ثبت نشده است.", {
      inline_keyboard: [[{text:"🔙 بازگشت به اعتبار من",callback_data:"menu:wallet"}],[{text:"🏠 منوی اصلی",callback_data:"menu:home"}]]
    });
  }
  if (data === "menu:tracking") {
    if (!env.DB) return sendMessage(env, chatId, "پایگاه داده هنوز متصل نشده است.", HOME_KEYBOARD);
    const u = await env.DB.prepare("SELECT id FROM users WHERE telegram_id=?").bind(String(userId)).first();
    const rows = u ? await env.DB.prepare("SELECT public_id,service_code,status,created_at FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10").bind(u.id).all() : { results: [] };
    const lines = (rows.results || []).map(o => `• ${o.public_id} — ${SERVICE_LABELS[o.service_code] || o.service_code} — ${o.status}`);
    return sendMessage(env, chatId, lines.length ? "📋 درخواست‌های شما:\n\n" + lines.join("\n") : "هنوز درخواستی ثبت نشده است.", HOME_KEYBOARD);
  }
  if (data === "menu:support") return sendMessage(env, chatId, "📞 پشتیبانی دفتر نت‌یار مهاجر\nبرای ارتباط مستقیم به @NetYar_esf پیام بدهید.", { inline_keyboard: [[{ text: "💬 ارتباط با پشتیبانی", url: "https://t.me/NetYar_esf" }], [{ text: "🔙 منوی اصلی", callback_data: "menu:home" }]] });
  if (data.startsWith("service:rules:")) return showRules(env, chatId, data.split(":")[2], userId);
  if (data.startsWith("service:accept:")) {
    const code = data.split(":")[2];
    const current = await getState(env, userId);
    if (current.state !== "awaiting_rules" || current.data.service_code !== code) return sendMessage(env, chatId, "این درخواست قوانین منقضی شده است؛ خدمت را دوباره انتخاب کنید.", HOME_KEYBOARD);
    return acceptService(env, chatId, userId, code);
  }
  if (data === "service:reject" || data === "flow:cancel") {
    await saveState(env, userId, "idle", {});
    return sendMessage(env, chatId, "درخواست لغو شد. هر زمان خواستید می‌توانید از منوی اصلی شروع کنید.", HOME_KEYBOARD);
  }
  return sendMessage(env, chatId, "این گزینه هنوز به نسخه Cloudflare منتقل نشده است.", HOME_KEYBOARD);
}

async function handleMessage(env, message) {
  const chatId = message.chat?.id;
  const userId = message.from?.id;
  if (!chatId || !userId) return;
  await ensureUser(env, message.from);
  const text = (message.text || message.caption || "").trim();
  if (message.web_app_data?.data) {
    try {
      const appData = JSON.parse(message.web_app_data.data);
      if (appData?.action === "start_service" && typeof appData.code === "string" && Object.hasOwn(SERVICE_LABELS, appData.code)) {
        return showRules(env, chatId, appData.code, userId);
      }
    } catch {}
    return sendMessage(env, chatId, "اطلاعات دریافتی از مینی‌اپ معتبر نبود. لطفاً دوباره تلاش کنید.", HOME_KEYBOARD);
  }
  if (text === "/start" || text === "🔄 شروع مجدد") {
    await saveState(env, userId, "idle", {});
    return sendMessage(env, chatId, "🌟 سلام و خوش آمدید به کمک‌یار مهاجر\n\nهمراه شما برای استفاده از خدمات دفتر نت‌یار مهاجر.\n\nاز منوی زیر می‌توانید خدمت موردنیاز را انتخاب کنید، درخواست‌هایتان را پیگیری کنید، اعتبار حساب را ببینید یا با پشتیبانی در ارتباط باشید.", HOME_KEYBOARD);
  }
  if (text === "/health") return sendMessage(env, chatId, "اتصال ربات فعال است.");
  const current = await getState(env, userId);
  if (current.state === "wallet_amount") {
    const raw = normalizeDigits(text).replace(/[,٬،\s]/g, "").replace(/تومان/g, "");
    const amount = Number(raw);
    await saveState(env, userId, "idle", {});
    return startRialitTopup(env, chatId, userId, amount);
  }
  if (current.state === "form") {
    const steps = formSteps(current.data.service_code);
    const step = steps[current.data.step || 0];
    if (!step) {
      await saveState(env, userId, "idle", {});
      return sendMessage(env, chatId, "وضعیت فرم نامعتبر بود؛ لطفاً دوباره شروع کنید.", HOME_KEYBOARD);
    }
    const photo = message.photo?.at(-1)?.file_id;
    if (!text && !photo) return sendMessage(env, chatId, "لطفاً متن یا تصویر مورد درخواست را ارسال کنید.");
    const value = photo || (step.key === "description" && ["رد", "ندارم", "skip"].includes(text.toLowerCase()) ? "" : text);
    const answers = { ...(current.data.answers || {}), [step.key]: value };
    const nextStep = (current.data.step || 0) + 1;
    if (nextStep < steps.length) {
      await saveState(env, userId, "form", { ...current.data, step: nextStep, answers });
      return sendMessage(env, chatId, steps[nextStep].label, {
        inline_keyboard: [[{ text: "❌ انصراف", callback_data: "flow:cancel" }]],
      });
    }
    if (!env.DB) {
      await saveState(env, userId, "idle", {});
      return sendMessage(env, chatId, "فرم تکمیل شد، اما پایگاه داده هنوز متصل نیست؛ درخواست ثبت نشد. لطفاً بعداً تلاش کنید.", HOME_KEYBOARD);
    }
    const user = await env.DB.prepare("SELECT id FROM users WHERE telegram_id=?").bind(String(userId)).first();
    const service = await env.DB.prepare("SELECT price_toman,enabled FROM services WHERE code=?").bind(current.data.service_code).first();
    if (!user || !service) return sendMessage(env, chatId, "ذخیره اطلاعات ناموفق بود؛ لطفاً با پشتیبانی تماس بگیرید.", HOME_KEYBOARD);
    if (!service.enabled || !Number.isSafeInteger(service.price_toman) || service.price_toman <= 0) {
      await saveState(env, userId, "idle", {});
      return sendMessage(env, chatId, "این خدمت هنوز در نسخه مهاجرتی فعال نشده است؛ تعرفه و قوانین باید توسط مدیریت تأیید شود. هیچ پرونده یا پرداختی ثبت نشد.", HOME_KEYBOARD);
    }
    const publicId = `DRAFT-${Date.now().toString(36).toUpperCase()}`;
    await env.DB.prepare("INSERT INTO order_drafts(public_id,user_id,service_code,status,amount_toman,data_json,description) VALUES(?,?,?,'awaiting_payment',?,?,?)")
      .bind(publicId, user.id, current.data.service_code, service.price_toman, JSON.stringify(answers), answers.description || "").run();
    await saveState(env, userId, "idle", {});
    return sendMessage(env, chatId, `اطلاعات فرم ذخیره شد، اما هنوز پرونده نهایی ایجاد نشده است.\n\nدرگاه پرداخت و بررسی رسید هنوز منتقل نشده‌اند؛ این نسخه هیچ وجهی دریافت نمی‌کند و اطلاعات شما تا تکمیل مهاجرت در پیش‌نویس نگهداری می‌شود.\nشناسه پیش‌نویس: ${publicId}`, HOME_KEYBOARD);
  }
  return sendMessage(env, chatId, "برای شروع، /start را بزنید.", HOME_KEYBOARD);
}


async function handleRialitWebhook(request, env) {
  if (request.method === "GET") {
    return json({ ok: true, service: "rialit-webhook", endpoint: "/webhooks/rialit", method: "POST" });
  }
  if (request.method !== "POST") {
    return json({ ok: false, error: "method_not_allowed" }, 405);
  }
  let payload;
  try { payload = await request.json(); } catch { return json({ ok: false, error: "invalid_json" }, 400); }
  const token = String(payload?.token || payload?.payment_token || payload?.data?.token || payload?.payment?.token || "").trim();
  // Webhook-provider test deliveries may contain no payment token. Acknowledge them
  // without touching payment state; this must never mark a payment as paid.
  if (!token) return json({ ok: true, action: "event_received_without_payment_token" });
  if (!env.DB) return json({ ok: false, error: "database_not_bound" }, 503);
  if (!env.RIALIT_API_KEY) return json({ ok: false, error: "gateway_not_configured" }, 503);
  const payment = await env.DB.prepare("SELECT * FROM rialit_payments WHERE token=?").bind(token).first();
  if (!payment) return json({ ok: false, error: "unknown_payment" }, 404);
  if (payment.status === "paid") return json({ ok: true, action: "duplicate" });
  let verifiedResponse;
  try {
    verifiedResponse = await fetch("https://api.rialit.org/api/v1/verify/" + encodeURIComponent(token), {
      method: "POST",
      headers: { "Authorization": "Bearer " + env.RIALIT_API_KEY, "Accept": "application/json" }
    });
  } catch {
    return json({ ok: false, error: "verification_unavailable" }, 502);
  }
  if (verifiedResponse.status === 409) return json({ ok: true, action: "pending" }, 202);
  if (verifiedResponse.status !== 200) {
    console.error("rialit_verify_failed", verifiedResponse.status);
    return json({ ok: false, error: "verification_unavailable" }, 502);
  }
  let verified;
  try { verified = await verifiedResponse.json(); } catch { return json({ ok: false, error: "invalid_verification_response" }, 502); }
  const data = verified?.data && typeof verified.data === "object" ? verified.data : verified;
  const verifiedStatus = Number(data?.status);
  if (verifiedStatus === 4) {
    await env.DB.prepare("UPDATE rialit_payments SET status='failed' WHERE id=? AND status='pending'").bind(payment.id).run();
    return json({ ok: true, action: "failed" });
  }
  if (verifiedStatus !== 3) return json({ ok: true, action: "pending" }, 202);
  const verifiedAmount = Number(data?.amount ?? data?.paid_amount);
  if (!Number.isFinite(verifiedAmount) || verifiedAmount !== Number(payment.amount_toman)) {
    console.error("rialit_amount_mismatch", payment.id);
    return json({ ok: false, error: "amount_mismatch" }, 400);
  }
  const now = new Date().toISOString();
  if (payment.kind === "order") {
    const claim = await env.DB.prepare("UPDATE orders SET status='payment_approved',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status IN ('waiting_payment','waiting_receipt_review')").bind(payment.order_id).run();
    if ((claim.meta?.changes || 0) !== 1) {
      await env.DB.prepare("UPDATE rialit_payments SET status='ignored' WHERE id=? AND status='pending'").bind(payment.id).run();
      return json({ ok: true, action: "already_handled" });
    }
    await env.DB.prepare("INSERT INTO payments(order_id,user_id,provider,provider_payment_id,amount_toman,status,verified_at,receipt_type) VALUES(?,?,?,?,?,'approved',?,'rialit')").bind(payment.order_id,payment.user_id,"rialit",token,payment.amount_toman,now).run();
  } else if (payment.kind === "topup") {
    const topup = await env.DB.prepare("SELECT * FROM wallet_topups WHERE id=? AND user_id=?").bind(payment.topup_id, payment.user_id).first();
    if (!topup || !["awaiting_payment","awaiting_receipt","waiting_receipt_review"].includes(topup.status) || Number(topup.amount_toman) !== Number(payment.amount_toman)) {
      await env.DB.prepare("UPDATE rialit_payments SET status='ignored' WHERE id=? AND status='pending'").bind(payment.id).run();
      return json({ ok: true, action: "already_handled" });
    }
    // Atomic D1 batch: duplicate webhook deliveries cannot credit the same top-up twice.
    const results = await env.DB.batch([
      env.DB.prepare("UPDATE rialit_payments SET status='processing' WHERE id=? AND status='pending'").bind(payment.id),
      env.DB.prepare("UPDATE wallet_topups SET status='processing_payment' WHERE id=? AND user_id=? AND amount_toman=? AND status IN ('awaiting_payment','awaiting_receipt','waiting_receipt_review') AND EXISTS (SELECT 1 FROM rialit_payments WHERE id=? AND status='processing')").bind(payment.topup_id, payment.user_id, payment.amount_toman, payment.id),
      env.DB.prepare("INSERT INTO wallets(user_id,balance_toman) SELECT ?,0 WHERE changes()=1 ON CONFLICT(user_id) DO NOTHING").bind(topup.user_id),
      env.DB.prepare("UPDATE wallets SET balance_toman=balance_toman+?,updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND EXISTS (SELECT 1 FROM wallet_topups WHERE id=? AND status='processing_payment')").bind(payment.amount_toman, topup.user_id, payment.topup_id),
      env.DB.prepare("INSERT INTO wallet_transactions(user_id,amount_toman,balance_after_toman,kind,description,topup_id) SELECT ?,?,balance_toman,'topup',?,? FROM wallets WHERE user_id=? AND changes()=1").bind(topup.user_id,payment.amount_toman,"افزایش اعتبار ریالت‌پی #"+topup.id,topup.id,topup.user_id),
      env.DB.prepare("UPDATE wallet_topups SET status='approved',reviewed_at=? WHERE id=? AND status='processing_payment'").bind(now,payment.topup_id),
      env.DB.prepare("UPDATE rialit_payments SET status='paid',paid_at=? WHERE id=? AND status='processing' AND EXISTS (SELECT 1 FROM wallet_topups WHERE id=? AND status='approved' AND reviewed_at=?)").bind(now,payment.id,payment.topup_id,now),
      env.DB.prepare("UPDATE rialit_payments SET status='ignored' WHERE id=? AND status='processing'").bind(payment.id)
    ]);
    if ((results[0]?.meta?.changes || 0) !== 1 || (results[1]?.meta?.changes || 0) !== 1 || (results[3]?.meta?.changes || 0) !== 1 || (results[6]?.meta?.changes || 0) !== 1) {
      return json({ ok: true, action: "already_handled" });
    }
    const wallet = await env.DB.prepare("SELECT balance_toman FROM wallets WHERE user_id=?").bind(topup.user_id).first();
    const userRow = await env.DB.prepare("SELECT telegram_id FROM users WHERE id=?").bind(topup.user_id).first();
    if (userRow?.telegram_id) {
      try { await telegram(env, "sendMessage", { chat_id: Number(userRow.telegram_id), text: "✅ افزایش اعتبار تأیید شد. مبلغ " + Number(payment.amount_toman).toLocaleString("fa-IR") + " تومان به اعتبار شما افزوده شد. موجودی جدید: " + Number(wallet?.balance_toman || 0).toLocaleString("fa-IR") + " تومان." }); } catch {}
    }
  } else if (payment.kind !== "vpn") {
    return json({ ok: false, error: "unsupported_payment_kind" }, 400);
  }
  if (payment.kind !== "topup") {
    const update = await env.DB.prepare("UPDATE rialit_payments SET status='paid',paid_at=? WHERE id=? AND status='pending'").bind(now,payment.id).run();
    if ((update.meta?.changes || 0) !== 1) return json({ ok: true, action: "duplicate" });
  }
  // VPN provisioning must be completed by the migrated VPN fulfillment workflow.
  if (payment.kind === "vpn") {
    return json({ ok: true, action: "paid_vpn_pending_fulfillment", user_id: payment.user_id, months: payment.vpn_months, gigabytes: payment.vpn_gigabytes });
  }
  return json({ ok: true, action: payment.kind === "order" ? "paid_order" : "paid_topup" });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "GET" && (url.pathname === "/" || url.pathname === "/app" || url.pathname === "/app/")) {
      return new Response(MINIAPP_HTML, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" } });
    }
    if (url.pathname === "/webhooks/rialit") return handleRialitWebhook(request, env);
    if (url.pathname === "/webhooks/variza") {
      if (request.method === "GET") return json({ ok: true, service: "variza-webhook", method: "POST", note: "Signed webhook integration must be validated before live payments." });
      return json({ ok: false, error: "variza_webhook_not_migrated" }, 501);
    }
    if (url.pathname === "/payments/variza/return" && request.method === "GET") {
      return new Response("پرداخت واریزا دریافت شد. وضعیت پرداخت فقط پس از تأیید سمت سرور مشخص می‌شود؛ به ربات برگردید.", {headers:{"content-type":"text/plain; charset=utf-8"}});
    }
    if (url.pathname.startsWith("/api/miniapp/")) {
      if (request.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
      return miniAppApi(request, env, url.pathname);
    }
    if (request.method === "GET" && url.pathname === "/health") {
      let telegramBot = null;
      let telegramApiOk = false;
      let telegramApiHttpStatus = null;
      let telegramApiErrorCode = null;
      let telegramApiError = null;
      let telegramNetworkError = false;
      if (env.BOT_TOKEN) {
        try {
          const botToken = String(env.BOT_TOKEN || "").trim();
          const r = await fetch(`https://api.telegram.org/bot${botToken}/getMe`);
          telegramApiHttpStatus = r.status;
          const d = await r.json();
          telegramApiOk = Boolean(r.ok && d.ok && d.result?.is_bot);
          if (telegramApiOk) telegramBot = d.result.username || null;
          else {
            telegramApiErrorCode = Number.isInteger(d.error_code) ? d.error_code : null;
            telegramApiError = typeof d.description === "string" ? d.description.slice(0, 180) : "telegram_api_rejected_request";
          }
        } catch (e) {
          telegramNetworkError = true;
          telegramApiError = "network_error";
        }
      }
      return json({ ok: true, service: "کمک‌یار مهاجر", mode: "cloudflare-migration-scaffold", database_bound: Boolean(env.DB), token_configured: Boolean(env.BOT_TOKEN), telegram_api_ok: telegramApiOk, telegram_bot_username: telegramBot, telegram_api_http_status: telegramApiHttpStatus, telegram_api_error_code: telegramApiErrorCode, telegram_api_error: telegramApiError, telegram_network_error: telegramNetworkError, webhook_secret_configured: Boolean(env.WEBHOOK_SECRET), note: "این نسخه‌ی مهاجرت اولیه است؛ پرداخت و پنل مدیریت هنوز منتقل نشده‌اند." });
    }
    if (url.pathname !== "/telegram-webhook" || request.method !== "POST") return json({ ok: false, error: "not_found" }, 404);
    if (!env.BOT_TOKEN) return json({ ok: false, error: "BOT_TOKEN_missing" }, 503);
    if (env.WEBHOOK_SECRET && request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET) return json({ ok: false, error: "invalid_secret" }, 403);
    let update;
    try { update = await request.json(); } catch { return json({ ok: false, error: "invalid_json" }, 400); }
    try {
      if (env.DB && Number.isInteger(update.update_id)) {
        const inserted = await env.DB.prepare("INSERT OR IGNORE INTO processed_updates(update_id,status) VALUES(?,'processing')").bind(update.update_id).run();
        if (inserted.meta?.changes === 0) {
          const previous = await env.DB.prepare("SELECT status FROM processed_updates WHERE update_id=?").bind(update.update_id).first();
          if (previous?.status === "processed") return json({ ok: true, duplicate: true });
          return json({ ok: false, error: "update_in_progress_retry" }, 503);
        }
      }
      if (update.callback_query) await handleCallback(env, update.callback_query);
      else if (update.message) await handleMessage(env, update.message);
      if (env.DB && Number.isInteger(update.update_id)) {
        await env.DB.prepare("UPDATE processed_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
      }
      return json({ ok: true });
    } catch (error) {
      if (env.DB && Number.isInteger(update?.update_id)) {
        try { await env.DB.prepare("DELETE FROM processed_updates WHERE update_id=?").bind(update.update_id).run(); } catch {}
      }
      console.error("webhook_processing_failed", error?.message || "unknown_error");
      // A non-200 response allows Telegram to retry transient processing failures.
      return json({ ok: false, error: "processing_failed" }, 500);
    }
  },
};
