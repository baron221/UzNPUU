import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8080

print(f"GROQ_API_KEY: {'SET' if os.environ.get('GROQ_API_KEY') else 'MISSING'}")
print(f"BOT_TOKEN: {'SET' if os.environ.get('BOT_TOKEN') else 'MISSING'}")

from file_loader import load_knowledge_base
from ai_responder import setup_ai, get_answer, parse_qa_pairs
from logger import get_stats, get_logs
import ai_responder

knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
clients = setup_ai()
ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
print("✅ AI ready!")

ADMIN_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>OʻzMPU Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Playfair+Display:wght@700&display=swap" rel="stylesheet"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#07080f;--s1:#0d1020;--s2:#131629;--card:#181d2e;
  --border:rgba(120,150,255,0.12);--border2:rgba(120,150,255,0.22);
  --accent:#7c8fff;--accent2:#ff8c69;--accent3:#52d9a4;--red:#ff6b6b;
  --text:#eef0f8;--muted:#6b7299;--muted2:#8890b8;--r:16px;--r2:12px;
}
body{background:var(--bg);color:var(--text);font-family:'Sora',sans-serif;min-height:100vh;font-size:14px}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:var(--border2);border-radius:99px}

.login-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.login-card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:32px;width:100%;max-width:380px;text-align:center}
.login-icon{font-size:40px;margin-bottom:16px}
.login-title{font-family:'Playfair Display',serif;font-size:24px;margin-bottom:6px}
.login-sub{font-size:12px;color:var(--muted2);margin-bottom:24px}
.login-input{width:100%;background:var(--s2);border:1px solid var(--border);border-radius:var(--r2);padding:12px 14px;color:var(--text);font-family:'Sora',sans-serif;font-size:14px;outline:none;margin-bottom:12px;transition:border-color 0.2s}
.login-input:focus{border-color:var(--accent)}
.login-input::placeholder{color:var(--muted)}
.login-btn{width:100%;background:linear-gradient(135deg,var(--accent),#5561d4);border:none;border-radius:var(--r2);padding:13px;color:#fff;font-family:'Sora',sans-serif;font-size:14px;font-weight:500;cursor:pointer}
.login-err{font-size:12px;color:var(--red);margin-top:8px}

.dash{display:none}
.topbar{background:var(--s1);border-bottom:1px solid var(--border);padding:14px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.topbar-left{display:flex;align-items:center;gap:10px}
.topbar-logo{width:32px;height:32px;background:linear-gradient(135deg,var(--accent),#5561d4);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px}
.topbar-title{font-family:'Playfair Display',serif;font-size:17px;font-weight:700}
.topbar-sub{font-size:10px;color:var(--muted);margin-top:1px}
.logout-btn{background:rgba(255,107,107,0.1);border:1px solid rgba(255,107,107,0.25);border-radius:8px;padding:6px 14px;color:var(--red);font-family:'Sora',sans-serif;font-size:12px;cursor:pointer}

.main{padding:20px 24px;max-width:1100px;margin:0 auto}
.tab-row{display:flex;gap:4px;margin-bottom:20px;background:var(--s2);border:1px solid var(--border);border-radius:var(--r2);padding:4px}
.tab-btn{flex:1;padding:9px;border:none;background:none;color:var(--muted2);font-family:'Sora',sans-serif;font-size:11px;cursor:pointer;border-radius:10px;transition:all 0.2s;font-weight:500}
.tab-btn.active{background:var(--card);color:var(--text);border:1px solid var(--border)}
.tab-page{display:none}.tab-page.active{display:block}

.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:16px}
.stat-icon{font-size:20px;margin-bottom:10px}
.stat-num{font-family:'Playfair Display',serif;font-size:28px;font-weight:700;line-height:1;margin-bottom:4px}
.stat-lbl{font-size:11px;color:var(--muted)}
.c-blue{color:var(--accent)}.c-green{color:var(--accent3)}.c-red{color:var(--red)}.c-orange{color:var(--accent2)}

.charts-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px}
@media(max-width:600px){.charts-grid{grid-template-columns:1fr}}
.chart-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:16px}
.chart-title{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:14px}
.chart-wrap{position:relative;height:180px}

.lang-bars{display:flex;flex-direction:column;gap:8px;margin-top:4px}
.lang-row{display:flex;align-items:center;gap:10px;font-size:12px}
.lang-name{width:24px;color:var(--muted2)}
.lang-bar-wrap{flex:1;background:var(--s2);border-radius:99px;height:8px;overflow:hidden}
.lang-bar{height:100%;border-radius:99px;transition:width 0.6s ease}
.lang-count{font-size:11px;color:var(--muted);width:30px;text-align:right}

.logs-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.logs-title{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted)}
.refresh-btn{background:var(--s2);border:1px solid var(--border);border-radius:8px;padding:6px 14px;color:var(--muted2);font-family:'Sora',sans-serif;font-size:11px;cursor:pointer}

.filter-row{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.filter-btn{background:var(--s2);border:1px solid var(--border);border-radius:99px;padding:5px 12px;font-size:11px;color:var(--muted2);cursor:pointer;font-family:'Sora',sans-serif}
.filter-btn.active{background:rgba(124,143,255,0.15);border-color:var(--accent);color:var(--accent)}

.log-item{background:var(--card);border:1px solid var(--border);border-radius:var(--r2);padding:13px 15px;margin-bottom:7px}
.log-item.unanswered{border-left:3px solid var(--red)}
.log-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:7px;gap:8px}
.log-user{font-size:12px;font-weight:500;color:var(--accent)}
.log-meta{display:flex;gap:6px;align-items:center;flex-shrink:0}
.tag{font-size:10px;padding:2px 8px;border-radius:99px;font-weight:500}
.tag-uz{background:rgba(82,217,164,0.12);color:var(--accent3)}
.tag-ru{background:rgba(255,107,107,0.12);color:var(--red)}
.tag-en{background:rgba(124,143,255,0.12);color:var(--accent)}
.tag-time{font-size:10px;color:var(--muted)}
.log-q{font-size:13px;color:var(--text);margin-bottom:5px;font-weight:500}
.log-a{font-size:12px;color:var(--muted2);line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}

.unans-item{background:var(--card);border:1px solid rgba(255,107,107,0.25);border-radius:var(--r2);padding:13px 15px;margin-bottom:8px}
.unans-q{font-size:13px;font-weight:500;color:var(--text);margin-bottom:5px}
.unans-meta{font-size:11px;color:var(--muted)}

.upload-zone{border:2px dashed var(--border2);border-radius:var(--r);padding:32px;text-align:center;cursor:pointer;transition:all 0.2s;margin-bottom:16px;background:var(--s2)}
.upload-zone:hover,.upload-zone.drag{border-color:var(--accent);background:rgba(124,143,255,0.06)}
.upload-icon{font-size:32px;margin-bottom:10px}
.upload-title{font-size:14px;font-weight:500;margin-bottom:4px}
.upload-sub{font-size:12px;color:var(--muted)}
.file-item{background:var(--card);border:1px solid var(--border);border-radius:var(--r2);padding:13px 15px;margin-bottom:8px;display:flex;align-items:center;gap:12px}
.file-icon{font-size:24px;flex-shrink:0}
.file-info{flex:1;min-width:0}
.file-name{font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.file-size{font-size:11px;color:var(--muted);margin-top:2px}
.file-del{background:rgba(255,107,107,0.1);border:1px solid rgba(255,107,107,0.2);border-radius:8px;padding:6px 12px;color:var(--red);font-size:12px;cursor:pointer;font-family:'Sora',sans-serif;white-space:nowrap}
.progress-wrap{background:var(--card);border:1px solid var(--border);border-radius:var(--r2);padding:14px;margin-bottom:12px;display:none}
.progress-bar-bg{background:var(--s1);border-radius:99px;height:6px;margin-top:8px;overflow:hidden}
.progress-bar{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent3));border-radius:99px;width:0%;transition:width 0.3s}
.success-msg{background:rgba(82,217,164,0.1);border:1px solid rgba(82,217,164,0.25);border-radius:var(--r2);padding:12px 14px;font-size:13px;color:var(--accent3);margin-bottom:12px;display:none}
.error-msg{background:rgba(255,107,107,0.1);border:1px solid rgba(255,107,107,0.25);border-radius:var(--r2);padding:12px 14px;font-size:13px;color:var(--red);margin-bottom:12px;display:none}
.empty{text-align:center;padding:40px;color:var(--muted);font-size:13px}
.loading{text-align:center;padding:30px;color:var(--muted);font-size:13px}
</style>
</head>
<body>

<div class="login-wrap" id="loginWrap">
  <div class="login-card">
    <div class="login-icon">🔐</div>
    <div class="login-title">Admin Panel</div>
    <div class="login-sub">OʻzMPU Bot boshqaruv paneli</div>
    <input class="login-input" type="password" id="passInput" placeholder="Parol kiriting..." onkeydown="if(event.key==='Enter')doLogin()"/>
    <button class="login-btn" onclick="doLogin()">Kirish</button>
    <div class="login-err" id="loginErr"></div>
  </div>
</div>

<div class="dash" id="dash">
  <div class="topbar">
    <div class="topbar-left">
      <div class="topbar-logo">🎓</div>
      <div>
        <div class="topbar-title">OʻzMPU Admin</div>
        <div class="topbar-sub">Bot boshqaruv paneli</div>
      </div>
    </div>
    <button class="logout-btn" onclick="doLogout()">Chiqish</button>
  </div>

  <div class="main">
    <div class="tab-row">
      <button class="tab-btn active" onclick="switchTab('overview',this)">📊 Umumiy</button>
      <button class="tab-btn" onclick="switchTab('logs',this)">💬 Savollar</button>
      <button class="tab-btn" onclick="switchTab('unanswered',this)">❓ Javobsiz</button>
      <button class="tab-btn" onclick="switchTab('files',this)">📁 Fayllar</button>
    </div>

    <div class="tab-page active" id="tab-overview">
      <div class="stats-grid" id="statsGrid"><div class="loading">Yuklanmoqda...</div></div>
      <div class="charts-grid">
        <div class="chart-card">
          <div class="chart-title">So'nggi 7 kun</div>
          <div class="chart-wrap"><canvas id="actChart"></canvas></div>
        </div>
        <div class="chart-card">
          <div class="chart-title">Kategoriyalar</div>
          <div class="chart-wrap"><canvas id="catChart"></canvas></div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">Til taqsimoti</div>
        <div class="lang-bars" id="langBars"></div>
      </div>
    </div>

    <div class="tab-page" id="tab-logs">
      <div class="logs-header">
        <div class="logs-title">Barcha savollar</div>
        <button class="refresh-btn" onclick="loadLogs()">Yangilash</button>
      </div>
      <div class="filter-row">
        <button class="filter-btn active" onclick="filterLogs('all',this)">Barchasi</button>
        <button class="filter-btn" onclick="filterLogs('uz',this)">UZ</button>
        <button class="filter-btn" onclick="filterLogs('ru',this)">RU</button>
        <button class="filter-btn" onclick="filterLogs('en',this)">EN</button>
        <button class="filter-btn" onclick="filterLogs('unanswered',this)">Javobsiz</button>
      </div>
      <div id="logsList"><div class="loading">Yuklanmoqda...</div></div>
    </div>

    <div class="tab-page" id="tab-unanswered">
      <div class="logs-header">
        <div class="logs-title">Javobsiz savollar</div>
        <button class="refresh-btn" onclick="loadLogs()">Yangilash</button>
      </div>
      <div id="unansweredList"><div class="loading">Yuklanmoqda...</div></div>
    </div>

    <div class="tab-page" id="tab-files">
      <div class="upload-zone" id="uploadZone"
        onclick="document.getElementById('fileInput').click()"
        ondragover="onDragOver(event)"
        ondragleave="onDragLeave(event)"
        ondrop="onDrop(event)">
        <input type="file" id="fileInput" style="display:none" accept=".pdf,.docx,.txt,.xlsx,.md" onchange="uploadFile(this.files[0])"/>
        <div class="upload-icon">📄</div>
        <div class="upload-title">Fayl yuklash uchun bosing yoki sudrab keling</div>
        <div class="upload-sub">PDF, DOCX, TXT, XLSX — max 10MB</div>
      </div>
      <div class="progress-wrap" id="progressWrap">
        <div style="font-size:13px;color:var(--muted2)" id="progressText">Yuklanmoqda...</div>
        <div class="progress-bar-bg"><div class="progress-bar" id="progressBar"></div></div>
      </div>
      <div class="success-msg" id="successMsg"></div>
      <div class="error-msg" id="errorMsg"></div>
      <div class="logs-header">
        <div class="logs-title">Yuklangan fayllar</div>
        <button class="refresh-btn" onclick="loadFiles()">Yangilash</button>
      </div>
      <div id="filesList"><div class="loading">Yuklanmoqda...</div></div>
    </div>
  </div>
</div>

<script>
var allLogs = [];
var actChartObj = null;
var catChartObj = null;

function doLogin() {
  var pass = document.getElementById('passInput').value;
  fetch('/api/auth', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({password: pass})
  })
  .then(function(r) { return r.json(); })
  .then(function(d) {
    if (d.ok) {
      document.getElementById('loginWrap').style.display = 'none';
      document.getElementById('dash').style.display = 'block';
      loadAll();
    } else {
      document.getElementById('loginErr').textContent = "Parol noto'g'ri!";
    }
  });
}

function doLogout() {
  document.getElementById('loginWrap').style.display = 'flex';
  document.getElementById('dash').style.display = 'none';
  document.getElementById('passInput').value = '';
}

function switchTab(name, btn) {
  document.querySelectorAll('.tab-page').forEach(function(p) { p.classList.remove('active'); });
  document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
  if (name === 'files') loadFiles();
  if (name === 'logs') loadLogs();
  if (name === 'unanswered') loadLogs();
}

function loadAll() {
  loadStats();
  loadLogs();
}

function loadStats() {
  fetch('/api/stats')
  .then(function(r) { return r.json(); })
  .then(function(s) {
    document.getElementById('statsGrid').innerHTML =
      '<div class="stat-card"><div class="stat-icon">💬</div><div class="stat-num c-blue">' + s.total + '</div><div class="stat-lbl">Jami savollar</div></div>' +
      '<div class="stat-card"><div class="stat-icon">✅</div><div class="stat-num c-green">' + s.answered + '</div><div class="stat-lbl">Javob berildi</div></div>' +
      '<div class="stat-card"><div class="stat-icon">❓</div><div class="stat-num c-red">' + s.unanswered + '</div><div class="stat-lbl">Javobsiz</div></div>' +
      '<div class="stat-card"><div class="stat-icon">👤</div><div class="stat-num c-orange">' + s.users + '</div><div class="stat-lbl">Foydalanuvchilar</div></div>';

    var days = Object.keys(s.daily || {});
    var counts = Object.values(s.daily || {});
    if (actChartObj) actChartObj.destroy();
    actChartObj = new Chart(document.getElementById('actChart'), {
      type: 'bar',
      data: {
        labels: days.map(function(d) { return d.slice(5); }),
        datasets: [{data: counts, backgroundColor: 'rgba(124,143,255,0.35)', borderColor: '#7c8fff', borderWidth: 1.5, borderRadius: 6}]
      },
      options: {responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
        scales:{x:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'#6b7299',font:{size:11}}},
                y:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'#6b7299',font:{size:11}}}}}
    });

    var cats = s.categories || {};
    var catColors = {UNIVERSITY:'#7c8fff', GENERAL:'#52d9a4', VAGUE:'#ff8c69', UNANSWERED:'#ff6b6b', ERROR:'#888'};
    if (catChartObj) catChartObj.destroy();
    catChartObj = new Chart(document.getElementById('catChart'), {
      type: 'doughnut',
      data: {
        labels: Object.keys(cats),
        datasets: [{data: Object.values(cats), backgroundColor: Object.keys(cats).map(function(k) { return catColors[k] || '#7c8fff'; }), borderWidth: 0}]
      },
      options: {responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'bottom', labels:{color:'#8890b8', font:{size:11}, padding:10}}}}
    });

    var langs = s.langs || {};
    var total = Object.values(langs).reduce(function(a,b){ return a+b; }, 0) || 1;
    var langColors = {uz:'#52d9a4', ru:'#ff6b6b', en:'#7c8fff'};
    var langNames = {uz:'UZ', ru:'RU', en:'EN'};
    document.getElementById('langBars').innerHTML = Object.entries(langs).map(function(e) {
      return '<div class="lang-row"><div class="lang-name">' + (langNames[e[0]]||e[0]) + '</div><div class="lang-bar-wrap"><div class="lang-bar" style="width:' + Math.round(e[1]/total*100) + '%;background:' + (langColors[e[0]]||'#7c8fff') + '"></div></div><div class="lang-count">' + e[1] + '</div></div>';
    }).join('') || '<div style="color:var(--muted);font-size:12px">Hali malumat yoq</div>';
  });
}

function loadLogs() {
  fetch('/api/logs')
  .then(function(r) { return r.json(); })
  .then(function(d) {
    allLogs = d.logs || [];
    renderLogs(allLogs);
    renderUnanswered(allLogs.filter(function(l) { return !l.answered; }));
  });
}

function filterLogs(type, btn) {
  document.querySelectorAll('.filter-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  if (type === 'all') renderLogs(allLogs);
  else if (type === 'unanswered') renderLogs(allLogs.filter(function(l) { return !l.answered; }));
  else renderLogs(allLogs.filter(function(l) { return l.lang === type; }));
}

function renderLogs(logs) {
  var c = document.getElementById('logsList');
  if (!logs.length) { c.innerHTML = '<div class="empty">Hech qanday savol yoq</div>'; return; }
  var tagMap = {uz:'tag-uz', ru:'tag-ru', en:'tag-en'};
  c.innerHTML = logs.map(function(l) {
    return '<div class="log-item ' + (!l.answered ? 'unanswered' : '') + '">' +
      '<div class="log-top"><div class="log-user">@' + l.username + '</div>' +
      '<div class="log-meta"><span class="tag ' + (tagMap[l.lang]||'tag-uz') + '">' + (l.lang||'uz').toUpperCase() + '</span>' +
      '<span class="tag-time">' + (l.time||'') + '</span></div></div>' +
      '<div class="log-q">' + l.question + '</div>' +
      '<div class="log-a">' + l.answer + '</div></div>';
  }).join('');
}

function renderUnanswered(logs) {
  var c = document.getElementById('unansweredList');
  if (!logs.length) { c.innerHTML = '<div class="empty">Barcha savollarga javob berilgan!</div>'; return; }
  c.innerHTML = logs.map(function(l) {
    return '<div class="unans-item"><div class="unans-q">' + l.question + '</div>' +
      '<div class="unans-meta">@' + l.username + ' - ' + (l.date||'') + ' ' + (l.time||'') + '</div></div>';
  }).join('');
}

var EXT_ICONS = {'.pdf':'📕','.docx':'📘','.txt':'📄','.xlsx':'📊','.md':'📝'};

function loadFiles() {
  var c = document.getElementById('filesList');
  c.innerHTML = '<div class="loading">Yuklanmoqda...</div>';
  fetch('/api/files')
  .then(function(r) { return r.json(); })
  .then(function(d) {
    if (!d.files || !d.files.length) {
      c.innerHTML = '<div class="empty">Hech qanday fayl yoq</div>'; return;
    }
    c.innerHTML = d.files.map(function(f) {
      return '<div class="file-item">' +
        '<div class="file-icon">' + (EXT_ICONS[f.ext]||'📄') + '</div>' +
        '<div class="file-info"><div class="file-name">' + f.name + '</div>' +
        '<div class="file-size">' + f.size + ' KB</div></div>' +
        '<button class="file-del" onclick="deleteFile(\\'' + f.name.replace(/'/g,"\\\\'") + '\\')">Ochirish</button></div>';
    }).join('');
  });
}

function deleteFile(name) {
  if (!confirm(name + " faylini ochirmoqchimisiz?")) return;
  fetch('/api/delete', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({filename: name})
  })
  .then(function(r) { return r.json(); })
  .then(function(d) {
    if (d.ok) { showSuccess(name + " ochirildi!"); loadFiles(); }
    else { showError("Xatolik: " + d.error); }
  });
}

function uploadFile(file) {
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) { showError("Fayl 10MB dan katta!"); return; }
  hideMessages();
  document.getElementById('progressWrap').style.display = 'block';
  document.getElementById('progressText').textContent = "Yuklanmoqda: " + file.name;
  document.getElementById('progressBar').style.width = '40%';
  var formData = new FormData();
  formData.append('file', file);
  fetch('/api/upload', {method: 'POST', body: formData})
  .then(function(r) { return r.json(); })
  .then(function(d) {
    document.getElementById('progressWrap').style.display = 'none';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('fileInput').value = '';
    if (d.ok) { showSuccess(d.filename + " yuklandi! " + d.pairs + " ta savol-javob qayta yuklandi."); loadFiles(); }
    else { showError("Xatolik: " + d.error); }
  })
  .catch(function(e) {
    document.getElementById('progressWrap').style.display = 'none';
    showError("Yuklashda xatolik: " + e.message);
  });
}

function onDragOver(e) { e.preventDefault(); document.getElementById('uploadZone').classList.add('drag'); }
function onDragLeave(e) { document.getElementById('uploadZone').classList.remove('drag'); }
function onDrop(e) {
  e.preventDefault();
  document.getElementById('uploadZone').classList.remove('drag');
  if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]);
}

function showSuccess(msg) {
  var el = document.getElementById('successMsg');
  el.textContent = msg; el.style.display = 'block';
  setTimeout(function() { el.style.display = 'none'; }, 5000);
}
function showError(msg) {
  var el = document.getElementById('errorMsg');
  el.textContent = msg; el.style.display = 'block';
  setTimeout(function() { el.style.display = 'none'; }, 5000);
}
function hideMessages() {
  document.getElementById('successMsg').style.display = 'none';
  document.getElementById('errorMsg').style.display = 'none';
}
</script>
</body>
</html>
"""



def reload_knowledge():
    global knowledge_base
    knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
    ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)
    print(f"🔄 Reloaded: {len(ai_responder._cached_pairs)} pairs")


class Handler(BaseHTTPRequestHandler):

    def log_message(self, *a): pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == '/health':
            self.send_json({"status": "ok", "pairs": len(ai_responder._cached_pairs or [])})
        elif path == '/api/stats':
            self.send_json(get_stats())
        elif path == '/api/logs':
            self.send_json({"logs": get_logs()[-50:][::-1]})
        elif path == '/api/files':
            self.handle_list_files()
        elif path in ['/admin', '/admin.html']:
            self.send_html(ADMIN_HTML)
        else:
            self.send_json({"status": "running", "message": "OʻzMPU Bot API"})

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        path = self.path.split("?")[0]
        if path == '/ask':
            self.handle_ask(body)
        elif path == '/api/auth':
            self.handle_auth(body)
        elif path == '/api/delete':
            self.handle_delete(body)
        elif path == '/api/upload':
            self.handle_upload(length, body)
        else:
            self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_ask(self, body):
        try:
            data = json.loads(body)
            question = data.get('question', '').strip()
            if not question:
                self.send_json({"answer": "Savol bo'sh!"}); return
            answer, options, lang, category = get_answer(question, knowledge_base, clients)
            if options:
                answer = answer + "\n\n" + "\n".join(f"• {o}" for o in options)
            self.send_json({"answer": answer})
        except Exception as e:
            self.send_json({"answer": f"Xatolik: {str(e)}"})

    def handle_auth(self, body):
        try:
            data = json.loads(body)
            self.send_json({"ok": data.get('password') == ADMIN_PASSWORD})
        except:
            self.send_json({"ok": False})

    def handle_list_files(self):
        try:
            folder = os.path.join(BASE_DIR, 'knowledge')
            files = []
            for f in os.listdir(folder):
                fp = os.path.join(folder, f)
                if os.path.isfile(fp):
                    files.append({
                        "name": f,
                        "size": round(os.path.getsize(fp) / 1024, 1),
                        "ext": os.path.splitext(f)[1].lower()
                    })
            self.send_json({"files": files})
        except Exception as e:
            self.send_json({"files": [], "error": str(e)})

    def handle_delete(self, body):
        try:
            data = json.loads(body)
            filename = os.path.basename(data.get('filename', ''))
            fp = os.path.join(BASE_DIR, 'knowledge', filename)
            if os.path.exists(fp):
                os.remove(fp)
                reload_knowledge()
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False, "error": "File not found"})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)})

    def handle_upload(self, length, body):
        try:
            ct = self.headers.get('Content-Type', '')
            if 'boundary=' not in ct:
                self.send_json({"ok": False, "error": "Invalid content type"}); return
            boundary = ct.split('boundary=')[1].strip().encode()
            parts = body.split(b'--' + boundary)
            filename = None
            filedata = None
            for part in parts:
                if b'Content-Disposition' not in part or b'filename=' not in part:
                    continue
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1: continue
                header = part[:header_end].decode('utf-8', errors='ignore')
                data = part[header_end + 4:]
                if data.endswith(b'\r\n'): data = data[:-2]
                for h in header.split('\r\n'):
                    if 'filename=' in h:
                        filename = os.path.basename(h.split('filename=')[1].strip().strip('"'))
                filedata = data
            if not filename or filedata is None:
                self.send_json({"ok": False, "error": "No file found"}); return
            allowed = ('.pdf', '.docx', '.txt', '.xlsx', '.md')
            if not filename.lower().endswith(allowed):
                self.send_json({"ok": False, "error": "File type not allowed"}); return
            save_path = os.path.join(BASE_DIR, 'knowledge', filename)
            with open(save_path, 'wb') as f:
                f.write(filedata)
            reload_knowledge()
            self.send_json({"ok": True, "filename": filename, "pairs": len(ai_responder._cached_pairs)})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)})

    def send_html(self, html):
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    print(f"🚀 Starting on port {PORT}")
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()