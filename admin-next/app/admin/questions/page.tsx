'use client';
import { useEffect, useState, useMemo, useRef } from 'react';
import { getQuestions, answerQuestion, markChatAsRead, type Question } from '@/lib/api';

export default function QuestionsPage() {
  const [all, setAll]           = useState<Question[]>([]);
  const [search, setSearch]     = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filterUnanswered, setFilterUnanswered] = useState(false);
  
  const [ans, setAns]           = useState('');
  const [sending, setSending]   = useState(false);
  const [loading, setLoading]   = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  async function load(showSkeleton = true) {
    if (showSkeleton) setLoading(true);
    try {
      const qd = await getQuestions();
      setAll(qd?.questions || []);
    } catch (err) {
      console.error('Failed to load questions:', err);
      setAll([]);
    } finally {
      if (showSkeleton) setLoading(false);
    }
  }

  useEffect(() => { 
    load();
    const interval = setInterval(() => load(false), 10000);
    return () => clearInterval(interval);
  }, []);

  // Parse status parameter on mount to toggle unanswered filter
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('status') === 'unanswered') {
        setFilterUnanswered(true);
        // Clear parameter from URL to allow natural navigation
        const url = new URL(window.location.href);
        url.searchParams.delete('status');
        window.history.replaceState(null, '', url.pathname + url.search);
      }
    }
  }, []);



  const unansweredChatsCount = useMemo(() => {
    const map = new Map<string, boolean>();
    if (!Array.isArray(all)) return 0;
    all.forEach(q => {
      if (q.status !== 'answered') {
        const uid = q.student_telegram_id || q.student_username || String(q.student_id) || `anonymous-${q.id}`;
        map.set(uid, true);
      }
    });
    return map.size;
  }, [all]);

  const grouped = useMemo(() => {
    const map = new Map<string, { id: string, name: string, username: string, faculty: string, questions: Question[], latest: string, unread: number }>();
    
    if (!Array.isArray(all)) return [];

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
        if (filterUnanswered && u.unread === 0) return false;
        if (!search) return true;
        return u.name.toLowerCase().includes(lowerSearch) || 
               u.username.toLowerCase().includes(lowerSearch) ||
               u.questions.some(q => q.question.toLowerCase().includes(lowerSearch));
      })
      .sort((a, b) => new Date(b.latest).getTime() - new Date(a.latest).getTime());
  }, [all, search, filterUnanswered]);

  // Auto-select chat from URL parameters (e.g. ?tg_id=12345 or ?student_id=250244)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tgId = params.get('tg_id');
      const studentId = params.get('student_id');
      if (tgId || studentId) {
        const found = grouped.find(u => 
          (tgId && u.id === tgId) || 
          (studentId && u.questions.some(q => String(q.student_id) === String(studentId)))
        );
        if (found) {
          if (selectedId !== found.id) {
            setSelectedId(found.id);
          }
          // Clear query parameters from URL to unlock Selection
          const url = new URL(window.location.href);
          url.searchParams.delete('tg_id');
          url.searchParams.delete('student_id');
          window.history.replaceState(null, '', url.pathname + url.search);
        }
      }
    }
  }, [grouped, selectedId]);

  useEffect(() => {
    if (selectedId) {
      const chat = grouped.find(g => g.id === selectedId);
      if (chat && chat.unread > 0) {
        markChatAsRead(selectedId).then(() => {
          setAll(prev => prev.map(q => 
            (q.student_telegram_id === selectedId && q.status !== 'answered') 
              ? { ...q, status: 'answered' } 
              : q
          ));
        }).catch(console.error);
      }
    }
  }, [selectedId, all, grouped]);

  const activeChat = selectedId ? grouped.find(u => u.id === selectedId) : null;
  const activeChatLength = activeChat?.questions.length || 0;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [selectedId, activeChatLength]);

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
      // Refresh to get the new ID and status from server immediately
      setAns(''); 
      await load(false); 
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
      const date = new Date(dateStr);
      const now = new Date();
      const isToday = date.getDate() === now.getDate() && 
                      date.getMonth() === now.getMonth() && 
                      date.getFullYear() === now.getFullYear();
      if (isToday) {
        return date.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' });
      } else {
        return date.toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit', year: 'numeric' });
      }
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

  const renderMessageText = (text: string) => {
    if (!text) return '';
    const imgRegex = /\[IMAGE:\s*(https?:\/\/[^\s\]]+)\]/gi;
    const fileRegex = /\[FILE:\s*(https?:\/\/[^\s\]]+)\]/gi;
    
    let match;
    let imageUrl: string | null = null;
    let fileUrl: string | null = null;
    
    let cleanText = text;
    
    // We execute regex and replace matched text
    const imgMatch = imgRegex.exec(text);
    if (imgMatch) {
      imageUrl = imgMatch[1];
      cleanText = cleanText.replace(imgMatch[0], '');
    }
    const fileMatch = fileRegex.exec(text);
    if (fileMatch) {
      fileUrl = fileMatch[1];
      cleanText = cleanText.replace(fileMatch[0], '');
    }
    
    cleanText = cleanText.trim();
    
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {imageUrl && (
          <div style={{ margin: '4px 0', maxWidth: '320px', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <a href={imageUrl} target="_blank" rel="noopener noreferrer" style={{ display: 'block', cursor: 'zoom-in' }}>
              <img 
                src={imageUrl} 
                alt="Attached Media" 
                style={{ maxWidth: '100%', height: 'auto', display: 'block', maxHeight: '240px', objectFit: 'cover' }} 
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            </a>
          </div>
        )}
        {fileUrl && (
          <div style={{ margin: '4px 0' }}>
            <a 
              href={fileUrl} 
              target="_blank" 
              rel="noopener noreferrer" 
              style={{ 
                display: 'inline-flex', 
                alignItems: 'center', 
                gap: '8px', 
                padding: '8px 12px', 
                background: '#f1f5f9', 
                border: '1px solid #cbd5e1', 
                borderRadius: '6px', 
                fontSize: '13px', 
                color: '#2563eb', 
                fontWeight: 600, 
                textDecoration: 'none' 
              }}
            >
              📎 Hujjatni yuklab olish
            </a>
          </div>
        )}
        {cleanText && <span style={{ whiteSpace: 'pre-wrap' }}>{cleanText}</span>}
      </div>
    );
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

      <div className={`admin-chat-wrap ${selectedId ? 'active-chat-selected' : ''}`}>
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
            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <button
                className={`btn btn-sm ${!filterUnanswered ? 'btn-primary' : 'btn-blue'}`}
                style={{ flex: 1, height: '32px', padding: '0 12px' }}
                onClick={() => setFilterUnanswered(false)}
              >
                Barchasi
              </button>
              <button
                className={`btn btn-sm ${filterUnanswered ? 'btn-primary' : 'btn-red'}`}
                style={{ flex: 1, height: '32px', padding: '0 12px', whiteSpace: 'nowrap' }}
                onClick={() => setFilterUnanswered(true)}
              >
                🔴 Javobsizlar ({unansweredChatsCount})
              </button>
            </div>
          </div>
          
          <div className="ac-user-list">
            {loading && all.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8' }}>Yuklanmoqda...</div>
            ) : grouped.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8' }}>Hech qanday chat topilmadi.</div>
            ) : grouped.map(u => {
              const isActive = selectedId === u.id;
              const isUnread = u.unread > 0;
              const latestQ = [...u.questions].sort((a,b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime() || a.id - b.id).pop();
              let excerpt = '';
              if (latestQ) {
                if (latestQ.status === 'answered' && latestQ.answer) {
                  excerpt = latestQ.answer.startsWith('Javob:') ? latestQ.answer : `Javob: ${latestQ.answer}`;
                } else {
                  const qText = latestQ.question?.trim() ?? '';
                  const isPlaceMeta = ['__ADMIN_FOLLOW_UP__', 'Adminstruatordan xabari', '(Admin xabari)'].includes(qText);
                  excerpt = isPlaceMeta ? "Admin xabari..." : qText;
                }
              }
              
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
                <button className="ac-back-btn" onClick={() => setSelectedId(null)}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 6 }}>
                    <line x1="19" y1="12" x2="5" y2="12"></line>
                    <polyline points="12 19 5 12 12 5"></polyline>
                  </svg>
                  Orqaga
                </button>
                <div>
                  <div className="ac-header-name">
                    {activeChat.name}
                    <span style={{ marginLeft: 12, fontSize: 13, background: '#f1f5f9', padding: '2px 8px', borderRadius: 6, color: '#64748b', fontWeight: 600 }}>
                      ID: {activeChat.questions[0]?.student_id || activeChat.id}
                    </span>
                  </div>
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
                {[...activeChat.questions].sort((a,b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime() || a.id - b.id).map(q => (
                  <div key={`thread-${q.id}`} style={{ display:'flex', flexDirection:'column', gap: 16 }}>
                    
                    {/* Only show the 'user' (student) bubble if it's NOT an internal admin follow-up placeholder */}
                    {!['__ADMIN_FOLLOW_UP__', 'Adminstruatordan xabari', '(Admin xabari)'].includes(q.question?.trim()) && (
                      <div className="ac-msg-wrap user">
                        <div className="ac-msg-bubble">
                          {renderMessageText(q.question)}
                          <span className={`badge ${CAT[q.category] ?? 'badge-blue'}`} style={{ marginLeft: 8, fontSize: 10, borderRadius: 6, fontWeight: 700 }}>
                            {CAT_LABEL[q.category] ?? q.category}
                          </span>
                        </div>
                        <div className="ac-msg-time">{formatTimeFull(q.created_at)}</div>
                      </div>
                    )}
                    
                    {/* Admin/AI Bubble: Show if an answer exists, even if status is pending */}
                    {q.answer && (
                      <div className="ac-msg-wrap admin">
                        <div className="ac-msg-bubble">
                          {renderMessageText(q.answer)}
                        </div>
                        <div className="ac-msg-time">
                          <span style={{ display:'inline-flex', alignItems:'center', gap:4 }}>
                            { (q as any).answered_at 
                              ? <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                              : <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4l3 3"></path></svg>
                            }
                            { (q as any).answered_at 
                              ? ((q as any).answered_by_name || String((q as any).answered_by || 'Admin').replace('TG:', ''))
                              : 'AI Javobi'
                            }
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
                    rows={1}
                    style={{ minHeight: '52px', maxHeight: '200px', overflowY: 'auto', resize: 'none' }}
                    placeholder="Talabaga javob yozish (Yuborish uchun Enter)..."
                    value={ans}
                    onChange={e => {
                      setAns(e.target.value);
                      e.target.style.height = 'auto';
                      e.target.style.height = e.target.scrollHeight + 'px';
                    }}
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
