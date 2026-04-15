'use client';
import { useEffect, useState } from 'react';
import { getAdminCards, createCard, updateCard, deleteCard, type ServiceCard } from '@/lib/api';

export default function CardsPage() {
  const [cards, setCards]     = useState<ServiceCard[]>([]);
  const [modal, setModal]     = useState(false);
  const [editId, setEditId]   = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm]       = useState({ title: '', description: '', icon: '🌟', link: '', type: 'message' as const, is_active: 1 });

  async function load() {
    setLoading(true);
    const d = await getAdminCards();
    setCards(d.cards);
    setLoading(false);
  }
  useEffect(() => { load(); }, []);

  async function save() {
    if (!form.title) { alert("Sarlavha kiritish shart!"); return; }
    if (editId) await updateCard(editId, form);
    else await createCard(form);
    
    closeModal();
    load();
  }

  function openModal(c?: ServiceCard) {
    if (c) {
      setEditId(c.id);
      setForm({ title: c.title, description: c.description, icon: c.icon, link: c.link, type: c.type, is_active: c.is_active });
    } else {
      setEditId(null);
      setForm({ title: '', description: '', icon: '🌟', link: '', type: 'message', is_active: 1 });
    }
    setModal(true);
  }

  function closeModal() {
    setModal(false);
    setEditId(null);
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Xizmatlar Boshqaruvi</div>
          <div className="page-sub">Dashboard kardiogrammalarini boshqarish</div>
        </div>
        <button className="btn btn-primary" onClick={() => openModal()}>+ Yangi karda</button>
      </div>

      {loading ? (
        <div className="table-card">
          {[1,2,3].map(i => <div key={i} style={{ padding:'16px 18px', borderBottom:'1px solid #f1f2f9' }}><div className="skeleton" style={{ height:14, width:'75%' }} /></div>)}
        </div>
      ) : (
        <div className="table-card">
          <table>
            <thead><tr><th>Ikon</th><th>Sarlavha</th><th>Tavsif</th><th>Turi</th><th>Holati</th><th></th></tr></thead>
            <tbody>
              {cards.length === 0 ? <tr><td colSpan={6} className="empty">Kardalar yo'q</td></tr>
                : cards.map(c => (
                  <tr key={c.id}>
                    <td style={{ fontSize:20 }}>{c.icon}</td>
                    <td style={{ fontWeight:600 }}>{c.title}</td>
                    <td style={{ color:'var(--muted)', maxWidth:200 }}>{c.description}</td>
                    <td><span className="badge">{c.type}</span></td>
                    <td><span className={`badge ${c.is_active ? 'badge-green' : 'badge-red'}`}>{c.is_active ? 'Faol' : 'Nofaol'}</span></td>
                    <td style={{ textAlign:'right' }}>
                      <button className="btn btn-sm" onClick={() => openModal(c)} style={{ marginRight:6 }}>Tahrir</button>
                      <button className="btn btn-sm btn-red" onClick={async () => { if (confirm("O'chirasizmi?")) { await deleteCard(c.id); load(); } }}>O'chir</button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && closeModal()}>
          <div className="modal">
            <div className="modal-title">{editId ? 'Kardani tahrirlash' : 'Yangi karda qo\'shish'}</div>
            
            <div className="form-row">
              <label className="form-label">Ikon (Emoji)</label>
              <input className="form-inp" style={{ width:60, textAlign:'center' }} value={form.icon} onChange={e => setForm(p => ({ ...p, icon: e.target.value }))} />
            </div>

            <div className="form-row">
              <label className="form-label">Sarlavha</label>
              <input className="form-inp" placeholder="Karda nomi..." value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} />
            </div>

            <div className="form-row">
              <label className="form-label">Tavsif</label>
              <textarea className="form-inp" rows={2} placeholder="Qisqacha tavsif..." value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} />
            </div>

            <div className="form-row">
              <label className="form-label">Turi</label>
              <select className="form-inp" value={form.type} onChange={e => setForm(p => ({ ...p, type: e.target.value as any }))}>
                <option value="message">Xabar yuborish (send as user)</option>
                <option value="link">Havola (Link)</option>
                <option value="tab">Ichki Tabga o'tish</option>
              </select>
            </div>

            <div className="form-row">
              <label className="form-label">Havola / Xabar / Tab nomi</label>
              <input className="form-inp" placeholder="Masalan: /faq yoki Salom..." value={form.link} onChange={e => setForm(p => ({ ...p, link: e.target.value }))} />
            </div>

            <div className="form-row" style={{ flexDirection:'row', alignItems:'center', gap:10 }}>
              <input type="checkbox" checked={!!form.is_active} onChange={e => setForm(p => ({ ...p, is_active: e.target.checked ? 1 : 0 }))} />
              <label className="form-label" style={{ marginBottom:0 }}>Faol</label>
            </div>

            <div className="modal-actions">
              <button className="btn btn-red" onClick={closeModal}>Bekor</button>
              <button className="btn btn-primary" onClick={save}>Saqlash</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
