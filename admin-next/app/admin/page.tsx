'use client';
import { useEffect, useRef, useState } from 'react';
import { getStats } from '@/lib/api';

const BARS = [
  { label: 'Jami savollar', icon: '💬', key: 'total',     color: 'linear-gradient(90deg,#6366f1,#8b5cf6)' },
  { label: 'Javob berilgan', icon: '✅', key: 'answered',  color: 'linear-gradient(90deg,#10b981,#34d399)' },
  { label: 'Javobsiz',       icon: '❓', key: 'unanswered',color: 'linear-gradient(90deg,#ef4444,#f87171)' },
  { label: 'Talabalar',      icon: '👤', key: 'users',     color: 'linear-gradient(90deg,#f59e0b,#fbbf24)' },
  { label: 'Fakultetlar',    icon: '🏫', key: 'faculties', color: 'linear-gradient(90deg,#8b5cf6,#a78bfa)' },
  { label: 'Xodimlar',       icon: '👥', key: 'staff',     color: 'linear-gradient(90deg,#06b6d4,#22d3ee)' },
];
const NUM_COLORS: Record<string,string> = {
  total:'#6366f1', answered:'#10b981', unanswered:'#ef4444',
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
                <div className="stat-card-bar" style={{ background: b.color }} />
                <div className="stat-icon">{b.icon}</div>
                <div className="stat-num" style={{ color: NUM_COLORS[b.key] }}>{(stats as Record<string, number>)[b.key] ?? 0}</div>
                <div className="stat-lbl">{b.label}</div>
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
