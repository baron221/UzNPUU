'use client';
import { useEffect, useState } from 'react';
import { getSettings, updateSettings, type Settings } from '@/lib/api';

const DAYS = [
  { val: '0', label: 'Dushanba' },
  { val: '1', label: 'Seshanba' },
  { val: '2', label: 'Chorshanba' },
  { val: '3', label: 'Payshanba' },
  { val: '4', label: 'Juma' },
  { val: '5', label: 'Shanba' },
  { val: '6', label: 'Yakshanba' },
];

export default function SettingsPage() {
  const [form, setForm] = useState<Settings>({
    bot_start_time: '09:00',
    bot_end_time: '18:00',
    bot_work_days: '0,1,2,3,4',
    bot_offline_message: 'Bot hozirda dam olish rejimida. Iltimos, ish vaqtida murojaat qiling.',
    rate_limit_requests: '2',
    rate_limit_window: '120'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');

  useEffect(() => {
    getSettings().then(s => {
      if (s) setForm(s);
    }).finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setSaving(true);
    setStatus('');
    try {
      const res = await updateSettings(form);
      if (res.ok) setStatus('✅ Sozlamalar muvaffaqiyatli saqlandi!');
      else setStatus('❌ Saqlashda xatolik yuz berdi.');
    } catch {
      setStatus('❌ Serverga ulanishda xatolik.');
    }
    setSaving(false);
    setTimeout(() => setStatus(''), 4000);
  }

  const toggleDay = (dayVal: string) => {
    const days = form.bot_work_days.split(',').filter(d => d.trim() !== '');
    if (days.includes(dayVal)) {
      setForm({ ...form, bot_work_days: days.filter(d => d !== dayVal).join(',') });
    } else {
      setForm({ ...form, bot_work_days: [...days, dayVal].sort().join(',') });
    }
  };

  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}>Yuklanmoqda...</div>;

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Sozlamalar</div>
          <div className="page-sub">Bot ishlash vaqtini va xabarlarni boshqarish</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 24, alignItems: 'start', maxWidth: 1000 }}>
        {/* --- LEFT CARD: WORKING HOURS --- */}
        <div className="card">
        <div className="section-title" style={{ marginBottom: 20 }}>Ish vaqti oraliqlari</div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
          <div className="form-row" style={{ marginBottom: 0 }}>
            <label className="form-label">Boshlanish vaqti</label>
            <input 
              type="time" 
              className="form-inp" 
              value={form.bot_start_time}
              onChange={e => setForm({ ...form, bot_start_time: e.target.value })}
            />
          </div>
          <div className="form-row" style={{ marginBottom: 0 }}>
            <label className="form-label">Tugash vaqti</label>
            <input 
              type="time" 
              className="form-inp" 
              value={form.bot_end_time}
              onChange={e => setForm({ ...form, bot_end_time: e.target.value })}
            />
          </div>
        </div>

        <div className="form-row">
          <label className="form-label">Ish kunlari</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 8 }}>
            {DAYS.map(day => {
              const isActive = form.bot_work_days.split(',').includes(day.val);
              return (
                <button
                  key={day.val}
                  onClick={() => toggleDay(day.val)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '8px',
                    border: `1px solid ${isActive ? 'var(--indigo)' : '#e2e8f0'}`,
                    background: isActive ? 'var(--indigo)' : '#fff',
                    color: isActive ? '#fff' : 'var(--text)',
                    cursor: 'pointer',
                    fontWeight: 500,
                    fontSize: 13,
                    transition: 'all 0.2s'
                  }}
                >
                  {day.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="form-row" style={{ marginTop: 32 }}>
          <label className="form-label">Dam olish rejimi xabari</label>
          <div className="form-desc" style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>
            Bot ishlamaydigan vaqtda foydalanuvchi yozsa, shu xabar boradi.
          </div>
          <textarea 
            className="form-inp" 
            rows={4}
            value={form.bot_offline_message}
            onChange={e => setForm({ ...form, bot_offline_message: e.target.value })}
          />
        </div>

        </div>
        
        {/* --- RIGHT CARD: RATE LIMIT --- */}
        <div className="card">
          <div className="section-title" style={{ marginBottom: 20 }}>Xabarlar cheklovi (Rate Limit)</div>
          
          <div className="form-row">
            <label className="form-label">Maksimal savollar soni</label>
            <div className="form-desc" style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>Bir foydalanuvchi bera oladigan savollar soni</div>
            <input 
              type="number" 
              className="form-inp" 
              value={form.rate_limit_requests || '2'}
              onChange={e => setForm({ ...form, rate_limit_requests: e.target.value })}
            />
          </div>
          
          <div className="form-row">
            <label className="form-label">Vaqt oralig'i (soniyada)</label>
            <div className="form-desc" style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>Qancha vaqt ichida shuncha savol bera oladi (120 = 2 daqiqa)</div>
            <input 
              type="number" 
              className="form-inp" 
              value={form.rate_limit_window || '120'}
              onChange={e => setForm({ ...form, rate_limit_window: e.target.value })}
            />
          </div>
        </div>
      </div>

      <div style={{ marginTop: 24, display: 'flex', alignItems: 'center', gap: 16 }}>
        <button 
          className="btn btn-primary" 
          onClick={handleSave} 
          disabled={saving}
          style={{ padding: '12px 24px', fontSize: 15, fontWeight: 500 }}
        >
          {saving ? 'Saqlanmoqda...' : 'Saqlash'}
        </button>
        {status && <div style={{ fontSize: 14, fontWeight: 500, color: status.startsWith('✅') ? '#10b981' : '#ef4444' }}>{status}</div>}
      </div>
    </>
  );
}
