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
  const [tab, setTab]         = useState<Tab>('home');
  const [cards, setCards]     = useState<ServiceCard[]>([]);
  const [msgs, setMsgs]       = useState<Msg[]>([{ text: '👋 Salom! Men UzNPUU botiman. Savolingizni yozing — yordam beraman!', type: 'bot' }]);
  const [input, setInput]     = useState('');
  const [typing, setTyping]   = useState(false);
  const [faqQ, setFaqQ]       = useState('');
  const [openFAQ, setOpenFAQ] = useState<string | null>(null);
  const msgsRef = useRef<HTMLDivElement>(null);

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
    <div className="student-wrap">
      {/* Header */}
      <div className="student-header">
        <div className="student-logo">
          <img src="/bot-icon.png" alt="Bot" />
        </div>
        <div>
          <div className="student-title">UzNPUU Bot</div>
          <div className="student-sub">Universitet yordamchisi • 24/7</div>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {tab === 'home' && (
          <div className="home-wrap">
            <div className="home-title">Xizmatlar</div>
            <div className="card-grid">
              {/* Static core cards */}
              <div className="home-card" onClick={() => setTab('faq')}>
                <div className="card-icon-box" style={{ background: 'rgba(108, 92, 231, 0.1)' }}>📋</div>
                <div className="card-info">
                  <div className="card-title">FAQ</div>
                  <div className="card-desc">Tez-tez so'raladigan savollar</div>
                </div>
              </div>
              <div className="home-card" onClick={() => setTab('profile')}>
                <div className="card-icon-box" style={{ background: 'rgba(0, 184, 148, 0.1)' }}>👤</div>
                <div className="card-info">
                  <div className="card-title">Profilim</div>
                  <div className="card-desc">GPA va ma'lumotlar</div>
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
              <div className="profile-name">UzNPUU Talabasi</div>
              <div className="profile-role">🎓 Bakalavr talabasi</div>
              <div className="profile-row"><span className="profile-label">Universitet</span><span className="profile-value">UzNPUU</span></div>
              <div className="profile-row"><span className="profile-label">Bot versiyasi</span><span className="profile-value">v2.0</span></div>
              <div className="profile-row"><span className="profile-label">Til</span><span className="profile-value">🇺🇿 O&#39;zbek</span></div>
            </div>
            <div className="profile-card" style={{ textAlign:'center', padding:20 }}>
              <div style={{ fontSize:13, color:'var(--muted)', lineHeight:1.7 }}>
                Bot yordamida arzon va tez ravishda savolaringizga javob oling.<br/>
                Muammolar bo&#39;lsa adminga murojaat qiling.
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Nav */}
      <nav className="student-nav">
        {([['home','🏠','Asosiy'], ['chat','💬','Chat'], ['faq','📋','FAQ'], ['profile','👤','Profil']] as const).map(([t,icon,label]) => (
          <button key={t} className={`s-nav-btn${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
            <span className="s-nav-icon">{icon}</span>{label}
          </button>
        ))}
      </nav>
    </div>
  );
}
