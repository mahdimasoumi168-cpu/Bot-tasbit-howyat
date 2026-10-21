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
  if (!initData || !botToken || initData.length > 8192) return null;
  const params = new URLSearchParams(initData);
  const receivedHash = params.get("hash");
  if (!receivedHash || !/^[a-f0-9]{64}$/i.test(receivedHash)) return null;
  params.delete("hash");
  params.delete("signature");
  const pairs = Array.from(params.entries()).sort(([a], [b]) => a.localeCompare(b));
  const checkString = pairs.map(([k, v]) => k + "=" + v).join("\n");
  const secret = await hmacSha256(new TextEncoder().encode(botToken), new TextEncoder().encode("WebAppData"));
  const expectedHash = bytesToHex(await hmacSha256(secret, new TextEncoder().encode(checkString)));
  if (expectedHash.length !== receivedHash.length) return null;
  let diff = 0;
  for (let i = 0; i < expectedHash.length; i++) diff |= expectedHash.charCodeAt(i) ^ receivedHash.toLowerCase().charCodeAt(i);
  if (diff !== 0) return null;
  const authDate = Number(params.get("auth_date"));
  const now = Math.floor(Date.now() / 1000);
  if (!Number.isFinite(authDate) || authDate > now + 60 || now - authDate > 86400) return null;
  let user;
  try { user = JSON.parse(params.get("user") || "null"); } catch { return null; }
  if (!user || !Number.isSafeInteger(user.id)) return null;
  return user;
}

async function authorizeMiniApp(request, env) {
  let body;
  try { body = await request.json(); } catch { return { error: "invalid_json" }; }
  const user = await verifyTelegramInitData(body?.initData, env.BOT_TOKEN);
  if (!user) return { error: "invalid_telegram_session" };
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
    [{ text: "🚀 باز کردن مینی‌اپ", web_app: { url: "https://bot-tasbit-howyat-migration.mahdi-masoumi168.workers.dev/app" } }],
    [{ text: "🧾 خدمات دفتر نت‌یار مهاجر", callback_data: "menu:services" }],
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
  if (!env.BOT_TOKEN) throw new Error("BOT_TOKEN_missing");
  const response = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
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
  let services = Object.entries(SERVICE_LABELS);
  if (env.DB) {
    const rows = await env.DB.prepare("SELECT code,name,enabled FROM services ORDER BY rowid").all();
    if (rows.results?.length) services = rows.results.filter(s => s.enabled).map(s => [s.code, s.name]);
  }
  const rows = services.map(([code, name]) => [{ text: name, callback_data: `service:rules:${code}` }]);
  rows.push([{ text: "🔙 بازگشت به منوی اصلی", callback_data: "menu:home" }]);
  return sendMessage(env, chatId, "🧾 خدمات دفتر نت‌یار مهاجر\n\nلطفاً خدمت موردنظر را انتخاب کنید:", { inline_keyboard: rows });
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

async function handleCallback(env, callback) {
  const data = callback.data || "";
  const chatId = callback.message?.chat?.id;
  const userId = callback.from?.id;
  if (!chatId || !userId) return;
  await ensureUser(env, callback.from);
  await answerCallback(env, callback.id, "انجام شد");
  if (data === "menu:home" || data === "menu:restart") {
    await saveState(env, userId, "idle", {});
    return sendMessage(env, chatId, "سلام، به کمک‌یار مهاجر خوش آمدید.\n\nاز منوی زیر گزینه موردنظر را انتخاب کنید:", HOME_KEYBOARD);
  }
  if (data === "menu:services") return showServices(env, chatId);
  if (data === "menu:account") return sendMessage(env, chatId, `👤 حساب شما\nشناسه تلگرام: ${userId}`, HOME_KEYBOARD);
  if (data === "menu:wallet") {
    let balance = 0;
    if (env.DB) {
      const u = await env.DB.prepare("SELECT id FROM users WHERE telegram_id=?").bind(String(userId)).first();
      const w = u ? await env.DB.prepare("SELECT balance_toman FROM wallets WHERE user_id=?").bind(u.id).first() : null;
      balance = w?.balance_toman || 0;
    }
    return sendMessage(env, chatId, `💰 اعتبار شما: ${Number(balance).toLocaleString("fa-IR")} تومان\n\nافزایش اعتبار و پرداخت هنوز در مرحله انتقال است.`, HOME_KEYBOARD);
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
    return sendMessage(env, chatId, "سلام، به کمک‌یار مهاجر خوش آمدید.\n\nاز منوی زیر گزینه موردنظر را انتخاب کنید:", HOME_KEYBOARD);
  }
  if (text === "/health") return sendMessage(env, chatId, "اتصال ربات فعال است.");
  const current = await getState(env, userId);
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "GET" && (url.pathname === "/" || url.pathname === "/app" || url.pathname === "/app/")) {
      return new Response(MINIAPP_HTML, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" } });
    }
    if (url.pathname.startsWith("/api/miniapp/")) {
      if (request.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
      return miniAppApi(request, env, url.pathname);
    }
    if (request.method === "GET" && url.pathname === "/health") {
      return json({ ok: true, service: "کمک‌یار مهاجر", mode: "cloudflare-migration-scaffold", database_bound: Boolean(env.DB), token_configured: Boolean(env.BOT_TOKEN), webhook_secret_configured: Boolean(env.WEBHOOK_SECRET), note: "این نسخه‌ی مهاجرت اولیه است؛ پرداخت و پنل مدیریت هنوز منتقل نشده‌اند." });
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
