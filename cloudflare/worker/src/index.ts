import { MINIAPP_HTML, MINIAPP_JS } from "./generated/miniapp.js";
import { expectedPayerAmount, matchesRialitFee } from "./fees.js";

interface Env {
  DB: D1Database;
  LEGACY_DB: D1Database;
  BOT_TOKEN: string;
  TELEGRAM_WEBHOOK_SECRET: string;
  RIALIT_API_KEY: string;
  API_VPN?: string;
  GOZARBAN_API_ROOT?: string;
  GOZARBAN_PLAN_ID?: string;
  MIGRATION_SECRET?: string;
  RIALIT_API_BASE_URL?: string;
  RIALIT_WEBHOOK_IPS?: string;
  PAYMENT_FEE_PERCENT?: string;
  APP_NAME?: string;
  ADMIN_IDS?: string;
  ADMIN_SETUP_SECRET?: string;
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
  `).bind(String(user.id), user.first_name || null, user.last_name || null, user.username || null).run();

  const row = await db.prepare("SELECT id FROM users WHERE telegram_id = ?")
    .bind(String(user.id)).first<{ id: number }>();
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


async function isAdmin(env: Env, telegramId: number): Promise<boolean> {
  const configured = new Set((env.ADMIN_IDS || "").split(",").map((x) => x.trim()).filter(Boolean));
  if (configured.has(String(telegramId))) return true;
  const row = await env.DB.prepare("SELECT id FROM operators WHERE telegram_id = ? AND active = 1 AND role IN ('admin','owner','operator')")
    .bind(String(telegramId)).first();
  return Boolean(row);
}

async function notifyAdmins(env: Env, details: {
  paymentId: number; userTelegramId: number; amount: number; title: string;
  fileId: string; mediaType: string;
}) {
  const ids = new Set((env.ADMIN_IDS || "").split(",").map((x) => x.trim()).filter(Boolean));
  const operators = await env.DB.prepare("SELECT telegram_id FROM operators WHERE active=1 AND role IN ('admin','owner','operator')").all();
  for (const row of operators.results || []) ids.add(String((row as any).telegram_id));
  const caption = "🧾 رسید جدید\n" + details.title + "\nمبلغ: " + details.amount.toLocaleString("en-US") +
    " تومان\nشناسه پرداخت: #" + details.paymentId + "\nشناسه مشترک: " + details.userTelegramId;
  const reply_markup = { inline_keyboard: [[
    { text: "✅ تأیید رسید", callback_data: "admin:payment:approve:" + details.paymentId },
    { text: "❌ رد رسید", callback_data: "admin:payment:reject:" + details.paymentId }
  ]] };
  for (const id of ids) {
    const method = details.mediaType === "photo" ? "sendPhoto" : "sendDocument";
    const mediaKey = details.mediaType === "photo" ? "photo" : "document";
    await telegram(env, method, {
      chat_id: id, [mediaKey]: details.fileId, caption, reply_markup
    }).catch(() => undefined);
  }
}

async function processReceiptMessage(message: any, user: TelegramUser, userId: number, env: Env): Promise<boolean> {
  const photo = Array.isArray(message.photo) && message.photo.length ? message.photo[message.photo.length - 1] : null;
  const document = message.document || null;
  if (!photo && !document) return false;
  const fileId = String(photo?.file_id || document?.file_id || "");
  if (!fileId) return false;
  const mediaType = photo ? "photo" : "document";
  const topup = await env.DB.prepare("SELECT id,amount_toman FROM wallet_topups WHERE user_id=? AND status='awaiting_receipt' ORDER BY id DESC LIMIT 1")
    .bind(userId).first<any>();
  if (topup) {
    const providerPaymentId = "topup:" + topup.id;
    const payment = await env.DB.prepare("SELECT id FROM payments WHERE user_id=? AND provider='card_transfer' AND provider_payment_id=? AND status='awaiting_receipt'")
      .bind(userId,providerPaymentId).first<{id:number}>();
    if (!payment) return false;
    await env.DB.batch([
      env.DB.prepare("UPDATE wallet_topups SET receipt_file_id=?,receipt_type=?,status='awaiting_receipt_review' WHERE id=? AND status='awaiting_receipt'")
        .bind(fileId,mediaType,topup.id),
      env.DB.prepare("UPDATE payments SET receipt_file_id=?,receipt_type=?,status='awaiting_review' WHERE id=? AND status='awaiting_receipt'")
        .bind(fileId,mediaType,payment.id),
      env.DB.prepare("INSERT INTO documents(user_id,document_type,telegram_file_id,media_type,caption,review_status) VALUES(?,'wallet_topup_receipt',?,?,?,'pending')")
        .bind(userId,fileId,mediaType,message.caption || null)
    ]);
    await notifyAdmins(env,{paymentId:payment.id,userTelegramId:user.id,amount:Number(topup.amount_toman),title:"افزایش اعتبار",fileId,mediaType});
    await telegram(env,"sendMessage",{chat_id:user.id,text:"✅ رسید افزایش اعتبار دریافت شد. پس از بررسی مدیریت، نتیجه به شما اطلاع داده می‌شود."});
    return true;
  }

  const payment = await env.DB.prepare("SELECT id,order_id,amount_toman FROM payments WHERE user_id=? AND provider='card_transfer' AND order_id IS NOT NULL AND status='awaiting_receipt' ORDER BY id DESC LIMIT 1")
    .bind(userId).first<any>();
  if (!payment) return false;
  await env.DB.batch([
    env.DB.prepare("UPDATE payments SET receipt_file_id=?,receipt_type=?,status='awaiting_review' WHERE id=? AND status='awaiting_receipt'")
      .bind(fileId,mediaType,payment.id),
    env.DB.prepare("UPDATE orders SET status='waiting_receipt_review',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='awaiting_receipt'")
      .bind(payment.order_id),
    env.DB.prepare("INSERT INTO documents(order_id,user_id,document_type,telegram_file_id,media_type,caption,review_status) VALUES(?,?,'payment_receipt',?,?,?,'pending')")
      .bind(payment.order_id,userId,fileId,mediaType,message.caption || null)
  ]);
  await notifyAdmins(env,{paymentId:payment.id,userTelegramId:user.id,amount:Number(payment.amount_toman),title:"پرداخت پرونده شماره "+payment.order_id,fileId,mediaType});
  await telegram(env,"sendMessage",{chat_id:user.id,text:"✅ رسید پرداخت پرونده دریافت شد و برای بررسی مدیریت ارسال شد."});
  return true;
}

async function claimFirstAdmin(message: any, user: TelegramUser, env: Env): Promise<boolean> {
  const textValue = String(message.text || "").trim();
  if (!textValue.startsWith("/claim_admin")) return false;
  const supplied = textValue.split(/\s+/)[1] || "";
  if (!env.ADMIN_SETUP_SECRET || supplied !== env.ADMIN_SETUP_SECRET) {
    await telegram(env,"sendMessage",{chat_id:user.id,text:"کد فعال‌سازی پنل مدیریت معتبر نیست."});
    return true;
  }
  const existing = await env.DB.prepare("SELECT COUNT(*) AS n FROM operators WHERE active=1 AND role IN ('admin','owner')")
    .first<{n:number}>();
  if (Number(existing?.n || 0) > 0) {
    await telegram(env,"sendMessage",{chat_id:user.id,text:"مدیر اصلی قبلاً ثبت شده است. برای افزودن مدیر جدید با مدیر فعلی تماس بگیرید."});
    return true;
  }
  await env.DB.prepare("INSERT OR IGNORE INTO operators(telegram_id,display_name,role,permissions_json,active) VALUES(?,?,'admin','{}',1)")
    .bind(String(user.id),[user.first_name,user.last_name].filter(Boolean).join(" ")).run();
  await env.DB.prepare("INSERT INTO settings(key,value) VALUES('admin_setup_claimed','1') ON CONFLICT(key) DO UPDATE SET value='1',updated_at=CURRENT_TIMESTAMP").run();
  await telegram(env,"sendMessage",{chat_id:user.id,text:"✅ دسترسی مدیر اصلی فعال شد. از این پس رسیدهای کارت‌به‌کارت برای بررسی به شما ارسال می‌شوند."});
  return true;
}

async function handleAdminPaymentCallback(callback: any, env: Env): Promise<boolean> {
  const match = String(callback.data || "").match(/^admin:payment:(approve|reject):(\d+)$/);
  if (!match) return false;
  const actorId = Number(callback.from?.id || 0);
  if (!await isAdmin(env,actorId)) {
    await telegram(env,"answerCallbackQuery",{callback_query_id:callback.id,text:"شما دسترسی مدیریت ندارید.",show_alert:true});
    return true;
  }
  const action = match[1];
  const paymentId = Number(match[2]);
  const payment = await env.DB.prepare("SELECT p.*,u.telegram_id AS user_telegram_id FROM payments p JOIN users u ON u.id=p.user_id WHERE p.id=?")
    .bind(paymentId).first<any>();
  if (!payment || payment.status !== "awaiting_review") {
    await telegram(env,"answerCallbackQuery",{callback_query_id:callback.id,text:"این رسید قبلاً بررسی شده یا وجود ندارد.",show_alert:true});
    return true;
  }
  const isTopup = String(payment.provider_payment_id || "").startsWith("topup:");
  const topupId = isTopup ? Number(String(payment.provider_payment_id).slice(6)) : 0;
  if (action === "approve" && isTopup) {
    await env.DB.batch([
      env.DB.prepare("UPDATE payments SET status='approved',verified_at=CURRENT_TIMESTAMP WHERE id=? AND status='awaiting_review'").bind(paymentId),
      env.DB.prepare("UPDATE wallet_topups SET status='approved',reviewed_at=CURRENT_TIMESTAMP,reviewed_by=? WHERE id=? AND status='awaiting_receipt_review' AND changes()=1").bind(String(actorId),topupId),
      env.DB.prepare("INSERT OR IGNORE INTO wallet_credit_events(source_key) SELECT 'card:topup:' || ? WHERE changes()=1").bind(topupId),
      env.DB.prepare("INSERT OR IGNORE INTO wallets(user_id,balance_toman) SELECT user_id,0 FROM wallet_topups WHERE id=? AND status='approved'").bind(topupId),
      env.DB.prepare("UPDATE wallets SET balance_toman=balance_toman+? WHERE user_id=(SELECT user_id FROM wallet_topups WHERE id=?) AND EXISTS(SELECT 1 FROM wallet_credit_events WHERE source_key=?) AND NOT EXISTS(SELECT 1 FROM wallet_transactions WHERE related_id=?)").bind(payment.amount_toman,topupId,"card:topup:"+topupId,"card:topup:"+topupId),
      env.DB.prepare("INSERT OR IGNORE INTO wallet_transactions(user_id,amount_toman,balance_after_toman,kind,description,related_id,topup_id) SELECT w.user_id,?,w.balance_toman,'topup','افزایش اعتبار کارت‌به‌کارت',?,? FROM wallets w WHERE w.user_id=(SELECT user_id FROM wallet_topups WHERE id=?) AND changes()=1").bind(payment.amount_toman,"card:topup:"+topupId,topupId,topupId)
    ]);
  } else if (action === "approve") {
    await env.DB.batch([
      env.DB.prepare("UPDATE payments SET status='approved',verified_at=CURRENT_TIMESTAMP WHERE id=? AND status='awaiting_review'").bind(paymentId),
      env.DB.prepare("UPDATE orders SET status='payment_approved',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='waiting_receipt_review' AND changes()=1").bind(payment.order_id)
    ]);
  } else {
    await env.DB.prepare("UPDATE payments SET status='rejected' WHERE id=? AND status='awaiting_review'").bind(paymentId).run();
    if (isTopup) {
      await env.DB.prepare("UPDATE wallet_topups SET status='rejected',reviewed_at=CURRENT_TIMESTAMP,reviewed_by=? WHERE id=? AND status='awaiting_receipt_review'")
        .bind(String(actorId),topupId).run();
    } else if (payment.order_id) {
      await env.DB.prepare("UPDATE orders SET status='payment_rejected',updated_at=CURRENT_TIMESTAMP WHERE id=?")
        .bind(payment.order_id).run();
    }
  }
  const userTelegramId = String(payment.user_telegram_id);
  await telegram(env,"sendMessage",{chat_id:userTelegramId,text:action==="approve" ? "✅ رسید پرداخت شما تأیید شد." : "❌ رسید پرداخت شما تأیید نشد. برای پیگیری با پشتیبانی تماس بگیرید."}).catch(()=>undefined);
  await telegram(env,"answerCallbackQuery",{callback_query_id:callback.id,text:action==="approve" ? "رسید تأیید شد." : "رسید رد شد."});
  if (callback.message?.chat?.id) {
    await telegram(env,"editMessageReplyMarkup",{chat_id:callback.message.chat.id,message_id:callback.message.message_id,reply_markup:{inline_keyboard:[]}});
  }
  return true;
}

async function ensureTelegramWebhook(env: Env, origin: string): Promise<void> {
  if (!env.BOT_TOKEN || !env.TELEGRAM_WEBHOOK_SECRET) return;
  const existing = await env.DB.prepare("SELECT value FROM settings WHERE key='telegram_webhook_origin'").first<{value:string}>();
  if (existing?.value === origin) return;
  const url = origin.replace(/\/$/,"") + "/webhooks/telegram";
  try {
    const response = await fetch("https://api.telegram.org/bot" + env.BOT_TOKEN + "/setWebhook", {
      method:"POST",
      headers:{"content-type":"application/json"},
      body:JSON.stringify({url,secret_token:env.TELEGRAM_WEBHOOK_SECRET,allowed_updates:["message","callback_query"],drop_pending_updates:false}),
      signal:AbortSignal.timeout(12_000)
    });
    const result = await response.json().catch(()=>({})) as any;
    if (!response.ok || result?.ok !== true) {
      console.error("Telegram webhook setup failed",response.status);
      return;
    }
    await env.DB.prepare("INSERT INTO settings(key,value) VALUES('telegram_webhook_origin',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP")
      .bind(origin).run();
    await telegram(env,"setChatMenuButton",{menu_button:{type:"web_app",text:"کمک‌یار مهاجر",web_app:{url:origin+"/app/"}}}).catch(()=>undefined);
  } catch (error) {
    console.error("Telegram webhook setup unavailable",error);
  }
}

async function handleTelegram(request: Request, env: Env): Promise<Response> {
  const expected = env.TELEGRAM_WEBHOOK_SECRET;
  const supplied = request.headers.get("x-telegram-bot-api-secret-token");
  if (!expected || supplied !== expected) return text("forbidden", 403);

  const update = await request.json().catch(() => null) as any;
  if (!update || !Number.isInteger(update.update_id)) return json({ ok: false }, 400);
  await env.DB.prepare("INSERT OR IGNORE INTO telegram_updates(update_id,status,processing_at) VALUES (?,'received',CURRENT_TIMESTAMP)")
    .bind(update.update_id).run();
  const claim = await env.DB.prepare("UPDATE telegram_updates SET status='processing',processing_at=CURRENT_TIMESTAMP WHERE update_id=? AND (status='received' OR (status='processing' AND processing_at < datetime('now','-1 minute')))").bind(update.update_id).run();
  if ((claim.meta?.changes || 0) !== 1) return json({ ok: true, duplicate: true });

  try {
    const message = update.message;
    if (message?.from?.id) {
      const user = message.from as TelegramUser;
      const userId = await ensureUser(env.DB,user);
      if (await claimFirstAdmin(message,user,env)) {
        await env.DB.prepare("UPDATE telegram_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
        return json({ok:true});
      }
      const incomingText = String(message.text || "").trim();
      if (incomingText.startsWith("/setcard")) {
        if (!await isAdmin(env,user.id)) {
          await telegram(env,"sendMessage",{chat_id:user.id,text:"دسترسی مدیریت ندارید."});
        } else {
          const values = incomingText.replace(/^\/setcard\s*/,"").split("|").map((x:string)=>x.trim());
          if (values.length < 3 || !/^\d{16}$/.test(values[0])) {
            await telegram(env,"sendMessage",{chat_id:user.id,text:"قالب دستور: /setcard شماره‌کارت۱۶رقمی|نام‌دارنده|نام‌بانک"});
          } else {
            const pairs = [["card_number",values[0]],["card_holder",values[1]],["card_bank",values[2]]];
            await env.DB.batch(pairs.map(([key,value])=>env.DB.prepare("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP").bind(key,value)));
            await telegram(env,"sendMessage",{chat_id:user.id,text:"✅ اطلاعات کارت دفتر ذخیره شد."});
          }
        }
        await env.DB.prepare("UPDATE telegram_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
        return json({ok:true});
      }
      if (await processReceiptMessage(message,user,userId,env)) {
        await env.DB.prepare("UPDATE telegram_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
        return json({ok:true});
      }
      const appUrl = new URL("/app/", request.url).toString();
      const greeting = String(message.text || "").startsWith("/start")
        ? (user.first_name ? "سلام " + user.first_name + " عزیز 🌷\n\n" : "سلام و خوش آمدید 🌷\n\n")
        : "";
      await telegram(env,"sendMessage",{
        chat_id:message.chat.id,
        text:greeting+"به «کمک‌یار مهاجر» خوش آمدید.\nاز دکمه زیر برای ثبت خدمات، پیگیری پرونده و مدیریت اعتبار استفاده کنید.",
        reply_markup:homeKeyboard(appUrl)
      });
    }

    const callback = update.callback_query;
    if (callback?.id && callback?.from?.id) {
      if (await handleAdminPaymentCallback(callback,env)) {
        await env.DB.prepare("UPDATE telegram_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
        return json({ok:true});
      }
      await telegram(env,"answerCallbackQuery",{callback_query_id:callback.id});
      const chatId = callback.message?.chat?.id;
      if (chatId) {
        const appUrl = new URL("/app/",request.url).toString();
        const labels: Record<string,string> = {
          "menu:home":"صفحه اصلی کمک‌یار مهاجر",
          "menu:services":"برای ثبت درخواست خدمت، مینی‌اپ را باز کنید.",
          "menu:wallet":"برای مشاهده اعتبار و افزایش موجودی، مینی‌اپ را باز کنید.",
          "menu:orders":"برای پیگیری پرونده‌ها، مینی‌اپ را باز کنید.",
          "menu:support":"پیام خود را برای پشتیبانی ارسال کنید."
        };
        await telegram(env,"sendMessage",{chat_id:chatId,text:labels[String(callback.data)]||"برای ادامه، مینی‌اپ را باز کنید.",reply_markup:homeKeyboard(appUrl)});
      }
    }
    await env.DB.prepare("UPDATE telegram_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
    return json({ok:true});
  } catch (error) {
    await env.DB.prepare("UPDATE telegram_updates SET status='received',processing_at=NULL WHERE update_id=?").bind(update.update_id).run();
    console.error("Telegram update processing failed",error);
    return json({ok:false,error:"telegram_update_failed"},503);
  }
}
async function bootstrap(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const userId = await ensureUser(env.DB, user);
  const [services, wallet, orders, settings] = await Promise.all([
    env.DB.prepare("SELECT id, code, name, price_toman, description, rules_text FROM services WHERE enabled = 1 ORDER BY id").all(),
    env.DB.prepare("SELECT balance_toman FROM wallets WHERE user_id = ?").bind(userId).first<{ balance_toman: number }>(),
    env.DB.prepare(`
      SELECT o.id, o.public_id, o.status, COALESCE(o.price_snapshot_toman,o.amount_toman) AS price_snapshot_toman, o.created_at, s.name AS service_name
      FROM orders o LEFT JOIN services s ON s.id = o.service_id
      WHERE o.user_id = ? ORDER BY o.id DESC LIMIT 20
    `).bind(userId).all(),
    env.DB.prepare("SELECT key, value FROM settings WHERE key IN ('card_number','card_holder','card_bank','support_username')").all(),
  ]);
  let legacy = { wallet_topups: [] as any[], rialit_payments: [] as any[] };
  let serviceRows = (services.results || []) as any[];
  try {
    const legacyUser = await env.LEGACY_DB.prepare("SELECT id FROM users WHERE telegram_id = ?")
      .bind(String(user.id)).first<{id:number}>();
    if (legacyUser) {
      const [legacyTopups, legacyPayments] = await Promise.all([
        env.LEGACY_DB.prepare("SELECT t.id,t.amount_toman,CASE WHEN t.status='awaiting_payment' AND EXISTS(SELECT 1 FROM rialit_payments rp WHERE rp.topup_id=t.id AND rp.status IN ('failed','expired','cancelled')) THEN 'payment_link_failed' ELSE t.status END AS status,t.created_at,t.reviewed_at FROM wallet_topups t WHERE t.user_id = ? ORDER BY t.id DESC LIMIT 20").bind(legacyUser.id).all(),
        env.LEGACY_DB.prepare("SELECT kind,amount_toman,status,created_at,paid_at FROM rialit_payments WHERE user_id = ? ORDER BY id DESC LIMIT 20").bind(legacyUser.id).all(),
      ]);
      legacy = { wallet_topups: legacyTopups.results || [], rialit_payments: legacyPayments.results || [] };
    }
    const legacyServices = await env.LEGACY_DB.prepare("SELECT code,name,description,price_toman,enabled,rules_text FROM services").all();
    const byCode = new Map((legacyServices.results || []).map((x: any) => [x.code, x]));
    serviceRows = serviceRows.map((service) => {
      const old = byCode.get(service.code) as any;
      if (!old) return service;
      return {
        ...service,
        name: service.name || old.name,
        description: service.description || old.description,
        price_toman: Number(service.price_toman || old.price_toman),
        rules_text: service.rules_text || old.rules_text,
      };
    });
  } catch {
    console.warn("Legacy D1 read unavailable; primary data remains usable");
  }

  return json({
    ok: true,
    user: { id: user.id, first_name: user.first_name, last_name: user.last_name },
    services: serviceRows,
    wallet: wallet || { balance_toman: 0 },
    orders: orders.results || [],
    legacy,
    settings: Object.fromEntries((settings.results || []).map((x: any) => [x.key, x.value])),
    payment: { rialit_fee_percent: Number(env.PAYMENT_FEE_PERCENT || "12"), min_toman: 50_000, max_toman: 10_000_000 },
  });
}

async function createOrder(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json().catch(() => null) as any;
  const serviceCode = String(body?.service_code || "");
  const formData = body?.form_data;
  if (body?.rules_accepted !== true) return json({ ok: false, error: "rules_not_accepted" }, 400);
  if (!serviceCode || !formData || typeof formData !== "object" || Array.isArray(formData)) {
    return json({ ok: false, error: "invalid_request" }, 400);
  }
  const userId = await ensureUser(env.DB, user);
  const serializedForm = JSON.stringify(formData);
  if (serializedForm.length > 20_000) return json({ ok: false, error: "form_too_large" }, 413);
  const service = await env.DB.prepare(
    "SELECT id, price_toman FROM services WHERE code = ? AND enabled = 1"
  ).bind(serviceCode).first<{ id: number; price_toman: number }>();
  if (!service) return json({ ok: false, error: "service_unavailable" }, 404);
  if (!Number.isSafeInteger(service.price_toman) || service.price_toman < 1) {
    return json({ ok: false, error: "service_price_not_configured" }, 503);
  }

  const publicId = `YM-${crypto.randomUUID().replaceAll("-", "").slice(0, 10).toUpperCase()}`;
  const created = await env.DB.prepare(`
    INSERT INTO orders (public_id, user_id, service_id, service_code, amount_toman, price_snapshot_toman, status, data_json)
    VALUES (?, ?, ?, ?, ?, ?, 'waiting_payment', ?)
    RETURNING id
  `).bind(publicId, userId, service.id, serviceCode, service.price_toman, service.price_toman, serializedForm).first<{ id: number }>();
  if (!created) return json({ ok: false, error: "order_create_failed" }, 500);
  return json({ ok: true, order_id: created.id, public_id: publicId, amount_toman: service.price_toman });
}

async function createRialitPayment(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json().catch(() => null) as any;
  const orderId = Number(body?.order_id);
  if (!Number.isSafeInteger(orderId) || orderId < 1) return json({ ok: false, error: "invalid_order" }, 400);
  const userId = await ensureUser(env.DB, user);
  const order = await env.DB.prepare(`
    SELECT o.id, o.public_id, o.price_snapshot_toman, o.amount_toman, o.status
    FROM orders o WHERE o.id = ? AND o.user_id = ?
  `).bind(orderId, userId).first<any>();
  if (!order) return json({ ok: false, error: "order_not_found" }, 404);
  if (order.status !== "waiting_payment") return json({ ok: false, error: "order_not_payable" }, 409);

  const amount = Number(order.price_snapshot_toman ?? order.amount_toman ?? 0);
  if (amount < 50_000 || amount > 10_000_000) {
    return json({ ok: false, error: "rialit_amount_out_of_range", card_transfer_available: true }, 400);
  }
  if (!env.RIALIT_API_KEY) return json({ ok: false, error: "rialit_not_configured" }, 503);

  const previous = await env.DB.prepare(
    "SELECT id, token, provider_order_id, pay_url, payer_amount_toman, payer_fee_toman, status, attempt_no FROM rialit_payments WHERE order_id = ? ORDER BY attempt_no DESC LIMIT 1"
  ).bind(order.id).first<any>();
  if (previous?.status === "pending" && previous.provider_order_id && previous.pay_url) {
    return json({ ok: true, pay_url: previous.pay_url, payer_amount_toman: previous.payer_amount_toman, payer_fee_toman: previous.payer_fee_toman });
  }
  if (previous && !["pending", "expired", "cancelled", "failed"].includes(String(previous.status))) {
    return json({ ok: false, error: "payment_not_reopenable" }, 409);
  }
  const attemptNo = previous?.status === "pending" && previous.provider_order_id ? Number(previous.attempt_no) : Number(previous?.attempt_no || 0) + 1;
  const providerOrderId = `mohajer-order-${order.id}-${attemptNo}`;
  if (!previous || previous.status !== "pending") {
    await env.DB.prepare(`
      INSERT OR IGNORE INTO rialit_payments
        (provider_order_id, attempt_no, kind, order_id, user_id, amount_toman, status)
      VALUES (?, ?, 'order', ?, ?, ?, 'pending')
    `).bind(providerOrderId, attemptNo, order.id, userId, amount).run();
  }

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
  if (!/^[A-Za-z0-9]{1,64}$/.test(token) || !Number.isSafeInteger(payerAmount) || !Number.isSafeInteger(payerFee) || Number(result?.amount) !== amount || !["pending", "paid"].includes(String(result?.status || "pending"))) {
    return json({ ok: false, error: "rialit_invalid_response" }, 502);
  }
  const payUrl = `https://pay.rialit.io/v1/${token}`;
  const feePercent = Number(env.PAYMENT_FEE_PERCENT || "12");
  if (!matchesRialitFee(amount, payerAmount, payerFee, feePercent)) {
    await env.DB.prepare("UPDATE rialit_payments SET token=?,pay_url=?,payer_amount_toman=?,payer_fee_toman=?,status='fee_mismatch' WHERE provider_order_id=? AND status='pending'")
      .bind(token,payUrl,payerAmount,payerFee,providerOrderId).run();
    return json({ok:false,error:"rialit_fee_mismatch",expected_payer_amount_toman:expectedPayerAmount(amount,feePercent)},409);
  }
  await env.DB.prepare(`
    UPDATE rialit_payments
    SET token = ?, pay_url = ?, payer_amount_toman = ?, payer_fee_toman = ?
    WHERE provider_order_id = ? AND status = 'pending'
  `).bind(token, payUrl, payerAmount, payerFee, providerOrderId).run();

  return json({
    ok: true,
    pay_url: payUrl,
    amount_toman: amount,
    payer_amount_toman: payerAmount,
    payer_fee_toman: payerFee,
    fee_percent: feePercent,
    fee_configuration_matches: true,
  });
}


async function createWalletTopup(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json().catch(() => null) as any;
  const amount = Number(body?.amount_toman);
  const method = String(body?.method || "");
  if (!Number.isSafeInteger(amount) || amount < 20_000 || amount > 10_000_000 || !["card", "rialit"].includes(method)) {
    return json({ ok: false, error: "invalid_topup_amount_or_method" }, 400);
  }
  if (method === "rialit" && amount < 50_000) return json({ ok: false, error: "rialit_minimum_50000" }, 400);
  const userId = await ensureUser(env.DB, user);
  if (method === "card") {
    const card = await env.DB.prepare("SELECT value FROM settings WHERE key='card_number'").first<{value:string}>();
    if (!card?.value) return json({ok:false,error:"card_not_configured"},503);
  }
  const status = method === "card" ? "awaiting_receipt" : "awaiting_payment";
  const topup = await env.DB.prepare("INSERT INTO wallet_topups(user_id,amount_toman,status) VALUES(?,?,?) RETURNING id")
    .bind(userId, amount, status).first<{id:number}>();
  if (!topup) return json({ ok: false, error: "topup_create_failed" }, 500);
  if (method === "card") {
    await env.DB.prepare("INSERT OR IGNORE INTO payments(user_id,provider,provider_payment_id,amount_toman,status,receipt_type) VALUES(?,'card_transfer',?,?,'awaiting_receipt','photo')")
      .bind(userId, "topup:" + topup.id, amount).run();
    await telegram(env,"sendMessage",{chat_id:user.id,text:"برای تکمیل افزایش اعتبار، مبلغ را به کارت دفتر واریز کنید و تصویر رسید را همین‌جا ارسال کنید."}).catch(()=>undefined);
  }
  return json({ ok: true, topup_id: topup.id, amount_toman: amount, method });
}

async function createRialitTopupPayment(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json().catch(() => null) as any;
  const topupId = Number(body?.topup_id);
  if (!Number.isSafeInteger(topupId) || topupId < 1) return json({ ok: false, error: "invalid_topup" }, 400);
  const userId = await ensureUser(env.DB, user);
  const topup = await env.DB.prepare("SELECT id,amount_toman,status FROM wallet_topups WHERE id = ? AND user_id = ?")
    .bind(topupId, userId).first<any>();
  if (!topup) return json({ ok: false, error: "topup_not_found" }, 404);
  if (!["awaiting_payment", "payment_link_failed"].includes(String(topup.status))) return json({ ok: false, error: "topup_not_payable" }, 409);
  const amount = Number(topup.amount_toman);
  if (amount < 50_000 || amount > 10_000_000) return json({ ok: false, error: "rialit_amount_out_of_range" }, 400);
  if (!env.RIALIT_API_KEY) return json({ ok: false, error: "rialit_not_configured" }, 503);

  const previous = await env.DB.prepare("SELECT id,token,provider_order_id,attempt_no,pay_url,payer_amount_toman,payer_fee_toman,status FROM rialit_payments WHERE topup_id = ? AND kind = 'topup' ORDER BY attempt_no DESC LIMIT 1")
    .bind(topupId).first<any>();
  if (previous?.status === "pending" && previous.provider_order_id && previous.pay_url) {
    return json({ ok: true, pay_url: previous.pay_url, payer_amount_toman: previous.payer_amount_toman, payer_fee_toman: previous.payer_fee_toman });
  }
  const attemptNo = previous?.status === "pending" && previous.provider_order_id ? Number(previous.attempt_no) : Number(previous?.attempt_no || 0) + 1;
  const providerOrderId = "mohajer-topup-" + topupId + "-" + attemptNo;
  const apiBase = (env.RIALIT_API_BASE_URL || "https://api.rialit.io/api/v1").replace(/\/$/, "");
  let response: Response;
  try {
    response = await fetch(apiBase + "/send", {
      method: "POST",
      headers: { authorization: "Bearer " + env.RIALIT_API_KEY, "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ amount, order_id: providerOrderId, payer_id: user.id }),
      signal: AbortSignal.timeout(25_000),
    });
  } catch {
    return json({ ok: false, error: "rialit_network_error", retry_same_order: true }, 502);
  }
  const result = await response.json().catch(() => ({})) as any;
  if (![200, 201].includes(response.status)) {
    if (response.status === 401) return json({ ok: false, error: "rialit_key_invalid" }, 502);
    if (response.status === 403) return json({ ok: false, error: "rialit_outbound_ip_not_allowed" }, 502);
    if (response.status === 409) return json({ ok: false, error: "rialit_order_id_conflict" }, 409);
    return json({ ok: false, error: "rialit_request_failed", status: response.status }, 502);
  }
  const token = String(result?.token || "");
  const payerAmount = Number(result?.payer_amount);
  const payerFee = Number(result?.payer_fee);
  if (!/^[A-Za-z0-9]{1,64}$/.test(token) || !Number.isSafeInteger(payerAmount) || !Number.isSafeInteger(payerFee) || Number(result?.amount) !== amount) {
    return json({ ok: false, error: "rialit_invalid_response" }, 502);
  }
  const payUrl = "https://pay.rialit.io/v1/" + token;
  const feePercent = Number(env.PAYMENT_FEE_PERCENT || "12");
  if (!matchesRialitFee(amount,payerAmount,payerFee,feePercent)) {
    await env.DB.prepare("INSERT INTO rialit_payments(token,provider_order_id,attempt_no,kind,topup_id,user_id,amount_toman,payer_amount_toman,payer_fee_toman,pay_url,status) VALUES(?,?,?,'topup',?,?,?,?,?,?,'fee_mismatch')")
      .bind(token,providerOrderId,attemptNo,topupId,userId,amount,payerAmount,payerFee,payUrl).run();
    return json({ok:false,error:"rialit_fee_mismatch",expected_payer_amount_toman:expectedPayerAmount(amount,feePercent)},409);
  }
  await env.DB.prepare("INSERT INTO rialit_payments(token,provider_order_id,attempt_no,kind,topup_id,user_id,amount_toman,payer_amount_toman,payer_fee_toman,pay_url,status) VALUES(?,?,?,'topup',?,?,?,?,?,?,'pending')")
    .bind(token,providerOrderId,attemptNo,topupId,userId,amount,payerAmount,payerFee,payUrl).run();
  await env.DB.prepare("UPDATE wallet_topups SET status='awaiting_payment' WHERE id=? AND user_id=?")
    .bind(topupId,userId).run();
  return json({ok:true,pay_url:payUrl,amount_toman:amount,payer_amount_toman:payerAmount,payer_fee_toman:payerFee,fee_percent:feePercent,fee_configuration_matches:true});
}

async function createCardPayment(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json().catch(() => null) as any;
  const orderId = Number(body?.order_id);
  if (!Number.isSafeInteger(orderId) || orderId < 1) return json({ ok: false, error: "invalid_order" }, 400);
  const userId = await ensureUser(env.DB, user);
  const order = await env.DB.prepare("SELECT id,public_id,amount_toman,price_snapshot_toman,status FROM orders WHERE id=? AND user_id=?")
    .bind(orderId,userId).first<any>();
  if (!order || order.status !== "waiting_payment") return json({ ok: false, error: "order_not_payable" }, 409);
  const amount = Number(order.price_snapshot_toman ?? order.amount_toman ?? 0);
  const card = await env.DB.prepare("SELECT value FROM settings WHERE key='card_number'").first<{value:string}>();
  if (!card?.value) return json({ok:false,error:"card_not_configured"},503);
  await env.DB.prepare("INSERT OR IGNORE INTO payments(order_id,user_id,provider,provider_payment_id,amount_toman,status,receipt_type) VALUES(?,?,'card_transfer',?,?,'awaiting_receipt','photo')")
    .bind(orderId,userId,"order:"+order.public_id,amount).run();
  await env.DB.prepare("UPDATE orders SET status='awaiting_receipt',updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?")
    .bind(orderId,userId).run();
  const settings = await env.DB.prepare("SELECT key,value FROM settings WHERE key IN ('card_number','card_holder','card_bank')").all();
  await telegram(env,"sendMessage",{chat_id:user.id,text:"برای پرداخت پرونده، مبلغ را به کارت دفتر واریز کنید و تصویر رسید را همین‌جا ارسال کنید."}).catch(()=>undefined);
  return json({ok:true,amount_toman:amount,settings:Object.fromEntries((settings.results||[]).map((x:any)=>[x.key,x.value]))});
}


const VPN_BASE_PRICE_PER_GB_TOMAN = 6_000;
function gozarbanRoot(env: Env): string {
  const root = (env.GOZARBAN_API_ROOT || "https://gozarban.com").replace(/\/$/, "");
  if (!root.startsWith("https://")) throw new Error("gozarban_invalid_api_root");
  return root;
}
async function getGozarbanPlan(env: Env): Promise<{id:number;name:string}> {
  if (!env.API_VPN) throw new Error("gozarban_api_not_configured");
  const response = await fetch(gozarbanRoot(env) + "/api/user/plans/active", {headers:{authorization:"Bearer "+env.API_VPN,accept:"application/json"},signal:AbortSignal.timeout(12_000)});
  if (!response.ok) throw new Error("gozarban_plans_http_" + response.status);
  const payload = await response.json() as any;
  const lists = [payload?.plans,payload?.data?.plans,payload?.result?.plans,payload?.data,payload?.result,payload?.items];
  const plans = lists.find((x) => Array.isArray(x)) as any[] | undefined;
  if (!plans?.length) throw new Error("gozarban_no_active_plans");
  const configured = Number(env.GOZARBAN_PLAN_ID || 0);
  const candidates = plans.filter((p) => p && p.is_active !== false && p.active !== false && p.enabled !== false);
  const selected = configured ? candidates.find((p) => Number(p.id ?? p.plan_id) === configured) : candidates.find((p) => Number.isSafeInteger(Number(p.id ?? p.plan_id)));
  const id = Number(selected?.id ?? selected?.plan_id);
  if (!Number.isSafeInteger(id) || id < 1) throw new Error("gozarban_plan_id_not_found");
  return {id,name:String(selected?.name || selected?.title || "پلن فعال")};
}
function getGozarbanSubscriptionUrl(payload: any): string | null {
  const objects = [payload,payload?.data,payload?.subscription,payload?.data?.subscription,payload?.result];
  for (const item of objects) {
    if (!item || typeof item !== "object") continue;
    for (const key of ["subscription_url","subscription_link","url","link"]) {
      const value = item[key];
      if (typeof value === "string" && /^(https:\/\/|vless:\/\/|vmess:\/\/|trojan:\/\/|ss:\/\/)/i.test(value)) return value;
    }
    const links = item?.external_data?.links;
    if (Array.isArray(links)) {
      const valid = links.filter((x:any) => typeof x === "string" && /^(https:\/\/|vless:\/\/|vmess:\/\/|trojan:\/\/|ss:\/\/)/i.test(x));
      if (valid.length) return valid.join("\n");
    }
  }
  return null;
}
async function provisionVpnPayment(env: Env, paymentId: number): Promise<void> {
  const job = await env.DB.prepare("SELECT j.*,rp.id AS payment_id,rp.status AS payment_status FROM vpn_provisioning_jobs j JOIN rialit_payments rp ON rp.id=j.rialit_payment_id WHERE j.rialit_payment_id=?").bind(paymentId).first<any>();
  if (!job || job.payment_status !== "paid" || !env.API_VPN) return;
  await env.DB.prepare("UPDATE vpn_provisioning_jobs SET status='processing',attempts=attempts+1,updated_at=CURRENT_TIMESTAMP WHERE rialit_payment_id=? AND status IN ('pending','failed','blocked_waiting_api_schema')").bind(paymentId).run();
  const username = "nyvpn" + job.telegram_user_id + "_" + paymentId;
  try {
    const plan = await getGozarbanPlan(env);
    const root = gozarbanRoot(env);
    const headers = {authorization:"Bearer "+env.API_VPN,accept:"application/json"};
    let existing: any = null;
    const lookup = await fetch(root+"/api/user/subscriptions?search="+encodeURIComponent(username)+"&skip=0&limit=10",{headers,signal:AbortSignal.timeout(15_000)});
    if (lookup.ok) {
      const data = await lookup.json() as any;
      const rows = Array.isArray(data?.subscriptions) ? data.subscriptions : Array.isArray(data?.data?.subscriptions) ? data.data.subscriptions : [];
      existing = rows.find((x:any)=>x?.marzban_username===username || x?.display_name===username || x?.username===username) || null;
    } else if (lookup.status !== 404) throw new Error("gozarban_lookup_http_"+lookup.status);
    let created = existing;
    if (!created) {
      const response = await fetch(root+"/api/user/subscription/create",{method:"POST",headers:{...headers,"content-type":"application/json"},body:JSON.stringify({data_size_gb:String(job.gigabytes),expire_days:String(Number(job.months)*30),plan_id:plan.id,username}),signal:AbortSignal.timeout(25_000)});
      const payload = await response.json().catch(()=>({})) as any;
      if (![200,201].includes(response.status)) throw new Error("gozarban_create_http_"+response.status);
      created = payload?.subscription || payload?.data?.subscription || payload?.data || payload;
    }
    const subscriptionId = created?.id ?? created?.subscription_id ?? null;
    const link = getGozarbanSubscriptionUrl(created);
    if (!subscriptionId && !link) throw new Error("gozarban_response_missing_subscription");
    await env.DB.prepare("UPDATE vpn_provisioning_jobs SET status='completed',provider_subscription_id=?,subscription_url=?,last_error=NULL,updated_at=CURRENT_TIMESTAMP WHERE rialit_payment_id=?").bind(subscriptionId==null?null:String(subscriptionId),link,paymentId).run();
    const message = "✅ پرداخت VPN تأیید و اشتراک شما ساخته شد.\n\nحجم: "+job.gigabytes+" گیگابایت\nمدت: "+job.months+" ماه\n"+(link?"لینک اشتراک شما:\n"+link:"شناسه اشتراک: "+String(subscriptionId)+"\nبرای دریافت لینک با پشتیبانی تماس بگیرید.");
    await telegram(env,"sendMessage",{chat_id:job.telegram_user_id,text:message,disable_web_page_preview:true}).catch(()=>undefined);
  } catch (error) {
    const reason = error instanceof Error ? error.message : "gozarban_unknown_error";
    await env.DB.prepare("UPDATE vpn_provisioning_jobs SET status='failed',last_error=?,updated_at=CURRENT_TIMESTAMP WHERE rialit_payment_id=?").bind(reason.slice(0,200),paymentId).run();
    await telegram(env,"sendMessage",{chat_id:job.telegram_user_id,text:"⚠️ پرداخت VPN تأیید شده، اما ساخت اشتراک در پنل گذربان ناموفق بود. سفارش شما محفوظ است و برای بررسی به پشتیبانی اطلاع داده شد."}).catch(()=>undefined);
  }
}
async function checkVpnApi(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request,env);
  if (!user) return json({ok:false,error:"unauthorized"},401);
  if (!env.API_VPN) return json({ok:false,error:"vpn_payment_not_configured"},503);
  try {
    const plan = await getGozarbanPlan(env);
    return json({ok:true,connected:true,plan_name:plan.name,plan_id:plan.id,base_price_per_gb_toman:VPN_BASE_PRICE_PER_GB_TOMAN,fee_percent:Number(env.PAYMENT_FEE_PERCENT||"12"),rialit_configured:Boolean(env.RIALIT_API_KEY)});
  } catch (error) {
    const detail = error instanceof Error ? error.message : "gozarban_unavailable";
    return json({ok:false,error:"gozarban_not_ready",detail},503);
  }
}

async function createVpnPayment(request: Request, env: Env): Promise<Response> {
  const user = await miniAppUser(request,env);
  if (!user) return json({ok:false,error:"unauthorized"},401);
  if (!env.RIALIT_API_KEY || !env.API_VPN) return json({ok:false,error:"vpn_payment_not_configured"},503);
  const body = await request.json().catch(()=>null) as any;
  const months = Number(body?.months), gigabytes = Number(body?.gigabytes), requestId = String(body?.request_id || "");
  if (![1,2,3,4].includes(months) || !Number.isSafeInteger(gigabytes) || gigabytes<10 || gigabytes>100 || gigabytes%10!==0 || !/^[0-9a-f-]{36}$/i.test(requestId)) return json({ok:false,error:"invalid_vpn_selection"},400);
  try { await getGozarbanPlan(env); } catch (error) {
    const reason = error instanceof Error ? error.message : "gozarban_unavailable";
    return json({ok:false,error:"gozarban_not_ready",detail:reason},503);
  }
  const userId = await ensureUser(env.DB,user);
  const amount = VPN_BASE_PRICE_PER_GB_TOMAN * gigabytes;
  if (amount<50_000 || amount>10_000_000) return json({ok:false,error:"rialit_amount_out_of_range"},400);
  const providerOrderId = "mohajer-vpn-"+user.id+"-"+requestId;
  const previous = await env.DB.prepare("SELECT id,provider_order_id,token,pay_url,payer_amount_toman,payer_fee_toman,status,attempt_no FROM rialit_payments WHERE provider_order_id=? OR provider_order_id LIKE ? ORDER BY attempt_no DESC LIMIT 1").bind(providerOrderId,providerOrderId+"-%").first<any>();
  if (previous?.status==="pending" && previous.pay_url) return json({ok:true,pay_url:previous.pay_url,amount_toman:amount,payer_amount_toman:previous.payer_amount_toman,payer_fee_toman:previous.payer_fee_toman,fee_percent:12});
  if (previous && previous.status==="paid") return json({ok:false,error:"vpn_payment_already_paid"},409);
  const attemptNo = previous ? Number(previous.attempt_no || 1) + (previous.status==="pending" ? 0 : 1) : 1;
  const stableOrderId = previous?.status==="pending" ? String(previous.provider_order_id) : attemptNo===1 ? providerOrderId : providerOrderId+"-"+attemptNo;
  if (!previous || previous.status!=="pending") await env.DB.prepare("INSERT INTO rialit_payments(provider_order_id,attempt_no,kind,user_id,amount_toman,vpn_months,vpn_gigabytes,status) VALUES(?,?,'vpn',?,?,?,?,'pending')").bind(stableOrderId,attemptNo,userId,amount,months,gigabytes).run();
  let response: Response;
  try {
    response = await fetch((env.RIALIT_API_BASE_URL || "https://api.rialit.io/api/v1").replace(/\/$/,"")+"/send",{method:"POST",headers:{authorization:"Bearer "+env.RIALIT_API_KEY,"content-type":"application/json",accept:"application/json"},body:JSON.stringify({amount,order_id:stableOrderId,payer_id:user.id}),signal:AbortSignal.timeout(25_000)});
  } catch { return json({ok:false,error:"rialit_network_error",retry_same_order:true},502); }
  const result = await response.json().catch(()=>({})) as any;
  if (![200,201].includes(response.status)) return json({ok:false,error:response.status===403?"rialit_outbound_ip_not_allowed":response.status===401?"rialit_key_invalid":"rialit_request_failed"},502);
  const token=String(result?.token||""),payerAmount=Number(result?.payer_amount),payerFee=Number(result?.payer_fee);
  if (!/^[A-Za-z0-9]{1,64}$/.test(token) || !Number.isSafeInteger(payerAmount) || !Number.isSafeInteger(payerFee) || Number(result?.amount)!==amount) return json({ok:false,error:"rialit_invalid_response"},502);
  const feePercent=Number(env.PAYMENT_FEE_PERCENT||"12"),payUrl="https://pay.rialit.io/v1/"+token;
  if (!matchesRialitFee(amount,payerAmount,payerFee,feePercent)) {
    await env.DB.prepare("UPDATE rialit_payments SET token=?,pay_url=?,payer_amount_toman=?,payer_fee_toman=?,status='fee_mismatch' WHERE provider_order_id=?").bind(token,payUrl,payerAmount,payerFee,stableOrderId).run();
    return json({ok:false,error:"rialit_fee_mismatch",expected_payer_amount_toman:expectedPayerAmount(amount,feePercent)},409);
  }
  await env.DB.prepare("UPDATE rialit_payments SET token=?,pay_url=?,payer_amount_toman=?,payer_fee_toman=? WHERE provider_order_id=? AND status='pending'").bind(token,payUrl,payerAmount,payerFee,stableOrderId).run();
  return json({ok:true,pay_url:payUrl,amount_toman:amount,payer_amount_toman:payerAmount,payer_fee_toman:payerFee,fee_percent:feePercent});
}
async function handleRialitWebhook(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
  const allowed = new Set((env.RIALIT_WEBHOOK_IPS || "").split(",").map((x) => x.trim()).filter(Boolean));
  const sourceIp = request.headers.get("cf-connecting-ip") || "";
  if (!sourceIp || !allowed.has(sourceIp)) return json({ ok: false, error: "source_ip_not_allowed" }, 403);

  const eventHeader = request.headers.get("x-rialit-event") || "";
  const deliveryHeader = request.headers.get("x-rialit-delivery") || "";
  const payload = await request.json().catch(() => null) as any;
  if (!payload || typeof payload !== "object") return json({ ok: false, error: "invalid_payload" }, 400);
  const eventId = String(payload.event_id || "");
  const eventType = String(payload.type || "");
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(eventId) || eventId !== deliveryHeader || eventType !== eventHeader) {
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
    "SELECT rp.*, u.telegram_id AS user_telegram_id FROM rialit_payments rp JOIN users u ON u.id = rp.user_id WHERE rp.token = ?"
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
  const verified = await verifiedResponse.json().catch(() => ({})) as any;
  const status = String(verified?.status || verified?.data?.status || "");
  const verifiedAmount = Number(verified?.amount ?? verified?.data?.amount);
  const verifiedPayer = Number(verified?.payer_id ?? verified?.data?.payer_id);
  const verifiedOrderId = String(verified?.order_id ?? verified?.data?.order_id ?? "");
  const verifiedPayerAmount = Number(verified?.payer_amount ?? verified?.data?.payer_amount);
  const verifiedPayerFee = Number(verified?.payer_fee ?? verified?.data?.payer_fee);
  if (status === "paid" && (
    verifiedAmount !== Number(payment.amount_toman) ||
    verifiedPayer !== Number(payment.user_telegram_id) ||
    verifiedOrderId !== payment.provider_order_id ||
    verifiedPayerAmount !== Number(payment.payer_amount_toman) ||
    verifiedPayerFee !== Number(payment.payer_fee_toman)
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
      env.DB.prepare("INSERT OR IGNORE INTO payments(order_id,user_id,provider,provider_payment_id,amount_toman,receipt_file_id,receipt_type,status,verified_at,provider_metadata_json,source_rialit_payment_id) SELECT ?,?,'rialit',?,?,NULL,'rialit','approved',CURRENT_TIMESTAMP,?,? WHERE changes() = 1")
        .bind(payment.order_id, payment.user_id, payment.token, payment.amount_toman, JSON.stringify({ payer_amount_toman: payment.payer_amount_toman, payer_fee_toman: payment.payer_fee_toman }), payment.id)
    );
  }

  if (status === "paid" && payment.kind === "topup" && payment.topup_id) {
    statements.push(
      env.DB.prepare("UPDATE wallet_topups SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP WHERE id = ? AND status IN ('awaiting_payment','awaiting_receipt','waiting_receipt_review') AND changes() = 1")
        .bind(payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO wallets(user_id,balance_toman) SELECT user_id,0 FROM wallet_topups WHERE id = ? AND status = 'approved'")
        .bind(payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO wallet_credit_events(source_key) SELECT 'rialit:' || ? WHERE EXISTS (SELECT 1 FROM wallet_topups WHERE id = ? AND status = 'approved') AND NOT EXISTS (SELECT 1 FROM wallet_credit_events WHERE source_key = 'rialit:' || ?) AND NOT EXISTS (SELECT 1 FROM wallet_transactions WHERE topup_id = ?)")
        .bind(payment.id, payment.topup_id, payment.id, payment.topup_id),
      env.DB.prepare("UPDATE wallets SET balance_toman = balance_toman + ? WHERE user_id = (SELECT user_id FROM wallet_topups WHERE id = ?) AND changes() = 1")
        .bind(payment.amount_toman, payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO wallet_transactions(user_id,amount_toman,balance_after_toman,kind,description,topup_id,source_rialit_payment_id) SELECT w.user_id,?,w.balance_toman,'topup',?, ?, ? FROM wallets w JOIN wallet_topups t ON t.user_id = w.user_id WHERE t.id = ? AND changes() = 1")
        .bind(payment.amount_toman, `افزایش اعتبار ریالت #${payment.topup_id}`, payment.topup_id, payment.id, payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO payments(user_id,provider,provider_payment_id,amount_toman,receipt_type,status,verified_at,provider_metadata_json,source_rialit_payment_id) SELECT ?, 'rialit', ?, ?, 'online', 'approved', CURRENT_TIMESTAMP, ?, ? WHERE EXISTS (SELECT 1 FROM wallet_topups WHERE id=? AND status='approved')")
        .bind(payment.user_id,payment.token,payment.amount_toman,JSON.stringify({payer_amount_toman:payment.payer_amount_toman,payer_fee_toman:payment.payer_fee_toman}),payment.id,payment.topup_id),
    );
  }

  await env.DB.batch(statements);
  if (status === "paid" && payment.kind === "vpn") {
    await env.DB.prepare("INSERT OR IGNORE INTO vpn_provisioning_jobs(rialit_payment_id,telegram_user_id,months,gigabytes,status) VALUES(?,?,?,?,'pending')").bind(payment.id,Number(payment.user_telegram_id),Number(payment.vpn_months||0),Number(payment.vpn_gigabytes||0)).run();
    ctx.waitUntil(provisionVpnPayment(env,payment.id));
  }
  if (status === "paid" && payment.kind !== "vpn") {
    ctx.waitUntil(telegram(env,"sendMessage",{chat_id:payment.user_telegram_id,text:"✅ پرداخت شما توسط ریالت‌پی تأیید شد. برای مشاهده وضعیت پرونده، مینی‌اپ را باز کنید."}).catch(()=>undefined));
  }
  return json({ ok: true, action: status });
}


const IMPORTABLE_COLUMNS: Record<string, string[]> = {
  users: ["id","telegram_id","first_name","last_name","username","created_at","updated_at"],
  services: ["id","code","name","price_toman","enabled","description"],
  orders: ["id","public_id","user_id","service_id","price_snapshot_toman","status","data_json","created_at","updated_at"],
  payments: ["id","order_id","amount_toman","receipt_file_id","receipt_type","status","source_rialit_payment_id","created_at"],
  variza_payments: ["id","slug","kind","order_id","topup_id","user_id","amount_toman","pay_url","status","attempt_code","expires_at","created_at","paid_at"],
  rialit_payments: ["id","token","provider_order_id","attempt_no","kind","order_id","topup_id","user_id","amount_toman","payer_amount_toman","payer_fee_toman","vpn_months","vpn_gigabytes","pay_url","status","created_at","paid_at","delivered_at"],
  wallets: ["id","user_id","balance_toman","created_at","updated_at"],
  wallet_transactions: ["id","user_id","amount_toman","balance_after_toman","kind","description","order_id","topup_id","source_rialit_payment_id","created_at"],
  wallet_topups: ["id","user_id","amount_toman","receipt_file_id","receipt_type","status","created_at","reviewed_at"],
  discount_codes: ["id","code","kind","value","active","max_uses","used_count","expires_at","created_at"],
  documents: ["id","order_id","document_type","telegram_file_id","review_status","reviewed_by_telegram_id","reviewed_at","created_at"],
  tickets: ["id","order_id","status","created_at","updated_at"],
  ticket_messages: ["id","ticket_id","sender_type","sender_telegram_id","content_type","text","file_id","created_at"],
  settings: ["id","key","value"],
  audit_logs: ["id","actor_telegram_id","action","order_id","details_json","created_at"],
  companions: ["id","order_id","full_name","mobile","created_at"],
  operators: ["id","telegram_id","display_name","role","permissions_json","active","created_at","updated_at"]
};

function authorizedMigration(request: Request, env: Env): boolean {
  const secret = env.MIGRATION_SECRET || "";
  return Boolean(secret) && request.headers.get("authorization") === "Bearer " + secret;
}

async function handleMigrationImport(request: Request, env: Env): Promise<Response> {
  if (!authorizedMigration(request, env)) return text("forbidden", 403);
  const body = await request.json().catch(() => null) as any;
  const table = String(body?.table || "");
  const columns = body?.columns;
  const rows = body?.rows;
  const batchId = String(body?.batch_id || "");
  const checksum = String(body?.checksum || "");
  if (!IMPORTABLE_COLUMNS[table] || !Array.isArray(columns) || !Array.isArray(rows) ||
      rows.length > 100 || !batchId || batchId.length > 160 || !checksum ||
      columns.length < 1 || columns.length > 32 ||
      columns.some((c: unknown) => typeof c !== "string" || !IMPORTABLE_COLUMNS[table].includes(c)) ||
      new Set(columns).size !== columns.length ||
      rows.some((r: unknown) => !Array.isArray(r) || r.length !== columns.length)) {
    return json({ ok: false, error: "invalid_import_batch" }, 400);
  }

  const prior = await env.DB.prepare("SELECT batch_id FROM migration_batches WHERE batch_id = ?")
    .bind(batchId).first();
  if (prior) return json({ ok: true, duplicate: true });

  const placeholders = columns.map(() => "?").join(",");
  const columnSql = columns.map((c: string) => '"' + c + '"').join(",");
  const insertSql = 'INSERT OR IGNORE INTO "' + table + '" (' + columnSql + ') VALUES (' + placeholders + ')';
  const statements: D1PreparedStatement[] = rows.map((row: unknown[]) =>
    env.DB.prepare(insertSql).bind(...row as any[])
  );
  statements.push(env.DB.prepare(
    "INSERT OR IGNORE INTO migration_batches(batch_id,table_name,row_count,checksum) VALUES(?,?,?,?)"
  ).bind(batchId, table, rows.length, checksum));
  await env.DB.batch(statements);
  return json({ ok: true, table, imported_rows: rows.length, batch_id: batchId });
}

async function handleMigrationManifest(request: Request, env: Env): Promise<Response> {
  if (!authorizedMigration(request, env)) return text("forbidden", 403);
  const body = await request.json().catch(() => null) as any;
  if (!body || typeof body !== "object" || !body.table_counts || typeof body.table_counts !== "object") {
    return json({ ok: false, error: "invalid_manifest" }, 400);
  }
  await env.DB.prepare(
    "INSERT OR REPLACE INTO migration_manifest(id,manifest_json,created_at) VALUES(1,?,CURRENT_TIMESTAMP)"
  ).bind(JSON.stringify(body)).run();
  return json({ ok: true });
}

async function handleMigrationStatus(request: Request, env: Env): Promise<Response> {
  if (!authorizedMigration(request, env)) return text("forbidden", 403);
  const counts: Record<string, number> = {};
  for (const table of Object.keys(IMPORTABLE_COLUMNS)) {
    const row = await env.DB.prepare('SELECT COUNT(*) AS n FROM "' + table + '"').first<{n:number}>();
    counts[table] = Number(row?.n || 0);
  }
  const manifest = await env.DB.prepare("SELECT manifest_json FROM migration_manifest WHERE id = 1").first<{manifest_json:string}>();
  const batches = await env.DB.prepare("SELECT COUNT(*) AS n FROM migration_batches").first<{n:number}>();
  return json({ ok: true, table_counts: counts, batch_count: Number(batches?.n || 0), manifest: manifest?.manifest_json ? JSON.parse(manifest.manifest_json) : null });
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname !== "/webhooks/telegram") ctx.waitUntil(ensureTelegramWebhook(env,url.origin));
    if (url.pathname === "/health") return json({ ok: true, service: "help-yar-mohajer", platform: "cloudflare-workers" });
    if (url.pathname === "/internal/import" && request.method === "POST") return handleMigrationImport(request, env);
    if (url.pathname === "/internal/manifest" && request.method === "POST") return handleMigrationManifest(request, env);
    if (url.pathname === "/internal/status" && request.method === "GET") return handleMigrationStatus(request, env);
    if (url.pathname === "/webhooks/telegram" && request.method === "POST") return handleTelegram(request, env);
    if (url.pathname === "/webhooks/rialit" && request.method === "POST") return handleRialitWebhook(request, env, ctx);
    if (url.pathname === "/api/miniapp/bootstrap" && request.method === "GET") return bootstrap(request, env);
    if (url.pathname === "/api/miniapp/orders" && request.method === "POST") return createOrder(request, env);
    if (url.pathname === "/api/miniapp/payments/rialit" && request.method === "POST") return createRialitPayment(request, env);
    if (url.pathname === "/api/miniapp/vpn/status" && request.method === "GET") return checkVpnApi(request,env);
    if (url.pathname === "/api/miniapp/vpn/pay" && request.method === "POST") return createVpnPayment(request, env);
    if (url.pathname === "/api/miniapp/payments/card" && request.method === "POST") return createCardPayment(request, env);
    if (url.pathname === "/api/miniapp/topups" && request.method === "POST") return createWalletTopup(request, env);
    if (url.pathname === "/api/miniapp/topups/rialit" && request.method === "POST") return createRialitTopupPayment(request, env);
    if (url.pathname === "/app" || url.pathname === "/app/") {
      return new Response(MINIAPP_HTML,{headers:{"content-type":"text/html; charset=utf-8","cache-control":"no-store"}});
    }
    if (url.pathname === "/app.js") return new Response(MINIAPP_JS,{headers:{"content-type":"application/javascript; charset=utf-8","cache-control":"no-store"}});
    if (url.pathname.startsWith("/api/")) return json({ ok: false, error: "not_found" }, 404);
    return text("not found",404);
  },
};
