'use client';
import { useEffect, useRef, useState } from 'react';
import { getStats } from '@/lib/api';

/* ── SVG Icons ──────────────────────────────────────────────────────────── */
const ICONS: Record<string, React.ReactNode> = {
  total:      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>,
  answered:   <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>,
  unanswered: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>,
  users:      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>,
  faculties:  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><line x1="9" y1="22" x2="9" y2="22"></line><line x1="15" y1="22" x2="15" y2="22"></line></svg>,
  staff:      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>,
};

const BARS = [
  { label: 'Jami savollar', icon: 'total',      key: 'total',     color: 'linear-gradient(90deg,#4f46e5,#7c3aed)' },
  { label: 'Javob berilgan', icon: 'answered',   key: 'answered',  color: 'linear-gradient(90deg,#10b981,#34d399)' },
  { label: 'Javobsiz',       icon: 'unanswered', key: 'unanswered',color: 'linear-gradient(90deg,#ef4444,#f87171)' },
  { label: 'Talabalar',      icon: 'users',      key: 'users',     color: 'linear-gradient(90deg,#f59e0b,#fbbf24)' },
  { label: 'Fakultetlar',    icon: 'faculties',  key: 'faculties', color: 'linear-gradient(90deg,#8b5cf6,#a78bfa)' },
  { label: 'Xodimlar',       icon: 'staff',      key: 'staff',     color: 'linear-gradient(90deg,#06b6d4,#22d3ee)' },
];
const NUM_COLORS: Record<string,string> = {
  total:'#4f46e5', answered:'#10b981', unanswered:'#ef4444',
  users:'#f59e0b', faculties:'#8b5cf6', staff:'#06b6d4',
};

export default function OverviewPage() {
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const actRef  = useRef<HTMLCanvasElement>(null);
  const langRef = useRef<HTMLCanvasElement>(null);
  const actChart = useRef<unknown>(null);
  const langChart = useRef<unknown>(null);

  useEffect(() => {
    getStats().then(s => {
      setStats(s);
      renderCharts(s);
    });
  }, []);

  function renderCharts(s: Record<string, number>) {
    if (typeof window === 'undefined') return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const Chart = (window as any).Chart;
    if (!Chart || !actRef.current || !langRef.current) return;

    const daily = (s as Record<string, unknown>).daily as Record<string, number> ?? {};
    if (actChart.current) (actChart.current as { destroy(): void }).destroy();
    actChart.current = new Chart(actRef.current, {
      type: 'bar',
      data: {
        labels: Object.keys(daily).map(d => d.slice(5)),
        datasets: [{ data: Object.values(daily), backgroundColor: 'rgba(99,102,241,.2)', borderColor: '#6366f1', borderWidth: 2, borderRadius: 6 }],
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
        scales: { x: { grid: { color: '#f1f2f9' }, ticks: { color: '#9ca3af', font: { size: 11 } } },
                  y: { grid: { color: '#f1f2f9' }, ticks: { color: '#9ca3af', font: { size: 11 } } } } },
    });

    const langs = (s as Record<string, unknown>).langs as Record<string, number> ?? {};
    const lc: Record<string, string> = { uz: '#10b981', ru: '#ef4444', en: '#6366f1' };
    if (langChart.current) (langChart.current as { destroy(): void }).destroy();
    langChart.current = new Chart(langRef.current, {
      type: 'doughnut',
      data: { labels: Object.keys(langs), datasets: [{ data: Object.values(langs), backgroundColor: Object.keys(langs).map(k => lc[k] ?? '#6366f1'), borderWidth: 0, hoverOffset: 6 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#6b7280', font: { size: 11 }, padding: 12 } } } },
    });
  }

  return (
    <>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js" async />
      <div className="page-header">
        <div>
          <div className="page-title">Umumiy ko&#39;rinish</div>
          <div className="page-sub">Barcha statistikalar va faollik</div>
        </div>
        <button className="btn btn-primary" onClick={() => getStats().then(s => { setStats(s); renderCharts(s); })}>↻ Yangilash</button>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        {stats
          ? BARS.map(b => (
              <div key={b.key} className="stat-card">
                <div className="stat-icon" style={{ background: `${NUM_COLORS[b.key]}15`, color: NUM_COLORS[b.key] }}>
                  <div style={{ width: 28, height: 28 }}>{ICONS[b.icon]}</div>
                </div>
                <div>
                  <div className="stat-num">{(stats as Record<string, number>)[b.key] ?? 0}</div>
                  <div className="stat-lbl">{b.label}</div>
                </div>
              </div>
            ))
          : BARS.map(b => (
              <div key={b.key} className="sk-card">
                <div className="skeleton sk-num" />
                <div className="skeleton sk-lbl" />
              </div>
            ))
        }
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="chart-card">
          <div className="chart-title">So&#39;nggi 7 kun faolligi</div>
          <div className="chart-wrap"><canvas ref={actRef} /></div>
        </div>
        <div className="chart-card">
          <div className="chart-title">Til taqsimoti</div>
          <div className="chart-wrap"><canvas ref={langRef} /></div>
        </div>
      </div>
    </>
  );
}
