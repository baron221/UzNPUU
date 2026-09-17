'use client';
import { useEffect, useState } from 'react';
import { getSettings, updateSettings, verifyAdminBot, type Settings } from '@/lib/api';

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
    rate_limit_requests: '5',
    rate_limit_window: '2',
    admin_bot_token: '',
    admin_bot_username: '',
    admin_group_id: '',
    admin_group_title: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');

  const [checking, setChecking] = useState(false);
  const [botCheck, setBotCheck] = useState('');
  const [foundGroups, setFoundGroups] = useState<{ id: string; title: string }[]>([]);

  useEffect(() => {
    getSettings().then(s => {
      if (s) {
        // Convert seconds to minutes for display
        setForm({
          ...s,
          rate_limit_window: String(Math.round(Number(s.rate_limit_window || 120) / 60))
        });
      }
    }).finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setSaving(true);
    setStatus('');
    try {
      // Convert minutes back to seconds before saving
      const saveData = {
        ...form,
        rate_limit_window: String(Number(form.rate_limit_window || 2) * 60)
      };
      const res = await updateSettings(saveData);
      if (res.ok) setStatus('✅ Sozlamalar muvaffaqiyatli saqlandi!');
      else setStatus('❌ Saqlashda xatolik yuz berdi.');
    } catch {
      setStatus('❌ Serverga ulanishda xatolik.');
    }
    setSaving(false);
    setTimeout(() => setStatus(''), 4000);
  }

  async function handleCheckBot() {
    if (!form.admin_bot_token?.trim()) {
      setBotCheck('❌ Avval bot tokenini kiriting.');
      return;
    }
    setChecking(true);
    setBotCheck('');
    setFoundGroups([]);
    try {
      const res = await verifyAdminBot(form.admin_bot_token.trim());
      if (res.ok) {
        setForm(f => ({ ...f, admin_bot_username: res.bot_username || '' }));
        setFoundGroups(res.groups || []);
        setBotCheck(
          res.groups && res.groups.length
            ? `✅ @${res.bot_username} ishlayapti. Quyidagi guruhlardan birini tanlang.`
            : `✅ @${res.bot_username} ishlayapti. Endi uni yangi guruhga qo'shib, guruhda bir xabar yozing, so'ng qayta "Tekshirish" bosing.`
        );
      } else {
        setBotCheck(`❌ ${(res as any).detail || res.error || 'Token noto\'g\'ri.'}`);
      }
    } catch {
      setBotCheck('❌ Serverga ulanishda xatolik.');
    }
    setChecking(false);
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

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 28, alignItems: 'start' }}>

        {/* LEFT CARD: WORKING HOURS */}
        <div className="card" style={{ height: '100%', boxSizing: 'border-box' }}>
          <div className="section-title" style={{ marginBottom: 24 }}>
            <span style={{ marginRight: 8 }}>🕐</span>Ish vaqti oraliqlari
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
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
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
              {DAYS.map(day => {
                const isActive = form.bot_work_days.split(',').includes(day.val);
                return (
                  <button
                    key={day.val}
                    onClick={() => toggleDay(day.val)}
                    style={{
                      padding: '7px 14px',
                      borderRadius: '8px',
                      border: `1.5px solid ${isActive ? 'var(--indigo)' : '#e2e8f0'}`,
                      background: isActive ? 'var(--indigo)' : 'var(--bg)',
                      color: isActive ? '#fff' : 'var(--text)',
                      cursor: 'pointer',
                      fontWeight: 600,
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

          <div className="form-row" style={{ marginTop: 24 }}>
            <label className="form-label">Dam olish rejimi xabari</label>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>
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

        {/* RIGHT CARD: RATE LIMIT */}
        <div className="card" style={{ height: '100%', boxSizing: 'border-box' }}>
          <div className="section-title" style={{ marginBottom: 24 }}>
            <span style={{ marginRight: 8 }}>⚡</span>Xabarlar cheklovi (Rate Limit)
          </div>

          <div style={{
            padding: '16px',
            borderRadius: '12px',
            background: 'var(--bg)',
            border: '1px solid #e2e8f0',
            marginBottom: 24,
            fontSize: 13,
            color: 'var(--muted)',
            lineHeight: 1.7
          }}>
            <strong style={{ color: 'var(--text)', display: 'block', marginBottom: 6 }}>ℹ️ Qanday ishlaydi?</strong>
            Agar bir talaba belgilangan vaqt ichida savollar sonidan oshib ketsa, bot uni vaqtincha to'xtatib qo'yadi.
            <br />Masalan: <strong style={{ color: 'var(--indigo)' }}>5 ta savol / 2 daqiqada</strong>
          </div>

          <div className="form-row">
            <label className="form-label">Maksimal savollar soni</label>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>
              Belgilangan vaqt ichida bera oladigan savollar soni
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <input
                type="number"
                className="form-inp"
                min={1}
                max={100}
                value={form.rate_limit_requests || '5'}
                onChange={e => setForm({ ...form, rate_limit_requests: e.target.value })}
                style={{ flex: 1 }}
              />
              <span style={{ fontSize: 13, color: 'var(--muted)', whiteSpace: 'nowrap' }}>ta savol</span>
            </div>
          </div>

          <div className="form-row">
            <label className="form-label">Vaqt oralig'i (daqiqada)</label>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>
              Qancha daqiqa ichida yuqoridagi savollar bera oladi
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <input
                type="number"
                className="form-inp"
                min={1}
                max={60}
                value={form.rate_limit_window || '2'}
                onChange={e => setForm({ ...form, rate_limit_window: e.target.value })}
                style={{ flex: 1 }}
              />
              <span style={{ fontSize: 13, color: 'var(--muted)', whiteSpace: 'nowrap' }}>daqiqa</span>
            </div>
          </div>

          <div style={{
            marginTop: 32,
            padding: '14px 18px',
            borderRadius: '12px',
            background: '#f0fdf4',
            border: '1px solid #bbf7d0',
            fontSize: 13,
            color: '#166534'
          }}>
            📊 Hozirgi sozlama: <strong>{form.rate_limit_requests || '5'} ta savol</strong> / <strong>{form.rate_limit_window || '2'} daqiqada</strong>
          </div>
        </div>
      </div>

      {/* ADMIN NOTIFICATION BOT + GROUP */}
      <div className="card" style={{ marginTop: 28 }}>
        <div className="section-title" style={{ marginBottom: 8 }}>
          <span style={{ marginRight: 8 }}>🔔</span>Admin bildirishnoma boti va guruhi
        </div>
        <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 20, lineHeight: 1.6 }}>
          Talabalarning savollari shu yerda ko'rsatilgan Telegram guruhga yuboriladi. Alohida fakultet guruhi
          bo'lmasa, savollar shu "asosiy guruh"ga tushadi.
          <br />
          1) @BotFather orqali yangi bot yarating va tokenini pastga kiriting. 2) Yangi Telegram guruh yarating va
          shu botni unga qo'shing. 3) Guruhda bir marta xabar yozing (masalan "salom"). 4) "Tekshirish" tugmasini
          bosing va topilgan guruhni tanlang.
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="form-row" style={{ marginBottom: 0 }}>
            <label className="form-label">Bot token</label>
            <input
              type="text"
              className="form-inp"
              placeholder="123456789:AA...."
              value={form.admin_bot_token || ''}
              onChange={e => setForm({ ...form, admin_bot_token: e.target.value, admin_bot_username: '' })}
            />
            {form.admin_bot_username && (
              <div style={{ fontSize: 12, color: '#10b981', marginTop: 6 }}>✅ Bot: @{form.admin_bot_username}</div>
            )}
          </div>
          <div className="form-row" style={{ marginBottom: 0 }}>
            <label className="form-label">Asosiy guruh</label>
            <input
              type="text"
              className="form-inp"
              placeholder="Guruh ID (masalan -1001234567890)"
              value={form.admin_group_id || ''}
              onChange={e => setForm({ ...form, admin_group_id: e.target.value })}
            />
            {form.admin_group_title && (
              <div style={{ fontSize: 12, color: '#10b981', marginTop: 6 }}>✅ Guruh: {form.admin_group_title}</div>
            )}
          </div>
        </div>

        <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 14 }}>
          <button className="btn" onClick={handleCheckBot} disabled={checking} style={{ padding: '9px 20px' }}>
            {checking ? 'Tekshirilmoqda...' : '🔍 Botni tekshirish'}
          </button>
          {botCheck && <div style={{ fontSize: 13 }}>{botCheck}</div>}
        </div>

        {foundGroups.length > 0 && (
          <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {foundGroups.map(g => (
              <button
                key={g.id}
                onClick={() => setForm(f => ({ ...f, admin_group_id: g.id, admin_group_title: g.title }))}
                style={{
                  padding: '7px 14px',
                  borderRadius: '8px',
                  border: `1.5px solid ${form.admin_group_id === g.id ? 'var(--indigo)' : '#e2e8f0'}`,
                  background: form.admin_group_id === g.id ? 'var(--indigo)' : 'var(--bg)',
                  color: form.admin_group_id === g.id ? '#fff' : 'var(--text)',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: 13,
                }}
              >
                {g.title} <span style={{ opacity: 0.7, fontWeight: 400 }}>({g.id})</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div style={{ marginTop: 24, display: 'flex', alignItems: 'center', gap: 16 }}>
        <button
          className="btn btn-primary"
          onClick={handleSave}
          disabled={saving}
          style={{ padding: '12px 32px', fontSize: 15, fontWeight: 600 }}
        >
          {saving ? 'Saqlanmoqda...' : '💾 Saqlash'}
        </button>
        {status && (
          <div style={{
            fontSize: 14, fontWeight: 500,
            color: status.startsWith('✅') ? '#10b981' : '#ef4444',
            padding: '10px 16px',
            borderRadius: '10px',
            background: status.startsWith('✅') ? '#ecfdf5' : '#fff1f2'
          }}>
            {status}
          </div>
        )}
      </div>
    </>
  );
}
