'use client';
import { useState, useRef, useEffect } from 'react';
import { askQuestion, getCards, askAdmin, getStudentHistory, type ServiceCard, type HistoryItem } from '@/lib/api';

type Msg = { text: string; type: 'user' | 'bot'; options?: string[]; showAdmin?: boolean; isHistory?: boolean; isPending?: boolean };
type Tab = 'home' | 'chat' | 'faq' | 'profile';

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
  const [msgs, setMsgs]       = useState<Msg[]>([]);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [input, setInput]     = useState('');
  const [typing, setTyping]   = useState(false);
  const [faqQ, setFaqQ]       = useState('');
  const [openFAQ, setOpenFAQ] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState('');
  const [loadingCards, setLoadingCards] = useState(false);
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
    // Attempt to load faculty_id from stored user metadata
    const metaStr = localStorage.getItem('tg_user');
    let fid = null;
    if (metaStr) {
      try {
        const meta = JSON.parse(metaStr);
        fid = meta.faculty_id || null;
      } catch (e) {}
    }
    
    setLoadingCards(true);
    getCards(fid).then(d => { 
      if (d?.cards) setCards(d.cards); 
    }).catch(err => {
      console.error('Failed to load cards:', err);
    }).finally(() => {
      setLoadingCards(false);
    });
  }, []);

  useEffect(() => {
    // @ts-ignore
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      const user = tg.initDataUnsafe?.user;
      if (user) {
        localStorage.setItem('tg_user', JSON.stringify({
          student_telegram_id: String(user.id),
          student_username: user.username,
          student_name: `${user.first_name || ''} ${user.last_name || ''}`.trim(),
        }));
      }
    }
  }, []);

  // Load unified history (bot + mini app) once when component mounts
  useEffect(() => {
    if (historyLoaded) return;
    const metaStr = localStorage.getItem('tg_user');
    if (!metaStr) {
      // No TG identity yet — show default welcome and mark done
      setMsgs([{ text: '👋 Salom! Men UzNPUU botiman. Savolingizni yozing — yordam beraman!', type: 'bot' }]);
      setHistoryLoaded(true);
      return;
    }
    const meta = JSON.parse(metaStr);
    const tgId: string = meta.student_telegram_id || '';
    if (!tgId || tgId === 'WEB') {
      setMsgs([{ text: '👋 Salom! Men UzNPUU botiman. Savolingizni yozing — yordam beraman!', type: 'bot' }]);
      setHistoryLoaded(true);
      return;
    }
    setLoadingHistory(true);
    getStudentHistory(tgId)
      .then(({ history }) => {
        const histMsgs: Msg[] = [];
        history.forEach((item: HistoryItem) => {
          // Student question
          histMsgs.push({ text: item.question, type: 'user', isHistory: true });
          // Bot/admin answer
          const answerText = item.answer && item.answer !== 'Admin javobini kuting...'
            ? item.answer
            : null;
          if (answerText) {
            histMsgs.push({ text: answerText, type: 'bot', isHistory: true });
          } else {
            histMsgs.push({ text: '⏳ Admin javobini kutilmoqda...', type: 'bot', isHistory: true, isPending: true });
          }
        });
        // Build final message list
        const welcomeMsg: Msg = { text: '👋 Salom! Men UzNPUU botiman. Savolingizni yozing — yordam beraman!', type: 'bot' };
        if (histMsgs.length > 0) {
          setMsgs([welcomeMsg, ...histMsgs]);
        } else {
          setMsgs([welcomeMsg]);
        }
      })
      .catch(() => {
        setMsgs([{ text: '👋 Salom! Men UzNPUU botiman. Savolingizni yozing — yordam beraman!', type: 'bot' }]);
      })
      .finally(() => {
        setHistoryLoaded(true);
        setLoadingHistory(false);
      });
  }, [historyLoaded]);

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
          <div className="student-badge">RASMIY BOT</div>
          <div className="student-title-container">
            <div className="student-title-uznpuu">UzNPUU</div>
            <div className="student-title-yordamchi">Yordamchi</div>
          </div>
          <div className="student-sub" style={{ marginTop: 20, fontSize: 13, lineHeight: 1.6, maxWidth: '85%', opacity: 0.8, fontWeight: 500 }}>Nizomiy nomidagi O&#39;zbekiston Milliy pedagogika universiteti</div>
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

              {loadingCards && (
                <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: 20 }}>
                  <div className="dots" style={{ margin: '0 auto' }}><span /><span /><span /></div>
                </div>
              )}

              {!loadingCards && cards.length === 0 && (
                <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: 20, color: 'var(--muted)', fontSize: 13 }}>
                  New services will be added soon...
                </div>
              )}

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
              {/* Loading history skeleton */}
              {loadingHistory && (
                <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--muted)', fontSize: 12 }}>
                  <div className="dots" style={{ margin: '0 auto 8px' }}><span /><span /><span /></div>
                  Oldingi suhbat yuklanmoqda...
                </div>
              )}

              {/* History separator — only show if there are history messages */}
              {!loadingHistory && msgs.some(m => m.isHistory) && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '12px 16px', color: 'var(--muted)', fontSize: 11,
                }}>
                  <div style={{ flex: 1, height: 1, background: 'var(--border, rgba(99,102,241,0.15))' }} />
                  <span style={{ whiteSpace: 'nowrap', fontWeight: 600, letterSpacing: '0.05em' }}>📅 OLDINGI SUHBAT</span>
                  <div style={{ flex: 1, height: 1, background: 'var(--border, rgba(99,102,241,0.15))' }} />
                </div>
              )}

              {msgs.map((m, i) => {
                // Separator between history and new session messages
                const isFirstLive = !m.isHistory && i > 0 && msgs[i - 1]?.isHistory;
                return (
                  <div key={i}>
                    {isFirstLive && (
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 8,
                        padding: '12px 16px', color: 'var(--muted)', fontSize: 11,
                      }}>
                        <div style={{ flex: 1, height: 1, background: 'var(--border, rgba(99,102,241,0.15))' }} />
                        <span style={{ whiteSpace: 'nowrap', fontWeight: 600, letterSpacing: '0.05em' }}>✨ YANGI SUHBAT</span>
                        <div style={{ flex: 1, height: 1, background: 'var(--border, rgba(99,102,241,0.15))' }} />
                      </div>
                    )}
                    <div
                      className={`msg ${m.type}`}
                      style={m.isHistory ? { opacity: m.isPending ? 0.6 : 0.75 } : undefined}
                    >
                      {m.text}
                    </div>
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
                );
              })}
              {typing && (
                <div className="msg bot">
                  <div className="dots"><span /><span /><span /></div>
                </div>
              )}
            </div>
            {/* Show suggestions only when no history and no live messages yet */}
            {!loadingHistory && msgs.filter(m => !m.isHistory).length <= 1 && (
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
            <div className="profile-card" style={{ position: 'relative', overflow: 'hidden' }}>
              <div className="profile-avatar" style={{ background: 'linear-gradient(135deg, #6366f1, #a855f7)', color: '#fff', boxShadow: '0 10px 20px -5px rgba(99, 102, 241, 0.4)' }}>
                👤
              </div>
              <div className="profile-name">Talaba</div>
              <div className="profile-role">
                <span style={{ color: '#10b981', marginRight: 4 }}>●</span>
                FAOL TALABA
              </div>

              <div className="gpa-container" style={{ margin: '20px 0' }}>
                <div className="gpa-ring" style={{ 
                  background: `conic-gradient(#4f46e5 ${0.0 * 3.6}deg, ${darkMode ? '#0f172a' : '#f1f5f9'} 0)`,
                  boxShadow: '0 0 30px rgba(79, 70, 229, 0.1)'
                }}>
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
