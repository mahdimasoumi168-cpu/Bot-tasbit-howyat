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
    if (!response.ok || data.ok === false) throw new Error(data.error || "خطا در دریافت اطلاعات");
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
    if (!items.length) { $("services").innerHTML = '<div class="empty">فعلاً خدمتی برای ثبت فعال نیست.</div>'; return; }
    items.forEach((service) => {
      const card = document.createElement("article");
      card.className = "service";
      const desc = service.description || "برای مشاهده شرایط و ثبت درخواست انتخاب کنید.";
      card.innerHTML = `<div class="symbol">${icons[service.code] || "📄"}</div><h3></h3><p></p><button type="button">ثبت درخواست</button>`;
      card.querySelector("h3").textContent = service.name;
      card.querySelector("p").textContent = desc;
      card.querySelector("button").addEventListener("click", () => openForm(service));
      $("services").appendChild(card);
    });
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
    root.innerHTML = `<section class="sheet"><h2>${escapeHtml(service.name)}</h2><div class="muted">مبلغ پایه: ${money(service.price_toman)}</div><div id="rule" class="notice">پیش از ثبت، مدارک و اطلاعات را دقیق و مطابق مدرک وارد کنید. ثبت درخواست به معنی تضمین نتیجه نهایی نیست.</div><form id="orderForm">${serviceFields.map(([name,label,type,opts]) => {
      if (type === "select") return `<label class="field"><span>${label}</span><select name="${name}" required>${opts.split("|").map(v=>`<option value="${v}">${v}</option>`).join("")}</select></label>`;
      if (type === "textarea") return `<label class="field"><span>${label}</span><textarea name="${name}" rows="3"></textarea></label>`;
      return `<label class="field"><span>${label}</span><input name="${name}" type="${type}" ${name==="student_count"?"min='1'":""} required></label>`;
    }).join("")}<div class="actions"><button class="primary" type="submit">ثبت و ادامه</button><button class="secondary" type="button" id="closeSheet">بازگشت</button></div></form><div id="formError" class="notice error hidden"></div></section>`;
    $("closeSheet").onclick = closeSheet;
    $("orderForm").onsubmit = submitOrder;
    root.addEventListener("click", (e) => { if (e.target === root) closeSheet(); }, { once: true });
  }
  function closeSheet() { $("sheetRoot").className = "hidden"; $("sheetRoot").innerHTML = ""; }
  async function submitOrder(event) {
    event.preventDefault();
    const formData = Object.fromEntries(new FormData(event.currentTarget).entries());
    const button = event.currentTarget.querySelector("button[type=submit]");
    button.disabled = true; button.textContent = "در حال ثبت…";
    try {
      const result = await api("/api/miniapp/orders", { method:"POST", body:JSON.stringify({ service_code:state.selected.code, form_data:formData }) });
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
    $("cardPay").onclick = () => {
      $("paymentResult").innerHTML = '<div class="notice">برای کارت‌به‌کارت، اطلاعات کارت را از ربات دریافت کنید و رسید را در همان گفت‌وگو ارسال کنید. پرونده پس از تأیید رسید وارد صف بررسی می‌شود.</div>';
      tg?.close?.();
    };
  }
  async function boot() {
    try {
      const data = await api("/api/miniapp/bootstrap");
      state.data = data;
      $("balance").textContent = money(data.wallet.balance_toman);
      renderServices(data.services || []);
      renderOrders(data.orders || []);
      $("walletButton").onclick = () => {
        $("orders").insertAdjacentHTML("afterbegin", '<div class="notice">برای افزایش اعتبار، از گزینه «اعتبار من» در ربات استفاده کنید.</div>');
      };
    } catch (error) {
      $("services").innerHTML = `<div class="empty">${escapeHtml(error.message)}<br>این صفحه باید از داخل ربات تلگرام باز شود.</div>`;
      $("orders").innerHTML = "";
    }
  }
  boot();
})();
