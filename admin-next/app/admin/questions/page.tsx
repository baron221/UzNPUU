'use client';
import { useEffect, useState, useMemo, useRef } from 'react';
import { getQuestions, answerQuestion, type Question } from '@/lib/api';

export default function QuestionsPage() {
  const [all, setAll]           = useState<Question[]>([]);
  const [search, setSearch]     = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  
  const [ans, setAns]           = useState('');
  const [sending, setSending]   = useState(false);
  const [loading, setLoading]   = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  async function load(showSkeleton = true) {
    if (showSkeleton) setLoading(true);
    try {
      const qd = await getQuestions();
      setAll(qd.questions);
    } finally {
      if (showSkeleton) setLoading(false);
    }
  }

  useEffect(() => { 
    load();
    const interval = setInterval(() => load(false), 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [selectedId, all]);

  const grouped = useMemo(() => {
    const map = new Map<string, { id: string, name: string, username: string, faculty: string, questions: Question[], latest: string, unread: number }>();
    
    all.forEach(q => {
      const uid = q.student_telegram_id || q.student_username || String(q.student_id) || `anonymous-${q.id}`;
      if (!map.has(uid)) {
        map.set(uid, {
          id: uid,
          name: q.student_name || 'Noma\'lum talaba',
          username: q.student_username || '',
          faculty: q.faculty_name || 'Umumiy',
          questions: [],
          latest: q.created_at,
          unread: 0
        });
      }
      
      const u = map.get(uid)!;
      u.questions.push(q);
      
      if (new Date(q.created_at) > new Date(u.latest)) {
        u.latest = q.created_at;
        if (q.student_name) u.name = q.student_name;
        if (q.student_username) u.username = q.student_username;
        if (q.faculty_name) u.faculty = q.faculty_name;
      }
      
      if (q.status !== 'answered') {
        u.unread++;
      }
    });

    const lowerSearch = search.toLowerCase();
    
    return Array.from(map.values())
      .filter(u => {
        if (!search) return true;
        return u.name.toLowerCase().includes(lowerSearch) || 
               u.username.toLowerCase().includes(lowerSearch) ||
               u.questions.some(q => q.question.toLowerCase().includes(lowerSearch));
      })
      .sort((a, b) => new Date(b.latest).getTime() - new Date(a.latest).getTime());
  }, [all, search]);

  const activeChat = selectedId ? grouped.find(u => u.id === selectedId) : null;

  async function send() {
    if (!ans.trim() || !activeChat) return;
    
    const sortedQuestions = [...activeChat.questions].sort((a,b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    const unanswered = sortedQuestions.filter(q => q.status !== 'answered');
    
    // Attach to oldest pending question, or if all are answered, attach to the latest question
    const targetQ = unanswered.length > 0 ? unanswered[0] : sortedQuestions[sortedQuestions.length - 1];
    if (!targetQ) return;

    setSending(true);
    const d = await answerQuestion(targetQ.id, ans);
    setSending(false);
    
    if (d.ok) { 
      // Optimistic update so it shows immediately!
      targetQ.status = 'answered';
      targetQ.answer = ans;
      (targetQ as any).answered_at = new Date().toISOString();
      setAll([...all]);
      setAns(''); 
      load(false); 
    } else {
      alert('Xatolik: ' + d.error);
    }
  }

  const CAT: Record<string, string> = {
    MANUAL:'badge-red', UNIVERSITY:'badge-blue', VAGUE:'badge-purple',
  };
  const CAT_LABEL: Record<string, string> = { MANUAL:'MANUAL', UNIVERSITY:'UNI', VAGUE:'VAGUE' };

  function relativeTime(dateStr: string) {
    if (!dateStr) return '';
    try {
      const msPerMinute = 60 * 1000;
      const msPerHour = msPerMinute * 60;
      const msPerDay = msPerHour * 24;
      const elapsed = Date.now() - new Date(dateStr).getTime();
      
      if (elapsed < msPerMinute) return 'Hozirgina';
      if (elapsed < msPerHour) return Math.round(elapsed/msPerMinute) + ' d. oldin';
      if (elapsed < msPerDay) return Math.round(elapsed/msPerHour) + ' soat oldin';
      return Math.round(elapsed/msPerDay) + ' kun oldin';
    } catch {
      return dateStr;
    }
  }

  function formatTimeFull(dateStr: string) {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('uz-UZ') + ' ' + d.toLocaleTimeString('uz-UZ', {hour: '2-digit', minute:'2-digit'});
    } catch {
      return dateStr;
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sending && ans.trim()) {
        send();
      }
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Savollar (Chat)</div>
          <div className="page-sub">Talabalar bilan muloqot tizimi</div>
        </div>
        <button className="btn btn-blue" onClick={() => load(true)}>↻ Yangilash</button>
      </div>

      <div className="admin-chat-wrap">
        {/* SIDEBAR */}
        <div className="ac-sidebar">
          <div className="ac-sidebar-header">
            <div className="ac-sidebar-title">
              Chat Users
              <span className="badge badge-purple">{grouped.length}</span>
            </div>
            <input 
              className="form-inp" 
              placeholder="🔍 Ism, yozishma orqali izlash..." 
              value={search} 
              onChange={e => setSearch(e.target.value)} 
              style={{ padding: '10px 14px', fontSize: 13 }}
            />
          </div>
          
          <div className="ac-user-list">
            {loading && all.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8' }}>Yuklanmoqda...</div>
            ) : grouped.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8' }}>Hech qanday chat topilmadi.</div>
            ) : grouped.map(u => {
              const isActive = selectedId === u.id;
              const isUnread = u.unread > 0;
              let excerpt = [...u.questions].sort((a,b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()).pop()?.question || '';
              
              return (
                <div 
                  key={u.id} 
                  className={`ac-user-item ${isActive ? 'active' : ''}`}
                  onClick={() => { setSelectedId(u.id); setAns(''); }}
                >
                  <div className={`ac-avatar ${isUnread ? 'orange' : 'indigo'}`}>
                    {u.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="ac-user-info">
                    <div className="ac-user-name">
                      {u.name}
                      <span className="ac-time">{relativeTime(u.latest)}</span>
                    </div>
                    <div className="ac-user-id">
                      {u.username ? `@${u.username}` : `ID: ${u.id}`}
                    </div>
                    <div className="ac-user-excerpt" style={{ color: isUnread ? '#334155' : '#94a3b8', fontWeight: isUnread ? 600 : 400 }}>
                      {excerpt}
                      {isUnread && <span className="ac-unread-badge">{u.unread} yangi</span>}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* MAIN HISTORY */}
        <div className="ac-main">
          {activeChat ? (
            <>
              <div className="ac-main-header">
                <div>
                  <div className="ac-header-name">{activeChat.name}</div>
                  <div className="ac-header-meta">
                    <span>{activeChat.username ? `@${activeChat.username}` : activeChat.id}</span>
                    &bull;
                    <span>{activeChat.faculty}</span>
                    &bull;
                    <span>{activeChat.questions.length} messages</span>
                  </div>
                </div>
              </div>
              
              <div className="ac-messages">
                {[...activeChat.questions].sort((a,b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()).map(q => (
                  <div key={`thread-${q.id}`} style={{ display:'flex', flexDirection:'column', gap: 16 }}>
                    
                    <div className="ac-msg-wrap user">
                      <div className="ac-msg-bubble">
                        {q.question}
                        <span className={`badge ${CAT[q.category] ?? 'badge-blue'}`} style={{ marginLeft: 8, fontSize: 10, borderRadius: 6, fontWeight: 700 }}>
                          {CAT_LABEL[q.category] ?? q.category}
                        </span>
                      </div>
                      <div className="ac-msg-time">{formatTimeFull(q.created_at)}</div>
                    </div>
                    
                    {q.status === 'answered' && q.answer && (
                      <div className="ac-msg-wrap admin">
                        <div className="ac-msg-bubble">
                          {q.answer}
                        </div>
                        <div className="ac-msg-time">
                          <span style={{ display:'inline-flex', alignItems:'center', gap:4 }}>
                            { (q as any).answered_at 
                              ? <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                              : <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4l3 3"></path></svg>
                            }
                            {(q as any).answered_at ? 'Admin' : 'AI Javobi'}
                          </span>
                          &nbsp;&bull; Javob berildi
                        </div>
                      </div>
                    )}
                    
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              <div className="ac-input-area">
                <textarea 
                  className="ac-textarea" 
                  rows={3} 
                  placeholder="Talabaga javob yozish (Yuborish uchun Enter)..."
                  value={ans}
                  onChange={e => setAns(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <div className="ac-input-actions">
                  <span style={{ fontSize: 13, color: '#94a3b8' }}>
                    Javobingiz Telegram orqali yuboriladi.
                  </span>
                  <button className="btn btn-primary" onClick={send} disabled={sending || !ans.trim()}>
                    {sending ? 'Yuborilmoqda...' : '📤 Yuborish'}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div style={{ margin: 'auto', textAlign:'center', color: '#94a3b8' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>💬</div>
              <div style={{ fontSize: 18, color: '#0f172a', fontWeight: 600, marginBottom: 8 }}>Chatni tanlang</div>
              <div>Yozishmani ko'rish uchun chap tomondan talabani tanlang.</div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
