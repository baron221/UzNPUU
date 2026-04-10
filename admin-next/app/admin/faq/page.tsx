'use client';
import { useEffect, useState } from 'react';
import { getFAQ, createFAQ, deleteFAQ, getFaculties, type FAQItem, type Faculty } from '@/lib/api';

export default function FAQPage() {
  const [items, setItems]       = useState<FAQItem[]>([]);
  const [faculties, setFaculties] = useState<Faculty[]>([]);
  const [form, setForm]         = useState({ faculty_id: '', question: '', answer: '' });
  const [loading, setLoading]   = useState(true);

  async function load() {
    setLoading(true);
    const [fd, fac] = await Promise.all([getFAQ(), getFaculties()]);
    setItems(fd.items); setFaculties(fac.faculties); setLoading(false);
  }
  useEffect(() => { load(); }, []);

  async function add() {
    if (!form.question || !form.answer) { alert("Savol va javob kiritish shart!"); return; }
    await createFAQ({ ...form, faculty_id: form.faculty_id ? Number(form.faculty_id) : undefined });
    setForm({ faculty_id: '', question: '', answer: '' });
    load();
  }

  return (
    <>
      <div className="page-header">
        <div><div className="page-title">FAQ Boshqaruv</div><div className="page-sub">Savol-javob qo&#39;shish</div></div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="section-title">Yangi savol-javob qo&#39;shish</div>
        <div className="form-row">
          <label className="form-label">Fakultet</label>
          <select className="form-inp" value={form.faculty_id} onChange={e => setForm(p => ({ ...p, faculty_id: e.target.value }))}>
            <option value="">Umumiy</option>
            {faculties.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
        </div>
        <div className="form-row">
          <label className="form-label">Savol</label>
          <input className="form-inp" placeholder="Savol matni..." value={form.question} onChange={e => setForm(p => ({ ...p, question: e.target.value }))} />
        </div>
        <div className="form-row">
          <label className="form-label">Javob</label>
          <textarea className="form-inp" rows={3} placeholder="Javob matni..." value={form.answer} onChange={e => setForm(p => ({ ...p, answer: e.target.value }))} />
        </div>
        <button className="btn btn-primary" onClick={add}>+ Qo&#39;shish</button>
      </div>

      {loading ? (
        <div className="table-card">
          {[1,2,3].map(i => <div key={i} style={{ padding:'16px 18px', borderBottom:'1px solid #f1f2f9' }}><div className="skeleton" style={{ height:14, width:'75%' }} /></div>)}
        </div>
      ) : (
        <div className="table-card">
          <table>
            <thead><tr><th>Fakultet</th><th>Savol</th><th>Javob</th><th></th></tr></thead>
            <tbody>
              {items.length === 0 ? <tr><td colSpan={4} className="empty">FAQ bo&#39;sh</td></tr>
                : items.map(f => (
                  <tr key={f.id}>
                    <td><span className="badge badge-purple">{f.faculty_name || 'Umumiy'}</span></td>
                    <td style={{ fontWeight:500 }}>{f.question}</td>
                    <td style={{ color:'var(--muted)', maxWidth:260 }}>{f.answer.slice(0, 80)}{f.answer.length > 80 ? '...' : ''}</td>
                    <td><button className="btn btn-sm btn-red" onClick={async () => { if (confirm("O'chirasizmi?")) { await deleteFAQ(f.id); load(); } }}>O&#39;chir</button></td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
