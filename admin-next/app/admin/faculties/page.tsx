'use client';
import { useEffect, useState } from 'react';
import { getFaculties, createFaculty, updateFaculty, deleteFaculty, type Faculty } from '@/lib/api';

const EMPTY: Partial<Faculty> = { name: '', description: '', telegram_group_id: '', telegram_group_name: '' };

export default function FacultiesPage() {
  const [items, setItems]   = useState<Faculty[]>([]);
  const [modal, setModal]   = useState(false);
  const [editing, setEditing] = useState<Faculty | null>(null);
  const [form, setForm]     = useState<Partial<Faculty>>(EMPTY);
  const [loading, setLoading] = useState(true);

  async function load() { setLoading(true); const d = await getFaculties(); setItems(d.faculties); setLoading(false); }
  useEffect(() => { load(); }, []);

  function openNew()  { setEditing(null); setForm(EMPTY); setModal(true); }
  function openEdit(f: Faculty) { setEditing(f); setForm({ name:f.name, description:f.description, telegram_group_id:f.telegram_group_id, telegram_group_name:f.telegram_group_name }); setModal(true); }

  async function save() {
    if (!form.name) { alert('Nomi kiritish shart!'); return; }
    if (editing) await updateFaculty(editing.id, form);
    else await createFaculty(form);
    setModal(false); load();
  }

  async function del(id: number) {
    if (!confirm("O'chirasizmi?")) return;
    await deleteFaculty(id); load();
  }

  return (
    <>
      <div className="page-header">
        <div><div className="page-title">Fakultetlar</div><div className="page-sub">CRUD boshqaruv</div></div>
        <button className="btn btn-primary" onClick={openNew}>+ Yangi fakultet</button>
      </div>

      {loading ? (
        <div className="table-card">
          {[1,2,3].map(i => <div key={i} style={{ padding:'16px 18px', borderBottom:'1px solid #f1f2f9' }}><div className="skeleton" style={{ height:14, width:'70%' }} /></div>)}
        </div>
      ) : (
        <div className="table-card">
          <table>
            <thead><tr><th>Nomi</th><th>Tavsif</th><th>Telegram guruh</th><th>Status</th><th>Amallar</th></tr></thead>
            <tbody>
              {items.length === 0 ? <tr><td colSpan={5} className="empty">Fakultetlar yo&#39;q</td></tr>
                : items.map(f => (
                  <tr key={f.id}>
                    <td><strong>{f.name}</strong></td>
                    <td style={{ color:'var(--muted)' }}>{f.description || '—'}</td>
                    <td style={{ fontSize:12, color:'#4f46e5' }}>{f.telegram_group_name || f.telegram_group_id || '—'}</td>
                    <td><span className={`badge ${f.is_active ? 'badge-green' : 'badge-red'}`}>{f.is_active ? 'Faol' : 'Nofaol'}</span></td>
                    <td style={{ display:'flex', gap:6 }}>
                      <button className="btn btn-sm btn-blue" onClick={() => openEdit(f)}>Tahrir</button>
                      <button className="btn btn-sm btn-red"  onClick={() => del(f.id)}>O&#39;chir</button>
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
            <div className="modal-title">{editing ? 'Tahrirlash' : 'Yangi fakultet'}</div>
            {(['name','description','telegram_group_id','telegram_group_name'] as const).map(k => (
              <div key={k} className="form-row">
                <label className="form-label">
                  {k === 'name' ? 'Fakultet nomi *' : k === 'description' ? 'Tavsif' : k === 'telegram_group_id' ? 'Telegram guruh ID' : 'Guruh nomi'}
                </label>
                <input className="form-inp" placeholder={k === 'name' ? 'Pedagogika fakulteti' : k === 'telegram_group_id' ? '-100xxxxxxxxxx' : ''}
                  value={(form[k] as string) ?? ''}
                  onChange={e => setForm(p => ({ ...p, [k]: e.target.value }))} />
              </div>
            ))}
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
