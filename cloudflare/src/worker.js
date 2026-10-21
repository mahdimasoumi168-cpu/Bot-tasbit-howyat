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
    const service = await env.DB.prepare("SELECT price_toman FROM services WHERE code=?").bind(current.data.service_code).first();
    if (!user || !service) return sendMessage(env, chatId, "ثبت درخواست ناموفق بود؛ لطفاً با پشتیبانی تماس بگیرید.", HOME_KEYBOARD);
    const publicId = `NY${Date.now().toString(36).toUpperCase()}`;
    await env.DB.prepare("INSERT INTO orders(public_id,user_id,service_code,status,amount_toman,data_json,description) VALUES(?,?,?,'awaiting_payment',?,?,?)")
      .bind(publicId, user.id, current.data.service_code, service.price_toman, JSON.stringify(answers), answers.description || "").run();
    await saveState(env, userId, "idle", {});
    return sendMessage(env, chatId, `✅ فرم شما ثبت شد.\n🔢 کد پیگیری: ${publicId}\n💰 مبلغ پایه: ${Number(service.price_toman).toLocaleString("fa-IR")} تومان\n\nتوجه: اتصال پرداخت و پنل بررسی هنوز منتقل نشده است؛ این نسخه از شما وجه دریافت نمی‌کند.`, HOME_KEYBOARD);
  }
  return sendMessage(env, chatId, "برای شروع، /start را بزنید.", HOME_KEYBOARD);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
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
        const inserted = await env.DB.prepare("INSERT OR IGNORE INTO processed_updates(update_id) VALUES(?)").bind(update.update_id).run();
        if (inserted.meta?.changes === 0) return json({ ok: true, duplicate: true });
      }
      if (update.callback_query) await handleCallback(env, update.callback_query);
      else if (update.message) await handleMessage(env, update.message);
      return json({ ok: true });
    } catch (error) {
      console.error("webhook_processing_failed", error?.message || "unknown_error");
      // A non-200 response allows Telegram to retry transient processing failures.
      return json({ ok: false, error: "processing_failed" }, 500);
    }
  },
};
