'use client';
import { useState, useRef, useEffect } from 'react';
import { askQuestion } from '@/lib/api';

type Msg = { text: string; type: 'user' | 'bot' };
type Tab = 'home' | 'chat' | 'faq' | 'profile';
import { getCards, type ServiceCard } from '@/lib/api';

const FAQS = [
  { cat: '📚 HEMIS tizimi', items: [
    { q: 'HEMIS parolimni qanday tiklash mumkin?', a: 'Registrator ofisi xodimlariga murojaat qiling yoki OneID tizimi orqali kiring.' },
    { q: 'HEMIS da dars jadvalini qanday ko\'raman?', a: 'student.tdpu.uz saytiga kiring — dashboardda Dars jadvali bo\'limi chiqadi.' },
    { q: 'GPA ballimni qayerdan ko\'raman?', a: 'Akademik ko\'rsatkichlar bo\'limida umumiy o\'rtacha baho (GPA) ko\'rsatiladi.' },
  ]},
  { cat: '💰 To\'lov va kontrakt', items: [
    { q: 'Kontrakt to\'lov summasini qayerdan bilaman?', a: 'kontrakt.edu.uz saytiga kiring. Shaxsiy kabinet → To\'lov ma\'lumotlari bo\'limidan ko\'ring.' },
    { q: 'Shartnoma to\'lovini online to\'lasa bo\'ladimi?', a: 'Ha, shartnoma to\'lovlarini online to\'lash mumkin.' },
    { q: 'To\'lov kvitansiyasini qayerdan yuklab olaman?', a: 'To\'lovlar tarixi bo\'limida PDF yuklab olish tugmasi orqali kvitansiyani olish mumkin.' },
  ]},
  { cat: '🎓 Grant va stipendiya', items: [
    { q: 'Grantga ariza topshirish uchun minimal GPA qancha?', a: '3.5 va undan yuqori.' },
    { q: 'To\'liq grant nima?', a: 'Bir o\'quv yiliga berilib, kontraktning 100% davlat tomonidan qoplanadigan va stipendiya beriladigan grant.' },
  ]},
];

const SUGGS = ['Dars jadvali qayerdan ko\'raman?', 'Kontrakt to\'lash', 'HEMIS login', 'Stipendiya shartlari'];

export default function StudentPage() {
  const [darkMode, setDarkMode] = useState(false);
  const [tab, setTab]         = useState<Tab>('home');
  const [cards, setCards]     = useState<ServiceCard[]>([]);
  const [msgs, setMsgs]       = useState<Msg[]>([{ text: '👋 Salom! Men UzNPUU botiman. Savolingizni yozing — yordam beraman!', type: 'bot' }]);
  const [input, setInput]     = useState('');
  const [typing, setTyping]   = useState(false);
  const [faqQ, setFaqQ]       = useState('');
  const [openFAQ, setOpenFAQ] = useState<string | null>(null);
  const msgsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem('student-theme');
    if (saved === 'dark') setDarkMode(true);
  }, []);

  const toggleTheme = () => {
    const next = !darkMode;
    setDarkMode(next);
    localStorage.setItem('student-theme', next ? 'dark' : 'light');
  };

  useEffect(() => {
    msgsRef.current?.scrollTo({ top: msgsRef.current.scrollHeight, behavior: 'smooth' });
  }, [msgs, typing]);

  useEffect(() => {
    getCards().then(d => setCards(d.cards));
  }, []);

  async function send(text?: string) {
    const q = (text ?? input).trim();
    if (!q) return;
    setInput('');
    setMsgs(p => [...p, { text: q, type: 'user' }]);
    setTyping(true);
    try {
      const d = await askQuestion(q);
      setMsgs(p => [...p, { text: d.answer || 'Xatolik yuz berdi.', type: 'bot' }]);
    } catch {
      setMsgs(p => [...p, { text: 'Serverga ulanishda xatolik.', type: 'bot' }]);
    }
    setTyping(false);
  }

  const filteredFAQ = FAQS.map(cat => ({
    ...cat,
    items: cat.items.filter(it =>
      !faqQ || it.q.toLowerCase().includes(faqQ.toLowerCase()) || it.a.toLowerCase().includes(faqQ.toLowerCase())
    ),
  })).filter(cat => cat.items.length > 0);

  return (
    <div className={`student-wrap${darkMode ? ' dark' : ''}`}>
      {/* Header */}
      <div className="student-header">
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ fontSize: 9, color: darkMode ? '#a5b4fc' : '#4f46e5', fontWeight: 800, letterSpacing: 2, marginBottom: 12, opacity: 0.7 }}>RASMIY BOT</div>
          <div className="student-title-container">
            <div className="student-title-uznpuu">UzNPUU</div>
            <div className="student-title-yordamchi">Yordamchi</div>
          </div>
          <div className="student-sub" style={{ marginTop: 16, fontSize: 13, lineHeight: 1.5, maxWidth: '85%' }}>Nizomiy nomidagi O&#39;zbekiston Milliy pedagogika universiteti</div>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {tab === 'home' && (
          <div className="home-wrap" style={{ paddingTop: 0 }}>
            <div className="card-grid">
              {/* Static core cards */}
              <div className="home-card" onClick={() => setTab('faq')}>
                <div className="card-icon-box" style={{ background: darkMode ? 'rgba(108, 92, 231, 0.2)' : '#eef2ff' }}>📋</div>
                <div className="card-info">
                  <div className="card-title">FAQ</div>
                  <div className="card-desc">Tez-tez soraladigan</div>
                </div>
              </div>
              
              <div className="home-card" onClick={() => setTab('profile')}>
                <div className="card-icon-box" style={{ background: darkMode ? 'rgba(108, 92, 231, 0.2)' : '#eef2ff' }}>👤</div>
                <div className="card-info">
                  <div className="card-title">Profilim</div>
                  <div className="card-desc">GPA va malumotlar</div>
                </div>
              </div>

              {/* Dynamic cards from DB */}
              {cards.map(c => (
                <div key={c.id} className="home-card" onClick={() => {
                  if (c.type === 'message') { setTab('chat'); send(c.link || c.title); }
                  else if (c.type === 'link') window.open(c.link, '_blank');
                  else if (c.type === 'tab') setTab(c.link as any);
                }}>
                  <div className="card-icon-box">{c.icon}</div>
                  <div className="card-info">
                    <div className="card-title">{c.title}</div>
                    <div className="card-desc">{c.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === 'chat' && (
          <>
            <div className="chat-area" ref={msgsRef}>
              {msgs.map((m, i) => <div key={i} className={`msg ${m.type}`}>{m.text}</div>)}
              {typing && (
                <div className="msg bot">
                  <div className="dots"><span /><span /><span /></div>
                </div>
              )}
            </div>
            {msgs.length === 1 && (
              <div className="suggs">
                {SUGGS.map(s => <button key={s} className="sugg" onClick={() => send(s)}>{s}</button>)}
              </div>
            )}
            <div className="chat-input-row">
              <textarea
                className="chat-input"
                placeholder="Savolingizni yozing..."
                value={input}
                onChange={e => { setInput(e.target.value); const el = e.target; el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 88) + 'px'; }}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
                rows={1}
              />
              <button className="send-btn" onClick={() => send()} disabled={!input.trim() || typing}>➤</button>
            </div>
          </>
        )}

        {tab === 'faq' && (
          <div className="faq-wrap">
            <input className="faq-search" placeholder="🔍 FAQ qidirish..." value={faqQ} onChange={e => setFaqQ(e.target.value)} />
            {filteredFAQ.map(cat => (
              <div key={cat.cat}>
                <div className="faq-cat">{cat.cat}</div>
                {cat.items.map(it => (
                  <div key={it.q} className={`faq-item${openFAQ === it.q ? ' open' : ''}`}>
                    <div className="faq-q" onClick={() => setOpenFAQ(openFAQ === it.q ? null : it.q)}>
                      {it.q}<span className="faq-arr">▼</span>
                    </div>
                    <div className="faq-a">{it.a}</div>
                  </div>
                ))}
              </div>
            ))}
            {filteredFAQ.length === 0 && <div style={{ textAlign:'center', color:'var(--muted)', padding:40, fontSize:13 }}>Hech narsa topilmadi</div>}
          </div>
        )}

        {tab === 'profile' && (
          <div className="profile-wrap">
            <div className="profile-card">
              <div className="profile-avatar">👤</div>
              <div className="profile-name">Talaba</div>
              <div className="profile-role">UzNPUU talabasi</div>
              <div className="gpa-container">
                <div className="gpa-ring" style={{ background: `conic-gradient(#4f46e5 ${0 * 3.6}deg, ${darkMode ? '#0f172a' : '#f1f5f9'} 0)` }}>
                  <div className="gpa-content">
                    <span className="gpa-val">—</span>
                    <span className="gpa-label">GPA</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="profile-stats">
              <div className="stat-card red">
                <span className="stat-label">Kreditor</span>
                <span className="stat-val">0</span>
              </div>
              <div className="stat-card green">
                <span className="stat-label">Kurs</span>
                <span className="stat-val">1</span>
              </div>
            </div>

            <div className="profile-list">
              <div className="profile-row">
                <span className="profile-label">Status</span>
                <span className="status-badge">Faol talaba</span>
              </div>
              <div className="profile-row">
                <span className="profile-label">Telegram ID</span>
                <span className="profile-value">—</span>
              </div>
              <div className="profile-row">
                <span className="profile-label">Foydalanuvchi</span>
                <span className="profile-value">—</span>
              </div>
            </div>

            <div className="hemis-box">
              <div className="hemis-text">To'liq akademik ma'lumotlar uchun HEMIS tizimiga kiring:</div>
              <a href="https://student.tdpu.uz" target="_blank" className="hemis-link">student.tdpu.uz</a>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Nav */}
      <nav className="student-nav">
        {[
          { t: 'home', icon: '🏠', label: 'Bosh sahifa' },
          { t: 'chat', icon: '💬', label: 'Chat' },
          { t: 'theme', icon: darkMode ? '☀️' : '🌙', label: 'Mavzu' },
        ].map(n => (
          <button
            key={n.t}
            className={`s-nav-btn${tab === n.t ? ' active' : ''}`}
            onClick={() => {
              if (n.t === 'theme') toggleTheme();
              else setTab(n.t as any);
            }}
          >
            <span className="s-nav-icon">{n.icon}</span>{n.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
