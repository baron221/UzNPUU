'use client';
import { useState } from 'react';
import { uploadFile } from '@/lib/api';

export default function UploadPage() {
  const [file, setFile]     = useState<File | null>(null);
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  async function upload() {
    if (!file) { alert('Fayl tanlang!'); return; }
    setLoading(true); setStatus('⏳ Yuklanmoqda...');
    try {
      const d = await uploadFile(file);
      setLoading(false);
      if (d.ok) setStatus(`✅ Yuklandi: ${d.filename} (${d.pairs} Q&A)`);
      else setStatus(`❌ Xatolik: ${d.error}`);
    } catch {
      setLoading(false);
      setStatus('❌ Serverga ulanib bo\'lmadi.');
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Bilimlar bazasi</div>
          <div className="page-sub">AI o&#39;rganishi uchun yangi hujjatlar yuklang</div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 800, margin: '0 auto' }}>
        <div 
          className={`dropzone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
          onClick={() => document.getElementById('file-inp')?.click()}
        >
          <div className="dropzone-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
          </div>
          <div className="dropzone-text">
            {file ? <span style={{ color: 'var(--indigo)', fontWeight: 700 }}>{file.name}</span> : <span>Faylni bu yerga tashlang yoki tanlash uchun bosing</span>}
          </div>
          <div className="dropzone-hint">PDF, DOCX, XLSX, TXT, MD formatlari (Max: 10MB)</div>
          <input 
            id="file-inp" type="file" style={{ display: 'none' }} 
            onChange={e => setFile(e.target.files?.[0] ?? null)} 
          />
        </div>

        <div style={{ marginTop: 32, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ fontSize: 13, color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            Hujjatlar avtomatik AI xotirasiga tushadi
          </div>
          <button 
            className="btn btn-primary" style={{ padding: '14px 32px' }}
            onClick={upload} disabled={loading || !file}
          >
            {loading ? 'Yuklanmoqda...' : 'Yuklashni boshlash'}
          </button>
        </div>

        {status && (
          <div style={{ 
            marginTop: 24, padding: '16px', borderRadius: '12px', fontSize: 13, fontWeight: 500,
            background: status.startsWith('✅') ? '#ecfdf5' : '#fff1f2',
            color: status.startsWith('✅') ? '#065f46' : '#991b1b',
            border: `1px solid ${status.startsWith('✅') ? '#10b98130' : '#ef444430'}`
          }}>
            {status}
          </div>
        )}
      </div>
    </>
  );
}
