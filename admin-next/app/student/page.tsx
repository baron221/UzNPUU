'use client';
import { useState, useRef, useEffect } from 'react';
import { getCards, type ServiceCard, askAdmin, askQuestion, getStudentProfile } from '@/lib/api';

type Msg = { text: string; type: 'user' | 'bot'; options?: string[]; showAdmin?: boolean };
type Tab = 'home' | 'chat' | 'faq' | 'profile';

const FAQS = [
  { cat: '🎓 Universitet hayoti', items: [
    { q: 'Yordamchi bot nima qila oladi?', a: 'Sizning universitet, darslar, shartnoma va boshqa akademik masalalardagi savollaringizga AI yordamida tezkor javob beradi.' },
    { q: 'Adminstrator bilan qanday bog\'lansa bo\'ladi?', a: 'Agar AI savolingizga javob topa olmasa, "Adminstratorga yuborish" tugmasi chiqadi. Shunda mutaxassis bilan bog\'lanishingiz mumkin.' },
    { q: 'Fakultet guruhlariga qanday qo\'shilish mumkin?', a: 'Botning Asosiy sahifasidagi foydali havolalar orqali o\'z fakultetingiz guruhini topishingiz mumkin.' },
  ]},
  { cat: '💰 To\'lov va shartnoma', items: [
    { q: 'Shartnoma to\'lovini online to\'lasa bo\'ladimi?', a: 'Ha, shartnoma to\'lovlarini ko\'plab to\'lov tizimlari (Click, Payme) orqali amalga oshirish mumkin.' },
  ]},
  { cat: '🎓 Grant va stipendiya', items: [
    { q: 'Grantga ariza topshirish uchun minimal GPA qancha?', a: '3.5 va undan yuqori.' },
    { q: 'To\'liq grant nima?', a: 'Bir o\'quv yiliga berilib, kontraktning 100% davlat tomonidan qoplanadigan va stipendiya beriladigan grant.' },
  ]},
];

const SUGGS = ['Dars jadvali', 'Shartnoma to\'lovlari', 'Fakultetlar ro\'yxati', 'Bot qanday ishlaydi?'];

export default function StudentPage() {
  const [darkMode, setDarkMode] = useState(false);
  const [tab, setTab]         = useState<Tab>('home');
  const [cards, setCards]     = useState<ServiceCard[]>([]);
  const [msgs, setMsgs]       = useState<Msg[]>([{ text: '👋 Salom! Men UzNPUU botiman. Savolingizni yozing — yordam beraman!', type: 'bot' }]);
  const [input, setInput]     = useState('');
  const [typing, setTyping]   = useState(false);
  const [faqQ, setFaqQ]       = useState('');
  const [openFAQ, setOpenFAQ] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState('');
  const [profile, setProfile] = useState<{ student_id?: string; telegram_id?: string; faculty_name?: string } | null>(null);
  const [fetchingProfile, setFetchingProfile] = useState(false);
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

  const [faculty_id, set_faculty_id] = useState<number | null>(null);

  useEffect(() => {
    // @ts-ignore
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      const user = tg.initDataUnsafe?.user;
      if (user) {
        const userData = {
          student_telegram_id: String(user.id),
          student_username: user.username,
          student_name: `${user.first_name || ''} ${user.last_name || ''}`.trim(),
        };
        localStorage.setItem('tg_user', JSON.stringify(userData));
        
        // Fetch profile from our DB
        setFetchingProfile(true);
        getStudentProfile(String(user.id)).then(p => {
          if (p.ok) setProfile(p);
          setFetchingProfile(false);
        }).catch(() => setFetchingProfile(false));
      }
    }
  }, []);

  async function send(text?: string) {
    const q = (text ?? input).trim();
    if (!q) return;

    setLastQuestion(q);
    const metaStr = localStorage.getItem('tg_user');
    const meta = metaStr ? JSON.parse(metaStr) : {};

    setInput('');
    setMsgs(p => [...p, { text: q, type: 'user' }]);
    setTyping(true);
    try {
      const d = await askQuestion(q, meta);
      const kws = ["topilmadi", "not found", "murojaat qiling", "mas'ul xodimi", "adminstrator", "ofisiga"];
      const showAdmin = kws.some(kw => d.answer.toLowerCase().includes(kw));
      
      setMsgs(p => [...p, { 
        text: d.answer || 'Xatolik yuz berdi.', 
        type: 'bot', 
        options: d.options,
        showAdmin 
      }]);
    } catch {
      setMsgs(p => [...p, { text: 'Serverga ulanishda xatolik.', type: 'bot' }]);
    }
    setTyping(false);
  }

  async function handleAskAdmin() {
    const metaStr = localStorage.getItem('tg_user');
    const meta = metaStr ? JSON.parse(metaStr) : {};
    setTyping(true);
    try {
      await askAdmin(lastQuestion, meta);
      setMsgs(p => [...p, { text: '📩 Savolingiz adminstratorga yuborildi. Tez orada javob olasiz!', type: 'bot' }]);
    } catch {
      setMsgs(p => [...p, { text: 'Xatolik: Adminstratorga yuborib bo\'lmadi.', type: 'bot' }]);
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
      <div className={`student-header${tab !== 'home' ? ' mini' : ''}`}>
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div className="premium-glow" />
          <div className="student-badge">UZNPUU ECOSYSTEM</div>
          <div className="student-title-container">
            <div className="student-title-uznpuu">UzNPUU</div>
            <div className="student-title-yordamchi">Yordamchi</div>
          </div>
          <div className="student-description">
            Innovatsion ta&#39;lim universiteti uchun aqlli yordamchi tizim
          </div>
          <div className="header-actions">
            <div className="h-stat">
              <span className="h-stat-val">24/7</span>
              <span className="h-stat-lbl">Online Support</span>
            </div>
            <div className="h-sep" />
            <div className="h-stat">
              <span className="h-stat-val">AI</span>
              <span className="h-stat-lbl">Smart Engine</span>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {tab === 'home' && (
          <div className="home-wrap" style={{ paddingTop: 0 }}>
            <div className="card-grid">
              {/* Static core cards */}
              <div className="home-card" onClick={() => setTab('faq')}>
                <div className="card-icon-box" style={{ background: darkMode ? 'rgba(99, 102, 241, 0.15)' : '#eef2ff' }}>📋</div>
                <div className="card-info">
                  <div className="card-title">FAQ</div>
                  <div className="card-desc">Tez-tez soraladigan</div>
                </div>
              </div>
              
              <div className="home-card" onClick={() => setTab('profile')}>
                <div className="card-icon-box" style={{ background: darkMode ? 'rgba(99, 102, 241, 0.15)' : '#eef2ff' }}>👤</div>
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
              {msgs.map((m, i) => (
                <div key={i}>
                  <div className={`msg ${m.type}`}>{m.text}</div>
                  {m.type === 'bot' && (m.options?.length || m.showAdmin) && (
                    <div className="suggs" style={{ marginTop: 8, marginBottom: 16 }}>
                      {m.options?.map(opt => (
                        <button key={opt} className="sugg" onClick={() => send(opt)}>{opt}</button>
                      ))}
                      {m.showAdmin && (
                        <button 
                          className="sugg" 
                          style={{ borderColor: '#ef4444', color: '#ef4444' }} 
                          onClick={() => { m.showAdmin = false; handleAskAdmin(); }}>
                          👤 Adminstratorga yuborish
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
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
            <div className="profile-card premium">
              <div className="profile-avatar shadow">
                👤
              </div>
              <div className="profile-name">
                {profile?.student_id ? 'Talaba Profili' : 'Ro&#39;yxatdan o&#39;tilmagan'}
              </div>
              <div className="profile-role">
                <span className="status-dot green" />
                FAOLLASHTIRILGAN TIZIM
              </div>
            </div>

            <div className="profile-list premium-list">
              <div className="profile-row">
                <span className="profile-label">Telegram ID</span>
                <span className="profile-value">{profile?.telegram_id || (localStorage.getItem('tg_user') ? JSON.parse(localStorage.getItem('tg_user')!).student_telegram_id : '—')}</span>
              </div>
              <div className="profile-row">
                <span className="profile-label">Student ID</span>
                <span className="profile-value" style={{ fontWeight: 700, color: '#4f46e5' }}>{profile?.student_id || '—'}</span>
              </div>
              <div className="profile-row">
                <span className="profile-label">Fakultet</span>
                <span className="profile-value">{profile?.faculty_name || 'Umumiy'}</span>
              </div>
              <div className="profile-row">
                <span className="profile-label">Toshkent davlat pedagogika universiteti</span>
              </div>
            </div>

            <div className="premium-footer">
              UzNPUU Ecosystem — Rasmiy talaba yordamchi tizimi
            </div>
          </div>
        )}
      </div>

      {/* Bottom Nav */}
      <nav className="student-nav">
        <button className={`s-nav-btn ${tab === 'home' ? 'active' : ''}`} onClick={() => setTab('home')}>
          <div className="s-nav-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
          </div>
          <span className="s-nav-label">Asosiy</span>
        </button>
        <button className={`s-nav-btn ${tab === 'chat' ? 'active' : ''}`} onClick={() => setTab('chat')}>
          <div className="s-nav-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><circle cx="12" cy="10" r="1" fill="currentColor"/><circle cx="16" cy="10" r="1" fill="currentColor"/><circle cx="8" cy="10" r="1" fill="currentColor"/></svg>
          </div>
          <span className="s-nav-label">Savol-javob</span>
        </button>
        <button className="s-nav-btn" onClick={() => setDarkMode(!darkMode)}>
          <div className="s-nav-icon">
            {darkMode ? (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
            ) : (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
            )}
          </div>
          <span className="s-nav-label">Mavzu</span>
        </button>
      </nav>
    </div>
  );
}
