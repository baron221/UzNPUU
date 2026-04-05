def get_admin_html():
    return '''<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>OʻzMPU Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#f0f4ff;
  --bg2:#e8eeff;
  --surface:#ffffff;
  --surface2:#f7f9ff;
  --border:#e2e8f8;
  --border2:#c7d2f0;
  --accent:#4f6ef7;
  --accent-light:#eef1ff;
  --accent2:#f97316;
  --accent2-light:#fff7ed;
  --accent3:#10b981;
  --accent3-light:#ecfdf5;
  --red:#ef4444;
  --red-light:#fef2f2;
  --purple:#8b5cf6;
  --purple-light:#f5f3ff;
  --text:#1e293b;
  --text2:#475569;
  --text3:#94a3b8;
  --shadow:0 1px 3px rgba(79,110,247,0.08),0 4px 16px rgba(79,110,247,0.06);
  --shadow2:0 4px 24px rgba(79,110,247,0.12);
  --r:14px;--r2:10px;--r3:8px;
}
body{background:var(--bg);color:var(--text);font-family:"Plus Jakarta Sans",sans-serif;min-height:100vh;font-size:14px}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-thumb{background:var(--border2);border-radius:99px}

/* ── LOGIN ── */
.login-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;
  background:linear-gradient(135deg,#667eea 0%,#764ba2 100%)}
.login-card{background:var(--surface);border-radius:24px;padding:40px;width:100%;max-width:420px;
  box-shadow:0 20px 60px rgba(0,0,0,0.15);text-align:center}
.login-logo{width:64px;height:64px;background:linear-gradient(135deg,var(--accent),#6366f1);border-radius:18px;
  display:flex;align-items:center;justify-content:center;font-size:28px;margin:0 auto 20px}
.login-title{font-family:"Playfair Display",serif;font-size:26px;color:var(--text);margin-bottom:6px}
.login-sub{font-size:13px;color:var(--text3);margin-bottom:28px}
.inp{width:100%;background:var(--bg);border:1.5px solid var(--border);border-radius:var(--r2);
  padding:12px 16px;color:var(--text);font-family:"Plus Jakarta Sans",sans-serif;font-size:14px;
  outline:none;margin-bottom:12px;transition:all 0.2s}
.inp:focus{border-color:var(--accent);background:var(--surface);box-shadow:0 0 0 3px rgba(79,110,247,0.1)}
.inp::placeholder{color:var(--text3)}
.btn-login{width:100%;background:linear-gradient(135deg,var(--accent),#6366f1);border:none;border-radius:var(--r2);
  padding:13px;color:#fff;font-family:"Plus Jakarta Sans",sans-serif;font-size:14px;font-weight:600;
  cursor:pointer;transition:all 0.2s;box-shadow:0 4px 12px rgba(79,110,247,0.3)}
.btn-login:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(79,110,247,0.4)}
.err{font-size:12px;color:var(--red);margin-top:10px;min-height:18px}

/* ── LAYOUT ── */
.dash{display:none}
.sidebar{position:fixed;left:0;top:0;bottom:0;width:240px;background:var(--surface);
  border-right:1px solid var(--border);padding:0;z-index:100;overflow-y:auto;
  box-shadow:2px 0 12px rgba(79,110,247,0.06)}
.sidebar-top{padding:24px 20px;border-bottom:1px solid var(--border);
  background:linear-gradient(135deg,var(--accent),#6366f1)}
.sidebar-logo-box{width:40px;height:40px;background:rgba(255,255,255,0.2);border-radius:10px;
  display:flex;align-items:center;justify-content:center;font-size:18px;margin-bottom:12px}
.sidebar-title{font-family:"Playfair Display",serif;font-size:18px;font-weight:700;color:#fff}
.sidebar-sub{font-size:11px;color:rgba(255,255,255,0.7);margin-top:2px}
.nav-section{font-size:10px;letter-spacing:2px;color:var(--text3);padding:20px 20px 8px;text-transform:uppercase;font-weight:600}
.nav-item{display:flex;align-items:center;gap:12px;padding:11px 20px;cursor:pointer;
  color:var(--text2);font-size:13px;font-weight:500;transition:all 0.2s;
  border-left:3px solid transparent;margin:2px 0}
.nav-item:hover{color:var(--accent);background:var(--accent-light)}
.nav-item.active{color:var(--accent);background:var(--accent-light);border-left-color:var(--accent);font-weight:600}
.nav-icon{font-size:17px;width:22px;text-align:center}
.nav-bottom{position:absolute;bottom:0;left:0;right:0;padding:16px 20px;border-top:1px solid var(--border)}
.logout-btn{width:100%;background:var(--red-light);border:1px solid rgba(239,68,68,0.2);border-radius:var(--r3);
  padding:10px;color:var(--red);font-family:"Plus Jakarta Sans",sans-serif;font-size:13px;
  font-weight:500;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;justify-content:center;gap:8px}
.logout-btn:hover{background:rgba(239,68,68,0.15)}

.content{margin-left:240px;padding:28px;min-height:100vh}
.page-header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px}
.page-title{font-family:"Playfair Display",serif;font-size:26px;font-weight:700;color:var(--text)}
.page-sub{font-size:13px;color:var(--text3);margin-top:4px}

/* ── STAT CARDS ── */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:24px}
.stat-card{background:var(--surface);border-radius:var(--r);padding:20px;box-shadow:var(--shadow);
  border:1px solid var(--border);position:relative;overflow:hidden;transition:transform 0.2s}
.stat-card:hover{transform:translateY(-2px);box-shadow:var(--shadow2)}
.stat-card::after{content:"";position:absolute;top:-20px;right:-20px;width:80px;height:80px;border-radius:50%;opacity:0.08}
.stat-card.blue::after{background:var(--accent)}
.stat-card.green::after{background:var(--accent3)}
.stat-card.red::after{background:var(--red)}
.stat-card.orange::after{background:var(--accent2)}
.stat-card.purple::after{background:var(--purple)}
.stat-icon-wrap{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;margin-bottom:14px}
.stat-card.blue .stat-icon-wrap{background:var(--accent-light)}
.stat-card.green .stat-icon-wrap{background:var(--accent3-light)}
.stat-card.red .stat-icon-wrap{background:var(--red-light)}
.stat-card.orange .stat-icon-wrap{background:var(--accent2-light)}
.stat-card.purple .stat-icon-wrap{background:var(--purple-light)}
.stat-num{font-family:"Playfair Display",serif;font-size:30px;font-weight:700;line-height:1;margin-bottom:4px}
.stat-card.blue .stat-num{color:var(--accent)}
.stat-card.green .stat-num{color:var(--accent3)}
.stat-card.red .stat-num{color:var(--red)}
.stat-card.orange .stat-num{color:var(--accent2)}
.stat-card.purple .stat-num{color:var(--purple)}
.stat-lbl{font-size:12px;color:var(--text3);font-weight:500}

/* ── CHARTS ── */
.charts-grid{display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-bottom:24px}
@media(max-width:900px){.charts-grid{grid-template-columns:1fr}}
.chart-card{background:var(--surface);border-radius:var(--r);padding:20px;box-shadow:var(--shadow);border:1px solid var(--border)}
.chart-title{font-size:13px;font-weight:600;color:var(--text2);margin-bottom:16px;letter-spacing:0.3px}
.chart-wrap{position:relative;height:200px}

/* ── TABLE ── */
.table-card{background:var(--surface);border-radius:var(--r);box-shadow:var(--shadow);border:1px solid var(--border);overflow:hidden;margin-bottom:16px}
.table-header{padding:16px 20px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)}
.table-title{font-size:14px;font-weight:600;color:var(--text)}
table{width:100%;border-collapse:collapse}
th{padding:11px 16px;text-align:left;font-size:11px;letter-spacing:0.8px;text-transform:uppercase;
  color:var(--text3);border-bottom:1px solid var(--border);background:var(--bg);font-weight:600}
td{padding:13px 16px;font-size:13px;border-bottom:1px solid var(--border);color:var(--text)}
tr:last-child td{border-bottom:none}
tr:hover td{background:var(--accent-light)}

/* ── BADGES ── */
.badge{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:99px;font-size:11px;font-weight:600}
.badge-green{background:var(--accent3-light);color:var(--accent3)}
.badge-red{background:var(--red-light);color:var(--red)}
.badge-blue{background:var(--accent-light);color:var(--accent)}
.badge-orange{background:var(--accent2-light);color:var(--accent2)}
.badge-purple{background:var(--purple-light);color:var(--purple)}

/* ── BUTTONS ── */
.btn{padding:8px 16px;border-radius:var(--r3);border:none;cursor:pointer;
  font-family:"Plus Jakarta Sans",sans-serif;font-size:13px;font-weight:600;transition:all 0.2s}
.btn-sm{padding:6px 12px;font-size:12px}
.btn-primary{background:linear-gradient(135deg,var(--accent),#6366f1);color:#fff;box-shadow:0 2px 8px rgba(79,110,247,0.25)}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 4px 14px rgba(79,110,247,0.35)}
.btn-blue{background:var(--accent-light);color:var(--accent);border:1px solid rgba(79,110,247,0.2)}
.btn-blue:hover{background:rgba(79,110,247,0.15)}
.btn-red{background:var(--red-light);color:var(--red);border:1px solid rgba(239,68,68,0.2)}
.btn-red:hover{background:rgba(239,68,68,0.15)}
.btn-green{background:var(--accent3-light);color:var(--accent3);border:1px solid rgba(16,185,129,0.2)}
.btn-green:hover{background:rgba(16,185,129,0.15)}

/* ── MODAL ── */
.modal-bg{display:none;position:fixed;inset:0;background:rgba(15,23,42,0.5);z-index:1000;
  align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(4px)}
.modal-bg.open{display:flex}
.modal{background:var(--surface);border-radius:20px;padding:28px;width:100%;max-width:500px;
  max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2)}
.modal-title{font-family:"Playfair Display",serif;font-size:22px;color:var(--text);margin-bottom:22px}
.form-row{margin-bottom:16px}
.form-label{font-size:12px;color:var(--text2);margin-bottom:6px;display:block;font-weight:600;letter-spacing:0.3px}
.form-inp{width:100%;background:var(--bg);border:1.5px solid var(--border);border-radius:var(--r3);
  padding:10px 14px;color:var(--text);font-family:"Plus Jakarta Sans",sans-serif;font-size:13px;
  outline:none;transition:all 0.2s}
.form-inp:focus{border-color:var(--accent);background:var(--surface);box-shadow:0 0 0 3px rgba(79,110,247,0.08)}
.form-inp::placeholder{color:var(--text3)}
select.form-inp option{background:var(--surface)}
.modal-actions{display:flex;gap:10px;margin-top:22px;justify-content:flex-end}
textarea.form-inp{resize:vertical;min-height:90px}

/* ── FILTERS ── */
.filter-row{display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;align-items:center}
.filter-select,.search-inp{background:var(--surface);border:1.5px solid var(--border);border-radius:var(--r3);
  padding:8px 14px;color:var(--text);font-family:"Plus Jakarta Sans",sans-serif;font-size:13px;
  outline:none;transition:all 0.2s}
.filter-select:focus,.search-inp:focus{border-color:var(--accent)}
.search-inp{min-width:220px}
.search-inp::placeholder{color:var(--text3)}

/* ── FAQ FORM ── */
.faq-add-form{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
  padding:20px;margin-bottom:20px;box-shadow:var(--shadow)}
.faq-add-title{font-size:13px;font-weight:600;color:var(--text2);margin-bottom:16px}

/* ── INFO BOX ── */
.info-box{background:var(--accent-light);border:1px solid rgba(79,110,247,0.2);border-radius:var(--r);
  padding:16px 20px;margin-bottom:20px;font-size:13px;color:var(--text2);line-height:1.7}

.empty{text-align:center;padding:48px;color:var(--text3);font-size:13px}
.loading{text-align:center;padding:32px;color:var(--text3);font-size:13px}

.tab-page{display:none}.tab-page.active{display:block}
</style>
</head>
<body>

<!-- LOGIN -->
<div class="login-wrap" id="loginWrap">
  <div class="login-card">
    <div class="login-logo">🎓</div>
    <div class="login-title">Admin Panel</div>
    <div class="login-sub">OʻzMPU Bot boshqaruv tizimi</div>
    <input class="inp" type="text" id="loginUser" placeholder="Login"/>
    <input class="inp" type="password" id="loginPass" placeholder="Parol" onkeydown="if(event.key==='Enter')doLogin()"/>
    <button class="btn-login" onclick="doLogin()">Kirish →</button>
    <div class="err" id="loginErr"></div>
  </div>
</div>

<!-- DASHBOARD -->
<div class="dash" id="dash">
  <div class="sidebar">
    <div class="sidebar-top">
      <div class="sidebar-logo-box">🎓</div>
      <div class="sidebar-title">OʻzMPU</div>
      <div class="sidebar-sub">Admin boshqaruv paneli</div>
    </div>
    <div class="nav-section">Asosiy</div>
    <div class="nav-item active" onclick="showPage('overview',this)"><span class="nav-icon">📊</span>Umumiy ko'rinish</div>
    <div class="nav-item" onclick="showPage('questions',this)"><span class="nav-icon">💬</span>Savollar</div>
    <div class="nav-section">Boshqaruv</div>
    <div class="nav-item" onclick="showPage('faculties',this)"><span class="nav-icon">🏫</span>Fakultetlar</div>
    <div class="nav-item" onclick="showPage('users',this)"><span class="nav-icon">👥</span>Xodimlar</div>
    <div class="nav-section">Kontent</div>
    <div class="nav-item" onclick="showPage('faq',this)"><span class="nav-icon">📋</span>FAQ Boshqaruv</div>
    <div class="nav-item" onclick="showPage('chatgroups',this)"><span class="nav-icon">📡</span>Telegram Guruhlar</div>
    <div class="nav-bottom">
      <button class="logout-btn" onclick="doLogout()">🚪 Chiqish</button>
    </div>
  </div>

  <div class="content">

    <!-- OVERVIEW -->
    <div id="page-overview" class="tab-page active">
      <div class="page-header">
        <div><div class="page-title">Umumiy ko'rinish</div><div class="page-sub">Barcha statistikalar bir joyda</div></div>
        <button class="btn btn-blue" onclick="loadOverview()">↻ Yangilash</button>
      </div>
      <div class="stats-grid" id="statsGrid"><div class="loading">Yuklanmoqda...</div></div>
      <div class="charts-grid">
        <div class="chart-card"><div class="chart-title">📈 So\'nggi 7 kun faolligi</div><div class="chart-wrap"><canvas id="actChart"></canvas></div></div>
        <div class="chart-card"><div class="chart-title">🌍 Til taqsimoti</div><div class="chart-wrap"><canvas id="langChart"></canvas></div></div>
      </div>
    </div>

    <!-- QUESTIONS -->
    <div id="page-questions" class="tab-page">
      <div class="page-header">
        <div><div class="page-title">Savollar</div><div class="page-sub">Talabalar yuborgan barcha savollar</div></div>
        <button class="btn btn-blue" onclick="loadQuestions()">↻ Yangilash</button>
      </div>
      <div class="filter-row">
        <select class="filter-select" id="qFacultyFilter" onchange="loadQuestions()">
          <option value="">Barcha fakultetlar</option>
        </select>
        <select class="filter-select" id="qStatusFilter" onchange="loadQuestions()">
          <option value="">Barcha statuslar</option>
          <option value="answered">✅ Javob berilgan</option>
          <option value="unanswered">❓ Javobsiz</option>
        </select>
        <input class="search-inp" id="qSearch" placeholder="🔍 Qidirish..." oninput="filterQLocal()"/>
      </div>
      <div id="questionsList"><div class="loading">Yuklanmoqda...</div></div>
    </div>

    <!-- FACULTIES -->
    <div id="page-faculties" class="tab-page">
      <div class="page-header">
        <div><div class="page-title">Fakultetlar</div><div class="page-sub">Qo\'shish, tahrirlash, o\'chirish</div></div>
        <button class="btn btn-primary" onclick="openFacultyModal()">+ Yangi fakultet</button>
      </div>
      <div id="facultiesList"><div class="loading">Yuklanmoqda...</div></div>
    </div>

    <!-- USERS -->
    <div id="page-users" class="tab-page">
      <div class="page-header">
        <div><div class="page-title">Xodimlar</div><div class="page-sub">Telefon raqami va parol bilan kirish</div></div>
        <button class="btn btn-primary" onclick="openUserModal()">+ Yangi xodim</button>
      </div>
      <div id="usersList"><div class="loading">Yuklanmoqda...</div></div>
    </div>

    <!-- FAQ -->
    <div id="page-faq" class="tab-page">
      <div class="page-header">
        <div><div class="page-title">FAQ Boshqaruv</div><div class="page-sub">Savol-javoblarni qo\'shish va boshqarish</div></div>
      </div>
      <div class="faq-add-form">
        <div class="faq-add-title">✍️ Yangi savol-javob qo\'shish</div>
        <div class="form-row">
          <label class="form-label">Fakultet</label>
          <select class="form-inp" id="faqFaculty"><option value="">Umumiy (barcha uchun)</option></select>
        </div>
        <div class="form-row">
          <label class="form-label">Savol</label>
          <input class="form-inp" id="faqQ" placeholder="Savol matni..."/>
        </div>
        <div class="form-row">
          <label class="form-label">Javob</label>
          <textarea class="form-inp" id="faqA" placeholder="Javob matni..."></textarea>
        </div>
        <button class="btn btn-primary" onclick="addFAQ()">+ Qo\'shish</button>
      </div>
      <div id="faqList"><div class="loading">Yuklanmoqda...</div></div>
    </div>

    <!-- CHAT GROUPS -->
    <div id="page-chatgroups" class="tab-page">
      <div class="page-header">
        <div><div class="page-title">Telegram Guruhlar</div><div class="page-sub">Savollar avtomatik guruhga yuboriladi</div></div>
      </div>
      <div class="info-box">
        💡 <strong>Qanday ishlaydi:</strong><br>
        1. Botni Telegram guruhingizga <strong>admin</strong> sifatida qo\'shing<br>
        2. Guruh ID sini pastdagi tegishli fakultet uchun kiriting<br>
        3. Talaba savol yuborganda — guruhga avtomatik xabar ketadi 🚀
      </div>
      <div id="chatGroupsList"><div class="loading">Yuklanmoqda...</div></div>
    </div>

  </div>
</div>

<!-- FACULTY MODAL -->
<div class="modal-bg" id="facultyModal">
  <div class="modal">
    <div class="modal-title" id="fModalTitle">Yangi fakultet</div>
    <input type="hidden" id="fModalId"/>
    <div class="form-row"><label class="form-label">Fakultet nomi *</label><input class="form-inp" id="fName" placeholder="Masalan: Pedagogika fakulteti"/></div>
    <div class="form-row"><label class="form-label">Tavsif</label><input class="form-inp" id="fDesc" placeholder="Qisqacha tavsif..."/></div>
    <div class="form-row"><label class="form-label">Telegram guruh ID</label><input class="form-inp" id="fGroupId" placeholder="-100xxxxxxxxxx"/></div>
    <div class="form-row"><label class="form-label">Guruh nomi</label><input class="form-inp" id="fGroupName" placeholder="Pedagogika guruh"/></div>
    <div class="modal-actions">
      <button class="btn btn-red" onclick="closeModal(\'facultyModal\')">Bekor qilish</button>
      <button class="btn btn-primary" onclick="saveFaculty()">💾 Saqlash</button>
    </div>
  </div>
</div>

<!-- USER MODAL -->
<div class="modal-bg" id="userModal">
  <div class="modal">
    <div class="modal-title" id="uModalTitle">Yangi xodim</div>
    <input type="hidden" id="uModalId"/>
    <div class="form-row"><label class="form-label">To\'liq ism *</label><input class="form-inp" id="uName" placeholder="Ism Familiya Sharif"/></div>
    <div class="form-row"><label class="form-label">Telefon raqami *</label><input class="form-inp" id="uPhone" placeholder="+998901234567"/></div>
    <div class="form-row"><label class="form-label">Parol *</label><input class="form-inp" type="password" id="uPass" placeholder="Kamida 6 ta belgi"/></div>
    <div class="form-row"><label class="form-label">Fakultet</label>
      <select class="form-inp" id="uFaculty"><option value="">Tanlang...</option></select>
    </div>
    <div class="form-row"><label class="form-label">Lavozim</label>
      <select class="form-inp" id="uRole">
        <option value="staff">Xodim</option>
        <option value="dean">Dekan</option>
        <option value="admin">Admin</option>
      </select>
    </div>
    <div class="modal-actions">
      <button class="btn btn-red" onclick="closeModal(\'userModal\')">Bekor qilish</button>
      <button class="btn btn-primary" onclick="saveUser()">💾 Saqlash</button>
    </div>
  </div>
</div>

<script>
var actChartObj=null,langChartObj=null,allQuestions=[];

async function api(path,method,body){
  var opts={method:method||"GET",headers:{"Content-Type":"application/json"}};
  if(body) opts.body=JSON.stringify(body);
  var r=await fetch("/api/admin"+path,opts);
  return r.json();
}

function doLogin(){
  var u=document.getElementById("loginUser").value;
  var p=document.getElementById("loginPass").value;
  fetch("/api/admin/auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:u,password:p})})
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.ok){
      document.getElementById("loginWrap").style.display="none";
      document.getElementById("dash").style.display="block";
      loadOverview();loadFacultiesData();
    }else{document.getElementById("loginErr").textContent="Login yoki parol noto\'g\'ri!";}
  });
}

function doLogout(){
  document.getElementById("loginWrap").style.display="flex";
  document.getElementById("dash").style.display="none";
}

function showPage(name,el){
  document.querySelectorAll(".tab-page").forEach(function(p){p.classList.remove("active");});
  document.querySelectorAll(".nav-item").forEach(function(n){n.classList.remove("active");});
  document.getElementById("page-"+name).classList.add("active");
  if(el) el.classList.add("active");
  if(name==="overview") loadOverview();
  if(name==="questions") loadQuestions();
  if(name==="faculties") loadFaculties();
  if(name==="users") loadUsers();
  if(name==="faq") loadFAQ();
  if(name==="chatgroups") loadChatGroups();
}

function loadOverview(){
  fetch("/api/admin/stats").then(function(r){return r.json();}).then(function(s){
    document.getElementById("statsGrid").innerHTML=
      "<div class='stat-card blue'><div class='stat-icon-wrap'>💬</div><div class='stat-num'>"+s.total+"</div><div class='stat-lbl'>Jami savollar</div></div>"+
      "<div class='stat-card green'><div class='stat-icon-wrap'>✅</div><div class='stat-num'>"+s.answered+"</div><div class='stat-lbl'>Javob berilgan</div></div>"+
      "<div class='stat-card red'><div class='stat-icon-wrap'>❓</div><div class='stat-num'>"+s.unanswered+"</div><div class='stat-lbl'>Javobsiz</div></div>"+
      "<div class='stat-card orange'><div class='stat-icon-wrap'>👤</div><div class='stat-num'>"+s.users+"</div><div class='stat-lbl'>Talabalar</div></div>"+
      "<div class='stat-card purple'><div class='stat-icon-wrap'>🏫</div><div class='stat-num'>"+s.faculties+"</div><div class='stat-lbl'>Fakultetlar</div></div>"+
      "<div class='stat-card blue'><div class='stat-icon-wrap'>👥</div><div class='stat-num'>"+s.staff+"</div><div class='stat-lbl'>Xodimlar</div></div>";

    var days=Object.keys(s.daily||{});
    var counts=Object.values(s.daily||{});
    if(actChartObj) actChartObj.destroy();
    actChartObj=new Chart(document.getElementById("actChart"),{
      type:"bar",
      data:{labels:days.map(function(d){return d.slice(5);}),
        datasets:[{data:counts,backgroundColor:"rgba(79,110,247,0.15)",borderColor:"rgba(79,110,247,0.8)",
          borderWidth:2,borderRadius:8,borderSkipped:false}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
        scales:{x:{grid:{display:false},ticks:{color:"#94a3b8",font:{size:11,family:"Plus Jakarta Sans"}}},
                y:{grid:{color:"rgba(0,0,0,0.05)"},ticks:{color:"#94a3b8",font:{size:11,family:"Plus Jakarta Sans"}}}}}
    });

    var langs=s.langs||{};
    var lColors={uz:"#10b981",ru:"#ef4444",en:"#4f6ef7"};
    if(langChartObj) langChartObj.destroy();
    langChartObj=new Chart(document.getElementById("langChart"),{
      type:"doughnut",
      data:{labels:Object.keys(langs).map(function(l){return l.toUpperCase();}),
        datasets:[{data:Object.values(langs),backgroundColor:Object.keys(langs).map(function(k){return lColors[k]||"#4f6ef7";}),
          borderWidth:3,borderColor:"#ffffff"}]},
      options:{responsive:true,maintainAspectRatio:false,
        plugins:{legend:{position:"bottom",labels:{color:"#475569",font:{size:12,family:"Plus Jakarta Sans"},padding:16}}}}
    });
  });
}

function loadQuestions(){
  var fId=document.getElementById("qFacultyFilter").value;
  var status=document.getElementById("qStatusFilter").value;
  var url="/api/admin/questions?limit=100"+(fId?"&faculty_id="+fId:"")+(status?"&status="+status:"");
  fetch(url).then(function(r){return r.json();}).then(function(d){
    allQuestions=d.questions||[];renderQuestions(allQuestions);
  });
}

function filterQLocal(){
  var q=document.getElementById("qSearch").value.toLowerCase();
  if(!q){renderQuestions(allQuestions);return;}
  renderQuestions(allQuestions.filter(function(i){
    return i.question.toLowerCase().includes(q)||(i.student_username||"").toLowerCase().includes(q);
  }));
}

function renderQuestions(items){
  var c=document.getElementById("questionsList");
  if(!items.length){c.innerHTML="<div class='empty'>😕 Hech qanday savol yo\'q</div>";return;}
  c.innerHTML="<div class='table-card'><table><thead><tr><th>Talaba</th><th>Fakultet</th><th>Savol</th><th>Til</th><th>Status</th><th>Vaqt</th></tr></thead><tbody>"+
  items.map(function(q){
    var langBadge={uz:"badge-green",ru:"badge-red",en:"badge-blue"};
    return "<tr><td><strong>@"+(q.student_username||"—")+"</strong><br><span style='font-size:11px;color:#94a3b8'>"+(q.student_name||"")+"</span></td>"+
    "<td><span class='badge badge-purple'>"+(q.faculty_name||"Umumiy")+"</span></td>"+
    "<td style='max-width:280px;color:#475569'>"+q.question+"</td>"+
    "<td><span class='badge "+(langBadge[q.lang]||"badge-blue")+"'>"+(q.lang||"uz").toUpperCase()+"</span></td>"+
    "<td><span class='badge "+(q.status==="answered"?"badge-green":"badge-red")+"'>"+(q.status==="answered"?"✅ Javob berilgan":"❓ Javobsiz")+"</span></td>"+
    "<td style='color:#94a3b8;font-size:12px'>"+(q.created_at||"").slice(0,16)+"</td></tr>";
  }).join("")+"</tbody></table></div>";
}

var cachedFaculties=[];
function loadFacultiesData(){
  fetch("/api/admin/faculties").then(function(r){return r.json();}).then(function(d){
    cachedFaculties=d.faculties||[];
    ["qFacultyFilter","faqFaculty","uFaculty"].forEach(function(id){
      var el=document.getElementById(id);if(!el)return;
      var first=el.options[0];el.innerHTML="";el.appendChild(first);
      cachedFaculties.forEach(function(f){
        var o=document.createElement("option");o.value=f.id;o.textContent=f.name;el.appendChild(o);
      });
    });
  });
}

function loadFaculties(){
  loadFacultiesData();
  fetch("/api/admin/faculties").then(function(r){return r.json();}).then(function(d){
    var items=d.faculties||[];
    var c=document.getElementById("facultiesList");
    if(!items.length){c.innerHTML="<div class='empty'>😕 Fakultetlar yo\'q</div>";return;}
    c.innerHTML="<div class='table-card'><table><thead><tr><th>Nomi</th><th>Tavsif</th><th>Telegram guruh</th><th>Status</th><th>Amallar</th></tr></thead><tbody>"+
    items.map(function(f){
      return "<tr><td><strong>"+f.name+"</strong></td>"+
      "<td style='color:#64748b'>"+(f.description||"—")+"</td>"+
      "<td><span style='font-size:12px;color:#4f6ef7;font-family:monospace'>"+(f.telegram_group_name||f.telegram_group_id||"—")+"</span></td>"+
      "<td><span class='badge "+(f.is_active?"badge-green":"badge-red")+"'>"+(f.is_active?"✅ Faol":"❌ Nofaol")+"</span></td>"+
      "<td style='display:flex;gap:8px'><button class='btn btn-sm btn-blue' onclick='editFaculty("+JSON.stringify(f)+")'>✏️ Tahrir</button>"+
      "<button class='btn btn-sm btn-red' onclick='deleteFaculty("+f.id+")'>🗑 O\'chir</button></td></tr>";
    }).join("")+"</tbody></table></div>";
  });
}

function openFacultyModal(f){
  document.getElementById("fModalTitle").textContent=f?"Fakultetni tahrirlash":"Yangi fakultet qo\'shish";
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
  var data={name:document.getElementById("fName").value,description:document.getElementById("fDesc").value,
    group_id:document.getElementById("fGroupId").value,group_name:document.getElementById("fGroupName").value};
  if(!data.name){alert("Fakultet nomi kiritish shart!");return;}
  var url=id?"/api/admin/faculties/"+id:"/api/admin/faculties";
  var method=id?"PUT":"POST";
  fetch(url,{method:method,headers:{"Content-Type":"application/json"},body:JSON.stringify(data)})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok){closeModal("facultyModal");loadFaculties();}
    else alert("Xatolik: "+(d.error||"Noma\'lum"));
  });
}

function deleteFaculty(id){
  if(!confirm("Fakultetni o\'chirasizmi?")) return;
  fetch("/api/admin/faculties/"+id,{method:"DELETE"}).then(function(){loadFaculties();});
}

function loadUsers(){
  fetch("/api/admin/users").then(function(r){return r.json();}).then(function(d){
    var items=d.users||[];
    var c=document.getElementById("usersList");
    if(!items.length){c.innerHTML="<div class='empty'>😕 Xodimlar yo\'q</div>";return;}
    c.innerHTML="<div class='table-card'><table><thead><tr><th>Ism</th><th>Telefon</th><th>Fakultet</th><th>Lavozim</th><th>Status</th><th>Amallar</th></tr></thead><tbody>"+
    items.map(function(u){
      return "<tr><td><strong>"+u.full_name+"</strong></td>"+
      "<td><code style='font-size:12px;background:#f1f5f9;padding:3px 8px;border-radius:6px'>"+u.phone+"</code></td>"+
      "<td><span class='badge badge-purple'>"+(u.faculty_name||"—")+"</span></td>"+
      "<td><span class='badge badge-blue'>"+u.role+"</span></td>"+
      "<td><span class='badge "+(u.is_active?"badge-green":"badge-red")+"'>"+(u.is_active?"✅ Faol":"❌ Nofaol")+"</span></td>"+
      "<td><button class='btn btn-sm btn-red' onclick='deleteUser("+u.id+")'>🗑 O\'chir</button></td></tr>";
    }).join("")+"</tbody></table></div>";
  });
}

function openUserModal(){
  document.getElementById("uName").value="";document.getElementById("uPhone").value="";
  document.getElementById("uPass").value="";
  document.getElementById("userModal").classList.add("open");
}

function saveUser(){
  var data={full_name:document.getElementById("uName").value,phone:document.getElementById("uPhone").value,
    password:document.getElementById("uPass").value,faculty_id:document.getElementById("uFaculty").value||null,
    role:document.getElementById("uRole").value};
  if(!data.full_name||!data.phone||!data.password){alert("Barcha majburiy maydonlarni to\'ldiring!");return;}
  fetch("/api/admin/users",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok){closeModal("userModal");loadUsers();}
    else alert("Xatolik: "+(d.error||"Noma\'lum"));
  });
}

function deleteUser(id){
  if(!confirm("Xodimni o\'chirasizmi?")) return;
  fetch("/api/admin/users/"+id,{method:"DELETE"}).then(function(){loadUsers();});
}

function loadFAQ(){
  fetch("/api/admin/faq").then(function(r){return r.json();}).then(function(d){
    var items=d.items||[];
    var c=document.getElementById("faqList");
    if(!items.length){c.innerHTML="<div class='empty'>😕 FAQ bo\'sh</div>";return;}
    c.innerHTML="<div class='table-card'><table><thead><tr><th>Fakultet</th><th>Savol</th><th>Javob</th><th></th></tr></thead><tbody>"+
    items.map(function(f){
      return "<tr><td><span class='badge badge-purple'>"+(f.faculty_name||"Umumiy")+"</span></td>"+
      "<td style='font-weight:500'>"+f.question+"</td>"+
      "<td style='color:#64748b;max-width:250px'>"+f.answer.slice(0,80)+(f.answer.length>80?"...":"")+"</td>"+
      "<td><button class='btn btn-sm btn-red' onclick='deleteFAQ("+f.id+")'>🗑</button></td></tr>";
    }).join("")+"</tbody></table></div>";
  });
}

function addFAQ(){
  var data={faculty_id:document.getElementById("faqFaculty").value||null,
    question:document.getElementById("faqQ").value,answer:document.getElementById("faqA").value};
  if(!data.question||!data.answer){alert("Savol va javob kiritish shart!");return;}
  fetch("/api/admin/faq",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok){document.getElementById("faqQ").value="";document.getElementById("faqA").value="";loadFAQ();}
    else alert("Xatolik: "+d.error);
  });
}

function deleteFAQ(id){
  if(!confirm("FAQ ni o\'chirasizmi?")) return;
  fetch("/api/admin/faq/"+id,{method:"DELETE"}).then(function(){loadFAQ();});
}

function loadChatGroups(){
  fetch("/api/admin/faculties").then(function(r){return r.json();}).then(function(d){
    var faculties=d.faculties||[];
    var c=document.getElementById("chatGroupsList");
    c.innerHTML="<div class='table-card'><table><thead><tr><th>Fakultet</th><th>Guruh ID</th><th>Guruh nomi</th><th></th></tr></thead><tbody>"+
    faculties.map(function(f){
      return "<tr><td><strong>"+f.name+"</strong></td>"+
      "<td><input class='form-inp' style='width:190px;padding:7px 12px;font-size:12px;font-family:monospace' id='gid_"+f.id+"' value='"+(f.telegram_group_id||"")+"' placeholder='-100xxxxxxx'/></td>"+
      "<td><input class='form-inp' style='width:180px;padding:7px 12px;font-size:12px' id='gname_"+f.id+"' value='"+(f.telegram_group_name||"")+"' placeholder='Guruh nomi'/></td>"+
      "<td><button class='btn btn-sm btn-green' onclick='saveGroupId("+f.id+")'>💾 Saqlash</button></td></tr>";
    }).join("")+"</tbody></table></div>";
  });
}

function saveGroupId(fId){
  var gid=document.getElementById("gid_"+fId).value;
  var gname=document.getElementById("gname_"+fId).value;
  fetch("/api/admin/faculties/"+fId,{method:"PUT",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({group_id:gid,group_name:gname,update_group_only:true})})
  .then(function(r){return r.json();}).then(function(d){
    if(d.ok) alert("✅ Muvaffaqiyatli saqlandi!");
    else alert("Xatolik: "+d.error);
  });
}

function closeModal(id){document.getElementById(id).classList.remove("open");}
</script>
</body>
</html>'''