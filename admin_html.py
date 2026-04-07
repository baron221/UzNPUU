def get_admin_html():
    return '''<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>OʻzMPU Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Playfair+Display:wght@700&display=swap" rel="stylesheet"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#07080f;--s1:#0d1020;--s2:#131629;--card:#181d2e;--border:rgba(120,150,255,0.12);--border2:rgba(120,150,255,0.22);--accent:#7c8fff;--accent2:#ff8c69;--accent3:#52d9a4;--red:#ff6b6b;--text:#eef0f8;--muted:#6b7299;--muted2:#8890b8;--r:16px;--r2:12px}
body{background:var(--bg);color:var(--text);font-family:"Sora",sans-serif;min-height:100vh;font-size:14px}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:var(--border2);border-radius:99px}
.login-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.login-card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:32px;width:100%;max-width:380px;text-align:center}
.login-icon{font-size:40px;margin-bottom:16px}
.login-title{font-family:"Playfair Display",serif;font-size:24px;margin-bottom:6px}
.login-sub{font-size:12px;color:var(--muted2);margin-bottom:24px}
.inp{width:100%;background:var(--s2);border:1px solid var(--border);border-radius:var(--r2);padding:12px 14px;color:var(--text);font-family:"Sora",sans-serif;font-size:14px;outline:none;margin-bottom:10px;transition:border-color 0.2s}
.inp:focus{border-color:var(--accent)}
.inp::placeholder{color:var(--muted)}
.btn-login{width:100%;background:linear-gradient(135deg,var(--accent),#5561d4);border:none;border-radius:var(--r2);padding:13px;color:#fff;font-family:"Sora",sans-serif;font-size:14px;font-weight:500;cursor:pointer}
.err{font-size:12px;color:var(--red);margin-top:8px;min-height:18px}
.dash{display:none}
.sidebar{position:fixed;left:0;top:0;bottom:0;width:240px;background:var(--s1);border-right:1px solid var(--border);padding:0;z-index:100;overflow-y:auto}
.sidebar-top{padding:24px 20px;border-bottom:1px solid var(--border)}
.sidebar-logo-box{width:36px;height:36px;background:linear-gradient(135deg,var(--accent),#5561d4);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;margin-bottom:12px}
.sidebar-title{font-family:"Playfair Display",serif;font-size:18px;font-weight:700}
.sidebar-sub{font-size:10px;color:var(--muted);margin-top:2px}
.nav-section{font-size:9px;letter-spacing:2px;color:var(--muted);padding:20px 20px 8px;text-transform:uppercase}
.nav-item{display:flex;align-items:center;gap:12px;padding:11px 20px;cursor:pointer;color:var(--muted2);font-size:13px;font-weight:500;transition:all 0.2s;border-left:3px solid transparent}
.nav-item:hover{color:var(--text);background:rgba(255,255,255,0.04)}
.nav-item.active{color:var(--accent);background:rgba(124,143,255,0.08);border-left-color:var(--accent)}
.nav-icon{font-size:16px;width:20px;text-align:center}
.nav-bottom{position:absolute;bottom:0;left:0;right:0;padding:16px 20px;border-top:1px solid var(--border)}
.logout-btn{width:100%;background:rgba(255,107,107,0.1);border:1px solid rgba(255,107,107,0.25);border-radius:8px;padding:10px;color:var(--red);font-family:"Sora",sans-serif;font-size:13px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px}
.content{margin-left:240px;padding:28px;min-height:100vh}
.page-header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px}
.page-title{font-family:"Playfair Display",serif;font-size:26px;font-weight:700}
.page-sub{font-size:12px;color:var(--muted2);margin-top:4px}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:18px}
.stat-icon{font-size:22px;margin-bottom:10px}
.stat-num{font-family:"Playfair Display",serif;font-size:30px;font-weight:700;line-height:1;margin-bottom:4px}
.stat-lbl{font-size:11px;color:var(--muted)}
.c-blue{color:var(--accent)}.c-green{color:var(--accent3)}.c-red{color:var(--red)}.c-orange{color:var(--accent2)}.c-purple{color:#b08fff}
.charts-grid{display:grid;grid-template-columns:2fr 1fr;gap:12px;margin-bottom:20px}
@media(max-width:900px){.charts-grid{grid-template-columns:1fr}}
.chart-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:20px}
.chart-title{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:14px}
.chart-wrap{position:relative;height:200px}
.table-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);overflow:hidden;margin-bottom:16px}
table{width:100%;border-collapse:collapse}
th{padding:11px 16px;text-align:left;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--border);background:var(--s2);font-weight:600}
td{padding:12px 16px;font-size:13px;border-bottom:1px solid rgba(255,255,255,0.04);color:var(--text)}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(124,143,255,0.04)}
.badge{display:inline-flex;align-items:center;padding:3px 10px;border-radius:99px;font-size:11px;font-weight:500}
.badge-green{background:rgba(82,217,164,0.12);color:var(--accent3)}
.badge-red{background:rgba(255,107,107,0.12);color:var(--red)}
.badge-blue{background:rgba(124,143,255,0.12);color:var(--accent)}
.badge-orange{background:rgba(255,140,105,0.12);color:var(--accent2)}
.badge-purple{background:rgba(176,143,255,0.12);color:#b08fff}
.btn{padding:8px 16px;border-radius:8px;border:none;cursor:pointer;font-family:"Sora",sans-serif;font-size:12px;font-weight:500;transition:all 0.2s}
.btn-sm{padding:5px 10px;font-size:11px}
.btn-primary{background:linear-gradient(135deg,var(--accent),#5561d4);color:#fff}
.btn-blue{background:rgba(124,143,255,0.15);color:var(--accent);border:1px solid rgba(124,143,255,0.3)}
.btn-blue:hover{background:rgba(124,143,255,0.25)}
.btn-red{background:rgba(255,107,107,0.1);color:var(--red);border:1px solid rgba(255,107,107,0.25)}
.btn-red:hover{background:rgba(255,107,107,0.2)}
.btn-green{background:rgba(82,217,164,0.1);color:var(--accent3);border:1px solid rgba(82,217,164,0.25)}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:1000;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(4px)}
.modal-bg.open{display:flex}
.modal{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:28px;width:100%;max-width:500px;max-height:90vh;overflow-y:auto}
.modal-title{font-family:"Playfair Display",serif;font-size:22px;margin-bottom:22px}
.form-row{margin-bottom:14px}
.form-label{font-size:12px;color:var(--muted2);margin-bottom:6px;display:block;font-weight:500}
.form-inp{width:100%;background:var(--s2);border:1px solid var(--border);border-radius:var(--r2);padding:10px 14px;color:var(--text);font-family:"Sora",sans-serif;font-size:13px;outline:none;transition:border-color 0.2s}
.form-inp:focus{border-color:var(--accent)}
.form-inp::placeholder{color:var(--muted)}
select.form-inp option{background:var(--card)}
textarea.form-inp{resize:vertical;min-height:90px}
.modal-actions{display:flex;gap:10px;margin-top:20px;justify-content:flex-end}
.filter-row{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;align-items:center}
.filter-select,.search-inp{background:var(--s2);border:1px solid var(--border);border-radius:8px;padding:8px 12px;color:var(--text);font-family:"Sora",sans-serif;font-size:12px;outline:none;transition:border-color 0.2s}
.filter-select:focus,.search-inp:focus{border-color:var(--accent)}
.search-inp{min-width:200px}
.search-inp::placeholder{color:var(--muted)}
.faq-add-form{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:20px;margin-bottom:16px}
.faq-add-title{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:14px}
.info-box{background:rgba(124,143,255,0.06);border:1px solid rgba(124,143,255,0.2);border-radius:var(--r);padding:16px 20px;margin-bottom:20px;font-size:13px;color:var(--muted2);line-height:1.7}
.empty{text-align:center;padding:48px;color:var(--muted);font-size:13px}
.loading{text-align:center;padding:32px;color:var(--muted);font-size:13px}
.tab-page{display:none}.tab-page.active{display:block}
</style>
</head>
<body>
<div class="login-wrap" id="loginWrap">
  <div class="login-card">
    <div class="login-icon">🔐</div>
    <div class="login-title">Admin Panel</div>
    <div class="login-sub">OʻzMPU Bot boshqaruv tizimi</div>
    <input class="inp" type="text" id="loginUser" placeholder="Login"/>
    <input class="inp" type="password" id="loginPass" placeholder="Parol" onkeydown="if(event.key===\'Enter\')doLogin()"/>
    <button class="btn-login" onclick="doLogin()">Kirish →</button>
    <div class="err" id="loginErr"></div>
  </div>
</div>
<div class="dash" id="dash">
  <div class="sidebar">
    <div class="sidebar-top">
      <div class="sidebar-logo-box">🎓</div>
      <div class="sidebar-title">OʻzMPU</div>
      <div class="sidebar-sub">Admin boshqaruv paneli</div>
    </div>
    <div class="nav-section">Asosiy</div>
    <div class="nav-item active" onclick="showPage(\'overview\',this)"><span class="nav-icon">📊</span>Umumiy</div>
    <div class="nav-item" onclick="showPage(\'questions\',this)"><span class="nav-icon">💬</span>Savollar</div>
    <div class="nav-section">Boshqaruv</div>
    <div class="nav-item" onclick="showPage(\'faculties\',this)"><span class="nav-icon">🏫</span>Fakultetlar</div>
    <div class="nav-item" onclick="showPage(\'users\',this)"><span class="nav-icon">👥</span>Xodimlar</div>
    <div class="nav-section">Kontent</div>
    <div class="nav-item" onclick="showPage(\'faq\',this)"><span class="nav-icon">📋</span>FAQ Boshqaruv</div>
    <div class="nav-section">Tizim</div>
    <div class="nav-item" onclick="showPage(\'upload\',this)"><span class="nav-icon">📁</span>Hujjat Yuklash</div>
    <div class="nav-bottom">
      <button class="logout-btn" onclick="doLogout()">🚪 Chiqish</button>
    </div>
  </div>
  <div class="content">
    <div id="page-overview" class="tab-page active">
      <div class="page-header">
        <div><div class="page-title">Umumiy ko\'rinish</div><div class="page-sub">Barcha statistikalar</div></div>
        <button class="btn btn-blue" onclick="loadOverview()">↻ Yangilash</button>
      </div>
      <div class="stats-grid" id="statsGrid"><div class="loading">Yuklanmoqda...</div></div>
      <div class="charts-grid">
        <div class="chart-card"><div class="chart-title">So\'nggi 7 kun faolligi</div><div class="chart-wrap"><canvas id="actChart"></canvas></div></div>
        <div class="chart-card"><div class="chart-title">Til taqsimoti</div><div class="chart-wrap"><canvas id="langChart"></canvas></div></div>
      </div>
    </div>
    <div id="page-questions" class="tab-page">
      <div class="page-header">
        <div><div class="page-title">Savollar</div><div class="page-sub">Talabalar yuborgan savollar</div></div>
        <button class="btn btn-blue" onclick="loadQuestions()">↻ Yangilash</button>
      </div>
      <div class="filter-row">
        <select class="filter-select" id="qFacultyFilter" onchange="loadQuestions()"><option value="">Barcha fakultetlar</option></select>
        <select class="filter-select" id="qStatusFilter" onchange="loadQuestions()">
          <option value="">Barcha statuslar</option>
          <option value="answered">✅ Javob berilgan</option>
          <option value="unanswered">❓ Javobsiz</option>
        </select>
        <input class="search-inp" id="qSearch" placeholder="🔍 Qidirish..." oninput="filterQLocal()"/>
      </div>
      <div id="questionsList"><div class="loading">Yuklanmoqda...</div></div>
    </div>
    <div id="page-faculties" class="tab-page">
      <div class="page-header">
        <div><div class="page-title">Fakultetlar</div><div class="page-sub">CRUD boshqaruv</div></div>
        <button class="btn btn-primary" onclick="openFacultyModal()">+ Yangi fakultet</button>
      </div>
      <div id="facultiesList"><div class="loading">Yuklanmoqda...</div></div>
    </div>
    <div id="page-users" class="tab-page">
      <div class="page-header">
        <div><div class="page-title">Xodimlar</div><div class="page-sub">Telefon va parol bilan kirish</div></div>
        <button class="btn btn-primary" onclick="openUserModal()">+ Yangi xodim</button>
      </div>
      <div id="usersList"><div class="loading">Yuklanmoqda...</div></div>
    </div>
    <div id="page-faq" class="tab-page">
      <div class="page-header">
        <div><div class="page-title">FAQ Boshqaruv</div><div class="page-sub">Savol-javob qo\'shish</div></div>
      </div>
      <div class="faq-add-form">
        <div class="faq-add-title">Yangi savol-javob qo\'shish</div>
        <div class="form-row"><label class="form-label">Fakultet</label><select class="form-inp" id="faqFaculty"><option value="">Umumiy</option></select></div>
        <div class="form-row"><label class="form-label">Savol</label><input class="form-inp" id="faqQ" placeholder="Savol matni..."/></div>
        <div class="form-row"><label class="form-label">Javob</label><textarea class="form-inp" id="faqA" placeholder="Javob matni..."></textarea></div>
        <button class="btn btn-primary" onclick="addFAQ()">+ Qo\'shish</button>
      </div>
      <div id="faqList"><div class="loading">Yuklanmoqda...</div></div>
    </div>
    <div id="page-upload" class="tab-page">
      <div class="page-header">
        <div><div class="page-title">Hujjat Yuklash</div><div class="page-sub">AI bilimlari bazasini boyitish</div></div>
      </div>
      <div class="info-box">📁 **Qo\'llab-quvvatlanadigan formatlar:** PDF, DOCX, XLSX, TXT, MD.<br>Yuklangan hujjatlar avtomatik AI tomonidan o\'rganiladi va talabalar savollariga javob berishda foydalaniladi.</div>
      <div class="faq-add-form">
        <div class="faq-add-title">Fayl tanlang</div>
        <input type="file" id="kbFile" class="form-inp" style="margin-bottom:16px"/>
        <button class="btn btn-primary" onclick="uploadKB()">📤 Yuklash</button>
        <div id="uploadStatus" style="margin-top:12px;font-size:12px"></div>
      </div>
    </div>
  </div>
</div>
<div class="modal-bg" id="facultyModal">
  <div class="modal">
    <div class="modal-title" id="fModalTitle">Yangi fakultet</div>
    <input type="hidden" id="fModalId"/>
    <div class="form-row"><label class="form-label">Fakultet nomi *</label><input class="form-inp" id="fName" placeholder="Pedagogika fakulteti"/></div>
    <div class="form-row"><label class="form-label">Tavsif</label><input class="form-inp" id="fDesc" placeholder="Qisqacha tavsif..."/></div>
    <div class="form-row"><label class="form-label">Telegram guruh ID</label><input class="form-inp" id="fGroupId" placeholder="-100xxxxxxxxxx"/></div>
    <div class="form-row"><label class="form-label">Guruh nomi</label><input class="form-inp" id="fGroupName" placeholder="Guruh nomi"/></div>
    <div class="modal-actions">
      <button class="btn btn-red" onclick="closeModal(\'facultyModal\')">Bekor</button>
      <button class="btn btn-primary" onclick="saveFaculty()">Saqlash</button>
    </div>
  </div>
</div>
<div class="modal-bg" id="userModal">
  <div class="modal">
    <div class="modal-title">Yangi xodim</div>
    <div class="form-row"><label class="form-label">To\'liq ism *</label><input class="form-inp" id="uName" placeholder="Ism Familiya"/></div>
    <div class="form-row"><label class="form-label">Telefon raqami *</label><input class="form-inp" id="uPhone" placeholder="+998901234567"/></div>
    <div class="form-row"><label class="form-label">Parol *</label><input class="form-inp" type="password" id="uPass" placeholder="Kamida 6 belgi"/></div>
    <div class="form-row"><label class="form-label">Fakultet</label><select class="form-inp" id="uFaculty"><option value="">Tanlang...</option></select></div>
    <div class="form-row"><label class="form-label">Lavozim</label>
      <select class="form-inp" id="uRole"><option value="staff">Xodim</option><option value="dean">Dekan</option><option value="admin">Admin</option></select>
    </div>
    <div class="modal-actions">
      <button class="btn btn-red" onclick="closeModal(\'userModal\')">Bekor</button>
      <button class="btn btn-primary" onclick="saveUser()">Saqlash</button>
    </div>
  </div>
</div>
<div class="modal-bg" id="replyModal">
  <div class="modal">
    <div class="modal-title">Talabaga javob berish</div>
    <input type="hidden" id="replyQId"/>
    <div class="info-box" id="replyQText" style="border:none;background:var(--s2);margin-bottom:16px;max-height:120px;overflow-y:auto"></div>
    <div class="form-row"><label class="form-label">Sizning javobingiz *</label><textarea class="form-inp" id="replyAnswer" placeholder="Tushunarli va aniq javob yozing..."></textarea></div>
    <div class="modal-actions">
      <button class="btn btn-red" onclick="closeModal(\'replyModal\')">Bekor</button>
      <button class="btn btn-primary" id="btnSendReply" onclick="sendAnswer()">📤 Yuborish</button>
    </div>
  </div>
</div>
<script>
var actChartObj=null,langChartObj=null,allQuestions=[];

function esc(str) {
  if (!str) return "";
  return str.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// ── Auth Helper ──────────────────────────────────────────────────────────────
function getAuthHeaders() {
  const token = localStorage.getItem("admin_token");
  return {
    "Content-Type": "application/json",
    "Authorization": token ? "Bearer " + token : ""
  };
}

function apiFetch(url, options = {}) {
  options.headers = Object.assign(getAuthHeaders(), options.headers || {});
  return fetch(url, options).then(r => {
    if (r.status === 401) {
      doLogout();
      throw new Error("Unauthorized");
    }
    return r.json();
  });
}

function doLogin(){
  var u=document.getElementById("loginUser").value,p=document.getElementById("loginPass").value;
  fetch("/api/admin/auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:u,password:p})})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok && d.token){
      localStorage.setItem("admin_token", d.token);
      document.getElementById("loginWrap").style.display="none";
      document.getElementById("dash").style.display="block";
      loadOverview();
      loadFacultiesData();
    }
    else document.getElementById("loginErr").textContent="Login yoki parol noto'g'ri!";
  });
}

function doLogout(){
  localStorage.removeItem("admin_token");
  document.getElementById("loginWrap").style.display="flex";
  document.getElementById("dash").style.display="none";
}

window.onload = function() {
  if (localStorage.getItem("admin_token")) {
    document.getElementById("loginWrap").style.display="none";
    document.getElementById("dash").style.display="block";
    loadOverview();
    loadFacultiesData();
  }
};

function showPage(name,el){
  document.querySelectorAll(".tab-page").forEach(function(p){p.classList.remove("active");});
  document.querySelectorAll(".nav-item").forEach(function(n){n.classList.remove("active");});
  document.getElementById("page-"+name).classList.add("active");if(el)el.classList.add("active");
  if(name==="overview")loadOverview();if(name==="questions")loadQuestions();
  if(name==="faculties")loadFaculties();if(name==="users")loadUsers();
  if(name==="faq")loadFAQ();
}

function loadOverview(){
  apiFetch("/api/admin/stats").then(function(s){
    document.getElementById("statsGrid").innerHTML=
      "<div class='stat-card'><div class='stat-icon'>💬</div><div class='stat-num c-blue'>"+s.total+"</div><div class='stat-lbl'>Jami savollar</div></div>"+
      "<div class='stat-card'><div class='stat-icon'>✅</div><div class='stat-num c-green'>"+s.answered+"</div><div class='stat-lbl'>Javob berilgan</div></div>"+
      "<div class='stat-card'><div class='stat-icon'>❓</div><div class='stat-num c-red'>"+s.unanswered+"</div><div class='stat-lbl'>Javobsiz</div></div>"+
      "<div class='stat-card'><div class='stat-icon'>👤</div><div class='stat-num c-orange'>"+s.users+"</div><div class='stat-lbl'>Talabalar</div></div>"+
      "<div class='stat-card'><div class='stat-icon'>🏫</div><div class='stat-num c-purple'>"+s.faculties+"</div><div class='stat-lbl'>Fakultetlar</div></div>"+
      "<div class='stat-card'><div class='stat-icon'>👥</div><div class='stat-num c-blue'>"+s.staff+"</div><div class='stat-lbl'>Xodimlar</div></div>";
    var days=Object.keys(s.daily||{}),counts=Object.values(s.daily||{});
    if(actChartObj)actChartObj.destroy();
    actChartObj=new Chart(document.getElementById("actChart"),{type:"bar",
      data:{labels:days.map(function(d){return d.slice(5);}),datasets:[{data:counts,backgroundColor:"rgba(124,143,255,0.25)",borderColor:"#7c8fff",borderWidth:2,borderRadius:6}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{color:"rgba(255,255,255,0.04)"},ticks:{color:"#6b7299",font:{size:11}}},y:{grid:{color:"rgba(255,255,255,0.04)"},ticks:{color:"#6b7299",font:{size:11}}}}}});
    var langs=s.langs||{},lColors={uz:"#52d9a4",ru:"#ff6b6b",en:"#7c8fff"};
    if(langChartObj)langChartObj.destroy();
    langChartObj=new Chart(document.getElementById("langChart"),{type:"doughnut",
      data:{labels:Object.keys(langs),datasets:[{data:Object.values(langs),backgroundColor:Object.keys(langs).map(function(k){return lColors[k]||"#7c8fff";}),borderWidth:0}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom",labels:{color:"#8890b8",font:{size:11},padding:10}}}}});
  }).catch(e => console.error(e));
}

function loadQuestions(){
  var fId=document.getElementById("qFacultyFilter").value,status=document.getElementById("qStatusFilter").value;
  apiFetch("/api/admin/questions?limit=100"+(fId?"&faculty_id="+fId:"")+(status?"&status="+status:""))
  .then(function(d){allQuestions=d.questions||[];renderQuestions(allQuestions);});
}

function filterQLocal(){
  var q=document.getElementById("qSearch").value.toLowerCase();
  if(!q){renderQuestions(allQuestions);return;}
  renderQuestions(allQuestions.filter(function(i){return i.question.toLowerCase().includes(q)||(i.student_username||"").toLowerCase().includes(q);}));
}

function renderQuestions(items){
  var c=document.getElementById("questionsList");
  if(!items.length){c.innerHTML="<div class='empty'>Hech qanday savol yo'q</div>";return;}
  c.innerHTML="<div class='table-card'><table><thead><tr><th>Talaba</th><th>Fakultet</th><th>Savol</th><th>Til</th><th>Status</th><th>Boshqaruv</th></tr></thead><tbody>"+
  items.map(function(q){
    var student = q.student_username ? "@" + q.student_username : (q.student_name || "—");
    var qTextEsc = esc(q.question);
    var btn = q.status !== "answered" ? `<button class="btn btn-sm btn-blue" onclick="openReplyModal(${q.id}, '${qTextEsc}')">Javob berish</button>` : "—";
    return `<tr><td><strong>${esc(student)}</strong></td><td><span class="badge badge-purple">${esc(q.faculty_name || "Umumiy")}</span></td><td style="max-width:260px;color:var(--muted2)">${esc(q.question)}</td><td><span class="badge ${lm[q.lang] || "badge-blue"}">${(q.lang || "uz").toUpperCase()}</span></td><td><span class="badge ${q.status === "answered" ? "badge-green" : "badge-red"}">${q.status === "answered" ? "✅ Javob berilgan" : "❓ Javobsiz"}</span></td><td>${btn}</td></tr>`;
  }).join("")+"</tbody></table></div>";
}

function openReplyModal(qid, qText) {
    document.getElementById("replyQId").value = qid;
    // qText comes in escaped for the attribute, but we want it clean for the textContent
    var div = document.createElement("div"); div.innerHTML = qText;
    document.getElementById("replyQText").textContent = div.textContent;
    document.getElementById("replyAnswer").value = "";
    document.getElementById("replyModal").classList.add("open");
}

function sendAnswer() {
    var qid = document.getElementById("replyQId").value;
    var ans = document.getElementById("replyAnswer").value.strip();
    if(!ans) { alert("Javob yozing!"); return; }
    
    var btn = document.getElementById("btnSendReply");
    btn.disabled = true; btn.textContent = "Yuborilmoqda...";
    
    apiFetch("/api/admin/questions/" + qid + "/answer", {
        method: "POST",
        body: JSON.stringify({answer: ans})
    }).then(d => {
        btn.disabled = false; btn.textContent = "📤 Yuborish";
        if(d.ok) {
            closeModal("replyModal");
            loadQuestions();
            loadOverview();
        } else {
            alert("Xatolik: " + d.error);
        }
    }).catch(e => {
        btn.disabled = false; btn.textContent = "📤 Yuborish";
        alert("Xato: " + e.message);
    });
}

var cachedFaculties=[];
function loadFacultiesData(){
  apiFetch("/api/admin/faculties").then(function(d){
    cachedFaculties=d.faculties||[];
    ["qFacultyFilter","faqFaculty","uFaculty"].forEach(function(id){
      var el=document.getElementById(id);if(!el)return;
      var first=el.options[0];el.innerHTML="";el.appendChild(first);
      cachedFaculties.forEach(function(f){var o=document.createElement("option");o.value=f.id;o.textContent=f.name;el.appendChild(o);});
    });
  });
}

function loadFaculties(){
  loadFacultiesData();
  apiFetch("/api/admin/faculties").then(function(d){
    var items=d.faculties||[],c=document.getElementById("facultiesList");
    if(!items.length){c.innerHTML="<div class='empty'>Fakultetlar yo'q</div>";return;}
    c.innerHTML="<div class='table-card'><table><thead><tr><th>Nomi</th><th>Tavsif</th><th>Telegram guruh</th><th>Status</th><th>Amallar</th></tr></thead><tbody>"+
    items.map(function(f){
      var fEsc = esc(JSON.stringify(f));
      return `<tr><td><strong>${esc(f.name)}</strong></td><td style="color:var(--muted2)">${esc(f.description || "—")}</td><td style="font-size:12px;color:var(--accent)">${esc(f.telegram_group_name || f.telegram_group_id || "—")}</td><td><span class="badge ${f.is_active ? "badge-green" : "badge-red"}">${f.is_active ? "Faol" : "Nofaol"}</span></td><td style="display:flex;gap:6px"><button class="btn btn-sm btn-blue" onclick="editFaculty('${fEsc}')">Tahrir</button><button class="btn btn-sm btn-red" onclick="deleteFaculty(${f.id})">O'chir</button></td></tr>`;
    }).join("")+"</tbody></table></div>";
  });
}

function editFaculty(fJsonEsc) {
  var div = document.createElement("div"); div.innerHTML = fJsonEsc;
  var f = JSON.parse(div.textContent);
  openFacultyModal(f);
}

function openFacultyModal(f){
  document.getElementById("fModalTitle").textContent=f?"Tahrirlash":"Yangi fakultet";
  document.getElementById("fModalId").value=f?f.id:"";
  document.getElementById("fName").value=f?f.name:"";
  document.getElementById("fDesc").value=f?(f.description||""):"";
  document.getElementById("fGroupId").value=f?(f.telegram_group_id||""):"";
  document.getElementById("fGroupName").value=f?(f.telegram_group_name||""):"";
  document.getElementById("facultyModal").classList.add("open");
}

function editFaculty(f){openFacultyModal(f);}

function saveFaculty(){
  var id=document.getElementById("fModalId").value;
  var data={name:document.getElementById("fName").value,description:document.getElementById("fDesc").value,group_id:document.getElementById("fGroupId").value,group_name:document.getElementById("fGroupName").value};
  if(!data.name){alert("Nomi kiritish shart!");return;}
  apiFetch(id?"/api/admin/faculties/"+id:"/api/admin/faculties",{method:id?"PUT":"POST",body:JSON.stringify(data)})
  .then(function(d){if(d.ok){closeModal("facultyModal");loadFaculties();}else alert(d.error||"Xatolik");});
}

function deleteFaculty(id){if(!confirm("O'chirasizmi?"))return;apiFetch("/api/admin/faculties/"+id,{method:"DELETE"}).then(function(){loadFaculties();});}

function loadUsers(){
  apiFetch("/api/admin/users").then(function(d){
    var items=d.users||[],c=document.getElementById("usersList");
    if(!items.length){c.innerHTML="<div class='empty'>Xodimlar yo'q</div>";return;}
    c.innerHTML="<div class='table-card'><table><thead><tr><th>Ism</th><th>Telefon</th><th>Fakultet</th><th>Lavozim</th><th>Status</th><th></th></tr></thead><tbody>"+
    items.map(function(u){return "<tr><td><strong>"+u.full_name+"</strong></td><td style='font-family:monospace;font-size:12px'>"+u.phone+"</td><td><span class='badge badge-purple'>"+(u.faculty_name||"—")+"</span></td><td><span class='badge badge-blue'>"+u.role+"</span></td><td><span class='badge "+(u.is_active?"badge-green":"badge-red")+"'>"+(u.is_active?"Faol":"Nofaol")+"</span></td><td><button class='btn btn-sm btn-red' onclick='deleteUser("+u.id+")'>O'chir</button></td></tr>";}).join("")+"</tbody></table></div>";
  });
}

function openUserModal(){document.getElementById("uName").value="";document.getElementById("uPhone").value="";document.getElementById("uPass").value="";document.getElementById("userModal").classList.add("open");}

function saveUser(){
  var data={full_name:document.getElementById("uName").value,phone:document.getElementById("uPhone").value,password:document.getElementById("uPass").value,faculty_id:document.getElementById("uFaculty").value||null,role:document.getElementById("uRole").value};
  if(!data.full_name||!data.phone||!data.password){alert("Barcha maydonlarni to'ldiring!");return;}
  apiFetch("/api/admin/users",{method:"POST",body:JSON.stringify(data)})
  .then(function(d){if(d.ok){closeModal("userModal");loadUsers();}else alert(d.error||"Xatolik");});
}

function deleteUser(id){if(!confirm("O'chirasizmi?"))return;apiFetch("/api/admin/users/"+id,{method:"DELETE"}).then(function(){loadUsers();});}

function loadFAQ(){
  apiFetch("/api/admin/faq").then(function(d){
    var items=d.items||[],c=document.getElementById("faqList");
    if(!items.length){c.innerHTML="<div class='empty'>FAQ bo'sh</div>";return;}
    c.innerHTML="<div class='table-card'><table><thead><tr><th>Fakultet</th><th>Savol</th><th>Javob</th><th></th></tr></thead><tbody>"+
    items.map(function(f){return "<tr><td><span class='badge badge-purple'>"+(f.faculty_name||"Umumiy")+"</span></td><td style='font-weight:500'>"+f.question+"</td><td style='color:var(--muted2);max-width:240px'>"+f.answer.slice(0,80)+(f.answer.length>80?"...":"")+"</td><td><button class='btn btn-sm btn-red' onclick='deleteFAQ("+f.id+")'>O'chir</button></td></tr>";}).join("")+"</tbody></table></div>";
  });
}

function addFAQ(){
  var data={faculty_id:document.getElementById("faqFaculty").value||null,question:document.getElementById("faqQ").value,answer:document.getElementById("faqA").value};
  if(!data.question||!data.answer){alert("Savol va javob kiritish shart!");return;}
  apiFetch("/api/admin/faq",{method:"POST",body:JSON.stringify(data)})
  .then(function(d){if(d.ok){document.getElementById("faqQ").value="";document.getElementById("faqA").value="";loadFAQ();}else alert(d.error||"Xatolik");});
}

function deleteFAQ(id){if(!confirm("O'chirasizmi?"))return;apiFetch("/api/admin/faq/"+id,{method:"DELETE"}).then(function(){loadFAQ();});}

function uploadKB() {
    var f = document.getElementById("kbFile").files[0];
    if(!f) { alert("Fayl tanlang!"); return; }
    var fd = new FormData(); fd.append("file", f);
    var status = document.getElementById("uploadStatus");
    status.textContent = "⏳ Yuklanmoqda...";
    fetch("/api/upload", {
        method: "POST",
        headers: {"Authorization": "Bearer " + localStorage.getItem("admin_token")},
        body: fd
    }).then(r => r.json()).then(d => {
        if(d.ok) status.textContent = "✅ Yuklandi: " + d.filename + " (" + d.pairs + " Q&A)";
        else status.textContent = "❌ Xatolik: " + d.error;
    });
}

function closeModal(id){document.getElementById(id).classList.remove("open");}

if(!String.prototype.strip) { String.prototype.strip = function() { return this.replace(/^\s+|\s+$/g, ""); }; }
</script>
</body>
</html>'''