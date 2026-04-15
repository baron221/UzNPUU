'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';

/* ── SVG Icons ──────────────────────────────────────────────────────────── */
const ICONS: Record<string, React.ReactNode> = {
  home:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>,
  chat:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>,
  building: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><line x1="9" y1="22" x2="9" y2="22"></line><line x1="15" y1="22" x2="15" y2="22"></line><line x1="12" y1="6" x2="12" y2="6"></line><line x1="12" y1="10" x2="12" y2="10"></line><line x1="12" y1="14" x2="12" y2="14"></line></svg>,
  users:    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>,
  help:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>,
  upload:   <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>,
  logout:   <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>,
  grid:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>,
};

const NAV = [
  { href: '/admin',            icon: 'home',     label: 'Umumiy' },
  { href: '/admin/questions',  icon: 'chat',     label: 'Savollar' },
  { href: '/admin/faculties',  icon: 'building', label: 'Fakultetlar' },
  { href: '/admin/users',      icon: 'users',    label: 'Xodimlar' },
  { href: '/admin/faq',        icon: 'help',     label: 'FAQ' },
  { href: '/admin/upload',     icon: 'upload',   label: 'Hujjat Yuklash' },
  { href: '/admin/cards',      icon: 'grid',     label: 'Xizmatlar' },
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
          <div className="sidebar-title">UzNPUU Admin</div>
          <div className="sidebar-sub">Boshqaruv tizimi</div>
        </div>

        <div className="nav-section">Asosiy</div>
        {NAV.slice(0, 2).map(n => (
          <Link key={n.href} href={n.href}
            className={`nav-item${pathname === n.href ? ' active' : ''}`}>
            <span className="nav-icon">{ICONS[n.icon]}</span>{n.label}
          </Link>
        ))}

        <div className="nav-section">Boshqaruv</div>
        {NAV.slice(2, 4).map(n => (
          <Link key={n.href} href={n.href}
            className={`nav-item${pathname === n.href ? ' active' : ''}`}>
            <span className="nav-icon">{ICONS[n.icon]}</span>{n.label}
          </Link>
        ))}

        <div className="nav-section">Kontent</div>
        {NAV.slice(4).map(n => (
          <Link key={n.href} href={n.href}
            className={`nav-item${pathname === n.href ? ' active' : ''}`}>
            <span className="nav-icon">{ICONS[n.icon]}</span>{n.label}
          </Link>
        ))}

        <div className="sidebar-footer">
          <button className="logout-btn" onClick={logout}>
            <span className="nav-icon" style={{ width:18, height:18 }}>{ICONS.logout}</span>
            <span>Chiqish</span>
          </button>
        </div>
      </aside>

      <main className="content fade-up mesh-bg" style={{ marginLeft: 260 }}>{children}</main>
    </div>
  );
}
