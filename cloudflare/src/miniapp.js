export const MINIAPP_HTML = String.raw`<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#145bd7"><meta name="color-scheme" content="light dark"><title>کمک‌یار مهاجر</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
:root{color-scheme:light;--blue:#145bd7;--navy:#123b78;--bg:#f4f7fc;--ink:#162844;--muted:#73819a;--card:#fff;--surface:#fff;--border:#e8eef7;--line:#edf1f7;--soft:#f5f8ff;--shadow:0 7px 24px #233e6808}
:root[data-theme="dark"]{color-scheme:dark;--blue:#79aaff;--navy:#d5e4ff;--bg:#0b1220;--ink:#edf3ff;--muted:#a4b1c7;--card:#131e30;--surface:#17243a;--border:#293951;--line:#293951;--soft:#16243a;--shadow:0 7px 24px #00000025}
:root[data-theme="dark"] body{background:var(--bg);color:var(--ink)}
:root[data-theme="dark"] .panel,:root[data-theme="dark"] .service{background:var(--card);border-color:var(--border);box-shadow:var(--shadow)}
:root[data-theme="dark"] .tile{border-color:var(--border);box-shadow:var(--shadow);color:var(--ink)}
:root[data-theme="dark"] .t-blue{background:#172b48}:root[data-theme="dark"] .t-blue .ico{background:#24436d}
:root[data-theme="dark"] .t-teal{background:#12332f}:root[data-theme="dark"] .t-teal .ico{background:#1d5149}
:root[data-theme="dark"] .t-orange{background:#39291c}:root[data-theme="dark"] .t-orange .ico{background:#604027}
:root[data-theme="dark"] .t-purple{background:#2b2342}:root[data-theme="dark"] .t-purple .ico{background:#46376c}
:root[data-theme="dark"] .t-pink{background:#3c2230}:root[data-theme="dark"] .t-pink .ico{background:#61334b}
:root[data-theme="dark"] .t-green{background:#233522}:root[data-theme="dark"] .t-green .ico{background:#385533}
:root[data-theme="dark"] .home-intro{background:linear-gradient(135deg,#17243a,#121c2e);border-color:var(--border)}
:root[data-theme="dark"] .home-intro .mark{background:#263d5d}
:root[data-theme="dark"] .service .ico{background:#213550}
:root[data-theme="dark"] .back{background:#1b3558;color:#9dc0ff}
:root[data-theme="dark"] .pill{background:#20395c;color:#b9d4ff}
:root[data-theme="dark"] .line{border-bottom-color:var(--line)}
:root[data-theme="dark"] .admin{background:#302919;border-color:#66512a}
:root[data-theme="dark"] .status{background:#332a18;color:#f6d68b}
:root[data-theme="dark"] .connection-pill{color:#f5f9ff}
:root[data-theme="dark"] .primary{color:#fff}
:root[data-theme="dark"] .foot{color:#8797b0}
:root[data-theme="dark"] .tile small,:root[data-theme="dark"] .service small{color:var(--muted)}
:root[data-theme="dark"] .home-intro .tiny{color:#78ddb0}
.theme-toggle{margin-right:auto;display:inline-flex;align-items:center;justify-content:center;gap:7px;min-height:40px;padding:8px 12px;border:1px solid #ffffff55;border-radius:14px;background:#ffffff18;color:#fff;font-size:12px;font-weight:800;white-space:nowrap;backdrop-filter:blur(8px)}
.theme-toggle:active{transform:scale(.97)}
.theme-toggle .theme-icon{font-size:17px;line-height:1}
@media(max-width:370px){.theme-toggle{padding:8px;gap:5px}.theme-toggle .theme-label{font-size:11px}.logo{width:44px;height:44px;flex:0 0 44px}.top{gap:9px}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font-family:"Vazirmatn","IRANSans","Iranian Sans",Tahoma,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:var(--ink);font-feature-settings:"kern";text-rendering:optimizeLegibility;padding:0 0 calc(22px + env(safe-area-inset-bottom));}button{font:inherit;cursor:pointer;border:0}
.hero{position:relative;overflow:hidden;background:linear-gradient(135deg,#103f91 0%,#145bd7 52%,#4a9bff 100%);color:white;padding:25px 18px 30px;border-radius:0 0 30px 30px;box-shadow:0 14px 34px #174e9b25}.hero:after{content:"";position:absolute;width:190px;height:190px;border-radius:50%;border:1px solid #ffffff20;left:-62px;top:-72px;box-shadow:0 0 0 22px #ffffff08,0 0 0 46px #ffffff06;pointer-events:none}.hero>*{position:relative;z-index:1}.top{display:flex;align-items:center;gap:12px}.logo{width:50px;height:50px;border-radius:17px;background:linear-gradient(145deg,#ffffff38,#ffffff12);display:grid;place-items:center;font-size:26px;border:1px solid #ffffff55;box-shadow:inset 0 1px #ffffff45}.hero h1{font-size:20px;margin:0 0 5px}.hero p{font-size:12px;margin:0;color:#e4efff}.hello{margin-top:24px;font-size:14px}.hello strong{display:block;font-size:21px;margin-top:5px}.wrap{padding:18px 15px;max-width:720px;margin:auto}.section-title{display:flex;align-items:center;justify-content:space-between;margin:5px 2px 12px;font-size:16px;font-weight:800}.section-title small{font-size:11px;color:var(--muted);font-weight:500}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}.tile{min-height:130px;border:1px solid #e8eef7;border-radius:21px;padding:15px;text-align:right;box-shadow:0 6px 20px #233e6809;display:flex;flex-direction:column;align-items:flex-start;gap:9px;transition:transform .12s}.tile:active{transform:scale(.98)}.tile .ico{width:43px;height:43px;border-radius:14px;display:grid;place-items:center;font-size:23px}.tile b{font-size:14px;line-height:1.5}.tile small{font-size:11px;color:var(--muted);line-height:1.5}.t-blue{background:#e7f0ff}.t-blue .ico{background:#c9ddff}.t-teal{background:#e0f8f3}.t-teal .ico{background:#b8eee3}.t-orange{background:#fff0df}.t-orange .ico{background:#ffdbb4}.t-purple{background:#f0eaff}.t-purple .ico{background:#dcd0ff}.t-pink{background:#ffe9f1}.t-pink .ico{background:#ffd0e1}.t-green{background:#e8f7df}.t-green .ico{background:#ccecb9}.wide{grid-column:1/-1;min-height:86px;flex-direction:row;align-items:center}.wide .txt{flex:1}.panel{background:var(--card);border:1px solid #e9eef6;border-radius:21px;padding:18px;margin-top:18px;box-shadow:0 7px 24px #233e6808}.panel h2{font-size:15px;margin:0 0 13px}.line{display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #edf1f7}.line:last-child{border:0}.line .ico{font-size:21px}.line .txt{flex:1;font-size:13px}.line small{display:block;color:var(--muted);font-size:11px;margin-top:4px}.pill{font-size:11px;border-radius:20px;background:#e7f0ff;color:#1456ad;padding:6px 9px}.muted{color:var(--muted);font-size:12px;line-height:1.8}.hidden{display:none!important}.view{display:none}.view.active{display:block}.back{color:var(--blue);background:#e7f0ff;padding:9px 13px;border-radius:12px;font-size:12px;font-weight:700;margin-bottom:14px}.service{display:flex;gap:12px;align-items:center;background:white;padding:14px;border:1px solid #e9eef6;border-radius:18px;margin:10px 0;box-shadow:0 5px 17px #233e6807}.service .ico{font-size:24px;width:44px;height:44px;display:grid;place-items:center;background:#edf4ff;border-radius:14px}.service .txt{flex:1}.service b{font-size:13px}.service small{display:block;color:var(--muted);margin-top:4px;font-size:11px}.primary{background:linear-gradient(135deg,#145bd7,#2e7cf0);color:white;padding:10px 14px;border-radius:13px;font-size:12px;font-weight:800;box-shadow:0 4px 12px #145bd720}.primary:disabled{opacity:.55;box-shadow:none}.admin{border:1px solid #ffdf9b;background:#fff9e9}.status{padding:12px;border-radius:13px;background:#fff3d8;color:#825500;font-size:12px;line-height:1.8;margin-top:12px}.foot{text-align:center;color:#8c9ab0;font-size:10px;padding:22px 10px 12px}.section-title{letter-spacing:-.2px}.tile b,.service b,.panel h2{letter-spacing:-.15px}.connection-pill{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;background:#ffffff1c;border:1px solid #ffffff35;color:#f5f9ff;font-size:11px;font-weight:700;white-space:nowrap}.connection-dot{width:7px;height:7px;border-radius:50%;background:#ffd166;box-shadow:0 0 0 3px #ffd16620}.connection-pill.verified{background:#d8fae91f;border-color:#a8f2c54f}.connection-pill.verified .connection-dot{background:#62e6a0;box-shadow:0 0 0 3px #62e6a022}.connection-pill.failed .connection-dot{background:#ff8d8d;box-shadow:0 0 0 3px #ff8d8d22}.welcome-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:13px}.welcome-chip{font-size:10px;padding:6px 9px;border-radius:10px;background:#ffffff16;border:1px solid #ffffff24;color:#f0f6ff}.home-intro{display:flex;align-items:flex-start;gap:12px;padding:15px;border-radius:19px;background:linear-gradient(135deg,#fff,#f5f8ff);border:1px solid #e6edf8;margin-bottom:18px}.home-intro .mark{width:42px;height:42px;flex:0 0 42px;display:grid;place-items:center;border-radius:14px;background:#e6efff;font-size:22px}.home-intro b{display:block;font-size:13px;margin:1px 0 5px}.home-intro p{font-size:11px;color:var(--muted);line-height:1.8;margin:0}.home-intro .tiny{font-size:10px;color:#1d6b48;margin-top:5px}button:focus-visible{outline:3px solid #70a9ff;outline-offset:3px}.toast{position:fixed;bottom:20px;right:16px;left:16px;background:#17365f;color:white;padding:13px 16px;border-radius:13px;font-size:13px;box-shadow:0 8px 24px #10274a33;z-index:9}
@media(min-width:520px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}.tile.wide{grid-column:span 2}.hero,.wrap{padding-left:24px;padding-right:24px}}

/* Premium night theme: layered navy surfaces, soft blue glow, accessible contrast */
:root[data-theme="dark"] body{
 background:radial-gradient(ellipse at 85% 0%,#17335b 0%,transparent 34%),linear-gradient(180deg,#0a1220 0%,#0d1728 48%,#0a1220 100%);
 color:#edf4ff;
}
:root[data-theme="dark"] .hero{
 background:linear-gradient(135deg,#101f3b 0%,#15386b 48%,#2456a0 100%);
 border-bottom:1px solid #7aaaff26;
 box-shadow:0 18px 42px #02081570,inset 0 -1px #ffffff0b;
}
:root[data-theme="dark"] .hero:after{border-color:#a8caff20;box-shadow:0 0 0 22px #9fc4ff08,0 0 0 46px #9fc4ff05}
:root[data-theme="dark"] .logo{background:linear-gradient(145deg,#ffffff24,#ffffff08);border-color:#a9c9ff45;box-shadow:inset 0 1px #ffffff35,0 7px 20px #02081735}
:root[data-theme="dark"] .theme-toggle{
 background:linear-gradient(135deg,#dceaff20,#83b2ff12);
 border-color:#b8d2ff40;color:#f3f7ff;
 box-shadow:inset 0 1px #ffffff15,0 4px 16px #030b1a25;
}
:root[data-theme="dark"] .theme-toggle:hover{background:#a9c9ff2a;border-color:#c7ddff75}
:root[data-theme="dark"] .wrap{color:var(--ink)}
:root[data-theme="dark"] .tile{
 background:linear-gradient(145deg,#17263c,#111d30);
 border-color:#334963;
 box-shadow:0 10px 24px #02081535,inset 0 1px #ffffff06;
}
:root[data-theme="dark"] .tile:active{background:#1a2d47}
:root[data-theme="dark"] .t-blue{background:linear-gradient(145deg,#172e4c,#13243b)}
:root[data-theme="dark"] .t-teal{background:linear-gradient(145deg,#143832,#102923)}
:root[data-theme="dark"] .t-orange{background:linear-gradient(145deg,#3b2b20,#2a211b)}
:root[data-theme="dark"] .t-purple{background:linear-gradient(145deg,#2b2447,#211d35)}
:root[data-theme="dark"] .t-pink{background:linear-gradient(145deg,#3b2434,#2b1c29)}
:root[data-theme="dark"] .t-green{background:linear-gradient(145deg,#253925,#1b2b1c)}
:root[data-theme="dark"] .tile .ico,:root[data-theme="dark"] .service .ico,:root[data-theme="dark"] .home-intro .mark{
 border:1px solid #ffffff12;box-shadow:inset 0 1px #ffffff0b;
}
:root[data-theme="dark"] .panel,:root[data-theme="dark"] .service{
 background:linear-gradient(145deg,#16243a,#111c2e);
 border-color:#2b3d56;
 box-shadow:0 10px 28px #02081535,inset 0 1px #ffffff08;
}
:root[data-theme="dark"] .home-intro{
 background:linear-gradient(135deg,#172944,#111d30 80%);
 border-color:#314661;box-shadow:0 9px 24px #02081525;
}
:root[data-theme="dark"] .section-title{color:#eaf2ff}
:root[data-theme="dark"] .line{border-bottom-color:#293b53}
:root[data-theme="dark"] .pill{background:#203b61;color:#c5dcff;border:1px solid #3c5a81}
:root[data-theme="dark"] .back{background:linear-gradient(135deg,#1d3b63,#172d4a);color:#c3dcff;border:1px solid #345477}
:root[data-theme="dark"] .primary{
 background:linear-gradient(135deg,#327df0,#205bc0);
 border:1px solid #82b4ff45;box-shadow:0 6px 16px #0b3d8a45,inset 0 1px #ffffff25;
}
:root[data-theme="dark"] .primary:active{filter:brightness(1.12);transform:translateY(1px)}
:root[data-theme="dark"] .admin{background:linear-gradient(135deg,#382e1d,#292319);border-color:#6b5733}
:root[data-theme="dark"] .status{background:linear-gradient(135deg,#3b301b,#2b2519);color:#ffe1a0;border:1px solid #66512c}
:root[data-theme="dark"] .toast{background:linear-gradient(135deg,#1b3558,#13243b);border:1px solid #4b6c94;box-shadow:0 12px 32px #0008}
:root[data-theme="dark"] input,:root[data-theme="dark"] textarea,:root[data-theme="dark"] select{
 background:#0f1a2b;color:#edf4ff;border:1px solid #354b67;border-radius:12px;
}
:root[data-theme="dark"] input::placeholder,:root[data-theme="dark"] textarea::placeholder{color:#8395b0}
:root[data-theme="dark"] button:focus-visible{outline-color:#9bc4ff}
:root[data-theme="dark"] .foot{color:#8395af}
:root[data-theme="dark"] .muted,:root[data-theme="dark"] .tile small,:root[data-theme="dark"] .service small{color:#aabbd2}
:root[data-theme="dark"] .connection-pill{background:#ffffff0b;border-color:#ffffff24}
@media(prefers-reduced-motion:no-preference){
 .tile,.service,.panel,.theme-toggle,.primary{transition:background .22s ease,border-color .22s ease,box-shadow .22s ease,transform .15s ease}
}

</style></head>
<body>
<header class="hero"><div class="top"><div class="logo">🤝</div><div><h1>کمک‌یار مهاجر</h1><p>خدمات دفتر نت‌یار مهاجر</p></div><button id="themeToggle" class="theme-toggle" type="button" aria-label="تغییر به تم شب" aria-pressed="false"><span id="themeIcon" class="theme-icon" aria-hidden="true">🌙</span><span id="themeLabel" class="theme-label">تم شب</span></button></div><div class="hello">به خانوادهٔ کمک‌یار مهاجر خوش آمدید<strong id="userName">مشترک گرامی 🌱</strong><div class="welcome-meta"><span class="welcome-chip">خدمات دفتر نت‌یار مهاجر</span><span class="welcome-chip">سریع · ساده · امن</span></div></div></header>
<main class="wrap">
<section id="home" class="view active">
<div class="section-title">صفحهٔ اصلی <span id="connection" class="connection-pill"><i class="connection-dot"></i><span>در حال تأیید نشست…</span></span></div><div class="home-intro"><span class="mark">✨</span><div><b>از کجا شروع کنیم؟</b><p>خدمت موردنیازتان را انتخاب کنید یا وضعیت درخواست‌های قبلی را ببینید. برای نمایش اطلاعات حساب، ابتدا نشست امن تلگرام تأیید می‌شود.</p><div id="sessionHint" class="tiny">در حال بررسی هویت تلگرام…</div></div></div>
<div class="grid">
<button class="tile t-blue" onclick="openView('services')"><span class="ico">🧾</span><b>خدمات دفتر نت‌یار مهاجر</b><small>ثبت درخواست خدمت</small></button>
<button class="tile t-teal" onclick="openView('wallet')"><span class="ico">💳</span><b>اعتبار من</b><small>موجودی و پرداخت‌ها</small></button>
<button class="tile t-purple" onclick="openView('account')"><span class="ico">👤</span><b>حساب من</b><small>اطلاعات حساب</small></button>
<button class="tile t-orange" onclick="openView('orders')"><span class="ico">📋</span><b>پیگیری درخواست‌ها</b><small>وضعیت پرونده‌ها</small></button>
<button class="tile t-pink" onclick="openView('support')"><span class="ico">💬</span><b>پشتیبانی</b><small>ارتباط با دفتر</small></button>
<button id="adminTile" class="tile t-green hidden" onclick="openView('admin')"><span class="ico">🛡️</span><b>پنل مدیریت</b><small>ویژه مدیران مجاز</small></button>
</div>
<div class="panel"><h2>📌 راهنمای استفاده</h2><div class="muted">خدمت موردنظر را انتخاب کنید، قوانین را بخوانید و فرم را با دقت تکمیل کنید. وضعیت درخواست پس از ثبت و بررسی در همین بخش قابل پیگیری خواهد بود.</div></div>
</section>
<section id="services" class="view"><button class="back" onclick="openView('home')">→ بازگشت به صفحه اصلی</button><div class="section-title">🧾 خدمات دفتر <small>انتخاب خدمت</small></div><div id="serviceList"></div><div class="status">ثبت نهایی درخواست، بارگذاری امن مدارک و پرداخت پس از تکمیل اتصال پایگاه داده فعال می‌شود.</div></section>
<section id="wallet" class="view"><button class="back" onclick="openView('home')">→ بازگشت</button><div class="panel"><h2>💳 اعتبار من</h2><div id="balance" style="font-size:26px;font-weight:800;color:var(--blue)">— تومان</div><p class="muted">موجودی فقط پس از اتصال پایگاه داده نمایش داده می‌شود. تا فعال‌شدن تأیید پرداخت سمت سرور، هیچ پرداختی از این صفحه انجام ندهید.</p></div></section>
<section id="account" class="view"><button class="back" onclick="openView('home')">→ بازگشت</button><div class="panel"><h2>👤 حساب من</h2><div class="line"><span class="txt">نام نمایشی</span><b id="accountName">—</b></div><div class="line"><span class="txt">شناسه تلگرام</span><b id="telegramId">در انتظار تأیید</b></div><p class="muted">اطلاعات از نشست امن تلگرام خوانده می‌شود؛ شناسه ارسالی از سمت مرورگر به‌تنهایی معتبر محسوب نمی‌شود.</p></div></section>
<section id="orders" class="view"><button class="back" onclick="openView('home')">→ بازگشت</button><div class="panel"><h2>📋 پیگیری درخواست‌ها</h2><div id="ordersList" class="muted">برای مشاهده پرونده‌ها باید اتصال پایگاه داده فعال و هویت تلگرام تأیید شده باشد.</div></div></section>
<section id="support" class="view"><button class="back" onclick="openView('home')">→ بازگشت</button><div class="panel"><h2>💬 ارتباط با پشتیبانی</h2><p class="muted">برای پیگیری، کد درخواست خود را آماده داشته باشید.</p><button class="primary" onclick="window.open('https://t.me/NetYar_esf','_blank')">ارتباط با پشتیبانی @NetYar_esf</button></div></section>
<section id="admin" class="view"><button class="back" onclick="openView('home')">→ بازگشت</button><div class="panel admin"><h2>🛡️ پنل مدیریت</h2><p class="muted">این بخش فقط برای شناسه‌هایی نمایش داده می‌شود که سرور در فهرست مدیران مجاز ثبت کرده باشد. ابزارهای بررسی درخواست، رسیدها، تنظیم تعرفه و مدیریت اپراتورها در مرحله بعد به API امن متصل می‌شوند.</p><div class="status">دسترسی مدیریتی در این نسخه فقط نمایشی است؛ هیچ عملیات مدیریتی از این صفحه اجرا نمی‌شود.</div></div></section>
<div class="foot">کمک‌یار مهاجر · دفتر نت‌یار مهاجر</div>
</main><div id="toast" class="toast hidden"></div>
<script>
const tg=window.Telegram?.WebApp;
if(tg){tg.ready();tg.expand();try{tg.setHeaderColor('#1769e0');tg.setBackgroundColor('#f3f7ff')}catch{}}
const $=id=>document.getElementById(id);
const themeButton=$('themeToggle'),themeIcon=$('themeIcon'),themeLabel=$('themeLabel');
function applyTheme(theme,save=true){
 const dark=theme==='dark';
 document.documentElement.dataset.theme=dark?'dark':'light';
 document.documentElement.style.colorScheme=dark?'dark':'light';
 const meta=document.querySelector('meta[name="theme-color"]');
 if(meta)meta.content=dark?'#0b1220':'#145bd7';
 if(themeIcon)themeIcon.textContent=dark?'☀️':'🌙';
 if(themeLabel)themeLabel.textContent=dark?'تم روز':'تم شب';
 if(themeButton){themeButton.setAttribute('aria-pressed',String(dark));themeButton.setAttribute('aria-label',dark?'تغییر به تم روز':'تغییر به تم شب');}
 try{if(save)localStorage.setItem('netyar-miniapp-theme',dark?'dark':'light')}catch{}
 try{if(tg){tg.setHeaderColor(dark?'#0b1220':'#145bd7');tg.setBackgroundColor(dark?'#0b1220':'#f4f7fc')}}catch{}
}
let initialTheme='light';
try{initialTheme=localStorage.getItem('netyar-miniapp-theme')||'light'}catch{}
applyTheme(initialTheme,false);
themeButton?.addEventListener('click',()=>applyTheme(document.documentElement.dataset.theme==='dark'?'light':'dark'));

const staticServices=[
{code:'identity',name:'تثبیت هویت',desc:'بررسی مدارک و درخواست تثبیت هویت',icon:'🪪'},
{code:'khodnevis',name:'کد رهگیری خودنویس',desc:'ثبت درخواست دریافت کد رهگیری',icon:'📝'},
{code:'fida',name:'ثبت‌نام کد فیدا غیرحضوری',desc:'ثبت اطلاعات برای دریافت کد فیدا',icon:'🪪'},
{code:'dolatman_login',name:'رفع مشکل ورود به درگاه دولت من',desc:'بررسی مشکل ورود و دسترسی',icon:'🔐'},
{code:'student_screening',name:'آزمون غربالگری دانش‌آموزان',desc:'ثبت اطلاعات دانش‌آموز',icon:'🎒'},
{code:'other_service',name:'درخواست خدمات دیگر',desc:'شرح خدمت موردنیاز',icon:'🧾'}
];
function openView(id){document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===id));if(tg)tg.BackButton.isVisible=id!=='home';window.scrollTo(0,0)}
if(tg){tg.BackButton.onClick(()=>{const active=document.querySelector('.view.active');openView(active?.id==='home'?'home':'home')})}
function toast(text){$('toast').textContent=text;$('toast').classList.remove('hidden');setTimeout(()=>$('toast').classList.add('hidden'),3600)}
function setSessionStatus(state,label,hint){const el=$('connection');el.classList.remove('verified','failed');if(state==='verified')el.classList.add('verified');if(state==='failed')el.classList.add('failed');el.innerHTML='<i class="connection-dot"></i><span></span>';el.querySelector('span').textContent=label;$('sessionHint').textContent=hint;}
function renderServices(services){$('serviceList').innerHTML='';services.forEach((s,i)=>{const icons={identity:'🪪',khodnevis:'📝',fida:'🪪',dolatman_login:'🔐',student_screening:'🎒',other_service:'🧾'};const el=document.createElement('div');el.className='service';const ico=document.createElement('span');ico.className='ico';ico.textContent=icons[s.code]||'📄';const txt=document.createElement('div');txt.className='txt';const name=document.createElement('b');name.textContent=s.name;const desc=document.createElement('small');desc.textContent=s.description||s.desc||'برای ثبت درخواست انتخاب کنید';txt.append(name,desc);const button=document.createElement('button');button.className='primary';button.textContent='انتخاب';button.onclick=async()=>{if(!tg?.initData){toast('برای انتخاب خدمت، مینی‌اپ را از داخل تلگرام باز کنید.');return}button.disabled=true;try{const r=await fetch('/api/miniapp/select-service',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({initData:tg.initData,code:s.code})});const d=await r.json();if(r.ok&&d.ok){toast('پیام قوانین به گفت‌وگوی ربات ارسال شد. برای ادامه به ربات برگردید.')}else if(d.error==='service_not_ready'){toast('این خدمت هنوز فعال نشده؛ تعرفه و قوانین باید تأیید شوند.')}else{toast('انتخاب خدمت انجام نشد؛ لطفاً دوباره تلاش کنید.')}}catch{toast('ارتباط با سرور برقرار نشد.')}finally{button.disabled=false}};el.append(ico,txt,button);$('serviceList').append(el)})}
renderServices(staticServices);
async function boot(){
 const initData=tg?.initData||'';
 if(!initData){setSessionStatus('failed','نشست تأیید نشده','برای تأیید نشست، مینی‌اپ را از دکمهٔ داخل گفت‌وگوی ربات تلگرام باز کنید.');toast('نشست تلگرام دریافت نشد؛ از داخل ربات باز کنید.');return}
 try{
  const res=await fetch('/api/miniapp/me',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({initData})});
  const data=await res.json();
  if(!res.ok||!data.ok){
   const reasons={
    init_data_missing:'اطلاعات نشست به سرور نرسیده است؛ مینی‌اپ را از دکمهٔ داخل ربات باز کنید.',
    bot_token_missing:'توکن ربات در تنظیمات سرور موجود نیست.',
    init_data_too_long:'اطلاعات نشست بیش از حد طولانی است؛ مینی‌اپ را دوباره باز کنید.',
    hash_missing_or_invalid:'امضای نشست تلگرام دریافت نشده یا قالب آن نامعتبر است.',
    hash_mismatch:'امضای نشست با توکن این ربات تطبیق ندارد؛ باید اتصال توکن ربات بررسی شود.',
    auth_date_invalid:'زمان ایجاد نشست نامعتبر است؛ مینی‌اپ را دوباره باز کنید.',
    init_data_expired:'نشست قدیمی شده است؛ مینی‌اپ را ببندید و دوباره از داخل ربات باز کنید.',
    user_invalid:'اطلاعات کاربر در نشست تلگرام معتبر نیست.',
    database_not_ready:'نشست تأیید شد، اما پایگاه داده آماده نیست.'
   };
   const reason=reasons[data.error]||'سرور نشست تلگرام را نپذیرفت؛ دوباره از داخل ربات باز کنید.';
   setSessionStatus('failed','تأیید ناموفق',reason);
   toast(reason);
   return;
  }
  setSessionStatus('verified','نشست تأیید شد','هویت شما توسط سرور تأیید شد؛ اطلاعات حساب از نشست معتبر تلگرام دریافت شده است.');
  $('userName').textContent=data.user.first_name||'مشترک گرامی 🌱';
  $('accountName').textContent=[data.user.first_name,data.user.last_name].filter(Boolean).join(' ')||'—';
  $('telegramId').textContent=data.user.id;
  if(data.isAdmin)$('adminTile').classList.remove('hidden');
  const servicesRes=await fetch('/api/miniapp/services',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({initData})});
  if(servicesRes.ok){const sd=await servicesRes.json();if(sd.services?.length)renderServices(sd.services)}
  const orderRes=await fetch('/api/miniapp/orders',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({initData})});
  if(orderRes.ok){const od=await orderRes.json();if(od.orders?.length){$('ordersList').textContent='';od.orders.forEach(o=>{const row=document.createElement('div');row.className='line';const t=document.createElement('div');t.className='txt';t.textContent=o.public_id+' · '+(o.service_code||'درخواست');const st=document.createElement('span');st.className='pill';st.textContent=o.status;t.appendChild(st);row.appendChild(t);$('ordersList').appendChild(row)})}else $('ordersList').textContent='درخواستی برای نمایش وجود ندارد.'}
 }catch(e){setSessionStatus('failed','خطای اتصال','سرور پاسخ نداد؛ اتصال اینترنت را بررسی و صفحه را دوباره باز کنید.');toast('اتصال به سرور برقرار نشد. لطفاً دوباره تلاش کنید.')}
}
boot();
</script></body></html>`;