// src/generated/miniapp.ts
var MINIAPP_HTML = '<!doctype html>\n<html lang="fa" dir="rtl">\n<head>\n  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n  <meta name="theme-color" content="#123d7a">\n  <title>\u06A9\u0645\u06A9\u200C\u06CC\u0627\u0631 \u0645\u0647\u0627\u062C\u0631</title>\n  <script src="https://telegram.org/js/telegram-web-app.js"><\/script>\n  <link rel="preconnect" href="https://fonts.googleapis.com">\n  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n  <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap" rel="stylesheet">\n  <style>\n    :root{font-family:Vazirmatn,system-ui,sans-serif;color:#15243b;background:#f3f6fb;font-synthesis:none}\n    *{box-sizing:border-box}body{margin:0;min-height:100vh;background:linear-gradient(160deg,#eaf1fc 0%,#f7f9fc 42%,#eef3fa 100%)}\n    .shell{max-width:760px;margin:auto;padding:18px 16px 48px}\n    .hero{position:relative;overflow:hidden;padding:24px;border-radius:26px;color:white;background:linear-gradient(125deg,#123d7a,#2369b5 58%,#52a4dc);box-shadow:0 18px 45px #163e7826}\n    .hero:after{content:"";position:absolute;width:210px;height:210px;border:1px solid #ffffff35;border-radius:50%;left:-70px;top:-100px;box-shadow:0 0 0 24px #ffffff0b,0 0 0 50px #ffffff0b}\n    .eyebrow{font-size:12px;opacity:.82}.hero h1{margin:8px 0 6px;font-size:25px;font-weight:800}.hero p{margin:0;max-width:440px;font-size:13px;line-height:2;opacity:.9}\n    .brand-row{display:flex;align-items:center;gap:12px}.brand-mark{width:54px;height:54px;flex:0 0 54px;display:grid;place-items:center;border:1px solid #ffffff45;border-radius:17px;background:#ffffff1c;box-shadow:inset 0 1px 0 #ffffff30}.brand-mark svg{width:38px;height:38px}\n    .hero-tools{display:flex;justify-content:flex-end;margin-bottom:12px}.theme-toggle{border:1px solid #ffffff55;border-radius:999px;padding:8px 12px;color:#fff;background:#ffffff16;font:inherit;font-size:11px;font-weight:700;cursor:pointer}\n    .fee-note{font-size:11px;opacity:.82;margin-top:4px}\n    .wallet{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:22px;padding:14px 16px;border:1px solid #ffffff38;border-radius:17px;background:#ffffff16;backdrop-filter:blur(8px)}\n    .wallet small{display:block;opacity:.8}.wallet strong{font-size:19px}\n    .section-head{display:flex;align-items:center;justify-content:space-between;margin:25px 2px 12px}.section-head h2{font-size:17px;margin:0}.muted{color:#6d7b90;font-size:12px}\n    .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}\n    .service{padding:16px;border:1px solid #e3eaf3;border-radius:20px;background:#fff;box-shadow:0 8px 22px #1c46700a;min-height:150px;display:flex;flex-direction:column;gap:9px}\n    .service .symbol{width:38px;height:38px;border-radius:13px;background:#eaf2ff;color:#20579a;display:grid;place-items:center;font-size:19px}\n    .service h3{font-size:14px;margin:0}.service p{font-size:11px;line-height:1.8;color:#758197;margin:0;flex:1}\n    .service button,.primary,.secondary{border:0;border-radius:13px;padding:11px 13px;font:inherit;font-size:12px;font-weight:700;cursor:pointer}\n    .service button,.primary{background:#1d5da4;color:#fff}.secondary{background:#edf3fb;color:#1e5189}\n    .panel{margin-top:16px;padding:17px;border:1px solid #e3eaf3;border-radius:20px;background:white}\n    .panel h3{margin:0 0 12px;font-size:15px}.empty{padding:18px;text-align:center;color:#7b8798;font-size:12px}\n    .order{display:flex;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid #eef1f6;font-size:12px}.order:last-child{border:0}\n    .status{color:#1d67a6;font-weight:700}.hidden{display:none!important}\n    .backdrop{position:fixed;inset:0;background:#0c1c33a6;display:grid;place-items:end center;padding:12px;z-index:5}\n    .sheet{width:min(100%,650px);max-height:88vh;overflow:auto;border-radius:24px 24px 18px 18px;background:#fff;padding:22px}\n    .sheet h2{font-size:18px;margin:0 0 6px}.field{display:block;margin:13px 0}.field span{display:block;font-size:12px;font-weight:700;margin-bottom:6px}\n    input,textarea,select{width:100%;border:1px solid #dbe4f0;border-radius:12px;padding:12px;background:#fbfcfe;font:inherit;font-size:13px;outline:none}\n    input:focus,textarea:focus,select:focus{border-color:#347ec1;box-shadow:0 0 0 3px #347ec11a}\n    .actions{display:flex;gap:9px;margin-top:18px}.actions>*{flex:1}\n    .notice{padding:12px;border-radius:13px;background:#f0f6ff;color:#255586;font-size:12px;line-height:1.9;margin:12px 0}\n    .error{background:#fff1f0;color:#9c3029}.success{background:#ecf9f1;color:#21623c}\n    @media(max-width:420px){.grid{grid-template-columns:1fr}.hero h1{font-size:22px}}\n    body[data-theme="dark"]{color:#e8eef8;background:#0b1220}\n    body[data-theme="dark"] .shell{color:#e8eef8}\n    body[data-theme="dark"] .service,body[data-theme="dark"] .panel,body[data-theme="dark"] .sheet{background:#151f30;border-color:#2a3a52;color:#e8eef8;box-shadow:0 12px 28px #0005}\n    body[data-theme="dark"] .service .symbol{background:#203b5b;color:#b8dcff}\n    body[data-theme="dark"] .service p,body[data-theme="dark"] .muted{color:#a6b4c8}\n    body[data-theme="dark"] .order{border-color:#2b394d}\n    body[data-theme="dark"] .status{color:#8bc4ff}\n    body[data-theme="dark"] input,body[data-theme="dark"] textarea,body[data-theme="dark"] select{background:#0e1726;border-color:#34445c;color:#f1f5fb}\n    body[data-theme="dark"] .secondary{background:#263a54;color:#d9eaff}\n    body[data-theme="dark"] .notice{background:#1b3550;color:#d1e8ff}\n    body[data-theme="dark"] .notice.error{background:#4a252b;color:#ffd6d6}\n    body[data-theme="dark"] .notice.success{background:#183c30;color:#c7f4da}\n    body[data-theme="dark"] .backdrop{background:#020611d9}\n    body[data-theme="dark"] .empty{color:#a6b4c8}\n    @media(prefers-reduced-motion:no-preference){.service,.panel,.primary,.secondary{transition:background .2s,border-color .2s,transform .2s}.service:active{transform:scale(.99)}}\n  </style>\n</head>\n<body>\n  <main class="shell">\n    <section class="hero">\n      <div class="hero-tools"><button type="button" class="theme-toggle" id="themeButton" aria-label="\u062A\u063A\u06CC\u06CC\u0631 \u062D\u0627\u0644\u062A \u0646\u0645\u0627\u06CC\u0634">\u{1F319} \u062D\u0627\u0644\u062A \u0634\u0628</button></div>\n      <div class="brand-row">\n        <div class="brand-mark" aria-label="\u0646\u0634\u0627\u0646 \u0631\u0628\u0627\u062A \u06A9\u0645\u06A9\u200C\u06CC\u0627\u0631 \u0645\u0647\u0627\u062C\u0631">\n          <svg viewBox="0 0 48 48" role="img" aria-hidden="true"><path d="M24 5v5" stroke="white" stroke-width="2.8" stroke-linecap="round"/><circle cx="24" cy="4" r="2.5" fill="#ffd76a"/><rect x="8" y="12" width="32" height="27" rx="9" fill="#f7fbff" stroke="#d5e8ff" stroke-width="1.5"/><rect x="13" y="18" width="22" height="13" rx="5" fill="#1c5795"/><circle cx="19" cy="24.5" r="2" fill="#8de4ff"/><circle cx="29" cy="24.5" r="2" fill="#8de4ff"/><path d="M19 34h10" stroke="#1c5795" stroke-width="2.4" stroke-linecap="round"/><path d="M8 21H5m38 0h-3" stroke="white" stroke-width="2.5" stroke-linecap="round"/></svg>\n        </div>\n        <div><div class="eyebrow">\u062F\u0641\u062A\u0631 \u0646\u062A\u200C\u06CC\u0627\u0631 \u0645\u0647\u0627\u062C\u0631</div><h1>\u06A9\u0645\u06A9\u200C\u06CC\u0627\u0631 \u0645\u0647\u0627\u062C\u0631</h1></div>\n      </div>\n      <p>\u062B\u0628\u062A \u062E\u062F\u0645\u0627\u062A\u060C \u067E\u06CC\u06AF\u06CC\u0631\u06CC \u067E\u0631\u0648\u0646\u062F\u0647\u200C\u0647\u0627 \u0648 \u0645\u062F\u06CC\u0631\u06CC\u062A \u0627\u0639\u062A\u0628\u0627\u0631\u061B \u0633\u0627\u062F\u0647\u060C \u0627\u0645\u0646 \u0648 \u0647\u0645\u06CC\u0634\u0647 \u062F\u0631 \u062F\u0633\u062A\u0631\u0633.</p>\n      <div id="feeNote" class="fee-note">\u067E\u0631\u062F\u0627\u062E\u062A \u0627\u0645\u0646 \u0628\u0627 \u0631\u06CC\u0627\u0644\u062A \u0648 \u06A9\u0627\u0631\u062A\u200C\u0628\u0647\u200C\u06A9\u0627\u0631\u062A</div>\n      <div class="wallet">\n        <div><small>\u0627\u0639\u062A\u0628\u0627\u0631 \u062D\u0633\u0627\u0628 \u0634\u0645\u0627</small><strong id="balance">\u2014 \u062A\u0648\u0645\u0627\u0646</strong></div>\n        <button class="secondary" id="walletButton">\u0627\u0641\u0632\u0627\u06CC\u0634 \u0627\u0639\u062A\u0628\u0627\u0631</button>\n      </div>\n    </section>\n    <div class="section-head"><h2>\u062E\u062F\u0645\u0627\u062A \u062F\u0641\u062A\u0631</h2><span class="muted">\u0627\u0646\u062A\u062E\u0627\u0628 \u062E\u062F\u0645\u062A \u0648 \u062B\u0628\u062A \u062F\u0631\u062E\u0648\u0627\u0633\u062A</span></div>\n    <section id="services" class="grid"><div class="empty">\u062F\u0631 \u062D\u0627\u0644 \u062F\u0631\u06CC\u0627\u0641\u062A \u062E\u062F\u0645\u0627\u062A\u2026</div></section>\n    <section class="panel">\n      <div class="section-head" style="margin:0 0 8px"><h3>\u067E\u0631\u0648\u0646\u062F\u0647\u200C\u0647\u0627\u06CC \u0627\u062E\u06CC\u0631</h3><span class="muted">\u0622\u062E\u0631\u06CC\u0646 \u062F\u0631\u062E\u0648\u0627\u0633\u062A\u200C\u0647\u0627</span></div>\n      <div id="orders" class="empty">\u062F\u0631 \u062D\u0627\u0644 \u062F\u0631\u06CC\u0627\u0641\u062A \u067E\u0631\u0648\u0646\u062F\u0647\u200C\u0647\u0627\u2026</div>\n    </section>\n    <div class="muted" style="text-align:center;margin:24px 0 0">\u067E\u0634\u062A\u06CC\u0628\u0627\u0646\u06CC: @NetYar_esf</div>\n  </main>\n  <div id="sheetRoot" class="hidden"></div>\n  <script src="/app.js"><\/script>\n</body>\n</html>\n';
var MINIAPP_JS = `(() => {
  const tg = window.Telegram?.WebApp;
  tg?.ready();
  tg?.expand();
  const $ = (id) => document.getElementById(id);
  let state = { data: null, selected: null };
  const money = (n) => new Intl.NumberFormat("fa-IR").format(Number(n || 0)) + " \u062A\u0648\u0645\u0627\u0646";
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
        unauthorized:"\u0628\u0631\u0627\u06CC \u0627\u0645\u0646\u06CC\u062A\u060C \u0645\u06CC\u0646\u06CC\u200C\u0627\u067E \u0631\u0627 \u0627\u0632 \u062F\u0627\u062E\u0644 \u0631\u0628\u0627\u062A \u062A\u0644\u06AF\u0631\u0627\u0645 \u0628\u0627\u0632 \u06A9\u0646\u06CC\u062F.",
        rialit_not_configured:"\u06A9\u0644\u06CC\u062F \u062F\u0631\u06AF\u0627\u0647 \u0631\u06CC\u0627\u0644\u062A \u062F\u0631 Worker \u062B\u0628\u062A \u0646\u0634\u062F\u0647 \u0627\u0633\u062A.",
        rialit_key_invalid:"\u06A9\u0644\u06CC\u062F \u067E\u0630\u06CC\u0631\u0646\u062F\u0647 \u0631\u06CC\u0627\u0644\u062A \u0645\u0639\u062A\u0628\u0631 \u0646\u06CC\u0633\u062A.",
        rialit_outbound_ip_not_allowed:"IP \u062E\u0631\u0648\u062C\u06CC Worker \u062F\u0631 \u0641\u0647\u0631\u0633\u062A IP\u0647\u0627\u06CC \u0645\u062C\u0627\u0632 \u067E\u0630\u06CC\u0631\u0646\u062F\u0647 \u0631\u06CC\u0627\u0644\u062A \u0646\u06CC\u0633\u062A.",
        rialit_merchant_inactive:"\u062D\u0633\u0627\u0628 \u067E\u0630\u06CC\u0631\u0646\u062F\u0647 \u0631\u06CC\u0627\u0644\u062A \u0641\u0639\u0627\u0644 \u0646\u06CC\u0633\u062A.",
        rialit_fee_mismatch:"\u06A9\u0627\u0631\u0645\u0632\u062F \u062F\u0631\u06AF\u0627\u0647 \u0628\u0627 \u06F1\u06F2\u066A \u062A\u0646\u0638\u06CC\u0645\u200C\u0634\u062F\u0647 \u0645\u0637\u0627\u0628\u0642\u062A \u0646\u062F\u0627\u0631\u062F\u061B \u067E\u0631\u062F\u0627\u062E\u062A \u0645\u062A\u0648\u0642\u0641 \u0634\u062F. \u062A\u0646\u0638\u06CC\u0645\u0627\u062A \u067E\u0630\u06CC\u0631\u0646\u062F\u0647 \u0631\u06CC\u0627\u0644\u062A \u0628\u0627\u06CC\u062F \u0628\u0631\u0631\u0633\u06CC \u0634\u0648\u062F.",
        rialit_network_error:"\u0627\u0631\u062A\u0628\u0627\u0637 Worker \u0628\u0627 \u0631\u06CC\u0627\u0644\u062A \u0628\u0631\u0642\u0631\u0627\u0631 \u0646\u0634\u062F. \u0633\u0641\u0627\u0631\u0634 \u062B\u0628\u062A \u0634\u062F\u0647 \u0648 \u0645\u06CC\u200C\u062A\u0648\u0627\u0646\u06CC\u062F \u062F\u0648\u0628\u0627\u0631\u0647 \u062A\u0644\u0627\u0634 \u06A9\u0646\u06CC\u062F.",
        rialit_retry_later:"\u062F\u0631\u06AF\u0627\u0647 \u0645\u0648\u0642\u062A\u0627\u064B \u067E\u0627\u0633\u062E \u0646\u0645\u06CC\u200C\u062F\u0647\u062F\u061B \u0686\u0646\u062F \u062F\u0642\u06CC\u0642\u0647 \u0628\u0639\u062F \u062F\u0648\u0628\u0627\u0631\u0647 \u062A\u0644\u0627\u0634 \u06A9\u0646\u06CC\u062F.",
        rialit_amount_out_of_range:"\u0645\u0628\u0644\u063A \u062E\u0627\u0631\u062C \u0627\u0632 \u0645\u062D\u062F\u0648\u062F\u0647 \u0645\u062C\u0627\u0632 \u0631\u06CC\u0627\u0644\u062A \u0627\u0633\u062A\u061B \u0627\u0632 \u06A9\u0627\u0631\u062A\u200C\u0628\u0647\u200C\u06A9\u0627\u0631\u062A \u0627\u0633\u062A\u0641\u0627\u062F\u0647 \u06A9\u0646\u06CC\u062F.",
        card_not_configured:"\u0634\u0645\u0627\u0631\u0647 \u06A9\u0627\u0631\u062A \u062F\u0641\u062A\u0631 \u0647\u0646\u0648\u0632 \u062F\u0631 \u062A\u0646\u0638\u06CC\u0645\u0627\u062A \u0645\u062F\u06CC\u0631\u06CC\u062A \u062B\u0628\u062A \u0646\u0634\u062F\u0647 \u0627\u0633\u062A.",
        order_not_payable:"\u0627\u06CC\u0646 \u0633\u0641\u0627\u0631\u0634 \u062F\u0631 \u0648\u0636\u0639\u06CC\u062A \u0642\u0627\u0628\u0644 \u067E\u0631\u062F\u0627\u062E\u062A \u0646\u06CC\u0633\u062A.",
        service_unavailable:"\u0627\u06CC\u0646 \u062E\u062F\u0645\u062A \u0641\u0639\u0644\u0627\u064B \u0641\u0639\u0627\u0644 \u0646\u06CC\u0633\u062A.",
        vpn_payment_not_configured:"\u0627\u062A\u0635\u0627\u0644 \u067E\u0631\u062F\u0627\u062E\u062A \u06CC\u0627 API \u0641\u06CC\u0644\u062A\u0631\u0634\u06A9\u0646 \u062F\u0631 Worker \u062A\u0646\u0638\u06CC\u0645 \u0646\u0634\u062F\u0647 \u0627\u0633\u062A.",
        gozarban_not_ready:"\u0627\u062A\u0635\u0627\u0644 \u067E\u0646\u0644 \u0641\u06CC\u0644\u062A\u0631\u0634\u06A9\u0646 \u06CC\u0627 \u067E\u0644\u0646 \u0641\u0639\u0627\u0644 \u062F\u0631 \u062F\u0633\u062A\u0631\u0633 \u0646\u06CC\u0633\u062A.",
        invalid_vpn_selection:"\u062D\u062C\u0645 \u06CC\u0627 \u0645\u062F\u062A \u0627\u0646\u062A\u062E\u0627\u0628\u06CC \u0645\u0639\u062A\u0628\u0631 \u0646\u06CC\u0633\u062A.",
        vpn_payment_already_paid:"\u0627\u06CC\u0646 \u0633\u0641\u0627\u0631\u0634 VPN \u0642\u0628\u0644\u0627\u064B \u067E\u0631\u062F\u0627\u062E\u062A \u0634\u062F\u0647 \u0627\u0633\u062A."
      };
      let message = messages[data.error] || data.error || "\u062E\u0637\u0627 \u062F\u0631 \u062F\u0631\u06CC\u0627\u0641\u062A \u0627\u0637\u0644\u0627\u0639\u0627\u062A";
      if (data.detail) message += " (" + String(data.detail) + ")";
      throw new Error(message);
    }
    return data;
  };
  const icons = { identity:"\u{1FAAA}", khodnevis:"\u{1F3E0}", fida:"\u{1F9FE}", dolatman_login:"\u{1F510}", student_screening:"\u{1F393}", other_service:"\u{1F4DD}" };
  const fields = {
    identity: [
      ["full_name","\u0646\u0627\u0645 \u0648 \u0646\u0627\u0645 \u062E\u0627\u0646\u0648\u0627\u062F\u06AF\u06CC \u0645\u0637\u0627\u0628\u0642 \u0645\u062F\u0631\u06A9","text"],
      ["mobile","\u0634\u0645\u0627\u0631\u0647 \u0645\u0648\u0628\u0627\u06CC\u0644 \u062F\u0631 \u062F\u0633\u062A\u0631\u0633","tel"],
      ["birth_date","\u062A\u0627\u0631\u06CC\u062E \u062A\u0648\u0644\u062F (\u0634\u0645\u0633\u06CC)","text"],
      ["return_date","\u062A\u0627\u0631\u06CC\u062E \u0628\u0627\u0632\u06AF\u0634\u062A (\u062F\u0631 \u0635\u0648\u0631\u062A \u0648\u062C\u0648\u062F)","text"],
      ["consulate","\u06A9\u0646\u0633\u0648\u0644\u06AF\u0631\u06CC \u0645\u0648\u0631\u062F\u0646\u0638\u0631","select","\u0632\u0627\u0647\u062F\u0627\u0646|\u0645\u0634\u0647\u062F"],
      ["document_type","\u0646\u0648\u0639 \u0645\u062F\u0631\u06A9","select","\u06A9\u0627\u0631\u062A \u0622\u0645\u0627\u06CC\u0634|\u06AF\u0630\u0631\u0646\u0627\u0645\u0647|\u062F\u0641\u062A\u0631\u0686\u0647 \u0627\u0642\u0627\u0645\u062A|\u0641\u0627\u0642\u062F \u0645\u062F\u0631\u06A9|\u0633\u0627\u06CC\u0631"],
      ["document_number","\u0634\u0645\u0627\u0631\u0647 \u0634\u0646\u0627\u0633\u0647 \u0645\u062F\u0631\u06A9 \u0634\u0646\u0627\u0633\u0627\u06CC\u06CC","text"],
      ["relative_tazkira","\u062A\u0648\u0636\u06CC\u062D \u0645\u062F\u0631\u06A9 \u062A\u0630\u06A9\u0631\u0647 \u0627\u0642\u0627\u0631\u0628 \u0646\u0632\u062F\u06CC\u06A9","textarea"]
    ],
    khodnevis: [
      ["full_name","\u0646\u0627\u0645 \u0648 \u0646\u0627\u0645 \u062E\u0627\u0646\u0648\u0627\u062F\u06AF\u06CC \u0645\u0633\u062A\u0623\u062C\u0631","text"],
      ["mobile","\u0634\u0645\u0627\u0631\u0647 \u062A\u0645\u0627\u0633","tel"],
      ["property_address","\u0646\u0634\u0627\u0646\u06CC \u06A9\u0627\u0645\u0644 \u0645\u0644\u06A9","textarea"],
      ["owner_name","\u0646\u0627\u0645 \u0635\u0627\u062D\u0628\u062E\u0627\u0646\u0647","text"],
      ["property_code","\u0634\u0646\u0627\u0633\u0647 \u0645\u0644\u06A9 / \u06A9\u062F \u067E\u0633\u062A\u06CC","text"]
    ],
    fida: [
      ["full_name","\u0646\u0627\u0645 \u0648 \u0646\u0627\u0645 \u062E\u0627\u0646\u0648\u0627\u062F\u06AF\u06CC","text"],
      ["mobile","\u0634\u0645\u0627\u0631\u0647 \u0645\u0648\u0628\u0627\u06CC\u0644 \u062F\u0631 \u062F\u0633\u062A\u0631\u0633","tel"],
      ["document_number","\u0634\u0645\u0627\u0631\u0647 \u0645\u062F\u0631\u06A9 \u0634\u0646\u0627\u0633\u0627\u06CC\u06CC","text"]
    ],
    dolatman_login: [
      ["mobile","\u0634\u0645\u0627\u0631\u0647 \u0645\u0648\u0628\u0627\u06CC\u0644 \u0648\u0631\u0648\u062F \u0628\u0647 \u062F\u0648\u0644\u062A \u0645\u0646","tel"],
      ["own_name_mobile","\u0622\u06CC\u0627 \u0633\u06CC\u0645\u200C\u06A9\u0627\u0631\u062A \u0628\u0647 \u0646\u0627\u0645 \u062E\u0648\u062F\u062A\u0627\u0646 \u0627\u0633\u062A\u061F","select","\u0628\u0644\u0647|\u062E\u06CC\u0631"],
      ["notes","\u062A\u0648\u0636\u06CC\u062D\u0627\u062A","textarea"]
    ],
    student_screening: [
      ["student_count","\u062A\u0639\u062F\u0627\u062F \u062F\u0627\u0646\u0634\u200C\u0622\u0645\u0648\u0632\u0627\u0646","number"],
      ["school_name","\u0646\u0627\u0645 \u0645\u062F\u0631\u0633\u0647","text"],
      ["notes","\u062A\u0648\u0636\u06CC\u062D\u0627\u062A","textarea"]
    ],
    other_service: [
      ["description","\u0634\u0631\u062D \u062F\u0631\u062E\u0648\u0627\u0633\u062A","textarea"]
    ]
  };
  function renderServices(items) {
    $("services").innerHTML = "";
    if (!items.length) $("services").innerHTML = '<div class="empty">\u0641\u0639\u0644\u0627\u064B \u062E\u062F\u0645\u062A\u06CC \u0628\u0631\u0627\u06CC \u062B\u0628\u062A \u0641\u0639\u0627\u0644 \u0646\u06CC\u0633\u062A.</div>';
    items.forEach((service) => {
      const card = document.createElement("article");
      card.className = "service";
      const desc = service.description || "\u0628\u0631\u0627\u06CC \u0645\u0634\u0627\u0647\u062F\u0647 \u0634\u0631\u0627\u06CC\u0637 \u0648 \u062B\u0628\u062A \u062F\u0631\u062E\u0648\u0627\u0633\u062A \u0627\u0646\u062A\u062E\u0627\u0628 \u06A9\u0646\u06CC\u062F.";
      card.innerHTML = '<div class="symbol">' + (icons[service.code] || "\u{1F4C4}") + '</div><h3></h3><p></p><button type="button">\u062B\u0628\u062A \u062F\u0631\u062E\u0648\u0627\u0633\u062A</button>';
      card.querySelector("h3").textContent = service.name;
      card.querySelector("p").textContent = desc;
      card.querySelector("button").addEventListener("click", () => openForm(service));
      $("services").appendChild(card);
    });
    const vpn = document.createElement("article");
    vpn.className = "service vpn-service";
    vpn.innerHTML = '<div class="symbol">\u{1F510}</div><h3>\u062E\u0631\u06CC\u062F \u0641\u06CC\u0644\u062A\u0631\u0634\u06A9\u0646</h3><p>\u0642\u06CC\u0645\u062A \u067E\u0627\u06CC\u0647 \u0647\u0631 \u06AF\u06CC\u06AF \u06F5\u066C\u06F6\u06F0\u06F0 \u062A\u0648\u0645\u0627\u0646\u061B \u06A9\u0627\u0631\u0645\u0632\u062F \u062F\u0631\u06AF\u0627\u0647 \u0631\u06CC\u0627\u0644\u062A \u06F1\u06F2\u066A \u062C\u062F\u0627\u06AF\u0627\u0646\u0647 \u0645\u062D\u0627\u0633\u0628\u0647 \u0645\u06CC\u200C\u0634\u0648\u062F.</p><button type="button">\u0627\u0646\u062A\u062E\u0627\u0628 \u062D\u062C\u0645 \u0648 \u0645\u062F\u062A</button>';
    vpn.querySelector("button").addEventListener("click", openVpnForm);
    $("services").appendChild(vpn);
  }
  function openVpnForm() {
    const root = $("sheetRoot");
    root.className = "backdrop";
    root.innerHTML = '<section class="sheet"><h2>\u{1F510} \u062E\u0631\u06CC\u062F \u0641\u06CC\u0644\u062A\u0631\u0634\u06A9\u0646</h2><p class="muted">\u0642\u06CC\u0645\u062A \u067E\u0627\u06CC\u0647 \u0647\u0631 \u06AF\u06CC\u06AF: \u06F5\u066C\u06F6\u06F0\u06F0 \u062A\u0648\u0645\u0627\u0646. \u06A9\u0627\u0631\u0645\u0632\u062F \u0631\u06CC\u0627\u0644\u062A: \u06F1\u06F2\u066A \u0627\u0632 \u0645\u0628\u0644\u063A \u067E\u0627\u06CC\u0647.</p><label class="field"><span>\u0645\u062F\u062A \u0627\u0634\u062A\u0631\u0627\u06A9</span><select id="vpnMonths"><option value="1">\u06F1 \u0645\u0627\u0647</option><option value="2">\u06F2 \u0645\u0627\u0647</option><option value="3">\u06F3 \u0645\u0627\u0647</option><option value="4">\u06F4 \u0645\u0627\u0647</option></select></label><label class="field"><span>\u062D\u062C\u0645 \u0627\u0634\u062A\u0631\u0627\u06A9</span><select id="vpnGb"></select></label><div id="vpnPrice" class="notice"></div><div class="actions"><button class="secondary" id="vpnCheck">\u0628\u0631\u0631\u0633\u06CC \u0627\u062A\u0635\u0627\u0644 API \u0641\u06CC\u0644\u062A\u0631\u0634\u06A9\u0646</button><button class="primary" id="vpnPay">\u0627\u062F\u0627\u0645\u0647 \u0648 \u062F\u0631\u06CC\u0627\u0641\u062A \u0644\u06CC\u0646\u06A9 \u067E\u0631\u062F\u0627\u062E\u062A</button><button class="secondary" id="vpnClose">\u0628\u0627\u0632\u06AF\u0634\u062A</button></div><div id="vpnResult"></div></section>';
    const gb = $("vpnGb");
    for (let n=10;n<=100;n+=10) { const option=document.createElement("option"); option.value=String(n); option.textContent=new Intl.NumberFormat("fa-IR").format(n)+" \u06AF\u06CC\u06AF\u0627\u0628\u0627\u06CC\u062A"; gb.appendChild(option); }
    const updatePrice = () => {
      const base = Number(gb.value || 10) * 5600;
      const fee = Math.round(base * 0.12);
      $("vpnPrice").textContent = "\u0645\u0628\u0644\u063A \u067E\u0627\u06CC\u0647: " + money(base) + " | \u06A9\u0627\u0631\u0645\u0632\u062F \u06F1\u06F2\u066A: " + money(fee) + " | \u0645\u0628\u0644\u063A \u062A\u0642\u0631\u06CC\u0628\u06CC \u067E\u0631\u062F\u0627\u062E\u062A: " + money(base+fee);
    };
    gb.addEventListener("change",updatePrice);
    $("vpnMonths").addEventListener("change",updatePrice);
    updatePrice();
    $("vpnClose").onclick = closeSheet;
    $("vpnCheck").onclick = async () => {
      const b=$("vpnCheck"); b.disabled=true; b.textContent="\u062F\u0631 \u062D\u0627\u0644 \u0628\u0631\u0631\u0633\u06CC \u0627\u062A\u0635\u0627\u0644 \u06AF\u0630\u0631\u0628\u0627\u0646\u2026";
      try {
        const result=await api("/api/miniapp/vpn/status");
        $("vpnResult").innerHTML='<div class="notice success">\u2705 \u0627\u062A\u0635\u0627\u0644 API \u06AF\u0630\u0631\u0628\u0627\u0646 \u0628\u0631\u0642\u0631\u0627\u0631 \u0627\u0633\u062A.<br>\u067E\u0644\u0646 \u0641\u0639\u0627\u0644: <strong>'+escapeHtml(result.plan_name)+'</strong><br>\u0642\u06CC\u0645\u062A \u067E\u0627\u06CC\u0647 \u0647\u0631 \u06AF\u06CC\u06AF: '+money(result.base_price_per_gb_toman)+' \u062A\u0648\u0645\u0627\u0646<br>\u06A9\u0627\u0631\u0645\u0632\u062F \u067E\u0631\u062F\u0627\u062E\u062A \u0631\u06CC\u0627\u0644\u062A: '+result.fee_percent+'\u066A</div>';
      } catch(error) {
        $("vpnResult").innerHTML='<div class="notice error">'+escapeHtml(error.message)+'</div>';
      } finally { b.disabled=false; b.textContent="\u0628\u0631\u0631\u0633\u06CC \u0627\u062A\u0635\u0627\u0644 API \u0641\u06CC\u0644\u062A\u0631\u0634\u06A9\u0646"; }
    };
    $("vpnPay").onclick = async () => {
      const b=$("vpnPay"); b.disabled=true; b.textContent="\u062F\u0631 \u062D\u0627\u0644 \u0628\u0631\u0631\u0633\u06CC \u0627\u062A\u0635\u0627\u0644 \u0648 \u0633\u0627\u062E\u062A \u0644\u06CC\u0646\u06A9\u2026";
      try {
        const result=await api("/api/miniapp/vpn/pay",{method:"POST",body:JSON.stringify({months:Number($("vpnMonths").value),gigabytes:Number(gb.value),request_id:crypto.randomUUID()})});
        $("vpnResult").innerHTML='<div class="notice success">\u0645\u0628\u0644\u063A \u067E\u0627\u06CC\u0647: '+money(result.amount_toman)+'<br>\u06A9\u0627\u0631\u0645\u0632\u062F \u0631\u06CC\u0627\u0644\u062A: '+money(result.payer_fee_toman)+'<br>\u0645\u0628\u0644\u063A \u0646\u0647\u0627\u06CC\u06CC \u062F\u0631\u06AF\u0627\u0647: <strong>'+money(result.payer_amount_toman)+'</strong></div><button class="primary" id="vpnOpenPay">\u0648\u0631\u0648\u062F \u0628\u0647 \u062F\u0631\u06AF\u0627\u0647 \u0627\u0645\u0646</button>';
        $("vpnOpenPay").onclick=()=>tg?.openLink?tg.openLink(result.pay_url):window.open(result.pay_url,"_blank");
      } catch(error) {
        $("vpnResult").innerHTML='<div class="notice error">'+escapeHtml(error.message)+'</div>';
      } finally { b.disabled=false; b.textContent="\u0627\u062F\u0627\u0645\u0647 \u0648 \u062F\u0631\u06CC\u0627\u0641\u062A \u0644\u06CC\u0646\u06A9 \u067E\u0631\u062F\u0627\u062E\u062A"; }
    };
  }
  function renderOrders(items) {
    if (!items.length) { $("orders").innerHTML = '<div class="empty">\u0647\u0646\u0648\u0632 \u067E\u0631\u0648\u0646\u062F\u0647\u200C\u0627\u06CC \u062B\u0628\u062A \u0646\u06A9\u0631\u062F\u0647\u200C\u0627\u06CC\u062F.</div>'; return; }
    $("orders").innerHTML = items.map((o) => \`<div class="order"><div><strong>\${escapeHtml(o.service_name)}</strong><div class="muted">\${escapeHtml(o.public_id || "")}</div></div><div style="text-align:left"><div class="status">\${escapeHtml(statusLabel(o.status))}</div><div class="muted">\${money(o.price_snapshot_toman)}</div></div></div>\`).join("");
  }
  function statusLabel(s) {
    return ({draft:"\u067E\u06CC\u0634\u200C\u0646\u0648\u06CC\u0633",waiting_payment:"\u062F\u0631 \u0627\u0646\u062A\u0638\u0627\u0631 \u067E\u0631\u062F\u0627\u062E\u062A",waiting_receipt_review:"\u062F\u0631 \u0627\u0646\u062A\u0638\u0627\u0631 \u0628\u0631\u0631\u0633\u06CC \u0631\u0633\u06CC\u062F",payment_approved:"\u067E\u0631\u062F\u0627\u062E\u062A \u062A\u0623\u06CC\u06CC\u062F \u0634\u062F",in_progress:"\u062F\u0631 \u062D\u0627\u0644 \u0627\u0646\u062C\u0627\u0645",waiting_user:"\u0645\u0646\u062A\u0638\u0631 \u0627\u0637\u0644\u0627\u0639\u0627\u062A \u0645\u0634\u062A\u0631\u06A9",completed:"\u062A\u06A9\u0645\u06CC\u0644 \u0634\u062F",rejected:"\u0631\u062F \u0634\u062F\u0647"})[s] || "\u062F\u0631 \u062D\u0627\u0644 \u067E\u06CC\u06AF\u06CC\u0631\u06CC";
  }
  function escapeHtml(v) { return String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
  function openForm(service) {
    state.selected = service;
    const root = $("sheetRoot");
    root.className = "backdrop";
    const serviceFields = fields[service.code] || fields.other_service;
    const rulesText = service.rules_text || "\u067E\u06CC\u0634 \u0627\u0632 \u062B\u0628\u062A\u060C \u0645\u062F\u0627\u0631\u06A9 \u0648 \u0627\u0637\u0644\u0627\u0639\u0627\u062A \u0631\u0627 \u062F\u0642\u06CC\u0642 \u0648 \u0645\u0637\u0627\u0628\u0642 \u0645\u062F\u0631\u06A9 \u0648\u0627\u0631\u062F \u06A9\u0646\u06CC\u062F. \u062B\u0628\u062A \u062F\u0631\u062E\u0648\u0627\u0633\u062A \u0628\u0647 \u0645\u0639\u0646\u06CC \u062A\u0636\u0645\u06CC\u0646 \u0646\u062A\u06CC\u062C\u0647 \u0646\u0647\u0627\u06CC\u06CC \u0646\u06CC\u0633\u062A.";
    root.innerHTML = \`<section class="sheet"><h2>\${escapeHtml(service.name)}</h2><div class="muted">\u0645\u0628\u0644\u063A \u067E\u0627\u06CC\u0647: \${money(service.price_toman)}</div><div id="rule" class="notice">\${escapeHtml(rulesText)}</div><form id="orderForm">\${serviceFields.map(([name,label,type,opts]) => {
      if (type === "select") return \`<label class="field"><span>\${label}</span><select name="\${name}" required>\${opts.split("|").map(v=>\`<option value="\${v}">\${v}</option>\`).join("")}</select></label>\`;
      if (type === "textarea") return \`<label class="field"><span>\${label}</span><textarea name="\${name}" rows="3"></textarea></label>\`;
      return \`<label class="field"><span>\${label}</span><input name="\${name}" type="\${type}" \${name==="student_count"?"min='1'":""} required></label>\`;
    }).join("")}<label class="field"><span><input name="rules_accepted" type="checkbox" required style="width:auto;margin-left:8px"> \u0642\u0648\u0627\u0646\u06CC\u0646 \u0627\u06CC\u0646 \u062E\u062F\u0645\u062A \u0631\u0627 \u062E\u0648\u0627\u0646\u062F\u0645 \u0648 \u0645\u06CC\u200C\u067E\u0630\u06CC\u0631\u0645.</span></label><div class="actions"><button class="primary" type="submit">\u062B\u0628\u062A \u0648 \u0627\u062F\u0627\u0645\u0647</button><button class="secondary" type="button" id="closeSheet">\u0628\u0627\u0632\u06AF\u0634\u062A</button></div></form><div id="formError" class="notice error hidden"></div></section>\`;
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
      $("formError").textContent = "\u0628\u0631\u0627\u06CC \u0627\u062F\u0627\u0645\u0647 \u0628\u0627\u06CC\u062F \u0642\u0648\u0627\u0646\u06CC\u0646 \u062E\u062F\u0645\u062A \u0631\u0627 \u0628\u067E\u0630\u06CC\u0631\u06CC\u062F.";
      $("formError").classList.remove("hidden");
      return;
    }
    const button = event.currentTarget.querySelector("button[type=submit]");
    button.disabled = true; button.textContent = "\u062F\u0631 \u062D\u0627\u0644 \u062B\u0628\u062A\u2026";
    try {
      const result = await api("/api/miniapp/orders", { method:"POST", body:JSON.stringify({ service_code:state.selected.code, form_data:formData, rules_accepted:true }) });
      await showPayment(result);
    } catch (error) {
      $("formError").textContent = error.message;
      $("formError").classList.remove("hidden");
      button.disabled = false; button.textContent = "\u062B\u0628\u062A \u0648 \u0627\u062F\u0627\u0645\u0647";
    }
  }
  async function showPayment(order) {
    const root = $("sheetRoot");
    const amount = Number(order.amount_toman || 0);
    root.innerHTML = \`<section class="sheet"><h2>\u062F\u0631\u062E\u0648\u0627\u0633\u062A \${escapeHtml(order.public_id)} \u062B\u0628\u062A \u0634\u062F</h2><div class="notice success">\u0627\u0637\u0644\u0627\u0639\u0627\u062A \u0634\u0645\u0627 \u062B\u0628\u062A \u0634\u062F. \u0631\u0648\u0634 \u067E\u0631\u062F\u0627\u062E\u062A \u0631\u0627 \u0627\u0646\u062A\u062E\u0627\u0628 \u06A9\u0646\u06CC\u062F.</div><div class="panel"><div class="muted">\u0645\u0628\u0644\u063A \u067E\u0627\u06CC\u0647 \u062E\u062F\u0645\u062A</div><strong>\${money(amount)}</strong><p class="muted">\u062F\u0631\u06AF\u0627\u0647 \u067E\u0631\u062F\u0627\u062E\u062A \u0631\u0645\u0632 \u067E\u0648\u06CC\u0627: \u06A9\u0627\u0631\u0645\u0632\u062F \u06F1\u06F2\u066A \u0627\u0632 \u062A\u0646\u0638\u06CC\u0645\u0627\u062A \u067E\u0630\u06CC\u0631\u0646\u062F\u0647 \u0631\u06CC\u0627\u0644\u062A \u0645\u062D\u0627\u0633\u0628\u0647 \u0645\u06CC\u200C\u0634\u0648\u062F \u0648 \u0645\u0628\u0644\u063A \u062F\u0642\u06CC\u0642 \u067E\u06CC\u0634 \u0627\u0632 \u067E\u0631\u062F\u0627\u062E\u062A \u0646\u0645\u0627\u06CC\u0634 \u062F\u0627\u062F\u0647 \u062E\u0648\u0627\u0647\u062F \u0634\u062F.</p></div><div class="actions"><button class="primary" id="rialitPay">\u{1F510} \u062F\u0631\u06AF\u0627\u0647 \u067E\u0631\u062F\u0627\u062E\u062A \u0631\u0645\u0632 \u067E\u0648\u06CC\u0627</button><button class="secondary" id="cardPay">\u{1F4B3} \u06A9\u0627\u0631\u062A \u0628\u0647 \u06A9\u0627\u0631\u062A</button></div><div id="paymentResult"></div><div class="actions"><button class="secondary" id="closePayment">\u0628\u0633\u062A\u0646</button></div></section>\`;
    $("closePayment").onclick = closeSheet;
    $("rialitPay").onclick = async () => {
      const b = $("rialitPay"); b.disabled = true; b.textContent = "\u062F\u0631 \u062D\u0627\u0644 \u0627\u062A\u0635\u0627\u0644 \u0628\u0647 \u062F\u0631\u06AF\u0627\u0647\u2026";
      try {
        const result = await api("/api/miniapp/payments/rialit", { method:"POST", body:JSON.stringify({order_id:order.order_id}) });
        $("paymentResult").innerHTML = \`<div class="notice success">\u0645\u0628\u0644\u063A \u067E\u0631\u062F\u0627\u062E\u062A\u06CC \u062F\u0631 \u062F\u0631\u06AF\u0627\u0647: <strong>\${money(result.payer_amount_toman)}</strong><br>\u06A9\u0627\u0631\u0645\u0632\u062F \u0631\u06CC\u0627\u0644\u062A: \${money(result.payer_fee_toman)}<br>\u0645\u0628\u0644\u063A \u067E\u0627\u06CC\u0647 \u067E\u0631\u0648\u0646\u062F\u0647: \${money(result.amount_toman)}</div><button class="primary" id="openRialit">\u0648\u0631\u0648\u062F \u0628\u0647 \u062F\u0631\u06AF\u0627\u0647 \u0627\u0645\u0646</button>\`;
        $("openRialit").onclick = () => tg?.openLink ? tg.openLink(result.pay_url) : window.open(result.pay_url, "_blank");
      } catch (error) {
        $("paymentResult").innerHTML = \`<div class="notice error">\${escapeHtml(error.message)}</div>\`;
      } finally { b.disabled = false; b.textContent = "\u{1F510} \u062F\u0631\u06AF\u0627\u0647 \u067E\u0631\u062F\u0627\u062E\u062A \u0631\u0645\u0632 \u067E\u0648\u06CC\u0627"; }
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
          $("paymentResult").innerHTML = '<div class="notice">\u0645\u0628\u0644\u063A \u06A9\u0627\u0631\u062A\u200C\u0628\u0647\u200C\u06A9\u0627\u0631\u062A: <strong>' + money(amount) + '</strong><br>\u0634\u0645\u0627\u0631\u0647 \u06A9\u0627\u0631\u062A: <strong>' + escapeHtml(number) + '</strong><br>\u0628\u0647 \u0646\u0627\u0645: <strong>' + escapeHtml(holder || "\u2014") + '</strong><br>\u0628\u0627\u0646\u06A9: ' + escapeHtml(bank || "\u2014") + '<br>\u067E\u0633 \u0627\u0632 \u0648\u0627\u0631\u06CC\u0632\u060C \u062A\u0635\u0648\u06CC\u0631 \u0631\u0633\u06CC\u062F \u0631\u0627 \u062F\u0631 \u06AF\u0641\u062A\u06AF\u0648\u06CC \u0631\u0628\u0627\u062A \u0627\u0631\u0633\u0627\u0644 \u06A9\u0646\u06CC\u062F.</div><button class="secondary" id="copyCard">\u06A9\u067E\u06CC \u0634\u0645\u0627\u0631\u0647 \u06A9\u0627\u0631\u062A</button>';
          $("copyCard").onclick = async () => { try { await navigator.clipboard.writeText(number); $("copyCard").textContent = "\u06A9\u067E\u06CC \u0634\u062F"; } catch { $("copyCard").textContent = number; } };
        } else {
          $("paymentResult").innerHTML = '<div class="notice error">\u0627\u0637\u0644\u0627\u0639\u0627\u062A \u06A9\u0627\u0631\u062A \u062F\u0641\u062A\u0631 \u0647\u0646\u0648\u0632 \u062F\u0631 \u062A\u0646\u0638\u06CC\u0645\u0627\u062A \u0645\u062F\u06CC\u0631\u06CC\u062A \u062B\u0628\u062A \u0646\u0634\u062F\u0647 \u0627\u0633\u062A.</div>';
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
    topups.forEach(x => rows.push({label:"\u0627\u0641\u0632\u0627\u06CC\u0634 \u0627\u0639\u062A\u0628\u0627\u0631",amount:x.amount_toman,status:x.status,date:x.created_at}));
    payments.forEach(x => rows.push({label:"\u067E\u0631\u062F\u0627\u062E\u062A \u0631\u06CC\u0627\u0644\u062A",amount:x.amount_toman,status:x.status,date:x.created_at}));
    const panel = document.createElement("section");
    panel.className = "panel";
    panel.innerHTML = "<h3>\u0633\u0648\u0627\u0628\u0642 \u0642\u0628\u0644\u06CC \u062D\u0633\u0627\u0628</h3>" + rows.map(x => "<div class=\\"order\\"><div><strong>" + escapeHtml(x.label) + "</strong><div class=\\"muted\\">" + escapeHtml(x.date || "") + "</div></div><div style=\\"text-align:left\\"><strong>" + money(x.amount) + "</strong><div class=\\"muted\\">" + escapeHtml(x.status === "paid" || x.status === "approved" ? "\u067E\u0631\u062F\u0627\u062E\u062A \u062A\u0623\u06CC\u06CC\u062F \u0634\u062F\u0647" : x.status === "payment_link_failed" ? "\u0633\u0627\u062E\u062A \u0644\u06CC\u0646\u06A9 \u0646\u0627\u0645\u0648\u0641\u0642" : x.status) + "</div></div></div>").join("");
    document.querySelector(".shell").appendChild(panel);
  }
  function openTopup() {
    const root = $("sheetRoot");
    root.className = "backdrop";
    root.innerHTML = '<section class="sheet"><h2>\u0627\u0641\u0632\u0627\u06CC\u0634 \u0627\u0639\u062A\u0628\u0627\u0631 \u062D\u0633\u0627\u0628</h2><div class="muted">\u0645\u0628\u0644\u063A \u0631\u0627 \u0628\u0647 \u062A\u0648\u0645\u0627\u0646 \u0648\u0627\u0631\u062F \u06A9\u0646\u06CC\u062F. \u062D\u062F\u0627\u0642\u0644 \u06A9\u0627\u0631\u062A\u200C\u0628\u0647\u200C\u06A9\u0627\u0631\u062A \u06F2\u06F0\u066C\u06F0\u06F0\u06F0 \u0648 \u062D\u062F\u0627\u0642\u0644 \u0631\u06CC\u0627\u0644\u062A \u06F5\u06F0\u066C\u06F0\u06F0\u06F0 \u062A\u0648\u0645\u0627\u0646 \u0627\u0633\u062A.</div><label class="field"><span>\u0645\u0628\u0644\u063A \u0627\u0641\u0632\u0627\u06CC\u0634 \u0627\u0639\u062A\u0628\u0627\u0631</span><input id="topupAmount" type="number" min="20000" max="10000000" step="1000" placeholder="\u0645\u062B\u0644\u0627\u064B \u06F1\u06F0\u06F0\u06F0\u06F0\u06F0"></label><div class="actions"><button class="primary" id="topupRialit">\u062F\u0631\u06AF\u0627\u0647 \u067E\u0631\u062F\u0627\u062E\u062A \u0631\u0645\u0632 \u067E\u0648\u06CC\u0627</button><button class="secondary" id="topupCard">\u06A9\u0627\u0631\u062A \u0628\u0647 \u06A9\u0627\u0631\u062A</button></div><div id="topupResult"></div><div class="actions"><button class="secondary" id="closeTopup">\u0628\u0627\u0632\u06AF\u0634\u062A</button></div></section>';
    $("closeTopup").onclick = closeSheet;
    $("topupRialit").onclick = async () => {
      const amount = Number($("topupAmount").value);
      const b = $("topupRialit"); b.disabled = true;
      try {
        const topup = await api("/api/miniapp/topups", {method:"POST",body:JSON.stringify({amount_toman:amount,method:"rialit"})});
        const result = await api("/api/miniapp/topups/rialit", {method:"POST",body:JSON.stringify({topup_id:topup.topup_id})});
        $("topupResult").innerHTML = '<div class="notice success">\u0645\u0628\u0644\u063A \u067E\u0627\u06CC\u0647: ' + money(result.amount_toman) + '<br>\u06A9\u0627\u0631\u0645\u0632\u062F \u0631\u06CC\u0627\u0644\u062A: ' + money(result.payer_fee_toman) + '<br>\u0645\u0628\u0644\u063A \u0646\u0647\u0627\u06CC\u06CC \u062F\u0631\u06AF\u0627\u0647: <strong>' + money(result.payer_amount_toman) + '</strong></div><button class="primary" id="openTopupRialit">\u0648\u0631\u0648\u062F \u0628\u0647 \u062F\u0631\u06AF\u0627\u0647</button>';
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
          $("topupResult").innerHTML = '<div class="notice error">\u0627\u0637\u0644\u0627\u0639\u0627\u062A \u06A9\u0627\u0631\u062A \u062F\u0641\u062A\u0631 \u0647\u0646\u0648\u0632 \u062F\u0631 \u062A\u0646\u0638\u06CC\u0645\u0627\u062A \u0645\u062F\u06CC\u0631\u06CC\u062A \u062B\u0628\u062A \u0646\u0634\u062F\u0647 \u0627\u0633\u062A.</div>';
        } else {
          $("topupResult").innerHTML = '<div class="notice">\u0645\u0628\u0644\u063A \u0648\u0627\u0631\u06CC\u0632: <strong>' + money(amount) + '</strong><br>\u0634\u0645\u0627\u0631\u0647 \u06A9\u0627\u0631\u062A: <strong>' + escapeHtml(number) + '</strong><br>\u0628\u0647 \u0646\u0627\u0645: ' + escapeHtml(settings.card_holder || "\u2014") + '<br>\u067E\u0633 \u0627\u0632 \u0648\u0627\u0631\u06CC\u0632\u060C \u0631\u0633\u06CC\u062F \u0631\u0627 \u062F\u0631 \u06AF\u0641\u062A\u06AF\u0648\u06CC \u0631\u0628\u0627\u062A \u0627\u0631\u0633\u0627\u0644 \u06A9\u0646\u06CC\u062F.</div><button class="secondary" id="copyTopupCard">\u06A9\u067E\u06CC \u0634\u0645\u0627\u0631\u0647 \u06A9\u0627\u0631\u062A</button>';
          $("copyTopupCard").onclick = async () => { try { await navigator.clipboard.writeText(number); $("copyTopupCard").textContent = "\u06A9\u067E\u06CC \u0634\u062F"; } catch { $("copyTopupCard").textContent = number; } };
        }
      } catch(error) { $("topupResult").innerHTML = '<div class="notice error">' + escapeHtml(error.message) + '</div>'; }
      finally { b.disabled = false; }
    };
  }
  function setTheme(theme) {
    document.body.dataset.theme = theme;
    const button = $("themeButton");
    if (button) {
      button.textContent = theme === "dark" ? "\u2600\uFE0F \u062D\u0627\u0644\u062A \u0631\u0648\u0632" : "\u{1F319} \u062D\u0627\u0644\u062A \u0634\u0628";
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
      $("services").innerHTML = \`<div class="empty">\${escapeHtml(error.message)}<br>\u0627\u06CC\u0646 \u0635\u0641\u062D\u0647 \u0628\u0627\u06CC\u062F \u0627\u0632 \u062F\u0627\u062E\u0644 \u0631\u0628\u0627\u062A \u062A\u0644\u06AF\u0631\u0627\u0645 \u0628\u0627\u0632 \u0634\u0648\u062F.</div>\`;
      $("orders").innerHTML = "";
    }
  }
  boot();
})();
`;

// src/fees.ts
function expectedPayerAmount(baseToman, feePercent = 12) {
  if (!Number.isSafeInteger(baseToman) || baseToman < 1) throw new Error("invalid_base_amount");
  if (!Number.isFinite(feePercent) || feePercent < 0 || feePercent >= 100) throw new Error("invalid_fee_percent");
  return Math.ceil(baseToman * (100 + feePercent) / 100);
}
function matchesRialitFee(baseToman, payerAmount, payerFee, feePercent = 12) {
  const expected = expectedPayerAmount(baseToman, feePercent);
  return Number.isSafeInteger(payerAmount) && Number.isSafeInteger(payerFee) && payerAmount === expected && payerFee === expected - baseToman;
}

// src/index.ts
var json = (data, status = 200) => new Response(JSON.stringify(data), {
  status,
  headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
});
var text = (value, status = 200) => new Response(value, { status, headers: { "content-type": "text/plain; charset=utf-8" } });
function toHex(bytes) {
  return [...new Uint8Array(bytes)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
async function verifyTelegramInitData(initData, botToken) {
  if (!initData || !botToken) return null;
  const params = new URLSearchParams(initData);
  const receivedHash = params.get("hash");
  const authDate = Number(params.get("auth_date") || 0);
  if (!receivedHash || !authDate || Math.abs(Date.now() / 1e3 - authDate) > 86400) return null;
  const checkString = [...params.entries()].filter(([key]) => key !== "hash").sort(([a], [b]) => a.localeCompare(b)).map(([key, value]) => `${key}=${value}`).join("\n");
  const encoder = new TextEncoder();
  const initialKey = await crypto.subtle.importKey(
    "raw",
    encoder.encode(botToken),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const secret = await crypto.subtle.sign("HMAC", initialKey, encoder.encode("WebAppData"));
  const validationKey = await crypto.subtle.importKey(
    "raw",
    secret,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const calculated = toHex(await crypto.subtle.sign("HMAC", validationKey, encoder.encode(checkString)));
  if (calculated.length !== receivedHash.length) return null;
  let mismatch = 0;
  for (let i = 0; i < calculated.length; i++) mismatch |= calculated.charCodeAt(i) ^ receivedHash.charCodeAt(i);
  if (mismatch !== 0) return null;
  try {
    return JSON.parse(params.get("user") || "null");
  } catch {
    return null;
  }
}
async function miniAppUser(request, env) {
  return verifyTelegramInitData(
    request.headers.get("x-telegram-init-data") || "",
    env.BOT_TOKEN
  );
}
async function ensureUser(db, user) {
  await db.prepare(`
    INSERT INTO users (telegram_id, first_name, last_name, username)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(telegram_id) DO UPDATE SET
      first_name = excluded.first_name,
      last_name = excluded.last_name,
      username = excluded.username,
      updated_at = CURRENT_TIMESTAMP
  `).bind(String(user.id), user.first_name || null, user.last_name || null, user.username || null).run();
  const row = await db.prepare("SELECT id FROM users WHERE telegram_id = ?").bind(String(user.id)).first();
  if (!row) throw new Error("user_upsert_failed");
  return row.id;
}
async function telegram(env, method, payload) {
  const response = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload)
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || !body?.ok) {
    console.error("Telegram API failure", method, response.status);
    throw new Error("telegram_api_failed");
  }
  return body.result;
}
function homeKeyboard(appUrl) {
  return {
    inline_keyboard: [
      [{ text: "\u{1F680} \u0648\u0631\u0648\u062F \u0628\u0647 \u0645\u06CC\u0646\u06CC\u200C\u0627\u067E \u06A9\u0645\u06A9\u200C\u06CC\u0627\u0631 \u0645\u0647\u0627\u062C\u0631", web_app: { url: appUrl } }],
      [
        { text: "\u{1F9FE} \u062E\u062F\u0645\u0627\u062A \u062F\u0641\u062A\u0631 \u0646\u062A\u200C\u06CC\u0627\u0631 \u0645\u0647\u0627\u062C\u0631", callback_data: "menu:services" },
        { text: "\u{1F4B0} \u0627\u0639\u062A\u0628\u0627\u0631 \u0645\u0646", callback_data: "menu:wallet" }
      ],
      [
        { text: "\u{1F4C2} \u067E\u0631\u0648\u0646\u062F\u0647\u200C\u0647\u0627\u06CC \u0645\u0646", callback_data: "menu:orders" },
        { text: "\u{1F3A7} \u067E\u0634\u062A\u06CC\u0628\u0627\u0646\u06CC", callback_data: "menu:support" }
      ]
    ]
  };
}
async function isAdmin(env, telegramId) {
  const configured = new Set((env.ADMIN_IDS || "").split(",").map((x) => x.trim()).filter(Boolean));
  if (configured.has(String(telegramId))) return true;
  const row = await env.DB.prepare("SELECT id FROM operators WHERE telegram_id = ? AND active = 1 AND role IN ('admin','owner','operator')").bind(String(telegramId)).first();
  return Boolean(row);
}
async function notifyAdmins(env, details) {
  const ids = new Set((env.ADMIN_IDS || "").split(",").map((x) => x.trim()).filter(Boolean));
  const operators = await env.DB.prepare("SELECT telegram_id FROM operators WHERE active=1 AND role IN ('admin','owner','operator')").all();
  for (const row of operators.results || []) ids.add(String(row.telegram_id));
  const caption = "\u{1F9FE} \u0631\u0633\u06CC\u062F \u062C\u062F\u06CC\u062F\n" + details.title + "\n\u0645\u0628\u0644\u063A: " + details.amount.toLocaleString("en-US") + " \u062A\u0648\u0645\u0627\u0646\n\u0634\u0646\u0627\u0633\u0647 \u067E\u0631\u062F\u0627\u062E\u062A: #" + details.paymentId + "\n\u0634\u0646\u0627\u0633\u0647 \u0645\u0634\u062A\u0631\u06A9: " + details.userTelegramId;
  const reply_markup = { inline_keyboard: [[
    { text: "\u2705 \u062A\u0623\u06CC\u06CC\u062F \u0631\u0633\u06CC\u062F", callback_data: "admin:payment:approve:" + details.paymentId },
    { text: "\u274C \u0631\u062F \u0631\u0633\u06CC\u062F", callback_data: "admin:payment:reject:" + details.paymentId }
  ]] };
  for (const id of ids) {
    const method = details.mediaType === "photo" ? "sendPhoto" : "sendDocument";
    const mediaKey = details.mediaType === "photo" ? "photo" : "document";
    await telegram(env, method, {
      chat_id: id,
      [mediaKey]: details.fileId,
      caption,
      reply_markup
    }).catch(() => void 0);
  }
}
async function processReceiptMessage(message, user, userId, env) {
  const photo = Array.isArray(message.photo) && message.photo.length ? message.photo[message.photo.length - 1] : null;
  const document = message.document || null;
  if (!photo && !document) return false;
  const fileId = String(photo?.file_id || document?.file_id || "");
  if (!fileId) return false;
  const mediaType = photo ? "photo" : "document";
  const topup = await env.DB.prepare("SELECT id,amount_toman FROM wallet_topups WHERE user_id=? AND status='awaiting_receipt' ORDER BY id DESC LIMIT 1").bind(userId).first();
  if (topup) {
    const providerPaymentId = "topup:" + topup.id;
    const payment2 = await env.DB.prepare("SELECT id FROM payments WHERE user_id=? AND provider='card_transfer' AND provider_payment_id=? AND status='awaiting_receipt'").bind(userId, providerPaymentId).first();
    if (!payment2) return false;
    await env.DB.batch([
      env.DB.prepare("UPDATE wallet_topups SET receipt_file_id=?,receipt_type=?,status='awaiting_receipt_review' WHERE id=? AND status='awaiting_receipt'").bind(fileId, mediaType, topup.id),
      env.DB.prepare("UPDATE payments SET receipt_file_id=?,receipt_type=?,status='awaiting_review' WHERE id=? AND status='awaiting_receipt'").bind(fileId, mediaType, payment2.id),
      env.DB.prepare("INSERT INTO documents(user_id,document_type,telegram_file_id,media_type,caption,review_status) VALUES(?,'wallet_topup_receipt',?,?,?,'pending')").bind(userId, fileId, mediaType, message.caption || null)
    ]);
    await notifyAdmins(env, { paymentId: payment2.id, userTelegramId: user.id, amount: Number(topup.amount_toman), title: "\u0627\u0641\u0632\u0627\u06CC\u0634 \u0627\u0639\u062A\u0628\u0627\u0631", fileId, mediaType });
    await telegram(env, "sendMessage", { chat_id: user.id, text: "\u2705 \u0631\u0633\u06CC\u062F \u0627\u0641\u0632\u0627\u06CC\u0634 \u0627\u0639\u062A\u0628\u0627\u0631 \u062F\u0631\u06CC\u0627\u0641\u062A \u0634\u062F. \u067E\u0633 \u0627\u0632 \u0628\u0631\u0631\u0633\u06CC \u0645\u062F\u06CC\u0631\u06CC\u062A\u060C \u0646\u062A\u06CC\u062C\u0647 \u0628\u0647 \u0634\u0645\u0627 \u0627\u0637\u0644\u0627\u0639 \u062F\u0627\u062F\u0647 \u0645\u06CC\u200C\u0634\u0648\u062F." });
    return true;
  }
  const payment = await env.DB.prepare("SELECT id,order_id,amount_toman FROM payments WHERE user_id=? AND provider='card_transfer' AND order_id IS NOT NULL AND status='awaiting_receipt' ORDER BY id DESC LIMIT 1").bind(userId).first();
  if (!payment) return false;
  await env.DB.batch([
    env.DB.prepare("UPDATE payments SET receipt_file_id=?,receipt_type=?,status='awaiting_review' WHERE id=? AND status='awaiting_receipt'").bind(fileId, mediaType, payment.id),
    env.DB.prepare("UPDATE orders SET status='waiting_receipt_review',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='awaiting_receipt'").bind(payment.order_id),
    env.DB.prepare("INSERT INTO documents(order_id,user_id,document_type,telegram_file_id,media_type,caption,review_status) VALUES(?,?,'payment_receipt',?,?,?,'pending')").bind(payment.order_id, userId, fileId, mediaType, message.caption || null)
  ]);
  await notifyAdmins(env, { paymentId: payment.id, userTelegramId: user.id, amount: Number(payment.amount_toman), title: "\u067E\u0631\u062F\u0627\u062E\u062A \u067E\u0631\u0648\u0646\u062F\u0647 \u0634\u0645\u0627\u0631\u0647 " + payment.order_id, fileId, mediaType });
  await telegram(env, "sendMessage", { chat_id: user.id, text: "\u2705 \u0631\u0633\u06CC\u062F \u067E\u0631\u062F\u0627\u062E\u062A \u067E\u0631\u0648\u0646\u062F\u0647 \u062F\u0631\u06CC\u0627\u0641\u062A \u0634\u062F \u0648 \u0628\u0631\u0627\u06CC \u0628\u0631\u0631\u0633\u06CC \u0645\u062F\u06CC\u0631\u06CC\u062A \u0627\u0631\u0633\u0627\u0644 \u0634\u062F." });
  return true;
}
async function claimFirstAdmin(message, user, env) {
  const textValue = String(message.text || "").trim();
  if (!textValue.startsWith("/claim_admin")) return false;
  const supplied = textValue.split(/\s+/)[1] || "";
  if (!env.ADMIN_SETUP_SECRET || supplied !== env.ADMIN_SETUP_SECRET) {
    await telegram(env, "sendMessage", { chat_id: user.id, text: "\u06A9\u062F \u0641\u0639\u0627\u0644\u200C\u0633\u0627\u0632\u06CC \u067E\u0646\u0644 \u0645\u062F\u06CC\u0631\u06CC\u062A \u0645\u0639\u062A\u0628\u0631 \u0646\u06CC\u0633\u062A." });
    return true;
  }
  const existing = await env.DB.prepare("SELECT COUNT(*) AS n FROM operators WHERE active=1 AND role IN ('admin','owner')").first();
  if (Number(existing?.n || 0) > 0) {
    await telegram(env, "sendMessage", { chat_id: user.id, text: "\u0645\u062F\u06CC\u0631 \u0627\u0635\u0644\u06CC \u0642\u0628\u0644\u0627\u064B \u062B\u0628\u062A \u0634\u062F\u0647 \u0627\u0633\u062A. \u0628\u0631\u0627\u06CC \u0627\u0641\u0632\u0648\u062F\u0646 \u0645\u062F\u06CC\u0631 \u062C\u062F\u06CC\u062F \u0628\u0627 \u0645\u062F\u06CC\u0631 \u0641\u0639\u0644\u06CC \u062A\u0645\u0627\u0633 \u0628\u06AF\u06CC\u0631\u06CC\u062F." });
    return true;
  }
  await env.DB.prepare("INSERT OR IGNORE INTO operators(telegram_id,display_name,role,permissions_json,active) VALUES(?,?,'admin','{}',1)").bind(String(user.id), [user.first_name, user.last_name].filter(Boolean).join(" ")).run();
  await env.DB.prepare("INSERT INTO settings(key,value) VALUES('admin_setup_claimed','1') ON CONFLICT(key) DO UPDATE SET value='1',updated_at=CURRENT_TIMESTAMP").run();
  await telegram(env, "sendMessage", { chat_id: user.id, text: "\u2705 \u062F\u0633\u062A\u0631\u0633\u06CC \u0645\u062F\u06CC\u0631 \u0627\u0635\u0644\u06CC \u0641\u0639\u0627\u0644 \u0634\u062F. \u0627\u0632 \u0627\u06CC\u0646 \u067E\u0633 \u0631\u0633\u06CC\u062F\u0647\u0627\u06CC \u06A9\u0627\u0631\u062A\u200C\u0628\u0647\u200C\u06A9\u0627\u0631\u062A \u0628\u0631\u0627\u06CC \u0628\u0631\u0631\u0633\u06CC \u0628\u0647 \u0634\u0645\u0627 \u0627\u0631\u0633\u0627\u0644 \u0645\u06CC\u200C\u0634\u0648\u0646\u062F." });
  return true;
}
async function handleAdminPaymentCallback(callback, env) {
  const match = String(callback.data || "").match(/^admin:payment:(approve|reject):(\d+)$/);
  if (!match) return false;
  const actorId = Number(callback.from?.id || 0);
  if (!await isAdmin(env, actorId)) {
    await telegram(env, "answerCallbackQuery", { callback_query_id: callback.id, text: "\u0634\u0645\u0627 \u062F\u0633\u062A\u0631\u0633\u06CC \u0645\u062F\u06CC\u0631\u06CC\u062A \u0646\u062F\u0627\u0631\u06CC\u062F.", show_alert: true });
    return true;
  }
  const action = match[1];
  const paymentId = Number(match[2]);
  const payment = await env.DB.prepare("SELECT p.*,u.telegram_id AS user_telegram_id FROM payments p JOIN users u ON u.id=p.user_id WHERE p.id=?").bind(paymentId).first();
  if (!payment || payment.status !== "awaiting_review") {
    await telegram(env, "answerCallbackQuery", { callback_query_id: callback.id, text: "\u0627\u06CC\u0646 \u0631\u0633\u06CC\u062F \u0642\u0628\u0644\u0627\u064B \u0628\u0631\u0631\u0633\u06CC \u0634\u062F\u0647 \u06CC\u0627 \u0648\u062C\u0648\u062F \u0646\u062F\u0627\u0631\u062F.", show_alert: true });
    return true;
  }
  const isTopup = String(payment.provider_payment_id || "").startsWith("topup:");
  const topupId = isTopup ? Number(String(payment.provider_payment_id).slice(6)) : 0;
  if (action === "approve" && isTopup) {
    await env.DB.batch([
      env.DB.prepare("UPDATE payments SET status='approved',verified_at=CURRENT_TIMESTAMP WHERE id=? AND status='awaiting_review'").bind(paymentId),
      env.DB.prepare("UPDATE wallet_topups SET status='approved',reviewed_at=CURRENT_TIMESTAMP,reviewed_by=? WHERE id=? AND status='awaiting_receipt_review' AND changes()=1").bind(String(actorId), topupId),
      env.DB.prepare("INSERT OR IGNORE INTO wallet_credit_events(source_key) SELECT 'card:topup:' || ? WHERE changes()=1").bind(topupId),
      env.DB.prepare("INSERT OR IGNORE INTO wallets(user_id,balance_toman) SELECT user_id,0 FROM wallet_topups WHERE id=? AND status='approved'").bind(topupId),
      env.DB.prepare("UPDATE wallets SET balance_toman=balance_toman+? WHERE user_id=(SELECT user_id FROM wallet_topups WHERE id=?) AND EXISTS(SELECT 1 FROM wallet_credit_events WHERE source_key=?) AND NOT EXISTS(SELECT 1 FROM wallet_transactions WHERE related_id=?)").bind(payment.amount_toman, topupId, "card:topup:" + topupId, "card:topup:" + topupId),
      env.DB.prepare("INSERT OR IGNORE INTO wallet_transactions(user_id,amount_toman,balance_after_toman,kind,description,related_id,topup_id) SELECT w.user_id,?,w.balance_toman,'topup','\u0627\u0641\u0632\u0627\u06CC\u0634 \u0627\u0639\u062A\u0628\u0627\u0631 \u06A9\u0627\u0631\u062A\u200C\u0628\u0647\u200C\u06A9\u0627\u0631\u062A',?,? FROM wallets w WHERE w.user_id=(SELECT user_id FROM wallet_topups WHERE id=?) AND changes()=1").bind(payment.amount_toman, "card:topup:" + topupId, topupId, topupId)
    ]);
  } else if (action === "approve") {
    await env.DB.batch([
      env.DB.prepare("UPDATE payments SET status='approved',verified_at=CURRENT_TIMESTAMP WHERE id=? AND status='awaiting_review'").bind(paymentId),
      env.DB.prepare("UPDATE orders SET status='payment_approved',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='waiting_receipt_review' AND changes()=1").bind(payment.order_id)
    ]);
  } else {
    await env.DB.prepare("UPDATE payments SET status='rejected' WHERE id=? AND status='awaiting_review'").bind(paymentId).run();
    if (isTopup) {
      await env.DB.prepare("UPDATE wallet_topups SET status='rejected',reviewed_at=CURRENT_TIMESTAMP,reviewed_by=? WHERE id=? AND status='awaiting_receipt_review'").bind(String(actorId), topupId).run();
    } else if (payment.order_id) {
      await env.DB.prepare("UPDATE orders SET status='payment_rejected',updated_at=CURRENT_TIMESTAMP WHERE id=?").bind(payment.order_id).run();
    }
  }
  const userTelegramId = String(payment.user_telegram_id);
  await telegram(env, "sendMessage", { chat_id: userTelegramId, text: action === "approve" ? "\u2705 \u0631\u0633\u06CC\u062F \u067E\u0631\u062F\u0627\u062E\u062A \u0634\u0645\u0627 \u062A\u0623\u06CC\u06CC\u062F \u0634\u062F." : "\u274C \u0631\u0633\u06CC\u062F \u067E\u0631\u062F\u0627\u062E\u062A \u0634\u0645\u0627 \u062A\u0623\u06CC\u06CC\u062F \u0646\u0634\u062F. \u0628\u0631\u0627\u06CC \u067E\u06CC\u06AF\u06CC\u0631\u06CC \u0628\u0627 \u067E\u0634\u062A\u06CC\u0628\u0627\u0646\u06CC \u062A\u0645\u0627\u0633 \u0628\u06AF\u06CC\u0631\u06CC\u062F." }).catch(() => void 0);
  await telegram(env, "answerCallbackQuery", { callback_query_id: callback.id, text: action === "approve" ? "\u0631\u0633\u06CC\u062F \u062A\u0623\u06CC\u06CC\u062F \u0634\u062F." : "\u0631\u0633\u06CC\u062F \u0631\u062F \u0634\u062F." });
  if (callback.message?.chat?.id) {
    await telegram(env, "editMessageReplyMarkup", { chat_id: callback.message.chat.id, message_id: callback.message.message_id, reply_markup: { inline_keyboard: [] } });
  }
  return true;
}
async function ensureTelegramWebhook(env, origin) {
  if (!env.BOT_TOKEN || !env.TELEGRAM_WEBHOOK_SECRET) return;
  const existing = await env.DB.prepare("SELECT value FROM settings WHERE key='telegram_webhook_origin'").first();
  if (existing?.value === origin) return;
  const url = origin.replace(/\/$/, "") + "/webhooks/telegram";
  try {
    const response = await fetch("https://api.telegram.org/bot" + env.BOT_TOKEN + "/setWebhook", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ url, secret_token: env.TELEGRAM_WEBHOOK_SECRET, allowed_updates: ["message", "callback_query"], drop_pending_updates: false }),
      signal: AbortSignal.timeout(12e3)
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || result?.ok !== true) {
      console.error("Telegram webhook setup failed", response.status);
      return;
    }
    await env.DB.prepare("INSERT INTO settings(key,value) VALUES('telegram_webhook_origin',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP").bind(origin).run();
    await telegram(env, "setChatMenuButton", { menu_button: { type: "web_app", text: "\u06A9\u0645\u06A9\u200C\u06CC\u0627\u0631 \u0645\u0647\u0627\u062C\u0631", web_app: { url: origin + "/app/" } } }).catch(() => void 0);
  } catch (error) {
    console.error("Telegram webhook setup unavailable", error);
  }
}
async function handleTelegram(request, env) {
  const expected = env.TELEGRAM_WEBHOOK_SECRET;
  const supplied = request.headers.get("x-telegram-bot-api-secret-token");
  if (!expected || supplied !== expected) return text("forbidden", 403);
  const update = await request.json().catch(() => null);
  if (!update || !Number.isInteger(update.update_id)) return json({ ok: false }, 400);
  await env.DB.prepare("INSERT OR IGNORE INTO telegram_updates(update_id,status,processing_at) VALUES (?,'received',CURRENT_TIMESTAMP)").bind(update.update_id).run();
  const claim = await env.DB.prepare("UPDATE telegram_updates SET status='processing',processing_at=CURRENT_TIMESTAMP WHERE update_id=? AND (status='received' OR (status='processing' AND processing_at < datetime('now','-1 minute')))").bind(update.update_id).run();
  if ((claim.meta?.changes || 0) !== 1) return json({ ok: true, duplicate: true });
  try {
    const message = update.message;
    if (message?.from?.id) {
      const user = message.from;
      const userId = await ensureUser(env.DB, user);
      if (await claimFirstAdmin(message, user, env)) {
        await env.DB.prepare("UPDATE telegram_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
        return json({ ok: true });
      }
      const incomingText = String(message.text || "").trim();
      if (incomingText.startsWith("/setcard")) {
        if (!await isAdmin(env, user.id)) {
          await telegram(env, "sendMessage", { chat_id: user.id, text: "\u062F\u0633\u062A\u0631\u0633\u06CC \u0645\u062F\u06CC\u0631\u06CC\u062A \u0646\u062F\u0627\u0631\u06CC\u062F." });
        } else {
          const values = incomingText.replace(/^\/setcard\s*/, "").split("|").map((x) => x.trim());
          if (values.length < 3 || !/^\d{16}$/.test(values[0])) {
            await telegram(env, "sendMessage", { chat_id: user.id, text: "\u0642\u0627\u0644\u0628 \u062F\u0633\u062A\u0648\u0631: /setcard \u0634\u0645\u0627\u0631\u0647\u200C\u06A9\u0627\u0631\u062A\u06F1\u06F6\u0631\u0642\u0645\u06CC|\u0646\u0627\u0645\u200C\u062F\u0627\u0631\u0646\u062F\u0647|\u0646\u0627\u0645\u200C\u0628\u0627\u0646\u06A9" });
          } else {
            const pairs = [["card_number", values[0]], ["card_holder", values[1]], ["card_bank", values[2]]];
            await env.DB.batch(pairs.map(([key, value]) => env.DB.prepare("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP").bind(key, value)));
            await telegram(env, "sendMessage", { chat_id: user.id, text: "\u2705 \u0627\u0637\u0644\u0627\u0639\u0627\u062A \u06A9\u0627\u0631\u062A \u062F\u0641\u062A\u0631 \u0630\u062E\u06CC\u0631\u0647 \u0634\u062F." });
          }
        }
        await env.DB.prepare("UPDATE telegram_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
        return json({ ok: true });
      }
      if (await processReceiptMessage(message, user, userId, env)) {
        await env.DB.prepare("UPDATE telegram_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
        return json({ ok: true });
      }
      const appUrl = new URL("/app/", request.url).toString();
      const greeting = String(message.text || "").startsWith("/start") ? user.first_name ? "\u0633\u0644\u0627\u0645 " + user.first_name + " \u0639\u0632\u06CC\u0632 \u{1F337}\n\n" : "\u0633\u0644\u0627\u0645 \u0648 \u062E\u0648\u0634 \u0622\u0645\u062F\u06CC\u062F \u{1F337}\n\n" : "";
      await telegram(env, "sendMessage", {
        chat_id: message.chat.id,
        text: greeting + "\u0628\u0647 \xAB\u06A9\u0645\u06A9\u200C\u06CC\u0627\u0631 \u0645\u0647\u0627\u062C\u0631\xBB \u062E\u0648\u0634 \u0622\u0645\u062F\u06CC\u062F.\n\u0627\u0632 \u062F\u06A9\u0645\u0647 \u0632\u06CC\u0631 \u0628\u0631\u0627\u06CC \u062B\u0628\u062A \u062E\u062F\u0645\u0627\u062A\u060C \u067E\u06CC\u06AF\u06CC\u0631\u06CC \u067E\u0631\u0648\u0646\u062F\u0647 \u0648 \u0645\u062F\u06CC\u0631\u06CC\u062A \u0627\u0639\u062A\u0628\u0627\u0631 \u0627\u0633\u062A\u0641\u0627\u062F\u0647 \u06A9\u0646\u06CC\u062F.",
        reply_markup: homeKeyboard(appUrl)
      });
    }
    const callback = update.callback_query;
    if (callback?.id && callback?.from?.id) {
      if (await handleAdminPaymentCallback(callback, env)) {
        await env.DB.prepare("UPDATE telegram_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
        return json({ ok: true });
      }
      await telegram(env, "answerCallbackQuery", { callback_query_id: callback.id });
      const chatId = callback.message?.chat?.id;
      if (chatId) {
        const appUrl = new URL("/app/", request.url).toString();
        const labels = {
          "menu:home": "\u0635\u0641\u062D\u0647 \u0627\u0635\u0644\u06CC \u06A9\u0645\u06A9\u200C\u06CC\u0627\u0631 \u0645\u0647\u0627\u062C\u0631",
          "menu:services": "\u0628\u0631\u0627\u06CC \u062B\u0628\u062A \u062F\u0631\u062E\u0648\u0627\u0633\u062A \u062E\u062F\u0645\u062A\u060C \u0645\u06CC\u0646\u06CC\u200C\u0627\u067E \u0631\u0627 \u0628\u0627\u0632 \u06A9\u0646\u06CC\u062F.",
          "menu:wallet": "\u0628\u0631\u0627\u06CC \u0645\u0634\u0627\u0647\u062F\u0647 \u0627\u0639\u062A\u0628\u0627\u0631 \u0648 \u0627\u0641\u0632\u0627\u06CC\u0634 \u0645\u0648\u062C\u0648\u062F\u06CC\u060C \u0645\u06CC\u0646\u06CC\u200C\u0627\u067E \u0631\u0627 \u0628\u0627\u0632 \u06A9\u0646\u06CC\u062F.",
          "menu:orders": "\u0628\u0631\u0627\u06CC \u067E\u06CC\u06AF\u06CC\u0631\u06CC \u067E\u0631\u0648\u0646\u062F\u0647\u200C\u0647\u0627\u060C \u0645\u06CC\u0646\u06CC\u200C\u0627\u067E \u0631\u0627 \u0628\u0627\u0632 \u06A9\u0646\u06CC\u062F.",
          "menu:support": "\u067E\u06CC\u0627\u0645 \u062E\u0648\u062F \u0631\u0627 \u0628\u0631\u0627\u06CC \u067E\u0634\u062A\u06CC\u0628\u0627\u0646\u06CC \u0627\u0631\u0633\u0627\u0644 \u06A9\u0646\u06CC\u062F."
        };
        await telegram(env, "sendMessage", { chat_id: chatId, text: labels[String(callback.data)] || "\u0628\u0631\u0627\u06CC \u0627\u062F\u0627\u0645\u0647\u060C \u0645\u06CC\u0646\u06CC\u200C\u0627\u067E \u0631\u0627 \u0628\u0627\u0632 \u06A9\u0646\u06CC\u062F.", reply_markup: homeKeyboard(appUrl) });
      }
    }
    await env.DB.prepare("UPDATE telegram_updates SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
    return json({ ok: true });
  } catch (error) {
    await env.DB.prepare("UPDATE telegram_updates SET status='received',processing_at=NULL WHERE update_id=?").bind(update.update_id).run();
    console.error("Telegram update processing failed", error);
    return json({ ok: false, error: "telegram_update_failed" }, 503);
  }
}
async function bootstrap(request, env) {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const userId = await ensureUser(env.DB, user);
  const [services, wallet, orders, settings] = await Promise.all([
    env.DB.prepare("SELECT id, code, name, price_toman, description, rules_text FROM services WHERE enabled = 1 ORDER BY id").all(),
    env.DB.prepare("SELECT balance_toman FROM wallets WHERE user_id = ?").bind(userId).first(),
    env.DB.prepare(`
      SELECT o.id, o.public_id, o.status, COALESCE(o.price_snapshot_toman,o.amount_toman) AS price_snapshot_toman, o.created_at, s.name AS service_name
      FROM orders o LEFT JOIN services s ON s.id = o.service_id
      WHERE o.user_id = ? ORDER BY o.id DESC LIMIT 20
    `).bind(userId).all(),
    env.DB.prepare("SELECT key, value FROM settings WHERE key IN ('card_number','card_holder','card_bank','support_username')").all()
  ]);
  let legacy = { wallet_topups: [], rialit_payments: [] };
  let serviceRows = services.results || [];
  try {
    const legacyUser = await env.LEGACY_DB.prepare("SELECT id FROM users WHERE telegram_id = ?").bind(String(user.id)).first();
    if (legacyUser) {
      const [legacyTopups, legacyPayments] = await Promise.all([
        env.LEGACY_DB.prepare("SELECT t.id,t.amount_toman,CASE WHEN t.status='awaiting_payment' AND EXISTS(SELECT 1 FROM rialit_payments rp WHERE rp.topup_id=t.id AND rp.status IN ('failed','expired','cancelled')) THEN 'payment_link_failed' ELSE t.status END AS status,t.created_at,t.reviewed_at FROM wallet_topups t WHERE t.user_id = ? ORDER BY t.id DESC LIMIT 20").bind(legacyUser.id).all(),
        env.LEGACY_DB.prepare("SELECT kind,amount_toman,status,created_at,paid_at FROM rialit_payments WHERE user_id = ? ORDER BY id DESC LIMIT 20").bind(legacyUser.id).all()
      ]);
      legacy = { wallet_topups: legacyTopups.results || [], rialit_payments: legacyPayments.results || [] };
    }
    const legacyServices = await env.LEGACY_DB.prepare("SELECT code,name,description,price_toman,enabled,rules_text FROM services").all();
    const byCode = new Map((legacyServices.results || []).map((x) => [x.code, x]));
    serviceRows = serviceRows.map((service) => {
      const old = byCode.get(service.code);
      if (!old) return service;
      return {
        ...service,
        name: service.name || old.name,
        description: service.description || old.description,
        price_toman: Number(service.price_toman || old.price_toman),
        rules_text: service.rules_text || old.rules_text
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
    settings: Object.fromEntries((settings.results || []).map((x) => [x.key, x.value])),
    payment: { rialit_fee_percent: Number(env.PAYMENT_FEE_PERCENT || "12"), min_toman: 5e4, max_toman: 1e7 }
  });
}
async function createOrder(request, env) {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json().catch(() => null);
  const serviceCode = String(body?.service_code || "");
  const formData = body?.form_data;
  if (body?.rules_accepted !== true) return json({ ok: false, error: "rules_not_accepted" }, 400);
  if (!serviceCode || !formData || typeof formData !== "object" || Array.isArray(formData)) {
    return json({ ok: false, error: "invalid_request" }, 400);
  }
  const userId = await ensureUser(env.DB, user);
  const serializedForm = JSON.stringify(formData);
  if (serializedForm.length > 2e4) return json({ ok: false, error: "form_too_large" }, 413);
  const service = await env.DB.prepare(
    "SELECT id, price_toman FROM services WHERE code = ? AND enabled = 1"
  ).bind(serviceCode).first();
  if (!service) return json({ ok: false, error: "service_unavailable" }, 404);
  if (!Number.isSafeInteger(service.price_toman) || service.price_toman < 1) {
    return json({ ok: false, error: "service_price_not_configured" }, 503);
  }
  const publicId = `YM-${crypto.randomUUID().replaceAll("-", "").slice(0, 10).toUpperCase()}`;
  const created = await env.DB.prepare(`
    INSERT INTO orders (public_id, user_id, service_id, service_code, amount_toman, price_snapshot_toman, status, data_json)
    VALUES (?, ?, ?, ?, ?, ?, 'waiting_payment', ?)
    RETURNING id
  `).bind(publicId, userId, service.id, serviceCode, service.price_toman, service.price_toman, serializedForm).first();
  if (!created) return json({ ok: false, error: "order_create_failed" }, 500);
  return json({ ok: true, order_id: created.id, public_id: publicId, amount_toman: service.price_toman });
}
async function createRialitPayment(request, env) {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json().catch(() => null);
  const orderId = Number(body?.order_id);
  if (!Number.isSafeInteger(orderId) || orderId < 1) return json({ ok: false, error: "invalid_order" }, 400);
  const userId = await ensureUser(env.DB, user);
  const order = await env.DB.prepare(`
    SELECT o.id, o.public_id, o.price_snapshot_toman, o.amount_toman, o.status
    FROM orders o WHERE o.id = ? AND o.user_id = ?
  `).bind(orderId, userId).first();
  if (!order) return json({ ok: false, error: "order_not_found" }, 404);
  if (order.status !== "waiting_payment") return json({ ok: false, error: "order_not_payable" }, 409);
  const amount = Number(order.price_snapshot_toman ?? order.amount_toman ?? 0);
  if (amount < 5e4 || amount > 1e7) {
    return json({ ok: false, error: "rialit_amount_out_of_range", card_transfer_available: true }, 400);
  }
  if (!env.RIALIT_API_KEY) return json({ ok: false, error: "rialit_not_configured" }, 503);
  const previous = await env.DB.prepare(
    "SELECT id, token, provider_order_id, pay_url, payer_amount_toman, payer_fee_toman, status, attempt_no FROM rialit_payments WHERE order_id = ? ORDER BY attempt_no DESC LIMIT 1"
  ).bind(order.id).first();
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
  let response;
  try {
    response = await fetch(`${apiBase}/send`, {
      method: "POST",
      headers: { authorization: `Bearer ${env.RIALIT_API_KEY}`, "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(25e3)
    });
  } catch {
    return json({ ok: false, error: "rialit_network_error", retry_same_order: true }, 502);
  }
  const result = await response.json().catch(() => ({}));
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
    await env.DB.prepare("UPDATE rialit_payments SET token=?,pay_url=?,payer_amount_toman=?,payer_fee_toman=?,status='fee_mismatch' WHERE provider_order_id=? AND status='pending'").bind(token, payUrl, payerAmount, payerFee, providerOrderId).run();
    return json({ ok: false, error: "rialit_fee_mismatch", expected_payer_amount_toman: expectedPayerAmount(amount, feePercent) }, 409);
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
    fee_configuration_matches: true
  });
}
async function createWalletTopup(request, env) {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json().catch(() => null);
  const amount = Number(body?.amount_toman);
  const method = String(body?.method || "");
  if (!Number.isSafeInteger(amount) || amount < 2e4 || amount > 1e7 || !["card", "rialit"].includes(method)) {
    return json({ ok: false, error: "invalid_topup_amount_or_method" }, 400);
  }
  if (method === "rialit" && amount < 5e4) return json({ ok: false, error: "rialit_minimum_50000" }, 400);
  const userId = await ensureUser(env.DB, user);
  if (method === "card") {
    const card = await env.DB.prepare("SELECT value FROM settings WHERE key='card_number'").first();
    if (!card?.value) return json({ ok: false, error: "card_not_configured" }, 503);
  }
  const status = method === "card" ? "awaiting_receipt" : "awaiting_payment";
  const topup = await env.DB.prepare("INSERT INTO wallet_topups(user_id,amount_toman,status) VALUES(?,?,?) RETURNING id").bind(userId, amount, status).first();
  if (!topup) return json({ ok: false, error: "topup_create_failed" }, 500);
  if (method === "card") {
    await env.DB.prepare("INSERT OR IGNORE INTO payments(user_id,provider,provider_payment_id,amount_toman,status,receipt_type) VALUES(?,'card_transfer',?,?,'awaiting_receipt','photo')").bind(userId, "topup:" + topup.id, amount).run();
    await telegram(env, "sendMessage", { chat_id: user.id, text: "\u0628\u0631\u0627\u06CC \u062A\u06A9\u0645\u06CC\u0644 \u0627\u0641\u0632\u0627\u06CC\u0634 \u0627\u0639\u062A\u0628\u0627\u0631\u060C \u0645\u0628\u0644\u063A \u0631\u0627 \u0628\u0647 \u06A9\u0627\u0631\u062A \u062F\u0641\u062A\u0631 \u0648\u0627\u0631\u06CC\u0632 \u06A9\u0646\u06CC\u062F \u0648 \u062A\u0635\u0648\u06CC\u0631 \u0631\u0633\u06CC\u062F \u0631\u0627 \u0647\u0645\u06CC\u0646\u200C\u062C\u0627 \u0627\u0631\u0633\u0627\u0644 \u06A9\u0646\u06CC\u062F." }).catch(() => void 0);
  }
  return json({ ok: true, topup_id: topup.id, amount_toman: amount, method });
}
async function createRialitTopupPayment(request, env) {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json().catch(() => null);
  const topupId = Number(body?.topup_id);
  if (!Number.isSafeInteger(topupId) || topupId < 1) return json({ ok: false, error: "invalid_topup" }, 400);
  const userId = await ensureUser(env.DB, user);
  const topup = await env.DB.prepare("SELECT id,amount_toman,status FROM wallet_topups WHERE id = ? AND user_id = ?").bind(topupId, userId).first();
  if (!topup) return json({ ok: false, error: "topup_not_found" }, 404);
  if (!["awaiting_payment", "payment_link_failed"].includes(String(topup.status))) return json({ ok: false, error: "topup_not_payable" }, 409);
  const amount = Number(topup.amount_toman);
  if (amount < 5e4 || amount > 1e7) return json({ ok: false, error: "rialit_amount_out_of_range" }, 400);
  if (!env.RIALIT_API_KEY) return json({ ok: false, error: "rialit_not_configured" }, 503);
  const previous = await env.DB.prepare("SELECT id,token,provider_order_id,attempt_no,pay_url,payer_amount_toman,payer_fee_toman,status FROM rialit_payments WHERE topup_id = ? AND kind = 'topup' ORDER BY attempt_no DESC LIMIT 1").bind(topupId).first();
  if (previous?.status === "pending" && previous.provider_order_id && previous.pay_url) {
    return json({ ok: true, pay_url: previous.pay_url, payer_amount_toman: previous.payer_amount_toman, payer_fee_toman: previous.payer_fee_toman });
  }
  const attemptNo = previous?.status === "pending" && previous.provider_order_id ? Number(previous.attempt_no) : Number(previous?.attempt_no || 0) + 1;
  const providerOrderId = "mohajer-topup-" + topupId + "-" + attemptNo;
  const apiBase = (env.RIALIT_API_BASE_URL || "https://api.rialit.io/api/v1").replace(/\/$/, "");
  let response;
  try {
    response = await fetch(apiBase + "/send", {
      method: "POST",
      headers: { authorization: "Bearer " + env.RIALIT_API_KEY, "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ amount, order_id: providerOrderId, payer_id: user.id }),
      signal: AbortSignal.timeout(25e3)
    });
  } catch {
    return json({ ok: false, error: "rialit_network_error", retry_same_order: true }, 502);
  }
  const result = await response.json().catch(() => ({}));
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
  if (!matchesRialitFee(amount, payerAmount, payerFee, feePercent)) {
    await env.DB.prepare("INSERT INTO rialit_payments(token,provider_order_id,attempt_no,kind,topup_id,user_id,amount_toman,payer_amount_toman,payer_fee_toman,pay_url,status) VALUES(?,?,?,'topup',?,?,?,?,?,?,'fee_mismatch')").bind(token, providerOrderId, attemptNo, topupId, userId, amount, payerAmount, payerFee, payUrl).run();
    return json({ ok: false, error: "rialit_fee_mismatch", expected_payer_amount_toman: expectedPayerAmount(amount, feePercent) }, 409);
  }
  await env.DB.prepare("INSERT INTO rialit_payments(token,provider_order_id,attempt_no,kind,topup_id,user_id,amount_toman,payer_amount_toman,payer_fee_toman,pay_url,status) VALUES(?,?,?,'topup',?,?,?,?,?,?,'pending')").bind(token, providerOrderId, attemptNo, topupId, userId, amount, payerAmount, payerFee, payUrl).run();
  await env.DB.prepare("UPDATE wallet_topups SET status='awaiting_payment' WHERE id=? AND user_id=?").bind(topupId, userId).run();
  return json({ ok: true, pay_url: payUrl, amount_toman: amount, payer_amount_toman: payerAmount, payer_fee_toman: payerFee, fee_percent: feePercent, fee_configuration_matches: true });
}
async function createCardPayment(request, env) {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  const body = await request.json().catch(() => null);
  const orderId = Number(body?.order_id);
  if (!Number.isSafeInteger(orderId) || orderId < 1) return json({ ok: false, error: "invalid_order" }, 400);
  const userId = await ensureUser(env.DB, user);
  const order = await env.DB.prepare("SELECT id,public_id,amount_toman,price_snapshot_toman,status FROM orders WHERE id=? AND user_id=?").bind(orderId, userId).first();
  if (!order || order.status !== "waiting_payment") return json({ ok: false, error: "order_not_payable" }, 409);
  const amount = Number(order.price_snapshot_toman ?? order.amount_toman ?? 0);
  const card = await env.DB.prepare("SELECT value FROM settings WHERE key='card_number'").first();
  if (!card?.value) return json({ ok: false, error: "card_not_configured" }, 503);
  await env.DB.prepare("INSERT OR IGNORE INTO payments(order_id,user_id,provider,provider_payment_id,amount_toman,status,receipt_type) VALUES(?,?,'card_transfer',?,?,'awaiting_receipt','photo')").bind(orderId, userId, "order:" + order.public_id, amount).run();
  await env.DB.prepare("UPDATE orders SET status='awaiting_receipt',updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?").bind(orderId, userId).run();
  const settings = await env.DB.prepare("SELECT key,value FROM settings WHERE key IN ('card_number','card_holder','card_bank')").all();
  await telegram(env, "sendMessage", { chat_id: user.id, text: "\u0628\u0631\u0627\u06CC \u067E\u0631\u062F\u0627\u062E\u062A \u067E\u0631\u0648\u0646\u062F\u0647\u060C \u0645\u0628\u0644\u063A \u0631\u0627 \u0628\u0647 \u06A9\u0627\u0631\u062A \u062F\u0641\u062A\u0631 \u0648\u0627\u0631\u06CC\u0632 \u06A9\u0646\u06CC\u062F \u0648 \u062A\u0635\u0648\u06CC\u0631 \u0631\u0633\u06CC\u062F \u0631\u0627 \u0647\u0645\u06CC\u0646\u200C\u062C\u0627 \u0627\u0631\u0633\u0627\u0644 \u06A9\u0646\u06CC\u062F." }).catch(() => void 0);
  return json({ ok: true, amount_toman: amount, settings: Object.fromEntries((settings.results || []).map((x) => [x.key, x.value])) });
}
var VPN_BASE_PRICE_PER_GB_TOMAN = 6000;
function gozarbanRoot(env) {
  const root = (env.GOZARBAN_API_ROOT || "https://gozarban.com").replace(/\/$/, "");
  if (!root.startsWith("https://")) throw new Error("gozarban_invalid_api_root");
  return root;
}
async function getGozarbanPlan(env) {
  if (!env.API_VPN) throw new Error("gozarban_api_not_configured");
  const response = await fetch(gozarbanRoot(env) + "/api/user/plans/active", { headers: { authorization: "Bearer " + env.API_VPN, accept: "application/json" }, signal: AbortSignal.timeout(12e3) });
  if (!response.ok) throw new Error("gozarban_plans_http_" + response.status);
  const payload = await response.json();
  const lists = [payload?.plans, payload?.data?.plans, payload?.result?.plans, payload?.data, payload?.result, payload?.items];
  const plans = lists.find((x) => Array.isArray(x));
  if (!plans?.length) throw new Error("gozarban_no_active_plans");
  const configured = Number(env.GOZARBAN_PLAN_ID || 0);
  const candidates = plans.filter((p) => p && p.is_active !== false && p.active !== false && p.enabled !== false);
  const selected = configured ? candidates.find((p) => Number(p.id ?? p.plan_id) === configured) : candidates.find((p) => Number.isSafeInteger(Number(p.id ?? p.plan_id)));
  const id = Number(selected?.id ?? selected?.plan_id);
  if (!Number.isSafeInteger(id) || id < 1) throw new Error("gozarban_plan_id_not_found");
  return { id, name: String(selected?.name || selected?.title || "\u067E\u0644\u0646 \u0641\u0639\u0627\u0644") };
}
function getGozarbanSubscriptionUrl(payload) {
  const objects = [payload, payload?.data, payload?.subscription, payload?.data?.subscription, payload?.result];
  for (const item of objects) {
    if (!item || typeof item !== "object") continue;
    for (const key of ["subscription_url", "subscription_link", "url", "link"]) {
      const value = item[key];
      if (typeof value === "string" && /^(https:\/\/|vless:\/\/|vmess:\/\/|trojan:\/\/|ss:\/\/)/i.test(value)) return value;
    }
    const links = item?.external_data?.links;
    if (Array.isArray(links)) {
      const valid = links.filter((x) => typeof x === "string" && /^(https:\/\/|vless:\/\/|vmess:\/\/|trojan:\/\/|ss:\/\/)/i.test(x));
      if (valid.length) return valid.join("\n");
    }
  }
  return null;
}
async function provisionVpnPayment(env, paymentId) {
  const job = await env.DB.prepare("SELECT j.*,rp.id AS payment_id,rp.status AS payment_status FROM vpn_provisioning_jobs j JOIN rialit_payments rp ON rp.id=j.rialit_payment_id WHERE j.rialit_payment_id=?").bind(paymentId).first();
  if (!job || job.payment_status !== "paid" || !env.API_VPN) return;
  await env.DB.prepare("UPDATE vpn_provisioning_jobs SET status='processing',attempts=attempts+1,updated_at=CURRENT_TIMESTAMP WHERE rialit_payment_id=? AND status IN ('pending','failed','blocked_waiting_api_schema')").bind(paymentId).run();
  const username = "nyvpn" + job.telegram_user_id + "_" + paymentId;
  try {
    const plan = await getGozarbanPlan(env);
    const root = gozarbanRoot(env);
    const headers = { authorization: "Bearer " + env.API_VPN, accept: "application/json" };
    let existing = null;
    const lookup = await fetch(root + "/api/user/subscriptions?search=" + encodeURIComponent(username) + "&skip=0&limit=10", { headers, signal: AbortSignal.timeout(15e3) });
    if (lookup.ok) {
      const data = await lookup.json();
      const rows = Array.isArray(data?.subscriptions) ? data.subscriptions : Array.isArray(data?.data?.subscriptions) ? data.data.subscriptions : [];
      existing = rows.find((x) => x?.marzban_username === username || x?.display_name === username || x?.username === username) || null;
    } else if (lookup.status !== 404) throw new Error("gozarban_lookup_http_" + lookup.status);
    let created = existing;
    if (!created) {
      const response = await fetch(root + "/api/user/subscription/create", { method: "POST", headers: { ...headers, "content-type": "application/json" }, body: JSON.stringify({ data_size_gb: String(job.gigabytes), expire_days: String(Number(job.months) * 30), plan_id: plan.id, username }), signal: AbortSignal.timeout(25e3) });
      const payload = await response.json().catch(() => ({}));
      if (![200, 201].includes(response.status)) throw new Error("gozarban_create_http_" + response.status);
      created = payload?.subscription || payload?.data?.subscription || payload?.data || payload;
    }
    const subscriptionId = created?.id ?? created?.subscription_id ?? null;
    const link = getGozarbanSubscriptionUrl(created);
    if (!subscriptionId && !link) throw new Error("gozarban_response_missing_subscription");
    await env.DB.prepare("UPDATE vpn_provisioning_jobs SET status='completed',provider_subscription_id=?,subscription_url=?,last_error=NULL,updated_at=CURRENT_TIMESTAMP WHERE rialit_payment_id=?").bind(subscriptionId == null ? null : String(subscriptionId), link, paymentId).run();
    const message = "\u2705 \u067E\u0631\u062F\u0627\u062E\u062A VPN \u062A\u0623\u06CC\u06CC\u062F \u0648 \u0627\u0634\u062A\u0631\u0627\u06A9 \u0634\u0645\u0627 \u0633\u0627\u062E\u062A\u0647 \u0634\u062F.\n\n\u062D\u062C\u0645: " + job.gigabytes + " \u06AF\u06CC\u06AF\u0627\u0628\u0627\u06CC\u062A\n\u0645\u062F\u062A: " + job.months + " \u0645\u0627\u0647\n" + (link ? "\u0644\u06CC\u0646\u06A9 \u0627\u0634\u062A\u0631\u0627\u06A9 \u0634\u0645\u0627:\n" + link : "\u0634\u0646\u0627\u0633\u0647 \u0627\u0634\u062A\u0631\u0627\u06A9: " + String(subscriptionId) + "\n\u0628\u0631\u0627\u06CC \u062F\u0631\u06CC\u0627\u0641\u062A \u0644\u06CC\u0646\u06A9 \u0628\u0627 \u067E\u0634\u062A\u06CC\u0628\u0627\u0646\u06CC \u062A\u0645\u0627\u0633 \u0628\u06AF\u06CC\u0631\u06CC\u062F.");
    await telegram(env, "sendMessage", { chat_id: job.telegram_user_id, text: message, disable_web_page_preview: true }).catch(() => void 0);
  } catch (error) {
    const reason = error instanceof Error ? error.message : "gozarban_unknown_error";
    await env.DB.prepare("UPDATE vpn_provisioning_jobs SET status='failed',last_error=?,updated_at=CURRENT_TIMESTAMP WHERE rialit_payment_id=?").bind(reason.slice(0, 200), paymentId).run();
    await telegram(env, "sendMessage", { chat_id: job.telegram_user_id, text: "\u26A0\uFE0F \u067E\u0631\u062F\u0627\u062E\u062A VPN \u062A\u0623\u06CC\u06CC\u062F \u0634\u062F\u0647\u060C \u0627\u0645\u0627 \u0633\u0627\u062E\u062A \u0627\u0634\u062A\u0631\u0627\u06A9 \u062F\u0631 \u067E\u0646\u0644 \u06AF\u0630\u0631\u0628\u0627\u0646 \u0646\u0627\u0645\u0648\u0641\u0642 \u0628\u0648\u062F. \u0633\u0641\u0627\u0631\u0634 \u0634\u0645\u0627 \u0645\u062D\u0641\u0648\u0638 \u0627\u0633\u062A \u0648 \u0628\u0631\u0627\u06CC \u0628\u0631\u0631\u0633\u06CC \u0628\u0647 \u067E\u0634\u062A\u06CC\u0628\u0627\u0646\u06CC \u0627\u0637\u0644\u0627\u0639 \u062F\u0627\u062F\u0647 \u0634\u062F." }).catch(() => void 0);
  }
}
async function checkVpnApi(request, env) {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  if (!env.API_VPN) return json({ ok: false, error: "vpn_payment_not_configured" }, 503);
  try {
    const plan = await getGozarbanPlan(env);
    return json({ ok: true, connected: true, plan_name: plan.name, plan_id: plan.id, base_price_per_gb_toman: VPN_BASE_PRICE_PER_GB_TOMAN, fee_percent: Number(env.PAYMENT_FEE_PERCENT || "12"), rialit_configured: Boolean(env.RIALIT_API_KEY) });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "gozarban_unavailable";
    return json({ ok: false, error: "gozarban_not_ready", detail }, 503);
  }
}
async function createVpnPayment(request, env) {
  const user = await miniAppUser(request, env);
  if (!user) return json({ ok: false, error: "unauthorized" }, 401);
  if (!env.RIALIT_API_KEY || !env.API_VPN) return json({ ok: false, error: "vpn_payment_not_configured" }, 503);
  const body = await request.json().catch(() => null);
  const months = Number(body?.months), gigabytes = Number(body?.gigabytes), requestId = String(body?.request_id || "");
  if (![1, 2, 3, 4].includes(months) || !Number.isSafeInteger(gigabytes) || gigabytes < 10 || gigabytes > 100 || gigabytes % 10 !== 0 || !/^[0-9a-f-]{36}$/i.test(requestId)) return json({ ok: false, error: "invalid_vpn_selection" }, 400);
  try {
    await getGozarbanPlan(env);
  } catch (error) {
    const reason = error instanceof Error ? error.message : "gozarban_unavailable";
    return json({ ok: false, error: "gozarban_not_ready", detail: reason }, 503);
  }
  const userId = await ensureUser(env.DB, user);
  const amount = VPN_BASE_PRICE_PER_GB_TOMAN * gigabytes;
  if (amount < 5e4 || amount > 1e7) return json({ ok: false, error: "rialit_amount_out_of_range" }, 400);
  const providerOrderId = "mohajer-vpn-" + user.id + "-" + requestId;
  const previous = await env.DB.prepare("SELECT id,provider_order_id,token,pay_url,payer_amount_toman,payer_fee_toman,status,attempt_no FROM rialit_payments WHERE provider_order_id=? OR provider_order_id LIKE ? ORDER BY attempt_no DESC LIMIT 1").bind(providerOrderId, providerOrderId + "-%").first();
  if (previous?.status === "pending" && previous.pay_url) return json({ ok: true, pay_url: previous.pay_url, amount_toman: amount, payer_amount_toman: previous.payer_amount_toman, payer_fee_toman: previous.payer_fee_toman, fee_percent: 12 });
  if (previous && previous.status === "paid") return json({ ok: false, error: "vpn_payment_already_paid" }, 409);
  const attemptNo = previous ? Number(previous.attempt_no || 1) + (previous.status === "pending" ? 0 : 1) : 1;
  const stableOrderId = previous?.status === "pending" ? String(previous.provider_order_id) : attemptNo === 1 ? providerOrderId : providerOrderId + "-" + attemptNo;
  if (!previous || previous.status !== "pending") await env.DB.prepare("INSERT INTO rialit_payments(provider_order_id,attempt_no,kind,user_id,amount_toman,vpn_months,vpn_gigabytes,status) VALUES(?,?,'vpn',?,?,?,?,'pending')").bind(stableOrderId, attemptNo, userId, amount, months, gigabytes).run();
  let response;
  try {
    response = await fetch((env.RIALIT_API_BASE_URL || "https://api.rialit.io/api/v1").replace(/\/$/, "") + "/send", { method: "POST", headers: { authorization: "Bearer " + env.RIALIT_API_KEY, "content-type": "application/json", accept: "application/json" }, body: JSON.stringify({ amount, order_id: stableOrderId, payer_id: user.id }), signal: AbortSignal.timeout(25e3) });
  } catch {
    return json({ ok: false, error: "rialit_network_error", retry_same_order: true }, 502);
  }
  const result = await response.json().catch(() => ({}));
  if (![200, 201].includes(response.status)) return json({ ok: false, error: response.status === 403 ? "rialit_outbound_ip_not_allowed" : response.status === 401 ? "rialit_key_invalid" : "rialit_request_failed" }, 502);
  const token = String(result?.token || ""), payerAmount = Number(result?.payer_amount), payerFee = Number(result?.payer_fee);
  if (!/^[A-Za-z0-9]{1,64}$/.test(token) || !Number.isSafeInteger(payerAmount) || !Number.isSafeInteger(payerFee) || Number(result?.amount) !== amount) return json({ ok: false, error: "rialit_invalid_response" }, 502);
  const feePercent = Number(env.PAYMENT_FEE_PERCENT || "12"), payUrl = "https://pay.rialit.io/v1/" + token;
  if (!matchesRialitFee(amount, payerAmount, payerFee, feePercent)) {
    await env.DB.prepare("UPDATE rialit_payments SET token=?,pay_url=?,payer_amount_toman=?,payer_fee_toman=?,status='fee_mismatch' WHERE provider_order_id=?").bind(token, payUrl, payerAmount, payerFee, stableOrderId).run();
    return json({ ok: false, error: "rialit_fee_mismatch", expected_payer_amount_toman: expectedPayerAmount(amount, feePercent) }, 409);
  }
  await env.DB.prepare("UPDATE rialit_payments SET token=?,pay_url=?,payer_amount_toman=?,payer_fee_toman=? WHERE provider_order_id=? AND status='pending'").bind(token, payUrl, payerAmount, payerFee, stableOrderId).run();
  return json({ ok: true, pay_url: payUrl, amount_toman: amount, payer_amount_toman: payerAmount, payer_fee_toman: payerFee, fee_percent: feePercent });
}
async function handleRialitWebhook(request, env, ctx) {
  const allowed = new Set((env.RIALIT_WEBHOOK_IPS || "").split(",").map((x) => x.trim()).filter(Boolean));
  const sourceIp = request.headers.get("cf-connecting-ip") || "";
  if (!sourceIp || !allowed.has(sourceIp)) return json({ ok: false, error: "source_ip_not_allowed" }, 403);
  const eventHeader = request.headers.get("x-rialit-event") || "";
  const deliveryHeader = request.headers.get("x-rialit-delivery") || "";
  const payload = await request.json().catch(() => null);
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
  const duplicate = await env.DB.prepare("SELECT event_id FROM rialit_webhook_events WHERE event_id = ?").bind(eventId).first();
  if (duplicate) return json({ ok: true, duplicate: true });
  const payment = await env.DB.prepare(
    "SELECT rp.*, u.telegram_id AS user_telegram_id FROM rialit_payments rp JOIN users u ON u.id = rp.user_id WHERE rp.token = ?"
  ).bind(token).first();
  if (!payment) return json({ ok: true, ignored: true });
  let verifiedResponse;
  try {
    verifiedResponse = await fetch(
      `${(env.RIALIT_API_BASE_URL || "https://api.rialit.io/api/v1").replace(/\/$/, "")}/status/${token}`,
      {
        headers: { authorization: `Bearer ${env.RIALIT_API_KEY}`, accept: "application/json" },
        signal: AbortSignal.timeout(8e3)
      }
    );
  } catch {
    return json({ ok: false, error: "rialit_verification_unavailable" }, 503);
  }
  if (!verifiedResponse.ok) return json({ ok: false, error: "rialit_verification_unavailable" }, 503);
  const verified = await verifiedResponse.json().catch(() => ({}));
  const status = String(verified?.status || verified?.data?.status || "");
  const verifiedAmount = Number(verified?.amount ?? verified?.data?.amount);
  const verifiedPayer = Number(verified?.payer_id ?? verified?.data?.payer_id);
  const verifiedOrderId = String(verified?.order_id ?? verified?.data?.order_id ?? "");
  const verifiedPayerAmount = Number(verified?.payer_amount ?? verified?.data?.payer_amount);
  const verifiedPayerFee = Number(verified?.payer_fee ?? verified?.data?.payer_fee);
  if (status === "paid" && (verifiedAmount !== Number(payment.amount_toman) || verifiedPayer !== Number(payment.user_telegram_id) || verifiedOrderId !== payment.provider_order_id || verifiedPayerAmount !== Number(payment.payer_amount_toman) || verifiedPayerFee !== Number(payment.payer_fee_toman))) {
    await env.DB.prepare(
      "INSERT OR IGNORE INTO rialit_webhook_events(event_id,event_type,payment_token,processed_at) VALUES(?,?,?,CURRENT_TIMESTAMP)"
    ).bind(eventId, eventType, token).run();
    return json({ ok: true, rejected: "payment_details_mismatch" });
  }
  if (!["pending", "paid", "expired", "cancelled"].includes(status)) {
    return json({ ok: false, error: "unknown_verified_status" }, 503);
  }
  const statements = [
    env.DB.prepare("INSERT OR IGNORE INTO rialit_webhook_events(event_id,event_type,payment_token,processed_at) VALUES(?,?,?,CURRENT_TIMESTAMP)").bind(eventId, eventType, token),
    env.DB.prepare("UPDATE rialit_payments SET status = ?, paid_at = CASE WHEN ? = 'paid' THEN CURRENT_TIMESTAMP ELSE paid_at END WHERE id = ? AND changes() = 1 AND status != 'paid'").bind(status, status, payment.id)
  ];
  if (status === "paid" && payment.kind === "order" && payment.order_id) {
    statements.push(
      env.DB.prepare("UPDATE orders SET status = 'payment_approved', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status IN ('waiting_payment','waiting_receipt_review') AND changes() = 1").bind(payment.order_id),
      env.DB.prepare("INSERT OR IGNORE INTO payments(order_id,user_id,provider,provider_payment_id,amount_toman,receipt_file_id,receipt_type,status,verified_at,provider_metadata_json,source_rialit_payment_id) SELECT ?,?,'rialit',?,?,NULL,'rialit','approved',CURRENT_TIMESTAMP,?,? WHERE changes() = 1").bind(payment.order_id, payment.user_id, payment.token, payment.amount_toman, JSON.stringify({ payer_amount_toman: payment.payer_amount_toman, payer_fee_toman: payment.payer_fee_toman }), payment.id)
    );
  }
  if (status === "paid" && payment.kind === "topup" && payment.topup_id) {
    statements.push(
      env.DB.prepare("UPDATE wallet_topups SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP WHERE id = ? AND status IN ('awaiting_payment','awaiting_receipt','waiting_receipt_review') AND changes() = 1").bind(payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO wallets(user_id,balance_toman) SELECT user_id,0 FROM wallet_topups WHERE id = ? AND status = 'approved'").bind(payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO wallet_credit_events(source_key) SELECT 'rialit:' || ? WHERE EXISTS (SELECT 1 FROM wallet_topups WHERE id = ? AND status = 'approved') AND NOT EXISTS (SELECT 1 FROM wallet_credit_events WHERE source_key = 'rialit:' || ?) AND NOT EXISTS (SELECT 1 FROM wallet_transactions WHERE topup_id = ?)").bind(payment.id, payment.topup_id, payment.id, payment.topup_id),
      env.DB.prepare("UPDATE wallets SET balance_toman = balance_toman + ? WHERE user_id = (SELECT user_id FROM wallet_topups WHERE id = ?) AND changes() = 1").bind(payment.amount_toman, payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO wallet_transactions(user_id,amount_toman,balance_after_toman,kind,description,topup_id,source_rialit_payment_id) SELECT w.user_id,?,w.balance_toman,'topup',?, ?, ? FROM wallets w JOIN wallet_topups t ON t.user_id = w.user_id WHERE t.id = ? AND changes() = 1").bind(payment.amount_toman, `\u0627\u0641\u0632\u0627\u06CC\u0634 \u0627\u0639\u062A\u0628\u0627\u0631 \u0631\u06CC\u0627\u0644\u062A #${payment.topup_id}`, payment.topup_id, payment.id, payment.topup_id),
      env.DB.prepare("INSERT OR IGNORE INTO payments(user_id,provider,provider_payment_id,amount_toman,receipt_type,status,verified_at,provider_metadata_json,source_rialit_payment_id) SELECT ?, 'rialit', ?, ?, 'online', 'approved', CURRENT_TIMESTAMP, ?, ? WHERE EXISTS (SELECT 1 FROM wallet_topups WHERE id=? AND status='approved')").bind(payment.user_id, payment.token, payment.amount_toman, JSON.stringify({ payer_amount_toman: payment.payer_amount_toman, payer_fee_toman: payment.payer_fee_toman }), payment.id, payment.topup_id)
    );
  }
  await env.DB.batch(statements);
  if (status === "paid" && payment.kind === "vpn") {
    await env.DB.prepare("INSERT OR IGNORE INTO vpn_provisioning_jobs(rialit_payment_id,telegram_user_id,months,gigabytes,status) VALUES(?,?,?,?,'pending')").bind(payment.id, Number(payment.user_telegram_id), Number(payment.vpn_months || 0), Number(payment.vpn_gigabytes || 0)).run();
    ctx.waitUntil(provisionVpnPayment(env, payment.id));
  }
  if (status === "paid" && payment.kind !== "vpn") {
    ctx.waitUntil(telegram(env, "sendMessage", { chat_id: payment.user_telegram_id, text: "\u2705 \u067E\u0631\u062F\u0627\u062E\u062A \u0634\u0645\u0627 \u062A\u0648\u0633\u0637 \u0631\u06CC\u0627\u0644\u062A\u200C\u067E\u06CC \u062A\u0623\u06CC\u06CC\u062F \u0634\u062F. \u0628\u0631\u0627\u06CC \u0645\u0634\u0627\u0647\u062F\u0647 \u0648\u0636\u0639\u06CC\u062A \u067E\u0631\u0648\u0646\u062F\u0647\u060C \u0645\u06CC\u0646\u06CC\u200C\u0627\u067E \u0631\u0627 \u0628\u0627\u0632 \u06A9\u0646\u06CC\u062F." }).catch(() => void 0));
  }
  return json({ ok: true, action: status });
}
var IMPORTABLE_COLUMNS = {
  users: ["id", "telegram_id", "first_name", "last_name", "username", "created_at", "updated_at"],
  services: ["id", "code", "name", "price_toman", "enabled", "description"],
  orders: ["id", "public_id", "user_id", "service_id", "price_snapshot_toman", "status", "data_json", "created_at", "updated_at"],
  payments: ["id", "order_id", "amount_toman", "receipt_file_id", "receipt_type", "status", "source_rialit_payment_id", "created_at"],
  variza_payments: ["id", "slug", "kind", "order_id", "topup_id", "user_id", "amount_toman", "pay_url", "status", "attempt_code", "expires_at", "created_at", "paid_at"],
  rialit_payments: ["id", "token", "provider_order_id", "attempt_no", "kind", "order_id", "topup_id", "user_id", "amount_toman", "payer_amount_toman", "payer_fee_toman", "vpn_months", "vpn_gigabytes", "pay_url", "status", "created_at", "paid_at", "delivered_at"],
  wallets: ["id", "user_id", "balance_toman", "created_at", "updated_at"],
  wallet_transactions: ["id", "user_id", "amount_toman", "balance_after_toman", "kind", "description", "order_id", "topup_id", "source_rialit_payment_id", "created_at"],
  wallet_topups: ["id", "user_id", "amount_toman", "receipt_file_id", "receipt_type", "status", "created_at", "reviewed_at"],
  discount_codes: ["id", "code", "kind", "value", "active", "max_uses", "used_count", "expires_at", "created_at"],
  documents: ["id", "order_id", "document_type", "telegram_file_id", "review_status", "reviewed_by_telegram_id", "reviewed_at", "created_at"],
  tickets: ["id", "order_id", "status", "created_at", "updated_at"],
  ticket_messages: ["id", "ticket_id", "sender_type", "sender_telegram_id", "content_type", "text", "file_id", "created_at"],
  settings: ["id", "key", "value"],
  audit_logs: ["id", "actor_telegram_id", "action", "order_id", "details_json", "created_at"],
  companions: ["id", "order_id", "full_name", "mobile", "created_at"],
  operators: ["id", "telegram_id", "display_name", "role", "permissions_json", "active", "created_at", "updated_at"]
};
function authorizedMigration(request, env) {
  const secret = env.MIGRATION_SECRET || "";
  return Boolean(secret) && request.headers.get("authorization") === "Bearer " + secret;
}
async function handleMigrationImport(request, env) {
  if (!authorizedMigration(request, env)) return text("forbidden", 403);
  const body = await request.json().catch(() => null);
  const table = String(body?.table || "");
  const columns = body?.columns;
  const rows = body?.rows;
  const batchId = String(body?.batch_id || "");
  const checksum = String(body?.checksum || "");
  if (!IMPORTABLE_COLUMNS[table] || !Array.isArray(columns) || !Array.isArray(rows) || rows.length > 100 || !batchId || batchId.length > 160 || !checksum || columns.length < 1 || columns.length > 32 || columns.some((c) => typeof c !== "string" || !IMPORTABLE_COLUMNS[table].includes(c)) || new Set(columns).size !== columns.length || rows.some((r) => !Array.isArray(r) || r.length !== columns.length)) {
    return json({ ok: false, error: "invalid_import_batch" }, 400);
  }
  const prior = await env.DB.prepare("SELECT batch_id FROM migration_batches WHERE batch_id = ?").bind(batchId).first();
  if (prior) return json({ ok: true, duplicate: true });
  const placeholders = columns.map(() => "?").join(",");
  const columnSql = columns.map((c) => '"' + c + '"').join(",");
  const insertSql = 'INSERT OR IGNORE INTO "' + table + '" (' + columnSql + ") VALUES (" + placeholders + ")";
  const statements = rows.map(
    (row) => env.DB.prepare(insertSql).bind(...row)
  );
  statements.push(env.DB.prepare(
    "INSERT OR IGNORE INTO migration_batches(batch_id,table_name,row_count,checksum) VALUES(?,?,?,?)"
  ).bind(batchId, table, rows.length, checksum));
  await env.DB.batch(statements);
  return json({ ok: true, table, imported_rows: rows.length, batch_id: batchId });
}
async function handleMigrationManifest(request, env) {
  if (!authorizedMigration(request, env)) return text("forbidden", 403);
  const body = await request.json().catch(() => null);
  if (!body || typeof body !== "object" || !body.table_counts || typeof body.table_counts !== "object") {
    return json({ ok: false, error: "invalid_manifest" }, 400);
  }
  await env.DB.prepare(
    "INSERT OR REPLACE INTO migration_manifest(id,manifest_json,created_at) VALUES(1,?,CURRENT_TIMESTAMP)"
  ).bind(JSON.stringify(body)).run();
  return json({ ok: true });
}
async function handleMigrationStatus(request, env) {
  if (!authorizedMigration(request, env)) return text("forbidden", 403);
  const counts = {};
  for (const table of Object.keys(IMPORTABLE_COLUMNS)) {
    const row = await env.DB.prepare('SELECT COUNT(*) AS n FROM "' + table + '"').first();
    counts[table] = Number(row?.n || 0);
  }
  const manifest = await env.DB.prepare("SELECT manifest_json FROM migration_manifest WHERE id = 1").first();
  const batches = await env.DB.prepare("SELECT COUNT(*) AS n FROM migration_batches").first();
  return json({ ok: true, table_counts: counts, batch_count: Number(batches?.n || 0), manifest: manifest?.manifest_json ? JSON.parse(manifest.manifest_json) : null });
}
var index_default = {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname !== "/webhooks/telegram") ctx.waitUntil(ensureTelegramWebhook(env, url.origin));
    if (url.pathname === "/health") return json({ ok: true, service: "help-yar-mohajer", platform: "cloudflare-workers" });
    if (url.pathname === "/internal/import" && request.method === "POST") return handleMigrationImport(request, env);
    if (url.pathname === "/internal/manifest" && request.method === "POST") return handleMigrationManifest(request, env);
    if (url.pathname === "/internal/status" && request.method === "GET") return handleMigrationStatus(request, env);
    if (url.pathname === "/webhooks/telegram" && request.method === "POST") return handleTelegram(request, env);
    if (url.pathname === "/webhooks/rialit" && request.method === "POST") return handleRialitWebhook(request, env, ctx);
    if (url.pathname === "/api/miniapp/bootstrap" && request.method === "GET") return bootstrap(request, env);
    if (url.pathname === "/api/miniapp/orders" && request.method === "POST") return createOrder(request, env);
    if (url.pathname === "/api/miniapp/payments/rialit" && request.method === "POST") return createRialitPayment(request, env);
    if (url.pathname === "/api/miniapp/vpn/status" && request.method === "GET") return checkVpnApi(request, env);
    if (url.pathname === "/api/miniapp/vpn/pay" && request.method === "POST") return createVpnPayment(request, env);
    if (url.pathname === "/api/miniapp/payments/card" && request.method === "POST") return createCardPayment(request, env);
    if (url.pathname === "/api/miniapp/topups" && request.method === "POST") return createWalletTopup(request, env);
    if (url.pathname === "/api/miniapp/topups/rialit" && request.method === "POST") return createRialitTopupPayment(request, env);
    if (url.pathname === "/app" || url.pathname === "/app/") {
      return new Response(MINIAPP_HTML, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });
    }
    if (url.pathname === "/app.js") return new Response(MINIAPP_JS, { headers: { "content-type": "application/javascript; charset=utf-8", "cache-control": "no-store" } });
    if (url.pathname.startsWith("/api/")) return json({ ok: false, error: "not_found" }, 404);
    return text("not found", 404);
  }
};
export {
  index_default as default
};
