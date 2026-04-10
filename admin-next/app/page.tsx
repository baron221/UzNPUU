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
    <div className="login-wrap">
      <div className="login-card">
        <div className="login-logo">🎓</div>
        <div className="login-title">Admin Panel</div>
        <div className="login-sub">UzNPUU Bot boshqaruv tizimi</div>

        <input
          className="inp" type="text" placeholder="Login"
          value={user} onChange={e => setUser(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && doLogin()}
        />
        <input
          className="inp" type="password" placeholder="Parol"
          value={pass} onChange={e => setPass(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && doLogin()}
        />
        <button className="btn-login" onClick={doLogin} disabled={loading}>
          {loading ? 'Kirilmoqda...' : 'Kirish →'}
        </button>
        <div className="login-err">{err}</div>
      </div>
    </div>
  );
}
