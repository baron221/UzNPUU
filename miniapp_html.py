def get_miniapp_html(railway_url=""):
    return f'''<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"/>
<title>UzNPUU</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,700;1,400&display=swap" rel="stylesheet"/>
<link rel="icon" href="/static/favicon.png" type="image/png"/>
<style>
*{{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}}
@keyframes shimmer{{0%{{background-position:-400px 0}}100%{{background-position:400px 0}}}}
.skeleton{{background:linear-gradient(90deg,#0d1020 25%,#131629 50%,#0d1020 75%);background-size:800px 100%;animation:shimmer 1.4s infinite;border-radius:8px;}}
:root{{--bg:#07080f;--s1:#0d1020;--s2:#131629;--card:#181d2e;--border:rgba(120,150,255,0.12);--border2:rgba(120,150,255,0.22);--accent:#7c8fff;--accent2:#ff8c69;--accent3:#52d9a4;--text:#eef0f8;--muted:#6b7299;--muted2:#8890b8;--r:16px;--r2:12px}}
body{{background:var(--bg);color:var(--text);font-family:"Sora",sans-serif;min-height:100vh;overflow-x:hidden;font-size:14px}}
::-webkit-scrollbar{{width:3px}}::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:99px}}
.nav{{position:fixed;bottom:0;left:0;right:0;z-index:200;background:var(--s1);border-top:1px solid var(--border);display:flex;padding:0 4px 4px}}
.nav-btn{{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px 4px 8px;gap:4px;border:none;background:none;cursor:pointer;color:var(--muted);font-family:"Sora",sans-serif;font-size:10px;border-radius:var(--r2);transition:color 0.2s}}
.nav-btn.active{{color:var(--accent)}}
.nav-icon{{font-size:20px;transition:transform 0.2s}}
.nav-btn.active .nav-icon{{transform:scale(1.15)}}
.page{{display:none;padding:16px 16px 90px;min-height:100vh}}
.page.active{{display:block}}
.hero{{background:linear-gradient(135deg,#0d1020,#131629);border:1px solid var(--border);border-radius:20px;padding:24px 20px;margin-bottom:16px;position:relative;overflow:hidden}}
.hero::before{{content:"";position:absolute;top:-40px;right:-40px;width:180px;height:180px;background:radial-gradient(circle,rgba(124,143,255,0.12),transparent 70%);border-radius:50%}}
.hero-label{{font-size:10px;letter-spacing:2.5px;color:var(--accent);text-transform:uppercase;margin-bottom:8px}}
.hero-title{{font-family:"Playfair Display",serif;font-size:26px;font-weight:700;line-height:1.2;margin-bottom:6px}}
.hero-title em{{font-style:italic;color:var(--accent)}}
.hero-sub{{font-size:12px;color:var(--muted2);line-height:1.6}}
.stats-row{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:16px}}
.stat-mini{{background:var(--card);border:1px solid var(--border);border-radius:var(--r2);padding:12px 10px;text-align:center}}
.stat-num{{font-family:"Playfair Display",serif;font-size:20px;font-weight:700}}
.stat-lbl{{font-size:10px;color:var(--muted);margin-top:3px}}
.quick-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px}}
.quick-card{{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:16px;cursor:pointer;transition:border-color 0.2s,transform 0.15s}}
.quick-card:active{{transform:scale(0.97)}}
.quick-card:hover{{border-color:var(--border2)}}
.quick-icon{{font-size:22px;margin-bottom:8px}}
.quick-label{{font-size:12px;font-weight:500;margin-bottom:3px}}
.quick-sub{{font-size:11px;color:var(--muted)}}
.section-title{{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin:20px 0 10px}}
.news-card{{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:14px 16px;margin-bottom:8px;display:flex;gap:12px}}
.news-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:5px}}
.news-text{{font-size:13px;line-height:1.5;flex:1}}
.news-date{{font-size:10px;color:var(--muted);margin-top:4px}}
.chat-header{{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:12px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px}}
.ai-avatar{{width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,var(--accent),#5561d4);display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}}
.ai-name{{font-weight:500;font-size:13px}}
.ai-status{{font-size:11px;color:var(--accent3);display:flex;align-items:center;gap:4px}}
.status-dot{{width:6px;height:6px;border-radius:50%;background:var(--accent3);display:inline-block}}
.chat-msgs{{display:flex;flex-direction:column;gap:10px;margin-bottom:14px;max-height:52vh;overflow-y:auto;padding-right:2px}}
.msg{{padding:10px 13px;border-radius:14px;font-size:13px;line-height:1.55;max-width:88%;animation:msgIn 0.25s ease}}
@keyframes msgIn{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
.msg.bot{{background:var(--s2);border:1px solid var(--border);align-self:flex-start;border-bottom-left-radius:4px}}
.msg.user{{background:linear-gradient(135deg,#3a45a8,#5561d4);align-self:flex-end;border-bottom-right-radius:4px}}
.msg.typing{{background:var(--s2);border:1px solid var(--border);align-self:flex-start}}
.dots{{display:flex;gap:4px;align-items:center;padding:2px 0}}
.dots span{{width:6px;height:6px;background:var(--muted);border-radius:50%;animation:dot 1.2s infinite}}
.dots span:nth-child(2){{animation-delay:.2s}}
.dots span:nth-child(3){{animation-delay:.4s}}
@keyframes dot{{0%,60%,100%{{transform:translateY(0)}}30%{{transform:translateY(-5px)}}}}
.suggested{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}}
.sug-btn{{background:var(--s2);border:1px solid var(--border);border-radius:99px;padding:6px 12px;font-size:11px;color:var(--muted2);cursor:pointer;font-family:"Sora",sans-serif;transition:all 0.2s}}
.sug-btn:hover{{border-color:var(--accent);color:var(--accent)}}
.chat-bar{{display:flex;gap:8px;align-items:flex-end}}
.chat-in{{flex:1;background:var(--s2);border:1px solid var(--border);border-radius:14px;padding:11px 14px;color:var(--text);font-family:"Sora",sans-serif;font-size:13px;resize:none;outline:none;transition:border-color 0.2s;max-height:90px;line-height:1.4}}
.chat-in:focus{{border-color:var(--accent)}}
.chat-in::placeholder{{color:var(--muted)}}
.send{{width:42px;height:42px;border-radius:12px;border:none;cursor:pointer;flex-shrink:0;background:linear-gradient(135deg,var(--accent),#5561d4);color:#fff;font-size:16px;display:flex;align-items:center;justify-content:center;transition:transform 0.15s}}
.send:active{{transform:scale(0.9)}}
.send:disabled{{opacity:0.35;cursor:not-allowed}}
.search-wrap{{position:relative;margin-bottom:16px}}
.search-in{{width:100%;background:var(--s2);border:1px solid var(--border);border-radius:var(--r2);padding:11px 14px 11px 36px;color:var(--text);font-family:"Sora",sans-serif;font-size:13px;outline:none;transition:border-color 0.2s}}
.search-in:focus{{border-color:var(--accent)}}
.search-in::placeholder{{color:var(--muted)}}
.search-icon{{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:14px}}
.faq-cat{{font-size:10px;letter-spacing:2px;color:var(--accent);text-transform:uppercase;margin:16px 0 8px;font-weight:500}}
.faq-item{{background:var(--card);border:1px solid var(--border);border-radius:var(--r2);margin-bottom:6px;overflow:hidden;transition:border-color 0.2s}}
.faq-item:hover{{border-color:var(--border2)}}
.faq-q{{padding:12px 14px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:13px;font-weight:500}}
.faq-arr{{color:var(--muted);font-size:11px;transition:transform 0.2s;flex-shrink:0}}
.faq-item.open .faq-arr{{transform:rotate(180deg)}}
.faq-a{{display:none;padding:0 14px 12px;font-size:12px;color:var(--muted2);line-height:1.6;border-top:1px solid var(--border);padding-top:10px}}
.faq-item.open .faq-a{{display:block}}
.profile-hero{{background:linear-gradient(135deg,var(--s1),var(--s2));border:1px solid var(--border);border-radius:20px;padding:20px;margin-bottom:14px;text-align:center}}
.p-avatar{{width:68px;height:68px;border-radius:18px;margin:0 auto 12px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-family:"Playfair Display",serif;font-size:28px;font-weight:700;color:#fff}}
.p-name{{font-family:"Playfair Display",serif;font-size:22px;font-weight:700;margin-bottom:3px}}
.p-role{{font-size:11px;color:var(--muted2)}}
.gpa-wrap{{margin:16px auto 0;width:110px;height:110px;position:relative}}
.gpa-wrap svg{{transform:rotate(-90deg)}}
.gpa-center{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center}}
.gpa-num{{font-family:"Playfair Display",serif;font-size:26px;font-weight:700;color:var(--accent);line-height:1}}
.gpa-lbl{{font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-top:2px}}
.info-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px}}
.info-card{{background:var(--card);border:1px solid var(--border);border-radius:var(--r2);padding:14px}}
.info-val{{font-family:"Playfair Display",serif;font-size:20px;font-weight:700;margin-bottom:3px}}
.info-lbl{{font-size:10px;color:var(--muted)}}
.detail-row{{background:var(--card);border:1px solid var(--border);border-radius:var(--r2);padding:11px 14px;display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}}
.det-lbl{{font-size:12px;color:var(--muted)}}
.det-val{{font-size:12px;font-weight:500}}
.badge{{display:inline-flex;align-items:center;gap:4px;background:rgba(82,217,164,0.12);border:1px solid rgba(82,217,164,0.25);border-radius:99px;padding:3px 10px;font-size:11px;color:var(--accent3)}}
.badge-dot{{width:5px;height:5px;border-radius:50%;background:var(--accent3)}}
.notice-box{{background:rgba(124,143,255,0.06);border:1px solid rgba(124,143,255,0.18);border-radius:var(--r2);padding:12px 14px;font-size:12px;color:var(--muted2);line-height:1.6;margin-top:6px;text-align:center}}
</style>
</head>
<body>

<div id="page-home" class="page active">
  <div class="hero">
    <div class="hero-label">Rasmiy bot</div>
    <div class="hero-title">UzNPUU<br><em>Yordamchi</em></div>
    <div class="hero-sub">Nizomiy nomidagi O\'zbekiston Milliy pedagogika universiteti</div>
  </div>
  <div class="stats-row">
    <div class="stat-mini"><div class="stat-num" style="color:var(--accent)" id="statPairs">172</div><div class="stat-lbl">Javoblar</div></div>
    <div class="stat-mini"><div class="stat-num" style="color:var(--accent2)">24/7</div><div class="stat-lbl">Ishlaydi</div></div>
    <div class="stat-mini"><div class="stat-num" style="color:var(--accent3)" id="statUsers">0</div><div class="stat-lbl">Foydalanuvchilar</div></div>
  </div>
  <div class="quick-grid">
    <div class="quick-card" onclick="goTo(\'chat\')"><div class="quick-icon">💬</div><div class="quick-label">Savol bering</div><div class="quick-sub">AI yordamida javob</div></div>
    <div class="quick-card" onclick="goTo(\'faq\')"><div class="quick-icon">📋</div><div class="quick-label">FAQ</div><div class="quick-sub">Tez-tez soraladigan</div></div>
    <div class="quick-card" onclick="goTo(\'profile\')"><div class="quick-icon">👤</div><div class="quick-label">Profilim</div><div class="quick-sub">GPA va malumotlar</div></div>
    <div class="quick-card" onclick="window.open(\'https://student.tdpu.uz\')"><div class="quick-icon">🖥️</div><div class="quick-label">HEMIS</div><div class="quick-sub">Tizimga kirish</div></div>
  </div>
  <div class="section-title">Yangiliklar</div>
  <div class="news-card"><div class="news-dot" style="background:var(--accent)"></div><div><div class="news-text">2025-2026 grant qayta taqsimlash natijalari elon qilindi</div><div class="news-date">15-avgust 2025</div></div></div>
  <div class="news-card"><div class="news-dot" style="background:var(--accent3)"></div><div><div class="news-text">Kredit-modul tizimi yangi qoidalari: 824-sonli qaror</div><div class="news-date">1-sentabr 2025</div></div></div>
  <div class="news-card"><div class="news-dot" style="background:var(--accent2)"></div><div><div class="news-text">Akademik talil va kochirish muddatlari — transfer.edu.uz</div><div class="news-date">20-iyul 2025</div></div></div>
</div>

<div id="page-chat" class="page">
  <div class="chat-header">
    <div class="ai-avatar">🎓</div>
    <div><div class="ai-name">UzNPUU Yordamchi</div><div class="ai-status"><span class="status-dot"></span>Faol — hujjatlardan javob beradi</div></div>
  </div>
  <div class="chat-msgs" id="chatMsgs">
    <div class="msg bot">Assalomu alaykum! 👋 Savolingizni yozing — rasmiy hujjatlarimizdan aniq javob beraman.</div>
  </div>
  <div class="suggested" id="suggs">
    <div class="sug-btn" onclick="useSug(this)">GPA qanday hisoblanadi?</div>
    <div class="sug-btn" onclick="useSug(this)">HEMIS parolini tiklash</div>
    <div class="sug-btn" onclick="useSug(this)">Akademik talil muddati</div>
    <div class="sug-btn" onclick="useSug(this)">Grant uchun minimal GPA</div>
  </div>
  <div class="chat-bar">
    <textarea class="chat-in" id="chatIn" placeholder="Savolingizni yozing..." rows="1" onkeydown="handleKey(event)" oninput="resize(this)"></textarea>
    <button class="send" id="sendBtn" onclick="sendMsg()">➤</button>
  </div>
</div>

<div id="page-faq" class="page">
  <div class="search-wrap">
    <span class="search-icon">🔍</span>
    <input class="search-in" id="faqQ" placeholder="Savol qidiring..." oninput="filterFAQ(this.value)"/>
  </div>
  <div id="faqList"></div>
</div>

<div id="page-profile" class="page">
  <div class="profile-hero">
    <div class="p-avatar" id="pAvatar">👤</div>
    <div class="p-name" id="pName">Talaba</div>
    <div class="p-role">UzNPUU talabasi</div>
    <div class="gpa-wrap">
      <svg width="110" height="110" viewBox="0 0 110 110">
        <circle cx="55" cy="55" r="46" fill="none" stroke="#131629" stroke-width="11"/>
        <circle cx="55" cy="55" r="46" fill="none" stroke="#7c8fff" stroke-width="11" stroke-dasharray="289.0" stroke-dashoffset="86.7" stroke-linecap="round"/>
      </svg>
      <div class="gpa-center"><div class="gpa-num">—</div><div class="gpa-lbl">GPA</div></div>
    </div>
  </div>
  <div class="info-grid">
    <div class="info-card"><div class="info-val" style="color:var(--accent2)">—</div><div class="info-lbl">Kreditlar</div></div>
    <div class="info-card"><div class="info-val" style="color:var(--accent3)">—</div><div class="info-lbl">Kurs</div></div>
  </div>
  <div class="detail-row"><span class="det-lbl">Status</span><span class="badge"><span class="badge-dot"></span>Faol talaba</span></div>
  <div class="detail-row"><span class="det-lbl">Telegram ID</span><span class="det-val" id="tgId">—</span></div>
  <div class="detail-row"><span class="det-lbl">Foydalanuvchi</span><span class="det-val" id="tgUser">—</span></div>
  <div class="notice-box">Toliq akademik malumotlar uchun HEMIS tizimiga kiring:<br><strong style="color:var(--accent)">student.tdpu.uz</strong></div>
</div>

<nav class="nav">
  <button class="nav-btn active" onclick="goTo(\'home\',this)"><span class="nav-icon">🏠</span>Bosh sahifa</button>
  <button class="nav-btn" onclick="goTo(\'chat\',this)"><span class="nav-icon">💬</span>Chat</button>
  <button class="nav-btn" onclick="goTo(\'faq\',this)"><span class="nav-icon">📋</span>FAQ</button>
  <button class="nav-btn" onclick="goTo(\'profile\',this)"><span class="nav-icon">👤</span>Profil</button>
</nav>

<script>
var API_URL = "{railway_url}";
var tg = window.Telegram && window.Telegram.WebApp;
if(tg){{ tg.ready(); tg.expand(); }}
var user = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
if(user){{
  var name = [user.first_name, user.last_name].filter(Boolean).join(" ");
  document.getElementById("pName").textContent = name || "Talaba";
  document.getElementById("tgId").textContent = user.id || "—";
  document.getElementById("tgUser").textContent = user.username ? "@"+user.username : "—";
  if(user.first_name){{ var av=document.getElementById("pAvatar"); av.textContent=user.first_name[0].toUpperCase(); av.style.fontSize="32px"; }}
}}

fetch(API_URL+"/api/stats").then(function(r){{return r.json();}}).then(function(s){{
  if(s.users) document.getElementById("statUsers").textContent = s.users;
  if(s.total) document.getElementById("statPairs").textContent = s.total;
}}).catch(function(){{}});

function goTo(name, btn){{
  document.querySelectorAll(".page").forEach(function(p){{p.classList.remove("active");}});
  document.querySelectorAll(".nav-btn").forEach(function(b){{b.classList.remove("active");}});
  document.getElementById("page-"+name).classList.add("active");
  if(btn) btn.classList.add("active");
  else {{ var idx={{home:0,chat:1,faq:2,profile:3}}[name]; document.querySelectorAll(".nav-btn")[idx] && document.querySelectorAll(".nav-btn")[idx].classList.add("active"); }}
  if(name==="faq") renderFAQ(faqs);
}}

async function sendMsg(){{
  var inp=document.getElementById("chatIn");
  var q=inp.value.trim();
  if(!q) return;
  addMsg(q,"user");
  inp.value=""; inp.style.height="auto";
  document.getElementById("sendBtn").disabled=true;
  document.getElementById("suggs").style.display="none";
  var tid=addTyping();
  try{{
    var r=await fetch(API_URL+"/ask",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{question:q}})}});
    var d=await r.json();
    removeTyping(tid);
    addMsg(d.answer||"Xatolik yuz berdi.","bot");
  }}catch(e){{
    removeTyping(tid);
    addMsg("Serverga ulanishda xatolik.","bot");
  }}
  document.getElementById("sendBtn").disabled=false;
}}

function useSug(el){{ document.getElementById("chatIn").value=el.textContent; sendMsg(); }}
function addMsg(text,type){{ var msgs=document.getElementById("chatMsgs"); var d=document.createElement("div"); d.className="msg "+type; d.textContent=text; msgs.appendChild(d); msgs.scrollTop=msgs.scrollHeight; }}
function addTyping(){{ var msgs=document.getElementById("chatMsgs"); var d=document.createElement("div"); var id="t"+Date.now(); d.id=id; d.className="msg typing"; d.innerHTML="<div class=\\"dots\\"><span></span><span></span><span></span></div>"; msgs.appendChild(d); msgs.scrollTop=msgs.scrollHeight; return id; }}
function removeTyping(id){{ var el=document.getElementById(id); if(el) el.remove(); }}
function handleKey(e){{ if(e.key==="Enter"&&!e.shiftKey){{ e.preventDefault(); sendMsg(); }} }}
function resize(el){{ el.style.height="auto"; el.style.height=Math.min(el.scrollHeight,90)+"px"; }}

var faqs=[
  {{cat:"📚 HEMIS tizimi",items:[
    {{q:"HEMIS parolimni qanday tiklash mumkin?",a:"Registrator ofisi xodimlariga kelib murojaat qilasiz, Telegram bot orqali fakultetingiz mas\'ul xodimiga yozasiz yoki OneID tizimi orqali kirishingiz mumkin."}},
    {{q:"HEMIS da dars jadvalini qanday koraman?",a:"student.tdpu.uz saytiga yoki HEMIS ilovasiga kirasiz — dashboardda Dars jadvali bolimi chiqadi."}},
    {{q:"HEMIS da GPA ballimni qayerdan koraman?",a:"Akademik korsatkichlar bolimida umumiy ortacha baho (GPA) korsatiladi."}},
    {{q:"HEMIS da baholarim chiqmayapti, nega?",a:"Baholar hali oqituvchi tomonidan kiritilmagan yoki tasdiqlanmagan bolishi mumkin. Registrator ofisi xodimlariga murojaat qiling."}}
  ]}},
  {{cat:"💰 Tolov va kontrakt",items:[
    {{q:"Kontrakt tolov summasini qayerdan bilaman?",a:"kontrakt.edu.uz saytiga kiring. Shaxsiy kabinet → Tolov malumotlari bolimidan kontrakt summasini koring."}},
    {{q:"Shartnoma tolovini online tolasa boladimi?",a:"Ha, shartnoma tolovlarini online tolash mumkin."}},
    {{q:"Tolov kvitansiyasini qayerdan yuklab olaman?",a:"Tolovlar tarixi bolimida PDF yuklab olish tugmasi orqali kvitansiyani olish mumkin."}}
  ]}},
  {{cat:"🎓 Grant va stipendiya",items:[
    {{q:"Grantga ariza topshirish uchun minimal GPA qancha?",a:"3.5 va undan yuqori."}},
    {{q:"Toliq grant nima?",a:"Bir oquv yiliga berilib, kontraktning 100% davlat tomonidan qoplanadigan va stipendiya beriladigan grant."}},
    {{q:"GPA qanday hisoblanadi?",a:"Kreditni bahoga kopaytirish orqali yigilgan umumiy ballni umumiy kreditga bolish orqali."}}
  ]}},
  {{cat:"📋 Akademik talil va kochirish",items:[
    {{q:"Akademik talilning maksimal muddati qancha?",a:"1 yil."}},
    {{q:"Oqushni kochirish uchun ariza qayerga topshiriladi?",a:"transfer.edu.uz platformasida elektron tarzda."}},
    {{q:"Akademik talilda stipendiya beriladimi?",a:"Yoq, akademik talilda bolgan talaba stipendiya va boshqa imtiyozlardan foydalana olmaydi."}}
  ]}}
];

function renderFAQ(data){{
  var c=document.getElementById("faqList"); c.innerHTML=""; var any=false;
  data.forEach(function(cat){{
    if(!cat.items.length) return; any=true;
    var lbl=document.createElement("div"); lbl.className="faq-cat"; lbl.textContent=cat.cat; c.appendChild(lbl);
    cat.items.forEach(function(it){{
      var d=document.createElement("div"); d.className="faq-item";
      d.innerHTML="<div class=\\"faq-q\\" onclick=\\"this.parentElement.classList.toggle(\'open\')\\">"+it.q+"<span class=\\"faq-arr\\">▼</span></div><div class=\\"faq-a\\">"+it.a+"</div>";
      c.appendChild(d);
    }});
  }});
  if(!any) c.innerHTML="<div style=\\"text-align:center;color:var(--muted);padding:40px;font-size:13px\\">Hech narsa topilmadi</div>";
}}

function filterFAQ(q){{
  if(!q.trim()){{ renderFAQ(faqs); return; }}
  var ql=q.toLowerCase();
  renderFAQ(faqs.map(function(cat){{ return {{...cat,items:cat.items.filter(function(it){{ return it.q.toLowerCase().includes(ql)||it.a.toLowerCase().includes(ql); }})}}; }}));
}}

renderFAQ(faqs);
</script>
</body>
</html>'''
