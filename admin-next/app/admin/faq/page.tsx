'use client';
import { useEffect, useState } from 'react';
import { getFAQ, createFAQ, deleteFAQ, updateFAQ, getFaculties, type FAQItem, type Faculty } from '@/lib/api';

export default function FAQPage() {
  const [items, setItems]       = useState<FAQItem[]>([]);
  const [faculties, setFaculties] = useState<Faculty[]>([]);
  const [modal, setModal]       = useState(false);
  const [editId, setEditId]     = useState<number | null>(null);
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
    if (editId) {
      await updateFAQ(editId, { ...form, faculty_id: form.faculty_id ? Number(form.faculty_id) : undefined });
    } else {
      await createFAQ({ ...form, faculty_id: form.faculty_id ? Number(form.faculty_id) : undefined });
    }
    setForm({ faculty_id: '', question: '', answer: '' });
    setEditId(null);
    setModal(false);
    load();
  }

  return (
    <>
      <div className="page-header">
        <div><div className="page-title">FAQ Boshqaruv</div><div className="page-sub">Savol-javob qo&#39;shish va tahrirlash</div></div>
        <button className="btn btn-primary" onClick={() => { setEditId(null); setForm({ faculty_id: '', question: '', answer: '' }); setModal(true); }}>+ Yangi savol</button>
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
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="btn btn-sm btn-primary" onClick={() => { setEditId(f.id); setForm({ faculty_id: String(f.faculty_id || ''), question: f.question, answer: f.answer }); setModal(true); }}>Tahrirlash</button>
                        <button className="btn btn-sm btn-red" onClick={async () => { if (confirm("O'chirasizmi?")) { await deleteFAQ(f.id); load(); } }}>O&#39;chirish</button>
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setModal(false)}>
          <div className="modal">
            <div className="modal-title">{editId ? "Savol-javobni tahrirlash" : "Yangi savol-javob qo'shish"}</div>
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
            <div className="modal-actions">
              <button className="btn btn-red" onClick={() => setModal(false)}>Bekor</button>
              <button className="btn btn-primary" onClick={add}>Saqlash</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
