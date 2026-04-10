'use client';
import { useEffect, useState } from 'react';
import { getQuestions, getFaculties, answerQuestion, type Question, type Faculty } from '@/lib/api';

export default function QuestionsPage() {
  const [all, setAll]           = useState<Question[]>([]);
  const [faculties, setFaculties] = useState<Faculty[]>([]);
  const [fFilter, setFFilter]   = useState('');
  const [sFilter, setSFilter]   = useState('');
  const [search, setSearch]     = useState('');
  const [reply, setReply]       = useState<Question | null>(null);
  const [ans, setAns]           = useState('');
  const [sending, setSending]   = useState(false);
  const [loading, setLoading]   = useState(true);

  async function load(showSkeleton = true) {
    if (showSkeleton) setLoading(true);
    try {
      const [qd, fd] = await Promise.all([getQuestions(), getFaculties()]);
      setAll(qd.questions);
      setFaculties(fd.faculties);
    } finally {
      if (showSkeleton) setLoading(false);
    }
  }

  useEffect(() => { 
    load();
    // Har 10 soniyada orqa fonda yangilab turish (auto update)
    const interval = setInterval(() => load(false), 10000);
    return () => clearInterval(interval);
  }, []);

  const filtered = all.filter(q => {
    if (fFilter && String(q.faculty_name) !== fFilter) return false;
    if (sFilter && q.status !== sFilter) return false;
    if (search) {
      const s = search.toLowerCase();
      return q.question.toLowerCase().includes(s) || (q.student_username ?? '').toLowerCase().includes(s);
    }
    return true;
  });

  async function send() {
    if (!ans.trim() || !reply) return;
    setSending(true);
    const d = await answerQuestion(reply.id, ans);
    setSending(false);
    if (d.ok) { setReply(null); setAns(''); load(); }
    else alert('Xatolik: ' + d.error);
  }

  const CAT: Record<string, string> = {
    MANUAL:'badge-red', UNIVERSITY:'badge-blue', VAGUE:'badge-purple',
  };
  const CAT_LABEL: Record<string, string> = { MANUAL:'MANUAL', UNIVERSITY:'UNI', VAGUE:'VAGUE' };

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Savollar</div>
          <div className="page-sub">Talabalar yuborgan barcha savollar</div>
        </div>
        <button className="btn btn-primary" onClick={() => load(true)}>↻ Yangilash</button>
      </div>

      <div className="filter-row">
        <select className="filter-select" value={fFilter} onChange={e => setFFilter(e.target.value)}>
          <option value="">Barcha fakultetlar</option>
          {faculties.map(f => <option key={f.id} value={f.name}>{f.name}</option>)}
        </select>
        <select className="filter-select" value={sFilter} onChange={e => setSFilter(e.target.value)}>
          <option value="">Barcha statuslar</option>
          <option value="answered">✅ Javob berilgan</option>
          <option value="unanswered">❓ Javobsiz</option>
        </select>
        <input className="search-inp" placeholder="🔍 Qidirish..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {loading ? (
        <div className="table-card">
          {[1,2,3,4].map(i => (
            <div key={i} style={{ padding:'16px 18px', borderBottom:'1px solid #f1f2f9', display:'flex', gap:12 }}>
              <div className="skeleton" style={{ height:14, width:80 }} />
              <div className="skeleton" style={{ height:14, flex:1 }} />
              <div className="skeleton" style={{ height:14, width:60 }} />
            </div>
          ))}
        </div>
      ) : (
        <div className="table-card">
          <table>
            <thead><tr>
              <th>Student ID</th><th>Tur</th><th>Talaba</th>
              <th>Fakultet</th><th>Savol</th><th>Status</th><th>Amal</th>
            </tr></thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={7} className="empty">Hech qanday savol yo&#39;q</td></tr>
              ) : filtered.map(q => {
                const student = q.student_username ? `@${q.student_username}` : q.student_name || '—';
                let statusBadge = '';
                if (q.status === 'answered') statusBadge = '✅ Javob berildi';
                else if (q.category === 'MANUAL') statusBadge = '🟠 Kutayotgan';
                else statusBadge = '❓ Topilmadi';
                const statusClass = q.status === 'answered' ? 'badge-green' : q.category === 'MANUAL' ? 'badge-orange' : 'badge-red';
                return (
                  <tr key={q.id}>
                    <td><span className="badge badge-orange">{q.student_id || '—'}</span></td>
                    <td><span className={`badge ${CAT[q.category] ?? 'badge-blue'}`}>{CAT_LABEL[q.category] ?? q.category}</span></td>
                    <td><strong>{student}</strong></td>
                    <td><span className="badge badge-purple">{q.faculty_name || 'Umumiy'}</span></td>
                    <td style={{ maxWidth:260, color:'var(--muted)' }}>{q.question}</td>
                    <td><span className={`badge ${statusClass}`}>{statusBadge}</span></td>
                    <td>
                      <button className="btn btn-sm btn-blue" onClick={() => { setReply(q); setAns(''); }}>
                        Javob berish
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Reply Modal */}
      {reply && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setReply(null)}>
          <div className="modal">
            <div className="modal-title">Talabaga javob berish</div>
            <div className="info-box" style={{ marginBottom:20 }}>
              <strong>Savol:</strong> {reply.question}
            </div>
            <div className="form-row">
              <label className="form-label">Sizning javobingiz *</label>
              <textarea className="form-inp" rows={4} placeholder="Tushunarli va aniq javob yozing..."
                value={ans} onChange={e => setAns(e.target.value)} />
            </div>
            <div className="modal-actions">
              <button className="btn btn-red" onClick={() => setReply(null)}>Bekor</button>
              <button className="btn btn-primary" onClick={send} disabled={sending}>
                {sending ? 'Yuborilmoqda...' : '📤 Yuborish'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
