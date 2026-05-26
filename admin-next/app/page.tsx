'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [err, setErr]   = useState('');
  const [loading, setLoading] = useState(false);

  async function doLogin() {
    if (!user || !pass) { setErr("Login va parolni kiriting!"); return; }
    setLoading(true); setErr('');
    try {
      const d = await login(user, pass);
      if (d.ok && d.token) {
        localStorage.setItem('admin_token', d.token);
        router.replace('/admin');
      } else {
        setErr(d.error ?? "Login yoki parol noto'g'ri!");
      }
    } catch {
      setErr("Serverga ulanib bo'lmadi.");
    }
    setLoading(false);
  }

  return (
    <div className="login-wrap mesh-bg">
      <div className="login-card" style={{ backdropFilter: 'blur(20px)', background: 'rgba(255,255,255,0.85)', border: '1px solid rgba(255,255,255,0.3)' }}>
        <div className="login-logo">🎓</div>
        <h1 className="login-title" style={{ fontWeight: 900, fontSize: 32, letterSpacing: -1 }}>NPUU Admin</h1>
        <p className="login-sub" style={{ fontSize: 14, fontWeight: 500 }}>Boshqaruv tizimiga xush kelibsiz</p>

        <div style={{ textAlign: 'left', marginTop: 20 }}>
          <input
            className="inp" type="text" placeholder="Login"
            value={user} onChange={e => setUser(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && doLogin()}
            style={{ padding: 16, borderRadius: 14, background: '#fff', border: '1px solid #e2e8f0' }}
          />
          <input
            className="inp" type="password" placeholder="Parol"
            value={pass} onChange={e => setPass(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && doLogin()}
            style={{ padding: 16, borderRadius: 14, background: '#fff', border: '1px solid #e2e8f0' }}
          />
        </div>
        
        <button className="btn-login" onClick={doLogin} disabled={loading} style={{ padding: 18, borderRadius: 14, marginTop: 10 }}>
          {loading ? 'Kirilmoqda...' : 'Tizimga kirish'}
        </button>
        <div className="login-err">{err}</div>
      </div>
    </div>
  );
}
