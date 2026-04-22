'use client';
import { useEffect, useState } from 'react';
import { getAdminCards, getFaculties, createCard, updateCard, deleteCard, reorderCard, type ServiceCard, type Faculty } from '@/lib/api';

const EMOJI_LIST = [
  '📋','📚','📝','📌','📎','📊','📈','📉','🗂️','🗃️',
  '🎓','🏫','👤','👥','💬','💡','🔔','🔍','⚙️','🛠️',
  '💰','💳','🏦','🎁','🌟','✅','❓','📣','🔗','🗓️',
  '📱','💻','🌐','🏆','📞','✉️','🚀','🧾','🔐','📂',
];

const emptyForm = {
  title: '', description: '', icon: '🌟', link: '',
  type: 'message' as ServiceCard['type'], is_active: 1,
  faculty_id: null as number | null,
  sort_order: 0,
  start_date: '',
  end_date: '',
};

export default function CardsPage() {
  const [cards, setCards]         = useState<ServiceCard[]>([]);
  const [faculties, setFaculties] = useState<Faculty[]>([]);
  const [modal, setModal]         = useState(false);
  const [editId, setEditId]       = useState<number | null>(null);
  const [loading, setLoading]     = useState(true);
  const [showEmoji, setShowEmoji] = useState(false);
  const [form, setForm]           = useState({ ...emptyForm });

  async function load() {
    setLoading(true);
    const [cd, fd] = await Promise.all([getAdminCards(), getFaculties()]);
    setCards(cd.cards);
    setFaculties(fd.faculties);
    setLoading(false);
  }
  useEffect(() => { load(); }, []);

  async function save() {
    if (!form.title) { alert('Sarlavha kiritish shart!'); return; }
    let link = form.link;
    if (form.type === 'link' && link && !link.startsWith('http://') && !link.startsWith('https://')) {
      link = 'https://' + link;
    }
    const payload = {
      ...form, link,
      faculty_id: form.faculty_id || null,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
    };
    if (editId) await updateCard(editId, payload);
    else await createCard(payload);
    closeModal();
    load();
  }

  function openModal(c?: ServiceCard) {
    if (c) {
      setEditId(c.id);
      setForm({
        title: c.title, description: c.description, icon: c.icon, link: c.link,
        type: c.type, is_active: c.is_active,
        faculty_id: c.faculty_id ?? null,
        sort_order: c.sort_order ?? 0,
        start_date: c.start_date ?? '',
        end_date: c.end_date ?? '',
      });
    } else {
      setEditId(null);
      setForm({ ...emptyForm });
    }
    setShowEmoji(false);
    setModal(true);
  }

  function closeModal() { setModal(false); setEditId(null); setShowEmoji(false); }

  async function handleReorder(id: number, dir: 'up' | 'down') {
    await reorderCard(id, dir);
    load();
  }

  const linkPlaceholder =
    form.type === 'link' ? 'https://example.com' :
    form.type === 'tab'  ? 'home | chat | faq | profile' :
    'Botga yuboriladigan xabar matni...';

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Cards</div>
          <div className="page-sub">Talaba dashboardidagi xizmatlar va kartalar boshqaruvi</div>
        </div>
        <button className="btn btn-primary" onClick={() => openModal()}>+ Yangi Card</button>
      </div>

      <div className="section-title">Mavjud Cards ({cards.length})</div>

      {loading ? (
        <div className="table-card">
          {[1,2,3].map(i => <div key={i} style={{ padding:'16px 18px', borderBottom:'1px solid #f1f2f9' }}><div className="skeleton" style={{ height:14, width:'75%' }} /></div>)}
        </div>
      ) : (
        <div className="table-card">
          <table>
            <thead>
              <tr>
                <th style={{width:40}}>№</th>
                <th>Ikon</th>
                <th>Sarlavha</th>
                <th>Fakultet</th>
                <th>Vaqt oralig&apos;i</th>
                <th>Turi</th>
                <th>Holat</th>
                <th>Tartib</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {cards.length === 0
                ? <tr><td colSpan={9} className="empty">Cardlar yo&apos;q</td></tr>
                : cards.map((c, idx) => (
                  <tr key={c.id}>
                    <td style={{ color:'#94a3b8', fontSize:12 }}>{idx + 1}</td>
                    <td style={{ fontSize:20 }}>{c.icon}</td>
                    <td style={{ fontWeight:600 }}>
                      {c.title}
                      {c.description && <div style={{ fontSize:11, color:'#94a3b8', fontWeight:400 }}>{c.description}</div>}
                    </td>
                    <td>
                      {c.faculty_name
                        ? <span className="badge badge-purple">{c.faculty_name}</span>
                        : <span style={{ color:'#94a3b8', fontSize:12 }}>Barcha</span>}
                    </td>
                    <td style={{ fontSize:12 }}>
                      {c.start_date || c.end_date
                        ? <span style={{ color:'#0ea5e9' }}>{c.start_date ?? '…'} → {c.end_date ?? '…'}</span>
                        : <span style={{ color:'#94a3b8' }}>Doimiy</span>}
                    </td>
                    <td><span className="badge">{c.type}</span></td>
                    <td><span className={`badge ${c.is_active ? 'badge-green' : 'badge-red'}`}>{c.is_active ? 'Faol' : 'Nofaol'}</span></td>
                    <td>
                      <div style={{ display:'flex', gap:4 }}>
                        <button className="btn btn-sm" onClick={() => handleReorder(c.id, 'up')} title="Yuqoriga">↑</button>
                        <button className="btn btn-sm" onClick={() => handleReorder(c.id, 'down')} title="Pastga">↓</button>
                      </div>
                    </td>
                    <td style={{ textAlign:'right', whiteSpace:'nowrap' }}>
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
          <div className="modal" style={{ maxWidth: 520 }}>
            <div className="modal-title">{editId ? 'Cardni tahrirlash' : "Yangi card qo'shish"}</div>

            {/* Emoji */}
            <div className="form-row">
              <label className="form-label">Ikon</label>
              <div style={{ display:'flex', gap:8, alignItems:'center' }}>
                <div onClick={() => setShowEmoji(p => !p)}
                  style={{ fontSize:28, cursor:'pointer', width:48, height:48, display:'flex', alignItems:'center', justifyContent:'center', border:'2px solid #e2e8f0', borderRadius:10, background:'#f8fafc' }}>
                  {form.icon}
                </div>
                <span style={{ fontSize:12, color:'#94a3b8' }}>Bosib tanlang</span>
              </div>
              {showEmoji && (
                <div style={{ marginTop:8, display:'grid', gridTemplateColumns:'repeat(10, 1fr)', gap:4, padding:10, background:'#f8fafc', borderRadius:10, border:'1px solid #e2e8f0' }}>
                  {EMOJI_LIST.map(em => (
                    <button key={em} onClick={() => { setForm(p => ({ ...p, icon: em })); setShowEmoji(false); }}
                      style={{ fontSize:20, background:'none', border:'none', cursor:'pointer', padding:4, borderRadius:6 }}
                      onMouseOver={ev => (ev.currentTarget.style.background='#e2e8f0')}
                      onMouseOut={ev => (ev.currentTarget.style.background='none')}>
                      {em}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="form-row">
              <label className="form-label">Sarlavha *</label>
              <input className="form-inp" placeholder="Karta nomi..." value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} />
            </div>

            <div className="form-row">
              <label className="form-label">Tavsif</label>
              <textarea className="form-inp" rows={2} placeholder="Qisqacha tavsif..." value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} />
            </div>

            {/* Faculty filter */}
            <div className="form-row">
              <label className="form-label">🏫 Fakultet (bo&apos;sh = barcha uchun)</label>
              <select className="form-inp" value={form.faculty_id ?? ''} onChange={e => setForm(p => ({ ...p, faculty_id: e.target.value ? Number(e.target.value) : null }))}>
                <option value="">— Barcha talabalar —</option>
                {faculties.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
              </select>
            </div>

            <div className="form-row">
              <label className="form-label">Turi</label>
              <select className="form-inp" value={form.type} onChange={e => setForm(p => ({ ...p, type: e.target.value as ServiceCard['type'] }))}>
                <option value="message">Xabar yuborish (bot savol sifatida)</option>
                <option value="link">Tashqi havola (URL)</option>
                <option value="tab">Ichki tabga o&apos;tish</option>
              </select>
            </div>

            <div className="form-row">
              <label className="form-label">
                {form.type === 'link' ? 'URL manzil' : form.type === 'tab' ? 'Tab nomi' : 'Xabar matni'}
              </label>
              <input className="form-inp" placeholder={linkPlaceholder} value={form.link} onChange={e => setForm(p => ({ ...p, link: e.target.value }))} />
              {form.type === 'link' && <div style={{ fontSize:11, color:'#94a3b8', marginTop:4 }}>https:// avtomatik qo&apos;shiladi</div>}
            </div>

            {/* Date range */}
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
              <div className="form-row">
                <label className="form-label">📅 Boshlanish sanasi</label>
                <input className="form-inp" type="date" value={form.start_date} onChange={e => setForm(p => ({ ...p, start_date: e.target.value }))} />
              </div>
              <div className="form-row">
                <label className="form-label">📅 Tugash sanasi</label>
                <input className="form-inp" type="date" value={form.end_date} onChange={e => setForm(p => ({ ...p, end_date: e.target.value }))} />
              </div>
            </div>
            <div style={{ fontSize:11, color:'#94a3b8', marginBottom:8 }}>Bo&apos;sh qoldirilsa — doimiy ko&apos;rsatiladi</div>

            <div className="form-row">
              <label className="form-label">Tartib raqami (kichik = yuqorida)</label>
              <input className="form-inp" type="number" min={0} value={form.sort_order} onChange={e => setForm(p => ({ ...p, sort_order: Number(e.target.value) }))} />
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
