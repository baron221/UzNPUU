'use client';
import { useEffect, useState } from 'react';
import { getUsers, createUser, deleteUser, getFaculties, type User, type Faculty } from '@/lib/api';

export default function UsersPage() {
  const [items, setItems]       = useState<User[]>([]);
  const [faculties, setFaculties] = useState<Faculty[]>([]);
  const [modal, setModal]       = useState(false);
  const [form, setForm]         = useState({ full_name:'', phone:'', password:'', faculty_id:'', role:'staff' });
  const [loading, setLoading]   = useState(true);

  async function load() {
    setLoading(true);
    const [ud, fd] = await Promise.all([getUsers(), getFaculties()]);
    setItems(ud.users); setFaculties(fd.faculties); setLoading(false);
  }
  useEffect(() => { load(); }, []);

  async function save() {
    if (!form.full_name || !form.phone || !form.password) { alert("Barcha maydonlarni to'ldiring!"); return; }
    await createUser({ ...form, faculty_id: form.faculty_id ? Number(form.faculty_id) as unknown as string : undefined });
    setModal(false);
    setForm({ full_name:'', phone:'', password:'', faculty_id:'', role:'staff' });
    load();
  }

  const ROLES: Record<string, string> = { admin:'badge-red', dean:'badge-purple', staff:'badge-blue' };

  return (
    <>
      <div className="page-header">
        <div><div className="page-title">Xodimlar</div><div className="page-sub">Telefon va parol bilan kirish</div></div>
        <button className="btn btn-primary" onClick={() => setModal(true)}>+ Yangi xodim</button>
      </div>

      {loading ? (
        <div className="table-card">
          {[1,2,3].map(i => <div key={i} style={{ padding:'16px 18px', borderBottom:'1px solid #f1f2f9' }}><div className="skeleton" style={{ height:14, width:'60%' }} /></div>)}
        </div>
      ) : (
        <div className="table-card">
          <table>
            <thead><tr><th>Ism</th><th>Telefon</th><th>Fakultet</th><th>Lavozim</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {items.length === 0 ? <tr><td colSpan={6} className="empty">Xodimlar yo&#39;q</td></tr>
                : items.map(u => (
                  <tr key={u.id}>
                    <td><strong>{u.full_name}</strong></td>
                    <td style={{ fontFamily:'monospace', fontSize:12 }}>{u.phone}</td>
                    <td><span className="badge badge-purple">{u.faculty_name || '—'}</span></td>
                    <td><span className={`badge ${ROLES[u.role] ?? 'badge-blue'}`}>{u.role}</span></td>
                    <td><span className={`badge ${u.is_active ? 'badge-green' : 'badge-red'}`}>{u.is_active ? 'Faol' : 'Nofaol'}</span></td>
                    <td><button className="btn btn-sm btn-red" onClick={async () => { if (confirm("O'chirasizmi?")) { await deleteUser(u.id); load(); } }}>O&#39;chir</button></td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setModal(false)}>
          <div className="modal">
            <div className="modal-title">Yangi xodim</div>
            {[
              { label:"To'liq ism *", k:'full_name', type:'text', ph:'Ism Familiya' },
              { label:'Telefon raqami *', k:'phone', type:'text', ph:'+998901234567' },
              { label:'Parol *', k:'password', type:'password', ph:'Kamida 6 belgi' },
            ].map(({ label, k, type, ph }) => (
              <div key={k} className="form-row">
                <label className="form-label">{label}</label>
                <input className="form-inp" type={type} placeholder={ph}
                  value={(form as Record<string,string>)[k]}
                  onChange={e => setForm(p => ({ ...p, [k]: e.target.value }))} />
              </div>
            ))}
            <div className="form-row">
              <label className="form-label">Fakultet</label>
              <select className="form-inp" value={form.faculty_id} onChange={e => setForm(p => ({ ...p, faculty_id: e.target.value }))}>
                <option value="">Tanlang...</option>
                {faculties.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
              </select>
            </div>
            <div className="form-row">
              <label className="form-label">Lavozim</label>
              <select className="form-inp" value={form.role} onChange={e => setForm(p => ({ ...p, role: e.target.value }))}>
                <option value="staff">Xodim</option>
                <option value="dean">Dekan</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="modal-actions">
              <button className="btn btn-red" onClick={() => setModal(false)}>Bekor</button>
              <button className="btn btn-primary" onClick={save}>Saqlash</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
