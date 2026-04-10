'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';

const NAV = [
  { href: '/admin',            icon: '📊', label: 'Umumiy' },
  { href: '/admin/questions',  icon: '💬', label: 'Savollar' },
  { href: '/admin/faculties',  icon: '🏫', label: 'Fakultetlar' },
  { href: '/admin/users',      icon: '👥', label: 'Xodimlar' },
  { href: '/admin/faq',        icon: '📋', label: 'FAQ' },
  { href: '/admin/upload',     icon: '📁', label: 'Hujjat Yuklash' },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname  = usePathname();
  const router    = useRouter();

  useEffect(() => {
    if (!localStorage.getItem('admin_token')) router.replace('/');
  }, []);

  function logout() {
    localStorage.removeItem('admin_token');
    router.replace('/');
  }

  return (
    <div style={{ display: 'flex' }}>
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="sidebar-logo">🎓</div>
          <div className="sidebar-title">UzNPUU</div>
          <div className="sidebar-sub">Admin boshqaruv paneli</div>
        </div>

        <div className="nav-section">Asosiy</div>
        {NAV.slice(0, 2).map(n => (
          <Link key={n.href} href={n.href}
            className={`nav-item${pathname === n.href ? ' active' : ''}`}>
            <span className="nav-icon">{n.icon}</span>{n.label}
          </Link>
        ))}

        <div className="nav-section">Boshqaruv</div>
        {NAV.slice(2, 4).map(n => (
          <Link key={n.href} href={n.href}
            className={`nav-item${pathname === n.href ? ' active' : ''}`}>
            <span className="nav-icon">{n.icon}</span>{n.label}
          </Link>
        ))}

        <div className="nav-section">Kontent</div>
        {NAV.slice(4).map(n => (
          <Link key={n.href} href={n.href}
            className={`nav-item${pathname === n.href ? ' active' : ''}`}>
            <span className="nav-icon">{n.icon}</span>{n.label}
          </Link>
        ))}

        <div className="sidebar-footer">
          <button className="logout-btn" onClick={logout}>🚪 Chiqish</button>
        </div>
      </aside>

      <main className="content fade-up">{children}</main>
    </div>
  );
}
