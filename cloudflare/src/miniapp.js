export const MINIAPP_HTML = String.raw`<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#145bd7"><meta name="color-scheme" content="light"><title>کمک‌یار مهاجر</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
:root{color-scheme:light;--blue:#145bd7;--navy:#123b78;--bg:#f4f7fc;--ink:#162844;--muted:#73819a;--card:#fff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font-family:"Vazirmatn",Tahoma,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:var(--ink);padding:0 0 calc(22px + env(safe-area-inset-bottom));}button{font:inherit;cursor:pointer;border:0}
.hero{position:relative;overflow:hidden;background:linear-gradient(135deg,#103f91 0%,#145bd7 52%,#4a9bff 100%);color:white;padding:25px 18px 30px;border-radius:0 0 30px 30px;box-shadow:0 14px 34px #174e9b25}.hero:after{content:"";position:absolute;width:190px;height:190px;border-radius:50%;border:1px solid #ffffff20;left:-62px;top:-72px;box-shadow:0 0 0 22px #ffffff08,0 0 0 46px #ffffff06;pointer-events:none}.hero>*{position:relative;z-index:1}.top{display:flex;align-items:center;gap:12px}.logo{width:50px;height:50px;border-radius:17px;background:linear-gradient(145deg,#ffffff38,#ffffff12);display:grid;place-items:center;font-size:26px;border:1px solid #ffffff55;box-shadow:inset 0 1px #ffffff45}.hero h1{font-size:20px;margin:0 0 5px}.hero p{font-size:12px;margin:0;color:#e4efff}.hello{margin-top:24px;font-size:14px}.hello strong{display:block;font-size:21px;margin-top:5px}.wrap{padding:18px 15px;max-width:720px;margin:auto}.section-title{display:flex;align-items:center;justify-content:space-between;margin:5px 2px 12px;font-size:16px;font-weight:800}.section-title small{font-size:11px;color:var(--muted);font-weight:500}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}.tile{min-height:130px;border:1px solid #e8eef7;border-radius:21px;padding:15px;text-align:right;box-shadow:0 6px 20px #233e6809;display:flex;flex-direction:column;align-items:flex-start;gap:9px;transition:transform .12s}.tile:active{transform:scale(.98)}.tile .ico{width:43px;height:43px;border-radius:14px;display:grid;place-items:center;font-size:23px}.tile b{font-size:14px;line-height:1.5}.tile small{font-size:11px;color:var(--muted);line-height:1.5}.t-blue{background:#e7f0ff}.t-blue .ico{background:#c9ddff}.t-teal{background:#e0f8f3}.t-teal .ico{background:#b8eee3}.t-orange{background:#fff0df}.t-orange .ico{background:#ffdbb4}.t-purple{background:#f0eaff}.t-purple .ico{background:#dcd0ff}.t-pink{background:#ffe9f1}.t-pink .ico{background:#ffd0e1}.t-green{background:#e8f7df}.t-green .ico{background:#ccecb9}.wide{grid-column:1/-1;min-height:86px;flex-direction:row;align-items:center}.wide .txt{flex:1}.panel{background:var(--card);border:1px solid #e9eef6;border-radius:21px;padding:18px;margin-top:18px;box-shadow:0 7px 24px #233e6808}.panel h2{font-size:15px;margin:0 0 13px}.line{display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #edf1f7}.line:last-child{border:0}.line .ico{font-size:21px}.line .txt{flex:1;font-size:13px}.line small{display:block;color:var(--muted);font-size:11px;margin-top:4px}.pill{font-size:11px;border-radius:20px;background:#e7f0ff;color:#1456ad;padding:6px 9px}.muted{color:var(--muted);font-size:12px;line-height:1.8}.hidden{display:none!important}.view{display:none}.view.active{display:block}.back{color:var(--blue);background:#e7f0ff;padding:9px 13px;border-radius:12px;font-size:12px;font-weight:700;margin-bottom:14px}.service{display:flex;gap:12px;align-items:center;background:white;padding:14px;border:1px solid #e9eef6;border-radius:18px;margin:10px 0;box-shadow:0 5px 17px #233e6807}.service .ico{font-size:24px;width:44px;height:44px;display:grid;place-items:center;background:#edf4ff;border-radius:14px}.service .txt{flex:1}.service b{font-size:13px}.service small{display:block;color:var(--muted);margin-top:4px;font-size:11px}.primary{background:linear-gradient(135deg,#145bd7,#2e7cf0);color:white;padding:10px 14px;border-radius:13px;font-size:12px;font-weight:800;box-shadow:0 4px 12px #145bd720}.primary:disabled{opacity:.55;box-shadow:none}.admin{border:1px solid #ffdf9b;background:#fff9e9}.status{padding:12px;border-radius:13px;background:#fff3d8;color:#825500;font-size:12px;line-height:1.8;margin-top:12px}.foot{text-align:center;color:#8c9ab0;font-size:10px;padding:22px 10px 12px}.section-title{letter-spacing:-.2px}.tile b,.service b,.panel h2{letter-spacing:-.15px}button:focus-visible{outline:3px solid #70a9ff;outline-offset:3px}.toast{position:fixed;bottom:20px;right:16px;left:16px;background:#17365f;color:white;padding:13px 16px;border-radius:13px;font-size:13px;box-shadow:0 8px 24px #10274a33;z-index:9}
@media(min-width:520px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}.tile.wide{grid-column:span 2}.hero,.wrap{padding-left:24px;padding-right:24px}}
</style></head>
<body>
<header class="hero"><div class="top"><div class="logo">🤝</div><div><h1>کمک‌یار مهاجر</h1><p>خدمات دفتر نت‌یار مهاجر</p></div></div><div class="hello">سلام، خوش آمدید<strong id="userName">مشترک گرامی 🌱</strong></div></header>
<main class="wrap">
<section id="home" class="view active">
<div class="section-title">خدمات و حساب شما <small id="connection">در حال اتصال…</small></div>
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
function renderServices(services){$('serviceList').innerHTML='';services.forEach((s,i)=>{const icons={identity:'🪪',khodnevis:'📝',fida:'🪪',dolatman_login:'🔐',student_screening:'🎒',other_service:'🧾'};const el=document.createElement('div');el.className='service';const ico=document.createElement('span');ico.className='ico';ico.textContent=icons[s.code]||'📄';const txt=document.createElement('div');txt.className='txt';const name=document.createElement('b');name.textContent=s.name;const desc=document.createElement('small');desc.textContent=s.description||s.desc||'برای ثبت درخواست انتخاب کنید';txt.append(name,desc);const button=document.createElement('button');button.className='primary';button.textContent='انتخاب';button.onclick=async()=>{if(!tg?.initData){toast('برای انتخاب خدمت، مینی‌اپ را از داخل تلگرام باز کنید.');return}button.disabled=true;try{const r=await fetch('/api/miniapp/select-service',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({initData:tg.initData,code:s.code})});const d=await r.json();if(r.ok&&d.ok){toast('پیام قوانین به گفت‌وگوی ربات ارسال شد. برای ادامه به ربات برگردید.')}else if(d.error==='service_not_ready'){toast('این خدمت هنوز فعال نشده؛ تعرفه و قوانین باید تأیید شوند.')}else{toast('انتخاب خدمت انجام نشد؛ لطفاً دوباره تلاش کنید.')}}catch{toast('ارتباط با سرور برقرار نشد.')}finally{button.disabled=false}};el.append(ico,txt,button);$('serviceList').append(el)})}
renderServices(staticServices);
async function boot(){
 const initData=tg?.initData||'';
 if(!initData){$('connection').textContent='پیش‌نمایش';toast('برای ورود امن، مینی‌اپ را از داخل ربات تلگرام باز کنید.');return}
 try{
  const res=await fetch('/api/miniapp/me',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({initData})});
  const data=await res.json();
  if(!res.ok||!data.ok){$('connection').textContent='نیازمند بررسی';toast(data.error==='database_not_ready'?'اتصال پایگاه داده هنوز آماده نیست.':'تأیید نشست تلگرام ناموفق بود. مینی‌اپ را از داخل ربات باز کنید.');return}
  $('connection').textContent='متصل';
  $('userName').textContent=data.user.first_name||'مشترک گرامی 🌱';
  $('accountName').textContent=[data.user.first_name,data.user.last_name].filter(Boolean).join(' ')||'—';
  $('telegramId').textContent=data.user.id;
  if(data.isAdmin)$('adminTile').classList.remove('hidden');
  const servicesRes=await fetch('/api/miniapp/services',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({initData})});
  if(servicesRes.ok){const sd=await servicesRes.json();if(sd.services?.length)renderServices(sd.services)}
  const orderRes=await fetch('/api/miniapp/orders',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({initData})});
  if(orderRes.ok){const od=await orderRes.json();if(od.orders?.length){$('ordersList').textContent='';od.orders.forEach(o=>{const row=document.createElement('div');row.className='line';const t=document.createElement('div');t.className='txt';t.textContent=o.public_id+' · '+(o.service_code||'درخواست');const st=document.createElement('span');st.className='pill';st.textContent=o.status;t.appendChild(st);row.appendChild(t);$('ordersList').appendChild(row)})}else $('ordersList').textContent='درخواستی برای نمایش وجود ندارد.'}
 }catch(e){$('connection').textContent='آفلاین';toast('اتصال به سرور برقرار نشد. لطفاً دوباره تلاش کنید.')}
}
boot();
</script></body></html>`;