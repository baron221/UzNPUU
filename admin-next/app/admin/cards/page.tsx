'use client';
import { useEffect, useState } from 'react';
import { getAdminCards, createCard, updateCard, deleteCard, type ServiceCard } from '@/lib/api';

const EMOJI_LIST = [
  '📋','📚','📝','📌','📎','📊','📈','📉','🗂️','🗃️',
  '🎓','🏫','👤','👥','💬','💡','🔔','🔍','⚙️','🛠️',
  '💰','💳','🏦','🎁','🌟','✅','❓','📣','🔗','🗓️',
  '📱','💻','🌐','🏆','📞','✉️','🚀','🧾','🔐','📂',
];

export default function CardsPage() {
  const [cards, setCards]     = useState<ServiceCard[]>([]);
  const [modal, setModal]     = useState(false);
  const [editId, setEditId]   = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [form, setForm] = useState({
    title: '', description: '', icon: '🌟', link: '',
    type: 'message' as ServiceCard['type'], is_active: 1
  });

  async function load() {
    setLoading(true);
    const d = await getAdminCards();
    setCards(d.cards);
    setLoading(false);
  }
  useEffect(() => { load(); }, []);

  async function save() {
    if (!form.title) { alert("Sarlavha kiritish shart!"); return; }
    let link = form.link;
    // Auto-add https:// for link type cards if missing
    if (form.type === 'link' && link && !link.startsWith('http://') && !link.startsWith('https://')) {
      link = 'https://' + link;
    }
    const payload = { ...form, link };
    if (editId) await updateCard(editId, payload);
    else await createCard(payload);
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
    setShowEmojiPicker(false);
    setModal(true);
  }

  function closeModal() {
    setModal(false);
    setEditId(null);
    setShowEmojiPicker(false);
  }

  const linkPlaceholder =
    form.type === 'link' ? 'https://example.com' :
    form.type === 'tab'  ? 'home | chat | faq | profile' :
    'Botga yuboriladigan xabar matni...';

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Xizmatlar Boshqaruvi</div>
          <div className="page-sub">Dashboard kartalarini boshqarish</div>
        </div>
        <button className="btn btn-primary" onClick={() => openModal()}>+ Yangi card</button>
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
              {cards.length === 0
                ? <tr><td colSpan={6} className="empty">Cardlar yo&apos;q</td></tr>
                : cards.map(c => (
                  <tr key={c.id}>
                    <td style={{ fontSize:20 }}>{c.icon}</td>
                    <td style={{ fontWeight:600 }}>{c.title}</td>
                    <td style={{ color:'var(--muted)', maxWidth:200 }}>{c.description}</td>
                    <td><span className="badge">{c.type}</span></td>
                    <td><span className={`badge ${c.is_active ? 'badge-green' : 'badge-red'}`}>{c.is_active ? 'Faol' : 'Nofaol'}</span></td>
                    <td style={{ textAlign:'right' }}>
                      <button className="btn btn-sm" onClick={() => openModal(c)} style={{ marginRight:6 }}>Tahrir</button>
                      <button className="btn btn-sm btn-red" onClick={async () => { if (confirm("O'chirasizmi?")) { await deleteCard(c.id); load(); } }}>O&apos;chir</button>
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && closeModal()}>
          <div className="modal">
            <div className="modal-title">{editId ? 'Cardni tahrirlash' : "Yangi card qo'shish"}</div>

            {/* Emoji Picker */}
            <div className="form-row">
              <label className="form-label">Ikon (Emoji)</label>
              <div style={{ display:'flex', gap:8, alignItems:'center' }}>
                <div
                  onClick={() => setShowEmojiPicker(p => !p)}
                  style={{ fontSize:28, cursor:'pointer', width:48, height:48, display:'flex', alignItems:'center', justifyContent:'center', border:'2px solid #e2e8f0', borderRadius:10, background:'#f8fafc' }}
                >
                  {form.icon}
                </div>
                <span style={{ fontSize:12, color:'#94a3b8' }}>Bosib emoji tanlang</span>
              </div>
              {showEmojiPicker && (
                <div style={{ marginTop:8, display:'grid', gridTemplateColumns:'repeat(10, 1fr)', gap:4, padding:10, background:'#f8fafc', borderRadius:10, border:'1px solid #e2e8f0' }}>
                  {EMOJI_LIST.map(em => (
                    <button
                      key={em}
                      onClick={() => { setForm(p => ({ ...p, icon: em })); setShowEmojiPicker(false); }}
                      style={{ fontSize:20, background:'none', border:'none', cursor:'pointer', padding:4, borderRadius:6 }}
                      onMouseOver={ev => (ev.currentTarget.style.background = '#e2e8f0')}
                      onMouseOut={ev => (ev.currentTarget.style.background = 'none')}
                    >
                      {em}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="form-row">
              <label className="form-label">Sarlavha</label>
              <input className="form-inp" placeholder="Karta nomi..." value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} />
            </div>

            <div className="form-row">
              <label className="form-label">Tavsif</label>
              <textarea className="form-inp" rows={2} placeholder="Qisqacha tavsif..." value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} />
            </div>

            <div className="form-row">
              <label className="form-label">Turi</label>
              <select className="form-inp" value={form.type} onChange={e => setForm(p => ({ ...p, type: e.target.value as ServiceCard['type'] }))}>
                <option value="message">Xabar yuborish (bot savol sifatida)</option>
                <option value="link">Tashqi havola (URL)</option>
                <option value="tab">Ichki Tabga o&apos;tish</option>
              </select>
            </div>

            <div className="form-row">
              <label className="form-label">
                {form.type === 'link' ? 'URL manzil' : form.type === 'tab' ? 'Tab nomi' : 'Xabar matni'}
              </label>
              <input
                className="form-inp"
                placeholder={linkPlaceholder}
                value={form.link}
                onChange={e => setForm(p => ({ ...p, link: e.target.value }))}
              />
              {form.type === 'link' && (
                <div style={{ fontSize:11, color:'#94a3b8', marginTop:4 }}>https:// avtomatik qo&apos;shiladi</div>
              )}
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
