'use client';
import { useState, useEffect, useRef } from 'react';
import { getAllowedStudents, uploadAllowedStudents } from '@/lib/api';

export default function AllowedStudentsPage() {
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadStudents(); }, []);

  async function loadStudents() {
    setLoading(true);
    try {
      const data = await getAllowedStudents();
      setStudents(data.students || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setStatus('⏳ Yuklanmoqda...');
    try {
      const data = await uploadAllowedStudents(file);
      if (data.ok) {
        setStatus(`✅ Muvaffaqiyatli yuklandi: ${data.count} ta talaba.`);
        setFile(null);
        loadStudents();
      } else {
        setStatus(`❌ Xatolik: ${data.error}`);
      }
    } catch (e: any) {
      setStatus(`❌ Xatolik: ${e.message}`);
    }
    setUploading(false);
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0];
    if (f && f.name.endsWith('.xlsx')) setFile(f);
    else alert('Faqat .xlsx fayl qabul qilinadi!');
  };

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Talabalar Bazasi</div>
          <div className="page-sub">Botdan ro'yxatdan o'ta oladigan talabalar ro'yxatini Excel (.xlsx) orqali yuklang.</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32, alignItems: 'start' }}>

        {/* Upload column */}
        <section>
          <div className="section-title">Yangi ro'yxat yuklash</div>
          <div className="card">
            <div
              className={`dropzone${dragActive ? ' active' : ''}`}
              onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
            >
              <div className="dropzone-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <div className="dropzone-text">
                {file
                  ? <span style={{ color: 'var(--indigo)', fontWeight: 700 }}>{file.name}</span>
                  : <span>Excel faylini bu yerga tashlang yoki tanlash uchun bosing</span>
                }
              </div>
              <div className="dropzone-hint">Faqat .xlsx formatidagi fayllar qabul qilinadi</div>
              <input
                ref={inputRef}
                type="file"
                accept=".xlsx"
                style={{ display: 'none' }}
                onChange={e => setFile(e.target.files?.[0] || null)}
              />
            </div>

            <div style={{ marginTop: 24 }}>
              <button
                className="btn btn-primary"
                style={{ width: '100%', padding: '14px' }}
                onClick={handleUpload}
                disabled={!file || uploading}
              >
                {uploading ? 'Yuklanmoqda...' : 'Yuklashni boshlash'}
              </button>
            </div>

            {status && (
              <div style={{
                marginTop: 20, padding: '14px', borderRadius: '12px', fontSize: 13, fontWeight: 500,
                background: status.startsWith('✅') ? '#ecfdf5' : status.startsWith('⏳') ? '#eff6ff' : '#fff1f2',
                color: status.startsWith('✅') ? '#065f46' : status.startsWith('⏳') ? '#1e40af' : '#991b1b',
                border: `1px solid ${status.startsWith('✅') ? '#10b98130' : status.startsWith('⏳') ? '#3b82f630' : '#ef444430'}`
              }}>
                {status}
              </div>
            )}

            <div style={{ marginTop: 20, padding: '14px', borderRadius: '12px', background: 'var(--bg)', fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
              <strong style={{ color: 'var(--text)', display: 'block', marginBottom: 6 }}>📋 Qoidalar:</strong>
              • 1-qator sarlavha bo'lishi kerak<br />
              • ID ustuni: "ID", "PINFL" so'zlarini o'z ichiga olishi kerak<br />
              • Ism ustuni: "Name", "F.I.O", "FISH" bo'lishi kerak<br />
              • Yangi fayl yuklasangiz, eski ro'yxat o'chib ketadi
            </div>
          </div>
        </section>

        {/* List column */}
        <section>
          <div className="section-title">Joriy bazadagi talabalar ({students.length})</div>
          <div className="table-card" style={{ margin: 0, display: 'flex', flexDirection: 'column', maxHeight: 520 }}>
            <table style={{ minWidth: '100%' }}>
              <thead style={{ position: 'sticky', top: 0, background: 'var(--card)', zIndex: 1 }}>
                <tr>
                  <th style={{ width: 50 }}>#</th>
                  <th>Talaba ID</th>
                  <th>F.I.O</th>
                </tr>
              </thead>
            </table>
            <div style={{ overflowY: 'auto', flex: 1 }}>
            <table style={{ minWidth: '100%' }}>
              <tbody>
                {loading ? (
                  Array(5).fill(0).map((_, i) => (
                    <tr key={i}>
                      <td colSpan={3}><div className="skeleton" style={{ height: 20, margin: '10px 0' }} /></td>
                    </tr>
                  ))
                ) : students.length === 0 ? (
                  <tr>
                    <td colSpan={3} style={{ textAlign: 'center', padding: '80px 0', color: 'var(--muted2)' }}>
                      Hali hech qanday talaba yuklanmagan
                    </td>
                  </tr>
                ) : (
                  students.map((s, i) => (
                    <tr key={i}>
                      <td style={{ color: 'var(--muted)', fontSize: 12 }}>{i + 1}</td>
                      <td style={{ fontWeight: 600 }}>{s.student_id}</td>
                      <td style={{ color: 'var(--muted)' }}>{s.full_name || '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
            </div>
          </div>
        </section>

      </div>
    </>
  );
}
