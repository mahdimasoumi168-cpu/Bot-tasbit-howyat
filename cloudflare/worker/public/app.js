(() => {
  const tg = window.Telegram?.WebApp;
  tg?.ready();
  tg?.expand();
  const $ = (id) => document.getElementById(id);
  let state = { data: null, selected: null };
  const money = (n) => new Intl.NumberFormat("fa-IR").format(Number(n || 0)) + " تومان";
  const api = async (path, options = {}) => {
    const response = await fetch(path, {
      ...options,
      headers: {
        "content-type": "application/json",
        "x-telegram-init-data": tg?.initData || "",
        ...(options.headers || {})
      }
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) {
      const messages = {
        unauthorized:"برای امنیت، مینی‌اپ را از داخل ربات تلگرام باز کنید.",
        rialit_not_configured:"کلید درگاه ریالت در Worker ثبت نشده است.",
        rialit_key_invalid:"کلید پذیرنده ریالت معتبر نیست.",
        rialit_outbound_ip_not_allowed:"IP خروجی Worker در فهرست IPهای مجاز پذیرنده ریالت نیست.",
        rialit_merchant_inactive:"حساب پذیرنده ریالت فعال نیست.",
        rialit_fee_mismatch:"کارمزد درگاه با ۱۲٪ تنظیم‌شده مطابقت ندارد؛ پرداخت متوقف شد. تنظیمات پذیرنده ریالت باید بررسی شود.",
        rialit_network_error:"ارتباط Worker با ریالت برقرار نشد. سفارش ثبت شده و می‌توانید دوباره تلاش کنید.",
        rialit_retry_later:"درگاه موقتاً پاسخ نمی‌دهد؛ چند دقیقه بعد دوباره تلاش کنید.",
        rialit_amount_out_of_range:"مبلغ خارج از محدوده مجاز ریالت است؛ از کارت‌به‌کارت استفاده کنید.",
        card_not_configured:"شماره کارت دفتر هنوز در تنظیمات مدیریت ثبت نشده است.",
        order_not_payable:"این سفارش در وضعیت قابل پرداخت نیست.",
        service_unavailable:"این خدمت فعلاً فعال نیست.",
        vpn_payment_not_configured:"اتصال پرداخت یا API فیلترشکن در Worker تنظیم نشده است.",
        gozarban_not_ready:"اتصال پنل فیلترشکن یا پلن فعال در دسترس نیست.",
        invalid_vpn_selection:"حجم یا مدت انتخابی معتبر نیست.",
        vpn_payment_already_paid:"این سفارش VPN قبلاً پرداخت شده است."
      };
      let message = messages[data.error] || data.error || "خطا در دریافت اطلاعات";
      if (data.detail) message += " (" + String(data.detail) + ")";
      throw new Error(message);
    }
    return data;
  };
  const icons = { identity:"🪪", khodnevis:"🏠", fida:"🧾", dolatman_login:"🔐", student_screening:"🎓", other_service:"📝" };
  const fields = {
    identity: [
      ["full_name","نام و نام خانوادگی مطابق مدرک","text"],
      ["mobile","شماره موبایل در دسترس","tel"],
      ["birth_date","تاریخ تولد (شمسی)","text"],
      ["return_date","تاریخ بازگشت (در صورت وجود)","text"],
      ["consulate","کنسولگری موردنظر","select","زاهدان|مشهد"],
      ["document_type","نوع مدرک","select","کارت آمایش|گذرنامه|دفترچه اقامت|فاقد مدرک|سایر"],
      ["document_number","شماره شناسه مدرک شناسایی","text"],
      ["relative_tazkira","توضیح مدرک تذکره اقارب نزدیک","textarea"]
    ],
    khodnevis: [
      ["full_name","نام و نام خانوادگی مستأجر","text"],
      ["mobile","شماره تماس","tel"],
      ["property_address","نشانی کامل ملک","textarea"],
      ["owner_name","نام صاحبخانه","text"],
      ["property_code","شناسه ملک / کد پستی","text"]
    ],
    fida: [
      ["full_name","نام و نام خانوادگی","text"],
      ["mobile","شماره موبایل در دسترس","tel"],
      ["document_number","شماره مدرک شناسایی","text"]
    ],
    dolatman_login: [
      ["mobile","شماره موبایل ورود به دولت من","tel"],
      ["own_name_mobile","آیا سیم‌کارت به نام خودتان است؟","select","بله|خیر"],
      ["notes","توضیحات","textarea"]
    ],
    student_screening: [
      ["student_count","تعداد دانش‌آموزان","number"],
      ["school_name","نام مدرسه","text"],
      ["notes","توضیحات","textarea"]
    ],
    other_service: [
      ["description","شرح درخواست","textarea"]
    ]
  };
  function renderServices(items) {
    $("services").innerHTML = "";
    if (!items.length) $("services").innerHTML = '<div class="empty">فعلاً خدمتی برای ثبت فعال نیست.</div>';
    items.forEach((service) => {
      const card = document.createElement("article");
      card.className = "service";
      const desc = service.description || "برای مشاهده شرایط و ثبت درخواست انتخاب کنید.";
      card.innerHTML = '<div class="symbol">' + (icons[service.code] || "📄") + '</div><h3></h3><p></p><button type="button">ثبت درخواست</button>';
      card.querySelector("h3").textContent = service.name;
      card.querySelector("p").textContent = desc;
      card.querySelector("button").addEventListener("click", () => openForm(service));
      $("services").appendChild(card);
    });
    const vpn = document.createElement("article");
    vpn.className = "service vpn-service";
    vpn.innerHTML = '<div class="symbol">🔐</div><h3>خرید فیلترشکن</h3><p>قیمت پایه هر گیگ ۶٬۰۰۰ تومان؛ کارمزد درگاه ریالت ۱۲٪ جداگانه محاسبه می‌شود.</p><button type="button">انتخاب حجم و مدت</button>';
    vpn.querySelector("button").addEventListener("click", openVpnForm);
    $("services").appendChild(vpn);
  }
  function openVpnForm() {
    const root = $("sheetRoot");
    root.className = "backdrop";
    root.innerHTML = '<section class="sheet"><h2>🔐 خرید فیلترشکن</h2><p class="muted">قیمت پایه هر گیگ: ۶٬۰۰۰ تومان. کارمزد ریالت: ۱۲٪ از مبلغ پایه.</p><label class="field"><span>مدت اشتراک</span><select id="vpnMonths"><option value="1">۱ ماه</option><option value="2">۲ ماه</option><option value="3">۳ ماه</option><option value="4">۴ ماه</option></select></label><label class="field"><span>حجم اشتراک</span><select id="vpnGb"></select></label><div id="vpnPrice" class="notice"></div><div class="actions"><button class="secondary" id="vpnCheck">بررسی اتصال API فیلترشکن</button><button class="primary" id="vpnPay">ادامه و دریافت لینک پرداخت</button><button class="secondary" id="vpnClose">بازگشت</button></div><div id="vpnResult"></div></section>';
    const gb = $("vpnGb");
    for (let n=10;n<=100;n+=10) { const option=document.createElement("option"); option.value=String(n); option.textContent=new Intl.NumberFormat("fa-IR").format(n)+" گیگابایت"; gb.appendChild(option); }
    const updatePrice = () => {
      const base = Number(gb.value || 10) * 6000;
      const fee = Math.ceil(base * 12 / 100);
      $("vpnPrice").textContent = "مبلغ پایه: " + money(base) + " | کارمزد ۱۲٪: " + money(fee) + " | مبلغ تقریبی پرداخت: " + money(base+fee);
    };
    gb.addEventListener("change",updatePrice);
    $("vpnMonths").addEventListener("change",updatePrice);
    updatePrice();
    $("vpnClose").onclick = closeSheet;
    $("vpnCheck").onclick = async () => {
      const b=$("vpnCheck"); b.disabled=true; b.textContent="در حال بررسی اتصال گذربان…";
      try {
        const result=await api("/api/miniapp/vpn/status");
        $("vpnResult").innerHTML='<div class="notice success">✅ اتصال API گذربان برقرار است.<br>پلن فعال: <strong>'+escapeHtml(result.plan_name)+'</strong><br>قیمت پایه هر گیگ: '+money(result.base_price_per_gb_toman)+' تومان<br>کارمزد پرداخت ریالت: '+result.fee_percent+'٪</div>';
      } catch(error) {
        $("vpnResult").innerHTML='<div class="notice error">'+escapeHtml(error.message)+'</div>';
      } finally { b.disabled=false; b.textContent="بررسی اتصال API فیلترشکن"; }
    };
    $("vpnPay").onclick = async () => {
      const b=$("vpnPay"); b.disabled=true; b.textContent="در حال بررسی اتصال و ساخت لینک…";
      try {
        const result=await api("/api/miniapp/vpn/pay",{method:"POST",body:JSON.stringify({months:Number($("vpnMonths").value),gigabytes:Number(gb.value),request_id:crypto.randomUUID()})});
        $("vpnResult").innerHTML='<div class="notice success">مبلغ پایه: '+money(result.amount_toman)+'<br>کارمزد ریالت: '+money(result.payer_fee_toman)+'<br>مبلغ نهایی درگاه: <strong>'+money(result.payer_amount_toman)+'</strong></div><button class="primary" id="vpnOpenPay">ورود به درگاه امن</button>';
        $("vpnOpenPay").onclick=()=>tg?.openLink?tg.openLink(result.pay_url):window.open(result.pay_url,"_blank");
      } catch(error) {
        $("vpnResult").innerHTML='<div class="notice error">'+escapeHtml(error.message)+'</div>';
      } finally { b.disabled=false; b.textContent="ادامه و دریافت لینک پرداخت"; }
    };
  }
  function renderOrders(items) {
    if (!items.length) { $("orders").innerHTML = '<div class="empty">هنوز پرونده‌ای ثبت نکرده‌اید.</div>'; return; }
    $("orders").innerHTML = items.map((o) => `<div class="order"><div><strong>${escapeHtml(o.service_name)}</strong><div class="muted">${escapeHtml(o.public_id || "")}</div></div><div style="text-align:left"><div class="status">${escapeHtml(statusLabel(o.status))}</div><div class="muted">${money(o.price_snapshot_toman)}</div></div></div>`).join("");
  }
  function statusLabel(s) {
    return ({draft:"پیش‌نویس",waiting_payment:"در انتظار پرداخت",waiting_receipt_review:"در انتظار بررسی رسید",payment_approved:"پرداخت تأیید شد",in_progress:"در حال انجام",waiting_user:"منتظر اطلاعات مشترک",completed:"تکمیل شد",rejected:"رد شده"})[s] || "در حال پیگیری";
  }
  function escapeHtml(v) { return String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
  function openForm(service) {
    state.selected = service;
    const root = $("sheetRoot");
    root.className = "backdrop";
    const serviceFields = fields[service.code] || fields.other_service;
    const rulesText = service.rules_text || "پیش از ثبت، مدارک و اطلاعات را دقیق و مطابق مدرک وارد کنید. ثبت درخواست به معنی تضمین نتیجه نهایی نیست.";
    root.innerHTML = `<section class="sheet"><h2>${escapeHtml(service.name)}</h2><div class="muted">مبلغ پایه: ${money(service.price_toman)}</div><div id="rule" class="notice">${escapeHtml(rulesText)}</div><form id="orderForm">${serviceFields.map(([name,label,type,opts]) => {
      if (type === "select") return `<label class="field"><span>${label}</span><select name="${name}" required>${opts.split("|").map(v=>`<option value="${v}">${v}</option>`).join("")}</select></label>`;
      if (type === "textarea") return `<label class="field"><span>${label}</span><textarea name="${name}" rows="3"></textarea></label>`;
      return `<label class="field"><span>${label}</span><input name="${name}" type="${type}" ${name==="student_count"?"min='1'":""} required></label>`;
    }).join("")}<label class="field"><span><input name="rules_accepted" type="checkbox" required style="width:auto;margin-left:8px"> قوانین این خدمت را خواندم و می‌پذیرم.</span></label><div class="actions"><button class="primary" type="submit">ثبت و ادامه</button><button class="secondary" type="button" id="closeSheet">بازگشت</button></div></form><div id="formError" class="notice error hidden"></div></section>`;
    $("closeSheet").onclick = closeSheet;
    $("orderForm").onsubmit = submitOrder;
    root.addEventListener("click", (e) => { if (e.target === root) closeSheet(); }, { once: true });
  }
  function closeSheet() { $("sheetRoot").className = "hidden"; $("sheetRoot").innerHTML = ""; }
  async function submitOrder(event) {
    event.preventDefault();
    const formData = Object.fromEntries(new FormData(event.currentTarget).entries());
    const rulesAccepted = formData.rules_accepted === "on";
    delete formData.rules_accepted;
    if (!rulesAccepted) {
      $("formError").textContent = "برای ادامه باید قوانین خدمت را بپذیرید.";
      $("formError").classList.remove("hidden");
      return;
    }
    const button = event.currentTarget.querySelector("button[type=submit]");
    button.disabled = true; button.textContent = "در حال ثبت…";
    try {
      const result = await api("/api/miniapp/orders", { method:"POST", body:JSON.stringify({ service_code:state.selected.code, form_data:formData, rules_accepted:true }) });
      await showPayment(result);
    } catch (error) {
      $("formError").textContent = error.message;
      $("formError").classList.remove("hidden");
      button.disabled = false; button.textContent = "ثبت و ادامه";
    }
  }
  async function showPayment(order) {
    const root = $("sheetRoot");
    const amount = Number(order.amount_toman || 0);
    root.innerHTML = `<section class="sheet"><h2>درخواست ${escapeHtml(order.public_id)} ثبت شد</h2><div class="notice success">اطلاعات شما ثبت شد. روش پرداخت را انتخاب کنید.</div><div class="panel"><div class="muted">مبلغ پایه خدمت</div><strong>${money(amount)}</strong><p class="muted">درگاه پرداخت رمز پویا: کارمزد ۱۲٪ از تنظیمات پذیرنده ریالت محاسبه می‌شود و مبلغ دقیق پیش از پرداخت نمایش داده خواهد شد.</p></div><div class="actions"><button class="primary" id="rialitPay">🔐 درگاه پرداخت رمز پویا</button><button class="secondary" id="cardPay">💳 کارت به کارت</button></div><div id="paymentResult"></div><div class="actions"><button class="secondary" id="closePayment">بستن</button></div></section>`;
    $("closePayment").onclick = closeSheet;
    $("rialitPay").onclick = async () => {
      const b = $("rialitPay"); b.disabled = true; b.textContent = "در حال اتصال به درگاه…";
      try {
        const result = await api("/api/miniapp/payments/rialit", { method:"POST", body:JSON.stringify({order_id:order.order_id}) });
        $("paymentResult").innerHTML = `<div class="notice success">مبلغ پرداختی در درگاه: <strong>${money(result.payer_amount_toman)}</strong><br>کارمزد ریالت: ${money(result.payer_fee_toman)}<br>مبلغ پایه پرونده: ${money(result.amount_toman)}</div><button class="primary" id="openRialit">ورود به درگاه امن</button>`;
        $("openRialit").onclick = () => tg?.openLink ? tg.openLink(result.pay_url) : window.open(result.pay_url, "_blank");
      } catch (error) {
        $("paymentResult").innerHTML = `<div class="notice error">${escapeHtml(error.message)}</div>`;
      } finally { b.disabled = false; b.textContent = "🔐 درگاه پرداخت رمز پویا"; }
    };
    $("cardPay").onclick = async () => {
      const b = $("cardPay"); b.disabled = true;
      try {
        const result = await api("/api/miniapp/payments/card", { method:"POST", body:JSON.stringify({order_id:order.order_id}) });
        const settings = result.settings || {};
        const number = settings.card_number || state.data?.settings?.card_number || "";
        const holder = settings.card_holder || state.data?.settings?.card_holder || "";
        const bank = settings.card_bank || state.data?.settings?.card_bank || "";
        if (number) {
          $("paymentResult").innerHTML = '<div class="notice">مبلغ کارت‌به‌کارت: <strong>' + money(amount) + '</strong><br>شماره کارت: <strong>' + escapeHtml(number) + '</strong><br>به نام: <strong>' + escapeHtml(holder || "—") + '</strong><br>بانک: ' + escapeHtml(bank || "—") + '<br>پس از واریز، تصویر رسید را در گفتگوی ربات ارسال کنید.</div><button class="secondary" id="copyCard">کپی شماره کارت</button>';
          $("copyCard").onclick = async () => { try { await navigator.clipboard.writeText(number); $("copyCard").textContent = "کپی شد"; } catch { $("copyCard").textContent = number; } };
        } else {
          $("paymentResult").innerHTML = '<div class="notice error">اطلاعات کارت دفتر هنوز در تنظیمات مدیریت ثبت نشده است.</div>';
        }
      } catch (error) {
        $("paymentResult").innerHTML = '<div class="notice error">' + escapeHtml(error.message) + '</div>';
      } finally { b.disabled = false; }
    };
  }
  function renderLegacy(legacy) {
    const topups = legacy?.wallet_topups || [];
    const payments = legacy?.rialit_payments || [];
    if (!topups.length && !payments.length) return;
    const rows = [];
    topups.forEach(x => rows.push({label:"افزایش اعتبار",amount:x.amount_toman,status:x.status,date:x.created_at}));
    payments.forEach(x => rows.push({label:"پرداخت ریالت",amount:x.amount_toman,status:x.status,date:x.created_at}));
    const panel = document.createElement("section");
    panel.className = "panel";
    panel.innerHTML = "<h3>سوابق قبلی حساب</h3>" + rows.map(x => "<div class=\"order\"><div><strong>" + escapeHtml(x.label) + "</strong><div class=\"muted\">" + escapeHtml(x.date || "") + "</div></div><div style=\"text-align:left\"><strong>" + money(x.amount) + "</strong><div class=\"muted\">" + escapeHtml(x.status === "paid" || x.status === "approved" ? "پرداخت تأیید شده" : x.status === "payment_link_failed" ? "ساخت لینک ناموفق" : x.status) + "</div></div></div>").join("");
    document.querySelector(".shell").appendChild(panel);
  }
  function openTopup() {
    const root = $("sheetRoot");
    root.className = "backdrop";
    root.innerHTML = '<section class="sheet"><h2>افزایش اعتبار حساب</h2><div class="muted">مبلغ را به تومان وارد کنید. حداقل کارت‌به‌کارت ۲۰٬۰۰۰ و حداقل ریالت ۵۰٬۰۰۰ تومان است.</div><label class="field"><span>مبلغ افزایش اعتبار</span><input id="topupAmount" type="number" min="20000" max="10000000" step="1000" placeholder="مثلاً ۱۰۰۰۰۰"></label><div class="actions"><button class="primary" id="topupRialit">درگاه پرداخت رمز پویا</button><button class="secondary" id="topupCard">کارت به کارت</button></div><div id="topupResult"></div><div class="actions"><button class="secondary" id="closeTopup">بازگشت</button></div></section>';
    $("closeTopup").onclick = closeSheet;
    $("topupRialit").onclick = async () => {
      const amount = Number($("topupAmount").value);
      const b = $("topupRialit"); b.disabled = true;
      try {
        const topup = await api("/api/miniapp/topups", {method:"POST",body:JSON.stringify({amount_toman:amount,method:"rialit"})});
        const result = await api("/api/miniapp/topups/rialit", {method:"POST",body:JSON.stringify({topup_id:topup.topup_id})});
        $("topupResult").innerHTML = '<div class="notice success">مبلغ پایه: ' + money(result.amount_toman) + '<br>کارمزد ریالت: ' + money(result.payer_fee_toman) + '<br>مبلغ نهایی درگاه: <strong>' + money(result.payer_amount_toman) + '</strong></div><button class="primary" id="openTopupRialit">ورود به درگاه</button>';
        $("openTopupRialit").onclick = () => tg?.openLink ? tg.openLink(result.pay_url) : window.open(result.pay_url,"_blank");
      } catch(error) { $("topupResult").innerHTML = '<div class="notice error">' + escapeHtml(error.message) + '</div>'; }
      finally { b.disabled = false; }
    };
    $("topupCard").onclick = async () => {
      const amount = Number($("topupAmount").value);
      const b = $("topupCard"); b.disabled = true;
      try {
        await api("/api/miniapp/topups", {method:"POST",body:JSON.stringify({amount_toman:amount,method:"card"})});
        const settings = state.data?.settings || {};
        const number = settings.card_number || "";
        if (!number) {
          $("topupResult").innerHTML = '<div class="notice error">اطلاعات کارت دفتر هنوز در تنظیمات مدیریت ثبت نشده است.</div>';
        } else {
          $("topupResult").innerHTML = '<div class="notice">مبلغ واریز: <strong>' + money(amount) + '</strong><br>شماره کارت: <strong>' + escapeHtml(number) + '</strong><br>به نام: ' + escapeHtml(settings.card_holder || "—") + '<br>پس از واریز، رسید را در گفتگوی ربات ارسال کنید.</div><button class="secondary" id="copyTopupCard">کپی شماره کارت</button>';
          $("copyTopupCard").onclick = async () => { try { await navigator.clipboard.writeText(number); $("copyTopupCard").textContent = "کپی شد"; } catch { $("copyTopupCard").textContent = number; } };
        }
      } catch(error) { $("topupResult").innerHTML = '<div class="notice error">' + escapeHtml(error.message) + '</div>'; }
      finally { b.disabled = false; }
    };
  }
  function setTheme(theme) {
    document.body.dataset.theme = theme;
    const button = $("themeButton");
    if (button) {
      button.textContent = theme === "dark" ? "☀️ حالت روز" : "🌙 حالت شب";
      button.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    }
    try { localStorage.setItem("netyar-theme", theme); } catch {}
  }
  function initTheme() {
    let saved = "";
    try { saved = localStorage.getItem("netyar-theme") || ""; } catch {}
    setTheme(saved === "dark" || (!saved && tg?.colorScheme === "dark") ? "dark" : "light");
    $("themeButton")?.addEventListener("click", () => setTheme(document.body.dataset.theme === "dark" ? "light" : "dark"));
  }
  async function boot() {
    initTheme();
    try {
      const data = await api("/api/miniapp/bootstrap");
      state.data = data;
      $("balance").textContent = money(data.wallet.balance_toman);
      renderServices(data.services || []);
      renderOrders(data.orders || []);
      renderLegacy(data.legacy);
      $("walletButton").onclick = openTopup;
    } catch (error) {
      $("services").innerHTML = `<div class="empty">${escapeHtml(error.message)}<br>این صفحه باید از داخل ربات تلگرام باز شود.</div>`;
      $("orders").innerHTML = "";
    }
  }
  boot();
})();
